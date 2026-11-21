#!/usr/bin/env bash
# Run 001-006 (then 007 after their checks) against a throwaway Postgres 15 container and check the rules in test_accounts.sql, test_pp_items.sql, test_reports.sql and test_pp_serve.sql. Exit 0 = all passed.
# Needs docker. Touches no real database.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); mig="$here/../../supabase/migrations"
name=ccx-sqltest-$$
docker run -d --rm --name "$name" -e POSTGRES_PASSWORD=x postgres:15-alpine >/dev/null
trap 'docker stop "$name" >/dev/null 2>&1 || true' EXIT
for _ in $(seq 60); do docker exec "$name" pg_isready -U postgres -q 2>/dev/null && break; sleep 1; done
sleep 1
run() { docker exec -i "$name" psql -U postgres -v ON_ERROR_STOP=1 -q -X "$@"; }
cat "$here/stub_supabase.sql" "$here/stub_storage.sql" "$mig/001_init.sql" "$here/seed_001.sql" "$mig/002_parents.sql" "$mig/003_no_family_code.sql" "$mig/004_pp_items.sql" "$mig/005_question_reports.sql" "$mig/006_pp_serve.sql" "$mig/008_pp_serve_active_only.sql" | run -o /dev/null
out=$(run -t -o /dev/null < "$here/test_accounts.sql" 2>&1) || { echo "$out" | sed 's/^psql:<stdin>:[0-9]*: //' | grep -v '^$'; exit 1; }
echo "$out" | sed -n 's/^.*NOTICE:  //p'; echo "$out" | grep -q 'ALL CHECKS PASSED' && echo 'ALL CHECKS PASSED'
pp=$(run -t -o /dev/null < "$here/test_pp_items.sql" 2>&1) || { echo "$pp" | sed 's/^psql:<stdin>:[0-9]*: //' | grep -v '^$'; exit 1; }
echo "$pp" | sed -n 's/^.*NOTICE:  //p'; echo "$pp" | grep -q 'PP CHECKS PASSED' && echo 'PP CHECKS PASSED'
rq=$(run -t -o /dev/null < "$here/test_reports.sql" 2>&1) || { echo "$rq" | sed 's/^psql:<stdin>:[0-9]*: //' | grep -v '^$'; exit 1; }
echo "$rq" | sed -n 's/^.*NOTICE:  //p' | tail -4; echo "$rq" | grep -q 'REPORT CHECKS PASSED' && echo 'REPORT CHECKS PASSED'
ps=$(run -t -o /dev/null < "$here/test_pp_serve.sql" 2>&1) || { echo "$ps" | sed 's/^psql:<stdin>:[0-9]*: //' | grep -v '^$'; exit 1; }
echo "$ps" | sed -n 's/^.*NOTICE:  //p' | tail -4; echo "$ps" | grep -q 'PP SERVE CHECKS PASSED' && echo 'PP SERVE CHECKS PASSED'
run -o /dev/null < "$mig/007_pp_lockdown.sql"
ld=$(run -t -o /dev/null < "$here/test_pp_lockdown.sql" 2>&1) || { echo "$ld" | sed 's/^psql:<stdin>:[0-9]*: //' | grep -v '^$'; exit 1; }
echo "$ld" | sed -n 's/^.*NOTICE:  //p'; echo "$ld" | grep -q 'LOCKDOWN CHECKS PASSED' && echo 'LOCKDOWN CHECKS PASSED'
