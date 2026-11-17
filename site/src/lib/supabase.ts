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

export const supabase = createClient(SUPABASE_URL, ANON_KEY, {
  auth: { storageKey: AUTH_KEY, persistSession: true, autoRefreshToken: true, detectSessionInUrl: false },
});

/** Stamp "active now" (called on sign-in and on every checked page load). */
export const touch = () => kv.set('lastSeen', String(Date.now()));

/** The current session, or null. Signs out (this browser only) when idle for more than 90 days. */
export async function currentSession(): Promise<Session | null> {
  const { data } = await supabase.auth.getSession();
  if (!data.session) return null;
  if (idleExpired(Number(kv.get('lastSeen') ?? 0))) {
    await supabase.auth.signOut({ scope: 'local' });
    kv.del('lastSeen');
    kv.set('sync:signedout', '1');
    return null;
  }
  touch();
  return data.session;
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
