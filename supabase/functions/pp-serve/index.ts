// pp-serve: the only way a quiz gets past-paper question text and pictures (ADR 0012, anti-scraping). Supabase Edge
// Runtime (Deno). Deploy WITH JWT verification (the default): `supabase functions deploy pp-serve --use-api --yes`.
//
// POST /functions/v1/pp-serve  { ids: ["pp-xxxxxxxxxx", ...] }   (1-15 ids)   Authorization: Bearer <child session token>
//   200 { items: [{ id, subtopic, level, pattern, stem, options, answer, year, figures: [{ path, url, w, h }] }] }
//   429 { error: "daily_limit" }  the account or its family reached today's limit (the admin is emailed once)
//   429 { error: "too_many" }     over 40 calls this hour
//   401 unauthorized, 403 forbidden (a parent, a deleted child), 400 bad_request, 500 server_error
// The limits, the log and the flag live in SQL (public.pp_serve, migration 006), called AS THE CHILD so auth.uid() is
// theirs. Pictures: the bucket is private and (after migration 007) readers cannot list or read it, so this function
// signs 10-minute URLs with the service role for exactly the questions it serves.
//
// Secrets: optional SITE_ORIGIN (CORS); optional ALERT_SMTP_USER, ALERT_SMTP_PASS (a Gmail app password), ALERT_TO for
// the flag email (unset: the flag still shows on the admin page, no email). Provided by the platform: SUPABASE_URL,
// SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY.
import { createClient } from 'npm:@supabase/supabase-js@2';

const ORIGIN = Deno.env.get('SITE_ORIGIN');
const CORS: Record<string, string> = {
  ...(ORIGIN ? { 'access-control-allow-origin': ORIGIN } : {}), // fail closed without a configured origin
  'access-control-allow-headers': 'authorization, apikey, content-type',
  'access-control-allow-methods': 'POST, OPTIONS',
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...CORS, 'content-type': 'application/json' } });
const ID_RE = /^pp-[0-9a-f]{10}$/;
const SIGN_TTL_S = 7200; // figure links outlive the longest quiz or paper plus its review (600 broke images after 10 min)

async function alert(name: string, reason: string, day: string) {
  const user = Deno.env.get('ALERT_SMTP_USER'), pass = Deno.env.get('ALERT_SMTP_PASS'), to = Deno.env.get('ALERT_TO');
  if (!user || !pass || !to) return console.warn('pp-serve: flag not emailed (ALERT_* secrets not set)');
  try {
    const { default: nodemailer } = await import('npm:nodemailer@6.9.16');
    // port 465 (TLS): Supabase Edge blocks outbound 25 and 587
    const t = nodemailer.createTransport({ host: 'smtp.gmail.com', port: 465, secure: true, auth: { user, pass } });
    await t.sendMail({
      from: user, to, subject: `Cookie Codex: past-paper limit reached (${name})`,
      text: `The account "${name}" reached a past-paper limit on ${day}: ${reason}.\n`
        + 'Past-paper questions are blocked for this account for the rest of the day. See "Heavy use" on the admin page.\n',
    });
  } catch (e) {
    console.error('pp-serve: flag email failed', e instanceof Error ? e.message : e); // never blocks the reply
  }
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null, { headers: CORS });
  if (req.method !== 'POST') return json({ error: 'bad_request' }, 405);
  try {
    const url = Deno.env.get('SUPABASE_URL')!, anon = Deno.env.get('SUPABASE_ANON_KEY')!, service = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    if (!url || !anon || !service) throw new Error('missing configuration');
    const auth = req.headers.get('authorization') ?? '';
    if (!/^Bearer\s+\S+$/i.test(auth)) return json({ error: 'unauthorized' }, 401);

    let body: { ids?: unknown };
    try { body = await req.json(); } catch { return json({ error: 'bad_request' }, 400); }
    const ids = body?.ids;
    if (!Array.isArray(ids) || ids.length < 1 || ids.length > 15 || !ids.every((x) => typeof x === 'string' && ID_RE.test(x))) {
      return json({ error: 'bad_request' }, 400);
    }

    // as the child: can_read_pp, the limits and the log all key on auth.uid()
    const asUser = createClient(url, anon, { global: { headers: { Authorization: auth } }, auth: { persistSession: false } });
    const { data, error } = await asUser.rpc('pp_serve', { p_ids: ids });
    if (error) {
      if (error.code === '42501') return json({ error: 'forbidden' }, 403);
      if (error.code === '53400') return json({ error: 'too_many' }, 429);
      if (error.code === '22023') return json({ error: 'bad_request' }, 400);
      if (/jwt|token/i.test(error.message)) return json({ error: 'unauthorized' }, 401);
      throw new Error(error.message);
    }
    const svc = createClient(url, service, { auth: { persistSession: false } });
    if (data?.status === 'limit') {
      const who = await asUser.auth.getUser();
      if (who.data?.user) {
        const { data: f } = await svc.rpc('pp_flag_take', { p_uid: who.data.user.id });
        if (Array.isArray(f) && f[0]) await alert(String(f[0].name), String(f[0].reason), String(f[0].day));
      }
      return json({ error: 'daily_limit' }, 429);
    }
    const items: Array<Record<string, unknown> & { figures?: Array<{ path: string; w: number; h: number }> }> = Array.isArray(data?.items) ? data.items : [];
    const paths = [...new Set(items.flatMap((i) => (i.figures ?? []).map((f) => f.path)).filter((p) => typeof p === 'string'))];
    const signed = new Map<string, string>();
    if (paths.length) {
      const { data: s, error: e } = await svc.storage.from('pp-figures').createSignedUrls(paths, SIGN_TTL_S);
      if (e) throw new Error('sign: ' + e.message);
      for (const x of s ?? []) if (x.path && x.signedUrl) signed.set(x.path, x.signedUrl);
    }
    // a question whose picture could not be signed is left out rather than shown without it
    const out = items
      .map((i) => ({ ...i, figures: (i.figures ?? []).map((f) => ({ ...f, url: signed.get(f.path) })) }))
      .filter((i) => i.figures.every((f) => typeof f.url === 'string'));
    return json({ items: out });
  } catch (e) {
    console.error('pp-serve:', e instanceof Error ? e.message : e);
    return json({ error: 'server_error' }, 500);
  }
});
