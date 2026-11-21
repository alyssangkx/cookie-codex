// Network half of the past-paper path (pure rules in pastpaper.ts), ADR 0012: per quiz, never in bulk. fetchPool lists ids,
// sub-topic, level and rank (no text); fetchItems gets the text and 10-minute picture URLs of the picked questions from the
// pp-serve function, at most 15 a call, under the daily limits. Loaded with a dynamic import only while PP_ENABLED.
// Any failure returns null; null (not []) tells Daily Review not to park the past-paper retests it could not load. The
// quiz page then: a one-pool quiz stops; a merged tier, Daily Review and papers carry on with the generated questions.
import { supabase, SUPABASE_URL, currentSession, callFunction } from './supabase';
import { ppSubjectOf, validRow, safeSignedUrl, toQ, stubOf, type PpQ, type PpStub } from './pastpaper';

const CHUNK = 15; // pp-serve takes at most 15 ids a call (migration 006)

export async function fetchPool(subs: string[], topicOf: (sub: string) => string | undefined): Promise<PpStub[] | null> {
  if (!subs.length) return [];
  try {
    if (!(await currentSession())) return null;
    const out: PpStub[] = [];
    const bySubject = new Map<string, string[]>(); // pp_pool lists one subject per call (Daily Review asks for several)
    for (const s of subs) {
      const subject = ppSubjectOf(s);
      if (!subject) return null;
      (bySubject.get(subject) ?? bySubject.set(subject, []).get(subject)!).push(s);
    }
    for (const [subject, list] of bySubject) {
      for (let i = 0; i < list.length; i += 40) { // pp_pool takes at most 40 sub-topics a call
        const { data, error } = await supabase.rpc('pp_pool', { p_subject: subject, p_subtopics: list.slice(i, i + 40) });
        if (error || !Array.isArray(data)) return null;
        for (const r of data) {
          const st = stubOf(r, topicOf(r?.subtopic));
          if (!st) return null; // a partial list is a failure: totals and milestones would be wrong
          out.push(st);
        }
      }
    }
    return out;
  } catch {
    return null;
  }
}

export type ItemsResult = { items: PpQ[] } | { error: 'daily_limit' | 'failed' };

/** The real questions for these ids (in any order). A missing or unsigned one makes the whole call a failure. */
export async function fetchItems(ids: string[], topicOf: (sub: string) => string | undefined): Promise<ItemsResult> {
  const want = [...new Set(ids)];
  if (!want.length) return { items: [] };
  try {
    const sess = await currentSession();
    if (!sess) return { error: 'failed' };
    const items: PpQ[] = [];
    for (let i = 0; i < want.length; i += CHUNK) {
      const r = await callFunction('pp-serve', { ids: want.slice(i, i + CHUNK) }, sess.access_token);
      if (r.status === 429 && r.body?.error === 'daily_limit') return { error: 'daily_limit' };
      if (r.status !== 200 || !Array.isArray(r.body?.items)) return { error: 'failed' };
      for (const row of r.body.items) {
        if (!validRow(row)) return { error: 'failed' };
        const signed = new Map<string, string>();
        for (const f of (row as { figures: { path: string; url?: unknown }[] }).figures) {
          if (typeof f.url === 'string' && safeSignedUrl(f.url, SUPABASE_URL)) signed.set(f.path, f.url);
        }
        const q = toQ(row, signed, topicOf(row.subtopic));
        if (!q) return { error: 'failed' };
        items.push(q);
      }
    }
    return items.length === want.length ? { items } : { error: 'failed' }; // an inactive or missing id: a stale pool
  } catch {
    return { error: 'failed' };
  }
}
