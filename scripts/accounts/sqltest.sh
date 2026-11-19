#!/usr/bin/env bash
# Run 001 + 002 against a throwaway Postgres 15 container and check the rules in test_002.sql. Exit 0 = all passed.
# Needs docker. Touches no real database.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); mig="$here/../../supabase/migrations"
name=ccx-sqltest-$$
docker run -d --rm --name "$name" -e POSTGRES_PASSWORD=x postgres:15-alpine >/dev/null
trap 'docker stop "$name" >/dev/null 2>&1 || true' EXIT
for _ in $(seq 60); do docker exec "$name" pg_isready -U postgres -q 2>/dev/null && break; sleep 1; done
sleep 1
run() { docker exec -i "$name" psql -U postgres -v ON_ERROR_STOP=1 -q -X "$@"; }
cat "$here/stub_supabase.sql" "$mig/001_init.sql" "$here/seed_001.sql" "$mig/002_parents.sql" | run -o /dev/null
out=$(run -t -o /dev/null < "$here/test_002.sql" 2>&1) || { echo "$out" | sed 's/^psql:<stdin>:[0-9]*: //' | grep -v '^$'; exit 1; }
echo "$out" | sed -n 's/^.*NOTICE:  //p'; echo "$out" | grep -q 'ALL CHECKS PASSED' && echo 'ALL CHECKS PASSED'
