"""Helpers shared by the reviewed-item bank builds (Chinese, English, Science)."""
import difflib
import hashlib
import json
import re
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
            return " ".join(t for el in root.iter() if el.tag.split("}")[-1] in ("text", "tspan", "title", "desc")
                            for t in [el.text or ""] if t.strip())
        except ET.ParseError:
            return " ".join(re.findall(r">([^<>]+)<", fig))
    return ""


def figure_mismatch(stem, fig):
    """Rough flag: the figure has words, but none of them is a content word of the stem."""
    fw = content_words(figure_text(fig))
    return bool(fw) and not (fw & content_words(stem))


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
    if science:
        svg = "<svg viewBox='0 0 1 1'><text>Beaker A</text><text>ice</text></svg>"
        t(figure_text(svg) == "Beaker A ice", "svg figure text")
        t(figure_text({"img": "/science/x.webp", "alt": "a pond", "labels": [{"x": 1, "y": 1, "text": "frog"}]}) == "a pond frog", "line-art figure text")
        t(not figure_mismatch("What happens to the ice in beaker A?", svg), "figure mentions a stem noun")
        t(figure_mismatch("Which animal eats the grass?", svg), "figure mentions no stem noun")
        t(not figure_mismatch("Which animal eats the grass?", "<svg viewBox='0 0 1 1'><path d='M0 0'/></svg>"), "a figure without words is not judged")
    return fails
