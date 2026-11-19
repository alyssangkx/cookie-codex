// Family code and lock-key helpers shared by pin-login and parent-api (docs/accounts-plan.md 12.5). Plain TS with
// no Deno APIs, so site/src/lib/accounts.test.ts runs them under Node.
export const CODE_ALPHA = '23456789ABCDEFGHJKMNPQRSTUVWXYZ'; // no 0, 1, I, L, O
export const CODE_RE = /^[2-9A-HJKMNP-Z]{8}$/;

/** What a child typed ("k7m4-qx2p ") -> the stored form ("K7M4QX2P"). Validate with CODE_RE afterwards. */
export const normaliseCode = (t: string) => t.toUpperCase().replace(/[\s-]/g, '');

/** The name-side lock key inside a family: '<parent_id>:<name_key>' (prefixed name: / trust: by the SQL). */
export const lockKey = (parentId: string, nameKey: string) => `${parentId}:${nameKey}`;

/** 8 random symbols, rejection sampling so every symbol is equally likely (248 = 31 * 8). */
export function newCode(): string {
  let out = '';
  while (out.length < 8) {
    for (const b of crypto.getRandomValues(new Uint8Array(16))) if (b < 248 && out.length < 8) out += CODE_ALPHA[b % 31];
  }
  return out;
}
