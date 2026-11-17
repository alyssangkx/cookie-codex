// Progress sync over store.ts. load()/save() stay synchronous for the pages; this module watches save(),
// pushes the local save to the server (push_save, compare-and-set on rev) and pulls a newer server copy.
// The pure decisions are at the top and are tested in sync.test.ts; the rest talks to Supabase and the DOM.
import { backupLocal, clearDirty, clearLocal, hasProgress, isDirty, kv, readLocalRaw, replaceLocal, restoreDirty, setSaveHook, SCHEMA } from './store.ts';

// ---------------------------------------------------------------- pure decisions

export type HydrateAction = 'keep' | 'push-local' | 'use-server' | 'reset-local' | 'conflict';

/**
 * What to do with the local save when a child signs in or a page loads.
 * serverRev: rev of the server row (null: no row yet). lastRev: the rev this browser last synced for this child.
 * owner: the child id the local save was last synced for (null: an anonymous, pre-account save).
 * dirty: the local save has changes the server has not seen.
 */
export function decideHydrate(i: {
  serverRev: number | null; lastRev: number | null; owner: string | null; childId: string; dirty: boolean; localHasProgress: boolean;
}): HydrateAction {
  const mine = i.owner === i.childId;
  if (i.serverRev === null) {
    if (i.owner !== null && !mine) return 'reset-local'; // another child's save must never be pushed as this child's
    return i.localHasProgress || i.dirty ? 'push-local' : 'keep';
  }
  if (!mine) return 'use-server'; // a different (or unknown) owner: take the server copy, the local one is backed up
  if (i.lastRev === null || i.serverRev !== i.lastRev) return i.dirty ? 'conflict' : 'use-server';
  return i.dirty ? 'push-local' : 'keep';
}

export type PushRow = { status: string; rev: number | null; data: unknown; schema_version: number | null };
export type PushOutcome =
  | { kind: 'ok'; rev: number }
  | { kind: 'conflict'; rev: number; data: unknown }
  | { kind: 'denied' }
  | { kind: 'error' };

/** Read the one row push_save returns. Anything unexpected is an error (retry later), never a success. */
export function decidePush(rows: unknown, error: unknown): PushOutcome {
  if (error) return { kind: 'error' };
  const row = (Array.isArray(rows) ? rows[0] : rows) as PushRow | undefined;
  if (!row || typeof row.status !== 'string') return { kind: 'error' };
  if (row.status === 'ok' && row.rev !== null && row.rev !== undefined) return { kind: 'ok', rev: Number(row.rev) };
  if (row.status === 'conflict' && row.rev !== null && row.rev !== undefined) return { kind: 'conflict', rev: Number(row.rev), data: row.data };
  if (row.status === 'denied') return { kind: 'denied' };
  return { kind: 'error' };
}

/** The user's answer to the conflict banner. 'newer' takes the server copy; 'mine' overwrites it (p_force). */
export const resolveConflict = (choice: 'newer' | 'mine') => (choice === 'newer' ? 'adopt-server' : 'force-push') as 'adopt-server' | 'force-push';

/** Only a child's (or the Test Player's) own session syncs. An admin or parent session never does. */
export const isChildSession = (user: { app_metadata?: { role?: string } } | null | undefined) =>
  !!user && !['admin', 'parent'].includes(user.app_metadata?.role ?? '');

export const IDLE_DAYS = 90;
/** True when the last activity was more than 90 days ago. 0 or a missing stamp is not idle (a first visit). */
export const idleExpired = (lastSeenMs: number, now = Date.now()) =>
  Number.isFinite(lastSeenMs) && lastSeenMs > 0 && now - lastSeenMs > IDLE_DAYS * 86_400_000;

export const PUSH_DELAY_MS = 2000;

const pendingKey = (id: string) => `sync:pending:${id}`;

/**
 * Before deciding what to do for `id`: (1) an unsynced save that belongs to ANOTHER child is stashed under that child's
 * own key, so a later backup or adoption cannot overwrite it; (2) a save stashed earlier for `id` becomes the local save
 * again (unsynced), so it is pushed, or raises the conflict banner, like any local save.
 */
export function prepareLocal(id: string) {
  const owner = kv.get('sync:owner');
  const raw = readLocalRaw();
  if (owner !== null && owner !== id && raw && isDirty()) {
    kv.set(pendingKey(owner), raw);
    clearLocal();
  }
  const mine = kv.get(pendingKey(id));
  if (mine) {
    restoreDirty(mine);
    kv.set('sync:owner', id);
    kv.del(pendingKey(id));
  }
}

// ---------------------------------------------------------------- runtime

let childId: string | null = null;
let stopped = false;
let inflight = false;
let version = 0; // counts saves, so a push can tell whether more happened while it was in flight
let timer: ReturnType<typeof setTimeout> | undefined;
let wired = false;
let accessToken: string | null = null; // cached so the page-close flush needs no await
let inflightSeen = -1; // the version the in-flight push started from
let conflicted = false;
let afterConflict: (() => void) | null = null;
let firstPush: Promise<void> | null = null;
/** Called once the user keeps this device's copy and it was pushed (the login page navigates then). */
export const onConflictResolved = (fn: (() => void) | null) => { afterConflict = fn; };

const revKey = (id: string) => `sync:rev:${id}`;
const lastRev = (id: string) => { const v = kv.get(revKey(id)); return v === null ? null : Number(v); };
const sb = async () => (await import('./supabase.ts')).supabase;

function banner(text: string, buttons: [string, () => void][] = []) {
  document.getElementById('sync-banner')?.remove();
  const el = document.createElement('div');
  el.id = 'sync-banner';
  el.setAttribute('role', 'status');
  el.style.cssText = 'position:fixed;left:50%;transform:translateX(-50%);bottom:12px;z-index:50;max-width:min(92vw,560px);' +
    'background:var(--cream,#fff8ee);color:var(--cocoa,#4b2e1e);border:1.5px solid var(--crust,#d9b88f);border-radius:12px;' +
    'padding:10px 14px;font-size:0.95rem;box-shadow:0 4px 14px rgba(0,0,0,.18);display:flex;flex-wrap:wrap;gap:8px;align-items:center';
  const t = document.createElement('span'); t.textContent = text; el.append(t);
  for (const [label, fn] of buttons) {
    const b = document.createElement('button');
    b.type = 'button'; b.textContent = label;
    b.style.cssText = 'min-height:44px;padding:0 14px;border-radius:10px;border:1.5px solid var(--berry,#a3365b);background:#fff;color:var(--berry,#a3365b);font:inherit;font-weight:600;cursor:pointer';
    b.addEventListener('click', () => { el.remove(); fn(); });
    el.append(b);
  }
  document.body.append(el);
}

function schedule(ms = PUSH_DELAY_MS) {
  if (stopped || !childId) return;
  clearTimeout(timer);
  timer = setTimeout(() => { void push(); }, ms);
}

function adoptServer(id: string, rev: number, data: unknown) {
  backupLocal();
  replaceLocal(data);
  kv.set(revKey(id), String(rev));
  kv.set('sync:owner', id);
}

async function push(force = false) {
  if (stopped || !childId || inflight) return;
  const raw = readLocalRaw();
  if (!raw) return;
  const id = childId, seen = version;
  inflight = true; inflightSeen = seen;
  let out: PushOutcome;
  try {
    const r = await (await sb()).rpc('push_save', {
      p_child: id, p_data: JSON.parse(raw), p_version: SCHEMA, p_base_rev: lastRev(id), p_force: force,
    });
    out = decidePush(r.data, r.error);
  } catch { out = { kind: 'error' }; }
  inflight = false;
  if (out.kind === 'ok') {
    kv.set(revKey(id), String(out.rev));
    kv.set('sync:owner', id);
    if (version === seen) clearDirty(); else schedule(); // saved again meanwhile: push the newer one
  } else if (out.kind === 'conflict') {
    showConflict(id, out);
  } else if (out.kind === 'denied') {
    stopped = true;
    banner('Progress is saved on this device only. Syncing is switched off for this account.');
  } else {
    schedule(15_000); // offline or a server hiccup: the local copy keeps working; retry, and on the 'online' event
  }
}

function showConflict(id: string, c: { rev: number; data: unknown }) {
  conflicted = true;
  stopped = true; // no pushes until the user chooses
  clearTimeout(timer);
  banner('Progress on another device is newer:', [
    ['Use the newer one', () => {
      if (resolveConflict('newer') === 'adopt-server') { conflicted = false; adoptServer(id, c.rev, c.data); location.reload(); }
    }],
    ["Keep this device's", () => {
      if (resolveConflict('mine') === 'force-push') {
        kv.set(revKey(id), String(c.rev)); stopped = false; conflicted = false;
        void push(true).then(() => afterConflict?.());
      }
    }],
  ]);
}

/** Pull the child's server save and reconcile it with the local one. Returns true when the local save was replaced. */
export async function hydrate(id: string): Promise<boolean> {
  const client = await sb();
  prepareLocal(id);
  const r = await client.from('saves').select('rev, data').eq('child_id', id).maybeSingle();
  if (r.error) return false; // offline: play from the local copy; pushes retry later
  const local = readLocalRaw();
  let parsed: any = null;
  try { parsed = local ? JSON.parse(local) : null; } catch { /* unreadable: treated as no progress */ }
  const action = decideHydrate({
    serverRev: r.data ? Number(r.data.rev) : null, lastRev: lastRev(id), owner: kv.get('sync:owner'), childId: id,
    dirty: isDirty(), localHasProgress: hasProgress(parsed),
  });
  switch (action) {
    case 'use-server': adoptServer(id, Number(r.data!.rev), r.data!.data); return true;
    case 'reset-local': backupLocal(); clearLocal(); kv.set('sync:owner', id); return true;
    case 'conflict': showConflict(id, { rev: Number(r.data!.rev), data: r.data!.data }); return false;
    case 'push-local': kv.set('sync:owner', id); firstPush = push(); return false;
    default: kv.set('sync:owner', id); return false;
  }
}

/** Page close: browsers cancel a normal request, so send the save with a keepalive fetch (the rev check makes a duplicate harmless). */
function flushOnClose() {
  if (stopped || !childId || !accessToken || !isDirty()) return;
  if (inflight && version === inflightSeen) return; // the push in flight already carries this save
  const raw = readLocalRaw();
  if (!raw) return;
  try {
    void fetch(`${supaUrl}/rest/v1/rpc/push_save`, {
      method: 'POST', keepalive: true,
      headers: { apikey: anonKey, Authorization: 'Bearer ' + accessToken, 'Content-Type': 'application/json' },
      body: JSON.stringify({ p_child: childId, p_data: JSON.parse(raw), p_version: SCHEMA, p_base_rev: lastRev(childId), p_force: false }),
    }).catch(() => {});
  } catch { /* best effort */ }
}
let supaUrl = '', anonKey = '';

/**
 * Start syncing for the current session, if it is a child's. Resolves once the first pull (and, when the local save
 * was newer, the first push, up to 3 s) is done. Returns 'conflict' while the conflict banner is waiting for an answer.
 * reload: reload the page when the local save was replaced (off on the login page, which navigates itself).
 */
export async function initSync(opts: { reload?: boolean } = {}): Promise<'ok' | 'conflict' | 'skip'> {
  const mod = await import('./supabase.ts');
  const client = mod.supabase;
  supaUrl = mod.SUPABASE_URL; anonKey = mod.ANON_KEY;
  const { data } = await client.auth.getSession();
  const user = data.session?.user;
  if (!user || !isChildSession(user)) return 'skip';
  childId = user.id; // set before hydrating, so the push-local branch can push
  accessToken = data.session!.access_token;
  stopped = false;
  if (!wired) {
    wired = true;
    client.auth.onAuthStateChange((_e, s) => { accessToken = s?.access_token ?? null; });
    setSaveHook(() => { version++; schedule(); });
    window.addEventListener('online', () => { if (!stopped) void push(); });
    document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') flushOnClose(); });
    window.addEventListener('pagehide', flushOnClose);
  }
  firstPush = null;
  if (await hydrate(childId) && opts.reload !== false) { location.reload(); return 'ok'; }
  if (firstPush) await Promise.race([firstPush, new Promise((res) => setTimeout(res, 3000))]);
  return conflicted ? 'conflict' : 'ok';
}

/** Push what is pending (best effort, short wait), then sign out of this browser only and go to /login. */
export async function logout() {
  const client = await sb();
  try {
    if (childId && isDirty() && !stopped) await Promise.race([push(), new Promise((res) => setTimeout(res, 2500))]);
  } catch { /* leave anyway */ }
  try { await client.auth.signOut({ scope: 'local' }); } catch { /* the local session is cleared regardless */ }
  kv.del('lastSeen');
  kv.set('sync:signedout', '1'); // a logged-out device never gets offline access
  location.href = '/login';
}
