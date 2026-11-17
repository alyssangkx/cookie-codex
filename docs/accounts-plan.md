# Accounts plan: Supabase login for Alyssa's Cookie Codex

Status: **Phase A, awaiting approval.** Nothing in this plan has been applied, deployed or created.
The SQL is in `supabase/migrations/001_init.sql`, the PIN function source is in
`supabase/functions/pin-login/index.ts` (with `_shared/pin.ts`). Neither has been run: there was no
Postgres or Deno on the dev machine, so the SQL and the Deno code are **untested: needs a Supabase project**.
`001_init.sql` has never been applied anywhere, so it is edited in place; after the first apply, every change is a new migration.

Goal: progress is saved on a server so Alyssa can play from any phone or computer, and more users
can be added later without a schema rewrite. The site stays a static Astro build; the browser talks
to Supabase directly.

## 1. Decisions carried in

| Topic | Decision |
|---|---|
| Backend | Supabase (auth + Postgres + Edge Functions), region Singapore (`ap-southeast-1`) |
| Today's users | One child, Alyssa, and one admin. A Test Player profile exists for the admin's test tools. |
| Child login | Name + 4-digit PIN. The PIN is a convenience, so it is checked **server-side** with lockout. |
| Remembered | The browser keeps the session until she presses "Log out". |
| Later | Parents with several children. Kept possible by `profiles.parent_id` and roles from day one. |
| PIN secrecy | The PIN is never in code, docs, seeds, commits or logs. The admin types it into the admin tool at setup; the server stores only a salted, peppered hash. |

## 2. Login flow

1. **First visit on a device.** `/login` shows "Who's playing?" with no names listed (the server
   never lists children to a stranger). Alyssa types her name and a PIN on a PIN pad.
2. The browser posts `{ name, pin, deviceId, deviceToken? }` to the `pin-login` Edge Function. `deviceId` is a
   random id generated once and kept in localStorage; `deviceToken` is the trusted-device token from an
   earlier successful login (also kept in localStorage), if any.
3. On success the function returns a normal Supabase session (access + refresh token) for
   **Alyssa's own auth user**. The page calls `supabase.auth.setSession(...)`. supabase-js stores
   it and refreshes the access token (1 hour) automatically, so she stays signed in.
4. On later visits the "Who's playing?" screen shows a tile for each name remembered on this
   device, and a session already present skips the screen entirely.
5. **Log out** (header control) calls `signOut()`, clears the session and the cached save, and
   returns to "Who's playing?". The remembered name tile stays, the PIN is asked again.
6. **Grown-ups** link at the bottom of `/login` goes to an email + password form for the admin.

Notes on "remembered for about 90 days":

- supabase-js keeps the session in localStorage, not a cookie. The site is static, so there is no
  server to set an HttpOnly cookie, and it makes no difference for this threat model.
- Refresh tokens do not expire by default. The 90-day inactivity limit and time-box are Pro-plan
  settings. The client will therefore write a `lastSeen` timestamp and treat a session idle for
  more than 90 days as signed out. This is a convenience limit, not a security control.
- "Log out" revokes the session server-side as well as clearing it locally.

## 3. Accounts and roles

| Account | How it exists | Role | Can do |
|---|---|---|---|
| Admin | Created by hand in the dashboard. Email + strong password (TOTP recommended). `app_metadata.role = 'admin'`, set in the dashboard or SQL, never from the client. | admin | See all profiles, reset PINs, run test tools on the Test Player, read (not write) Alyssa's save. |
| Alyssa | Auth user with synthetic address `child-<uuid>@children.invalid` and a **derived** password (HMAC of her id under `CHILD_PW_SECRET`). Nobody types or stores it. `profiles.id` = her auth user id. | child | Read and write her own save only. |
| Test Player | Same as a child but `profiles.role = 'test'`, no PIN, login refused. | test | Its save is the only one an admin session may write. |
| Parents (later) | Email sign-up, `app_metadata.role = 'parent'`, own children via `parent_id`. | parent | Their own children's profiles and saves, via the same RLS. |

`app_metadata` is writable only with the service role, so a user cannot promote themselves.
Alyssa's `parent_id` is the admin's user id for now.

## 4. Schema (`001_init.sql`)

- `profiles(id pk -> auth.users, parent_id -> auth.users, name, name_key, role child|test, pin_hash, pin_set_at, created_at)`.
  The spec's columns plus `role` and `pin_set_at` (a trigger sets it whenever the PIN is set or reset; it goes into the trusted-device token's HMAC). `name` is ASCII only for now: `^[A-Za-z][A-Za-z -]{0,19}$` (the same regex in JS and in the SQL CHECK). Non-ASCII names later need NFC normalisation on both sides.
  `name_key` is `lower(btrim(name))` (JS: `name.trim().toLowerCase()`; collation-independent for ASCII), generated and stored, with a partial unique index `where role = 'child'`: login does an
  exact `eq('name_key', ...)`, never `ilike`/`like`. Names are globally unique while login is by name; when a second family joins, add a family code and make it unique per parent.
- `saves(child_id pk -> profiles, data jsonb, schema_version int, rev bigint, updated_at timestamptz)`.
  `rev` starts at 0 and goes up by one on every write (a trigger enforces it too). `updated_at` is set
  by a trigger, so the server clock decides, not the phone's. Size capped at 2 MB.
- `private.pin_attempts(key, fails, strikes, locked_until, updated_at)`: lockout counters (`device:`, `name:`, `trust:` keys), no client access.
- `public.push_save(...)`: compare-and-set write on `rev` for sync (section 6). It decides write permission first: the child itself or the owning non-admin parent, or an admin on a `test` profile; anything else returns `status: 'denied'` on both the update and insert paths. It calls the same helpers the RLS policies use (`private.is_admin`, `private.is_test_profile`, `private.owns_child`, and `private.is_self` for the child's own session) instead of repeating the rules.
- `public.pin_reserve_attempt(device_key, name_key, trusted) / pin_clear(device_key, name_key)`: lockout, **service role only**. `pin_reserve_attempt` is ONE call with both keys: under row locks it checks both locks, and only if neither is locked counts both, before the PIN is verified. `pin_clear` resets the device key and the child's `name:` and `trust:` keys.
- `public.pin_clear_name_lock(child_id)`: admin only (checked from the JWT inside); clears a child's per-name and trusted-name locks from `/admin/`.

### RLS

Both tables have RLS on. Access is by `auth.uid()`:

| | profiles | saves |
|---|---|---|
| select | `parent_id = uid` or `id = uid` (the child) or admin | owning parent, the child itself, or admin |
| insert | **admin only** (`private.is_admin()`); a profile also needs an auth user, so creation really goes through `admin-pin` | owning parent or the child |
| update | **admin only**, name column only | owning parent or the child |
| delete | **admin only** | owning parent |

Profile writes are admin-only, so no child or parent session can create, rename or delete a profile
from the browser. A child reads only its own row, a parent only its own children's rows.

Two guards beyond the spec:

1. **`pin_hash` is never readable by a client.** Column-level grants expose only
   `id, parent_id, name, role, pin_set_at, created_at`. The hash is read and written by Edge
   Functions with the service role.
2. **The admin cannot write Alyssa's save.** The admin is also her `parent_id`, which would
   otherwise grant write access. Three RESTRICTIVE policies on `saves` say an admin session may
   write only a `test` profile's save. This is what makes "Alyssa's real progress is never touched"
   true in the database, not just in the UI.

Required check once applied: two parent test accounts, each must see only its own profiles and saves;
an admin session must fail to update Alyssa's save and succeed on the Test Player's.

## 5. The `pin-login` Edge Function

**Input:** `POST { name, pin: "dddd", deviceId }`, JSON. Bad shape returns 400.

**Output:** 200 with `{ session, profile: { id, name } }`; 401 `wrong_name_or_pin` with
`attemptsLeft` (identical for an unknown name, so names cannot be enumerated; it is **this device's own** remaining tries only, never the per-name count); 429 `locked` (plain, no counts) when the name is locked for an untrusted device, or `locked` with `retryAfterSec` for this device's own lock; 503 `try_again_later` if any reservation or clear RPC errors (**fail closed**: the PIN is not checked, and a null result is never read as 0 failures). On success the body also carries `deviceToken`.

**Hashing.** PBKDF2-HMAC-SHA256, 600,000 iterations, a random 16-byte salt per child, stored as
`pbkdf2-sha256$iterations$salt$hash`. The PIN is mixed with `PIN_PEPPER`, a function secret that is
not in the database. Chosen over argon2/scrypt because it is native Web Crypto in the Edge
runtime with no WASM or dependency. Honest limit: a 4-digit PIN has 10,000 values, so if the
database **and** the pepper both leaked the PIN would fall instantly. The pepper plus the lockout
are the real protection; the hash only stops casual exposure. This is acceptable because the
PIN guards a child's quiz progress, not money or contact data.

**Name checks.** The name is trimmed (`trim()`), lowercased, and must match `^[A-Za-z][A-Za-z -]{0,19}$` (ASCII only; non-ASCII names later need NFC normalisation on both sides). Anything else is rejected before any lookup, counts against the device limit, and answers
like a wrong PIN. The lookup is `eq('name_key', key)`: no pattern matching anywhere.

**Lockout.** Counters live in `private.pin_attempts`. `pin_reserve_attempt` is **one** RPC per request, taking
the device key and the name key (`name:` for an untrusted request, `trust:` for one with a valid token). Under
row locks it checks BOTH locks first: if either is locked it answers `locked` and counts **nothing** (no device
try is spent while the name is locked). Otherwise it counts both, **before the PIN is verified**, so concurrent
requests cannot exceed a limit. On a wrong PIN the counters stand; on success `pin_clear` resets the device key
and the child's `name:` and `trust:` keys, fails and strikes alike. A lock is applied the moment a limit is
reached (the attempt that reaches it still runs; the next is refused). Every lock doubles each time it trips:
15 min, 30 min, 1 h, 2 h, 4 h, 8 h, 16 h, then 24 h. Windows differ by key: the **device** failure counter restarts after **15 minutes** with no failure (it forgives a child's scattered typos); the **name** and **trust** counters restart only after **24 hours**, so pacing guesses under the limit still escalates. The escalation level (`strikes`) returns to 0 only after **7 days** with no new lock. A success clears the device and only the name-side key the request used, so a trusted login never resets a stranger's `name:` escalation. `private.pin_bump` does this with plpgsql variables: `SELECT ... FOR UPDATE`,
compute once, one `UPDATE`.

| Key | Limit | Why |
|---|---|---|
| `device:<deviceId>` | 5 wrong, then the escalating lock | every request. `deviceId` is client-chosen, so alone it only stops a well-behaved browser, or one copied token (a token is bound to one device id) |
| `name:<name_key>` | 20 wrong from untrusted requests, then the escalating lock | the **real brute-force bound**, because headers and device ids can be forged. Keyed by the typed name, so an unknown name behaves identically |
| `trust:<name_key>` | 30 wrong from requests with a valid trusted-device token, then the escalating lock | bounds copied tokens; locks trusted access for that name only |
| IP | **none** | see below |

**Why no IP limit.** Supabase documents no client-IP header for Edge Functions that a caller cannot
forge: `x-forwarded-for` can be supplied by the caller (reported in
[supabase/discussions/34647](https://github.com/orgs/supabase/discussions/34647)), and `x-real-ip` /
`cf-connecting-ip` are not documented for Edge Functions. A limit on a forgeable value adds nothing,
and a shared `unknown` bucket would let one stranger lock everyone out. If Supabase later documents a
trustworthy header, add it as a third, looser key.

**Trusted devices.** On every successful PIN login the function issues a token: HMAC-SHA256 over
(child id, device id, issued-at, `pin_set_at`), signed with the function secret `PIN_DEVICE_SECRET` (read from env,
never hard-coded; the function refuses to run without it). The client keeps it in localStorage next to
its device id and sends it as `deviceToken`. A request carrying a valid token for that child and device,
issued under 180 days ago, skips the per-name lock and does not feed it, but counts against the device
limit and the separate `trust:` limit. A request without a valid token stays under the per-name
escalating lock. Because `pin_set_at` is in the message, **any PIN set or reset voids every token issued
before it** (the admin resets the PIN if a device is lost). Rotating `PIN_DEVICE_SECRET` does the same for all children.
A `pin_set_at` (or lock expiry) that does not parse makes the function throw, answered as 500 `server_error`:
a token is never signed or verified over `NaN`.

**Worst-case guessing rates.** Method: the `name:`, `trust:` and `device:` budgets are separate rows, so an
attacker who holds tokens spends the untrusted budget with forged device ids **and** the trusted budget with
the tokens, at the same time. A device id can be forged freely only on untrusted requests; a token is bound
to its own device id, so one token reaches the trusted path with one device id (limit 5). A *batch* is the
tries before a key locks; the lock after batch k is 15 min x 2^(k-1), so batch 8 opens after 31.75 hours,
then one batch per 24 hours.

| Attacker | First 31.75 h | Then, per day | Expected time to hit the PIN (5,000 guesses) |
|---|---|---|---|
| (a) Stranger, no token | `name:` 8 batches x 20 = **160** | **20** | about 240 days |
| (b) One or many copied tokens | `name:` 160 + `trust:` 8 x 30 = 240, so **400** | 20 + 30 = **50** | about 92 days; a PIN reset voids every token at once |

Pacing does not help: the `name:` and `trust:` fail counts reset only after **24 hours** with no failure, so
guessing slowly under the limit still trips the lock and escalates. Only the `device:` count resets after 15
quiet minutes (to forgive a child's scattered typos); it is forgeable on untrusted requests anyway, so it is a
usability limit, not the security bound. With one token, the trusted path is also capped by that token's
device limit (5 per batch, escalating), which never exceeds the `trust:` budget. Each guess costs a
600,000-iteration PBKDF2. A locked key answers 429 without comparing the PIN and without counting, so
parallel requests cannot escalate it.

**Order.** (1) Look up the profile (exact `name_key`; dummy profile for an unknown name). (2) Verify the token
HMAC (against the dummy profile for an unknown name). (3) ONE reservation RPC for the device and the
`name:` / `trust:` key, still before the PIN. A locked key is refused here, before the expensive PIN hash,
and counts nothing. (4) Compute the PIN hash (dummy hash for an unknown name or a profile without a PIN) and
compare. On failure the counters stand; on success clear them. The token HMAC and the PIN hash always run, so
response time does not reveal whether a name exists. A locked device still costs one cheap profile lookup, the
price of having only one round trip.

**Threat model.** A stranger who knows her name can lock the name by guessing 20 times, for up to 24
hours if they repeat it, but that lock applies to **untrusted devices only**. Alyssa's own devices hold
a trusted-device token and keep working (limited only by the device limit); a new or cleared browser
has to wait out the lock, or the admin clears it with `pin_clear_name_lock(child_id)` from `/admin/`.
Strangers cannot learn the per-name count: `attemptsLeft` reflects only the requesting device, and a
name lock answers a plain `locked`. A stolen token is bound to one child and device id, is void after a PIN reset, expires
after 180 days, and is bounded by the device and `trust:` limits above (see the worst-case table: copied tokens add the `trust:` budget on top of the `name:` one). If trusted access for a name is locked (30 wrong
trusted tries), the admin clears it with the same `pin_clear_name_lock`. Untested: needs a Supabase project.

**Issuing the session.** After a correct PIN the function signs in as the child's own auth user
with the derived password (`signInWithPassword` using the anon key) and returns the session tokens.
No custom JWT signing, so Supabase's own refresh and revocation work unchanged. Unknown names run
a full dummy token check and hash compare so timing does not reveal which names exist.

**Secrets:** `PIN_PEPPER`, `CHILD_PW_SECRET`, `PIN_DEVICE_SECRET` (function secrets), optional `SITE_ORIGIN` for CORS.
The service-role key is available only inside the function and is never in the client or `site/.env`.

**Companion functions (Phase B, not written yet):**
- `admin-pin`: admin only. Creates a child (auth user, profile) or sets/resets a PIN. The admin
  types the PIN into the form; it travels over HTTPS to this function, is hashed, and is not
  logged. It checks `app_metadata.role = 'admin'` from the verified JWT.
- `delete-account`: a parent deletes their account, their children's auth users and all data.

## 6. Sync design

`store.ts` stays the only code touching storage, and its synchronous `load()`/`save()` stay as they
are, because every page calls them synchronously. The adapter sits **under** them:

```ts
interface StorageAdapter {
  read(): string | null;              // sync: the localStorage cache
  write(raw: string): void;           // sync: cache now, push later
  hydrate?(): Promise<void>;          // async: pull server save into the cache
  flush?(): Promise<void>;            // async: push now
  status?(): 'synced' | 'pending' | 'offline' | 'conflict';
}
```

- **`LocalAdapter`**: today's behaviour, key `ccx:save`.
- **`SupabaseAdapter`**:
  - **Pick/login:** `hydrate()` fetches `saves` for the profile, runs the schema migration on it
    (the v1 to v2 migration already exists), and writes it to the cache under
    `ccx:save:<profileId>`. Pages call `await ready()` once before first `load()`.
  - **Push:** `write()` updates the cache, marks pending and debounces a `push_save` call about
    5 seconds out, plus an immediate flush after each finished quiz and on `pagehide` /
    `visibilitychange`.
  - **Conflict:** the push sends the `rev` the client last saw (an integer, `null` before the first
    sync). `push_save` updates only `where rev = p_base_rev` and sets `rev = rev + 1`, returning the new
    `rev`; the first save is `insert ... on conflict do nothing` then the same compare-and-set, so two
    devices creating the row cannot both win. Before touching any row `push_save` checks write permission and returns `status: 'denied'` if the caller may not write. If the server row has moved on (another device
    played), nothing is overwritten and the server copy comes back with `status: 'conflict'`. The client shows a plain warning ("Alyssa played on another device")
    and offers the newer copy. The default is the **higher `rev`, i.e. last write wins**, as
    decided, but it is chosen consciously by the user, not silently. A later improvement is a field
    merge (union of `days` and `attempts`, max `stars`, later `due` per question); see open questions.
  - **Offline:** writes only hit the cache and stay pending; on the next load or `online` event
    the push retries. The cache is always playable.
- **Backup:** the migration already copies the pre-migration save to `ccx:backup`. A save this site cannot read (corrupt, unknown or newer version, failed migration) is kept in `ccx:failed:1`..`ccx:failed:3` (up to 3 distinct copies; a new one is added only if it differs from all stored copies, and when all 3 are full the slots rotate: 2 to 1, 3 to 2, the new one into 3, so the newest broken save is always kept; a legacy `ccx:failed` key is folded into the slots once and removed); `ccx:save` and `ccx:backup` are left alone.
- **First login migration:** if `ccx:save` (the anonymous browser save) has progress and the server
  has none for this profile, offer "Copy this browser's progress to Alyssa". If both have progress,
  the user chooses which to keep; the other goes to `ccx:backup`. After copying, the old key is
  kept as a read-only backup, not deleted.
- **Dependency:** `@supabase/supabase-js` is the only new package, added in Phase B after approval.

Test tools: the admin's clock jump is a client-side offset (`ccx:clock-offset`) honoured by
`store.ts` only when the signed-in role is admin **and** the active profile is the Test Player.
Reset-tier and grant-card edit the Test Player's save through the normal adapter; the restrictive
RLS above stops any admin write to a real child.

## 7. Pages

| Route | Behaviour |
|---|---|
| `/login/` | "Who's playing?" tiles for remembered names, plus name + PIN pad. Wrong PIN shows this device's attempts left; a device lock shows a countdown; a name lock just says locked. Small "Grown-ups" link to the admin form. |
| `/admin/` | Admin session and role only. Lists profiles, set/reset PIN, shows lock state, creates the Test Player, switches to it, and holds the test tools (day jump, reset tier, grant card). |
| `/parent/` | Gated by the admin session for now (the existing PIN-gated page stays as a screen-lock until then). |
| Header | "Log out" control, and the name of who is playing. |
| Privacy note | A plain-language page linked from `/login/`. |

Every page other than `/login/` redirects to it when there is no session. Draft privacy note:
"This site stores the first name you play under and your quiz progress, so you can continue on
another device. It does not collect your email, your birthday or your location, has no ads, and
shares nothing with anyone. A grown-up can delete everything at any time."

## 8. PDPA and data minimisation

The Singapore PDPA applies to organisations; a family project may be outside it, but this design
follows it anyway and treats the child's data as needing a guardian's consent.

- **Collect only:** first name, a salted PIN hash, quiz progress. No child email (the auth address
  is synthetic), no date of birth, no school, no photo, no location.
- **Consent and purpose:** the parent/guardian gives consent at setup; the only purpose is saving
  progress. No analytics, no advertising, nothing sent to third parties. Supabase and the host act
  as data intermediaries only.
- **Location:** database in Singapore (`ap-southeast-1`), so no overseas transfer for the stored data.
- **Retention and deletion:** a parent "Delete account and all data" button calls `delete-account`,
  which removes the auth users, profiles and saves (cascades). The admin can also delete a profile.
- **Access:** the parent can export a child's save code (already built) to see what is held.
- **Security:** RLS everywhere, PIN hash unreadable by clients, service-role key server-side only,
  TLS only. Admin MFA recommended. Report any breach to the parent and, where required, the PDPC.
- **No comparing children:** the schema has no cross-profile reads, matching the design rules.

## 9. Hosting for the static site

| Option | For | Against |
|---|---|---|
| **Vercel (recommended)** | Zero-config Astro static, global CDN, preview URLs per branch, free Hobby tier, easy custom domain, already in use elsewhere. | Hobby is for personal non-commercial use. Preview URLs vary, so each needs adding to Supabase's allowed redirects. |
| Netlify | Equivalent features and free tier. | Same redirect-URL handling; no advantage over Vercel here. |
| Cloudflare Pages | Free, generous bandwidth, no commercial-use clause. | One more account to run. |

Recommendation: **Vercel** for the site. Supabase **Auth > URL Configuration**: Site URL = the
production URL, plus the preview wildcard for the Vercel project. Password login for the admin does
not use redirects, but password reset does. Set `SITE_ORIGIN` in the function to the production URL
so CORS is not `*`. Do not deploy until approved.

## 10. Build order after approval

1. B0 (done): stable question ids and the save migration, so progress keyed on ids survives edits.
2. You create the Supabase project (Singapore) and give the URL and anon key.
3. You confirm; apply `001_init.sql`; create the admin by hand and set its role.
4. Write `admin-pin`, deploy `pin-login`, set the secrets, and set Alyssa's PIN in `/admin/`.
5. Add `@supabase/supabase-js` (ask first), implement the adapter, `/login/`, `/admin/`, header.
6. RLS checks with two parent accounts; adapter tests with a mocked client (load, push, conflict, offline).
7. Browser check from the prompt; code review; stop and ask before deploying.

## 11. Open questions

1. **Supabase free plan pauses a project after 7 days of inactivity.** Fine for the build; for daily
   use either pay for Pro (also gives 90-day inactivity limits) or add a weekly keep-alive ping.
2. **Conflict handling:** keep "warn, then choose" (default newer wins), or build the field merge
   so two devices never lose a quiz?
3. **Name uniqueness:** are globally unique child names acceptable until a family code is added?
4. **Admin MFA:** require TOTP on the admin account (recommended)?
5. **Same account, same device:** should the parent gate (`/parent/` PIN screen) remain once the
   admin session gates it, or be removed?
6. **Hosting:** confirm Vercel, and the production domain.
7. **Lockout of Alyssa by others:** a guessed name can lock the name for untrusted devices, escalating up to 24 hours; her trusted devices keep working (until 30 wrong trusted tries, which lock trusted access too) and the admin can clear the locks.

## Decisions (2026-11-17, approved at Checkpoint A)

| Question | Decision |
|---|---|
| Free-tier pausing | Stay on the free plan; a scheduled keep-alive pings the project every 3 days. Revisit Pro when more children join. |
| PIN lockout | Per device: 5 wrong PINs lock it for 15 minutes. Every lock doubles each time it trips (15 min up to 24 h) and resets on a successful login for the key that login used. A device locks after 5 wrong tries. A name locks after 20 wrong tries from untrusted requests; that name limit is the real bound. Trusted devices (HMAC token, 180 days, void after a PIN reset) skip the name lock but keep the device limit and a separate trusted limit of 30 wrong tries per name. Attempts are counted before the PIN is checked. No IP limit: no trustworthy client-IP header exists on Edge Functions (section 5). |
| Admin second factor | Required: Supabase TOTP (authenticator app) on the admin account. |
| Hosting | Vercel, free `*.vercel.app` subdomain, deployed from the GitHub repo; custom domain later. |
| Sync conflict | Newer save wins, with a visible warning; no field merge yet. |
| Child names | Globally unique for now (one family). |
| `/parent/` PIN screen | Dropped once the admin session gates the page. |
