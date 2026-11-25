#!/usr/bin/env python3
"""Maths and Science past-paper explanations, first tranche (24-25 Nov 2026): TEXT-ONLY questions (no figure) of the 10 Maths and
10 Science sub-topics with the most of them. A child who answers wrong sees "Why <answer> is right: ..." and, beside the option
picked, why it is wrong. Claude agents write and check; this script picks, packs, lints, ties verdicts to what was checked, and
applies. It reuses section_explain.py (verdict files, ties, merge, doubts) and explain.py (fp); it changes neither.

  ms_explain.py pick                    both subjects: the live text-only counts per sub-topic, the top 10 of each -> WORK/<subject>/chosen.json
  ms_explain.py pack SUBJECT [--force]  writer packs -> WORK/<subject>/pack_N.jsonl (about 60 questions each; writers fill out_N.jsonl)
  ms_explain.py lint SUBJECT            the rule checks, counted by reason
  ms_explain.py checkpack SUBJECT       lint-clean items without a verdict that still holds -> cpack_rR_N.jsonl (checkers fill check_rR_N.jsonl)
  ms_explain.py recheck SUBJECT TAG     the same, one pack -> cpack_TAG.jsonl (-> check_TAG.jsonl)
  ms_explain.py apply SUBJECT [--write] [--drop-failed]
                                        lint-clean + checker-passed + no doubt, MERGED with the lines already in the live selection's
                                        explain.jsonl (nothing existing is dropped, except a stale fp or --drop-failed). Without
                                        --write the merged file goes to WORK/<subject>/explain.preview.jsonl and the selection is
                                        not touched; with --write it replaces <selection>/explain.jsonl (a backup first).
  ms_explain.py selftest

SUBJECT is maths or science. WORK is /data/alvin/tmp/cookie-codex/msexp (env SECEXP_WORK, as in section_explain.py; SECEXP_SEL
replaces the selection folder for the run). LIVE selections (24 Nov 2026, checked against public.pp_items: every active row is in
the selection and every selection row is active): maths -> ppimport/math1826h/maths (upload/dedupe.sh), science ->
ppimport/sci1826g/science (upload/science_audit.sh). Past-paper text stays out of the repo; WORK is outside it.

WRITER CONTRACT. A pack line: {"id", "sub", "stem", "options" (stored order), "key" (0-based index of the right option)}.
Work the question YOURSELF first and note your own answer as "blind" BEFORE you look at "key". Then write, per question, one line of
out_N.jsonl (same N as pack_N.jsonl):
  {"id", "blind": <your own answer index>, "doubt": "<only if blind differs from key, or the question is faulty or ambiguous>",
   "right": "<why the key is right>", "wrong": [<a note per option in stored order; null at the key's index>]}
Rewrites after a failed check go in out_fix<anything>.jsonl (same shape), which override out_N in name order.
A doubt means the question is NOT explained (it goes to doubts.jsonl for the owner); never explain a key you believe is wrong.
  MATHS "right": the working in at most 3 short steps with the numbers, plain text (no LaTeX; fractions as 3/4, "x" or "×" for
  times), ending with the answer value, which must appear exactly as the key option's number (12, 3/4, 2.5, $5.40; units may be left
  off). Each wrong note names the likely MISTAKE that gives that option, with the numbers ("Added instead of multiplying: 12 + 5 = 17.").
  Made-up example (the options are shuffled on screen):
  stem "A pen costs $3 and a book costs 4 times as much. How much do they cost together?" options ["$12","$15","$7","$24"] key 1
  {"id": "pp-0000000001", "blind": 1, "right": "The book costs 4 x $3 = $12. Together: $3 + $12 = $15.", "wrong": ["Found only the price of the book: 4 x 3 = 12.", null, "Added 3 + 4 = 7 instead of multiplying for the book.", "Multiplied the two prices by 4 again: 3 x 4 x 2 = 24."]}
  SCIENCE "right": the concept in one or two sentences a 12-year-old follows, tied to the words of the question, naming the key
  option's words. Each wrong note says why that option is not true, or does not answer the question. PSLE syllabus only (no mass
  and acceleration, no action-reaction).
  Made-up example: stem "Which part of a plant takes in water from the soil?" options ["Leaf","Root","Flower","Stem"] key 1
  {"id": "pp-0000000002", "blind": 1, "right": "The root grows in the soil and takes in water, which then moves up the stem to the leaves.", "wrong": ["The leaf makes food and lets gases in and out; it does not take water from the soil.", null, "The flower makes seeds and does not take in water from the soil.", "The stem carries water upwards but does not take it in from the soil."]}
  BOTH: no "!"; never start "The answer is"; never name an option by letter or number ("(2)", "option B", "answer 3": the options are
  shuffled on the site); every wrong note talks about its own option; "right" 15-600 characters, a wrong note at most 400.

CHECKER CONTRACT. A cpack line is {"grp", "sub", "questions": [{"id", "n", "stem", "options", "key", "explanation": {"right", "wrong"},
"fp"}]}. For each question, work it yourself, then judge the explanation. Write check_X.jsonl beside cpack_X.jsonl, one line each:
  {"id", "ok": true|false, "reason": "<what is wrong, when ok is false>", "doubt": "<only if the key itself looks wrong>"}
ok is true only when ALL hold: the key is right and "right" is correct and complete (Maths: every step recomputed); every wrong note is
true of ITS option (Maths: the named mistake really gives that option's number; Science: the statement is correct, so the option is
indeed wrong, within the PSLE syllabus); nothing is misleading, unfinished or too hard for a 12-year-old. A failed one goes back to
the writer (out_fix*.jsonl) and needs a new check.

LINT: the rules in section_explain.py (lengths, no "!", no "The answer is", no option letters or numbers, a note per wrong option and
null at the key, notes about their own options), and "right" names the answer: Maths = the key option's value as a whole number or
fraction in the text; Science = the option's words. A verdict counts only while the explanation text, the key and the question (stem,
options) are exactly what its checker was given.
"""
import collections
import json
import os
import re
import sys
import time
from pathlib import Path

TMP = Path("/data/alvin/tmp/cookie-codex")
os.environ.setdefault("SECEXP_WORK", str(TMP / "msexp"))  # before section_explain reads it
sys.path.insert(0, str(Path(__file__).resolve().parent))
import section_explain as se  # noqa: E402
from explain import fp, jl  # noqa: E402

PP = TMP / "ppimport"
SUBJECTS = {  # live selections; "per" = writer pack size, "cper" = lines (of up to GROUP questions) per check pack
    "maths": {"sel": PP / "math1826h/maths", "prefix": "math-", "top": 10},
    "science": {"sel": PP / "sci1826g/science", "prefix": "sci-", "top": 10},
}
PACK, GROUP, CPER = 60, 10, 6
for _s in SUBJECTS:  # the shared helpers (order, record, verdicts, cfg) read this table
    se.SECTIONS[_s] = {"sub": None, "sel": SUBJECTS[_s]["sel"], "kind": "ms", "per": CPER}

# ---------------------------------------------------------------- which questions

# a stem that points at a picture, diagram, table or graph that is not in the text (heuristic, counted by reason)
PICTURE = [
    ("picture word", re.compile(r"\b(diagrams?|figures?|pictures?|graphs?|charts?|pictograms?|pictographs?|illustrations?|photographs?|"
                                r"maps?|drawings?|sketch(?:es)?|net of|apparatus|set-?ups?|flow ?charts?|food (?:chain|web)s?|"
                                r"number line|line plot|bar chart|histogram|dot plot|pie chart|table of values)\b", re.I)),
    ("shown/drawn below", re.compile(r"\b(shown|shows?|illustrated|drawn|given|pictured|displayed|seen|labelled|marked)\s+"
                                     r"(below|above|here|in the|on the|as)\b|\b(as|is|are) shown\b|\bshaded\b|\bin the (?:figure|box)\b", re.I)),
    ("below/above", re.compile(r"\b(?:the|this|these|following|a)\s+(?:\w+\s+){0,2}(?:below|above)\b|\b(?:below|above)\s*[:.]?\s*$", re.I)),
    ("table", re.compile(r"\b(?:the|following|given|shown|above|below|complete the|this)\s+(?:\w+\s+)?table\b|\btable\s+(?:below|above|shows|shown|gives)\b"
                         r"|\bin the table\b", re.I)),
    ("see/refer", re.compile(r"\b(?:look at|refer to|study|examine|observe)\s+the\b", re.I)),
]


def picture_reason(stem, options=()):
    """Why a text-only row's stem points at a picture that is not in the text, or ''. A table counts as present when the
    stem has table text (a '|' row, or 3+ lines with 2+ cells split by tabs or runs of spaces)."""
    for name, rx in PICTURE:
        if rx.search(stem or ""):
            if name == "table" and has_table_text(stem):
                continue
            return name
    return ""


def has_table_text(stem):
    lines = [l for l in (stem or "").split("\n") if l.strip()]
    if sum(1 for l in lines if "|" in l) >= 2:
        return True
    return sum(1 for l in lines if re.search(r"\t| {3,}", l)) >= 3


def selection_rows(subject):
    return [r for r in jl(se.cfg(subject)["sel"] / "selected.jsonl") if r.get("subject") == subject]


def classify(subject):
    """(candidates, skipped) of the selection: text-only (no crops, no set pages), 4 options, not in a set, a normal MCQ.
    skipped is {reason: n} for the text-only ones that look like they need a picture."""
    cands, skipped = [], collections.Counter()
    for r in selection_rows(subject):
        if r.get("kind", "mcq") != "mcq" or len(r.get("options") or []) != 4 or r.get("grp") or r.get("crops") or r.get("set_pages"):
            continue
        why = picture_reason(r["stem"], r["options"])
        if why:
            skipped[why] += 1
        else:
            cands.append(r)
    return cands, skipped


def chosen_path(subject):
    return se.wdir(subject) / "chosen.json"


def chosen(subject):
    p = chosen_path(subject)
    if not p.exists():
        sys.exit(f"{p} missing: run `ms_explain.py pick` first")
    return json.loads(p.read_text())["subtopics"]


def rows(subject):
    """{id: row} of the questions to explain: the candidates of the chosen sub-topics, with a synthetic grp/seq for the
    check packs (GROUP per line, in id order inside a sub-topic)."""
    keep = set(chosen(subject))
    by = collections.defaultdict(list)
    for r in classify(subject)[0]:
        if r["subtopic"] in keep:
            by[r["subtopic"]].append(r)
    out = {}
    for sub, rs in sorted(by.items()):
        for k, r in enumerate(sorted(rs, key=lambda x: x["id"])):
            out[r["id"]] = dict(r, grp=f"{sub}#{k // GROUP}", seq=k % GROUP + 1)
    return out


def cmd_pick(only=None):
    for subject in ([only] if only else SUBJECTS):
        c = SUBJECTS[subject]
        sel = se.cfg(subject)["sel"]
        allrows = selection_rows(subject)
        cands, skipped = classify(subject)
        text_only = sum(1 for r in allrows if r.get("kind", "mcq") == "mcq" and len(r.get("options") or []) == 4
                        and not r.get("grp") and not r.get("crops") and not r.get("set_pages"))
        n = collections.Counter(r["subtopic"] for r in cands)
        top = [s for s, _ in sorted(n.items(), key=lambda kv: (-kv[1], kv[0]))[:c["top"]]]
        print(f"== {subject}: live selection {sel} ({len(allrows)} active rows); text-only 4-option not-in-set {text_only}; "
              f"skipped as picture-dependent {sum(skipped.values())} {dict(skipped.most_common())}; candidates {len(cands)}")
        for i, (s, k) in enumerate(sorted(n.items(), key=lambda kv: (-kv[1], kv[0])), 1):
            print(f"  {'*' if s in top else ' '} {i:2d}. {k:4d}  {s}")
            if i >= c["top"] + 3:
                print(f"     ... {len(n) - i} more sub-topics")
                break
        print(f"  chosen {len(top)} sub-topics, {sum(n[s] for s in top)} questions")
        d = se.wdir(subject)
        d.mkdir(parents=True, exist_ok=True)
        p = chosen_path(subject)
        if p.exists() and json.loads(p.read_text())["subtopics"] != top:
            print(f"  NOTE {p} differs from this pick and was kept (delete it to re-pick); packs use the kept list")
        else:
            p.write_text(json.dumps({"subtopics": top, "counts": {s: n[s] for s in top}, "skipped": dict(skipped),
                                     "date": time.strftime("%Y-%m-%d")}, indent=1))


# ---------------------------------------------------------------- lint

def norm_num(s):
    s = (s or "").replace("−", "-").replace("–", "-").replace("×", "x").replace("$", "")
    return re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", s)


def has_value(opt, text):
    """The Maths key option's value is in the text: its number (fraction, mixed number, decimal, percent) as a whole token, units
    optional ('12 cm' is met by 12); an option with no digit is met like a Science one (its words)."""
    o = norm_num(opt).strip().strip("\"'“”").strip()
    t = norm_num(text)
    if not re.search(r"\d", o):
        return se.names_answer(opt, text)
    core = re.sub(r"\s*[A-Za-z°²³]+(?:\s*[A-Za-z°²³/]+)*\.?$", "", o).strip() or o  # drop trailing units: "12 cm" -> "12", "2 1/3 h" -> "2 1/3"
    for cand in dict.fromkeys([o, core, re.sub(r"\s+", " ", core)]):
        # not inside another number: not after a digit, '/', 'digit.', or '-' ('-5' for 5), and a fraction not after
        # "digits + space" ('1 3/4' for 3/4, '2 1/3' for 1/3)
        pre = r"(?<![\d/])(?<!\d\.)(?<!-)" + (r"(?<!\d )" if re.fullmatch(r"\d+/\d+", cand or "") else "")
        if cand and re.search(pre + re.escape(cand) + r"(?![\d]|[./]\d)", t):
            return True
    return False


def lint_ms(subject, r, rec):
    """Why a writer's line fails the rules, or '' when it passes (section_explain.lint_mcq's rules; the answer is named by value)."""
    if not rec:
        return "not written"
    none_fits = rec.get("blind") == -1 and bool(str(rec.get("doubt") or "").strip())  # "no option is right" is an honest blind answer, with a doubt
    if not isinstance(rec.get("blind"), int) or isinstance(rec.get("blind"), bool) or not (none_fits or 0 <= rec["blind"] < len(r["options"])):
        return "no blind answer"
    e = se.expl_of(rec)
    k, o = r["answer"], r["options"]
    if len(e["right"]) < se.RIGHT_MIN:
        return "right missing or too short"
    if len(e["right"]) > se.RIGHT_MAX:
        return f"right longer than {se.RIGHT_MAX}"
    if e["wrong"] is None or len(e["wrong"]) != len(o):
        return "wrong is not one entry per option"
    if e["wrong"][k] is not None:
        return "the key's slot is not null"
    if any(e["wrong"][j] is None for j in range(len(o)) if j != k):
        return "a wrong option has no note"
    if any(len(s) > se.WRONG_MAX for s in e["wrong"] if s):
        return f"a wrong note longer than {se.WRONG_MAX}"
    for t in [e["right"], *[s for s in e["wrong"] if s]]:
        if se.style(t):
            return se.style(t)
        if se.numbered(t):
            return "names an option by letter or number"
    if subject == "maths":
        if not has_value(o[k], e["right"]):
            return "right does not contain the answer value"
    elif not (se.names_answer(o[k], e["right"]) or se.mention(e["right"], o[k])):
        return "does not name the answer"
    if sum(se.about(e["wrong"][j], o[j]) for j in range(len(o)) if j != k) < len(o) - 2:
        return "the notes do not talk about their own options"
    return ""


def state(subject):
    rs = rows(subject)
    w = se.written_mcq(subject)
    texts = {i: se.expl_of(w[i]) for i in rs if i in w}
    return rs, texts, {i: lint_ms(subject, r, w.get(i)) for i, r in rs.items()}, w


# ---------------------------------------------------------------- commands

def cmd_pack(subject, force=False):
    rs = rows(subject)
    d = se.wdir(subject)
    answered = sorted(f.name for f in d.glob("out_[0-9]*.jsonl")) + sorted(f.name for f in d.glob("check_*.jsonl"))
    if answered and not force:
        sys.exit(f"{d} already has {', '.join(answered)}: new packs could reorder what they answer (pass --force to rebuild)")
    for f in d.glob("pack_*.jsonl"):
        f.unlink()
    items = [{"id": r["id"], "sub": r["subtopic"], "stem": r["stem"], "options": r["options"], "key": r["answer"]}
             for r in sorted(rs.values(), key=lambda r: (r["subtopic"], r["id"]))]
    groups = se.chunks(items, PACK)
    for k, g in enumerate(groups):
        se.write_jsonl(d / f"pack_{k}.jsonl", g)
    print(f"{subject}: {len(items)} questions in {len(groups)} packs ({', '.join(str(len(g)) for g in groups)}) -> {d}/pack_N.jsonl")


def cmd_lint(subject, quiet=False):
    rs, texts, lint, w = state(subject)
    why = collections.Counter(v or "ok" for v in lint.values())
    if not quiet:
        print(subject, dict(why.most_common()))
        if w:
            print("  doubts:", sum(1 for i, r in rs.items() if not lint[i] and se.doubt_of(w.get(i), r)))
    return rs, texts, lint, w


def cmd_checkpack(subject, tag=None):
    """Packs for the checkers: every lint-clean item with no doubt and no verdict that still holds (lint failures are listed:
    the writer fixes them in out_fix*.jsonl). A pack already answered is never overwritten."""
    rs, texts, lint, w = cmd_lint(subject)
    v, _ = se.verdicts(subject, rs, texts)
    todo = {i for i in rs if not lint[i] and i not in v and not se.doubt_of(w.get(i), rs[i])}
    bad = sorted(i for i in rs if lint[i] and lint[i] != "not written")
    if bad:
        print(f"{len(bad)} fail lint (not sent: the writer fixes them):")
        for i in bad[:40]:
            print(f"  {i}: {lint[i]}")
    d = se.wdir(subject)
    d.mkdir(parents=True, exist_ok=True)
    by = collections.defaultdict(list)
    for i in sorted(rs):
        if i in todo:
            by[rs[i]["grp"]].append(rs[i])
    lines = [{"grp": g, "sub": q[0]["subtopic"], "questions": [
        {"id": r["id"], "n": r["seq"], "stem": r["stem"], "options": r["options"], "key": r["answer"],
         "explanation": texts[r["id"]], "fp": fp(r)} for r in q]} for g, q in sorted(by.items())]
    if not lines:
        print("nothing to check (no pack written)")
        return
    if tag:
        names, groups = [tag], [lines]
    else:
        rnd = 1
        while list(d.glob(f"cpack_r{rnd}_*.jsonl")):
            rnd += 1
        groups = se.chunks(lines, CPER)
        names = [f"r{rnd}_{k}" for k in range(len(groups))]
    for name in names[:len(groups)]:
        if (d / f"cpack_{name}.jsonl").exists():
            sys.exit(f"cpack_{name}.jsonl already exists: pick another tag")
    for name, g in zip(names, groups):
        se.write_jsonl(d / f"cpack_{name}.jsonl", g)
    if lines:
        se.record(subject, [f"cpack_{n}.jsonl" for n in names[:len(groups)]])
    print(f"{len(todo)} to check in {len(groups) if lines else 0} packs: "
          + ", ".join(f"cpack_{n}.jsonl" for n in names[:len(groups) if lines else 0]))


def cmd_apply(subject, write=False, drop_failed=False):
    sel = se.cfg(subject)["sel"]
    rs, texts, lint, w = cmd_lint(subject, quiet=True)
    v, failed = se.verdicts(subject, rs, texts)
    new, doubts, why = {}, [], collections.Counter()
    for i, r in sorted(rs.items()):
        dbt = se.doubt_of(w.get(i), r, v.get(i))
        if dbt:
            doubts.append({"id": i, "sub": r["subtopic"], "stem": r["stem"], "options": r["options"], "answer": r["answer"],
                           "blind": (w.get(i) or {}).get("blind"), "doubt": dbt})
            why["doubt (not explained)"] += 1
        elif lint[i]:
            why["lint: " + lint[i]] += 1
        elif i not in v:
            why["not checked (or checked for another text, key or question)"] += 1
        elif v[i].get("ok") is not True:
            why["checker failed it"] += 1
        else:
            new[i] = {"id": i, "fp": fp(r), "explain": texts[i], "src": "claude-checked"}
            why["passed"] += 1
    # the merge keeps every line of the selection's explain.jsonl: other sub-topics and subjects' lines untouched, a stale fp
    # dropped (the upload would ignore it). cur covers the WHOLE selection, not just the chosen sub-topics
    allcur = {r["id"]: fp(r) for r in selection_rows(subject)}
    path = sel / "explain.jsonl"
    old = jl(path)
    flagged = se.failed_lines(old, new, allcur, failed, "ms")
    out, st = se.merge(old, new, allcur, flagged if drop_failed else frozenset(), {x["id"] for x in doubts})
    d = se.wdir(subject)
    d.mkdir(parents=True, exist_ok=True)
    se.write_jsonl(d / "doubts.jsonl", doubts)
    if write:
        if path.exists():
            (d / "backup").mkdir(exist_ok=True)
            (d / "backup" / f"explain.{time.strftime('%Y%m%d-%H%M%S')}.jsonl").write_bytes(path.read_bytes())
        se.write_jsonl(path, out)
        target = path
    else:
        target = d / "explain.preview.jsonl"
        se.write_jsonl(target, out)
    print(f"{subject}: {len(rs)} questions {dict(why.most_common())}")
    print(f"  {target}: {len(out)} lines ({'WRITTEN to the live selection' if write else 'preview only; pass --write to replace ' + str(path)}); {dict(st)}"
          + (f"; {len(flagged)} existing lines a checker failed were " + ("dropped" if drop_failed else "KEPT (pass --drop-failed)") if flagged else ""))
    print(f"  {len(doubts)} doubts -> {d / 'doubts.jsonl'}")


# ---------------------------------------------------------------- selftest

def selftest():
    # picture heuristics
    assert picture_reason("The diagram shows a circuit.") == "picture word"
    assert picture_reason("What is shown below?") == "shown/drawn below"
    assert picture_reason("Study the table below.") in ("below/above", "table")
    assert picture_reason("Complete the table: x | 1 | 2\ny | 3 | 4\nz | 5 | 6") == "", "table text is in the stem"
    assert picture_reason("A table costs $50 and a chair $20. Find the total.") == ""
    assert picture_reason("What is 3/4 of 24?") == "" and picture_reason("Which part of a plant takes in water?") == ""
    assert picture_reason("The table below shows the scores.\nName | Score\nAnn | 4\nBo | 5") != "table"
    assert has_table_text("a\nx | y\n1 | 2") and not has_table_text("one line | only")
    # maths values
    assert has_value("12", "4 x 3 = 12.") and not has_value("12", "It is 120 or 1.12 or 5/12.")
    assert has_value("$5.40", "Total = $5.40.") and has_value("5.40", "so $5.40 in all")
    assert has_value("3/4", "which is 3/4.") and not has_value("3/4", "13/4")
    assert has_value("2 1/3", "so 2 1/3 hours") and has_value("12 cm", "Perimeter = 12 cm.") and has_value("12 cm", "gives 12.")
    assert has_value("1,200", "= 1200 in all") and has_value("-5", "so x = -5") and not has_value("5", "x = 3.5")
    assert has_value("25%", "that is 25%.") and not has_value("25", "that is 125.")
    assert has_value("triangle", "It is a \"triangle\" with 3 sides.")
    # not inside another number: a mixed number, a negative number
    assert not has_value("3/4", "so 1 3/4 in all") and not has_value("1/3", "that is 2 1/3.") and not has_value("5", "x = -5")
    assert has_value("3/4", "= 3/4") and has_value("5", "the answer is 5") and has_value("$5", "costs $5.") and has_value("5", "5 cm long")
    assert has_value("3/4", "so 3/4 and 1 3/4") and has_value("3/4", "1 and 3/4"), "a clean match elsewhere still passes"
    # lint, on made-up rows
    m = {"id": "x1", "subtopic": "math-demo", "stem": "A pen costs $3 and a book 4 times as much. Total?", "options": ["$12", "$15", "$7", "$24"], "answer": 1}
    g = {"id": "x1", "blind": 1, "right": "The book costs 4 x $3 = $12. Together: $3 + $12 = $15.",
         "wrong": ["Found only the price of the book: 4 x 3 = 12.", None, "Added 3 + 4 = 7 instead of multiplying for the book.", "Multiplied the prices by 4 and 2: 3 x 4 x 2 = 24."]}
    assert lint_ms("maths", m, g) == "", lint_ms("maths", m, g)
    bad = lambda **kw: lint_ms("maths", m, dict(g, **kw))
    assert bad(right="The book costs 4 x $3 = $12. So they cost fifteen dollars.") == "right does not contain the answer value"
    assert bad(right="Together: $3 + $12 = $15 (option B).") == "names an option by letter or number"
    assert bad(right="Together: $3 + $12 = $15 (2).") == "names an option by letter or number"
    assert bad(right="Together they cost $3 + $12 = $15!") == "has '!'"
    assert bad(wrong=["Only the book: 12.", None, "Added 3 + 4 = 7.", None]) == "a wrong option has no note"
    assert bad(wrong=["Only the book: 12.", "x", "Added 3 + 4 = 7.", "3 x 4 x 2 = 24."]) == "the key's slot is not null"
    assert bad(blind=None) == "no blind answer" and lint_ms("maths", m, None) == "not written"
    assert bad(blind=-1) == "no blind answer" and bad(blind=-1, doubt="no option is right") != "no blind answer", "-1 only with a doubt"
    assert bad(wrong=["Slipped.", None, "Slipped.", "Slipped."]) == "the notes do not talk about their own options"
    s = {"id": "x2", "subtopic": "sci-demo", "stem": "Which part of a plant takes in water from the soil?", "options": ["Leaf", "Root", "Flower", "Stem"], "answer": 1}
    sg = {"id": "x2", "blind": 1, "right": "The root grows in the soil and takes in water, which then moves up the stem.",
          "wrong": ["The leaf makes food; it does not take water from the soil.", None, "The flower makes seeds, not water intake.", "The stem carries water up but does not take it in."]}
    assert lint_ms("science", s, sg) == "", lint_ms("science", s, sg)
    assert lint_ms("science", s, dict(sg, right="Plants drink through their underground part, which is long.")) == "does not name the answer"
    assert se.doubt_of(dict(sg, blind=0), s).startswith("the writer's blind answer")
    # end to end on a made-up selection under WORK/_selftest: pick, pack, lint, checkpack, verdict tie, apply (preview, then --write)
    import builtins
    import shutil
    saved_work, saved_sec = se.WORK, dict(se.SECTIONS)
    base = TMP / "msexp" / "_selftest"
    shutil.rmtree(base, ignore_errors=True)
    sel = base / "sel"
    sel.mkdir(parents=True)
    qs = []
    for k in range(7):
        qs.append({"id": f"t{k}", "subject": "maths", "subtopic": "math-a" if k < 5 else "math-b", "kind": "mcq",
                   "stem": f"A box has {k + 2} bags of {k + 3} sweets. How many sweets are there?",
                   "options": [str((k + 2) * (k + 3)), str(k + 5), str((k + 2) + (k + 3) + 1), str((k + 3) * (k + 4))], "answer": 0,
                   "crops": [], "grp": None})
    qs.append(dict(qs[0], id="pic", stem="The diagram shows a box of sweets. How many?", subtopic="math-a"))
    qs.append(dict(qs[0], id="fig", crops=["c.png"], subtopic="math-a"))
    se.write_jsonl(sel / "selected.jsonl", qs)
    old_line = {"id": "other", "fp": "zz", "explain": {"right": "kept", "wrong": []}}
    se.write_jsonl(sel / "explain.jsonl", [old_line])
    SUBJECTS_SAVED = dict(SUBJECTS)
    SUBJECTS["maths"] = dict(SUBJECTS["maths"], sel=sel, top=1)
    se.SECTIONS["maths"] = {"sub": None, "sel": sel, "kind": "ms", "per": CPER}
    _print = builtins.print
    builtins.print = lambda *a, **k: None
    try:
        se.WORK = base
        cmd_pick("maths")
        assert chosen("maths") == ["math-a"], chosen("maths")  # 5 candidates beat 2; the picture stem and the cropped row are out
        assert sorted(rows("maths")) == ["t0", "t1", "t2", "t3", "t4"]
        cmd_pack("maths")
        p = jl(base / "maths" / "pack_0.jsonl")
        assert [x["id"] for x in p] == ["t0", "t1", "t2", "t3", "t4"] and set(p[0]) == {"id", "sub", "stem", "options", "key"}
        outs = []
        for i, r in sorted(rows("maths").items()):
            v = r["options"][0]
            outs.append({"id": i, "blind": 0, "right": f"{r['stem'].split('has ')[1].split(' sweets')[0]} gives {v}. So the box holds {v} sweets.",
                         "wrong": [None, f"Gave the sum of the numbers: {r['options'][1]}.", f"Added and then one more: {r['options'][2]}.",
                                   f"Multiplied by the wrong number: {r['options'][3]}."]})
        se.write_jsonl(base / "maths" / "out_0.jsonl", outs)
        rs, texts, lint, w = cmd_lint("maths", quiet=True)
        assert all(v == "" for v in lint.values()), lint
        cmd_checkpack("maths")
        cps = sorted((base / "maths").glob("cpack_r1_*.jsonl"))
        assert cps, "a check pack"
        cl = jl(cps[0])
        ids = [q["id"] for x in cl for q in x["questions"]]
        assert set(ids) == {i for i in rs if not lint[i] and not se.doubt_of(w.get(i), rs[i])}
        se.write_jsonl(base / "maths" / "check_r1_0.jsonl", [{"id": i, "ok": True, "reason": ""} for i in ids])
        before = (sel / "explain.jsonl").read_bytes()
        cmd_apply("maths")  # preview: the selection is untouched
        assert (sel / "explain.jsonl").read_bytes() == before and (base / "maths" / "explain.preview.jsonl").exists()
        prev = {x["id"] for x in jl(base / "maths" / "explain.preview.jsonl")}
        assert "other" in prev and set(ids) <= prev, prev
        cmd_apply("maths", write=True)
        got = {x["id"]: x for x in jl(sel / "explain.jsonl")}
        assert set(got) == prev and "other" in got and all(got[i]["fp"] == fp(rs[i]) for i in ids)
        assert list((base / "maths" / "backup").glob("explain.*.jsonl"))
        # a changed key withdraws the verdict (new fp): nothing to ship for it, and its stale line goes
        qs2 = [dict(q, answer=1) if q["id"] == "t0" else q for q in qs]
        se.write_jsonl(sel / "selected.jsonl", qs2)
        rs2 = rows("maths")
        v2, _ = se.verdicts("maths", rs2, {i: se.expl_of(w[i]) for i in rs2 if i in w})
        assert "t0" not in v2 and "t1" in v2
        # a doubt keeps a question out
        w2 = dict(outs[1], doubt="the key looks wrong")
        se.write_jsonl(base / "maths" / "out_fix1.jsonl", [w2])
        assert se.doubt_of(se.written_mcq("maths")["t1"], rs2["t1"])
    finally:
        builtins.print = _print
        se.WORK = saved_work
        se.SECTIONS.clear()
        se.SECTIONS.update(saved_sec)
        SUBJECTS.clear()
        SUBJECTS.update(SUBJECTS_SAVED)
        shutil.rmtree(base, ignore_errors=True)
    print("ms_explain selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:]
    cmd = a[0] if a else ""
    if cmd == "selftest":
        selftest()
    elif cmd == "pick":
        cmd_pick(a[1] if len(a) > 1 else None)
    elif cmd in ("pack", "lint", "checkpack", "recheck", "apply") and len(a) >= 2 and a[1] in SUBJECTS:
        s = a[1]
        if cmd == "pack":
            cmd_pack(s, force="--force" in a)
        elif cmd == "lint":
            cmd_lint(s)
        elif cmd == "checkpack":
            cmd_checkpack(s)
        elif cmd == "recheck" and len(a) >= 3:
            cmd_checkpack(s, a[2])
        elif cmd == "apply":
            cmd_apply(s, write="--write" in a, drop_failed="--drop-failed" in a)
        else:
            sys.exit(__doc__)
    else:
        sys.exit(__doc__)
