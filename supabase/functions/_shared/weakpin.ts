// DRAFT (docs/accounts-plan.md section 12): not used by any deployed function yet.
// Weak 4-digit PIN check, applied when a parent SETS a PIN (existing PINs are never re-checked).
// Honest limit: this blocks about 1.7% (171) of the 10,000 values. The real bounds are the family code and the
// escalating lockouts; this only removes the guesses an attacker would try first. Pure, no I/O.

const TOP = new Set([
  '1234', '1111', '0000', '1212', '7777', '1004', '2000', '4444', '2222', '6969', '9999', '3333',
  '5555', '6666', '1122', '1313', '8888', '4321', '2001', '1010', '2580', '0852', '2468', '1357',
  '0123', '1357', '0007', '5683', '1230', '2323', '1999', '1221', '0101', '1986', '8520',
]);

/** A reason string when the PIN is too guessable, else null. Input must already match /^\d{4}$/. */
export function weakPin(pin: string): string | null {
  if (!/^\d{4}$/.test(pin)) return 'format';
  const d = [...pin].map(Number);
  if (d.every((x) => x === d[0])) return 'repeat';
  const step = d[1] - d[0];
  if (Math.abs(step) === 1 && d.every((x, i) => i === 0 || x - d[i - 1] === step)) return 'sequence';
  if (d[0] === d[2] && d[1] === d[3]) return 'pairs';          // 1212, 6969
  if (TOP.has(pin)) return 'common';
  const n = Number(pin);
  if (n >= 1990 && n <= 2035) return 'year';                    // birth years and this year
  return null;
}
