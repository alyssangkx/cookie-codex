#!/usr/bin/env python3
"""Explanations for three English past-paper sections (owner, 24 Nov 2026): Visual Text and Vocabulary Cloze get new ones
(why the key is right, and a note for each wrong option); Synthesis & Transformation keeps its one-line tips, each CHECKED
by a second model and rewritten only when it fails. Claude Opus agents write and check; this script packs, lints, ties
verdicts to what was checked, and applies.

  section_explain.py pack SECTION [--force]   writer packs -> WORK/<section>/pack_N.jsonl (writers fill out_N.jsonl);
                                              Synthesis: the packs ARE the first check of the existing tips
  section_explain.py lint SECTION             the rule checks, counted by reason
  section_explain.py checkpack SECTION        lint-clean items without a verdict that still holds -> cpack_rR_N.jsonl
                                              (checkers fill check_rR_N.jsonl; R is the next free round)
  section_explain.py recheck SECTION TAG      the same, one pack -> cpack_TAG.jsonl (-> check_TAG.jsonl)
  section_explain.py apply SECTION [--drop-failed]
                                              lint-clean + checker-passed + no doubt -> <selection>/english/explain.jsonl,
                                              merged with the lines already there; doubts -> WORK/<section>/doubts.jsonl
  section_explain.py selftest

SECTION is visual-text, vocab-cloze or synthesis. WORK is /data/alvin/tmp/cookie-codex/secexp.

WRITER OUTPUT (Visual Text, Vocabulary Cloze): out_N.jsonl beside pack_N.jsonl, one JSON object per question:
  {"id", "blind": <0-based index of the option the writer picks BEFORE looking at the key>,
   "doubt": "<reason; only when blind differs from the key or the key looks wrong>",
   "right": "<why the key is right>", "wrong": [<a note per option in stored order; null at the key's index>]}
  Visual Text example (made up):
  {"id": "pp-0000000001", "blind": 2, "right": "The poster says the fair is run by \\"the Parents' Group\\", so they organise it.", "wrong": ["The library only lends its hall for the fair.", "The bakery is listed as a sponsor, not as the organiser.", null, "The website only sells the tickets."]}
  Vocabulary Cloze example (made up):
  {"id": "pp-0000000002", "blind": 0, "right": "\\"Lavish\\" means rich and costly, so \\"extravagant\\" is closest in meaning.", "wrong": [null, "\\"Careful\\" means the opposite of spending a lot.", "\\"Noisy\\" is about sound, not cost.", "\\"Tiny\\" is about size, not cost."]}
  Rewrites after a failed check go in out_fix<anything>.jsonl (same shape), which override out_N in name order.

CHECKER OUTPUT (Visual Text, Vocabulary Cloze): check_X.jsonl beside cpack_X.jsonl:
  {"id", "ok": true|false, "reason": "<what is wrong, when ok is false>", "doubt": "<only if the key itself looks wrong>"}
SYNTHESIS CHECKER OUTPUT: out_N.jsonl beside pack_N.jsonl (first check) and check_X.jsonl beside cpack_X.jsonl:
  {"id", "ok": true|false, "reason", "rewrite": "<a better tip, only when ok is false>"}
  example (made up): {"id": "pp-0000000003", "ok": false, "reason": "It says 'Despite' takes a clause.", "rewrite": "\\"Despite\\" is followed by a noun or an -ing word, never by a full clause."}
  A pack line whose "lint" is not empty fails the rules as it stands: the checker answers ok false with a rewrite.
  A rewrite replaces the tip it judged, and counts only after another checker passes it (checkpack / recheck).

LINT: "right" 15-600 characters, "wrong" notes at most 400 (the site drops longer ones, pastpaper.ts cleanExplain); no
"!"; never starts "The answer is"; names the answer (a short option quoted, explain/cloze_explain `named`; an option of
5+ words by most of its words, explain.mentions); no option letters or numbers ("(2)", "option B": options are shuffled
on the site); a note for every wrong option, null at the key, and the notes about their own options (most share a word with it).
Synthesis tips: the same length and style rules, and the tip mentions the scaffold's printed connective word(s) (each
printed stretch's connective words that are not in the two sentences).

A verdict counts only while the explanation text, the key and the question (stem with its passage, options; Visual Text
also its page images) are exactly what its checker was given. Past-paper text stays out of the repo (made-up tests only).
"""
import collections
import json
import math
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cloze_explain import named, spans  # noqa: E402
from explain import OPTNUM, fp, jl, mentions  # noqa: E402

import os  # noqa: E402

TMP = Path("/data/alvin/tmp/cookie-codex")
WORK = Path(os.environ.get("SECEXP_WORK") or TMP / "secexp")  # SECEXP_WORK / SECEXP_SEL: run on copies (comparisons)
PP = TMP / "ppimport"
# the live selection of each section (pp_items active ids and figures match these, 24 Nov 2026; engvt3-5 hold the same
# questions with no WebP figures, so they cannot be uploaded)
SECTIONS = {
    "visual-text": {"sub": "eng-visual-text", "sel": PP / "engvt2/english", "kind": "vt", "per": 10},
    "vocab-cloze": {"sub": "eng-vocab-cloze", "sel": PP / "engvc/english", "kind": "vc", "per": 100},
    "synthesis": {"sub": "eng-synthesis", "sel": PP / "engst/english", "kind": "st", "per": 95},
}
RIGHT_MAX, WRONG_MAX, RIGHT_MIN = 600, 400, 15
LETTER = re.compile(r"\b(?i:option|choice|answer)\s*[（(]?\s*[A-D1-4]\s*[)）]?(?![\w'’])|[（(]\s*[A-D]\s*[)）]"
                    r"|\b(?i:first|second|third|fourth|last)\s+(?i:option)\b")
STOP = {"a", "an", "the", "it", "is", "was", "were", "are", "my", "his", "her", "their", "our", "your", "its", "i", "he",
        "she", "they", "we", "you", "me", "him", "them", "us"}


def cfg(section):
    if section not in SECTIONS:
        sys.exit(f"unknown section {section!r}: one of {', '.join(SECTIONS)}")
    c = SECTIONS[section]
    return dict(c, sel=Path(os.environ["SECEXP_SEL"])) if os.environ.get("SECEXP_SEL") else c


def wdir(section):
    return WORK / section


def rows(section):
    c = cfg(section)
    return {r["id"]: r for r in jl(c["sel"] / "selected.jsonl") if r["subtopic"] == c["sub"]}


def images(r):
    return list(r.get("set_pages") or []) + list(r.get("crops") or [])


def passage_of(r):
    return r["stem"].rsplit("\n\n", 1)[0]


def question_of(r):
    return r["stem"].rsplit("\n\n", 1)[1] if "\n\n" in r["stem"] else r["stem"]


def ekey(e):
    return json.dumps(e, ensure_ascii=False, sort_keys=True)


def chunks(xs, per):
    n = max(1, math.ceil(len(xs) / per))
    size = math.ceil(len(xs) / n) if xs else 0
    return [xs[i * size:(i + 1) * size] for i in range(n)] if xs else []


def sets(rs):
    by = collections.defaultdict(list)
    for r in rs.values():
        by[r["grp"]].append(r)
    return [sorted(v, key=lambda r: r["seq"]) for _, v in sorted(by.items())]


def write_jsonl(path, items):
    tmp = path.with_suffix(path.suffix + ".part")
    with open(tmp, "w", encoding="utf-8") as f:
        for x in items:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    tmp.replace(path)


# ---------------------------------------------------------------- written texts, verdicts

def existing(section):
    """{id: line} of the selection's explain.jsonl (every line, whatever its fp)."""
    return {x["id"]: x for x in jl(cfg(section)["sel"] / "explain.jsonl")}


def written_mcq(section):
    """The writers' lines by id; out_fix*.jsonl override out_N.jsonl, in name order."""
    d = wdir(section)
    files = sorted(d.glob("out_[0-9]*.jsonl"), key=lambda f: int(re.findall(r"\d+", f.name)[0])) + sorted(d.glob("out_fix*.jsonl"))
    w = {}
    for f in files:
        for x in jl(f):
            if isinstance(x, dict) and x.get("id"):
                w[x["id"]] = x
    return w


def expl_of(rec):
    """A writer's line as the {right, wrong[]} the site reads (texts stripped, nothing else changed)."""
    if not rec:
        return None
    w = rec.get("wrong")
    return {"right": (rec.get("right") or "").strip() if isinstance(rec.get("right"), str) else "",
            "wrong": [s.strip() if isinstance(s, str) and s.strip() else None for s in w] if isinstance(w, list) else None}


SEQ = "seq.json"  # {file name: order}: the order check packs (and synthesis fixes) were made, never file times


def order(section):
    """The section's check packs (synthesis: also its first-check packs and out_fix files) in the order they were made,
    as recorded in WORK/<section>/seq.json. A file not recorded yet is recorded now: pack_N as 0 and cpack_rR_N as R
    (files made before seq.json existed), anything else (a recheck tag, an out_fix file) after everything recorded,
    in name order. checkpack and recheck record their packs when they write them."""
    d = wdir(section)
    p = d / SEQ
    seq = json.loads(p.read_text()) if p.exists() else {}
    st = cfg(section)["kind"] == "st"
    names = [f.name for f in d.glob("cpack_*.jsonl")]
    if st:
        names += [f.name for f in d.glob("pack_*.jsonl")] + [f.name for f in d.glob("out_fix*.jsonl")]
    before = dict(seq)

    def derived(n):
        m = re.fullmatch(r"cpack_r(\d+)_\d+\.jsonl", n)
        return 0 if n.startswith("pack_") else int(m.group(1)) if m else None
    for n in sorted(names):
        if n not in seq and derived(n) is not None:
            seq[n] = derived(n)
    for n in sorted(names):
        if n not in seq:
            seq[n] = max(seq.values(), default=0) + 1
    if seq != before and d.is_dir():
        p.write_text(json.dumps(seq, indent=1, sort_keys=True))
    return sorted(names, key=lambda n: (seq[n], n))


def record(section, names):
    """Record new check packs as made after everything recorded so far (one order number for one round)."""
    d = wdir(section)
    order(section)
    p = d / SEQ
    seq = json.loads(p.read_text()) if p.exists() else {}
    s = max(seq.values(), default=0) + 1
    seq.update({n: s for n in names})
    p.write_text(json.dumps(seq, indent=1, sort_keys=True))


def verdict_file(section, name):
    return wdir(section) / (name.replace("cpack_", "check_", 1) if name.startswith("cpack_") else name.replace("pack_", "out_", 1))


def pairs(section):
    """(pack, verdicts) files in the recorded order: the synthesis first check (pack_N/out_N) and every cpack_X/check_X."""
    d = wdir(section)
    return [(d / n, verdict_file(section, n)) for n in order(section) if not n.startswith("out_fix")]


def seen_in(pack, kind):
    """{id: what the checker was given} from a check pack."""
    seen = {}
    for line in jl(pack):
        if kind == "st":
            seen[line["id"]] = ((line.get("tip") or "").strip(), line["fp"])
        else:
            for q in line["questions"]:
                seen[q["id"]] = (ekey(q["explanation"]), q["fp"], tuple(line.get("images") or []))
    return seen


def st_texts(section, rs):
    """Synthesis: the tip of each id as it stands. It starts from the tip its first-check pack (pack_N) was given, or
    the selection's explain.jsonl line for an id in no first-check pack (current fp only; a missing tip is ""); then,
    in the recorded order (seq.json), a checker's rewrite of exactly the tip as it stood replaces it, and an
    out_fix*.jsonl line {"id", "right"} replaces it."""
    d = wdir(section)
    ex = existing(section)
    t = {}
    for i, r in rs.items():
        right = (ex.get(i, {}).get("explain") or {}).get("right") if ex.get(i, {}).get("fp") == fp(r) else None
        t[i] = right.strip() if isinstance(right, str) else ""
    for n in order(section):
        if n.startswith("pack_"):
            for line in jl(d / n):
                if line.get("id") in rs and line.get("fp") == fp(rs[line["id"]]):
                    t[line["id"]] = (line.get("tip") or "").strip()
    for n in order(section):
        if n.startswith("out_fix"):
            for x in jl(d / n):
                if x.get("id") in rs and isinstance(x.get("right"), str) and x["right"].strip():
                    t[x["id"]] = x["right"].strip()
            continue
        seen = seen_in(d / n, "st")
        for x in jl(verdict_file(section, n)):
            i = x.get("id")
            if i in rs and x.get("ok") is False and isinstance(x.get("rewrite"), str) and x["rewrite"].strip() \
                    and seen.get(i) == (t.get(i, ""), fp(rs[i])):
                t[i] = x["rewrite"].strip()
    return {i: s for i, s in t.items() if s}


def tie(kind, r, text):
    return (text, fp(r)) if kind == "st" else (ekey(text), fp(r), tuple(images(r)))


def verdicts(section, rs, texts):
    """The verdict of each id that still holds (text, key, question and images exactly as checked); the newest wins.
    Also {id: text} of every text a checker failed (whether or not it still stands)."""
    kind = cfg(section)["kind"]
    v, failed = {}, collections.defaultdict(set)
    for pack, ver in pairs(section):
        seen = seen_in(pack, kind)
        for x in jl(ver):
            i = x.get("id")
            if i not in rs or i not in seen:
                continue
            if x.get("ok") is not True:
                failed[i].add(seen[i][0])
            if i in texts and seen[i] == tie(kind, rs[i], texts[i]):
                v[i] = x
    return v, failed


# ---------------------------------------------------------------- lint

def mention(text, opt):
    """explain.mentions with single quote marks taken off the words ('unless' -> unless); an apostrophe inside a word stays."""
    return mentions(re.sub(r"(?<![A-Za-z])['‘’]|['‘’](?![A-Za-z])", " ", text or ""), opt)


QUOTES = "\"'“”‘’"


def quoted_word(w, text):
    """w as a whole word (no letter or digit on either side) inside a quoted stretch of the text, any case."""
    pat = r"(?<![\w])" + re.escape(w) + r"(?![\w])"
    return any(re.search(pat, s, re.I) for s in spans(text))


def names_answer(opt, text):
    """A short option (up to 4 words) quoted in the text as a whole word or phrase (explain/cloze_explain `named`; an
    option stored with its own quote marks, "Ahoy Captain", is named by writing Ahoy Captain inside one pair of quotes);
    a long one by most of its words."""
    o = opt.strip().strip(QUOTES).strip()
    if len(o.split()) >= 5:
        return mention(text, o)
    return named(o, text) or quoted_word(o, text)


def numbered(text, r=None):
    """The text names an option by letter or number. A Vocabulary Cloze blank's own number "(17)" is allowed."""
    t = text
    if r is not None and r.get("seq"):
        t = t.replace(f"({r['seq']})", "")
    return bool(OPTNUM.search(t) or LETTER.search(t))


def style(text):
    """'!' outside a quotation (quoting a poster's "Join us!" or an option with '!' is fine), or 'The answer is ...'."""
    bare = text
    for q in spans(text):
        bare = bare.replace(q, "")
    if "!" in bare:
        return "has '!'"
    if text.strip().lower().startswith("the answer is"):
        return "starts 'The answer is'"
    return ""


def lint_mcq(r, rec):
    """Why a writer's line fails the rules, or '' when it passes."""
    if not rec:
        return "not written"
    if not isinstance(rec.get("blind"), int) or isinstance(rec.get("blind"), bool) or not 0 <= rec["blind"] < len(r["options"]):
        return "no blind answer"
    e = expl_of(rec)
    k, o = r["answer"], r["options"]
    if len(e["right"]) < RIGHT_MIN:
        return "right missing or too short"
    if len(e["right"]) > RIGHT_MAX:
        return f"right longer than {RIGHT_MAX}"
    if e["wrong"] is None or len(e["wrong"]) != len(o):
        return "wrong is not one entry per option"
    if e["wrong"][k] is not None:
        return "the key's slot is not null"
    if any(e["wrong"][j] is None for j in range(len(o)) if j != k):
        return "a wrong option has no note"
    if any(len(s) > WRONG_MAX for s in e["wrong"] if s):
        return f"a wrong note longer than {WRONG_MAX}"
    for t in [e["right"], *[s for s in e["wrong"] if s]]:
        if style(t):
            return style(t)
        if numbered(t, r if cfg_kind(r) == "vc" else None):
            return "names an option by letter or number"
    if not names_answer(o[k], e["right"]):
        return "does not name the answer"
    if sum(about(e["wrong"][j], o[j]) for j in range(len(o)) if j != k) < len(o) - 2:
        return "the notes do not talk about their own options"
    return ""


def about(text, opt):
    """A note talks about its option: it has one of the option's content words in some form (explain.mentions per word;
    looser than explain.aligned, whose most-of-the-words rule fails a fair note on a long Visual Text option). An option
    with no content word (a price, a time, a date: "$12", "10 a.m.") is matched by its numbers as whole tokens."""
    ws = [w for w in words(opt) if w not in STOP and len(w) >= 3]
    if ws:
        return any(mention(text, w) for w in ws)
    nums = re.findall(r"\d+(?:[.:,]\d+)*", opt)
    if nums:
        return any(re.search(r"(?<![\d.:,])" + re.escape(n) + r"(?![\d]|[.:,]\d)", text or "") for n in nums)
    return any(mention(text, w) for w in words(opt)) or (bool(opt.strip()) and opt.strip().lower() in (text or "").lower())


def cfg_kind(r):
    return {c["sub"]: c["kind"] for c in SECTIONS.values()}.get(r.get("subtopic"), "")


def words(s):
    return re.findall(r"[a-z']+", (s or "").lower().replace("’", "'"))


# the words of a scaffold that make the structure being tested (others are names, nouns or words copied from the sentences)
CONNECTIVE = set("""unlike although though despite spite unless whose whom who which where when whether if neither nor either
or both as well not only but also no sooner than hardly scarcely barely had having being owing due because since so such too
enough instead without with upon on in by for of to regardless however therefore much all every none each prefers prefer
preferred rather would until till before after while whereas lest provided providing otherwise else together along besides
addition apart except matter whatever whoever wherever whenever more less most least whichever were should""".split())
REPORTING = set("""told asked said reminded warned ordered advised informed explained wondered promised suggested begged urged
instructed exclaimed replied remarked complained insisted admitted denied agreed offered refused threatened invited encouraged
apologised apologized enquired inquired commanded requested announced assured""".split())


# the only other forms a connective may take in a tip (otherwise the word itself, whole, any case)
INFLECT = {"prefer": {"prefers", "preferred", "preferring"}, "prefers": {"prefer", "preferred", "preferring"},
           "preferred": {"prefer", "prefers", "preferring"}, "provided": {"providing"}, "providing": {"provided"}}


def connectives(r):
    """Per printed stretch of the scaffold, the phrases a tip must mention one of. A phrase is a run of consecutive
    connective words (CONNECTIVE: "in spite of", "no sooner", "not only", "unlike") with at least one word not in the
    two sentences. A stretch with a reporting verb (told, asked ...) may also be met by that verb, "reported", "direct",
    "speech", "if" or "whether", and one whose phrase has "by" by "passive". A stretch with neither asks nothing."""
    stem = set(words(r["stem"]))
    out = []
    for part in re.split(r"_{2,}", r.get("scaffold") or ""):
        ws = words(part)
        runs, cur = [], []
        for w in ws + [None]:
            if w in CONNECTIVE:
                cur.append(w)
                continue
            if cur and any(x not in stem for x in cur):
                runs.append(tuple(cur))
            cur = []
        rep = sorted(REPORTING & set(ws))
        if runs or rep:
            out.append(runs + ([(x,) for x in rep + ["reported", "direct", "speech", "if", "whether"]] if rep else [])
                       + ([("passive",)] if any("by" in x for x in runs) else []))
    return out


def phrase_in(run, text):
    """A connective phrase in a tip: several words as that exact phrase (spaces or quote marks between them); one word
    whole, any case, in its listed forms only (INFLECT); a short word (3 letters or fewer: in, on, so, if) only when
    quoted or right next to a quoted stretch ('in' + 'disbelief', in "disbelief")."""
    q = "[\"'“”‘’]"
    if len(run) > 1:
        return bool(re.search(r"(?<![\w])" + (r"(?:\s|" + q + r")+").join(map(re.escape, run)) + r"(?![\w])", text, re.I))
    for f in {run[0]} | INFLECT.get(run[0], set()):
        w = re.escape(f)
        if len(f) > 3:
            if re.search(r"(?<![\w])" + w + r"(?!\w|['’]\w)", text, re.I):
                return True
        elif quoted_word(f, text) or re.search(r"(?<![\w'’])" + w + r"\s*(?:\+\s*)?" + q, text, re.I) \
                or re.search(q + r"\s*(?:\+\s*)?" + w + r"(?!\w|['’]\w)", text, re.I):
            return True
    return False


def lint_st(r, text):
    if not text:
        return "no tip"
    if len(text) < RIGHT_MIN:
        return "tip too short"
    if len(text) > RIGHT_MAX:
        return f"tip longer than {RIGHT_MAX}"
    if style(text):
        return style(text)
    if numbered(text):
        return "names an option by letter or number"
    for alts in connectives(r):
        if not any(phrase_in(run, text) for run in alts):
            return "does not mention the scaffold's connective"
    return ""


def doubt_of(rec, r, verdict=None):
    """Why a question's key is in doubt, or '' (a writer's doubt, a blind answer that differs, a checker's doubt)."""
    if rec and isinstance(rec.get("doubt"), str) and rec["doubt"].strip():
        return rec["doubt"].strip()
    if rec and isinstance(rec.get("blind"), int) and not isinstance(rec.get("blind"), bool) and rec["blind"] != r["answer"]:
        return f"the writer's blind answer is option index {rec['blind']}, the key is {r['answer']}"
    if verdict and isinstance(verdict.get("doubt"), str) and verdict["doubt"].strip():
        return "checker: " + verdict["doubt"].strip()
    return ""


def state(section):
    """rs, texts {id: explanation as the site would get it}, lint {id: reason or ''}, records (writer lines)."""
    kind, rs = cfg(section)["kind"], rows(section)
    if kind == "st":
        texts = st_texts(section, rs)
        return rs, texts, {i: lint_st(r, texts.get(i, "")) for i, r in rs.items()}, {}
    w = written_mcq(section)
    texts = {i: expl_of(w[i]) for i in rs if i in w}
    return rs, texts, {i: lint_mcq(r, w.get(i)) for i, r in rs.items()}, w


# ---------------------------------------------------------------- commands

def cmd_pack(section, force=False):
    c, rs = cfg(section), rows(section)
    d = wdir(section)
    d.mkdir(parents=True, exist_ok=True)
    answered = sorted(f.name for f in d.glob("out_[0-9]*.jsonl")) + sorted(f.name for f in d.glob("check_*.jsonl"))
    if answered and (c["kind"] == "st" or not force):
        # synthesis: out_N are the verdicts on pack_N's tips; new packs would tie them to texts they never judged
        sys.exit(f"{d} already has {', '.join(answered)}: " + ("move pack_N and out_N away together first (they are "
                 "the first check of the tips)" if c["kind"] == "st" else "new packs could reorder what they answer "
                 "(pass --force to rebuild)"))
    texts = st_texts(section, rs) if c["kind"] == "st" else {}  # read before anything is removed
    for f in d.glob("pack_*.jsonl"):
        f.unlink()
    if c["kind"] == "st":
        items = [{"id": i, "stem": r["stem"], "scaffold": r["scaffold"], "accept": r["accept"], "tip": texts.get(i, ""),
                  "lint": lint_st(r, texts.get(i, "")), "fp": fp(r)} for i, r in sorted(rs.items())]
        groups = chunks(items, c["per"])
        missing = sum(1 for x in items if not x["tip"])
        for k, g in enumerate(groups):
            write_jsonl(d / f"pack_{k}.jsonl", g)
        print(f"{section}: {len(items)} tips in {len(groups)} packs ({', '.join(str(len(g)) for g in groups)}); "
              f"{sum(1 for x in items if x['lint'])} fail lint as they stand; {missing} without a tip -> {d}/pack_N.jsonl")
        return
    ss = sets(rs)
    lines = []
    for s in ss:
        qs = [{"id": r["id"], "n": r["seq"], "stem": question_of(r) if c["kind"] == "vc" else r["stem"],
               "options": r["options"], "key": r["answer"]} for r in s]
        line = {"grp": s[0]["grp"], "section": "Visual Text" if c["kind"] == "vt" else "Vocabulary Cloze"}
        if c["kind"] == "vt":
            line["images"] = images(s[0])
            assert all(images(r) == line["images"] for r in s), f"{s[0]['grp']}: questions of one set with different pages"
        else:
            line["passage"] = passage_of(s[0])
            assert all(passage_of(r) == line["passage"] for r in s), f"{s[0]['grp']}: questions of one set with different passages"
        line["questions"] = qs
        lines.append(line)
    groups = chunks(lines, c["per"])
    for k, g in enumerate(groups):
        write_jsonl(d / f"pack_{k}.jsonl", g)
    imgs = [p for x in lines for p in x.get("images", [])]
    lost = [p for p in imgs if not Path(p).is_file()]
    print(f"{section}: {len(lines)} sets, {len(rs)} questions in {len(groups)} packs "
          f"({', '.join(str(sum(len(x['questions']) for x in g)) + 'q/' + str(len(g)) + 's' for g in groups)})"
          + (f"; {len(imgs)} images, {len(set(imgs))} distinct, {len(lost)} missing on disk" if c["kind"] == "vt" else "")
          + f" -> {d}/pack_N.jsonl")
    if lost:
        print("missing images:", *lost[:10], sep="\n  ")


def cmd_lint(section, quiet=False):
    rs, texts, lint, w = state(section)
    why = collections.Counter(v or "ok" for v in lint.values())
    if not quiet:
        print(section, dict(why.most_common()))
        if w:
            print("  doubts:", sum(1 for i, r in rs.items() if not lint[i] and doubt_of(w.get(i), r)))
    return rs, texts, lint, w


def cmd_checkpack(section, tag=None):
    """Packs for the checkers: every lint-clean item with no doubt and no verdict that still holds. Synthesis also sends
    every tip that fails lint (a rewrite that broke a rule, or no tip at all) with its "lint" reason, for the checker to
    rewrite; Visual Text and Vocabulary Cloze list theirs (a writer fixes those, in out_fix*.jsonl). A pack already
    answered is never overwritten (its verdicts would no longer match what the checker saw); the packs are recorded in
    seq.json as made after everything before them."""
    c = cfg(section)
    rs, texts, lint, w = cmd_lint(section)
    v, _ = verdicts(section, rs, texts)
    todo = {i for i in rs if not lint[i] and i not in v and not (w and doubt_of(w.get(i), rs[i]))}
    bad = sorted(i for i in rs if lint[i] and (c["kind"] == "st" or lint[i] != "not written"))
    if bad:
        print(f"{len(bad)} fail lint" + (" (sent with their reason)" if c["kind"] == "st" else " (not sent: the writer fixes them)") + ":")
        for i in bad:
            print(f"  {i}: {lint[i]}")
    d = wdir(section)
    d.mkdir(parents=True, exist_ok=True)
    if c["kind"] == "st":
        lines = [{"id": i, "stem": rs[i]["stem"], "scaffold": rs[i]["scaffold"], "accept": rs[i]["accept"],
                  "tip": texts.get(i, ""), "lint": lint[i], "fp": fp(rs[i])} for i in sorted(todo | set(bad))]
        count = len(lines)
    else:
        lines = []
        for s in sets(rs):
            qs = [{"id": r["id"], "n": r["seq"], "stem": question_of(r) if c["kind"] == "vc" else r["stem"],
                   "options": r["options"], "key": r["answer"], "explanation": texts[r["id"]], "fp": fp(r)}
                  for r in s if r["id"] in todo]
            if qs:
                line = {"grp": s[0]["grp"]}
                line.update({"images": images(s[0])} if c["kind"] == "vt" else {"passage": passage_of(s[0])})
                lines.append(dict(line, questions=qs))
        count = sum(len(x["questions"]) for x in lines)
    if not lines:
        print("nothing to check (no pack written)")
        return
    if tag:
        names, groups = [tag], [lines]
    else:
        rnd = 1
        while list(d.glob(f"cpack_r{rnd}_*.jsonl")):
            rnd += 1
        groups = chunks(lines, c["per"])
        names = [f"r{rnd}_{k}" for k in range(len(groups))]
    for name in names[:len(groups)]:
        if (d / f"cpack_{name}.jsonl").exists():
            sys.exit(f"cpack_{name}.jsonl already exists: pick another tag")
    for name, g in zip(names, groups):
        write_jsonl(d / f"cpack_{name}.jsonl", g)
    if groups:
        record(section, [f"cpack_{n}.jsonl" for n in names[:len(groups)]])
    print(f"{count} to check in {len(groups) if lines else 0} packs: " + ", ".join(f"cpack_{n}.jsonl" for n in names[:len(groups) if lines else 0]))


def merge(old_lines, new_by_id, cur_fp, drop=frozenset(), doubted=frozenset()):
    """The selection's explain.jsonl after this run. old_lines: its lines; new_by_id: {id: line} this run ships;
    cur_fp: {id: fp} of this section's questions; drop: ids whose existing line must go (--drop-failed);
    doubted: ids this run records a doubt for (writer blind != key, writer or checker doubt): their old line goes too.
    Lines of other sections are kept untouched; a line of this section with a stale fp is dropped (the upload would
    ignore it); a current one stays unless this run replaces it."""
    out, st = [], collections.Counter()
    seen = set()
    for x in old_lines:
        i = x.get("id")
        if i not in cur_fp:
            out.append(x)
            st["other sections kept"] += 1
        elif x.get("fp") != cur_fp[i]:
            st["stale dropped"] += 1
            continue  # not "seen": a new line for this id must still be added below (25 Nov 2026: it took a second run)
        elif i in doubted:
            st["dropped: now doubted"] += 1
        elif i in new_by_id:
            same = new_by_id[i]["explain"] == x.get("explain")
            out.append(x if same else new_by_id[i])
            st["kept (confirmed)" if same else "replaced"] += 1
        elif i in drop:
            st["dropped (checker failed)"] += 1
        else:
            out.append(x)
            st["kept"] += 1
        seen.add(i)
    for i, x in new_by_id.items():
        if i not in seen:
            out.append(x)
            st["added"] += 1
    return out, st


def failed_lines(old, new, cur, failed, kind):
    """Ids of existing lines (current fp, not replaced by this run) whose exact text a checker failed; texts compared
    stripped; a line with no explanation, or none with a "right", is never flagged."""
    def norm(e):
        if not isinstance(e, dict) or not isinstance(e.get("right"), str):
            return None
        if kind == "st":
            return e["right"].strip()
        w = e.get("wrong")
        return ekey({"right": e["right"].strip(),
                     "wrong": [s.strip() if isinstance(s, str) and s.strip() else None for s in w] if isinstance(w, list) else None})
    fails = {i: {s.strip() if kind == "st" else s for s in ts if isinstance(s, str)} for i, ts in failed.items()}
    return {x["id"] for x in old if x.get("id") in cur and x.get("fp") == cur[x["id"]] and x["id"] not in new
            and norm(x.get("explain")) is not None and norm(x.get("explain")) in fails.get(x["id"], set())}


def cmd_apply(section, drop_failed=False):
    c = cfg(section)
    rs, texts, lint, w = cmd_lint(section, quiet=True)
    v, failed = verdicts(section, rs, texts)
    new, doubts, why = {}, [], collections.Counter()
    for i, r in sorted(rs.items()):
        dbt = doubt_of(w.get(i), r, v.get(i)) if c["kind"] != "st" else ""
        if dbt:
            doubts.append({"id": i, "grp": r.get("grp"), "stem": r["stem"], "options": r["options"], "answer": r["answer"],
                           "blind": (w.get(i) or {}).get("blind"), "doubt": dbt,
                           **({"images": images(r)} if c["kind"] == "vt" else {})})
            why["doubt (not explained)"] += 1
        elif lint[i]:
            why["lint: " + lint[i]] += 1
        elif i not in v:
            why["not checked (or checked for another text, key or question)"] += 1
        elif v[i].get("ok") is not True:
            why["checker failed it"] += 1
        else:
            e = {"right": texts[i], "wrong": []} if c["kind"] == "st" else texts[i]
            new[i] = {"id": i, "fp": fp(r), "explain": e, "src": "claude-opus-checked"}
            why["passed"] += 1
    cur = {i: fp(r) for i, r in rs.items()}
    path = c["sel"] / "explain.jsonl"
    old = jl(path)
    flagged = failed_lines(old, new, cur, failed, c["kind"])
    out, st = merge(old, new, cur, flagged if drop_failed else frozenset(), {x["id"] for x in doubts})
    d = wdir(section)
    d.mkdir(parents=True, exist_ok=True)
    if path.exists():
        (d / "backup").mkdir(exist_ok=True)
        (d / "backup" / f"explain.{time.strftime('%Y%m%d-%H%M%S')}.jsonl").write_bytes(path.read_bytes())
    write_jsonl(path, out)
    write_jsonl(d / "doubts.jsonl", doubts)
    print(f"{section}: {len(rs)} questions {dict(why.most_common())}")
    print(f"  {path}: {len(out)} lines; {dict(st)}" + (f"; {len(flagged)} existing lines a checker failed were "
          + ("dropped" if drop_failed else "KEPT (pass --drop-failed to remove them)") if flagged else ""))
    print(f"  {len(doubts)} doubts -> {d / 'doubts.jsonl'}")


# ---------------------------------------------------------------- selftest

def selftest():
    o = ["a red kite", "a blue boat", "a green frog", "a yellow bus"]
    r = {"id": "x1", "subtopic": "eng-visual-text", "stem": "What does the poster show?", "options": o, "answer": 2}
    good = {"id": "x1", "blind": 2, "right": "The poster shows \"a green frog\" sitting on a leaf.",
            "wrong": ["The kite is on another poster, not this one.", "The boat appears in the shop's other advert.", None,
                      "The bus is only in the background of the photograph."]}
    assert lint_mcq(r, good) == "", lint_mcq(r, good)
    bad = lambda **kw: lint_mcq(r, dict(good, **kw))
    assert bad(right="x" * 601 + " \"a green frog\"") == f"right longer than {RIGHT_MAX}"
    assert bad(wrong=["k" * 401 + " kite", "boat no", None, "bus no"]) == f"a wrong note longer than {WRONG_MAX}"
    assert bad(right="The poster shows \"a green frog\"!") == "has '!'"
    assert bad(right="The poster says \"Meet a green frog today!\", so \"a green frog\" fits.") == "", "'!' inside a quote"
    assert bad(right="The answer is \"a green frog\" on a leaf.") == "starts 'The answer is'"
    assert bad(right="The poster shows an animal on a leaf near water.") == "does not name the answer"
    assert bad(right="(3) \"a green frog\" sits on a leaf.") == "names an option by letter or number"
    assert bad(right="Option C, \"a green frog\", sits on a leaf.") == "names an option by letter or number"
    assert bad(wrong=["The kite is not there.", "Unlike option B, ...", None, "The bus is not there."]) == "names an option by letter or number"
    assert bad(wrong=["The kite is not there.", "The boat is elsewhere.", "x", "The bus is far."]) == "the key's slot is not null"
    assert bad(wrong=["The kite is not there.", None, None, "The bus is far."]) == "a wrong option has no note"
    assert bad(wrong=["The kite.", "The boat."]) == "wrong is not one entry per option"
    assert bad(wrong=["Not on the poster.", "Not on the poster.", None, "Not on the poster."]) == "the notes do not talk about their own options"
    assert bad(blind=None) == "no blind answer" and lint_mcq(r, None) == "not written"
    assert lint_mcq(r, dict(good, right="An answer like \"a green frog\" fits; the answer a child picks matters.")) == "", "the article a is not a letter"
    assert doubt_of(dict(good, blind=1), r).startswith("the writer's blind answer") and doubt_of(good, r) == ""
    assert doubt_of(dict(good, doubt="two options fit"), r) == "two options fit"
    assert doubt_of(good, r, {"ok": True, "doubt": "key?"}) == "checker: key?"
    long_o = ["People can join the walk for free on Saturday morning", "x y", "z w", "q r"]
    assert names_answer(long_o[0], "Anyone may join the morning walk on Saturday for free.") and not names_answer(long_o[0], "It costs money.")
    vc = {"id": "v", "subtopic": "eng-vocab-cloze", "seq": 3, "stem": "p\n\nq", "options": ["huge", "tiny", "quiet", "noisy"], "answer": 0}
    vgood = {"id": "v", "blind": 0, "right": "The word marked (3) means very big, so \"huge\" fits.",
             "wrong": [None, "\"Tiny\" means very small.", "\"Quiet\" is about sound.", "\"Noisy\" is about sound."]}
    assert lint_mcq(vc, vgood) == "", "a blank's own number is allowed in Vocabulary Cloze"
    assert lint_mcq(vc, dict(vgood, right="Like (2), \"huge\" means very big.")) == "names an option by letter or number"
    st = {"stem": "Tom likes tea but Ann does not.", "scaffold": "Unlike Tom, ____"}
    assert connectives(st) == [[("unlike",)]]
    rep = {"stem": "\"I will come,\" said Tom.", "scaffold": "Tom told Ann that ____"}
    assert connectives(rep) == [[("told",), ("reported",), ("direct",), ("speech",), ("if",), ("whether",)]] and lint_st(rep, "In reported speech, 'will' becomes 'would'.") == ""
    assert connectives({"stem": "x", "scaffold": "Mr Lim's ____"}) == [], "a name is not a connective"
    assert lint_st(st, "\"Unlike\" compares two people, so say how Ann is different.") == ""
    assert lint_st(st, "Compare the two people and say how Ann is different.") == "does not mention the scaffold's connective"
    assert lint_st(st, "\"Unlike\" compares two people!") == "has '!'"
    assert lint_st(st, "x" * 601 + " unlike") == f"tip longer than {RIGHT_MAX}"
    nn = {"stem": "Tom cannot swim. Ann cannot swim.", "scaffold": "Neither ____ nor ____"}
    assert connectives(nn) == [[("neither",)], [("nor",)]] and lint_st(nn, "\"Neither\" goes with \"nor\" and a singular verb.") == ""
    assert lint_st(nn, "Use \"neither\" with a singular verb.") == "does not mention the scaffold's connective"
    assert lint_st(st, "Use 'Unlike' + a noun, then say how Ann differs.") == "", "single-quoted words count"
    assert lint_st(nn, "Put 'neither' before the first choice and 'nor' before the second.") == "", "'first choice' is plain English"
    assert lint_st({"stem": "s t", "scaffold": "____ in ____"}, "Use \"in\" before the place.") == "", "a short connective"
    # 5: the printed connective phrase, whole; a short word only quoted or next to a quote
    sp = {"stem": "It rained. We played.", "scaffold": "In spite of ____"}
    assert connectives(sp) == [[("in", "spite", "of")]]
    assert lint_st(sp, "Use 'in spite of' + a noun or an -ing word.") == ""
    assert lint_st(sp, "Use 'spite' with a noun, and put the reason first.") == "does not mention the scaffold's connective"
    ns = {"stem": "He sat. It rang.", "scaffold": "No sooner ____ than ____"}
    assert lint_st(ns, "\"No sooner\" is followed by had, then \"than\".") == ""
    assert lint_st(ns, "Say \"sooner\" first, then \"than\".") == "does not mention the scaffold's connective"
    ins = {"stem": "s t", "scaffold": "____ in ____"}
    assert lint_st(ins, "Put the place word in the right order here.") == "does not mention the scaffold's connective"
    assert lint_st(ins, "Use in 'disbelief' as a phrase about feeling.") == "" and lint_st(ins, "Use 'in' + a noun of feeling.") == ""
    # 6: whole words only (Unlike is not Unless); only listed inflections
    un = {"stem": "Go now or you will be late.", "scaffold": "____ unless ____"}
    assert lint_st(un, "\"Unlike\" would compare; this needs a condition.") == "does not mention the scaffold's connective"
    assert lint_st(un, "\"Unless\" means if not, so drop the not.") == ""
    pf = {"stem": "Ann likes tea more than coffee.", "scaffold": "Ann prefers ____"}
    assert lint_st(pf, "After 'prefer', use 'tea to coffee' with to.") == "", "a listed form"
    assert lint_st(pf, "Use 'preference' and then the noun.") == "does not mention the scaffold's connective"
    # 7: names_answer is whole-word, and an option's own quote marks are not needed twice
    assert not names_answer("on", "We \"rely upon\" friends.") and names_answer("on", "We \"rely on\" friends.")
    assert names_answer("\"Ahoy Captain\"", "The sign says \"Ahoy Captain\" at the door.")
    assert names_answer("$12", "The poster says \"$12\" for adults.") and not names_answer("$12", "The poster says \"$125\".")
    # 9: options with no content word are matched by their numbers
    assert about("Tickets cost $12 at the door.", "$12") and not about("Tickets cost $120.", "$12")
    assert about("The show starts at 10 a.m. sharp.", "10 a.m.") and not about("The show starts at 11 a.m.", "10 a.m.")
    assert about("It closes on 3 May.", "3 May") and not about("It is closed.", "3:30 p.m.")
    # 10: --drop-failed: null or right-less lines never flagged, texts compared stripped
    oldl = [{"id": "a", "fp": "1", "explain": None}, {"id": "b", "fp": "2", "explain": {"wrong": []}},
            {"id": "c", "fp": "3", "explain": {"right": "Tip C.  ", "wrong": []}}, {"id": "d", "fp": "4", "explain": {"right": "Tip D.", "wrong": []}}]
    assert failed_lines(oldl, {}, {"a": "1", "b": "2", "c": "3", "d": "4"},
                        {"a": {""}, "b": {"x"}, "c": {"Tip C."}, "d": {"other"}}, "st") == {"c"}
    me = {"right": "R ", "wrong": [None, " w1", "w2", "w3"]}
    assert failed_lines([{"id": "m", "fp": "1", "explain": me}], {}, {"m": "1"},
                        {"m": {ekey({"right": "R", "wrong": [None, "w1", "w2", "w3"]})}}, "vt") == {"m"}
    # merge: other sections untouched, stale dropped, current kept unless replaced, new added, --drop-failed
    old = [{"id": "a", "fp": "1", "explain": {"right": "A"}}, {"id": "b", "fp": "old", "explain": {"right": "B"}},
           {"id": "c", "fp": "3", "explain": {"right": "C"}}, {"id": "z", "fp": "9", "explain": {"right": "Z"}},
           {"id": "d", "fp": "4", "explain": {"right": "D"}}, {"id": "f", "fp": "6", "explain": {"right": "F"}}]
    new = {"c": {"id": "c", "fp": "3", "explain": {"right": "C2"}}, "e": {"id": "e", "fp": "5", "explain": {"right": "E"}},
           "d": {"id": "d", "fp": "4", "explain": {"right": "D"}, "src": "x"}}
    cur = {"a": "1", "b": "2", "c": "3", "d": "4", "e": "5", "f": "6"}
    out, s = merge(old, new, cur)
    got = {x["id"]: x["explain"]["right"] for x in out}
    assert got == {"a": "A", "c": "C2", "z": "Z", "d": "D", "e": "E", "f": "F"}, got
    assert s == {"kept": 2, "stale dropped": 1, "replaced": 1, "other sections kept": 1, "kept (confirmed)": 1, "added": 1}, s
    out2, s2 = merge(old, new, cur, drop={"f"})
    assert "f" not in {x["id"] for x in out2} and s2["dropped (checker failed)"] == 1 and s2["kept"] == 1
    assert merge(old, {}, {})[0] == old, "a section with no questions leaves the file as it is"
    out3, s3 = merge(old, new, cur, doubted={"a", "z", "e"})  # a current line now doubted goes; other sections and new lines do not
    assert "a" not in {x["id"] for x in out3} and s3["dropped: now doubted"] == 1 and {"z", "e"} <= {x["id"] for x in out3}, s3
    # a stale line whose question this run re-checked: the new line is added in the SAME run (25 Nov 2026: it took two)
    out4, s4 = merge(old, {"b": {"id": "b", "fp": "2", "explain": {"right": "B2"}}}, cur)
    assert {x["id"]: x["explain"]["right"] for x in out4}.get("b") == "B2" and s4["stale dropped"] == 1 and s4["added"] == 1, s4
    # verdict ties and synthesis rewrites, on files under WORK/_selftest (never /tmp)
    global SECTIONS
    saved = SECTIONS
    base = WORK / "_selftest"
    try:
        import shutil
        shutil.rmtree(base, ignore_errors=True)
        sel = base / "sel"
        sel.mkdir(parents=True)
        q = {"id": "s1", "subtopic": "eng-synthesis", "kind": "typed", "stem": "Tom likes tea but Ann does not.",
             "scaffold": "Unlike Tom, ____", "accept": ["Unlike Tom, Ann does not like tea."], "options": [], "answer": 0}
        q2 = dict(q, id="s2")
        write_jsonl(sel / "selected.jsonl", [q, q2])
        write_jsonl(sel / "explain.jsonl", [{"id": "s1", "fp": fp(q), "explain": {"right": "Compare the two people here.", "wrong": []}},
                                            {"id": "s2", "fp": fp(q2), "explain": {"right": "\"Unlike\" shows a difference.", "wrong": []}},
                                            {"id": "other", "fp": "x", "explain": {"right": "kept", "wrong": []}}])
        SECTIONS = {"synthesis": {"sub": "eng-synthesis", "sel": sel, "kind": "st", "per": 95}}
        import builtins
        _print = builtins.print
        builtins.print = lambda *a, **k: None
        try:
            globals()["WORK"], wsaved = base, WORK
            d = wdir("synthesis")
            cmd_pack("synthesis")
            p0 = jl(d / "pack_0.jsonl")
            assert [x["lint"] for x in p0] == ["does not mention the scaffold's connective", ""], p0
            write_jsonl(d / "out_0.jsonl", [{"id": "s1", "ok": False, "reason": "no connective", "rewrite": "\"Unlike\" says how Ann differs."},
                                            {"id": "s2", "ok": True, "reason": ""}])
            rs = rows("synthesis")
            t = st_texts("synthesis", rs)
            assert t["s1"] == "\"Unlike\" says how Ann differs.", "a rewrite replaces the tip it judged"
            v, failed = verdicts("synthesis", rs, t)
            assert "s1" not in v and v["s2"]["ok"] is True, "the rewrite has no verdict yet"
            cmd_checkpack("synthesis")
            cp = jl(d / "cpack_r1_0.jsonl")
            assert [x["id"] for x in cp] == ["s1"], cp
            cmd_apply("synthesis")
            ex = {x["id"]: x for x in jl(sel / "explain.jsonl")}
            assert ex["s1"]["explain"]["right"] == "Compare the two people here." and ex["other"]["explain"]["right"] == "kept", "nothing lost before the rewrite passes"
            write_jsonl(d / "check_r1_0.jsonl", [{"id": "s1", "ok": True, "reason": ""}])
            cmd_apply("synthesis")
            ex = {x["id"]: x for x in jl(sel / "explain.jsonl")}
            assert ex["s1"]["explain"]["right"] == "\"Unlike\" says how Ann differs." and len(ex) == 3, ex
            assert ex["s1"]["fp"] == fp(q)
            # a changed key withdraws the verdict (and the stale line)
            write_jsonl(sel / "selected.jsonl", [dict(q, accept=["Unlike Tom, Ann dislikes tea."]), q2])
            rs = rows("synthesis")
            t = st_texts("synthesis", rs)
            v, _ = verdicts("synthesis", rs, t)
            assert "s1" not in v and "s1" not in t, "a new model answer needs a new tip and a new check"
            assert list((d / "backup").glob("explain.*.jsonl")), "a backup of the file before each apply"
            write_jsonl(sel / "selected.jsonl", [q, q2, dict(q, id="s3")])
            # 3: a fix after round 1, then a later check's rewrite of exactly that fix wins (recorded order, not file times)
            write_jsonl(d / "out_fix1.jsonl", [{"id": "s2", "right": "\"Unlike\" says how two people differ."}])
            rs = rows("synthesis")
            assert st_texts("synthesis", rs)["s2"] == "\"Unlike\" says how two people differ."
            cmd_checkpack("synthesis")
            cp2 = {x["id"]: x for x in jl(d / "cpack_r2_0.jsonl")}
            # 2 and 8: s3 has no tip; it is sent with its lint reason and tip ""
            assert cp2["s3"]["tip"] == "" and cp2["s3"]["lint"] == "no tip" and "s2" in cp2, cp2
            seq = json.loads((d / SEQ).read_text())
            assert seq["pack_0.jsonl"] < seq["cpack_r1_0.jsonl"] < seq["out_fix1.jsonl"] < seq["cpack_r2_0.jsonl"], seq
            import os
            os.utime(d / "cpack_r1_0.jsonl", (2e9, 2e9))  # a newer file time must not move it after round 2
            write_jsonl(d / "check_r2_0.jsonl", [{"id": "s2", "ok": False, "reason": "vague", "rewrite": "\"Unlike\" sets Ann against Tom."},
                                                 {"id": "s3", "ok": False, "reason": "no tip", "rewrite": "\"Unlike\" contrasts Ann with Tom."}])
            t = st_texts("synthesis", rs)
            assert t["s2"] == "\"Unlike\" sets Ann against Tom.", "a checker's rewrite of a fix takes effect"
            assert t["s3"] == "\"Unlike\" contrasts Ann with Tom.", "a rewrite of a missing tip is adopted"
            v, _ = verdicts("synthesis", rs, t)
            assert v["s1"]["ok"] is True and "s2" not in v and "s3" not in v
        finally:
            builtins.print = _print
            globals()["WORK"] = wsaved
    finally:
        SECTIONS = saved
        import shutil
        shutil.rmtree(base, ignore_errors=True)
    print("section_explain selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:]
    cmd = a[0] if a else ""
    if cmd == "selftest":
        selftest()
    elif cmd == "pack" and len(a) >= 2:
        cmd_pack(a[1], force="--force" in a)
    elif cmd == "lint" and len(a) >= 2:
        cmd_lint(a[1])
    elif cmd == "checkpack" and len(a) >= 2:
        cmd_checkpack(a[1])
    elif cmd == "recheck" and len(a) >= 3:
        cmd_checkpack(a[1], a[2])
    elif cmd == "apply" and len(a) >= 2:
        cmd_apply(a[1], drop_failed="--drop-failed" in a)
    else:
        sys.exit(__doc__)
