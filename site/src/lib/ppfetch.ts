// Network half of the past-paper path (pure rules in pastpaper.ts), ADR 0012: per quiz, never in bulk. fetchPool lists ids,
// sub-topic, level and rank (no text); fetchItems gets the text and 10-minute picture URLs of the picked questions from the
// pp-serve function, at most 15 a call, under the daily limits. Loaded with a dynamic import only while PP_ENABLED.
// Any failure returns null; null (not []) tells Daily Review not to park the past-paper retests it could not load. The
// quiz page then: a one-pool quiz stops; a merged tier, Daily Review and papers carry on with the generated questions.
import { supabase, SUPABASE_URL, currentSession, callFunction } from './supabase';
import { ppSubjectOf, pageStep, validRow, safeSignedUrl, toQ, stubOf, type PpQ, type PpStub } from './pastpaper';

const CHUNK = 15; // pp-serve takes at most 15 ids a call (migration 006)
const POOL_PAGE = 1000; // rows asked per pp_pool call (the API's default max_rows; a lower cap just means more pages)

export async function fetchPool(subs: string[], topicOf: (sub: string) => string | undefined): Promise<PpStub[] | null> {
  if (!subs.length) return [];
  try {
    if (!(await currentSession())) return null;
    const out: PpStub[] = [];
    // pp_pool lists one subject per call (Daily Review asks for several). ponytail: one failing subject fails the whole list
    // (null: Daily Review skips past papers that day, parks nothing); per-subject results if that ever bites
    const bySubject = new Map<string, string[]>();
    for (const s of subs) {
      const subject = ppSubjectOf(s);
      if (!subject) return null;
      (bySubject.get(subject) ?? bySubject.set(subject, []).get(subject)!).push(s);
    }
    for (const [subject, list] of bySubject) {
      for (let i = 0; i < list.length; i += 40) { // pp_pool takes at most 40 sub-topics a call
        // the API returns at most max_rows a call (Supabase, 1000 by default) and English grammar alone has 1,900+: page
        // through pp_pool's fixed order (sub-topic, rank, id) and check every page against the server's exact total, so a
        // list cut by a lower cap, or shifted by an upload between pages, fails closed instead of passing as complete.
        // ponytail: each page is one pp_pool rate hit (about 7 for a three-subject Daily Review, limit 120 an hour)
        let total: number | null | undefined, got = 0; // null: the server sent no total (pageStep explains)
        for (let step = 'more'; step === 'more';) { // the next page starts after the rows received (a lower cap returns fewer)
          const { data, error, count } = await supabase.rpc('pp_pool', { p_subject: subject, p_subtopics: list.slice(i, i + 40) },
            { count: 'exact' }).range(got, got + POOL_PAGE - 1);
          if (error || !Array.isArray(data)) return null;
          const c = typeof count === 'number' ? count : null;
          if (total === undefined) total = c;
          for (const r of data) {
            const st = stubOf(r, topicOf(r?.subtopic));
            if (!st) return null; // a partial list is a failure: totals and milestones would be wrong
            out.push(st);
          }
          got += data.length;
          step = pageStep(total, c, got, data.length, POOL_PAGE);
          if (step === 'fail') return null;
        }
      }
    }
    return new Set(out.map((q) => q.id)).size === out.length ? out : null; // a row seen twice: the order moved between pages
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
        for (const f of (row as { figures: { path?: string; url?: unknown }[] }).figures) {
          if (typeof f.path === 'string' && typeof f.url === 'string' && safeSignedUrl(f.url, SUPABASE_URL)) signed.set(f.path, f.url);
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
