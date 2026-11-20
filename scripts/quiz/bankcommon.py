"""Helpers shared by the reviewed-item bank builds (Chinese, English, Science)."""
import difflib
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

# passage sets: vis-NN-K (visual text), read-NN-K (comprehension), ecloze-NN-K (cloze). A set ships whole or not at all.
PASSAGE = re.compile(r"^(vis|read|ecloze)-(\d+)-(\d+)$")


def fingerprint(it):
    """Hash of everything a reviewer judged; an item edited after review no longer matches its verdict."""
    body = json.dumps([it["stem"], it["options"], it["answer"], it["explain"], it["solution"],
                       it.get("gloss"), it.get("level"), it.get("outcome"), it.get("pattern")]
                      + ([it["visual"]] if it.get("visual") else [])  # appended only when present: old fingerprints stay valid
                      + ([it["figure"]] if it.get("figure") else []),  # Science figures: an edited figure needs a fresh review
                      ensure_ascii=False)
    return hashlib.sha1(body.encode()).hexdigest()[:16]


# ------------------------------------------------------------------ review warnings (check_english / check_science)
# Rough flags found in item reviews. Warnings by default (exit code unchanged); --strict turns them into failures.
STOPWORDS = set("""
a an the and or but nor so yet of to in on at by for from with without into onto over under about above below
after before during between through up down out off than then there here this that these those it its is are was were be
been being am do does did done has have had having will would shall should can could may might must not no yes all any
each every some more most less least many much few very too also just only own same such both either neither which what
who whom whose when where why how if as because while until unless though although he she they we you i me him her them
us my your his their our one two three four five six seven eight nine ten first second third other another
""".split())
WARN_LIMIT = 10  # examples printed per rule
NEAR_DUP = 0.95  # normalised option similarity at or above which two options look like near-duplicates
NEAR_DUP_MIN_LEN = 12  # shorter options (one-word grammar contrasts such as leave/leaves) are not compared
LABEL = re.compile(r"^([a-z]|[ivx]+|\d+([.,]\d+)?)$")  # P, Q, II, 20: options that differ only in these are deliberate
LONGEST_SHARE = 0.35  # warn when more than this share of a sub-topic's correct options are strictly the longest
LONGEST_MIN_ITEMS = 8  # sub-topics with fewer items are not judged for the longest-option share


def _stem_word(w):
    w = w.lower().removesuffix("'s")
    if len(w) > 4 and w.endswith("ies"): return w[:-3] + "y"
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"): return w[:-1]
    return w


def content_words(text):
    """Lower-case content words (letters only, 3+ characters, no stopwords), lightly stemmed (plural s)."""
    return {_stem_word(w) for w in re.findall(r"[A-Za-z][A-Za-z'-]*[A-Za-z]|[A-Za-z]", str(text or ""))
            if len(w) >= 3 and w.lower() not in STOPWORDS}


def distinctive_words(options, answer):
    """Content words of the correct option that no other option uses."""
    if not isinstance(answer, int) or not 0 <= answer < len(options): return set()
    others = set().union(*(content_words(o) for i, o in enumerate(options) if i != answer))
    return content_words(options[answer]) - others


def echoes(text, options, answer):
    """True when every distinctive word of the correct option appears in `text` (and there is at least one)."""
    d = distinctive_words(options, answer)
    return bool(d) and d <= content_words(text)


def gives_away(text, options, answer):
    """The correct option echoes in `text` (see echoes) and no other option does: a list of every choice (food-web
    labels, a stem naming all four) reveals nothing."""
    return echoes(text, options, answer) and not any(echoes(text, options, i) for i in range(len(options)) if i != answer)


def question_part(stem):
    """The question after a passage: the text after the last blank line, else the whole stem."""
    s = str(stem or "")
    return s.rsplit("\n\n", 1)[-1] if "\n\n" in s else s


def _tokens(o):
    """Lower-case words without punctuation or articles."""
    return [w for w in re.sub(r"[^\w\s]", " ", str(o).lower()).split() if w not in ("a", "an", "the")]


def _only_labels_differ(a, b):
    diff = [w for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes() if tag != "equal" for w in a[i1:i2] + b[j1:j2]]
    return bool(diff) and all(LABEL.match(w) for w in diff)


def near_duplicates(options, threshold=NEAR_DUP):
    """Pairs of options whose normalised text (lower case, no punctuation or articles) is at least `threshold` alike
    (difflib ratio). Options shorter than NEAR_DUP_MIN_LEN, and pairs that differ only in labels (P/Q, II, 20), are
    skipped: those contrasts are deliberate."""
    toks = [_tokens(o) for o in options]
    n = [" ".join(t) for t in toks]
    return [(options[i], options[j]) for i in range(len(n)) for j in range(i + 1, len(n))
            if min(len(n[i]), len(n[j])) >= NEAR_DUP_MIN_LEN and not _only_labels_differ(toks[i], toks[j])
            and difflib.SequenceMatcher(None, n[i], n[j]).ratio() >= threshold]


def correct_is_longest(options, answer):
    """True when the correct option is strictly longer (in characters) than every other option."""
    if not isinstance(answer, int) or not 0 <= answer < len(options): return False
    la = len(str(options[answer]).strip())
    return all(la > len(str(o).strip()) for i, o in enumerate(options) if i != answer)


def figure_text(fig):
    """Visible words of a figure: line-art alt + labels, or an inline SVG's <text>/<tspan>/<title>/<desc> content."""
    if isinstance(fig, dict):
        return " ".join([str(fig.get("alt") or "")] + [str(lb.get("text", "")) for lb in fig.get("labels") or [] if isinstance(lb, dict)])
    if isinstance(fig, str):
        try:
            root = ET.fromstring(fig)
            # itertext() of each <text>/<title>/<desc> includes nested <tspan> text AND the tails after them
            return " ".join(t for el in root.iter() if el.tag.split("}")[-1] in ("text", "title", "desc")
                            for t in ["".join(el.itertext())] if t.strip())
        except ET.ParseError:
            return " ".join(re.findall(r">([^<>]+)<", fig))
    return ""


def figure_mismatch(stem, fig):
    """Rough flag: the figure has words, but none of them is a content word of the stem."""
    fw = content_words(figure_text(fig))
    return bool(fw) and not (fw & content_words(stem))


# a STATE word referring to the switch: closed/open, or on/off next to switch/turn/is/stays (the bare word "switch" says nothing)
SWITCH_STATE = re.compile(r"\b(closed|open(ed)?|(switch(ed|es)?|turn(ed|s)?)\s+(it\s+|them\s+|S\d*\s+)?(on|off)|(is|are|stays?|remains?)\s+(on|off))\b", re.I)
SWITCH_DRAWN = re.compile(r'data-switch="1"|width="30" height="12" fill="#fff" stroke="none"/><circle')  # figs_circuit._switch marker, or its older exact string (stored figures)
# items whose drawn switch state IS the question ("The bulb does not light. Why?"): the child reads it off the figure
SWITCH_STATE_IS_QUESTION = {"ci-005", "ci-010"}


def unstated_switch(stem, fig, key=None):
    """FAIL rule figure-unstated-switch: the figure draws a switch labelled S (S, S1, S2 ...) but the stem never gives
    a state word (closed/open/on/off), so a child cannot tell the switch's state (owner's ci-114 photo, 20 Nov 2026).
    Keys in SWITCH_STATE_IS_QUESTION are exempt."""
    if key in SWITCH_STATE_IS_QUESTION: return False
    if not isinstance(fig, str) or not SWITCH_DRAWN.search(fig): return False
    if not any(re.fullmatch(r"S\d*", t) for t in figure_text(fig).split()): return False
    return not SWITCH_STATE.search(stem)


def unqualified_stays_lit(options, answer):
    """WARN rule stays-lit-unqualified: the key is a bare 'It stays lit' (also 'will stay lit', 'remains lit', 'Bulb X
    stays lit') while another option says brighter/dimmer (PSLE answer: it stays lit at the same brightness)."""
    if not isinstance(answer, int) or not 0 <= answer < len(options): return False
    return bool(re.fullmatch(r"\s*(?:(?:it|the bulb|bulb \w+)\s+)?(?:(?:will|would)\s+)?(?:stays?|remains?)\s+(?:lit|on)\.?\s*", str(options[answer]), re.I)) and \
        any(re.search(r"brighter|dimmer", str(o), re.I) for i, o in enumerate(options) if i != answer)


class Warnings:
    """Collects warnings per rule; report() prints counts and up to WARN_LIMIT examples per rule."""

    def __init__(self, rules):
        self.rules = dict(rules)  # rule id -> one-line description
        self.hits = {r: [] for r in self.rules}

    def add(self, rule, msg):
        self.hits[rule].append(msg)

    def report(self):
        print("WARN section (does not change the exit code unless --strict):")
        for r, desc in self.rules.items():
            print(f"WARN {r}: {len(self.hits[r])} ({desc})")
            for m in self.hits[r][:WARN_LIMIT]:
                print(f"  {m}")
        return sum(len(v) for v in self.hits.values())


def longest_share_warnings(per_sub):
    """per_sub: {sub: [bool correct-is-longest per item]} -> messages for sub-topics above LONGEST_SHARE."""
    out = []
    for sub, flags in sorted(per_sub.items()):
        if len(flags) >= LONGEST_MIN_ITEMS and sum(flags) / len(flags) > LONGEST_SHARE:
            out.append(f"{sub}: correct option strictly longest in {sum(flags)}/{len(flags)} items ({sum(flags) / len(flags):.0%})")
    return out


def warning_self_tests(science=False):
    """Tiny self-tests for each warning rule; returns failure messages (an empty list means all pass)."""
    fails = []
    opts = ["evaporation of water", "condensation of water", "melting of ice", "freezing of water"]
    t = lambda ok, name: ok or fails.append(f"warning self-test failed: {name}")
    t(distinctive_words(opts, 0) == {"evaporation"}, "distinctive words")
    t(echoes("Arrows show evaporation from the pond.", opts, 0), "figure leak / stem echo flags the answer word")
    ov = svg_text_overflows  # figure-text-overflow (owner's ph-211 screenshot, 20 Nov 2026)
    cell = '<svg viewBox="0 0 200 50"><rect x="0" y="0" width="{w}" height="40"/><g font-size="18" font-weight="700"><text x="{c}" y="20" text-anchor="middle">Mass gained</text></g></svg>'
    t(ov(cell.format(w=160, c=80)) == [], "overflow: a label that fits passes")
    t(bool(ov(cell.format(w=60, c=30))), "overflow: inherited bold 18px label wider than its cell fails")
    t(ov('<svg><text x="1">&nbsp;</text></svg>')[0][1].startswith("SVG cannot"), "overflow: unparseable SVG fails")
    t(ov('<svg viewBox="0 0 9 9"><text x="50%" font-size="14px">x</text></svg>') == [], "overflow: unit values are skipped, not a crash")
    t(bool(ov('<svg viewBox="0 0 300 60"><g transform="translate(150 30)"><rect x="-16" y="-10" width="32" height="20"/>'
              '<text x="0" y="5" text-anchor="middle" font-size="12">an object</text></g></svg>')), "overflow: translated groups are measured")
    t(not echoes("Arrows show water in a pond.", opts, 0), "figure leak / stem echo ignores shared words")
    t(not echoes("anything", ["A", "B", "C", "D"], 0), "letter options never echo")
    t(gives_away("Arrows show evaporation from the pond.", opts, 0), "gives away: only the answer echoes")
    t(not gives_away("Labels: evaporation, condensation, melting", opts, 0), "every option named: not a give-away")
    t(question_part("Passage text.\n\nWhy did she go?") == "Why did she go?", "question part after a passage")
    t(bool(near_duplicates(["The plant grows taller in light.", "The plant grows taller in the light", "It wilts.", "It dies."])), "near-duplicate options flagged")
    t(not near_duplicates(["has been", "will be", "was", "is being"]), "distinct options not flagged")
    t(not near_duplicates(["Part P makes food for it", "Part Q makes food for it", "x", "y"]), "label-only contrast not flagged")
    t(correct_is_longest(["a much longer option", "short", "tiny", "mid size"], 0), "strictly longest")
    t(not correct_is_longest(["same", "same", "x", "y"], 0), "a tie is not strictly longest")
    t(len(longest_share_warnings({"s": [True] * 4 + [False] * 4})) == 1, "longest share above 35% warns")
    t(not longest_share_warnings({"s": [True] * 2 + [False] * 6}), "longest share at 25% is quiet")
    sw = '<svg viewBox="0 0 9 9"><g><rect x="1" y="1" width="30" height="12" fill="#fff" stroke="none"/><circle cx="1" cy="1" r="2.5"/></g><text x="3" y="3">S</text></svg>'
    t(unstated_switch("Will the bulb light up?", sw), "unstated switch: stem silent about S fails")
    t(not unstated_switch("Switch S is closed. Will the bulb light up?", sw), "unstated switch: stem states S passes")
    t(not unstated_switch("Will the bulb light up?", "<svg viewBox='0 0 9 9'><text>S</text></svg>"), "unstated switch: a figure without a switch symbol is not judged")
    t(unstated_switch("The switch is shown. Will the bulb light up?", sw), "unstated switch: the bare word 'switch' is not a state")
    t(not unstated_switch("Switch S is turned off. Will the bulb light up?", sw), "unstated switch: 'turned off' is a state")
    t(not unstated_switch("The bulb does not light up. Why?", sw, "ci-005"), "unstated switch: allowlisted state-is-the-question item passes")
    for v in ("It stays lit", "It will stay lit", "It remains lit", "Bulb X stays lit", "The bulb remains on."):
        t(unqualified_stays_lit(["It goes out", v, "It becomes dimmer", "It becomes brighter"], 1), f"stays-lit variant flagged: {v}")
    t(unqualified_stays_lit(["It goes out", "It stays lit", "It becomes dimmer", "It becomes brighter"], 1), "bare stays-lit key flagged")
    t(not unqualified_stays_lit(["It goes out", "It stays lit at the same brightness", "It becomes dimmer", "It becomes brighter"], 1), "qualified stays-lit key quiet")
    if science:  # the real figs_circuit._switch output (new marker) and the old stored string both reach the detector
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).parent / "science"))
        import figs_circuit
        real = figs_circuit.circuit([[("L", "X")], [("B", 1), ("S", "S", True)]], W=300)
        t(unstated_switch("Will the bulb light up?", real), "unstated switch: real _switch() output is detected")
        t(not unstated_switch("Switch S is closed. Will the bulb light up?", real), "unstated switch: real output, state stated")
        t('data-switch="1"' not in sw and unstated_switch("Will it light?", sw), "unstated switch: old stored string still detected")
    if science:
        svg = "<svg viewBox='0 0 1 1'><text>Beaker A</text><text>ice</text></svg>"
        t(figure_text(svg) == "Beaker A ice", "svg figure text")
        t(figure_text({"img": "/science/x.webp", "alt": "a pond", "labels": [{"x": 1, "y": 1, "text": "frog"}]}) == "a pond frog", "line-art figure text")
        t(not figure_mismatch("What happens to the ice in beaker A?", svg), "figure mentions a stem noun")
        t(figure_mismatch("Which animal eats the grass?", svg), "figure mentions no stem noun")
        t(not figure_mismatch("Which animal eats the grass?", "<svg viewBox='0 0 1 1'><path d='M0 0'/></svg>"), "a figure without words is not judged")
    return fails


# ------------------------------------------------------------------ SVG text fit (check_science; reusable for other inline figures)
TEXT_OVERFLOW_SLACK = 4  # px a label may pass its cell or the viewBox before it counts as overflowing


def svg_text_overflows(svg):
    """Labels of an inline SVG that do not fit: each <text> width is estimated (font-size x 0.55 per character,
    0.6 bold; font-size and weight inherited from parent groups; text-anchor respected) and compared with the smallest
    <rect> that holds it centred (a table cell or box) and with the viewBox. Returns [(text, reason)]. Simple and
    slightly generous on purpose. Not measured (no false alarms): text under a transform other than translate(), text with <tspan> lines,
    values with units or lists. An SVG that cannot be parsed is itself a failure.
    ponytail: horizontal fit only and a fixed per-character width; add vertical fit / real font metrics if a fault slips by."""
    import re
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as e:
        return [("(figure)", f"SVG cannot be parsed ({e})")]
    tag = lambda el: el.tag.split("}")[-1]
    parent = {c: p for p in root.iter() for c in p}
    def num(v, default=None):
        try:
            return float(v)
        except (TypeError, ValueError):
            return default
    def inherited(el, attr):
        while el is not None:
            if el.get(attr) is not None:
                return el.get(attr)
            el = parent.get(el)
        return None
    def offset(el):
        """Summed translate() of the element and its groups; None under any other transform (not measured)."""
        dx = dy = 0.0
        while el is not None:
            t = el.get("transform")
            if t:
                m = re.fullmatch(r"\s*translate\(\s*(-?[\d.]+)(?:[\s,]+(-?[\d.]+))?\s*\)\s*", t)
                if not m:
                    return None
                dx, dy = dx + float(m.group(1)), dy + float(m.group(2) or 0)
            el = parent.get(el)
        return dx, dy
    vb = [num(v) for v in re.split(r"[ ,]+", (root.get("viewBox") or "").strip()) if v]
    vb = vb if len(vb) == 4 and None not in vb else []
    rects = []
    for el in root.iter():
        if tag(el) == "rect" and offset(el) is not None:
            (dx, dy), r = offset(el), tuple(num(el.get(k, 0)) for k in ("x", "y", "width", "height"))
            if None not in r:
                rects.append((r[0] + dx, r[1] + dy, r[2], r[3]))
    out = []
    for el in root.iter():
        if tag(el) != "text" or offset(el) is None or any(tag(c) == "tspan" for c in el):
            continue
        s = "".join(el.itertext()).strip()
        x, y, fs = num(el.get("x")), num(el.get("y", 0)), num(inherited(el, "font-size") or 14)
        if not s or x is None or y is None or fs is None:
            continue
        x, y = x + offset(el)[0], y + offset(el)[1]
        bold = (inherited(el, "font-weight") or "") in ("bold", "bolder", "600", "700", "800", "900")
        w = len(s) * fs * (0.6 if bold else 0.55)
        anchor = inherited(el, "text-anchor") or "start"
        x0, x1 = (x - w / 2, x + w / 2) if anchor == "middle" else (x - w, x) if anchor == "end" else (x, x + w)
        # cell check only for text centred in its box (table cells, labelled boxes); free labels are held to the viewBox only
        holders = [r for r in rects if anchor == "middle" and r[2] >= 30 and abs(x - (r[0] + r[2] / 2)) < 1 and r[1] <= y <= r[1] + r[3]]
        if holders:
            rx, _, rw, _ = min(holders, key=lambda r: r[2] * r[3])
            if x0 < rx - TEXT_OVERFLOW_SLACK or x1 > rx + rw + TEXT_OVERFLOW_SLACK:
                out.append((s, f"text ~{w:.0f}px wide overflows its {rw:.0f}px cell"))
                continue
        if vb and (x0 < vb[0] - TEXT_OVERFLOW_SLACK or x1 > vb[0] + vb[2] + TEXT_OVERFLOW_SLACK):
            out.append((s, "text runs past the viewBox"))
    return out


