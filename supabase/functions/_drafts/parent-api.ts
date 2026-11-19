// DRAFT - not deployed. In Phase 2 this becomes supabase/functions/parent-api/index.ts (deploy WITH JWT
// verification, never --no-verify-jwt), only after the owner says "apply". Design: docs/accounts-plan.md
// section 12. The parent's tool for their OWN children. The admin keeps the `admin` function.
//
// POST /functions/v1/parent-api  { action, ...args }   Authorization: Bearer <parent session access token>
// Caller rules (the Auth server validates the token; claims are read only after that):
//   * email confirmed, and not a synthetic child address (so a child session can never call this);
//   * app_metadata.role === 'parent' (set by `register`, service role only); `register` is the one action
//     open to a confirmed user who has no role yet. An admin is refused (403 use_admin);
//   * if the parent has a VERIFIED TOTP factor, the token must be aal2 (403 mfa_required). Parent 2FA is
//     optional and enforced once enrolled (section 12.3: the owner may choose "required" instead);
//   * every action is scoped by parent_id = caller.id; another family's child is a 404;
//   * a per-parent counter (rate_hit) caps hashing and child changes at 60 per hour (429 slow_down).
//   register             { consent_version }              -> { code }   family row + consent record + role
//   me                   {}                               -> { code, children: [{ id, name, pin_set_at, created_at }] }
//   create_child         { name, pin }                    -> { child: { id, name } }   409 name_taken|child_limit, 400 weak_pin|name_reserved
//   rename_child         { child_id, name }               -> { ok: true }
//   set_pin              { child_id, pin }                -> { ok: true }   voids device tokens; 400 weak_pin
//   clear_name_lock      { child_id }                     -> { ok: true }
//   delete_child         { child_id, confirm }            -> { ok: true }   confirm = the child's name
//   rotate_family_code   {}                               -> { code }       old code stops working at once
//   delete_account       { confirm }                      -> { ok: true }   confirm = the parent's email; everything is removed
// Secrets: PIN_PEPPER, CHILD_PW_SECRET, SITE_ORIGIN. Env: CONSENT_VERSION (the current notice id), MAX_FAMILIES unused (DB trigger caps at 500).
import { createClient } from 'npm:@supabase/supabase-js@2';
import { childPassword, hashPin } from '../_shared/pin.ts';
import { weakPin } from '../_shared/weakpin.ts';

const NAME_RE = /^[A-Za-z][A-Za-z -]{0,19}$/;
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const CODE_ALPHA = '23456789ABCDEFGHJKMNPQRSTUVWXYZ';
const RESERVED = new Set(['admin', 'test player']);
const nameKey = (n: string) => n.trim().toLowerCase();

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

/** 8 symbols, rejection sampling (no modulo bias). */
function newCode(): string {
  let out = '';
  while (out.length < 8) {
    for (const b of crypto.getRandomValues(new Uint8Array(16))) {
      if (b < 248 && out.length < 8) out += CODE_ALPHA[b % 31]; // 248 = 31 * 8
    }
  }
  return out;
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
    const hit = await svc.rpc('rate_hit', { p_key: `parent:${caller.id}`, p_max: 60, p_window: '1 hour' });
    if (hit.error) throw hit.error;
    if (hit.data !== true) throw new Refuse(429, 'slow_down');

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
      if (weakPin(v)) throw new Refuse(400, 'weak_pin');
      return v;
    };
    const profileOf = async (id: string) => {
      const r = await svc.from('profiles').select('id, name, role').eq('id', id).eq('parent_id', caller.id).eq('role', 'child').maybeSingle();
      if (r.error) throw r.error;
      if (!r.data) throw new Refuse(404, 'not_found');
      return r.data as { id: string; name: string; role: 'child' };
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
        const c = await svc.rpc('pin_clear', { p_device_key: '', p_name_key: `${caller.id}:${nameKey(name)}`, p_trusted: trusted });
        if (c.error) throw c.error;
      }
    };
    const familyCode = async () => {
      const f = await svc.from('families').select('code').eq('parent_id', caller.id).maybeSingle();
      if (f.error) throw f.error;
      if (!f.data) throw new Refuse(404, 'not_found');
      return f.data.code as string;
    };

    switch (body.action) {
      case 'register': {
        if (role === 'parent') return json({ code: await familyCode() }); // idempotent
        if (typeof body.consent_version !== 'string' || body.consent_version !== (Deno.env.get('CONSENT_VERSION') ?? body.consent_version)) {
          throw new Refuse(400, 'consent_required');
        }
        let code = '';
        for (let i = 0; i < 5 && !code; i++) {
          const c = newCode();
          const ins = await svc.from('families').insert({ parent_id: caller.id, code: c, consent_version: body.consent_version });
          if (!ins.error) code = c;
          else if (ins.error.code !== '23505') throw ins.error;
          else if (/families_pkey/.test(ins.error.message ?? '')) { code = await familyCode(); } // raced with ourselves
        }
        if (!code) throw new Error('no family code');
        // role is set only after the family row exists; the client then refreshes its session to see it
        const up = await svc.auth.admin.updateUserById(caller.id, { app_metadata: { ...caller.app_metadata, role: 'parent' } });
        if (up.error) throw up.error;
        return json({ code });
      }
      case 'me': {
        const r = await svc.from('profiles').select('id, name, pin_set_at, created_at').eq('parent_id', caller.id).eq('role', 'child').order('created_at');
        if (r.error) throw r.error;
        return json({ code: await familyCode(), children: r.data });
      }
      case 'create_child': {
        const name = goodName(body.name);
        const pin = goodPin(body.pin);
        const dup = await svc.from('profiles').select('id').eq('parent_id', caller.id).eq('role', 'child').eq('name_key', nameKey(name)).maybeSingle();
        if (dup.error) throw dup.error;
        if (dup.data) throw new Refuse(409, 'name_taken');
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
        const dup = await svc.from('profiles').select('id').eq('parent_id', caller.id).eq('role', 'child').eq('name_key', nameKey(name)).neq('id', id).maybeSingle();
        if (dup.error) throw dup.error;
        if (dup.data) throw new Refuse(409, 'name_taken');
        await clearLocks(old.name); // the lock keys follow the name: leave none behind
        const u = await svc.from('profiles').update({ name }).eq('id', id).eq('parent_id', caller.id).select('id');
        if (u.error) { if (u.error.code === '23505') throw new Refuse(409, 'name_taken'); throw u.error; }
        if (!u.data?.length) throw new Refuse(404, 'not_found');
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
        if (body.confirm !== p.name) throw new Refuse(400, 'confirm_required');
        await clearLocks(p.name);
        const del = await svc.auth.admin.deleteUser(id); // profile and save cascade
        if (del.error) throw del.error;
        return json({ ok: true });
      }
      case 'rotate_family_code': {
        for (let i = 0; i < 5; i++) {
          const c = newCode();
          const u = await svc.from('families').update({ code: c }).eq('parent_id', caller.id).select('code');
          if (!u.error) { if (!u.data?.length) throw new Refuse(404, 'not_found'); return json({ code: c }); }
          if (u.error.code !== '23505') throw u.error;
        }
        throw new Error('no family code');
      }
      case 'delete_account': {
        if (typeof body.confirm !== 'string' || body.confirm.trim().toLowerCase() !== caller.email.toLowerCase()) {
          throw new Refuse(400, 'confirm_required');
        }
        const kids = await svc.from('profiles').select('id, name').eq('parent_id', caller.id);
        if (kids.error) throw kids.error;
        // children first (their auth users do not cascade from the parent); a failure stops before the parent goes
        for (const k of kids.data ?? []) {
          await clearLocks(k.name);
          const d = await svc.auth.admin.deleteUser(k.id);
          if (d.error) throw d.error;
        }
        const d = await svc.auth.admin.deleteUser(caller.id); // families cascades
        if (d.error) throw d.error;
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
