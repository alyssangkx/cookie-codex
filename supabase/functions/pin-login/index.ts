// pin-login: the ONLY place a child's PIN is checked. Written for the Supabase Edge Runtime (Deno).
// SOURCE ONLY: nothing is deployed from this repo until the plan is approved (docs/accounts-plan.md).
//
// POST /functions/v1/pin-login   { name: string, pin: "dddd", deviceId: string }
//   200 { session: { access_token, refresh_token, expires_in, expires_at, token_type }, profile: { id, name } }
//   401 { error: "wrong_name_or_pin", attemptsLeft: number }     same body for an unknown name
//   429 { error: "locked", retryAfterSec: number }                see "Lockouts" below
//   400 { error: "bad_request" }
//
// Secrets (supabase secrets set ...): PIN_PEPPER, CHILD_PW_SECRET, optional SITE_ORIGIN.
// Provided by the platform: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY.
import { createClient } from 'npm:@supabase/supabase-js@2';
import { childPassword, DUMMY_HASH, verifyPin } from '../_shared/pin.ts';

// Lockouts (docs/accounts-plan.md section 5):
//   device: 5 wrong tries -> 15 minutes. The deviceId is chosen by the client, so this only stops a
//           well-behaved browser; an attacker simply sends a new id per request.
//   name:   20 wrong tries from anywhere -> lock, doubling each time it trips (15 min, 30 min, 1 h,
//           ... capped at 24 h), reset by a successful login. THIS is the real brute-force bound.
//   IP:     deliberately NOT limited. Supabase documents no client-IP header for Edge Functions that
//           a caller cannot forge: x-forwarded-for can be supplied by the caller (reported in
//           supabase/discussions/34647), and x-real-ip / cf-connecting-ip are not documented for
//           Edge Functions. A limit keyed on a forgeable value is worthless, and a shared 'unknown'
//           bucket would let anyone lock everyone out, so there is no IP limit.
// Worst-case guessing rate against one name, from any number of devices and addresses: 20 tries,
// then locks of 15m, 30m, 1h, 2h, 4h, 8h, 16h, 24h, 24h, ... So 160 guesses in about 2.3 days, then
// 20 per day: all 10,000 PINs take about 500 days, about 250 expected. Each guess also costs one
// 600,000-iteration PBKDF2. Unknown names get the same limits, so names cannot be probed freely.
// UNTESTED: needs a Supabase project (no Deno or Postgres on the dev machine).
const DEVICE_MAX = 5;
const DEVICE_LOCK = '15 minutes';
const NAME_MAX = 20;
const NAME_LOCK = '15 minutes';
const NAME_WINDOW = '24 hours';
const NAME_CAP = '24 hours';
const NAME_RE = /^[\p{L} -]{1,20}$/u; // 1-20 letters, spaces or hyphens; same rule as the profiles check
// Same normalisation as the profiles.name_key column: lower(btrim(name)). btrim trims spaces only.
const nameKey = (n: string) => n.replace(/^ +| +$/g, '').toLowerCase();

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
  const pin = typeof body.pin === 'string' ? body.pin : '';
  const deviceId = typeof body.deviceId === 'string' ? body.deviceId.slice(0, 64) : '';
  if (typeof body.name !== 'string' || !/^\d{4}$/.test(pin) || !deviceId) return json({ error: 'bad_request' }, 400);
  const key = nameKey(body.name.slice(0, 100));
  const validName = NAME_RE.test(key);

  const url = Deno.env.get('SUPABASE_URL')!;
  const admin = createClient(url, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!, { auth: { persistSession: false } });
  const pepper = Deno.env.get('PIN_PEPPER')!;

  const deviceKey = `device:${deviceId}`;
  const nameLockKey = `name:${key}`; // by name, so an unknown name locks exactly like a real one

  const recordDevice = () => admin.rpc('pin_record_failure', { p_key: deviceKey, p_max: DEVICE_MAX, p_lock: DEVICE_LOCK });

  // 1. Already locked? Answer before touching the PIN, and count nothing further.
  const lockKeys = validName ? [deviceKey, nameLockKey] : [deviceKey];
  const locks = await Promise.all(lockKeys.map((k) => admin.rpc('pin_locked_until', { p_key: k })));
  const until = latest(locks.map((r) => (r.data ? Date.parse(r.data as string) : 0)));
  if (until > Date.now()) return locked(until);

  // 2. A malformed name never reaches the database: it counts against the device and fails like a wrong PIN.
  if (!validName) {
    const r = (await recordDevice()).data as Fail[] | null;
    const lockedAt = r?.[0]?.locked_until ? Date.parse(r[0].locked_until) : 0;
    if (lockedAt > Date.now()) return locked(lockedAt);
    return json({ error: 'wrong_name_or_pin', attemptsLeft: Math.max(0, DEVICE_MAX - (r?.[0]?.fails ?? 0)) }, 401);
  }

  // 3. Exact lookup on the generated name_key column (never ilike/like). An unknown name still runs a full hash compare.
  const { data: prof } = await admin.from('profiles').select('id, name, pin_hash')
    .eq('role', 'child').eq('name_key', key).maybeSingle();
  const match = await verifyPin(pin, prof?.pin_hash ?? DUMMY_HASH, pepper);
  const ok = match && !!prof?.pin_hash;

  if (!ok) {
    const [dev, nm] = await Promise.all([
      recordDevice(),
      admin.rpc('pin_record_failure', {
        p_key: nameLockKey, p_max: NAME_MAX, p_lock: NAME_LOCK, p_window: NAME_WINDOW, p_escalate: true, p_cap: NAME_CAP,
      }),
    ]);
    const rows = [dev, nm].map((r) => (r.data as Fail[] | null)?.[0]);
    const lockedAt = latest(rows.map((r) => (r?.locked_until ? Date.parse(r.locked_until) : 0)));
    if (lockedAt > Date.now()) return locked(lockedAt);
    const left = Math.max(0, Math.min(DEVICE_MAX - (rows[0]?.fails ?? 0), NAME_MAX - (rows[1]?.fails ?? 0)));
    return json({ error: 'wrong_name_or_pin', attemptsLeft: left }, 401);
  }

  // 4. Success: reset this name (and its escalation) and device, then sign in as the child's own auth user.
  await admin.rpc('pin_clear', { p_keys: [deviceKey, nameLockKey] });
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
