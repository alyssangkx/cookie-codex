"""Explanations for the typed cloze blanks (owner, 24 Nov 2026: "can there be a review for answers got wrong in comprehension
cloze, it currently says Why? with no explanation"; option A: Claude writes, a second Claude pass checks).

  cloze_explain.py pack                   packs of ~10 passages -> WORK/pack_N.jsonl (writers fill out_N.jsonl)
  cloze_explain.py lint                   rule checks on the written ones (count, length, names the answer, no '!')
  cloze_explain.py checkpack              lint-clean ones + their passage -> WORK/cpack_N.jsonl (checkers fill check_N.jsonl)
  cloze_explain.py recheck TAG            the ones without a verdict that still holds -> WORK/cpack_TAG.jsonl (-> check_TAG)
  cloze_explain.py apply                  lint-clean AND checker-passed -> <ship>/english/explain.jsonl (load_pp upload reads it)

An explanation is used only for the question version it was written for (explain.fp: stem, key and accepted answers).
"""
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from explain import fp  # noqa: E402

WORK = Path("/data/alvin/tmp/cookie-codex/clozeexp")
SHIP = Path("/data/alvin/tmp/cookie-codex/ppimport/engcloze-ship/english")
N = 10
MAX = 300


def jl(p):
    return [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()] if Path(p).exists() else []


def rows():
    return {r["id"]: r for r in jl(SHIP / "selected.jsonl")}


def passages(rs):
    by = collections.defaultdict(list)
    for r in rs.values():
        by[r["grp"]].append(r)
    out = []
    for g, ps in sorted(by.items()):
        ps.sort(key=lambda r: r["seq"])
        out.append({"grp": g, "section": "Grammar Cloze" if ps[0]["subtopic"] == "eng-grammar-cloze" else "Comprehension Cloze",
                    "passage": re.sub(r"\((\d+)\) _{4,}", r"(\1) ____", ps[0]["stem"]),
                    "blanks": [{"id": r["id"], "n": r["seq"], "accept": r["accept"]} for r in ps]})
    return out


def norm(stem):
    return re.sub(r"\((\d+)\) _{4,}", r"(\1) ____", stem)


def written():
    """The writers' texts; out_fix*.jsonl (rewrites after a failed check or a changed key, in name order) override them."""
    w = {x["id"]: x["right"].strip() for k in range(N) for x in jl(WORK / f"out_{k}.jsonl") if isinstance(x.get("right"), str)}
    for f in sorted(WORK.glob("out_fix*.jsonl")):
        w |= {x["id"]: x["right"].strip() for x in jl(f)}
    return w


def verdicts(rs, w):
    """The checker verdict for each id that still holds: a verdict counts only while the explanation text, the accepted
    answers and the passage are exactly what its checker was given (cpack_X.jsonl beside check_X.jsonl); the newest wins."""
    v = {}
    for cp in sorted(WORK.glob("cpack_*.jsonl"), key=lambda f: f.stat().st_mtime):
        seen = {b["id"]: (b["explanation"], b["accept"], p["passage"]) for p in jl(cp) for b in p["blanks"]}
        for x in jl(WORK / cp.name.replace("cpack_", "check_")):
            i, r = x["id"], rs.get(x["id"])
            if r and seen.get(i) == (w.get(i), r["accept"], norm(r["stem"])):
                v[i] = x
    return v


def spans(text):
    """The quoted stretches of a text; an apostrophe inside a word (don't, children's) is not a quote mark."""
    return re.findall(r"(?:(?<=\s)|^|(?<=\())['‘\"“](.+?)['’\"”](?=[\s.,;:)?]|$)", text)


def named(a, text):
    """The answer as a whole word inside a quoted stretch ('every single day' names 'every'; the article a in a sentence
    does not name the answer 'a')."""
    return any(re.search(r"\b" + re.escape(a) + r"\b", s, re.I) for s in spans(text))


def lint_one(r, text):
    """Why an explanation fails the rules, or '' when it passes."""
    if not text:
        return "empty"
    if len(text) > MAX:
        return f"longer than {MAX}"
    if "!" in text or text.lower().startswith("the answer is"):
        return "style"
    if not named(r["accept"][0], text):
        return "does not name the answer"
    if len(r["accept"]) <= 3 and not all(named(a, text) for a in r["accept"][1:]):  # a long list: some named is enough
        return "an accepted answer is not mentioned"
    return ""


def cmd_pack():
    ps = passages(rows())
    WORK.mkdir(parents=True, exist_ok=True)
    for k in range(N):
        with open(WORK / f"pack_{k}.jsonl", "w", encoding="utf-8") as f:
            for p in ps[k::N]:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(len(ps), "passages", sum(len(p["blanks"]) for p in ps), "blanks")


def cmd_lint():
    rs, w = rows(), written()
    why = collections.Counter(lint_one(r, w.get(i, "")) or "ok" for i, r in rs.items())
    print(dict(why))
    return rs, w


def cmd_checkpack(tag=None):
    """Packs for the checkers: every lint-clean explanation without a verdict that still holds (all of them the first time).
    With a tag (recheck), one pack cpack_<tag>.jsonl."""
    rs, w = cmd_lint()
    v = verdicts(rs, w)
    ps = [dict(p, blanks=[dict(b, explanation=w[b["id"]]) for b in p["blanks"]
                          if not lint_one(rs[b["id"]], w.get(b["id"], "")) and b["id"] not in v]) for p in passages(rs)]
    ps = [p for p in ps if p["blanks"]]
    for k, name in ([(0, tag)] if tag else [(k, str(k)) for k in range(N)]):
        with open(WORK / f"cpack_{name}.jsonl", "w", encoding="utf-8") as f:
            for p in (ps if tag else ps[k::N]):
                f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(sum(len(p["blanks"]) for p in ps), "to check")


def cmd_apply():
    rs, w = rows(), written()
    verdict = verdicts(rs, w)
    out, why = [], collections.Counter()
    for i, r in rs.items():
        bad = lint_one(r, w.get(i, ""))
        v = verdict.get(i)
        if bad:
            why["lint: " + bad] += 1
        elif not v:
            why["not checked (or checked for another text, key or passage)"] += 1
        elif v.get("ok") is not True:
            why["checker failed it"] += 1
        else:
            out.append({"id": i, "explain": {"right": w[i], "wrong": []}, "fp": fp(r)})
            why["shipped"] += 1
    with open(SHIP / "explain.jsonl", "w", encoding="utf-8") as f:
        for x in out:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    print(dict(why), "->", SHIP / "explain.jsonl")


def selftest():
    r = {"accept": ["instance", "example"]}
    assert lint_one(r, "'For' needs 'instance' here; 'example' also works.") == ""
    assert lint_one(r, "'For' needs 'instance' here.") == "an accepted answer is not mentioned"
    assert lint_one({"accept": ["a", "b", "c", "d"]}, "'a' fits; 'b' also works.") == "", "a long list: not every one named"
    assert lint_one(r, "Great choice!") == "style"
    assert lint_one(r, "x" * 301 + "instance example") == f"longer than {MAX}"
    assert lint_one({"accept": ["a"]}, "A particular thing takes an article.") == "does not name the answer", "the letter a is not the answer named"
    assert named("in", "Skin 'covered in' scales.") and not named("in", "meaning in context")
    assert named("every", "'Every single day' is a phrase.") and not named("it", "Children's books don't use it.")
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1] == "recheck":
        cmd_checkpack(sys.argv[2])
    else:
        {"pack": cmd_pack, "lint": cmd_lint, "checkpack": cmd_checkpack, "apply": cmd_apply, "selftest": selftest}[sys.argv[1]]()
