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

- `profiles(id pk -> auth.users, parent_id -> auth.users, name, role child|test, pin_hash, pin_set_at, created_at)`.
  The spec's columns plus `role` and `pin_set_at`. Child names are unique (case-insensitive) while
  login is by name; when a second family joins, add a family code and make it unique per parent.
- `saves(child_id pk -> profiles, data jsonb, schema_version int, updated_at timestamptz)`.
  `updated_at` is set by a trigger, so the server clock decides, not the phone's. Size capped at 2 MB.
- `private.pin_attempts(key, fails, locked_until, updated_at)`: lockout counters, no client access.
- `public.push_save(...)`: compare-and-set write for sync (section 6).
- `public.pin_locked_until / pin_record_failure / pin_clear`: lockout helpers, **service role only**.

### RLS

Both tables have RLS on. Access is by `auth.uid()`:

| | profiles | saves |
|---|---|---|
| select | `parent_id = uid` or `id = uid` (the child) or admin | owning parent, the child itself, or admin |
| insert | `parent_id = uid` (a profile also needs an auth user, so creation really goes through a function) | owning parent or the child |
| update | `parent_id = uid`, **name column only** | owning parent or the child |
| delete | `parent_id = uid` | owning parent |

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

**Lockout.** Counters live in `private.pin_attempts`, updated atomically by `pin_record_failure`.
Three keys per attempt:

| Key | Limit | Why |
|---|---|---|
| `device:<deviceId>` | 5 wrong, then 15 min | the spec's per-device lock |
| `name:<lowercase name>` | 5 wrong, then 15 min | the spec's per-child lock; keyed by typed name so a nonexistent name behaves identically |
| `ip:<sha256 of address>` | 20 wrong, then 15 min | stops rotating `deviceId` (client-controlled); looser for shared Wi-Fi; stored hashed |

Order: check locks first (a locked key returns 429 without comparing the PIN), then compare, then
on failure increment all three; on success clear device and name. A failure older than 15 minutes
restarts the count. Known trade-off: anyone who knows her name can lock her out for 15 minutes by
guessing. That is accepted; the admin can see lock state and the lock expires on its own.

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
  - **Conflict:** the push sends the `updated_at` the client last saw. If the server row has moved
    on (another device played), nothing is overwritten and the server copy comes back with
    `status: 'conflict'`. The client shows a plain warning ("Alyssa played on another device")
    and offers the newer copy. The default is the **newer `updated_at`, i.e. last write wins**, as
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
7. **Lockout of Alyssa by others:** acceptable that a guessed name can lock her for 15 minutes?
