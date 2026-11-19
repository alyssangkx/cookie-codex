// Live two-family isolation check (docs/accounts-plan.md 12.12). Run ONLY after 002 is applied and parent-api is
// deployed. Creates two throwaway parent accounts and their children, checks that neither family can see or change
// the other's, then deletes everything it made (finally). Never touches any other account.
//
//   set -a; . site/.env; set +a                     # the public URL and anon key
//   read -rs SUPABASE_SERVICE_ROLE_KEY; export SUPABASE_SERVICE_ROLE_KEY   # paste, nothing is shown
//   node scripts/accounts/isolation.mjs; unset SUPABASE_SERVICE_ROLE_KEY
//
// The service-role key is read from the environment and never printed. Exit 0 = every check passed.
const URL_ = process.env.SUPABASE_URL ?? process.env.PUBLIC_SUPABASE_URL;
const ANON = process.env.SUPABASE_ANON_KEY ?? process.env.PUBLIC_SUPABASE_ANON_KEY;
const SVC = process.env.SUPABASE_SERVICE_ROLE_KEY;
if (!URL_ || !ANON || !SVC) { console.error('set SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY'); process.exit(2); }
if (SVC.startsWith('sb_publishable_') || SVC === ANON) { console.error('that is the public key; paste the secret (service_role / sb_secret_) key'); process.exit(2); }

let failed = 0;
const ok = (c, what) => { console.log(`${c ? 'ok  ' : 'FAIL'} ${what}`); if (!c) failed++; };
// New-style keys (sb_publishable_..., sb_secret_...) go in the apikey header only (the gateway turns them into a JWT);
// a Bearer header must then be a real JWT or be left out. Legacy keys are JWTs and work either way.
const isJwt = (t) => typeof t === 'string' && t.split('.').length === 3;
const req = async (path, { method = 'GET', token = ANON, key = ANON, body, headers = {} } = {}) => {
  const r = await fetch(`${URL_}${path}`, {
    method, headers: { apikey: key, ...(isJwt(token) ? { authorization: `Bearer ${token}` } : {}), 'content-type': 'application/json', ...headers },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  let json = null; try { json = await r.json(); } catch { /* empty */ }
  return { status: r.status, body: json };
};
const admin = (path, opts = {}) => req(`/auth/v1/admin${path}`, { ...opts, token: SVC, key: SVC });
const rest = (token, path, opts = {}) => req(`/rest/v1/${path}`, { ...opts, token });
const fn = (token, body) => req('/functions/v1/parent-api', { method: 'POST', token, body });
const rnd = () => Math.random().toString(36).slice(2, 10);

const made = []; // auth user ids to delete
async function parent() {
  const email = `ccx-iso-${rnd()}@example.com`, password = `${rnd()}${rnd()}Aa1!`;
  const u = await admin('/users', { method: 'POST', body: { email, password, email_confirm: true } });
  if (u.status !== 200) throw new Error(`create parent ${u.status}`);
  made.push(u.body.id);
  // Auth CAPTCHA is on: a password grant with the service-role key is exempt (as in pin-login); the token is the parent's
  const signIn = async () => (await req('/auth/v1/token?grant_type=password', { method: 'POST', token: SVC, key: SVC, body: { email, password } })).body.access_token;
  let token = await signIn();
  const reg = await fn(token, { action: 'register', consent_version: '1' });
  if (reg.status !== 200) throw new Error(`register ${reg.status} ${reg.body?.error}`);
  token = await signIn(); // the role is in the new token
  const kid = await fn(token, { action: 'create_child', name: 'Emma', pin: '3817' });
  if (kid.status !== 200) throw new Error(`create_child ${kid.status} ${kid.body?.error}`);
  made.push(kid.body.child.id);
  return { id: u.body.id, email, token, code: reg.body.code, child: kid.body.child.id };
}

try {
  const A = await parent(), B = await parent();
  ok(A.code !== B.code, 'two families, two codes; the same child name in both');
  for (const [me, other, n] of [[A, B, 'A'], [B, A, 'B']]) {
    const prof = await rest(me.token, 'profiles?select=id,parent_id');
    ok(prof.status === 200 && prof.body.length === 1 && prof.body[0].id === me.child, `${n} sees only its own child`);
    const fam = await rest(me.token, 'families?select=parent_id,code');
    ok(fam.status === 200 && fam.body.length === 1 && fam.body[0].parent_id === me.id, `${n} sees only its own family row`);
    const pin = await rest(me.token, 'profiles?select=pin_hash');
    ok(pin.status !== 200, `${n} cannot read pin_hash`);
    const push = await rest(me.token, 'rpc/push_save', { method: 'POST', body: { p_child: other.child, p_data: { schemaVersion: 4 }, p_version: 4 } });
    ok(push.status === 200 && push.body?.[0]?.status === 'denied', `${n} push_save on the other child is denied`);
    const own = await rest(me.token, 'rpc/push_save', { method: 'POST', body: { p_child: me.child, p_data: { schemaVersion: 4 }, p_version: 4 } });
    ok(own.status === 200 && own.body?.[0]?.status === 'ok', `${n} push_save on its own child works`);
    const saves = await rest(me.token, 'saves?select=child_id');
    ok(saves.status === 200 && saves.body.every((s) => s.child_id === me.child), `${n} reads only its own child's save`);
    await rest(me.token, `profiles?id=eq.${other.child}`, { method: 'PATCH', body: { name: 'Hacked' } });
    await rest(me.token, `saves?child_id=eq.${other.child}`, { method: 'DELETE' });
    for (const action of ['set_pin', 'rename_child', 'clear_name_lock', 'delete_child']) {
      const r = await fn(me.token, { action, child_id: other.child, pin: '5049', name: 'Zed', confirm: 'Emma' });
      ok(r.status === 404, `${n} parent-api ${action} on the other child is 404`);
    }
    for (const bad of [{ action: 'create_child', name: 'Admin', pin: '5049' }]) {
      const r = await fn(me.token, bad);
      ok(r.status === 400 && r.body?.error === 'name_reserved', `${n} cannot name a child Admin`);
    }
    const weak = await fn(me.token, { action: 'set_pin', child_id: me.child, pin: '1234' });
    ok(weak.status === 400 && weak.body?.error === 'weak_pin', `${n} weak PIN refused`);
  }
  const svcProf = await rest(SVC, `profiles?select=name&id=in.(${A.child},${B.child})`, { key: SVC });
  ok(svcProf.body?.every((p) => p.name === 'Emma'), 'neither child was renamed by the other parent');
  const svcSaves = await rest(SVC, `saves?select=child_id&child_id=in.(${A.child},${B.child})`, { key: SVC });
  ok(svcSaves.body?.length === 2, 'neither save was deleted by the other parent');
  // delete and undo (soft delete, 7 days)
  const del = await fn(A.token, { action: 'delete_account', confirm: A.email });
  ok(del.status === 200, 'A deletes the account');
  const after = await fn(A.token, { action: 'create_child', name: 'Mia', pin: '5049' });
  ok(after.status === 410, 'a deleted account can only restore');
  const pushDel = await rest(A.token, 'rpc/push_save', { method: 'POST', body: { p_child: A.child, p_data: { schemaVersion: 4 }, p_version: 4, p_force: true } });
  ok(pushDel.body?.[0]?.status === 'denied', "A's child can no longer be written");
  const res = await fn(A.token, { action: 'restore_account' });
  ok(res.status === 200, 'A restores the account');
} catch (e) {
  failed++; console.log('FAIL', e instanceof Error ? e.message : 'error');
} finally {
  for (const id of made.reverse()) await admin(`/users/${id}`, { method: 'DELETE' }); // children first: reversed order
  const left = await Promise.all(made.map((id) => admin(`/users/${id}`)));
  ok(left.every((r) => r.status === 404), `cleanup: all ${made.length} throwaway users deleted`);
}
console.log(failed ? `${failed} FAILED` : 'ALL ISOLATION CHECKS PASSED');
process.exit(failed ? 1 : 0);
