// admin: the grown-up's tool for children, PINs and the Test Player. Written for the Supabase Edge Runtime (Deno).
// Deploy WITH JWT verification (the default): the gateway rejects a missing or forged token, and this
// function checks the caller again. Never use --no-verify-jwt for this function.
//
// POST /functions/v1/admin  { action, ...args }   Authorization: Bearer <admin session access token>
// The caller must be a signed-in user whose app_metadata.role is 'admin' (read from the Auth server, not
// from the client) AND whose token says aal2 (the authenticator code was verified in this session).
//   create_child         { name }                    -> { child: { id, name, role } }
//   set_pin              { child_id, pin: "dddd" }   -> { ok: true }   (sets pin_set_at, which voids device tokens)
//   clear_name_lock      { child_id }                -> { ok: true }
//   list_children        {}                          -> { children: [{ id, name, role, pin_set_at, created_at }] }  (never pin_hash)
//   create_test_player   {}                          -> { child, pin }  the random PIN is returned ONCE
//   test_login           { child_id }                -> { session, profile }  a session for the Test Player only
//   delete_child         { child_id, confirm? }      -> { ok: true }   anything but a 'test' profile needs confirm = its name
// Errors: 401 unauthorized, 403 forbidden / mfa_required, 400 bad_request, 404 not_found, 409 name_taken|exists,
// 500 server_error (any unexpected failure: fail closed, nothing is half-reported as success).
//
// Secrets: PIN_PEPPER, CHILD_PW_SECRET (the same ones pin-login uses), optional SITE_ORIGIN.
// Provided by the platform: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY.
import { createClient } from 'npm:@supabase/supabase-js@2';
import { childPassword, hashPin } from '../_shared/pin.ts';

const NAME_RE = /^[A-Za-z][A-Za-z -]{0,19}$/; // same rule as profiles.name and pin-login
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const nameKey = (n: string) => n.trim().toLowerCase();

const CORS = {
  'access-control-allow-origin': Deno.env.get('SITE_ORIGIN') ?? '*',
  'access-control-allow-headers': 'authorization, apikey, content-type, x-client-info',
  'access-control-allow-methods': 'POST, OPTIONS',
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...CORS, 'content-type': 'application/json' } });

class Refuse extends Error {
  constructor(public status: number, public code: string) { super(code); }
}

/** The aal claim of an access token. Only read AFTER auth.getUser has validated the token with the Auth server. */
function aalOf(token: string): string {
  const part = token.split('.')[1];
  if (!part) return '';
  const pad = '='.repeat((4 - (part.length % 4)) % 4);
  const payload = JSON.parse(atob(part.replace(/-/g, '+').replace(/_/g, '/') + pad));
  return typeof payload?.aal === 'string' ? payload.aal : '';
}

const randomPin = () => {
  const n = crypto.getRandomValues(new Uint32Array(1))[0] % 10000;
  return String(n).padStart(4, '0');
};

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null, { headers: CORS });
  if (req.method !== 'POST') return json({ error: 'bad_request' }, 405);
  try {
    const url = Deno.env.get('SUPABASE_URL')!;
    const anonKey = Deno.env.get('SUPABASE_ANON_KEY')!;
    const pepper = Deno.env.get('PIN_PEPPER');
    const pwSecret = Deno.env.get('CHILD_PW_SECRET');
    if (!url || !anonKey || !pepper || !pwSecret || !Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')) throw new Error('missing configuration');

    // ---- who is calling: validated by the Auth server, then admin + aal2 or nothing
    const token = (req.headers.get('authorization') ?? '').replace(/^Bearer\s+/i, '');
    if (!token) throw new Refuse(401, 'unauthorized');
    const svc = createClient(url, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!, { auth: { persistSession: false } });
    const who = await svc.auth.getUser(token);
    const caller = who.data?.user;
    if (who.error || !caller) throw new Refuse(401, 'unauthorized');
    if (caller.app_metadata?.role !== 'admin') throw new Refuse(403, 'forbidden');
    if (aalOf(token) !== 'aal2') throw new Refuse(403, 'mfa_required');

    let body: Record<string, unknown>;
    try { body = await req.json(); } catch { throw new Refuse(400, 'bad_request'); }
    if (!body || typeof body !== 'object') throw new Refuse(400, 'bad_request');
    const childId = () => {
      if (typeof body.child_id !== 'string' || !UUID_RE.test(body.child_id)) throw new Refuse(400, 'bad_request');
      return body.child_id.toLowerCase();
    };
    const profileOf = async (id: string) => {
      const r = await svc.from('profiles').select('id, name, role').eq('id', id).maybeSingle();
      if (r.error) throw r.error;
      if (!r.data) throw new Refuse(404, 'not_found');
      return r.data as { id: string; name: string; role: 'child' | 'test' };
    };
    const setPin = async (id: string, pin: string) => {
      const r = await svc.from('profiles').update({ pin_hash: await hashPin(pin, pepper) }).eq('id', id).select('id');
      if (r.error || !r.data?.length) throw r.error ?? new Error('pin not stored');
    };
    // an auth user + profile. The email and password both depend on the user id, so the user is created
    // first with throwaway values, then switched to the synthetic address and derived password pin-login uses.
    const makeChild = async (name: string, role: 'child' | 'test') => {
      const created = await svc.auth.admin.createUser({
        email: `new-${crypto.randomUUID()}@children.invalid`,
        password: crypto.randomUUID() + crypto.randomUUID(),
        email_confirm: true,
      });
      const id = created.data?.user?.id;
      if (created.error || !id) throw created.error ?? new Error('no user');
      try {
        const fixed = await svc.auth.admin.updateUserById(id, {
          email: `child-${id}@children.invalid`, password: await childPassword(id, pwSecret), email_confirm: true,
        });
        if (fixed.error) throw fixed.error;
        const ins = await svc.from('profiles').insert({ id, parent_id: caller.id, name, role });
        if (ins.error) throw ins.error;
      } catch (e) {
        await svc.auth.admin.deleteUser(id); // roll back: no orphan auth user
        throw e;
      }
      return { id, name, role };
    };

    switch (body.action) {
      case 'create_child': {
        if (typeof body.name !== 'string') throw new Refuse(400, 'bad_request');
        const name = body.name.trim();
        if (!NAME_RE.test(name)) throw new Refuse(400, 'bad_request');
        const dup = await svc.from('profiles').select('id').eq('role', 'child').eq('name_key', nameKey(name)).maybeSingle();
        if (dup.error) throw dup.error;
        if (dup.data) throw new Refuse(409, 'name_taken');
        return json({ child: await makeChild(name, 'child') });
      }
      case 'set_pin': {
        const id = childId();
        if (typeof body.pin !== 'string' || !/^\d{4}$/.test(body.pin)) throw new Refuse(400, 'bad_request');
        await profileOf(id);
        await setPin(id, body.pin);
        return json({ ok: true });
      }
      case 'clear_name_lock': {
        const id = childId();
        await profileOf(id);
        // pin_clear_name_lock checks the admin role from the caller's own JWT, so call it as the caller
        const as = createClient(url, anonKey, { auth: { persistSession: false }, global: { headers: { Authorization: `Bearer ${token}` } } });
        const r = await as.rpc('pin_clear_name_lock', { p_child: id });
        if (r.error) throw r.error;
        return json({ ok: true });
      }
      case 'list_children': {
        const r = await svc.from('profiles').select('id, name, role, pin_set_at, created_at').order('created_at');
        if (r.error) throw r.error;
        return json({ children: r.data });
      }
      case 'create_test_player': {
        const have = await svc.from('profiles').select('id').eq('role', 'test').eq('parent_id', caller.id).limit(1);
        if (have.error) throw have.error;
        if (have.data?.length) throw new Refuse(409, 'exists');
        const child = await makeChild('Test Player', 'test');
        const pin = randomPin();
        try { await setPin(child.id, pin); } catch (e) { await svc.auth.admin.deleteUser(child.id); throw e; }
        return json({ child, pin }); // the only time this PIN exists in clear text
      }
      case 'test_login': {
        const id = childId();
        const p = await profileOf(id);
        if (p.role !== 'test') throw new Refuse(403, 'forbidden'); // never a session for a real child
        const anon = createClient(url, anonKey, { auth: { persistSession: false } });
        const { data, error } = await anon.auth.signInWithPassword({
          email: `child-${id}@children.invalid`, password: await childPassword(id, pwSecret),
        });
        if (error || !data.session) throw error ?? new Error('no session');
        const { access_token, refresh_token, expires_in, expires_at, token_type } = data.session;
        return json({ session: { access_token, refresh_token, expires_in, expires_at, token_type }, profile: { id, name: p.name } });
      }
      case 'delete_child': {
        const id = childId();
        const p = await profileOf(id);
        if (p.role !== 'test' && body.confirm !== p.name) throw new Refuse(400, 'confirm_required');
        const del = await svc.auth.admin.deleteUser(id); // profiles and saves cascade
        if (del.error) throw del.error;
        for (const trusted of [false, true]) await svc.rpc('pin_clear', { p_device_key: '', p_name_key: nameKey(p.name), p_trusted: trusted });
        return json({ ok: true });
      }
      default:
        throw new Refuse(400, 'bad_request');
    }
  } catch (e) {
    if (e instanceof Refuse) return json({ error: e.code }, e.status);
    console.error('admin failed', e instanceof Error ? e.message : 'unknown'); // never echo details to the client
    return json({ error: 'server_error' }, 500);
  }
});
