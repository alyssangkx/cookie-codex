// pin-login: the ONLY place a child's PIN is checked. Written for the Supabase Edge Runtime (Deno).
// SOURCE ONLY: nothing is deployed from this repo until the plan is approved (docs/accounts-plan.md).
//
// POST /functions/v1/pin-login   { name: string, pin: "dddd", deviceId: string, deviceToken?: string }
//   200 { session: { access_token, refresh_token, expires_in, expires_at, token_type }, profile: { id, name }, deviceToken }
//   401 { error: "wrong_name_or_pin", attemptsLeft: number }   attemptsLeft = THIS device's own tries only; same body for an unknown name
//   429 { error: "locked" }                                      name lock (untrusted) or trusted-access lock for the name: no counts at all
//   429 { error: "locked", retryAfterSec: number }               this device's own lock
//   500 { error: "server_error" }                                 unexpected failure, e.g. an unparseable timestamp
//   503 { error: "try_again_later" }                             the lock RPC failed: fail closed, the PIN is not checked
//   400 { error: "bad_request" }
//
// Secrets (supabase secrets set ...): PIN_PEPPER, CHILD_PW_SECRET, PIN_DEVICE_SECRET, optional SITE_ORIGIN.
// Provided by the platform: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY.
import { createClient } from 'npm:@supabase/supabase-js@2';
import {
  childPassword, DUMMY_HASH, issueDeviceToken, tsMs, verifyDeviceToken, verifyPin,
} from '../_shared/pin.ts';

// Lockouts (docs/accounts-plan.md section 5). The limits live in SQL (public.pin_reserve_attempt); this
// file calls it ONCE per request with two keys. In one transaction with row locks it checks BOTH locks
// first (a locked key means nothing is counted at all), then counts BOTH, all before the PIN is checked,
// so concurrent requests can never exceed a limit. Every lock doubles each time it trips (15 min, 30 min,
// 1 h, 2 h, 4 h, 8 h, 16 h, then 24 h). Windows: the device fail count restarts after 15 quiet minutes; name and trust counts only after 24 h;
// escalation decays after 7 quiet days. Success clears the device and only the name-side key used.
//   device:  5 tries per lock. Applies to every request. The deviceId is chosen by the client, so alone
//            it only stops a well-behaved browser (or one copied token, which has one device id).
//   name:    20 tries, for requests WITHOUT a valid trusted-device token. The brute-force bound against a
//            stranger. A valid token skips it, so strangers cannot lock Alyssa's own devices out.
//   trust:   30 tries, for requests WITH a valid token (HMAC over child id, device id, issued-at and
//            pin_set_at; under 180 days old; void after a PIN reset). Bounds copied tokens.
//   IP:      deliberately NOT limited. Supabase documents no client-IP header for Edge Functions that
//            a caller cannot forge: x-forwarded-for can be supplied by the caller (reported in
//            supabase/discussions/34647), and x-real-ip / cf-connecting-ip are not documented for
//            Edge Functions. A limit keyed on a forgeable value is worthless, and a shared 'unknown'
//            bucket would let anyone lock everyone out, so there is no IP limit.
// Worst-case guessing rates. Method: the budgets are separate rows, so an attacker holding tokens can
// spend the untrusted (name) budget with forged device ids AND the trusted (trust) budget with the tokens
// at the same time. A device id is free to forge only on untrusted requests; a token is bound to its own
// device id. A batch is the tries before a key locks; the lock after batch k is 15 min * 2^(k-1), so
// batch 8 opens after 31.75 h, then one batch per 24 h.
//   name: and trust: fail counts reset only after 24 h with no failure, so pacing below the limit gains
//   nothing; device: resets after 15 quiet minutes (usability only; forgeable on untrusted requests).
//     (a) stranger, no token:      160 in the first 31.75 h, then 20 per day  -> ~240 days to 5,000 guesses
//     (b) one or many tokens:      160 + 240 = 400, then 20 + 30 = 50 per day -> ~92 days; a PIN reset voids tokens
// Order: profile lookup (exact name_key; dummy profile for an unknown name), token HMAC (always runs),
// then ONE reservation RPC for device + name/trust, then the PIN hash (always runs, dummy hash for an
// unknown name). A locked key is refused before the expensive hash. Fail closed: if the RPC or the clear
// errors, answer 503 without checking the PIN; a timestamp that does not parse answers 500.
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

  // The one lock RPC: an error or a malformed row throws, so nothing is read as "not locked".
  const reserve = async (nKey: string | null, trusted: boolean) => {
    const r = await admin.rpc('pin_reserve_attempt', { p_device_key: deviceKey, p_name_key: nKey, p_trusted: trusted });
    const row = (r.data as Reserve[] | null)?.[0];
    if (r.error || !row || typeof row.allowed !== 'boolean') throw new Unavailable();
    return row;
  };
  const deviceLocked = (untilMs: number) => {
    const retryAfterSec = Math.max(1, Math.ceil((untilMs - Date.now()) / 1000));
    return json({ error: 'locked', retryAfterSec }, 429, { 'retry-after': String(retryAfterSec) });
  };

  try {
    // 1. Exact lookup on the generated name_key column (never ilike/like). A malformed name never reaches the database.
    let real: { id: string; name: string; pin_hash: string | null; pin_set_at: string | null } | null = null;
    if (validName) {
      const r = await admin.from('profiles').select('id, name, pin_hash, pin_set_at').eq('role', 'child').eq('name_key', key).maybeSingle();
      if (r.error) throw new Unavailable();
      real = r.data;
    }
    const prof = real ?? DUMMY;
    const pinSetAt = tsMs(prof.pin_set_at); // throws on an unparseable timestamp: no token is signed or checked over NaN

    // 2. Token HMAC always runs, against the dummy profile for an unknown name.
    const tokenOk = await verifyDeviceToken(deviceSecret, body.deviceToken, prof.id, deviceId, pinSetAt);
    const trusted = !!real && tokenOk;

    // 3. ONE reservation for device + (name | trust), counted BEFORE the PIN is checked. Either lock
    //    held means nothing is counted. A malformed name has no name key: only the device is counted,
    //    and it still gets the full hash below and fails like a wrong PIN.
    const rs = await reserve(validName ? key : null, trusted);
    if (!rs.allowed) return rs.scope === 'device' ? deviceLocked(tsMs(rs.device_until)) : json({ error: 'locked' }, 429);
    const deviceUntil = tsMs(rs.device_until); // set when THIS attempt used the device's last try
    const nameUntil = tsMs(rs.name_until);     // likewise for the name / trust key
    const attemptsLeft = Math.max(0, rs.attempts_left ?? 0);

    // 5. PIN hash always runs (dummy hash for an unknown name or a profile without a PIN).
    const pinOk = await verifyPin(pin, prof.pin_hash ?? DUMMY_HASH, pepper);
    const match = !!real && !!real.pin_hash && pinOk;
    if (!match) {
      if (deviceUntil > Date.now()) return deviceLocked(deviceUntil);
      if (nameUntil > Date.now()) return json({ error: 'locked' }, 429);
      return json({ error: 'wrong_name_or_pin', attemptsLeft }, 401); // this device only
    }

    // 6. Success: reset this device and the name-side key this request used (trust: or name:), then sign in.
    const cleared = await admin.rpc('pin_clear', { p_device_key: deviceKey, p_name_key: key, p_trusted: trusted });
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
      deviceToken: await issueDeviceToken(deviceSecret, prof.id, deviceId, pinSetAt),
    });
  } catch (e) {
    if (e instanceof Unavailable) return json({ error: 'try_again_later' }, 503);
    console.error('pin-login failed', e); // visible in the function logs; never echoed to the client
    return json({ error: 'server_error' }, 500); // includes a timestamp that does not parse
  }
});
