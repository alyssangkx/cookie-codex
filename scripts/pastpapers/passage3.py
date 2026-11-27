#!/usr/bin/env python3
"""More cloze passages from the third read (read3.jsonl, Qwen3.8). passage.py keeps a passage only when its first two reads
agree; about 245 stay held, most because the two disagree. Here a passage is also accepted when ANY TWO of the three reads
agree under the very same rule (passage.judge: same markers, same underlined words, text ratio >= 0.95). Nothing of
passage.py or its outputs is changed. Work files: /data/alvin/tmp/cookie-codex/passage3/ (PP3_WORK overrides). Past-paper
text never goes in the repo.

  passage3.py agree3    cloze / vocabulary-cloze sections not in passage.py's passages.jsonl, accepted when two of the three
                        reads agree -> passage3/passages3.jsonl (passages.jsonl's shape: sec, st, year, paper, ids, passage,
                        markers); prints counts per section type and why the rest stay unagreed
  passage3.py pack      blind-answer packs for the newly agreed passages that could still ship (a readable key for every blank;
                        a Grammar Cloze needs a trustworthy word box; no copy of a live or earlier passage)
                          passage3/blind_N.jsonl  Grammar/Comprehension Cloze, ~10 passages each, NO KEYS:
                            {"sec", "st", "box": [words] | null, "blanks": [n, ...], "text": "... (n) ____ ..."}
                          passage3/vc_N.jsonl     Vocabulary Cloze, ~10 passages each, NO KEYS:
                            {"sec", "passage": "... {{n|underlined}} ...", "questions": [{"n", "options": [4 strings]}]}
  passage3.py settle    two independent blind outputs per pack -> passage3/ship/english/selected.jsonl (complete passages only)
  passage3.py judge-pack   blanks held as "both blind answers agree against the key" / "blind answers differ from each other
                        and from the key", in passages otherwise complete -> passage3/judge_1.jsonl
                          {"sec", "st", "box", "passage", "blanks": [{"n", "key": [accepted words], "blind": [a1, a2],
                           "options" (Vocabulary only: key and blind are option texts), "why_held"}]}
                        JUDGE OUTPUT: judge_out_1.jsonl, one line per blank
                          {"sec", "n", "key_fits": true|false|"unsure", "blind_also_right": [blind words ALSO fully correct], "why": "<under 20 words>"}
                        key_fits: the school key is grammatically and semantically correct there (Vocabulary: the key option is
                        the closest in meaning). settle then also writes passage3/ship_judged/english/selected.jsonl: only
                        passages made complete by key_fits true on every judged blank (the key alone is accepted); the blind
                        words listed in blind_also_right are NOT added, they go to passage3/also_right.jsonl for the owner.
  hold.jsonl lines {"sec", "reason"}: settle skips those passages (printed under the reason).
  passage3.py explain-pack      writer packs for ship/ and ship_judged/ (when present), under passage3/explain/<target>/:
                          cloze/pack_N.jsonl (cloze_explain.py's shape: {grp, section, passage, blanks: [{id, n, accept}]});
                          vc/vocab-cloze/pack_N.jsonl (section_explain.py's shape)
  passage3.py explain-checkpack [TAG]   lint-clean explanations -> cloze/cpack_N.jsonl, vc/vocab-cloze/cpack_rR_N.jsonl
  passage3.py explain-apply     lint-clean AND checker ok AND verdict tied to the exact text, key and passage -> <target>/english/explain.jsonl
                        (cloze_explain and section_explain are reused as they are: WORK/SHIP are re-pointed at runtime for
                        cloze_explain, SECEXP_WORK / SECEXP_SEL are set for section_explain; no live folder is touched)
  WRITER OUTPUT  cloze: cloze/out_N.jsonl  {"id", "right"}   (N = pack number; rewrites in out_fix*.jsonl)
                 vocab: vc/vocab-cloze/out_N.jsonl {"id", "blind", "right", "wrong": [note per option, null at the key], "doubt"?}
  CHECKER OUTPUT cloze: cloze/check_N.jsonl {"id", "ok": true|false, "reason"} beside cloze/cpack_N.jsonl
                 vocab: vc/vocab-cloze/check_rR_N.jsonl {"id", "ok", "reason", "doubt"?} beside cpack_rR_N.jsonl
  passage3.py selftest  made-up text only

ANSWERER OUTPUT CONTRACT (one JSON line per passage of the pack; the same text is given to two independent answerers):
  blind_out_N.jsonl  and  blind_out2_N.jsonl   {"sec": "<sec>", "answers": {"<n>": "<one word>"}}      (Grammar/Comprehension)
  vc_out_N.jsonl     and  vc_out2_N.jsonl      {"sec": "<sec>", "answers": {"<n>": <0-based index of the option>}}  (Vocabulary)
  Grammar Cloze: a word from the passage's box. Every blank number of the pack line should be answered.

SETTLING (per blank, school key as passage.py reads it: word-box letters resolved, "/" alternatives, load_pp.key for options):
  key equals both blind answers            -> settled, "key + both"
  key equals one, the other differs        -> settled, "key + one"
  both blind answers agree against the key -> UNSETTLED (the owner looks)
  no key, a blind answer missing, or the two blind answers differ from each other and from the key -> UNSETTLED
A passage ships only when every blank is settled. Row ids are pp_id(source question); set ids follow load_pp.set_id and the
rename rule of passage.export_cloze (-2, -3, ... when the id is already used by a live or earlier set)."""
import collections
import glob
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import passage as P  # noqa: E402

DEFAULT_OUT = P.TMP / "passage3"
OUT = Path(os.environ.get("PP3_WORK", str(DEFAULT_OUT)))  # another batch (e.g. queue 46) works in its own folder
KINDS = ("eng-grammar-cloze", "eng-comp-cloze", "eng-vocab-cloze")
READS = (("1", "read.jsonl"), ("2", "read2.jsonl"), ("3", "read3.jsonl"))
PAIRS = (("1", "3"), ("2", "3"))  # reads 1 and 2 already failed: `check` has seen them disagree
PER = 10
SUFFIX = {"eng-grammar-cloze": "gc", "eng-comp-cloze": "cc", "eng-vocab-cloze": "vc"}


def jl(p):
    return P.jl(p)


# ---- 1. agree3 ----------------------------------------------------------------------------------------------------------

def agree3():
    secs = {r["sec"]: r for r in jl(P.WORK / "sections.jsonl")}
    reads = {lb: {r["sec"]: r["raw"] for r in jl(P.WORK / f)} for lb, f in READS}
    have = {r["sec"] for r in jl(P.WORK / "passages.jsonl")}
    new, got, left = [], collections.Counter(), collections.Counter()
    for s, r in secs.items():
        if r["st"] not in KINDS or s in have:
            continue
        hit, whys = None, []
        for a, b in PAIRS:
            if s not in reads[b]:
                whys.append(f"{a}+{b}: no third read")
                continue
            p, w = P.judge(r, reads[a].get(s), reads[b].get(s))
            if p:
                hit = (p, f"{a}+{b}")
                break
            whys.append(f"{a}+{b}: {w}")
        if hit:
            new.append({"sec": s, "st": r["st"], "year": r["year"], "paper": r["paper"], "ids": r["ids"], "passage": hit[0],
                        "markers": P.markers(hit[0], r["kind"]), "agree": hit[1]})
            got[r["st"]] += 1
        else:
            # the reasons of both pairs; a section with no third read only has that one
            left[(r["st"], " | ".join(dict.fromkeys(whys)))] += 1
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "passages3.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in new))
    total = collections.Counter(r["st"] for s, r in secs.items() if r["st"] in KINDS and s not in have)
    print(f"{len(new)} newly agreed of {sum(total.values())} not agreed before -> {OUT / 'passages3.jsonl'}")
    for st in KINDS:
        print(f"  {st}: {got[st]} newly agreed, {total[st] - got[st]} still unagreed (of {total[st]})")
    # reasons: per pair first (what stops the third read helping), then the combination
    byreason = collections.Counter()
    for (st, w), n in left.items():
        for part in w.split(" | "):
            byreason[(st, part.split(": ", 1)[1] if ": " in part else part)] += n
    print("why the rest stay unagreed (a section counts once per pair that failed; top 12):")
    for (st, w), n in byreason.most_common(12):
        print(f"  {n:4d}  {st}  {w}")
    return new


# ---- shared: candidates for packs and settling --------------------------------------------------------------------------

def _qs():
    return {q["id"]: q for y in range(2018, 2027) for q in jl(P.TMP / "pastpapers" / "english" / str(y) / "merged.jsonl")}


def _tags():
    return {t["id"]: t for y in range(2018, 2027) for t in jl(P.TMP / "pastpapers" / "english" / str(y) / "tags72.jsonl")}


def _used():
    """Every set id, row id and passage text already used by a live or earlier set (they must not be reused or copied)."""
    grps, ids, sigs = set(), set(), set()
    for d in ("engcloze", "engcloze-ship", "engvc"):
        for f in glob.glob(str(P.TMP / "ppimport" / d / "english" / "*.jsonl")):
            for r in jl(f):
                if r.get("grp"):
                    grps.add(r["grp"])
                if r.get("id"):
                    ids.add(r["id"])
    for p in jl(P.WORK / "passages.jsonl"):
        sigs.add(" ".join(P.plain(p["passage"]).split()))
    if OUT != DEFAULT_OUT:  # a later batch: the first passage3 batch's passages and shipped sets count as used too
        for p in jl(DEFAULT_OUT / "passages3.jsonl"):
            sigs.add(" ".join(P.plain(p["passage"]).split()))
        for f in glob.glob(str(DEFAULT_OUT / "ship*" / "english" / "*.jsonl")):
            for r in jl(f):
                grps.add(r["grp"]) if r.get("grp") else None
                ids.add(r["id"]) if r.get("id") else None
    return grps, ids, sigs


def plan():
    """([candidate, ...], Counter of why a newly agreed passage cannot ship). A candidate:
    {"p": passage row, "st", "box", "keys": {n: [accepted words]} (cloze) or {n: 0-based index} (vocabulary),
     "qs": {n: source question}, "grp"}. Deterministic, so pack and settle see the same list."""
    import load_pp
    qs, tags = _qs(), _tags()
    used_grps, used_ids, sigs = _used()
    out, why, grp_sec = [], collections.Counter(), {}
    for p in sorted(jl(OUT / "passages3.jsonl"), key=lambda x: x["sec"]):
        st = p["st"]
        sig = " ".join(P.plain(p["passage"]).split())
        if sig in sigs:
            why[(st, "same text as a live or earlier passage")] += 1
            continue
        cands = [qs[i] for i in p["ids"] if i in qs]
        by = collections.defaultdict(list)
        for q in cands:
            by[q.get("qno")].append(q)
        marks = sorted(int(k) for k in p["markers"])
        box, letters, keys, qsrc = None, None, {}, {}
        if st == "eng-vocab-cloze":
            for n in marks:
                opts = [q for q in by.get(n, []) if len(q.get("options") or []) == 4]
                ks = {load_pp.key(q.get("answer"), q["options"]) for q in opts}
                if not opts or len(ks) != 1 or None in ks:
                    why[(st, "a mark has no question, no key, or copies disagree")] += 1
                    break
                q = sorted(opts, key=lambda q: q["id"])[0]
                if load_pp.garbled(load_pp.VC_STEM, q["options"]):
                    why[(st, "options garbled")] += 1
                    break
                keys[n], qsrc[n] = int(next(iter(ks))) - 1, q
            else:
                if len({tuple(load_pp.strip_opts(q["options"])) for q in qsrc.values()}) < len(qsrc):
                    why[(st, "two questions with the same options")] += 1
                    continue
                sigs.add(sig)
                out.append({"p": p, "st": st, "box": None, "keys": keys, "qs": qsrc})
            continue
        if st == "eng-grammar-cloze":
            box = next((q["options"] for q in cands if len(q.get("options") or []) >= 8), None)
            letters = [m.group(1) for m in (re.match(r"^\(?([A-Z])\)?\s+", o) for o in box or []) if m] if box else []
            letters = letters if box and len(letters) == len(box) else None
            box = [re.sub(r"^\(?[A-Z]\)?\s+", "", o).strip() for o in box] if box else None
            if not P.box_ok(box):
                why[(st, "word box missing or garbled")] += 1
                continue
        for n in marks:
            ks = [P.cloze_keys(st, q.get("answer"), box, letters) for q in by.get(n, [])]
            ks = [k for k in ks if k]
            if not ks or any([w.lower() for w in k] != [w.lower() for w in ks[0]] for k in ks):
                why[(st, "a blank has no readable key or its copies disagree")] += 1
                break
            keys[n], qsrc[n] = ks[0], sorted(by[n], key=lambda q: q["id"])[0]
        else:
            sigs.add(sig)
            out.append({"p": p, "st": st, "box": box, "keys": keys, "qs": qsrc})
    assign_grps(out, used_grps, used_ids, grp_sec)
    return out, why


def assign_grps(out, used_grps, used_ids, grp_sec):
    """Set ids: load_pp.set_id of the first blank's question, renamed (-2, -3, ...) when already used (passage.export_cloze).
    Sets c["grp"] on every candidate; asserts no row id is already live."""
    import load_pp
    for c in out:
        q = c["qs"][min(c["qs"])]
        g, k = load_pp.set_id(q, SUFFIX[c["st"]]), 2
        base = g
        while g in used_grps or (g in grp_sec and grp_sec[g] != c["p"]["sec"]):
            g, k = f"{base}-{k}", k + 1
        grp_sec[g] = c["p"]["sec"]
        c["grp"] = g
        for n, q in c["qs"].items():
            assert load_pp.pp_id(q["id"]) not in used_ids, f"{q['id']}: row id already used by a live row"


# ---- fingerprints: answers and verdicts belong to the text, box and key they were given for ---------------------------------

FP = "packed_fp.json"        # {sec: fingerprint of what the blind answerers were given}
JFP = "judge_fp.json"        # {sec: fingerprint of what the judge was given (that plus the open blanks and blind answers)}
OUT_PATTERNS = {"blind": ("blind_out_*.jsonl", "blind_out2_*.jsonl", "vc_out_*.jsonl", "vc_out2_*.jsonl"), "judge": ("judge_out_*.jsonl",)}


def _h(x):
    import hashlib
    return hashlib.sha1(json.dumps(x, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def fingerprint(c):
    """Of a candidate: its text as packed, word box and keys (Vocabulary: the option lists and key indices)."""
    import load_pp
    vc = c["st"] == "eng-vocab-cloze"
    text = c["p"]["passage"] if vc else P.cloze_stem(c["p"]["passage"], -1)
    opts = {str(n): load_pp.strip_opts(q["options"]) for n, q in c["qs"].items()} if vc else None
    return _h([text, c["box"], {str(n): k for n, k in c["keys"].items()}, opts])


def judge_fingerprint(c, res):
    """The packed fingerprint plus every open blank's key and the two blind answers the judge saw."""
    return _h([fingerprint(c), [[n, c["keys"][n], blind_of(c, n)] for n, (ok, _) in sorted(res.items()) if not ok]])


def _load_fp(name):
    f = OUT / name
    return json.loads(f.read_text()) if f.exists() else None


def _answered(kind):
    secs = set()
    for pat in OUT_PATTERNS[kind]:
        for f in glob.glob(str(OUT / pat)):
            secs |= {r["sec"] for r in jl(f) if r.get("sec")}
    return secs


def write_fp(name, new, kind):
    """Merge new {sec: fp} into the stamp file. A section that already has answers keeps its old stamp when the new one
    differs (so settle goes on refusing it until its stale answer rows are removed and it is re-packed); those secs are
    returned."""
    old = _load_fp(name) or {}
    done, stale = _answered(kind), []
    for s, fp in new.items():
        if s not in old or s not in done:
            old[s] = fp
        elif old[s] != fp:
            stale.append(s)
    (OUT / name).write_text(json.dumps(old, indent=0, sort_keys=True) + "\n")
    return stale


def stamp():
    """One-off, run deliberately for a run made before the stamps existed: stamp every candidate that has blind answers
    (and every judgeable one that has a judge verdict) with its CURRENT fingerprint. Right only if the packs were made
    from this plan()."""
    cs, _ = plan()
    done = _answered("blind")
    fp = _load_fp(FP) or {}
    n = 0
    for c in cs:
        s = c["p"]["sec"]
        if s in done and s not in fp:
            fp[s] = fingerprint(c)
            n += 1
    (OUT / FP).write_text(json.dumps(fp, indent=0, sort_keys=True) + "\n")
    jfp, jn = _load_fp(JFP) or {}, 0
    jdone = _answered("judge")
    for c, res, status in evaluate(check=False):
        s = c["p"]["sec"]
        if status == "judgeable" and s in jdone and s not in jfp:
            jfp[s] = judge_fingerprint(c, res)
            jn += 1
    (OUT / JFP).write_text(json.dumps(jfp, indent=0, sort_keys=True) + "\n")
    print(f"stamped {n} passages in {OUT / FP}, {jn} judged passages in {OUT / JFP}")


def stale_why(c, fps, kind="blind", fp=None):
    """"" if the stamp for this candidate matches, else why settle must not use its answers."""
    s = c["p"]["sec"]
    if fps is None or s not in fps:
        return "no pack stamp (run `stamp` once for an older run, or re-pack)"
    return "" if fps[s] == (fp or fingerprint(c)) else "answers are for another text, box or key: re-pack and re-answer"


# ---- 2. pack ------------------------------------------------------------------------------------------------------------

def pack():
    cs, why = plan()
    for f in glob.glob(str(OUT / "blind_[0-9]*.jsonl")) + glob.glob(str(OUT / "vc_[0-9]*.jsonl")):
        Path(f).unlink()  # a re-pack replaces the old packs; outputs (blind_out*, vc_out*) are not touched
    import load_pp
    cl = [c for c in cs if c["st"] != "eng-vocab-cloze"]
    vc = [c for c in cs if c["st"] == "eng-vocab-cloze"]
    for i in range(0, len(cl), PER):
        lines = [{"sec": c["p"]["sec"], "st": c["st"], "box": c["box"], "blanks": sorted(c["keys"]),
                  "text": P.cloze_stem(c["p"]["passage"], -1)} for c in cl[i:i + PER]]
        (OUT / f"blind_{i // PER + 1}.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in lines))
    for i in range(0, len(vc), PER):
        lines = [{"sec": c["p"]["sec"], "passage": c["p"]["passage"],
                  "questions": [{"n": n, "options": load_pp.strip_opts(c["qs"][n]["options"])} for n in sorted(c["qs"])]}
                 for c in vc[i:i + PER]]
        (OUT / f"vc_{i // PER + 1}.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in lines))
    stale = write_fp(FP, {c["p"]["sec"]: fingerprint(c) for c in cs}, "blind")
    if stale:
        print(f"WARNING {len(stale)} passages changed since they were answered (stamp kept old, settle refuses them): "
              f"remove their rows from the blind_out*/vc_out* files, then pack again: {stale}")
    cnt = collections.Counter(c["st"] for c in cs)
    print(f"packable: {dict(cnt)}; blanks/questions: " + str({st: sum(len(c['keys']) for c in cs if c['st'] == st) for st in cnt}))
    print(f"packs: {-(-len(cl) // PER)} blind_N ({len(cl)} passages), {-(-len(vc) // PER)} vc_N ({len(vc)} passages) -> {OUT}")
    for (st, w), n in why.most_common():
        print(f"  not packed: {n:3d}  {st}  {w}")


# ---- 3. settle ----------------------------------------------------------------------------------------------------------

def norm(w):
    return str(w if w is not None else "").strip().lower().strip(" .,'\"")


def settle_blank(key, a1, a2):
    """(settled?, reason) for one blank. key: list of accepted words, or an int index, or None; a1, a2: the blind answers."""
    if key is None or key == []:
        return False, "no key"
    if a1 is None or a2 is None:
        return False, "a blind answer is missing"
    ok = (lambda a: norm(a) in {norm(k) for k in key}) if isinstance(key, list) else (lambda a: str(a).strip() == str(key))
    m1, m2 = ok(a1), ok(a2)
    if m1 and m2:
        return True, "key + both"
    if m1 or m2:
        return True, "key + one"
    same = (norm(a1) == norm(a2)) if isinstance(key, list) else (str(a1).strip() == str(a2).strip())
    return False, "both blind answers agree against the key" if same else "blind answers differ from each other and from the key"


def _answers(pattern):
    out = collections.defaultdict(dict)
    for f in sorted(glob.glob(str(OUT / pattern))):
        for r in jl(f):
            out[r["sec"]] = {str(k): v for k, v in (r.get("answers") or {}).items()}
    return out


JUDGEABLE = ("both blind answers agree against the key", "blind answers differ from each other and from the key")


def evaluate(check=True):
    """[(candidate, {n: (settled?, reason)} or None, status)]; status is "complete" (every blank settled by key + blind),
    "judgeable" (every unsettled blank is one of JUDGEABLE: the key and both answers are there, they just disagree) or a
    "held: ..." reason."""
    cs, _ = plan()
    fps = _load_fp(FP)
    if check and fps is None and _answered("blind"):
        sys.exit(f"{OUT / FP} is missing but blind answers exist: run `passage3.py stamp` once (only if the packs came from this plan), or re-pack")
    ans = {"cl": (_answers("blind_out_*.jsonl"), _answers("blind_out2_*.jsonl")),
           "vc": (_answers("vc_out_*.jsonl"), _answers("vc_out2_*.jsonl"))}
    out = []
    for c in cs:
        a, b = ans["vc" if c["st"] == "eng-vocab-cloze" else "cl"]
        s = c["p"]["sec"]
        if s not in a or s not in b:
            out.append((c, None, "held: no blind output from both answerers yet"))
            continue
        bad_fp = stale_why(c, fps) if check else ""
        if bad_fp:
            out.append((c, None, "held: " + bad_fp))
            continue
        res = {n: settle_blank(c["keys"][n], a[s].get(str(n)), b[s].get(str(n))) for n in sorted(c["keys"])}
        bad = [r for ok, r in res.values() if not ok]
        out.append((c, res, "complete" if not bad else "judgeable" if all(r in JUDGEABLE for r in bad) else "held: a blank unsettled"))
    return out


def blind_of(c, n):
    a, b = (("vc_out_*.jsonl", "vc_out2_*.jsonl") if c["st"] == "eng-vocab-cloze" else ("blind_out_*.jsonl", "blind_out2_*.jsonl"))
    s = c["p"]["sec"]
    return [_answers(a)[s].get(str(n)), _answers(b)[s].get(str(n))]


def judge_pack():
    """One line per judgeable passage -> passage3/judge_1.jsonl:
    {"sec", "st", "box", "passage", "blanks": [{"n", "key": [accepted words] (Vocabulary: [the key option]), "blind": [a1, a2]
    (Vocabulary: the two chosen option texts), "options": [...] (Vocabulary only), "why_held"}]}"""
    import load_pp
    lines, jnew = [], {}
    for c, res, status in evaluate():
        if status != "judgeable":
            continue
        jnew[c["p"]["sec"]] = judge_fingerprint(c, res)
        vc = c["st"] == "eng-vocab-cloze"
        bl = []
        for n, (ok, why) in res.items():
            if ok:
                continue
            blind = blind_of(c, n)
            if vc:
                opts = load_pp.strip_opts(c["qs"][n]["options"])
                pick = lambda i: opts[int(i)] if str(i).strip().isdigit() and int(i) < len(opts) else None
                bl.append({"n": n, "key": [opts[c["keys"][n]]], "blind": [pick(x) for x in blind], "options": opts, "why_held": why})
            else:
                bl.append({"n": n, "key": c["keys"][n], "blind": blind, "why_held": why})
        lines.append({"sec": c["p"]["sec"], "st": c["st"], "box": c["box"],
                      "passage": c["p"]["passage"] if vc else P.cloze_stem(c["p"]["passage"], -1), "blanks": bl})
    (OUT / "judge_1.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in lines))
    stale = write_fp(JFP, jnew, "judge")
    if stale:
        print(f"WARNING {len(stale)} passages changed since they were judged (settle refuses them): remove their rows from "
              f"judge_out_*.jsonl, then judge-pack again: {stale}")
    print(f"{len(lines)} passages, {sum(len(x['blanks']) for x in lines)} blanks to judge "
          f"({dict(collections.Counter(x['st'] for x in lines))}) -> {OUT / 'judge_1.jsonl'}")


def judged_answers():
    """{(sec, n): the judge's line} from judge_out_*.jsonl (a later line wins)."""
    out = {}
    for f in sorted(glob.glob(str(OUT / "judge_out_*.jsonl"))):
        for r in jl(f):
            try:
                out[(r["sec"], int(r["n"]))] = r
            except (KeyError, TypeError, ValueError):
                pass
    return out


def build_rows(c, res):
    import load_pp
    p, st, rows = c["p"], c["st"], []
    tags = _tags()
    for n in sorted(c["keys"]):
        q = c["qs"][n]
        d = (tags.get(q["id"]) or {}).get("difficulty")
        lvl = load_pp.LEVEL.get(d if isinstance(d, int) else 2, "intermediate")
        tag = res[n][1]
        base = {"id": load_pp.pp_id(q["id"]), "src_id": q["id"], "subject": "english", "subtopic": st, "level": lvl,
                "difficulty": d, "crops": [], "year": p["year"], "school": q.get("school"), "paper": q.get("paper"),
                "qno": n, "marks": q.get("marks"), "grp": c["grp"], "seq": n, "sec": p["sec"]}
        if st == "eng-vocab-cloze":
            opts = load_pp.strip_opts(q["options"])
            rows.append(dict(base, pattern="eng-pat-vocab-passage-mcq", stem=f"{p['passage']}\n\n{load_pp.VC_STEM.format(n=n)}",
                             options=opts, answer=c["keys"][n], pages=q.get("pages"), pages_dir=None, answer_src="key",
                             part=q.get("part"), blind_src=f"passage3: {tag}", repeat=1))
        else:
            rows.append(dict(base, pattern=None, stem=P.cloze_stem(p["passage"], n, c["box"]), options=[], answer=0,
                             blind_src=f"passage3: {tag}", kind="typed", accept=c["keys"][n], scaffold=None))
    return rows


def check_rows(rows):
    owner = {}
    for r in rows:
        assert owner.setdefault(r["grp"], r["sec"]) == r["sec"], f"set {r['grp']} holds two passages"
    assert len({r["id"] for r in rows}) == len(rows), "a row id repeats"
    asked = collections.defaultdict(set)
    for r in rows:
        asked[r["grp"]].add(r["seq"])
    for r in rows:
        shown = {int(n) for n in re.findall(r"\((\d+)\) _{4,8}", r["stem"])}
        assert shown <= asked[r["grp"]], f"{r['id']}: blanks {sorted(shown - asked[r['grp']])} shown but not asked"


def write_sel(rows, folder):
    out = OUT / folder / "english"
    out.mkdir(parents=True, exist_ok=True)
    (out / "selected.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    return out


def settle():
    """ship/: complete by key + both blind answers. ship_judged/: complete only because the judge (judge_out_N.jsonl) said
    key_fits true on every blank the blind answers left open; the key alone is the accepted answer. also_right.jsonl lists
    the blind words the judge found also correct (not added)."""
    rows, jrows, why, blanks = [], [], collections.Counter(), collections.Counter()
    ja, also = judged_answers(), []
    hold = {h["sec"]: h["reason"] for h in jl(OUT / "hold.jsonl")}  # {"sec", "reason"}: neither ship/ nor ship_judged/
    for c, res, status in evaluate():
        st, s = c["st"], c["p"]["sec"]
        if s in hold:
            why[(st, f"held by hold.jsonl: {hold[s]}")] += 1
            continue
        if res:
            for ok, r in res.values():
                blanks[(st, r)] += 1
        if status == "complete":
            why[(st, "complete")] += 1
            rows += build_rows(c, res)
            continue
        if status != "judgeable":
            why[(st, status)] += 1
            continue
        open_ = [n for n, (ok, _) in res.items() if not ok]
        jfps = _load_fp(JFP)
        if jfps is None and any(k[0] == s for k in ja):
            sys.exit(f"{OUT / JFP} is missing but judge verdicts exist: run `passage3.py stamp` once, or run judge-pack again")
        if any(k[0] == s for k in ja) and stale_why(c, jfps, fp=judge_fingerprint(c, res)):
            why[(st, "held: judge verdict is for other text or answers: re-run judge-pack")] += 1
            continue
        js = {n: ja.get((s, n)) for n in open_}
        for n, j in js.items():
            if j and j.get("blind_also_right"):
                also.append({"sec": s, "n": n, "st": st, "key": c["keys"][n], "blind_also_right": j["blind_also_right"],
                             "why": j.get("why"), "shipped": False})
        if any(j is None for j in js.values()):
            why[(st, "held: not judged yet")] += 1
        elif all(j.get("key_fits") is True for j in js.values()):
            why[(st, "complete by the judge")] += 1
            res2 = {n: (True, "judge: key fits") if n in js else v for n, v in res.items()}
            jrows += build_rows(c, res2)
            for x in also:
                if x["sec"] == s:
                    x["shipped"] = True
        else:
            why[(st, "held: the judge doubts the key")] += 1
    check_rows(rows)
    check_rows(jrows)
    assert not ({r["grp"] for r in rows} & {r["grp"] for r in jrows}) and not ({r["id"] for r in rows} & {r["id"] for r in jrows})
    out = write_sel(rows, "ship")
    if jrows or glob.glob(str(OUT / "judge_out_*.jsonl")):
        write_sel(jrows, "ship_judged")
    (OUT / "also_right.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in also))
    print("passages: " + ", ".join(f"{s} {w} {n}" for (s, w), n in sorted(why.items())))
    print("blanks: " + ", ".join(f"{s} {w} {n}" for (s, w), n in sorted(blanks.items())))
    print(f"ship: {len(rows)} rows in {len({r['grp'] for r in rows})} passages -> {out}")
    print(f"ship_judged: {len(jrows)} rows in {len({r['grp'] for r in jrows})} passages -> {OUT / 'ship_judged' / 'english'}; "
          f"{len(also)} blanks with blind words also right -> {OUT / 'also_right.jsonl'}")


# ---- explanations: cloze_explain.py (Grammar/Comprehension) and section_explain.py vocab-cloze, pointed at passage3 folders

EX = OUT / "explain"
TARGETS = ("ship", "ship_judged")


def _targets():
    for t in TARGETS:
        f = OUT / t / "english" / "selected.jsonl"
        rs = jl(f)
        if rs:
            yield t, rs


def _ce(t):
    """cloze_explain pointed at passage3/explain/<t>/cloze (its WORK) and a copy of the typed rows only (its SHIP: it reads
    every row of its selection as a cloze, vocabulary rows would be mislabelled)."""
    import cloze_explain as CE
    sel = EX / t / "cloze_sel" / "english"
    sel.mkdir(parents=True, exist_ok=True)
    rows = [r for r in jl(OUT / t / "english" / "selected.jsonl") if r.get("kind") == "typed"]
    (sel / "selected.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    CE.WORK, CE.SHIP = EX / t / "cloze", sel
    CE.WORK.mkdir(parents=True, exist_ok=True)
    return CE, rows


def _vc(t, cmd):
    """section_explain.py <cmd> vocab-cloze with SECEXP_WORK / SECEXP_SEL (its own switches for runs on copies)."""
    import os
    import subprocess
    if not any(r.get("subtopic") == "eng-vocab-cloze" for r in jl(OUT / t / "english" / "selected.jsonl")):
        return
    env = dict(os.environ, SECEXP_WORK=str(EX / t / "vc"), SECEXP_SEL=str(OUT / t / "english"))
    r = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "section_explain.py"), *cmd, "vocab-cloze"],
                       env=env, capture_output=True, text=True)
    print(f"[{t} vocab-cloze {cmd[0]}] " + (r.stdout.strip() or r.stderr.strip()).replace("\n", "\n    "))


def explain_pack():
    n = 0
    for t, rs in _targets():
        CE, cl = _ce(t)
        if cl:
            print(f"[{t} cloze]", end=" ")
            CE.cmd_pack()
        _vc(t, ["pack"])
        n += 1
    if not n:
        print("no ship/ or ship_judged/ rows yet: run settle first")


def explain_checkpack(tag=None):
    for t, rs in _targets():
        CE, cl = _ce(t)
        if cl:
            # cloze_explain's untagged checkpack rewrites cpack_0..9 (emptying them once checked, which loses every verdict's
            # tie to its text): always a new tagged pack, cpack_<tag>.jsonl, never an existing one
            k = 1
            while not tag and (CE.WORK / f"cpack_r{k}.jsonl").exists():
                k += 1
            name = tag or f"r{k}"
            print(f"[{t} cloze]", end=" ")
            CE.cmd_checkpack(name)
            f = CE.WORK / f"cpack_{name}.jsonl"
            if f.exists() and not f.read_text().strip():
                f.unlink()
        _vc(t, ["checkpack"])


def explain_apply():
    """-> <ship>/english/explain.jsonl for ship/ and ship_judged/: lint-clean AND checker ok AND the verdict tied to the exact
    text, key and passage (both reused scripts' own rule). Vocabulary lines come from section_explain apply, the cloze
    lines from cloze_explain apply are merged in by id."""
    for t, rs in _targets():
        _vc(t, ["apply"])
        CE, cl = _ce(t)
        if cl:
            print(f"[{t} cloze]", end=" ")
            CE.cmd_apply()
            new = jl(CE.SHIP / "explain.jsonl")
            path = OUT / t / "english" / "explain.jsonl"
            keep = [x for x in jl(path) if x["id"] not in {y["id"] for y in new}]
            path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in keep + new))
            print(f"  {path}: {len(keep) + len(new)} lines")


# ---- 4. selftest --------------------------------------------------------------------------------------------------------

def selftest():
    # settling
    assert settle_blank(["the"], "The", "the") == (True, "key + both")
    assert settle_blank(["make", "produce"], "produce", "build") == (True, "key + one")
    assert settle_blank(["the"], "an", "an") == (False, "both blind answers agree against the key")
    assert settle_blank(["the"], "an", "a")[0] is False and settle_blank(None, "a", "a") == (False, "no key")
    assert settle_blank([], "a", "a")[1] == "no key" and settle_blank(["the"], None, "the")[1] == "a blind answer is missing"
    assert settle_blank(2, 2, 1) == (True, "key + one") and settle_blank(2, 0, 0)[0] is False and settle_blank(0, 0, 0) == (True, "key + both")
    assert settle_blank(["on"], "on.", " On ") == (True, "key + both"), "case, spaces and a stop do not matter"
    # two-of-three agreement, through passage.judge exactly as agree3 uses it
    sec = {"kind": "blank", "qnos": [31, 32], "st": "eng-comp-cloze"}
    t = "Bees fly to a [[31]] and bring [[32]] home."
    raw = lambda x: json.dumps({"passage": x})
    assert P.judge(sec, raw(t), raw(t.replace("[[32]]", "[[33]]")))[1] == "the second read's markers differ"
    assert P.judge(sec, raw(t), raw(t.replace("Bees", "Wasps").replace("bring", "carry")))[1] == "the two reads' text differs"
    assert P.judge(sec, raw(t), raw(t + " "))[0] == t, "the first of the pair is the text kept"
    # packs never show a key: the text only has open blanks; the word box rides along
    s = P.cloze_stem("Bees fly to a [[31]] and bring [[32]] home.", -1)
    assert s == "Bees fly to a (31) ____ and bring (32) ____ home." and "________" not in s
    # set id rename: a used id gets -2, then -3
    import load_pp
    q = {"id": "eng-2099-001-x-q31", "paper": "eng-2099-001", "part": "Booklet B"}
    g = load_pp.set_id(q, "cc")
    cands = [{"st": "eng-comp-cloze", "p": {"sec": "s1"}, "qs": {31: q}}, {"st": "eng-comp-cloze", "p": {"sec": "s2"}, "qs": {31: q}},
             {"st": "eng-comp-cloze", "p": {"sec": "s1"}, "qs": {31: q}}]
    assign_grps(cands, {g, f"{g}-2"}, set(), {})  # the real code plan() calls
    assert [c["grp"] for c in cands] == [f"{g}-3", f"{g}-4", f"{g}-3"], "used ids skipped; a second section never shares; the same section keeps its id"
    try:
        assign_grps([cands[0]], set(), {load_pp.pp_id(q["id"])}, {})
        raise SystemExit("a live row id must fail")
    except AssertionError:
        pass
    # fingerprints: text, box and key change the stamp; a stale or missing stamp is refused
    cf = {"st": "eng-grammar-cloze", "p": {"sec": "s", "passage": "A [[1]] b."}, "box": ["on", "in"], "keys": {1: ["on"]}, "qs": {}}
    f0 = fingerprint(cf)
    assert f0 == fingerprint(dict(cf)) and len({f0, fingerprint(dict(cf, box=["on", "at"])), fingerprint(dict(cf, keys={1: ["in"]})),
                                                 fingerprint(dict(cf, p={"sec": "s", "passage": "A [[1]] c."}))}) == 4
    assert stale_why(cf, {"s": f0}) == "" and "another text" in stale_why(cf, {"s": "x"}) and "no pack stamp" in stale_why(cf, {})
    assert "no pack stamp" in stale_why(cf, None) and stale_why(cf, {"s": "j"}, fp="j") == ""
    # evaluate/judge rules on made-up blanks
    assert all(r in JUDGEABLE for r in ("both blind answers agree against the key",
                                        "blind answers differ from each other and from the key"))
    assert "no key" not in JUDGEABLE and "a blind answer is missing" not in JUDGEABLE
    j = {("s", 3): {"key_fits": True}, ("s", 4): {"key_fits": "unsure"}}
    assert j[("s", 3)].get("key_fits") is True and j[("s", 4)].get("key_fits") is not True, "only true counts"
    c = {"st": "eng-comp-cloze", "keys": {1: ["on"], 2: ["in"]}, "grp": "g", "p": {"sec": "s", "year": 2099, "passage": "A [[1]] b [[2]]."},
         "box": None, "qs": {1: {"id": "q1", "school": "X", "paper": "p", "marks": 1}, 2: {"id": "q2", "school": "X", "paper": "p", "marks": 1}}}
    rs = build_rows(c, {1: (True, "judge: key fits"), 2: (True, "key + one")})
    assert [r["accept"] for r in rs] == [["on"], ["in"]] and rs[0]["stem"] == "A (1) ________ b (2) ____." and rs[0]["blind_src"].endswith("judge: key fits")
    check_rows(rs)
    # the explanation packs: cloze_explain's shape from a typed row, and its lint rule is the one apply uses
    import cloze_explain as CE
    ps = CE.passages({r["id"]: r for r in rs})
    assert ps[0]["blanks"] == [{"id": rs[0]["id"], "n": 1, "accept": ["on"]}, {"id": rs[1]["id"], "n": 2, "accept": ["in"]}]
    assert CE.lint_one(rs[0], "'On' goes with the day.") == "" and CE.lint_one(rs[0], "It fits here.") == "does not name the answer"
    import tempfile
    global OUT
    keep = OUT
    with tempfile.TemporaryDirectory() as d:  # a re-pack never refreshes the stamp of a section that already has answers
        OUT = Path(d)
        try:
            assert write_fp(FP, {"a": "1", "b": "2"}, "blind") == [] and write_fp(FP, {"a": "9"}, "blind") == []
            (OUT / "blind_out_1.jsonl").write_text(json.dumps({"sec": "a", "answers": {}}) + "\n")
            assert write_fp(FP, {"a": "5", "b": "7"}, "blind") == ["a"] and _load_fp(FP) == {"a": "9", "b": "7"}
        finally:
            OUT = keep
    print("passage3 selftest ok")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "explain-checkpack":
        explain_checkpack(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        {"agree3": agree3, "pack": pack, "settle": settle, "judge-pack": judge_pack, "explain-pack": explain_pack,
         "explain-apply": explain_apply, "stamp": stamp, "selftest": selftest}.get(cmd, lambda: sys.exit(__doc__))()
