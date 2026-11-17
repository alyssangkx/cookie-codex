// pin-login: the ONLY place a child's PIN is checked. Written for the Supabase Edge Runtime (Deno).
// SOURCE ONLY: nothing is deployed from this repo until the plan is approved (docs/accounts-plan.md).
//
// POST /functions/v1/pin-login   { name: string, pin: "dddd", deviceId: string, deviceToken?: string }
//   200 { session: { access_token, refresh_token, expires_in, expires_at, token_type }, profile: { id, name }, deviceToken }
//   401 { error: "wrong_name_or_pin", attemptsLeft: number }   attemptsLeft = THIS device's own tries only; same body for an unknown name
//   429 { error: "locked" }                                      name lock (untrusted) or trusted-access lock for the name: no counts at all
//   429 { error: "locked", retryAfterSec: number }               this device's own lock
//   503 { error: "try_again_later" }                             a lock RPC failed: fail closed, the PIN is not checked
//   400 { error: "bad_request" }
//
// Secrets (supabase secrets set ...): PIN_PEPPER, CHILD_PW_SECRET, PIN_DEVICE_SECRET, optional SITE_ORIGIN.
// Provided by the platform: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY.
import { createClient } from 'npm:@supabase/supabase-js@2';
import {
  childPassword, DUMMY_HASH, issueDeviceToken, pinSetAtMs, verifyDeviceToken, verifyPin,
} from '../_shared/pin.ts';

// Lockouts (docs/accounts-plan.md section 5). The limits live in SQL (public.pin_reserve_attempt); this
// file only calls it. Each attempt is RESERVED (counted) before the PIN is checked, atomically under
// row locks, so concurrent requests can never exceed a limit. Every lock doubles each time it trips
// (15 min, 30 min, 1 h, 2 h, 4 h, 8 h, 16 h, then 24 h) and resets on a successful login.
//   device:  5 wrong tries per lock. Applies to every request. The deviceId is chosen by the client,
//            so alone it only stops a well-behaved browser (or one copied token, which has one device id).
//   name:    20 tries from requests WITHOUT a valid trusted-device token. THIS is the real brute-force
//            bound against a stranger. A valid token skips it, so strangers cannot lock Alyssa's own
//            devices out.
//   trust:   30 tries from requests WITH a valid token (HMAC over child id, device id, issued-at and
//            pin_set_at; under 180 days old; void after a PIN reset). Bounds a copied token, or many.
//   IP:      deliberately NOT limited. Supabase documents no client-IP header for Edge Functions that
//            a caller cannot forge: x-forwarded-for can be supplied by the caller (reported in
//            supabase/discussions/34647), and x-real-ip / cf-connecting-ip are not documented for
//            Edge Functions. A limit keyed on a forgeable value is worthless, and a shared 'unknown'
//            bucket would let anyone lock everyone out, so there is no IP limit.
// Worst-case guessing rates (the lock after batch k is 15 min * 2^(k-1); batch 8 opens after 31.75 h):
//   untrusted attacker, forging every device id: name limit only: 20 tries per batch, 160 guesses in
//     31.75 h, then 20 per day (24 h lock). 10,000 PINs take about 500 days (about 250 expected).
//   one copied token (one device id): device limit binds: 5 per batch, 40 in 31.75 h, then 5 per day.
//   many copied tokens (each its own device id): trust limit binds: 30 per batch, 240 in 31.75 h, then
//     30 per day (about 330 days for all 10,000). Resetting the PIN voids every token at once.
// Order: device reservation first (one cheap RPC, before any profile lookup); then the profile lookup;
// then token HMAC and PIN hash ALWAYS run (dummy profile for an unknown name) so timing does not reveal
// whether a name exists; the name/trust reservation sits between the token check and the PIN check.
// Fail closed: if any reservation or clear RPC errors, answer 503 without checking the PIN.
// UNTESTED: needs a Supabase project (no Deno or Postgres on the dev machine).
const NAME_RE = /^[A-Za-z][A-Za-z -]{0,19}$/; // ASCII only for now; same rule as the profiles check
// Same normalisation as profiles.name_key = lower(btrim(name)). Non-ASCII names later need NFC
// normalisation on both sides.
const nameKey = (n: string) => n.trim().toLowerCase();

const CORS = {
  'access-control-allow-origin': Deno.env.get('SITE_ORIGIN') ?? '*', // set SITE_ORIGIN to the real site in production
  'access-control-allow-headers': 'authorization, apikey, content-type',
  'access-control-allow-methods': 'POST, OPTIONS',
};
const json = (body: unknown, status = 200, extra: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), { status, headers: { ...CORS, 'content-type': 'application/json', ...extra } });

type Reserve = {
  allowed: boolean; scope: 'device' | 'name' | null;
  device_until: string | null; name_until: string | null; attempts_left: number | null;
};
class Unavailable extends Error {}
const ms = (v: string | null | undefined) => (v ? Date.parse(v) : 0);

// A profile for names that do not exist (or are malformed): same work, never matches.
const DUMMY = { id: '00000000-0000-0000-0000-000000000000', name: '', pin_hash: DUMMY_HASH as string | null, pin_set_at: null as string | null };

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null, { headers: CORS });
  if (req.method !== 'POST') return json({ error: 'bad_request' }, 405);

  let body: { name?: unknown; pin?: unknown; deviceId?: unknown; deviceToken?: unknown };
  try { body = await req.json(); } catch { return json({ error: 'bad_request' }, 400); }
  const pin = typeof body.pin === 'string' ? body.pin : '';
  const deviceId = typeof body.deviceId === 'string' ? body.deviceId.slice(0, 64) : '';
  if (typeof body.name !== 'string' || !/^\d{4}$/.test(pin) || !deviceId) return json({ error: 'bad_request' }, 400);
  const key = nameKey(body.name.slice(0, 100));
  const validName = NAME_RE.test(key);

  const url = Deno.env.get('SUPABASE_URL')!;
  const admin = createClient(url, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!, { auth: { persistSession: false } });
  const pepper = Deno.env.get('PIN_PEPPER')!;
  const deviceSecret = Deno.env.get('PIN_DEVICE_SECRET');
  if (!deviceSecret) return json({ error: 'server_error' }, 500); // never fall back to a built-in secret

  const deviceKey = `device:${deviceId}`;

  // Every lock RPC goes through here: an error or a malformed row throws, so nothing is read as "not locked".
  const reserve = async (devKey: string | null, nKey: string | null, trusted: boolean) => {
    const r = await admin.rpc('pin_reserve_attempt', { p_device_key: devKey, p_name_key: nKey, p_trusted: trusted });
    const row = (r.data as Reserve[] | null)?.[0];
    if (r.error || !row || typeof row.allowed !== 'boolean') throw new Unavailable();
    return row;
  };
  const deviceLocked = (untilMs: number) => {
    const retryAfterSec = Math.max(1, Math.ceil((untilMs - Date.now()) / 1000));
    return json({ error: 'locked', retryAfterSec }, 429, { 'retry-after': String(retryAfterSec) });
  };

  try {
    // 1. Device first: one cheap RPC, before any profile lookup. A locked device counts nothing further.
    const dev = await reserve(deviceKey, null, false);
    if (!dev.allowed) return deviceLocked(ms(dev.device_until));
    const deviceUntil = ms(dev.device_until); // set when THIS attempt used the last try
    const attemptsLeft = Math.max(0, dev.attempts_left ?? 0);
    const wrong = () => deviceUntil > Date.now()
      ? deviceLocked(deviceUntil)
      : json({ error: 'wrong_name_or_pin', attemptsLeft }, 401); // this device only

    // 2. Exact lookup on the generated name_key column (never ilike/like). A malformed name never reaches the database.
    let real: { id: string; name: string; pin_hash: string | null; pin_set_at: string | null } | null = null;
    if (validName) {
      const r = await admin.from('profiles').select('id, name, pin_hash, pin_set_at').eq('role', 'child').eq('name_key', key).maybeSingle();
      if (r.error) throw new Unavailable();
      real = r.data;
    }
    const prof = real ?? DUMMY;

    // 3. Token HMAC always runs, against the dummy profile for an unknown name.
    const tokenOk = await verifyDeviceToken(deviceSecret, body.deviceToken, prof.id, deviceId, pinSetAtMs(prof.pin_set_at));
    const trusted = !!real && tokenOk;

    // 4. Name (untrusted) or trusted-name reservation: counted BEFORE the PIN is checked. A malformed
    //    name has no name key; it still gets the full hash below and fails like a wrong PIN.
    let nameUntil = 0;
    if (validName) {
      const nm = await reserve(null, key, trusted);
      if (!nm.allowed) return json({ error: 'locked' }, 429);
      nameUntil = ms(nm.name_until);
    }

    // 5. PIN hash always runs (dummy hash for an unknown name or a profile without a PIN).
    const pinOk = await verifyPin(pin, prof.pin_hash ?? DUMMY_HASH, pepper);
    const match = !!real && !!real.pin_hash && pinOk;
    if (!match) return nameUntil > Date.now() ? json({ error: 'locked' }, 429) : wrong();

    // 6. Success: reset the counters this request used, then sign in as the child's own auth user.
    const cleared = await admin.rpc('pin_clear', { p_keys: [deviceKey, `${trusted ? 'trust' : 'name'}:${key}`] });
    if (cleared.error) throw new Unavailable();
    const anon = createClient(url, Deno.env.get('SUPABASE_ANON_KEY')!, { auth: { persistSession: false } });
    const { data, error } = await anon.auth.signInWithPassword({
      email: `child-${prof.id}@children.invalid`, // synthetic address: no real email is ever collected for a child
      password: await childPassword(prof.id, Deno.env.get('CHILD_PW_SECRET')!),
    });
    if (error || !data.session) return json({ error: 'server_error' }, 500);
    const { access_token, refresh_token, expires_in, expires_at, token_type } = data.session;
    return json({
      session: { access_token, refresh_token, expires_in, expires_at, token_type },
      profile: { id: prof.id, name: prof.name },
      // bound to pin_set_at: a later PIN reset voids it. The client keeps it in localStorage next to its device id.
      deviceToken: await issueDeviceToken(deviceSecret, prof.id, deviceId, pinSetAtMs(prof.pin_set_at)),
    });
  } catch (e) {
    if (e instanceof Unavailable) return json({ error: 'try_again_later' }, 503);
    throw e;
  }
});
