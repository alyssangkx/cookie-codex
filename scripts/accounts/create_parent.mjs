// Create a parent account the owner sets up by hand (no email confirmation) and move an existing child into it
// (owner, 23 Nov 2026: a parent login for Alyssa's family; the child's username, PIN, progress and cards are untouched).
// Does what sign-up + parent-api `register` do: the Auth user (email already confirmed), the families row with the
// privacy-notice version, then app_metadata.role = 'parent'; then the child's profiles.parent_id moves to the new parent.
//
// Run in the owner's terminal only (the service-role key never leaves it):
//   export SUPABASE_URL=https://<project>.supabase.co
//   read -rs SUPABASE_SERVICE_ROLE_KEY && export SUPABASE_SERVICE_ROLE_KEY
//   read -rs PARENT_PASSWORD && export PARENT_PASSWORD
//   node scripts/accounts/create_parent.mjs --email someone@example.com --child Alyssa          # dry run: what would change
//   node scripts/accounts/create_parent.mjs --email someone@example.com --child Alyssa --apply  # do it
// Prints counts and outcomes only: never the password, the key or a PIN.
const args = process.argv.slice(2);
const arg = (k) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : undefined; };
const email = (arg('--email') || '').trim().toLowerCase();
const child = (arg('--child') || '').trim();
const apply = args.includes('--apply');
const CONSENT_VERSION = '1'; // site/src/lib/supabase.ts CONSENT_VERSION: the notice this parent is recorded as accepting
const url = (process.env.SUPABASE_URL || '').replace(/\/$/, '');
const key = (process.env.SUPABASE_SERVICE_ROLE_KEY || '').trim();
const password = process.env.PARENT_PASSWORD || '';
const die = (m) => { console.error('STOP: ' + m); process.exit(1); };
if (!url || !key) die('SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set');
if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) die('--email is not an email address');
if (!child) die('--child <username> is required');
if (password.length < 6) die('PARENT_PASSWORD must be set (6 characters or more)');
const H = { apikey: key, 'content-type': 'application/json', ...(key.startsWith('eyJ') ? { authorization: `Bearer ${key}` } : {}) };
const call = async (method, path, body, extra = {}) => {
  const r = await fetch(url + path, { method, headers: { ...H, ...extra }, body: body ? JSON.stringify(body) : undefined });
  const t = await r.text();
  if (!r.ok) die(`${method} ${path.split('?')[0]} -> HTTP ${r.status} ${t.slice(0, 160)}`);
  return t ? JSON.parse(t) : null;
};

// the child: exactly one live child profile with that username (usernames are unique site-wide)
const nameKey = child.trim().toLowerCase(); // profiles.name_key = lower(btrim(name)) (001_init.sql)
const kids = await call('GET', `/rest/v1/profiles?select=id,parent_id,role,deleted_at&name_key=eq.${encodeURIComponent(nameKey)}&role=eq.child&deleted_at=is.null`);
if (kids.length !== 1) die(`expected exactly 1 live child named ${child}, found ${kids.length}`);
const kid = kids[0];
// the parent: an existing Auth user with that email is reused only if it is not already someone else's admin
const found = await call('GET', `/auth/v1/admin/users?per_page=1000`);
const existing = (found.users || []).find((u) => (u.email || '').toLowerCase() === email);
if (existing && existing.app_metadata?.role === 'admin') die('that email is an admin account: not touched');
console.log(`child ${child}: found (currently in another family: ${kid.parent_id !== existing?.id})`);
console.log(`parent ${email}: ${existing ? 'exists, will be made a parent' : 'will be created, email marked confirmed'}`);
if (!apply) { console.log('dry run: nothing changed. Add --apply to create the parent and move the child.'); process.exit(0); }

let parentId = existing?.id;
if (!existing) {
  const u = await call('POST', '/auth/v1/admin/users', { email, password, email_confirm: true });
  parentId = u.id;
} else {
  await call('PUT', `/auth/v1/admin/users/${parentId}`, { password, email_confirm: true });
}
// family row first, role second (as parent-api register: a parent role never exists without its consent record)
await call('POST', '/rest/v1/families?on_conflict=parent_id', { parent_id: parentId, consent_version: CONSENT_VERSION },
  { prefer: 'resolution=ignore-duplicates,return=minimal' });
const me = await call('GET', `/auth/v1/admin/users/${parentId}`);
await call('PUT', `/auth/v1/admin/users/${parentId}`, { app_metadata: { ...(me.app_metadata || {}), role: 'parent' } });
// move the child: only parent_id changes (username, PIN hash, save, cards and progress stay as they are)
await call('PATCH', `/rest/v1/profiles?id=eq.${kid.id}`, { parent_id: parentId }, { prefer: 'return=minimal' });
const check = await call('GET', `/rest/v1/profiles?select=parent_id&id=eq.${kid.id}`);
console.log(check[0]?.parent_id === parentId ? `done: ${email} is a parent and ${child} is in that family` : 'STOP: the child did not move');
