// pin-login: the ONLY place a child's PIN is checked. Written for the Supabase Edge Runtime (Deno).
// SOURCE ONLY: nothing is deployed from this repo until the plan is approved (docs/accounts-plan.md).
//
// POST /functions/v1/pin-login   { name: string, pin: "dddd", deviceId: string }
//   200 { session: { access_token, refresh_token, expires_in, expires_at, token_type }, profile: { id, name } }
//   401 { error: "wrong_name_or_pin", attemptsLeft: number }     same body for an unknown name
//   429 { error: "locked", retryAfterSec: number }                15 minutes after 5 wrong tries
//   400 { error: "bad_request" }
//
// Secrets (supabase secrets set ...): PIN_PEPPER, CHILD_PW_SECRET, optional SITE_ORIGIN.
// Provided by the platform: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY.
import { createClient } from 'npm:@supabase/supabase-js@2';
import { childPassword, DUMMY_HASH, sha256Hex, verifyPin } from '../_shared/pin.ts';

const MAX_TRIES = 5;      // per device and per name
const MAX_IP_TRIES = 20;  // per network address: looser, because Wi-Fi is shared
const LOCK = '15 minutes';

const CORS = {
  'access-control-allow-origin': Deno.env.get('SITE_ORIGIN') ?? '*', // set SITE_ORIGIN to the real site in production
  'access-control-allow-headers': 'authorization, apikey, content-type',
  'access-control-allow-methods': 'POST, OPTIONS',
};
const json = (body: unknown, status = 200, extra: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), { status, headers: { ...CORS, 'content-type': 'application/json', ...extra } });

type Fail = { fails: number; locked_until: string | null };
const latest = (ms: (number | 0)[]) => ms.reduce((a, b) => Math.max(a, b), 0);

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null, { headers: CORS });
  if (req.method !== 'POST') return json({ error: 'bad_request' }, 405);

  let body: { name?: unknown; pin?: unknown; deviceId?: unknown };
  try { body = await req.json(); } catch { return json({ error: 'bad_request' }, 400); }
  const name = typeof body.name === 'string' ? body.name.trim().slice(0, 30) : '';
  const pin = typeof body.pin === 'string' ? body.pin : '';
  const deviceId = typeof body.deviceId === 'string' ? body.deviceId.slice(0, 64) : '';
  if (!name || !/^\d{4}$/.test(pin) || !deviceId) return json({ error: 'bad_request' }, 400);

  const url = Deno.env.get('SUPABASE_URL')!;
  const admin = createClient(url, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!, { auth: { persistSession: false } });
  const pepper = Deno.env.get('PIN_PEPPER')!;

  const ip = (req.headers.get('x-forwarded-for') ?? 'unknown').split(',')[0].trim();
  const keys = {
    device: `device:${deviceId}`,
    name: `name:${name.toLowerCase()}`, // by name, so an unknown name locks exactly like a real one
    ip: `ip:${await sha256Hex(ip)}`,    // hashed: no raw addresses stored
  };

  // 1. Already locked? Answer before touching the PIN, and count nothing further.
  const locks = await Promise.all(Object.values(keys).map((k) => admin.rpc('pin_locked_until', { p_key: k })));
  const until = latest(locks.map((r) => (r.data ? Date.parse(r.data as string) : 0)));
  if (until > Date.now()) return locked(until);

  // 2. Look up the child and compare the hash. An unknown name still runs a full hash compare.
  const escaped = name.replace(/[%_\\]/g, '\\$&'); // ilike without wildcards: exact, case-insensitive
  const { data: prof } = await admin.from('profiles').select('id, name, pin_hash')
    .eq('role', 'child').ilike('name', escaped).maybeSingle();
  const match = await verifyPin(pin, prof?.pin_hash ?? DUMMY_HASH, pepper);
  const ok = match && !!prof?.pin_hash;

  if (!ok) {
    const results = await Promise.all([
      admin.rpc('pin_record_failure', { p_key: keys.device, p_max: MAX_TRIES, p_lock: LOCK }),
      admin.rpc('pin_record_failure', { p_key: keys.name, p_max: MAX_TRIES, p_lock: LOCK }),
      admin.rpc('pin_record_failure', { p_key: keys.ip, p_max: MAX_IP_TRIES, p_lock: LOCK }),
    ]);
    const rows = results.map((r) => (r.data as Fail[] | null)?.[0]);
    const lockedAt = latest(rows.map((r) => (r?.locked_until ? Date.parse(r.locked_until) : 0)));
    if (lockedAt > Date.now()) return locked(lockedAt);
    const left = Math.max(0, MAX_TRIES - Math.max(rows[0]?.fails ?? 0, rows[1]?.fails ?? 0));
    return json({ error: 'wrong_name_or_pin', attemptsLeft: left }, 401);
  }

  // 3. Success: reset this name and device, then sign in as the child's own auth user.
  await admin.rpc('pin_clear', { p_keys: [keys.device, keys.name] });
  const anon = createClient(url, Deno.env.get('SUPABASE_ANON_KEY')!, { auth: { persistSession: false } });
  const { data, error } = await anon.auth.signInWithPassword({
    email: `child-${prof!.id}@children.invalid`, // synthetic address: no real email is ever collected for a child
    password: await childPassword(prof!.id, Deno.env.get('CHILD_PW_SECRET')!),
  });
  if (error || !data.session) return json({ error: 'server_error' }, 500);
  const { access_token, refresh_token, expires_in, expires_at, token_type } = data.session;
  return json({
    session: { access_token, refresh_token, expires_in, expires_at, token_type },
    profile: { id: prof!.id, name: prof!.name },
  });
});

function locked(untilMs: number) {
  const retryAfterSec = Math.max(1, Math.ceil((untilMs - Date.now()) / 1000));
  return json({ error: 'locked', retryAfterSec }, 429, { 'retry-after': String(retryAfterSec) });
}
