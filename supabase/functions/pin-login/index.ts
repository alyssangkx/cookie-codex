// pin-login: the ONLY place a child's PIN is checked. Written for the Supabase Edge Runtime (Deno).
// SOURCE ONLY: nothing is deployed from this repo until the plan is approved (docs/accounts-plan.md).
//
// POST /functions/v1/pin-login   { name: string, pin: "dddd", deviceId: string, deviceToken?: string }
//   200 { session: { access_token, refresh_token, expires_in, expires_at, token_type }, profile: { id, name }, deviceToken }
//   401 { error: "wrong_name_or_pin", attemptsLeft: number }   attemptsLeft = THIS device's own tries only; same body for an unknown name
//   429 { error: "locked" }                                      name lock for an untrusted device: no counts at all
//   429 { error: "locked", retryAfterSec: number }               this device's own lock
//   503 { error: "try_again_later" }                             a lock RPC failed: fail closed, the PIN is not checked
//   400 { error: "bad_request" }
//
// Secrets (supabase secrets set ...): PIN_PEPPER, CHILD_PW_SECRET, PIN_DEVICE_SECRET, optional SITE_ORIGIN.
// Provided by the platform: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY.
import { createClient } from 'npm:@supabase/supabase-js@2';
import { childPassword, DUMMY_HASH, issueDeviceToken, verifyDeviceToken, verifyPin } from '../_shared/pin.ts';

// Lockouts (docs/accounts-plan.md section 5):
//   device: 5 wrong tries -> 15 minutes. Applies to every request, trusted or not. The deviceId is
//           chosen by the client, so alone it only stops a well-behaved browser.
//   name:   20 wrong tries from untrusted requests -> lock, doubling each time it trips (15 min,
//           30 min, 1 h, ... capped at 24 h), reset by a successful login. THIS is the real
//           brute-force bound. A request carrying a valid trusted-device token (HMAC over child id,
//           device id, issued-at; under 180 days old) skips this lock, so strangers cannot lock
//           Alyssa's own devices out; it is still bound by the device limit.
//   IP:     deliberately NOT limited. Supabase documents no client-IP header for Edge Functions that
//           a caller cannot forge: x-forwarded-for can be supplied by the caller (reported in
//           supabase/discussions/34647), and x-real-ip / cf-connecting-ip are not documented for
//           Edge Functions. A limit keyed on a forgeable value is worthless, and a shared 'unknown'
//           bucket would let anyone lock everyone out, so there is no IP limit.
// Worst-case guessing rate against one name from untrusted requests: 20 tries, then locks of 15m, 30m,
// 1h, 2h, 4h, 8h, 16h, 24h, 24h, ... So 160 guesses in about 2.3 days, then 20 per day.
// Fail closed: if any lock or failure-recording RPC errors, answer 503 without checking the PIN.
// UNTESTED: needs a Supabase project (no Deno or Postgres on the dev machine).
const DEVICE_MAX = 5;
const DEVICE_LOCK = '15 minutes';
const NAME_MAX = 20;
const NAME_LOCK = '15 minutes';
const NAME_WINDOW = '24 hours';
const NAME_CAP = '24 hours';
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

type Fail = { fails: number; locked_until: string | null };
class Unavailable extends Error {}
const ms = (v: string | null | undefined) => (v ? Date.parse(v) : 0);

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
  const nameLockKey = `name:${key}`; // by name, so an unknown name locks exactly like a real one

  // Every lock RPC goes through here: an error or a missing row throws, so nothing is read as 0 failures.
  const lockedUntil = async (k: string) => {
    const r = await admin.rpc('pin_locked_until', { p_key: k });
    if (r.error) throw new Unavailable();
    return ms(r.data as string | null); // null is a real answer here: not locked
  };
  const recordFailure = async (args: Record<string, unknown>) => {
    const r = await admin.rpc('pin_record_failure', args);
    const row = (r.data as Fail[] | null)?.[0];
    if (r.error || !row || typeof row.fails !== 'number') throw new Unavailable();
    return { fails: row.fails, until: ms(row.locked_until) };
  };
  const recordDevice = () => recordFailure({ p_key: deviceKey, p_max: DEVICE_MAX, p_lock: DEVICE_LOCK });
  const recordName = () => recordFailure({
    p_key: nameLockKey, p_max: NAME_MAX, p_lock: NAME_LOCK, p_window: NAME_WINDOW, p_escalate: true, p_cap: NAME_CAP,
  });
  const wrong = (deviceFails: number) =>
    json({ error: 'wrong_name_or_pin', attemptsLeft: Math.max(0, DEVICE_MAX - deviceFails) }, 401); // this device only

  try {
    // 1. Exact lookup on the generated name_key column (never ilike/like). A malformed name never reaches the database.
    let prof: { id: string; name: string; pin_hash: string | null } | null = null;
    if (validName) {
      const r = await admin.from('profiles').select('id, name, pin_hash').eq('role', 'child').eq('name_key', key).maybeSingle();
      if (r.error) throw new Unavailable();
      prof = r.data;
    }
    const trusted = !!prof && await verifyDeviceToken(deviceSecret, body.deviceToken, prof.id, deviceId);

    // 2. Already locked? Answer before touching the PIN, and count nothing further.
    const deviceUntil = await lockedUntil(deviceKey);
    if (deviceUntil > Date.now()) return deviceLocked(deviceUntil);
    if (validName && !trusted && (await lockedUntil(nameLockKey)) > Date.now()) return json({ error: 'locked' }, 429);

    // 3. A malformed name counts against the device and fails like a wrong PIN.
    if (!validName) {
      const d = await recordDevice();
      return d.until > Date.now() ? deviceLocked(d.until) : wrong(d.fails);
    }

    // 4. Compare. An unknown name still runs a full hash compare so timing does not reveal it.
    const match = await verifyPin(pin, prof?.pin_hash ?? DUMMY_HASH, pepper);
    if (!(match && !!prof?.pin_hash)) {
      // A trusted request is bound by its device limit only; it does not feed the name lock.
      const [d, n] = await Promise.all([recordDevice(), trusted ? Promise.resolve(null) : recordName()]);
      if (d.until > Date.now()) return deviceLocked(d.until);
      if (n && n.until > Date.now()) return json({ error: 'locked' }, 429);
      return wrong(d.fails);
    }

    // 5. Success: reset this name (and its escalation) and device, then sign in as the child's own auth user.
    const cleared = await admin.rpc('pin_clear', { p_keys: [deviceKey, nameLockKey] });
    if (cleared.error) throw new Unavailable();
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
      deviceToken: await issueDeviceToken(deviceSecret, prof!.id, deviceId), // the client keeps it in localStorage next to its device id
    });
  } catch (e) {
    if (e instanceof Unavailable) return json({ error: 'try_again_later' }, 503);
    throw e;
  }
});

function deviceLocked(untilMs: number) {
  const retryAfterSec = Math.max(1, Math.ceil((untilMs - Date.now()) / 1000));
  return json({ error: 'locked', retryAfterSec }, 429, { 'retry-after': String(retryAfterSec) });
}
