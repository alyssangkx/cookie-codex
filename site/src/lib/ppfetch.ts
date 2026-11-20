// Network half of the past-paper path (pure rules in pastpaper.ts). Loaded with a dynamic import only when
// PP_ENABLED is true, so while the flag is off no page calls it. Any failure (signed out, offline, RPC refused, rate
// limit) returns null and the quiz falls back to the generated items; null (not []) tells Daily Review not to park
// the past-paper retests it could not load.
import { supabase, SUPABASE_URL, currentSession } from './supabase';
import { PP_SUBJECT, PP_BUCKET, SIGN_TTL_S, validRow, safeSignedUrl, toQ, fetchComplete, type PpQ } from './pastpaper';

export async function fetchPp(subs: string[], topicOf: (sub: string) => string | undefined): Promise<PpQ[] | null> {
  if (!subs.length) return [];
  try {
    if (!(await currentSession())) return null;
    const { data, error } = await supabase.rpc('pp_items_for', { p_subject: PP_SUBJECT, p_subtopics: subs });
    if (error || !Array.isArray(data)) return null;
    const rows = data.filter(validRow);
    const paths = [...new Set(rows.flatMap((r) => r.figures.map((f) => f.path)))];
    let signErrors = 0;
    const signed = new Map<string, string>();
    for (let i = 0; i < paths.length; i += 100) {
      const { data: s, error: e } = await supabase.storage.from(PP_BUCKET).createSignedUrls(paths.slice(i, i + 100), SIGN_TTL_S);
      if (e) { signErrors++; continue; }
      for (const x of s ?? []) if (x.path && x.signedUrl && safeSignedUrl(x.signedUrl, SUPABASE_URL)) signed.set(x.path, x.signedUrl);
    }
    const qs = rows.map((r) => toQ(r, signed, topicOf(r.subtopic))).filter((q): q is PpQ => q !== null);
    return fetchComplete(data.length, rows.length, qs.length, signErrors) ? qs : null; // partial = failure
  } catch {
    return null;
  }
}
