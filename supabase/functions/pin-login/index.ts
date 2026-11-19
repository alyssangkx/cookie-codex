// Child PIN login, family version (docs/accounts-plan.md sections 5 and 12). NOT YET DEPLOYED: it needs
// migration 002 (families, family-scoped lock keys), so deploy it right after 002 is applied, never before.
// The previous version is in git history (commit before "Parent sign-up").
//
// Differences from the previous pin-login:
//   * input gains familyCode (8 symbols, hyphen/spaces/case ignored) and captchaToken;
//   * the profile is looked up inside the family (families.code -> parent_id, then parent_id + name_key);
//   * lockout keys are '<parent_id>:<name_key>' (name: / trust:), so the same first name in two families
//     never shares a lock, and a stranger needs the family code to lock anyone (audit F1, F5);
//   * an UNTRUSTED request (no valid device token) must carry a CAPTCHA token, checked after the cheap
//     steps and BEFORE the lock RPC and the 600,000-iteration hash (audit F4). A trusted device skips it.
//     Off unless CAPTCHA_REQUIRED=true. A failed CAPTCHA counts nothing against any lock;
//   * unknown family code behaves like a malformed name: only the device is counted, the full hash still
//     runs, the answer is the same wrong_name_or_pin;
//   * CORS fails closed when SITE_ORIGIN is unset (audit F14);
//   * a child or family marked deleted (7-day undo) is treated as unknown: same answer, same work.
// Errors added: 400 { error: 'captcha_failed' }, 503 try_again_later also when the CAPTCHA provider is down.
// Secrets: PIN_PEPPER, CHILD_PW_SECRET, PIN_DEVICE_SECRET, SITE_ORIGIN, CAPTCHA_SECRET (+ CAPTCHA_REQUIRED).
// The lockout limits, windows and escalation are unchanged (docs section 5): they live in SQL.
import { createClient } from 'npm:@supabase/supabase-js@2';
import {
  childPassword, DUMMY_HASH, issueDeviceToken, tsMs, verifyDeviceToken, verifyPin,
} from '../_shared/pin.ts';
import { captchaRequired, CaptchaUnavailable, verifyCaptcha } from '../_shared/captcha.ts';
import { CODE_RE, lockKey as familyLockKey, normaliseCode } from '../_shared/family.ts';

const NAME_RE = /^[A-Za-z][A-Za-z -]{0,19}$/;
const nameKey = (n: string) => n.trim().toLowerCase();

const ORIGIN = Deno.env.get('SITE_ORIGIN');
const CORS: Record<string, string> = {
  ...(ORIGIN ? { 'access-control-allow-origin': ORIGIN } : {}), // unset: no header, browsers refuse
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

const DUMMY = { id: '00000000-0000-0000-0000-000000000000', name: '', pin_hash: DUMMY_HASH as string | null, pin_set_at: null as string | null };

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null, { headers: CORS });
  if (req.method !== 'POST') return json({ error: 'bad_request' }, 405);

  let body: { familyCode?: unknown; name?: unknown; pin?: unknown; deviceId?: unknown; deviceToken?: unknown; captchaToken?: unknown };
  try { body = await req.json(); } catch { return json({ error: 'bad_request' }, 400); }
  const pin = typeof body.pin === 'string' ? body.pin : '';
  const deviceId = typeof body.deviceId === 'string' ? body.deviceId.slice(0, 64) : '';
  if (typeof body.name !== 'string' || typeof body.familyCode !== 'string' || !/^\d{4}$/.test(pin) || !deviceId) {
    return json({ error: 'bad_request' }, 400);
  }
  const key = nameKey(body.name.slice(0, 100));
  const code = normaliseCode(body.familyCode.slice(0, 40));
  const validName = NAME_RE.test(key);
  const validCode = CODE_RE.test(code);

  const url = Deno.env.get('SUPABASE_URL')!;
  const admin = createClient(url, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!, { auth: { persistSession: false } });
  const pepper = Deno.env.get('PIN_PEPPER')!;
  const deviceSecret = Deno.env.get('PIN_DEVICE_SECRET');
  if (!deviceSecret) return json({ error: 'server_error' }, 500);

  const deviceKey = `device:${deviceId}`;
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
    // 1. Family by exact code, then the child by exact (parent_id, name_key). Malformed input never reaches the database.
    let parentId: string | null = null;
    if (validCode) {
      const f = await admin.from('families').select('parent_id, deleted_at').eq('code', code).maybeSingle();
      if (f.error) throw new Unavailable();
      parentId = f.data && !f.data.deleted_at ? f.data.parent_id : null;
    }
    let real: { id: string; name: string; pin_hash: string | null; pin_set_at: string | null; unlimited?: boolean } | null = null;
    if (validName && parentId) {
      const r = await admin.from('profiles').select('id, name, pin_hash, pin_set_at, unlimited, deleted_at')
        .eq('role', 'child').eq('parent_id', parentId).eq('name_key', key).maybeSingle();
      if (r.error) throw new Unavailable();
      real = r.data && !r.data.deleted_at ? r.data : null;
    }
    const prof = real ?? DUMMY;
    const pinSetAt = tsMs(prof.pin_set_at);

    // 2. Token HMAC always runs.
    const tokenOk = await verifyDeviceToken(deviceSecret, body.deviceToken, prof.id, deviceId, pinSetAt);
    const trusted = !!real && tokenOk;

    // 2b. CAPTCHA for untrusted requests, before anything is counted and before the hash.
    if (!trusted && captchaRequired()) {
      if (!(await verifyCaptcha(body.captchaToken))) return json({ error: 'captcha_failed' }, 400);
    }

    // 3. ONE reservation. The lock key carries the family: '<parent_id>:<name_key>'. No family or bad name:
    //    only the device is counted.
    const lockKey = validName && parentId ? familyLockKey(parentId, key) : null;
    const rs = await reserve(lockKey, trusted);
    if (!rs.allowed) return rs.scope === 'device' ? deviceLocked(tsMs(rs.device_until)) : json({ error: 'locked' }, 429);
    const deviceUntil = tsMs(rs.device_until);
    const nameUntil = tsMs(rs.name_until);
    const attemptsLeft = Math.max(0, rs.attempts_left ?? 0);

    // 4. PIN hash always runs.
    const pinOk = await verifyPin(pin, prof.pin_hash ?? DUMMY_HASH, pepper);
    const match = !!real && !!real.pin_hash && pinOk;
    if (!match) {
      if (deviceUntil > Date.now()) return deviceLocked(deviceUntil);
      if (nameUntil > Date.now()) return json({ error: 'locked' }, 429);
      return json({ error: 'wrong_name_or_pin', attemptsLeft }, 401);
    }

    // 5. Success: clear this device and the name-side key this request used.
    const cleared = await admin.rpc('pin_clear', { p_device_key: deviceKey, p_name_key: lockKey, p_trusted: trusted });
    if (cleared.error) throw new Unavailable();
    const anon = createClient(url, Deno.env.get('SUPABASE_ANON_KEY')!, { auth: { persistSession: false } });
    const { data, error } = await anon.auth.signInWithPassword({
      email: `child-${prof.id}@children.invalid`,
      password: await childPassword(prof.id, Deno.env.get('CHILD_PW_SECRET')!),
    });
    if (error || !data.session) return json({ error: 'server_error' }, 500);
    const { access_token, refresh_token, expires_in, expires_at, token_type } = data.session;
    return json({
      session: { access_token, refresh_token, expires_in, expires_at, token_type },
      profile: { id: prof.id, name: prof.name, unlimited: real?.unlimited === true },
      deviceToken: await issueDeviceToken(deviceSecret, prof.id, deviceId, pinSetAt),
    });
  } catch (e) {
    if (e instanceof Unavailable || e instanceof CaptchaUnavailable) return json({ error: 'try_again_later' }, 503);
    console.error('pin-login failed', e);
    return json({ error: 'server_error' }, 500);
  }
});
