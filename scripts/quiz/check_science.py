"""Validate the Science item files and the compiled banks; exits non-zero on any failure.

    python3 scripts/quiz/check_science.py            # review warnings are printed but do not fail
    python3 scripts/quiz/check_science.py --strict   # review warnings count as failures

Figures: an item's "figure" is an inline SVG string (code-made, currentColor, no scripts or external references)
or line art {"img": "/science/<file>.webp", "alt", "labels": [{"x", "y", "text"}]} whose file must exist under site/public/.

Review warnings (WARN section, helpers in bankcommon.py): figure text naming the answer, stem echo, near-duplicate
options, the correct option strictly longest in over 35% of a sub-topic, and a figure that names none of the stem's words.
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from bankcommon import (unstated_switch, unqualified_stays_lit, Warnings, gives_away, near_duplicates, correct_is_longest, figure_text, figure_mismatch,  # noqa: E402
                        longest_share_warnings, warning_self_tests, NEAR_DUP, svg_text_overflows)
STRICT = "--strict" in sys.argv[1:]
ROOT = HERE.parents[1]
SYL = json.loads((ROOT / "site" / "src" / "data" / "syllabus" / "science.json").read_text())
OUTCOMES = {o["id"] for st in SYL["strands"] for t in st["topics"] for sb in t["subtopics"] for o in sb["outcomes"]}
SUBS = {sb["id"] for st in SYL["strands"] for t in st["topics"] for sb in t["subtopics"]}
PAT_FILE = HERE / "science" / "patterns.json"
# the pattern catalogue is written separately; until it exists only "a non-empty string" is required
PATTERNS = {p["id"] for p in json.loads(PAT_FILE.read_text())["patterns"]} if PAT_FILE.exists() else None
LEVELS = {"basic", "intermediate", "competent"}
IMG = re.compile(r"^/science/[\w.-]+\.webp$")
OK_PAINT = {"currentcolor", "none", "transparent", "white", "black", "#fff", "#ffffff", "#000", "#000000"}
BAD_TAGS = {"script", "foreignobject", "iframe", "object", "embed", "image", "use", "a", "animate", "set", "audio", "video"}
PAINT_ATTRS = {"fill", "stroke", "color", "stop-color", "flood-color", "lighting-color"}
MAX_SVG = 30_000
errors = []
SELF_TESTS = [  # (svg, must fail?)
    ("<svg viewBox='0 0 100 40'><rect x='0' y='0' width='50' height='30'/><text x='25' y='20' text-anchor='middle' font-size='14'>Hours of light a day</text></svg>", True),
    ("<svg viewBox='0 0 100 40'><rect x='0' y='0' width='90' height='30'/><text x='45' y='20' text-anchor='middle' font-size='14'>Hours</text></svg>", False),
    ("<svg viewBox='0 0 1 1'><path d='M0 0' fill='currentColor' style='stroke:black'/></svg>", False),
    ("<svg viewBox='0 0 1 1'><path d='M0 0' style='color:red'/></svg>", True),
    ("<svg viewBox='0 0 1 1'><stop stop-color='#f00'/></svg>", True),
    ("<svg viewBox='0 0 1 1'><style>path{fill:#f00}</style><path d='M0 0'/></svg>", True),
]


def svg_errors(s):
    """An inline SVG must be one well-formed <svg> with a viewBox, black/white or currentColor paint, nothing active or external."""
    if not isinstance(s, str) or not s.strip(): return ["svg figure is empty"]
    if len(s) > MAX_SVG: return [f"svg figure is {len(s)} chars (limit {MAX_SVG})"]
    if re.search(r"<!(DOCTYPE|ENTITY)|<\?", s, re.I): return ["svg figure has a DOCTYPE, ENTITY or processing instruction"]
    try:
        root = ET.fromstring(s)
    except ET.ParseError as ex:
        return [f"svg figure is not well-formed: {ex}"]
    out = []
    if root.tag not in ("svg", "{http://www.w3.org/2000/svg}svg"): out.append(f"svg figure root is <{root.tag}>")
    if not root.get("viewBox"): out.append("svg figure has no viewBox")
    for el in root.iter():
        tag = el.tag.split("}")[-1].lower()
        if tag in BAD_TAGS: out.append(f"svg figure has a <{tag}> element")
        if tag == "style": out.append("svg figure has a <style> element (set paint with fill/stroke attributes)")
        for k, v in el.attrib.items():
            name = k.split("}")[-1].lower()
            if name.startswith("on"): out.append(f"svg figure has an {name} handler")
            if name == "href" or k.startswith("{"):
                if not (name == "href" and v.startswith("#")): out.append(f"svg figure has external attribute {name}")
            if re.search(r"javascript:|data:|https?:|//", v, re.I): out.append(f"svg attribute {name} has a URL or script")
            if re.search(r"url\((?!\s*['\"]?#)", v, re.I): out.append(f"svg attribute {name} has a non-local url()")
            if name in PAINT_ATTRS and v.strip().lower() not in OK_PAINT and not v.strip().lower().startswith("url(#"):
                out.append(f"svg {name}={v!r}: use currentColor (black and white only)")
            if name == "style":
                for prop, val in re.findall(r"([\w-]+)\s*:\s*([^;]+)", v):
                    val = val.strip().lower()
                    if prop.lower() in PAINT_ATTRS and val not in OK_PAINT and not val.startswith("url(#"):
                        out.append(f"svg style sets {prop.lower()}:{val} (use currentColor, black and white only)")
    out += [f"figure-text-overflow: {t!r}: {why}" for t, why in svg_text_overflows(s)]  # wrap or widen the cell (fillkit.table does)
    return sorted(set(out))


def figure_errors(fig, answer_text=None, options=()):
    if isinstance(fig, str): return svg_errors(fig)
    if not isinstance(fig, dict): return ["figure is neither an svg string nor a line-art object"]
    out = []
    extra = set(fig) - {"img", "alt", "labels"}
    if extra: out.append(f"figure has unknown fields {sorted(extra)}")
    img = fig.get("img")
    if not isinstance(img, str) or not IMG.match(img): out.append(f"figure img {img!r} must look like /science/<file>.webp")
    elif not (ROOT / "site" / "public" / img.lstrip("/")).is_file(): out.append(f"figure image site/public{img} does not exist")
    if not isinstance(fig.get("alt"), str) or not fig["alt"].strip(): out.append("figure needs a non-empty alt")
    label_texts = {str(lb.get("text", "")).strip().lower() for lb in fig.get("labels") or [] if isinstance(lb, dict)}
    other_opts = {str(o).strip().lower() for o in options} - {str(answer_text or "").strip().lower()}
    labels = fig.get("labels", [])
    if not isinstance(labels, list): return out + ["figure labels must be a list"]
    for lb in labels:
        if not isinstance(lb, dict) or set(lb) != {"x", "y", "text"}: out.append("figure label must be exactly {x, y, text}"); continue
        for ax in ("x", "y"):
            if isinstance(lb[ax], bool) or not isinstance(lb[ax], (int, float)) or not 0 <= lb[ax] <= 100:
                out.append(f"figure label {ax} must be a number from 0 to 100")
        t = lb["text"]
        if not isinstance(t, str) or not t.strip() or len(t) > 40: out.append("figure label text must be 1-40 characters")
        elif re.search(r"<[A-Za-z/!]|&[#A-Za-z0-9]+;", t): out.append(f"figure label {t!r} must be plain text (no HTML or entities)")
        elif answer_text and t.strip().lower() == answer_text.strip().lower() and not (other_opts & label_texts):
            # a label equal to the answer gives it away only when no OTHER option is also a label
            # (letter questions label every choice A-D on the picture, which reveals nothing)
            out.append(f"figure label {t!r} gives away the answer")
    return out


# keys and stems must be unique per SUB-TOPIC across files (several files can share one sub-topic; the
# review verdict, shuffle seed and question id (build.py qid) are all keyed by sub-topic|key, never topic|key)
_all = [(f, json.loads(f.read_text())) for f in sorted((HERE / "science" / "items").glob("*.json"))]
sub_keys = Counter((d.get("subtopic"), it.get("key")) for _, d in _all for it in d["items"])
sub_stems = Counter((d.get("subtopic"), it.get("stem")) for _, d in _all for it in d["items"])
warn = Warnings({
    "figure-leak": "figure alt/labels/text contain every distinctive word of the correct option, and of no other option",
    "stem-echo": "stem contains every distinctive word of the correct option, and of no other option",
    "near-dup-options": f"two options at least {NEAR_DUP:.0%} alike after normalising (labels and short options skipped)",
    "longest-correct": "sub-topics where the correct option is strictly the longest in over 35% of items",
    "refers-to-other-item": "stem starts 'In/Using the same ...' (every item must stand alone, with its own figure or data)",
    "stays-lit-unqualified": "key is a bare 'It stays lit' next to a brighter/dimmer option (say 'at the same brightness')",
    "figure-mismatch": "figure text names none of the stem's content words",
})
longest = {}

for f, data in _all:
    sub = data.get("subtopic")
    if sub not in SUBS:
        errors.append(f"{f.name}: unknown subtopic {sub}")
    for it in data["items"]:
        e = lambda m: errors.append(f"{f.name} {it.get('key')}: {m}")
        if not str(it.get("key", "")).strip(): e("missing key")
        if sub_keys[(sub, it.get("key"))] > 1: e("duplicate key in this sub-topic")
        if sub_stems[(sub, it.get("stem"))] > 1: e("duplicate stem in this sub-topic")
        if it.get("level") not in LEVELS: e(f"bad level {it.get('level')}")
        oc = str(it.get("outcome", ""))
        if oc not in OUTCOMES or re.sub(r"-\d+$", "", oc) != sub: e(f"bad outcome {it.get('outcome')}")
        pat = it.get("pattern")
        if not isinstance(pat, str) or not pat.strip() or (PATTERNS is not None and pat not in PATTERNS): e(f"unknown pattern {pat}")
        stem = str(it.get("stem", ""))
        opts = it.get("options", [])
        if not stem.strip(): e("empty stem")
        elif not re.search(r"_{3,}", stem) and "?" not in stem: e("stem has no blank (____) and asks no question")
        if len(opts) != 4 or any(not isinstance(o, str) or not o.strip() for o in opts) or len(set(opts)) != 4:
            e(f"options not 4 distinct non-empty strings: {opts}")
        elif len({o.strip().lower() for o in opts}) != 4: e(f"options differ only by case: {opts}")
        a = it.get("answer")
        ex = it.get("explain", [])
        if not isinstance(a, int) or isinstance(a, bool) or not 0 <= a < 4: e("answer out of range")
        elif len(ex) != 4 or ex[a] is not None or any(not (x and x.get("tag") and x.get("why")) for i, x in enumerate(ex) if i != a):
            e("explain must be null for the answer and {tag, why} for each wrong option")
        if not it.get("solution"): e("missing solution")
        # a bare string is shown one letter per step (list("...") in build.py): 76 live items did this until 20 Nov 2026
        elif not (isinstance(it["solution"], list) and all(isinstance(x, str) and x.strip() for x in it["solution"])):
            e("solution must be a list of non-empty strings (one step each)")
        if "figure" in it:
            ans = opts[a] if isinstance(a, int) and not isinstance(a, bool) and 0 <= a < len(opts) and isinstance(opts[a], str) else None
            for msg in figure_errors(it["figure"], ans, opts if isinstance(opts, list) else ()): e(msg)
            if unstated_switch(stem, it["figure"]): e("figure-unstated-switch: the figure draws a switch S but the stem never says if it is closed or open")
        if isinstance(opts, list) and len(opts) == 4 and all(isinstance(o, str) for o in opts) \
                and isinstance(a, int) and not isinstance(a, bool) and 0 <= a < 4:
            w = lambda rule, m: warn.add(rule, f"{f.name} {it.get('key')}: {m}")
            if "figure" in it and gives_away(figure_text(it["figure"]), opts, a): w("figure-leak", f"answer {opts[a]!r}")
            if gives_away(stem, opts, a): w("stem-echo", f"answer {opts[a]!r}")
            if re.match(r"\s*(in|using|from|for) the same\b", stem, re.I): w("refers-to-other-item", f"stem {stem[:50]!r}")
            if unqualified_stays_lit(opts, a): w("stays-lit-unqualified", f"answer {opts[a]!r}")
            for x, y in near_duplicates(opts): w("near-dup-options", f"{x!r} ~ {y!r}")
            if "figure" in it and figure_mismatch(stem, it["figure"]):
                w("figure-mismatch", f"figure text {figure_text(it['figure'])[:60]!r}")
            longest.setdefault(sub, []).append(correct_is_longest(opts, a))
for m in longest_share_warnings(longest): warn.add("longest-correct", m)

# compiled banks: unique ids, 4-option shape, figure schema
ids = Counter()
for f in sorted((ROOT / "site" / "src" / "data" / "quiz" / "science").glob("*.json")):
    for q in json.loads(f.read_text())["questions"]:
        ids[q["id"]] += 1
        if len(q["options"]) != 4 or not 0 <= q["answer"] < 4 or q["explain"][q["answer"]] is not None:
            errors.append(f"{f.name} {q['id']}: bad compiled shape")
        if "figure" in q:
            errors += [f"{f.name} {q['id']}: {m}" for m in figure_errors(q["figure"], q["options"][q["answer"]], q["options"])]
errors += [f"duplicate question id {i}" for i, n in ids.items() if n > 1]

for svg, must_fail in SELF_TESTS:
    if bool(svg_errors(svg)) != must_fail: errors.append(f"svg rule self-test failed for {svg}")
errors += warning_self_tests(science=True)

print(f"checked {len(_all)} item files, {sum(ids.values())} shipped questions")
warn.report()
if STRICT: errors += [f"[{r}] {m}" for r, ms in warn.hits.items() for m in ms]
for m in errors[:40]:
    print("FAIL", m)
print(f"{len(errors)} failures")
sys.exit(1 if errors else 0)
