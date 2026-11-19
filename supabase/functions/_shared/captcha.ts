// CAPTCHA check for pin-login (docs/accounts-plan.md 12.5, 12.8): Cloudflare Turnstile by default;
// hCaptcha uses the same shape with CAPTCHA_VERIFY_URL=https://hcaptcha.com/siteverify).
// Secrets (supabase secrets set, typed by the owner, never in the repo): CAPTCHA_SECRET.
// Config: CAPTCHA_REQUIRED=true turns the check on. Fails CLOSED: required + secret missing -> throws;
// the provider unreachable -> throws (the caller answers 503), never "assume it passed".
export class CaptchaUnavailable extends Error {}

export const captchaRequired = () => Deno.env.get('CAPTCHA_REQUIRED') === 'true';

export async function verifyCaptcha(token: unknown): Promise<boolean> {
  const secret = Deno.env.get('CAPTCHA_SECRET');
  if (!secret) throw new CaptchaUnavailable();
  if (typeof token !== 'string' || token.length === 0 || token.length > 2048) return false;
  const url = Deno.env.get('CAPTCHA_VERIFY_URL') ?? 'https://challenges.cloudflare.com/turnstile/v0/siteverify';
  try {
    // no remoteip: no client-IP header on Edge Functions can be trusted (accounts-plan section 5)
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'content-type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ secret, response: token }),
      signal: AbortSignal.timeout(4000),
    });
    if (!r.ok) throw new CaptchaUnavailable();
    return (await r.json())?.success === true;
  } catch (e) {
    if (e instanceof CaptchaUnavailable) throw e;
    throw new CaptchaUnavailable();
  }
}
