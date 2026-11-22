// The one browser Supabase client. supabase-js keeps the session in localStorage, so it survives a browser
// restart and refreshes itself. Idle limit: the session is dropped when the last activity was over 90 days ago
// (a convenience limit, not a security control: refresh tokens do not expire on the free plan).
import { createClient } from '@supabase/supabase-js';
import type { Session } from '@supabase/supabase-js';
import { kv } from './store.ts';
import { idleExpired } from './sync.ts';

export const SUPABASE_URL = import.meta.env.PUBLIC_SUPABASE_URL as string;
export const ANON_KEY = import.meta.env.PUBLIC_SUPABASE_ANON_KEY as string;
export const FUNCTIONS_URL = `${SUPABASE_URL}/functions/v1`;

/** The session's localStorage key. Base.astro's pre-paint gate script checks this same literal. */
export const AUTH_KEY = 'ccx:auth';

/** The grown-up's session (parent or admin) lives under its own key (owner, 23 Nov 2026), so a child playing and a
 *  grown-up on the Parent or Admin page never sign each other out on a shared device. */
export const GROWNUP_AUTH_KEY = 'ccx:auth-gu';
const client = (storageKey: string) => createClient(SUPABASE_URL, ANON_KEY, {
  auth: { storageKey, persistSession: true, autoRefreshToken: true, detectSessionInUrl: false },
});
/** The child playing: game pages, sync, past-paper fetches, the PIN login. */
export const supabase = client(AUTH_KEY);
/** The grown-up: /parent, /admin, /grownups, sign-up, the emailed links, parent-api. */
export const grownup = client(GROWNUP_AUTH_KEY);

/** Stamp "active now" (called on sign-in and on every checked page load). */
export const touch = (key = 'lastSeen') => kv.set(key, String(Date.now()));
/** The grown-up session's own idle stamp (the child's play never keeps a grown-up signed in). */
export const GROWNUP_SEEN = 'lastSeen-gu';

/** The current session, or null. Signs out (this browser only) when idle for more than 90 days. */
export async function currentSession(sb = supabase): Promise<Session | null> {
  const { data } = await sb.auth.getSession();
  if (!data.session) return null;
  const key = sb === supabase ? 'lastSeen' : GROWNUP_SEEN;
  if (idleExpired(Number(kv.get(key) ?? 0))) {
    await sb.auth.signOut({ scope: 'local' });
    kv.del(key);
    if (sb === supabase) kv.set('sync:signedout', '1'); // the child's offline play only ends with the child's session
    return null;
  }
  touch(key);
  return data.session;
}

/** Before 23 Nov 2026 one key held every session: a parent or admin signed in then sits in the player's slot. Move it to
 *  the grown-up's slot (same tokens) and clear the player's, once. */
export async function adoptGrownup() {
  const s = (await supabase.auth.getSession()).data.session;
  if (!s || !roleOf(s)) return;
  try { if (!(await grownup.auth.getSession()).data.session) await grownup.auth.setSession({ access_token: s.access_token, refresh_token: s.refresh_token }); }
  catch { /* the grown-up signs in again */ }
  await supabase.auth.signOut({ scope: 'local' });
}

/**
 * True when a signed-out-looking page load should still open the game: this device has signed in before and was not
 * logged out, and we are offline (or the token refresh failed for lack of network). Sync resumes on reconnect.
 */
export async function offlineAllowed(): Promise<boolean> {
  if (kv.get('sync:signedout') || !kv.get('sync:owner') || !kv.get('device-token')) return false;
  if (typeof navigator !== 'undefined' && navigator.onLine === false) return true;
  try {
    const { error } = await supabase.auth.getSession();
    return !!error && (error.name === 'AuthRetryableFetchError' || /fetch|network/i.test(error.message));
  } catch { return false; }
}

/** Call a function with plain fetch (the CORS allow-list has no x-client-info). `token` defaults to the publishable key. */
export async function callFunction(name: string, body: unknown, token?: string) {
  const headers: Record<string, string> = { apikey: ANON_KEY, 'content-type': 'application/json' };
  if (token) headers.authorization = `Bearer ${token}`;
  const res = await fetch(`${FUNCTIONS_URL}/${name}`, { method: 'POST', headers, body: JSON.stringify(body) });
  let json: any = null;
  try { json = await res.json(); } catch { /* not JSON */ }
  return { status: res.status, body: json };
}

/** The signed-in grown-up's role from the session's app_metadata (set only by the server): admin, parent or none. */
export const roleOf = (s: Session | null): 'admin' | 'parent' | null => {
  const r = s?.user?.app_metadata?.role;
  return r === 'admin' || r === 'parent' ? r : null;
};

/** parent-api with the current session; throws an Error whose message is the function's error code. */
export async function callParentApi<T = any>(body: Record<string, unknown>): Promise<T> {
  const { data } = await grownup.auth.getSession();
  if (!data.session) throw new Error('unauthorized');
  const r = await callFunction('parent-api', body, data.session.access_token);
  if (r.status !== 200) throw new Error(r.body?.error ?? 'server_error');
  return r.body as T;
}

/** The privacy notice version a parent accepts at sign-up (parent-api checks it against its CONSENT_VERSION). */
export const CONSENT_VERSION = '1';

/**
 * Pick up the session from an emailed link (sign-up confirmation, password reset). The client has
 * detectSessionInUrl off, so the verify and reset pages call this: it reads the implicit-flow fragment
 * (#access_token=...&refresh_token=...&type=...) or a PKCE ?code=, sets the session, and removes the tokens from
 * the address bar. `type` is 'signup' or 'recovery' when the link said so.
 */
export async function sessionFromLink(): Promise<{ type: string | null; error: string | null }> {
  const q = new URLSearchParams(location.search), h = new URLSearchParams(location.hash.slice(1));
  const clear = () => history.replaceState(null, '', location.pathname);
  const err = h.get('error_description') ?? q.get('error_description');
  if (err) { clear(); return { type: null, error: err }; }
  const code = q.get('code');
  if (code) {
    const r = await grownup.auth.exchangeCodeForSession(code); clear();
    return { type: q.get('type'), error: r.error?.message ?? null };
  }
  const at = h.get('access_token'), rt = h.get('refresh_token');
  if (at && rt) {
    const r = await grownup.auth.setSession({ access_token: at, refresh_token: rt }); clear();
    return { type: h.get('type'), error: r.error?.message ?? null };
  }
  return { type: null, error: null };
}
