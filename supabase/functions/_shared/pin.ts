// PIN hashing shared by pin-login and the (Phase B) admin-pin function. Deno / Web Crypto only.
// Format: pbkdf2-sha256$<iterations>$<salt b64>$<hash b64>
//
// A 4-digit PIN has only 10,000 values, so no hash can protect it if the database leaks. What
// protects it is (1) the server-side lockout and (2) PIN_PEPPER, a secret held in the function's
// environment and never in the database: the stored hash cannot be attacked without it.
// This file never contains, logs or returns a PIN.

const ITERATIONS = 600_000; // OWASP guidance for PBKDF2-HMAC-SHA256
const enc = new TextEncoder();

const b64 = (u: Uint8Array) => btoa(String.fromCharCode(...u));
const unb64 = (t: string) => Uint8Array.from(atob(t), (c) => c.charCodeAt(0));

async function derive(pin: string, salt: Uint8Array, iterations: number, pepper: string) {
  const key = await crypto.subtle.importKey('raw', enc.encode(`${pepper}:${pin}`), 'PBKDF2', false, ['deriveBits']);
  return new Uint8Array(await crypto.subtle.deriveBits({ name: 'PBKDF2', hash: 'SHA-256', salt, iterations }, key, 256));
}

export async function hashPin(pin: string, pepper: string): Promise<string> {
  const salt = crypto.getRandomValues(new Uint8Array(16)); // per-child salt
  return `pbkdf2-sha256$${ITERATIONS}$${b64(salt)}$${b64(await derive(pin, salt, ITERATIONS, pepper))}`;
}

function timingSafeEqual(a: Uint8Array, b: Uint8Array) {
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a[i] ^ b[i];
  return d === 0;
}

export async function verifyPin(pin: string, stored: string | null, pepper: string): Promise<boolean> {
  const [alg, it, salt, hash] = (stored ?? '').split('$');
  if (alg !== 'pbkdf2-sha256' || !salt || !hash) return false;
  return timingSafeEqual(await derive(pin, unb64(salt), Number(it), pepper), unb64(hash));
}

/** A real-shaped hash to compare against when the name is unknown, so timing does not reveal which names exist. */
export const DUMMY_HASH = `pbkdf2-sha256$${ITERATIONS}$${b64(new Uint8Array(16))}$${b64(new Uint8Array(32))}`;

/** The child's auth password: derived, never stored, never typed. Rotating the secret locks everyone out. */
export async function childPassword(profileId: string, secret: string): Promise<string> {
  const key = await crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  return b64(new Uint8Array(await crypto.subtle.sign('HMAC', key, enc.encode(`child-pw:${profileId}`))));
}

export async function sha256Hex(text: string) {
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256', enc.encode(text)))]
    .map((x) => x.toString(16).padStart(2, '0')).join('');
}
