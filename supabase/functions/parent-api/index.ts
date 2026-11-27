// NOT YET DEPLOYED. Deploy WITH JWT verification (never --no-verify-jwt), after migration 002, only when the owner
// says "apply". Design: docs/accounts-plan.md section 12. The parent's tool for their OWN children. The admin keeps
// the `admin` function.
//
// POST /functions/v1/parent-api  { action, ...args }   Authorization: Bearer <parent session access token>
// Caller rules (the Auth server validates the token; claims are read only after that):
//   * email confirmed, and not a synthetic child address (so a child session can never call this);
//   * app_metadata.role === 'parent' (set by `register`, service role only); `register` is the one action
//     open to a confirmed user who has no role yet. An admin is refused (403 use_admin);
//   * if the parent has a VERIFIED TOTP factor, the token must be aal2 (403 mfa_required). Parent 2FA is
//     optional and enforced once enrolled (section 12.3: the owner may choose "required" instead);
//   * every action is scoped by parent_id = caller.id; another family's child is a 404;
//   * a per-parent counter (rate_hit) caps every action except `me` at 60 per hour (429 slow_down);
//   * deletes are soft (7-day undo, owner's decision): deleted_at is set, the child's auth user is banned (its
//     refresh token stops working) and pin-login / push_save refuse it; private.purge_deleted() removes the rows
//     after 7 days. A parent whose account is marked deleted may only call `me` and `restore_account` (410 deleted).
//   register             { consent_version }              -> { ok: true }   family row + consent record + role
//   me                   {}                               -> { deleted_at, children: [{ id, name, pin_set_at, created_at, deleted_at }] }
//   create_child         { name, pin }                    -> { child: { id, name } }   409 name_taken (site-wide) | name_deleted | child_limit, 400 weak_pin|name_reserved
//   rename_child         { child_id, name }               -> { ok: true }
//   set_pin              { child_id, pin }                -> { ok: true }   voids device tokens; 400 weak_pin
//   clear_name_lock      { child_id }                     -> { ok: true }
//   delete_child         { child_id, confirm }            -> { ok: true }   confirm = the child's name; undo for 7 days
//   restore_child        { child_id }                     -> { ok: true }   409 child_limit
//   delete_account       { confirm }                      -> { ok: true }   confirm = the parent's email; undo for 7 days
//   restore_account      {}                               -> { ok: true }
// Secrets: PIN_PEPPER, CHILD_PW_SECRET, SITE_ORIGIN, CONSENT_VERSION (= CONSENT_VERSION in site/src/lib/supabase.ts;
// register fails closed without it). The 500-family cap is a DB trigger.
import { createClient } from 'npm:@supabase/supabase-js@2';
import { childPassword, hashPin } from '../_shared/pin.ts';
import { weakPin } from '../_shared/weakpin.ts';
const ALLOW_WEAK_PIN = true; // TEMPORARY (owner, 27 Nov 2026: testing). Revert to false before real families sign up.

const NAME_RE = /^[A-Za-z][A-Za-z0-9 -]{0,19}$/; // the username; unique across the site (migration 003)
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const RESERVED = new Set(['admin', 'test player']);
const nameKey = (n: string) => n.trim().toLowerCase();
const BAN = '876000h'; // until the purge deletes the user; 'none' lifts it

const ORIGIN = Deno.env.get('SITE_ORIGIN');
const CORS: Record<string, string> = {
  ...(ORIGIN ? { 'access-control-allow-origin': ORIGIN } : {}),
  'access-control-allow-headers': 'authorization, apikey, content-type, x-client-info',
  'access-control-allow-methods': 'POST, OPTIONS',
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...CORS, 'content-type': 'application/json' } });
class Refuse extends Error { constructor(public status: number, public code: string) { super(code); } }

function aalOf(token: string): string {
  const part = token.split('.')[1];
  if (!part) return '';
  const pad = '='.repeat((4 - (part.length % 4)) % 4);
  const payload = JSON.parse(atob(part.replace(/-/g, '+').replace(/_/g, '/') + pad));
  return typeof payload?.aal === 'string' ? payload.aal : '';
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null, { headers: CORS });
  if (req.method !== 'POST') return json({ error: 'bad_request' }, 405);
  try {
    const url = Deno.env.get('SUPABASE_URL')!;
    const anonKey = Deno.env.get('SUPABASE_ANON_KEY')!;
    const pepper = Deno.env.get('PIN_PEPPER');
    const pwSecret = Deno.env.get('CHILD_PW_SECRET');
    const svcKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
    if (!url || !anonKey || !pepper || !pwSecret || !svcKey) throw new Error('missing configuration');

    const token = (req.headers.get('authorization') ?? '').replace(/^Bearer\s+/i, '');
    if (!token) throw new Refuse(401, 'unauthorized');
    const svc = createClient(url, svcKey, { auth: { persistSession: false } });
    const who = await svc.auth.getUser(token);
    const caller = who.data?.user;
    if (who.error || !caller) throw new Refuse(401, 'unauthorized');
    if (!caller.email_confirmed_at || !caller.email || caller.email.endsWith('@children.invalid')) throw new Refuse(403, 'forbidden');
    const role = caller.app_metadata?.role;
    if (role === 'admin') throw new Refuse(403, 'use_admin');

    let body: Record<string, unknown>;
    try { body = await req.json(); } catch { throw new Refuse(400, 'bad_request'); }
    if (!body || typeof body !== 'object') throw new Refuse(400, 'bad_request');

    if (body.action !== 'register' && role !== 'parent') throw new Refuse(403, 'forbidden');
    if (role === 'parent' && (caller.factors ?? []).some((f) => f.status === 'verified') && aalOf(token) !== 'aal2') {
      throw new Refuse(403, 'mfa_required');
    }
    if (body.action !== 'me') {
      const hit = await svc.rpc('rate_hit', { p_key: `parent:${caller.id}`, p_max: 60, p_window: '1 hour' });
      if (hit.error) throw hit.error;
      if (hit.data !== true) throw new Refuse(429, 'slow_down');
    }

    const childId = () => {
      if (typeof body.child_id !== 'string' || !UUID_RE.test(body.child_id)) throw new Refuse(400, 'bad_request');
      return body.child_id.toLowerCase();
    };
    const goodName = (v: unknown) => {
      if (typeof v !== 'string') throw new Refuse(400, 'bad_request');
      const n = v.trim();
      if (!NAME_RE.test(n)) throw new Refuse(400, 'bad_request');
      if (RESERVED.has(nameKey(n))) throw new Refuse(400, 'name_reserved');
      return n;
    };
    const goodPin = (v: unknown) => {
      if (typeof v !== 'string' || !/^\d{4}$/.test(v)) throw new Refuse(400, 'bad_request');
      // ponytail: owner 27 Nov 2026 allows easy PINs (1111, 1234) for testing "for the moment". Set ALLOW_WEAK_PIN back to
      // false to restore the check (the login limits still apply either way). Still 4 digits.
      if (!ALLOW_WEAK_PIN && weakPin(v)) throw new Refuse(400, 'weak_pin');
      return v;
    };
    type Kid = { id: string; name: string; role: 'child'; deleted_at: string | null };
    const profileOf = async (id: string, deletedOk = false) => {
      const r = await svc.from('profiles').select('id, name, role, deleted_at').eq('id', id).eq('parent_id', caller.id).eq('role', 'child').maybeSingle();
      if (r.error) throw r.error;
      if (!r.data || (r.data.deleted_at && !deletedOk)) throw new Refuse(404, 'not_found');
      return r.data as Kid;
    };
    const ban = async (id: string, on: boolean) => {
      const b = await svc.auth.admin.updateUserById(id, { ban_duration: on ? BAN : 'none' });
      if (b.error) throw b.error;
    };
    const activeCount = async () => {
      const r = await svc.from('profiles').select('id', { count: 'exact', head: true })
        .eq('parent_id', caller.id).eq('role', 'child').is('deleted_at', null);
      if (r.error) throw r.error;
      return r.count ?? 0;
    };
    const setPin = async (id: string, pin: string) => {
      const r = await svc.from('profiles').update({ pin_hash: await hashPin(pin, pepper) }).eq('id', id).select('id');
      if (r.error || !r.data?.length) throw r.error ?? new Error('pin not stored');
      // a child session can call auth.updateUser: re-assert the synthetic address and derived password (audit F13)
      const fix = await svc.auth.admin.updateUserById(id, {
        email: `child-${id}@children.invalid`, password: await childPassword(id, pwSecret), email_confirm: true,
      });
      if (fix.error) throw fix.error;
    };
    const clearLocks = async (name: string) => {
      for (const trusted of [false, true]) {
        const c = await svc.rpc('pin_clear', { p_device_key: '', p_name_key: nameKey(name), p_trusted: trusted });
        if (c.error) throw c.error;
      }
    };
    const family = async () => {
      const f = await svc.from('families').select('deleted_at').eq('parent_id', caller.id).maybeSingle();
      if (f.error) throw f.error;
      if (!f.data) throw new Refuse(404, 'not_found');
      return f.data as { deleted_at: string | null };
    };
    if (role === 'parent' && !['me', 'register', 'restore_account'].includes(String(body.action)) && (await family()).deleted_at) {
      throw new Refuse(410, 'deleted');
    }

    switch (body.action) {
      case 'register': {
        if (role === 'parent') return json({ ok: true }); // idempotent
        const consent = Deno.env.get('CONSENT_VERSION');
        if (!consent) throw new Error('missing configuration'); // fail closed: never record a notice that does not exist
        if (typeof body.consent_version !== 'string' || body.consent_version !== consent) {
          throw new Refuse(400, 'consent_required');
        }
        const ins = await svc.from('families').insert({ parent_id: caller.id, consent_version: body.consent_version });
        if (ins.error && ins.error.code !== '23505') throw ins.error; // 23505: the row exists (a retried register)
        // role is set only after the family row exists; the client then refreshes its session to see it
        const up = await svc.auth.admin.updateUserById(caller.id, { app_metadata: { ...caller.app_metadata, role: 'parent' } });
        if (up.error) throw up.error;
        return json({ ok: true });
      }
      case 'me': {
        const r = await svc.from('profiles').select('id, name, pin_set_at, created_at, deleted_at').eq('parent_id', caller.id).eq('role', 'child').order('created_at');
        if (r.error) throw r.error;
        const f = await family();
        return json({ deleted_at: f.deleted_at, children: r.data });
      }
      case 'create_child': {
        const name = goodName(body.name);
        const pin = goodPin(body.pin);
        // usernames are unique across the site: a name held by any child (another family's too) is taken
        const dup = await svc.from('profiles').select('id, parent_id, deleted_at').eq('role', 'child').eq('name_key', nameKey(name)).maybeSingle();
        if (dup.error) throw dup.error;
        if (dup.data) throw new Refuse(409, dup.data.parent_id === caller.id && dup.data.deleted_at ? 'name_deleted' : 'name_taken');
        if ((await activeCount()) >= 6) throw new Refuse(409, 'child_limit');
        const created = await svc.auth.admin.createUser({
          email: `new-${crypto.randomUUID()}@children.invalid`, password: crypto.randomUUID() + crypto.randomUUID(), email_confirm: true,
        });
        const id = created.data?.user?.id;
        if (created.error || !id) throw created.error ?? new Error('no user');
        try {
          const ins = await svc.from('profiles').insert({ id, parent_id: caller.id, name, role: 'child' });
          if (ins.error) {
            if (ins.error.code === '23505') throw new Refuse(409, 'name_taken');
            if (/child limit/.test(ins.error.message ?? '')) throw new Refuse(409, 'child_limit');
            if (/reserved name/.test(ins.error.message ?? '')) throw new Refuse(400, 'name_reserved');
            throw ins.error;
          }
          await setPin(id, pin); // also moves the auth user to the synthetic address and derived password
          await clearLocks(name); // the lock key is the username: a new child never inherits a stranger's lock-out
        } catch (e) {
          await svc.auth.admin.deleteUser(id); // no orphan auth user, no profile (cascade)
          throw e;
        }
        return json({ child: { id, name } });
      }
      case 'rename_child': {
        const id = childId();
        const name = goodName(body.name);
        const old = await profileOf(id);
        const dup = await svc.from('profiles').select('id').eq('role', 'child').eq('name_key', nameKey(name)).neq('id', id).maybeSingle();
        if (dup.error) throw dup.error;
        if (dup.data) throw new Refuse(409, 'name_taken');
        const u = await svc.from('profiles').update({ name }).eq('id', id).eq('parent_id', caller.id).select('id');
        if (u.error) { if (u.error.code === '23505') throw new Refuse(409, 'name_taken'); throw u.error; }
        if (!u.data?.length) throw new Refuse(404, 'not_found');
        await clearLocks(old.name); // only after the rename: a failed rename must not reset an attacker's lock
        await clearLocks(name); // nor start the new username with someone else's lock-out
        return json({ ok: true });
      }
      case 'set_pin': {
        const id = childId();
        const pin = goodPin(body.pin);
        await profileOf(id);
        await setPin(id, pin);
        return json({ ok: true });
      }
      case 'clear_name_lock': {
        const id = childId();
        await profileOf(id);
        const as = createClient(url, anonKey, { auth: { persistSession: false }, global: { headers: { Authorization: `Bearer ${token}` } } });
        const r = await as.rpc('pin_clear_name_lock', { p_child: id }); // owner check runs on the caller's own JWT
        if (r.error) throw r.error;
        return json({ ok: true });
      }
      case 'delete_child': {
        const id = childId();
        const p = await profileOf(id);
        if (typeof body.confirm !== 'string' || nameKey(body.confirm) !== nameKey(p.name)) throw new Refuse(400, 'confirm_required');
        await clearLocks(p.name);
        await ban(id, true); // first: if the mark below fails, the child is only locked out, nothing is lost
        const u = await svc.from('profiles').update({ deleted_at: new Date().toISOString() }).eq('id', id).eq('parent_id', caller.id);
        if (u.error) throw u.error;
        return json({ ok: true });
      }
      case 'restore_child': {
        const id = childId();
        const p = await profileOf(id, true);
        if (!p.deleted_at) { await ban(id, false); return json({ ok: true }); } // a delete that failed after its ban
        if ((await activeCount()) >= 6) throw new Refuse(409, 'child_limit');
        const u = await svc.from('profiles').update({ deleted_at: null }).eq('id', id).eq('parent_id', caller.id);
        if (u.error) throw u.error;
        await ban(id, false);
        return json({ ok: true });
      }
      case 'delete_account': {
        if (typeof body.confirm !== 'string' || body.confirm.trim().toLowerCase() !== caller.email.toLowerCase()) {
          throw new Refuse(400, 'confirm_required');
        }
        const kids = await svc.from('profiles').select('id, name').eq('parent_id', caller.id);
        if (kids.error) throw kids.error;
        // lock every child out first; the family mark is what pin-login and push_save check, so set it last and
        // a failure part-way leaves an account that still works and a button that can be pressed again
        await Promise.all((kids.data ?? []).map(async (k) => { await clearLocks(k.name); await ban(k.id, true); }));
        const u = await svc.from('families').update({ deleted_at: new Date().toISOString() }).eq('parent_id', caller.id);
        if (u.error) throw u.error;
        return json({ ok: true });
      }
      case 'restore_account': {
        const u = await svc.from('families').update({ deleted_at: null }).eq('parent_id', caller.id);
        if (u.error) throw u.error;
        const kids = await svc.from('profiles').select('id').eq('parent_id', caller.id).is('deleted_at', null);
        if (kids.error) throw kids.error;
        await Promise.all((kids.data ?? []).map((k) => ban(k.id, false))); // a child deleted on its own stays deleted
        return json({ ok: true });
      }
      default:
        throw new Refuse(400, 'bad_request');
    }
  } catch (e) {
    if (e instanceof Refuse) return json({ error: e.code }, e.status);
    console.error('parent-api failed', e instanceof Error ? e.message : 'unknown');
    return json({ error: 'server_error' }, 500);
  }
});
