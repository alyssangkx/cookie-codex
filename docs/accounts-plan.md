# Accounts plan: Supabase login for Alyssa's Cookie Codex

Status: **Implemented: yes (Phase B, 2026-11-17).** Schema applied, `pin-login` and `admin` deployed, `/login/`, `/admin/`, sync and the login gate built and live-tested against the real project with throwaway users (see "Phase B as built" at the end). The original Phase A text below is kept as written.
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


## Phase B as built (2026-11-17)

Implemented: yes. What differs from the plan above:

- **`admin` function** replaces the planned `admin-pin`. Actions: `create_child`, `set_pin`, `clear_name_lock`, `list_children` (never `pin_hash`), `create_test_player`, `test_login`, `delete_child`. Requires admin role (read from the Auth server) and an `aal2` token; deployed with JWT verification on; every error fails closed (500 `server_error`).
- **Playing as the Test Player** uses the admin action `test_login` (a session for a `test` profile only), because `pin-login` refuses the `test` role. The random PIN is still created and shown once, but is not needed.
- **Admin has no clock offset.** The "jump the clock a day" tool shifts the Test Player's day keys, pass days, due dates and timestamps back one day inside its save (pushed with `push_save`), instead of the planned `ccx:clock-offset` in `store.ts`.
- **Sync** debounces 2 s (not 5 s). There is no `StorageAdapter` interface: `store.ts` gained `setSaveHook`, `replaceLocal`, `kv`, and sync listens to `save()`. One local key `ccx:save` is kept (not per profile); `ccx:sync:owner` records whose save it is, so a different child on the same device never pushes the first child's progress. First sign-in with an anonymous local save and an empty server row adopts the local save automatically (no prompt); with progress on both sides the server copy wins and the local one goes to `ccx:backup`.
- A newer server copy with unsynced local changes shows the conflict banner instead of overwriting.
- **Log out** signs out this browser only (`scope: local`) so it does not end the child's other devices; it keeps the device id and token. It does not clear the cached save.
- **Login page** has no remembered-name tiles yet; it always asks for the name.
- **`/parent/`** shows the save on this device (an admin session has no child save of its own); the PIN screen and the Change-PIN form are removed.
- **Browser calls** use plain `fetch` to the functions (the CORS allow-list has no `x-client-info`). `SITE_ORIGIN` is `http://localhost:4321`, so the live test served the site on 4321, not 4331.
- Not built: privacy page, `delete-account`, field-merge on conflict.


## 12. Open parent sign-up

Status: **built (Phase 2, 19 Nov 2026), not applied or deployed.** `002_parents.sql` passes `scripts/accounts/sqltest.sh` (a Postgres container); the functions pass `deno check`; the live two-family check is `scripts/accounts/isolation.mjs` (after apply). Phase 1 design text below; the drafts named in it now live at their final paths (`parent-api/index.ts`, `pin-login/index.ts`, the patched `admin/index.ts`, `_shared/family.ts`). Owner's decision: any parent can register with an email address and add their own children; PINs are never emailed, the parent sets each PIN on the site after verifying their email. Drafts written for this section: `supabase/migrations/002_parents.sql`, `supabase/functions/_drafts/{parent-api.ts, pin-login.family.ts, admin.family.patch.txt}`, `supabase/functions/_shared/{weakpin.ts, captcha.ts}`. The security audit (F1-F20, `/data/alvin/tmp/cookie-codex/site-review/security.md`) is the checklist: every finding marked "worse under open sign-up" is in the table in 12.10.

### 12.1 Sign-up and verify flow

1. **`/signup/`**: email, password (10+ characters), CAPTCHA, and two ticked boxes on the consent screen (12.9: "I am the parent or guardian of the children I will add", "I have read the privacy notice"). The browser calls `supabase.auth.signUp` with the CAPTCHA token and `emailRedirectTo = /signup/verify/`. Supabase sends the verification email through the custom SMTP provider (12.8). The page then says "Check your email" and nothing else (the same words whether or not the address already exists; Supabase already hides that).
2. **Verify.** The link opens `/signup/verify/` with a session. The page calls `parent-api` `register { consent_version }`. The function (service role) checks the email is confirmed and is not a `@children.invalid` address, creates the `families` row (random family code, consent version, server timestamp), and only then sets `app_metadata.role = 'parent'` (the client can never write it). The page refreshes its session so the token carries the role.
3. **`/parent/`** opens on "Add your first child": name, PIN typed twice (weak PINs are refused with a reason), then a card showing the **family code** ("Alyssa logs in at the Cookie Codex with this code, her name and her PIN") with Copy and Print.
4. **Child login** (`/login/`): family code + name + PIN pad. The code is remembered on that device. New devices pass the CAPTCHA once; a trusted device (valid device token) does not.
5. **Later**: the parent signs in at `/grownups/` (email + password, authenticator code if enrolled), manages children, and can delete the account.

An unverified sign-up is purged after 3 days (`private.purge_unconfirmed`). A parent who never reaches `register` has an auth user and no family row and can do nothing.

### 12.2 Roles

| Role | Where it lives | Powers |
|---|---|---|
| admin | `app_metadata.role = 'admin'`, aal2 required, by hand | unchanged: the `admin` function, all-profile reads, test tools, read-only Alyssa's save (restrictive RLS) |
| parent | `app_metadata.role = 'parent'`, set only by `parent-api register` | their own family only: list/add/rename/delete children, set PIN, clear locks, rotate the code, read their children's saves (existing RLS `owns_child`), delete the account |
| child | no role; synthetic address and derived password | read/write own save only |
| test | `profiles.role = 'test'` | unchanged; admin's own profile only (a trigger refuses it under any other parent) |

`is_admin()` is untouched, so a parent never gains a global read (F7). `parent-api` refuses an admin session (403 `use_admin`) and the `admin` function refuses a parent, so neither role can borrow the other's door. All parent writes still go through an Edge Function with the service role scoped by `parent_id = caller.id`: **RLS on `profiles` and `saves` is not widened**; the browser only reads, as today (parent: own children via `parent_id = uid`, own saves via `owns_child`).

### 12.3 Parent login and 2FA

Email + password at `/grownups/`. aal1 is enough to view and manage children. **TOTP for parents is optional and enforced once enrolled**: `parent-api` returns 403 `mfa_required` for a parent with a verified factor whose token is not aal2, and the page then asks for the code (same flow as `/admin/`). `/signup/verify/` and `/parent/` offer "Add an authenticator app" after sign-up. Why not required: the families are parents of Primary 6 children, a forced second factor will cost sign-ups and password-reset support, and a parent account protects a quiz save and a first name, not money. Why not nothing: F8 (credential stuffing). Compensations: password 10+ characters, leaked-password check (Supabase Pro only, see 12.8), the CAPTCHA and Auth's own rate limits, a 60-per-hour cap on parent actions, `delete_account` needs the typed email. **Owner decision: optional-if-enrolled (draft default) or required.** Password reset by email (`/reset/`, CAPTCHA on the request) is the recovery path; there is no admin override for a parent's password.

### 12.4 Parent page scope (`/parent/`)

Own children only. The page gate becomes: admin at aal2 (as today) **or** parent (aal2 if enrolled). For a parent it shows the family code (copy, print, "Make a new code" if it leaked), the child list with PIN-set date and lock state, per-child: Rename, Set PIN, Clear lock, Delete (type the name), the save on this device and the picked child's save summary and "Questions answered wrong" (the existing code, reading through RLS), and "Delete account and all data" (12.9). Adding a child: name (same ASCII rule, unique inside the family; "Admin" and "Test Player" are reserved), PIN twice, at most **6 children per parent**. A renamed child keeps their save; the lock rows of the old name are cleared first. `set_pin` also voids every trusted-device token of that child (existing `pin_set_at` rule). The admin keeps managing Alyssa, the Admin player and the Test Player in `/admin/` with the same functions as today.

### 12.5 Family code and login lockout keys

- **Format** (draft, owner may change): 8 symbols from `23456789ABCDEFGHJKMNPQRSTUVWXYZ` (no 0, 1, I, L, O), shown as `K7M4-QX2P`; input ignores case, hyphen and spaces. 31^8 = 8.5e11 values, unique, random, rotatable. It is a **locator, not a secret**: children share it. The secret is still the PIN, bounded by the lockouts.
- **Login** is `{ familyCode, name, pin, deviceId, deviceToken?, captchaToken? }`. The function finds the family by exact code, then the child by exact `(parent_id, name_key)`. Names are unique **per parent** (index `profiles_family_name_uq` replaces the global one). Unknown code, unknown name and wrong PIN all answer `wrong_name_or_pin`, with the same work (dummy hash), as today.
- **Lockout keys** become `name:<parent_id>:<name_key>` and `trust:<parent_id>:<name_key>`; `device:<id>` is unchanged. The SQL RPCs (`pin_reserve_attempt`, `pin_clear`) are **not changed**: the key is a text built by the function, so limits, windows, escalation and the worst-case table in section 5 stand. What changes is who can reach a key: an attacker now needs the family code plus the name, and one family's "Emma" no longer collides with another's. Unknown code or malformed name: only the device key is counted.
- **Weak PINs** (`_shared/weakpin.ts`) are refused when a parent sets one: repeats, runs (1234, 9876), `abab` pairs, a short list of the most common PINs, years 1990-2035. That is 171 of 10,000 values: it removes the first guesses, it does not change the bound. The honest bound against a classmate who knows the code and the name is unchanged, the section 5 numbers (about 240 days to 5,000 guesses).
- **No global name lookup remains**, so the code, not the name, is what an attacker lacks (F1). A stranger who learns a code can only affect that family, and the parent can rotate the code or clear a lock themselves (F5).
- **CAPTCHA on untrusted logins** (12.8): checked after the cheap lookups and before the lock RPC and the 600,000-iteration hash; a failed CAPTCHA counts against no lock. A trusted device skips it, so a child on a known tablet is never asked.

### 12.6 Role-based unlimited play

`isUnlimited()` (store.ts) stops comparing the name to `Admin`. New column `profiles.unlimited boolean` (default false; **no client write grant**; readable by the owner and the child). A trigger sets it for `role = 'test'` and refuses it unless the profile's `parent_id` is an admin account; names `admin` and `test player` are refused for any non-admin parent. `login/` and `sync.hydrate` store the flag in kv `profile-unlimited` from the profile row; `isUnlimited()` reads that. The live "Admin" player keeps working: the migration sets `unlimited = true` on the admin-owned profile with `name_key = 'admin'` and on the Test Player. No save-schema change, so no `store.ts` migration step. Honest limit (F11): the daily cap, tries and tier locks live in the client-writable save and kv, so a child with devtools can still lift them; the flag only removes the "name your child Admin" route. Server-side enforcement of the caps in `push_save` is out of scope (open decision 9).

### 12.7 Changes by file

**SQL (`supabase/migrations/002_parents.sql`, draft written)**

| Change | Why |
|---|---|
| `public.families(parent_id pk, code unique, consent_version, consented_at)`; RLS: select own row only, no client write; backfill a row for the admin; 500-row cap trigger | family code, consent record, free-tier backstop (F6) |
| drop `profiles_name_key_uq`, add `profiles_family_name_uq (parent_id, name_key) where role = 'child'` | names per parent (F1) |
| `profiles.unlimited` + `private.profiles_guard` (reserved names, 6 children per parent, test/unlimited admin-only) | 12.6, F6, F11 |
| `pin_clear_name_lock(uuid)` replaced: admin **or owning parent**; keys `<parent_id>:<name_key>` | F5, F7 |
| `push_save` replaced: object, at most 40 keys, numeric `schemaVersion`, under 512 KB, else status `invalid`; `saves_size_cap` check `NOT VALID` | F6, F2 server side |
| `public.rate_hit()` + `private.rate_hits` | parent action cap, register cap (F4) |
| `private.purge_pin_attempts()`, `private.purge_unconfirmed()`; `cron.schedule` lines commented out (needs pg_cron enabled) | F4 table growth, unverified sign-ups |
| backfill: families row for the existing grown-up; `unlimited` for the Test Player and the Admin player | 12.11 |

**Edge Functions** (drafts in `supabase/functions/_drafts/`; underscore directories are never deployed by `supabase functions deploy`)

| File | Change |
|---|---|
| `_drafts/parent-api.ts` -> `functions/parent-api/index.ts` | new: `register`, `me`, `create_child`, `rename_child`, `set_pin`, `clear_name_lock`, `delete_child`, `rotate_family_code`, `delete_account`; JWT verification ON; parent role, aal2-if-enrolled, per-parent scope and 60/hour cap; `set_pin` re-asserts the child's synthetic email and derived password (F13) |
| `_drafts/pin-login.family.ts` -> `functions/pin-login/index.ts` | family code, family-scoped keys, CAPTCHA for untrusted requests, CORS fails closed (F14) |
| `_drafts/admin.family.patch.txt` -> `functions/admin/index.ts` | per-parent duplicate check and error match, family-scoped `pin_clear` in `delete_child`, CORS fails closed |
| `_shared/weakpin.ts`, `_shared/captcha.ts` | new, used by the above (written, `weakpin` run under Node for the counts above) |

New secrets, typed by the owner with `supabase secrets set` and never in the repo: `CAPTCHA_SECRET`; config values `CAPTCHA_REQUIRED=true`, `CONSENT_VERSION`; `SITE_ORIGIN` must be the production origin before deploy (the old value is `http://localhost:4321`).

**Auth settings** (dashboard, only these; each needs the owner's "go")

1. Allow new users to sign up: ON (today `disable_signup: true`). Confirm email: stays ON (`mailer_autoconfirm: false`). Anonymous sign-ins: OFF.
2. Custom SMTP (12.8), sender name and address, email subject and body for the confirm, reset and change-email templates (plain, no tracking links).
3. CAPTCHA protection: ON, provider and secret from the owner (12.8).
4. Password: minimum length 10; leaked-password protection ON if the plan allows it (Pro).
5. Rate limits: emails per hour raised to the SMTP provider's allowance; sign-ups and sign-ins per IP lowered (draft: 10 per 5 minutes); keep OTP/link expiry at 1 hour.
6. URL Configuration: Site URL = production; redirect allow-list `/signup/verify/` and `/reset/` for production only (no wildcard for previews unless needed).
7. MFA: TOTP stays enabled (already on for the admin); no phone MFA.
8. Secure email change ON, so a child session cannot attach an address (F13).
9. Extensions: enable `pg_cron`, then schedule the two purge jobs.

**Site pages** (Phase 2)

| File | Change |
|---|---|
| `site/src/pages/signup/index.astro`, `signup/verify.astro` (new) | sign-up form, CAPTCHA widget, consent screen, verify -> `register` -> `/parent/` |
| `site/src/pages/grownups/index.astro`, `reset/index.astro` (new) | parent and admin email login with TOTP step; password reset |
| `site/src/pages/privacy/index.astro` (new) | notice (12.9); linked from `/signup/`, `/login/`, `/parent/` |
| `site/src/pages/login/index.astro` | family code field (remembered), CAPTCHA widget reset after every try, new `captcha_failed` message |
| `site/src/pages/parent/index.astro` | gate: admin aal2 or parent; children manager, family code, delete account; every dynamic value through `esc(String(x))` |
| `site/src/layouts/Base.astro` | public routes add `/signup`, `/signup/verify`, `/grownups`, `/reset`, `/privacy`; `/parent` allows `role === 'parent'` (aal2 when `nextLevel === 'aal2'`) or admin at aal2 |
| `site/src/lib/supabase.ts` | `callParentApi()`, `roleOf(session)` helper |
| `site/src/lib/sync.ts` | **validate once at hydrate** (below); store `profile-unlimited`; `decidePush` handles status `invalid` like `denied` |
| `site/src/lib/store.ts` | `isUnlimited()` reads kv `profile-unlimited` (no name check) |
| `vercel.json` (F3, same release) | CSP with the CAPTCHA provider's script and frame origins allowed, `frame-ancestors 'none'`, `nosniff`, referrer policy |

**F2 follow-up (the parent page is fixed; the other pages are not).** `site/src/lib/cleansave.ts` (`cleanSave`) already renders a clean copy for the parent page and My House. The remaining readers (quiz, train, collection, paper, home) read the synced save through `store.load()`. Build plan: run `cleanSave` **once at hydrate time in `sync.ts`** (`adoptServer`, the conflict copy, and the picked-child read), before the save reaches `localStorage`, and discard or flag a save that does not clean (keep the raw string in `ccx:failed:n`, as `load()` already does). Then every page reads validated data without each call site validating. Add tests to `sync.test.ts` (a tampered server save is cleaned before it is stored; the cleaned copy is what `load()` returns).

### 12.8 Choices the owner must make

| Choice | Options and recommendation |
|---|---|
| **SMTP provider** | Supabase's built-in sender allows only a few emails an hour and is not for production. Recommend **Resend** (free 3,000/month, simple SMTP) or **Brevo** (free 300/day) or AWS SES (cheapest at scale, needs a verified domain and leaving the sandbox). All need a sender **domain** with SPF, DKIM and DMARC records: the free `*.vercel.app` host cannot send from its own address, so a sender domain (any cheap one) is needed. |
| **CAPTCHA** | Recommend **Cloudflare Turnstile** (free, invisible mostly, no puzzle for children, supported natively by Supabase Auth). hCaptcha is the alternative. Applies to sign-up, password reset, and untrusted child logins. |
| **Parent 2FA** | Optional and enforced once enrolled (draft) vs required (12.3). |
| **Family-code format** | 8 symbols, `XXXX-XXXX` (draft) vs shorter 6 symbols (easier to type, 31^6 = 8.9e8, still unique and rotatable). |
| **Sign-up cap and cost** | 500 families (trigger), 6 children each, 512 KB per save. Free Supabase is 500 MB and 50,000 monthly active users but pauses after inactivity and has no backups; with real families, move to Pro (also unlocks leaked-password protection and session limits). |
| **Privacy and contact** | Who is named as the contact for access, correction and deletion requests, and the notice text. |
| **Existing family** | OK that Alyssa's new devices need the family code once (her signed-in devices keep working)? |
| **Server-side caps** | Enforce the daily cap in `push_save` (F11) or leave the limits advisory? |
| **Delete retention** | Hard delete now (draft) or a 14-day undo window? |

### 12.9 PDPA screens and deletion

- **Consent screen at sign-up** (before the form submits): what is collected (the parent's email; each child's first name, a hashed PIN and quiz progress), why (saving progress across devices), where (Supabase, Singapore, no overseas transfer of stored data), who sees it (the parent; the site's operator can read it to run the service; nothing is shared, sold or used for ads or analytics), how long (until deleted), and two required, unticked boxes: parent or guardian of the children added; has read the privacy notice. `consent_version` and a server timestamp are stored in `families`; a changed notice gets a new version and a re-consent screen at the next parent sign-in.
- **`/privacy/`**: the plain-language notice (extends the draft in section 7): no child email, birthday, school, photo or location; no tracking; data access (the save code export), correction (rename, PIN change), withdrawal and deletion (below), contact for requests, breach handling (notify the parent, and the PDPC where required).
- **Delete account and all data**: `parent-api delete_account`, confirmed by typing the email. It clears each child's lock rows, deletes each child's auth user (profile and save cascade), then the parent's auth user (`families` cascades). Children first, so a failure leaves the account intact and the button can be pressed again. A parent can also delete one child (type the name). The admin can delete any profile as today.
- **Data minimisation stays**: no new personal fields; the only new personal datum is the parent's email, held by Supabase Auth, never copied into a table of ours.

### 12.10 Audit findings and how this design answers them

| ID | Handled by |
|---|---|
| F1 | family code, names unique per parent, family-scoped lockouts, weak-PIN refusal (12.5). Residual: a classmate who knows code + name keeps the section 5 bound. Option: 6-digit PIN (decision) |
| F2 | parent page fixed and pushed; the rest by validating the save at hydrate (12.7) and the `push_save` shape gate |
| F3 | `vercel.json` headers in the same release; the CAPTCHA origins are allowed in the CSP |
| F4 | CAPTCHA before the hash on untrusted logins, the 60/hour parent cap, `purge_pin_attempts`, Auth sign-up limits |
| F5 | parent clears their own child's lock (`clear_name_lock`), the code gates who can lock, rotating the code cuts off a stranger |
| F6 | 6 children per parent, 500 families, save under 512 KB, shape check in `push_save` |
| F7 | separate `parent` role and function scoped by `parent_id`; `is_admin()` untouched; `pin_clear_name_lock` checks the owner. The cross-family test (12.12) is the proof |
| F8 | optional TOTP enforced once enrolled, CAPTCHA, email confirmation, leaked-password check (Pro), rate limits. **Open decision**: required 2FA |
| F9 | open: refresh-token lifetime needs Pro. Mitigated by the CSP and by `signOut` scope. Listed in 12.8 (Pro) |
| F11 | `profiles.unlimited` replaces the name check; caps stay advisory (decision) |
| F12 | unchanged; add the rotation runbook in Phase 2 docs. More children now sit behind one secret |
| F13 | `set_pin` re-asserts the synthetic email and derived password; Secure email change ON |
| F14 | `SITE_ORIGIN` unset means no CORS header, in all three functions |
| F15 | 001 is frozen (this is 002); fix its header comment when 002 is applied; add the RLS isolation script |

### 12.11 Migration of existing data and apply order

Existing: the admin (also parent of Alyssa), Alyssa, the Admin player, the Test Player. `002` gives the admin a `families` row (the admin sees the code in `/admin/`, a new line to add), sets `unlimited` on the Test Player and the Admin player, keeps all `profiles` and `saves` rows, and changes no save. Alyssa's existing sessions and trusted-device tokens keep working (the token binds child id, device id and `pin_set_at`, none of which change); a **new** device needs the code once. Order, each step after the owner says so: (1) read-only checks: one admin-owned profile named Admin; the Test Player's save size and key count against the 512 KB and 40-key limits; (2) apply `002` and deploy the new `pin-login` back to back (the lock-key format changes; Alyssa's lock rows under the old keys are dead and purged); (3) deploy `admin` (patched) and `parent-api`; (4) set secrets and CAPTCHA/SMTP, then flip Auth sign-up on **last**; (5) site release with the pages above. Rollback of 002: drop `families`, `rate_hit`, the new triggers and column, restore the 001 index and functions; the draft keeps all data.

### 12.11a Apply checklist (19 Nov 2026)

Done by the owner: Gmail SMTP; Turnstile widget; Vercel `PUBLIC_TURNSTILE_SITE_KEY`; function secrets
`CAPTCHA_SECRET`, `CAPTCHA_REQUIRED=true`, `CONSENT_VERSION=1`. Still to do: enable `pg_cron`.

Supabase Auth CAPTCHA ("Attack Protection") also guards **password sign-in**, so: the `/admin/` and `/grownups/`
forms send a Turnstile token, and `pin-login` / `admin test_login` sign the child in with a service-role client
(Auth skips its CAPTCHA for an admin-role key: `verifyCaptcha` in supabase/auth `internal/api/middleware.go`).
Order at "apply": read-only checks -> 002 -> deploy `pin-login`, `admin`, `parent-api` -> push the site ->
check child, admin and Test Player logins -> turn Auth CAPTCHA on -> check the three logins again (off at once if
any fails) -> `pg_cron` jobs -> Auth sign-up on -> `isolation.mjs` -> a real sign-up end to end.

### 12.12 Test plan

- **Unit** (`node --test site/src/lib/*.test.ts`, in the style of `sync.test.ts`): `weakPin` table; family-code normalisation; lock-key builder; `isUnlimited` reads the flag and ignores the name `Admin`; `decidePush` with `invalid`; hydrate cleans a tampered server save; the parent gate decision (role, aal, enrolled factor).
- **Isolation script** (live, exit 0, two throwaway parent accounts created and deleted afterwards, never Alyssa or `baziadmin@gmail.com`): parent A and B each create a child. Each sees only its own `profiles`, `families` row and `saves` through RLS; A's `push_save` on B's child returns `denied`; A's direct `update/delete` on B's `profiles` and `saves` change nothing; `parent-api` `set_pin`, `rename_child`, `delete_child`, `clear_name_lock` on B's child as A return 404; a child session of A cannot call `parent-api` (403); neither parent reads `pin_hash` or the other's family code; the same child name in both families is allowed and each logs in only with its own code; a seventh child, the name `Admin` and `unlimited` are refused; an admin session still fails to write Alyssa's save and succeeds on the Test Player's (the section 4 check); `delete_account` leaves no auth user, profile, save or lock row. Cleanup runs in a `finally`.
- **Live browser checks** with the Admin player only: family-code login, CAPTCHA on a new device and not on a trusted one, lock then parent clear, sign-up end to end with an owner-controlled address.
- **Gates**: `node --test site/src/lib/*.test.ts`, `cd site && npm run build`, the isolation script, each by real exit code.

### 12.x Owner's decisions (19 Nov 2026)

- **Email (SMTP):** Resend, with a sender domain the owner owns (SPF and DKIM records set up before sign-up opens).
- **CAPTCHA:** Cloudflare Turnstile (Supabase Auth native; also used by `pin-login` on untrusted devices).
- **Parent 2FA:** optional, enforced once a parent enrols an authenticator. The admin keeps required TOTP.
- **Family code and PIN:** 8-symbol family code, 4-digit PIN (weak PINs refused).
- **Supabase plan:** stay on Free. Accepted costs: no leaked-password check (the 10-character minimum and the
  CAPTCHA stay), no refresh-token lifetime limit (F9 stays mitigated by the CSP only), no automatic backups (a weekly
  `pg_dump` of `profiles`, `families` and `saves` to the owner's machine is the only copy; keep the last 4), and the project pauses after 7 quiet
  days (the keep-alive already covers it). Limits that bite first: 500 MB database and 5 GB egress a month. Hydrate
  must fetch `rev` first and `data` only when it changed, or egress caps the site at roughly 100 daily players (done 19 Nov 2026: `hydrate()` in `sync.ts`).
- **Daily caps:** advisory for now (not enforced in `push_save`).
- **Delete retention:** 7-day undo. `delete_account` and `delete_child` set `deleted_at`; the children's logins stop
  at once. The parent can still sign in, but sees only a "Restore" page until the purge. A daily `pg_cron` job
  hard-deletes rows older than 7 days (the steps in 12.9); old dumps age out after 4 weeks. Apart from that
  dump, this window is the only undo.
- **Email sender:** Gmail SMTP for now (a domain may come later, then switch to Resend). Sender and privacy contact:
  `psleadmin@gmail.com`, a dedicated account separate from the admin sign-in. `smtp.gmail.com:587` with an app
  password; about 500 emails a day. Set in the Supabase SMTP settings by the owner on 19 Nov 2026 (Auth sign-up still
  off). Not yet tested by a real send: the first verify mail in the Phase 2 end-to-end test is the check.
- **Privacy contact:** the same address, named in the notice (12.13). Notice text drafted below.
- **Still open:** the pre-apply checks in this section.

### 12.13 Privacy notice (draft for `/privacy/`)

The contact is `psleadmin@gmail.com`. Version 1, to be stored as `consent_version = 1`.

> **Privacy notice: Alyssa's Cookie Codex**
>
> Cookie Codex is a free PSLE revision game run by a parent in Singapore. This notice says what we keep about you
> and your children, why, and how to have it changed or deleted.
>
> **What we keep**
> - About you (the parent or guardian): your email address and a password, held by our sign-in service. We use your
>   email only to confirm your account and to reset your password. We never send newsletters or ads.
> - About each child you add: a first name or nickname, a 4-digit PIN (stored only in scrambled form, so nobody can
>   read it back), and their game progress: quiz scores, which questions they got wrong and the answer they chose,
>   cards earned, and time played each day.
> - We do **not** ask for a child's email, birthday, school, photo, phone number or location.
>
> **Why:** only so your child's progress is saved and follows them across devices, and so you can see it on the
> parent page. No analytics, no tracking cookies, no advertising, and nothing is sold or shared with anyone.
>
> **Where:** your children's names and progress are kept in a database in Singapore run by Supabase. The website is
> served by Vercel from servers around the world, sign-in emails are sent through Google's Gmail, and the operator keeps
> a weekly backup copy on their own computer. These services store or deliver the data for us and may
> not use it for anything else.
>
> **Who can see it:** you, for your own children only. The site's operator can read it to run and fix the service.
> Other families cannot see your children, and the game never compares children.
>
> **Your choices**
> - **See it:** the parent page shows each child's progress, and "Save code" exports a child's full progress. For
>   a copy of everything else we hold (names, account email, sign-in records), email us.
> - **Correct it:** rename a child or change their PIN on the parent page.
> - **Delete it:** "Delete account and all data" on the parent page removes you and every child. You can delete one
>   child the same way. Your children can no longer sign in, and everything is erased after 7 days, and from
>   backup copies within a further 4 weeks. Within those 7 days you can sign in as the parent and restore it.
> - **Withdraw consent:** deleting the account withdraws it.
>
> **Keeping it safe:** encrypted connections only, each family can reach only its own rows, and the site has
> no access keys in your browser that could read other families. If data were ever exposed, we would tell affected
> parents and, where the law requires, the Personal Data Protection Commission.
>
> **Questions or requests:** email psleadmin@gmail.com. We reply within 30 days.
>
> **Changes:** if this notice changes, you will be asked to read and agree to it again the next time you sign in.
>
> Last updated: `<date of release>`.
