// Cloudflare Turnstile widget (docs/accounts-plan.md 12.8). The site key is public (PUBLIC_TURNSTILE_SITE_KEY);
// the secret lives only in Supabase (Auth CAPTCHA setting, and pin-login's CAPTCHA_SECRET). With no site key set
// the widget is skipped and the token is undefined: the server then refuses only if it requires a CAPTCHA.
const SITE_KEY = import.meta.env.PUBLIC_TURNSTILE_SITE_KEY as string | undefined;
const SRC = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';

type Turnstile = { render(el: HTMLElement, o: Record<string, unknown>): string; reset(id: string): void };
let loading: Promise<Turnstile> | null = null;
const load = () => (loading ??= new Promise<Turnstile>((ok, fail) => {
  const s = document.createElement('script');
  s.src = SRC; s.async = true;
  s.onload = () => ok((window as unknown as { turnstile: Turnstile }).turnstile);
  s.onerror = () => { loading = null; fail(new Error('captcha script')); };
  document.head.append(s);
}));

export type Captcha = { shown: boolean; token(): string | undefined; reset(): void };

/** Show the widget in `el` (once). token() is undefined until it is solved; reset() after every server try. */
export async function mountCaptcha(el: HTMLElement): Promise<Captcha> {
  let tok: string | undefined, id = '';
  const t = SITE_KEY ? await load() : null;
  if (t) {
    id = t.render(el, {
      sitekey: SITE_KEY, theme: 'light', size: 'flexible',
      callback: (v: string) => { tok = v; }, 'expired-callback': () => { tok = undefined; }, 'error-callback': () => { tok = undefined; },
    });
  }
  return { shown: !!(t && id), token: () => tok, reset: () => { tok = undefined; if (t && id) t.reset(id); } };
}
