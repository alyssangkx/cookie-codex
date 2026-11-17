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

export const supabase = createClient(SUPABASE_URL, ANON_KEY, {
  auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: false },
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
    return null;
  }
  touch();
  return data.session;
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
