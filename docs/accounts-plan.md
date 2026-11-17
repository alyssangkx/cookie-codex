# Accounts plan: Supabase login for Alyssa's Cookie Codex

Status: **Phase A, awaiting approval.** Nothing in this plan has been applied, deployed or created.
The SQL is in `supabase/migrations/001_init.sql`, the PIN function source is in
`supabase/functions/pin-login/index.ts` (with `_shared/pin.ts`). Neither has been run: there was no
Postgres or Deno on the dev machine, so both are untested until the Supabase project exists.

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
2. The browser posts `{ name, pin, deviceId }` to the `pin-login` Edge Function. `deviceId` is a
   random id generated once and kept in localStorage.
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
  The spec's columns plus `role` and `pin_set_at`. `name` is 1-20 letters, spaces or hyphens.
  `name_key` is `lower(btrim(name))`, generated and stored, with a unique index: login does an
  exact `eq('name_key', ...)`, never `ilike`/`like`. Names are globally unique while login is by name; when a second family joins, add a family code and make it unique per parent.
- `saves(child_id pk -> profiles, data jsonb, schema_version int, rev bigint, updated_at timestamptz)`.
  `rev` starts at 0 and goes up by one on every write (a trigger enforces it too). `updated_at` is set
  by a trigger, so the server clock decides, not the phone's. Size capped at 2 MB.
- `private.pin_attempts(key, fails, strikes, locked_until, updated_at)`: lockout counters, no client access.
- `public.push_save(...)`: compare-and-set write on `rev` for sync (section 6).
- `public.pin_locked_until / pin_record_failure / pin_clear`: lockout helpers, **service role only**.

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
`attemptsLeft` (identical for an unknown name, so names cannot be enumerated); 429 `locked` with
`retryAfterSec`.

**Hashing.** PBKDF2-HMAC-SHA256, 600,000 iterations, a random 16-byte salt per child, stored as
`pbkdf2-sha256$iterations$salt$hash`. The PIN is mixed with `PIN_PEPPER`, a function secret that is
not in the database. Chosen over argon2/scrypt because it is native Web Crypto in the Edge
runtime with no WASM or dependency. Honest limit: a 4-digit PIN has 10,000 values, so if the
database **and** the pepper both leaked the PIN would fall instantly. The pepper plus the lockout
are the real protection; the hash only stops casual exposure. This is acceptable because the
PIN guards a child's quiz progress, not money or contact data.

**Name checks.** The name is trimmed of spaces, lowercased, and must be 1-20 letters, spaces or
hyphens. Anything else is rejected before any lookup, counts against the device limit, and answers
like a wrong PIN. The lookup is `eq('name_key', key)`: no pattern matching anywhere.

**Lockout.** Counters live in `private.pin_attempts`, updated atomically by `pin_record_failure`.

| Key | Limit | Why |
|---|---|---|
| `device:<deviceId>` | 5 wrong, then 15 min | the spec's per-device lock. `deviceId` is client-chosen, so this only stops a well-behaved browser |
| `name:<name_key>` | 20 wrong from anywhere, then a lock that doubles each time it trips: 15 min, 30 min, 1 h, 2 h, 4 h, 8 h, 16 h, 24 h, then 24 h | the **real brute-force bound**, because headers and device ids can be forged. Keyed by the typed name, so an unknown name behaves identically. A successful login resets the count and the escalation |
| IP | **none** | see below |

**Why no IP limit.** Supabase documents no client-IP header for Edge Functions that a caller cannot
forge: `x-forwarded-for` can be supplied by the caller (reported in
[supabase/discussions/34647](https://github.com/orgs/supabase/discussions/34647)), and `x-real-ip` /
`cf-connecting-ip` are not documented for Edge Functions. A limit on a forgeable value adds nothing,
and a shared `unknown` bucket would let one stranger lock everyone out. If Supabase later documents a
trustworthy header, add it as a third, looser key.

**Worst-case guessing rate.** An attacker who forges every device id and address is still bound by
the name lock: 20 tries, then locks of 15 min, 30 min, 1 h, 2 h, 4 h, 8 h, 16 h and 24 h, so about 160
guesses in 2.3 days and then 20 per day. The 10,000 PINs take about 500 days, about 250 expected,
and each guess costs a 600,000-iteration PBKDF2. A locked key answers 429 without comparing the PIN
and without counting further, so parallel requests cannot escalate it.

Order: check locks first, then compare, then on failure increment device and name; on success clear
both. Known trade-off: anyone who knows her name can lock her out by guessing 20 times, for up to 24
hours if they repeat it; the admin can clear a lock (`pin_clear`) from `/admin/`. Accepted. Untested:
needs a Supabase project.

**Issuing the session.** After a correct PIN the function signs in as the child's own auth user
with the derived password (`signInWithPassword` using the anon key) and returns the session tokens.
No custom JWT signing, so Supabase's own refresh and revocation work unchanged. Unknown names run
a full dummy hash compare so timing does not reveal which names exist.

**Secrets:** `PIN_PEPPER`, `CHILD_PW_SECRET` (function secrets), optional `SITE_ORIGIN` for CORS.
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
    devices creating the row cannot both win. If the server row has moved on (another device
    played), nothing is overwritten and the server copy comes back with `status: 'conflict'`. The client shows a plain warning ("Alyssa played on another device")
    and offers the newer copy. The default is the **higher `rev`, i.e. last write wins**, as
    decided, but it is chosen consciously by the user, not silently. A later improvement is a field
    merge (union of `days` and `attempts`, max `stars`, later `due` per question); see open questions.
  - **Offline:** writes only hit the cache and stay pending; on the next load or `online` event
    the push retries. The cache is always playable.
- **Backup:** the migration already copies the pre-migration save to `ccx:backup`.
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
| `/login/` | "Who's playing?" tiles for remembered names, plus name + PIN pad. Wrong PIN shows attempts left; locked shows a countdown. Small "Grown-ups" link to the admin form. |
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
7. **Lockout of Alyssa by others:** accepted: a guessed name can lock her, escalating up to 24 hours; the admin can clear it.

## Decisions (2026-11-17, approved at Checkpoint A)

| Question | Decision |
|---|---|
| Free-tier pausing | Stay on the free plan; a scheduled keep-alive pings the project every 3 days. Revisit Pro when more children join. |
| PIN lockout | Per device: 5 wrong PINs lock it for 15 minutes. A name locks after 20 wrong tries from anywhere, with the lock doubling each time (15 min up to 24 h) and resetting on a successful login; that name limit is the real bound. No IP limit: no trustworthy client-IP header exists on Edge Functions (section 5). |
| Admin second factor | Required: Supabase TOTP (authenticator app) on the admin account. |
| Hosting | Vercel, free `*.vercel.app` subdomain, deployed from the GitHub repo; custom domain later. |
| Sync conflict | Newer save wins, with a visible warning; no field merge yet. |
| Child names | Globally unique for now (one family). |
| `/parent/` PIN screen | Dropped once the admin session gates the page. |
