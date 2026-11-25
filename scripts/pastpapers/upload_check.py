#!/usr/bin/env python3
"""Check owner upload scripts against the LIVE database before handing them over (25 Nov 2026: a script built from a stale
folder would have switched off 95 live cloze rows, another 28 Vocabulary Cloze rows; the dry run cannot count switch-offs
without the service key).

  upload_check.py SCRIPT.sh [...] [--allow]

For every `python3 scripts/pastpapers/load_pp.py upload ...` line in each script (comment lines are skipped; `$VAR` set in
the script is expanded): the rows load_pp.py upload would send (its own `selection`: after hold.jsonl and the
lone-set drop), live active rows of the sub-topics it uploads that it does not send (the upload switches them off),
rows whose stem changes, live explanations the upload would no longer send (no explain.jsonl line whose fp matches the row),
and new rows. Read-only: one `supabase db query --remote --read-only` returning ids, md5 of the stem and whether an
explanation exists; no question text, no child data. Exit 1 when any row would be switched off or any live explanation
dropped, unless --allow (the script's header says how many are intended).
"""
import argparse
import collections
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
REPO = Path(__file__).resolve().parents[2]
CLI = os.environ.get("SUPABASE_CLI") or str(Path.home() / ".npm/_npx/a0b0486f7f118473/node_modules/.bin/supabase")


def upload_lines(text: str) -> list:
    """(subject, out, subtopics or None) per upload command of a bash script: backslash-continued lines joined, comment
    lines skipped, NAME=value (quoted or not) set earlier in the script expanded as $NAME / ${NAME}, --opt=value accepted.
    Pure (selftest)."""
    text = re.sub(r"\\\n", " ", text)
    var = {}
    out = []
    ap = argparse.ArgumentParser(add_help=False)
    for o in ("--subject", "--out", "--subtopics"):
        ap.add_argument(o)
    for line in text.splitlines():
        m = re.fullmatch(r"\s*(\w+)=(.*)", line)
        if m:
            var[m.group(1)] = (shlex.split(m.group(2)) or [""])[0]
            continue
        if not re.match(r"\s*python3 scripts/pastpapers/load_pp\.py upload\b", line):
            continue
        line = re.sub(r"\$\{(\w+)\}|\$(\w+)", lambda x: var.get(x.group(1) or x.group(2), x.group(0)), line)
        a, _ = ap.parse_known_args(shlex.split(line))
        out.append((a.subject, a.out, a.subtopics.split(",") if a.subtopics else None))
    return out


def compare(live: list, sel: list, expl: dict, fp) -> collections.Counter:
    """Counts for one upload: live = [{id, h, ex}] already filtered to its subject/sub-topics, sel = the folder's rows (same
    filter), expl = id -> explain.jsonl line, or None when the folder has no explain.jsonl (the upload then leaves live
    explanations alone). Pure (selftest)."""
    rows = {r["id"]: r for r in sel}
    c = collections.Counter()
    for d in live:
        r = rows.get(d["id"])
        if r is None:
            c["switched off"] += 1
            continue
        if hashlib.md5(r["stem"].encode()).hexdigest() != d["h"]:
            c["stem changed"] += 1
        if expl is not None and d["ex"] and not (d["id"] in expl and expl[d["id"]].get("fp") == fp(r)):
            c["explanation dropped"] += 1
    c["new"] = len(set(rows) - {d["id"] for d in live})
    return c


def live_rows() -> list:
    sql = ("select id, subject, subtopic, md5(stem) h, (explain is not null) ex from pp_items where active")
    p = subprocess.run([CLI, "db", "query", "--remote", "--read-only", "-o", "json", sql], cwd=REPO, capture_output=True,
                       text=True, timeout=300)
    if p.returncode:
        sys.exit(f"supabase query failed (exit {p.returncode}); log in from your own terminal first")
    return json.loads(p.stdout)["rows"]


def jl(p):
    return [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()]


def selftest():
    t = "set -e\nC=a-x,a-y\n# python3 scripts/pastpapers/load_pp.py upload --subject maths --out /old\n" \
        "python3 scripts/pastpapers/load_pp.py upload --subject english --out /f --subtopics $C \"$@\"\n"
    assert upload_lines(t) == [("english", "/f", ["a-x", "a-y"])]  # the commented line is skipped, $C expanded
    t2 = 'C=x\nCC="a-z"\npython3 scripts/pastpapers/load_pp.py upload --subject english --out=/g \\\n  --subtopics $CC --apply\n'
    assert upload_lines(t2) == [("english", "/g", ["a-z"])]  # continuation, --out=, $CC not read as $C + "C", quoted value
    h = hashlib.md5(b"S").hexdigest()
    live = [{"id": "1", "h": h, "ex": True}, {"id": "2", "h": h, "ex": True}, {"id": "3", "h": h, "ex": False}]
    sel = [{"id": "1", "stem": "S"}, {"id": "3", "stem": "T"}, {"id": "4", "stem": "S"}]
    c = compare(live, sel, {"1": {"fp": "x"}}, lambda r: "y")
    assert (c["switched off"], c["stem changed"], c["explanation dropped"], c["new"]) == (1, 1, 1, 1)
    assert compare(live, sel, None, lambda r: "y")["explanation dropped"] == 0  # no explain.jsonl: live ones are kept
    print("selftest ok")


def main(argv):
    if argv[:1] == ["selftest"]:
        return selftest()
    allow = "--allow" in argv
    scripts = [a for a in argv if a != "--allow"]
    if not scripts:
        sys.exit(__doc__)
    from explain import fp
    import load_pp
    live = live_rows()
    bad = 0
    for s in scripts:
        for subj, out, subs in upload_lines(Path(s).read_text(encoding="utf-8")):
            # load_pp's own selection: after hold.jsonl and the lone-set drop; switch-offs only in the sub-topics it uploads
            sel, usubs, _ = load_pp.selection(argparse.Namespace(subject=subj, out=out, subtopics=",".join(subs) if subs else None))
            keep = lambda r: r["subject"] == subj and r["subtopic"] in usubs
            ep = Path(out) / subj / "explain.jsonl"
            expl = {x["id"]: x for x in jl(ep)} if ep.exists() else None
            c = compare([d for d in live if keep(d)], sel, expl, fp)
            bad += c["switched off"] + c["explanation dropped"]
            print(f"{Path(s).name:24} {subj:8} {out[-48:]:48} live {sum(map(keep, live)):5} sel {len(sel):5} "
                  f"off {c['switched off']} stem {c['stem changed']} expl-dropped {c['explanation dropped']} new {c['new']}")
    if bad and not allow:
        sys.exit(f"FAIL: {bad} live rows would be switched off or lose their explanation (pass --allow if intended)")


if __name__ == "__main__":
    main(sys.argv[1:])
