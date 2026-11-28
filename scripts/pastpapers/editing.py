#!/usr/bin/env python3
"""English Editing (spelling and grammar) as typed questions: which printed word each question number corrects.

A PSLE Editing passage prints numbered underlined words, each with one spelling or grammar error; the child writes the
corrected word in a box. The two vision reads (passage.py) copy the WORDS well but put the numbers on the wrong word
(the boxes sit between the lines, so a reader tends to give number n to the next underlined word), and they sometimes
"correct" a misspelling as they copy it. So the school key, not the readers' numbers, says where each question is.

  editing.py text      the three reads -> one text per section, every underlined word either reader marked kept as a
                       candidate, words the readers spell differently marked spelling_unsure     -> OUT/text.jsonl
  editing.py place     an ordered assignment of each keyed number to a word (spelling, sound, word form, grammar-word
                       swaps; question order = text order; the readers' n / n+1 marks a weak prior), with a confidence,
                       the runner-up, and the section sanity check (keys that do not belong)       -> OUT/place.jsonl
  editing.py pack      packs of ~12 sections for a text-only confirmer                          -> OUT/pack_N.jsonl
  editing.py vpack     packs of ~8 sections for page-read confirmers (Opus reads the scans; brief OUT/VCONFIRM.md,
                       reply OUT/vout_N.jsonl: the contract below plus "printed", "sure", "missing_word" per number
                       and "numbers_on_page", "unnumbered" per section). final prefers vout over out.
  editing.py final     after the confirmers: complete passages only, as typed rows
                       -> TMP/ppimport/engedit-ship/english/selected.jsonl  (then load_pp.py upload --out that dir)
  editing.py selftest  made-up examples only (no past-paper text in the repo)
  editing.py explain-pack | explain-lint | explain-checkpack | explain-recheck TAG | explain-apply
                       the "Why this works" texts for the shipped rows (cloze_explain.py's machinery, pointed at
                       OUT/explain; see EXPLANATIONS below)

EXPLANATIONS. Writers read OUT/explain/WRITER.md and a pack OUT/explain/pack_N.jsonl (about 4 passages: {grp, section,
passage with each asked word shown as "(n) wrong-word", blanks: [{id, n, wrong, accept}]}) and write out_N.jsonl, one line
per question: {"id", "right"}. "right" is 1-2 short sentences, at most 280 characters, for a 12-year-old: it quotes the
printed wrong word and the correct word in single quotes; for a spelling error it says what is wrong with the spelling in
a way that helps remember it (swapped, doubled or missing letters, the sound that fooled the writer); for a grammar error
it names the rule and the clue words in the sentence, quoted exactly as in the passage. Made-up example, passage "Tom
(1) runned to school.", accept ["ran"]:
  {"id": "x1", "right": "'Runned' is not a word: 'run' is irregular, so the past tense is 'ran'. The clue is 'Tom' and the finished action."}
A key that looks wrong is still explained, and a line {"id", "reason"} goes to doubts_N.jsonl. explain-lint checks the rules
(at most 300 characters, no "!", not "The answer is...", names the correct word and the printed wrong word inside quotes,
names every other accepted answer when there are 3 or fewer). Checkers read OUT/explain/CHECKER.md and cpack_N.jsonl (the
pack plus "explanation" on each question) and write check_N.jsonl: {"id", "ok": true|false, "reason"}. explain-apply ships
only lint-clean AND checker-ok explanations whose verdict was given for exactly this text, key and passage ->
SHIP/english/explain.jsonl ({"id", "explain": {"right", "wrong": []}, "fp"}; load_pp.py upload reads it).

CONFIRMER CONTRACT (the reply to one pack_N.jsonl, written as OUT/out_N.jsonl): one JSON line per section,
  {"sec": "<the section id>", "q": [<one object per number in the section's key list>]}
each object
  {"n": <question number>,
   "span": <word index i of the wrong word, from the text's marks ⟦i|word⟧, or null if it cannot be placed>,
   "wrong": "<the wrong word exactly as printed in the text (when a mark shows two readings a~b, the one you believe)>",
   "correct": "<the key>",
   "also": [<other corrections that are equally right, if any>],
   "doubt": "<reason, if the key seems wrong or does not belong to this passage; else empty>",
   "context": "<optional, when span is null but the word is in the text unmarked: the wrong word with the 3 words before it>"}
A mark ⟦i|word⟧ is a word the readers underlined or the matcher proposes; i is its word index in the text. A two-word
wrong span uses the index of its first word. "correct" repeats the key; a better correction goes in "doubt".

final keeps a number only when the matcher and the confirmer agree on the span, the confirmer has no doubt and keeps the
key, and at least two of the three readers spelled that word the same (two models do not invent the same misspelling)
and that spelling is not the key (readers silently correct), or the owner file gives its spelling; a section ships only when every
one of its numbers is kept (as cloze_final). Owner file OUT/editing_owner.jsonl, one change per line:
  {"sec", "n", "add": [...]} / {"sec", "n", "drop": [...]}   accepted answers (drops apply before adds)
  {"sec", "n", "wrong": "exstrimli"}                        the printed spelling of the wrong word (settles spelling_unsure)
  {"sec", "n", "span": i}                                   the owner's placement (overrides matcher and confirmer)
  {"sec", "fix": [old, new]}                                a text fix, exactly once, outside the marked words
  {"sec", "hold": "reason"}                                 never ship this section"""
import collections
import difflib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import passage as P  # noqa: E402

TMP = P.TMP
OUT = TMP / "editing"
SHIP = TMP / "ppimport" / "engedit-ship"
WORD = re.compile(r"[A-Za-z0-9]+(?:['’][A-Za-z]+)*")
OPEN, CLOSE = "⟦", "⟧"


def jw(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def nw(w):
    return re.sub(r"[^a-z0-9']", "", (w or "").lower().replace("’", "'"))


# ------------------------------------------------------------------ text

def strip_marks(p):
    """The read's text without {{n|...}} marks, and the marks as (n, start, end) in that text."""
    out, marks, last = [], [], 0
    for m in P.UNDER.finditer(p):
        out.append(p[last:m.start()])
        s = sum(map(len, out))
        out.append(m.group(2))
        marks.append((int(m.group(1)), s, s + len(m.group(2))))
        last = m.end()
    out.append(p[last:])
    return "".join(out), marks


def toks(text):
    return [(m.group(0), m.start(), m.end()) for m in WORD.finditer(text)]


def merge(p1, p2):
    """One text from the two reads. Base = read 1 (the bigger model) unless read 2 has clearly more words; a run only the
    other read has (up to 30 words) is put in. Each word: {w, s, e, src: both|diff|one, alt: other read's spelling,
    m1/m2: the numbers each reader put on it}. Returns (text, words, ratio, gap)."""
    reads = [x for x in (p1, p2)]
    t = [strip_marks(p) if p else ("", []) for p in reads]
    k = [toks(x[0]) for x in t]
    bi = 0 if k[0] and (not k[1] or len(k[1]) <= 1.1 * len(k[0])) else 1
    oi = 1 - bi
    (bt, bm), (ot, om) = t[bi], t[oi]
    a, b = k[bi], k[oi]
    sm = difflib.SequenceMatcher(None, [nw(x[0]) for x in a], [nw(x[0]) for x in b], autojunk=False)
    ratio = sm.ratio() if a and b else 0.0
    text, words, bmap, omap, gap = "", [], {}, {}, False
    if a:
        text = bt[:a[0][1]]

    def put(w, src, alt=None, tail=" "):
        nonlocal text
        s = len(text)
        text += w
        words.append({"w": w, "s": s, "e": s + len(w), "src": src, "alt": alt})
        text += tail
        return len(words) - 1

    def tail(i):  # base text after word i up to the next word
        return bt[a[i][2]:a[i + 1][1]] if i + 1 < len(a) else bt[a[i][2]:]

    for tag, i1, i2, j1, j2 in (sm.get_opcodes() if b else [("delete", 0, len(a), 0, 0)]):
        if tag == "insert":
            if j2 - j1 > 30:
                gap = True
                continue
            # the other read's words go before the gap text already written after the last word
            last_e = words[-1]["e"] if words else len(text)
            gapt, text = text[last_e:], text[:last_e]
            for j in range(j1, j2):
                if words and text and not text[-1].isspace():
                    text += " "
                omap[j] = put(b[j][0], "one", None, "")
            text += gapt if gapt else " "
            continue
        for x, i in enumerate(range(i1, i2)):
            if tag == "equal":
                bmap[i] = put(a[i][0], "both", None, tail(i))
                omap[j1 + x] = bmap[i]
            elif tag == "replace":
                same_len = (i2 - i1) == (j2 - j1)
                alt = b[j1 + x][0] if same_len else " ".join(w for w, _, _ in b[j1:j2])
                bmap[i] = put(a[i][0], "diff", alt, tail(i))
                if same_len:
                    omap[j1 + x] = bmap[i]
                elif x == 0:
                    for j in range(j1, j2):
                        omap.setdefault(j, bmap[i])
            else:
                bmap[i] = put(a[i][0], "one", None, tail(i))
    for w in words:
        w["m1"], w["m2"] = [], []
    for idx, (marks, ks, mp) in enumerate(((bm, a, bmap), (om, b, omap))):
        key = "m1" if (bi if idx == 0 else oi) == 0 else "m2"
        for n, s, e in marks:
            hit = [mp[j] for j, (_, ws, we) in enumerate(ks) if ws < e and we > s and j in mp]
            if not hit and s == e:  # an empty box (a missing word): the word after it
                hit = [mp[j] for j, (_, ws, _) in enumerate(ks) if ws >= s and j in mp][:1]
            for h in hit:
                words[h][key].append(n)
    return text, words, round(ratio, 3), gap


READERS = ("1", "2", "3")  # read.jsonl (Qwen2.5-VL-72B), read2.jsonl (32B), read3.jsonl (Qwen3)


def align(words, p):
    """One read against the merged words: (its spelling per merged word or None, its marks as {merged word: [n]})."""
    t, marks = strip_marks(p)
    k = toks(t)
    sm = difflib.SequenceMatcher(None, [nw(w["w"]) for w in words], [nw(x[0]) for x in k], autojunk=False)
    rd, mp = [None] * len(words), {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("equal", "replace"):
            for j in range(j1, j2):
                mp[j] = i1 + min(j - j1, i2 - i1 - 1)
            if i2 - i1 == j2 - j1:
                for x in range(i2 - i1):
                    rd[i1 + x] = k[j1 + x][0]
    m = collections.defaultdict(list)
    for n, s, e in marks:
        hit = [mp[j] for j, (_, ws, we) in enumerate(k) if ws < e and we > s and j in mp]
        if not hit and s == e:  # an empty box (a missing word): the word after it
            hit = [mp[j] for j, (_, ws, _) in enumerate(k) if ws >= s and j in mp][:1]
        for h in hit:
            m[h].append(n)
    return rd, m, sm.ratio()


def merge_reads(reads):
    """One text from up to three reads {label: passage}: the first two available are merged (merge), then every read is
    aligned to it. Each word gets reads {label: spelling}, m1/m2/m3 (each reader's numbers on it), agree (the readers
    giving its shown spelling), trusted (two or more readers give that same spelling; the shown spelling is then theirs),
    alts (the other spellings seen). Returns (text, words, ratio of the first two, gap)."""
    have = [lb for lb in READERS if reads.get(lb)]
    if not have:
        return "", [], 0.0, False
    text, words, ratio, gap = merge(reads[have[0]], reads[have[1]] if len(have) > 1 else None)
    for w in words:
        w["reads"] = {}
        for lb in READERS:
            w["m" + lb] = []
    for lb in have:
        rd, m, _ = align(words, reads[lb])
        for i, w in enumerate(words):
            if rd[i] is not None:
                w["reads"][lb] = rd[i]
            w["m" + lb] = m.get(i, [])
    out, last = [], 0
    for w in words:
        votes = collections.Counter(w["reads"].values())
        top, nv = votes.most_common(1)[0] if votes else (w["w"], 0)
        shown = top if nv >= 2 else w["w"]
        out.append(text[last:w["s"]])
        last = w["e"]
        w["w"], w["trusted"] = shown, nv >= 2
        w["agree"] = sorted(lb for lb, x in w["reads"].items() if x == shown)
        w["alts"] = sorted({x for x in w["reads"].values() if x != shown and len(x.split()) == 1})
        w["src"] = "both" if w["trusted"] else ("diff" if w["alts"] else "one")
        w["alt"] = w["alts"][0] if w["alts"] else None
        out.append(shown)
    out.append(text[last:])
    # offsets in the rebuilt text
    pos, t2 = 0, ""
    for piece_i in range(0, len(out) - 1, 2):
        t2 += out[piece_i]
        w = words[piece_i // 2]
        w["s"] = len(t2)
        t2 += out[piece_i + 1]
        w["e"] = len(t2)
    t2 += out[-1]
    return t2, words, ratio, gap


def unsure(w):
    return not w.get("trusted", w.get("src") == "both")


def marked(w):
    return [n for lb in READERS for n in w.get("m" + lb, [])]


def clean_key(raw):
    """(accepted spellings, note): note is '' for a usable key, else why the key is not an Editing answer."""
    k = (raw or "").strip()
    if not k:
        return [], "no key"
    if re.fullmatch(r"\(?[1-4]\)?\.?", k) or re.search(r"\(1\).*;", k):
        return [], "an MCQ key"
    if re.match(r"^[A-Z]\s+(prep|tense|wf|sva|sp|spelling|grammar)\b", k, re.I):
        return [], "an annotation, not a word"
    if re.fullmatch(r"\(?[A-HJ-Z]\)?", k):
        return [], "a word-box letter (another section)"
    if re.fullmatch(r"\(?[A-Z]\)?\s*\(?[A-Za-z'’]+\)?", k) and re.match(r"^\(?[A-Z]\)?\s", k):
        return [], "a word-box letter (another section)"
    k = re.sub(r"\s*\((?![^()]*\)\s*$).*$", "", k) if not k.startswith("(") else k  # "be (become - not accepted ...)"
    k = re.sub(r"\s*\([^()]*\)\s*$", "", k) if not k.startswith("(") else k
    m = re.fullmatch(r"\((.+)\)", k)
    k = m.group(1) if m else k
    note = "caps" if k.isupper() and len(k) > 1 else ""
    alts = [a.strip(" .;:'\"").lower() if note else a.strip(" .;:'\"") for a in re.split(r"\s*(?:/|,|\bor\b)\s*", k)]
    alts = [a for a in alts if a]
    if not alts or any(len(a.split()) > 3 for a in alts) or not all(re.fullmatch(r"[A-Za-z'’ -]+", a) for a in alts):
        return [], "a sentence or not a word"
    return alts, note


# ------------------------------------------------------------------ scoring

SWAP = [{"is", "are", "was", "were", "be", "been", "am", "being"}, {"has", "have", "had", "having"},
        {"do", "does", "did", "done", "doing"}, {"a", "an", "the"},
        {"he", "him", "his", "she", "her", "hers", "i", "me", "my", "mine", "we", "us", "our", "ours", "they", "them",
         "their", "theirs", "it", "its", "you", "your", "yours"},
        {"himself", "herself", "myself", "ourselves", "themselves", "itself", "yourself", "yourselves"},
        {"this", "that", "these", "those"}, {"who", "whom", "whose", "which", "that", "where", "when", "what"},
        {"in", "on", "at", "to", "for", "of", "by", "with", "from", "into", "onto", "about", "over", "under", "among",
         "between", "through", "across", "along", "towards", "toward", "upon", "since", "during", "off", "out", "up",
         "down", "without", "within", "against", "beside", "besides", "after", "before", "until", "till", "as", "like"},
        {"and", "but", "or", "so", "because", "although", "though", "while", "whereas", "unless", "if", "when",
         "whenever", "as", "since", "until", "before", "after", "yet", "nor", "however", "therefore"},
        {"each", "every", "all", "both", "either", "neither", "any", "some", "no", "none"},
        {"much", "many", "few", "little", "less", "fewer", "more", "most", "least"},
        {"can", "could", "will", "would", "shall", "should", "may", "might", "must"},
        {"there", "their", "they're"}, {"its", "it's"}, {"your", "you're"}, {"then", "than"}, {"to", "too", "two"},
        {"whether", "weather"}, {"lose", "loose", "lost"}, {"affect", "effect"}, {"accept", "except"},
        {"quite", "quiet"}, {"past", "passed"}, {"no", "not", "never"}, {"lie", "lay", "lain", "laid", "lying", "lies"},
        {"rise", "raise", "rose", "raised", "risen"}, {"sit", "set", "sat"}, {"learnt", "learned", "taught"}]
IRREG = {"went": "go", "gone": "go", "goes": "go", "ran": "run", "saw": "see", "seen": "see", "took": "take",
         "taken": "take", "came": "come", "brought": "bring", "bought": "buy", "thought": "think", "caught": "catch",
         "taught": "teach", "lost": "lose", "children": "child", "feet": "foot", "teeth": "tooth", "mice": "mouse",
         "women": "woman", "men": "man", "people": "person", "ate": "eat", "eaten": "eat", "wrote": "write",
         "written": "write", "gave": "give", "given": "give", "began": "begin", "begun": "begin", "knew": "know",
         "known": "know", "flew": "fly", "flown": "fly", "fell": "fall", "fallen": "fall", "drove": "drive",
         "driven": "drive", "better": "good", "best": "good", "worse": "bad", "worst": "bad", "left": "leave",
         "felt": "feel", "kept": "keep", "slept": "sleep", "swam": "swim", "swum": "swim", "sang": "sing",
         "sung": "sing", "rang": "ring", "rung": "ring", "spoke": "speak", "spoken": "speak", "broke": "break",
         "broken": "break", "chose": "choose", "chosen": "choose", "froze": "freeze", "frozen": "freeze",
         "stole": "steal", "stolen": "steal", "hid": "hide", "hidden": "hide", "bit": "bite", "bitten": "bite",
         "shook": "shake", "shaken": "shake", "woke": "wake", "woken": "wake", "wore": "wear", "worn": "wear",
         "tore": "tear", "torn": "tear", "grew": "grow", "grown": "grow", "threw": "throw", "thrown": "throw",
         "drew": "draw", "drawn": "draw", "blew": "blow", "blown": "blow", "held": "hold", "stood": "stand",
         "understood": "understand", "won": "win", "sat": "sit", "met": "meet", "led": "lead", "fed": "feed",
         "fought": "fight", "sought": "seek", "sold": "sell", "told": "tell", "paid": "pay", "said": "say",
         "laid": "lay", "lain": "lie", "made": "make", "found": "find", "heard": "hear", "built": "build",
         "sent": "send", "spent": "spend", "lent": "lend", "bent": "bend", "meant": "mean", "dug": "dig",
         "hung": "hang", "struck": "strike", "stuck": "stick", "swept": "sweep", "wept": "weep", "crept": "creep",
         "leapt": "leap", "dealt": "deal", "rode": "ride", "ridden": "ride", "rose": "rise", "risen": "rise",
         "forgot": "forget", "forgotten": "forget", "got": "get", "gotten": "get", "became": "become", "did": "do",
         "done": "do", "was": "be", "were": "be", "is": "be", "are": "be", "been": "be", "has": "have", "had": "have",
         "mine": "my", "geese": "goose", "lives": "life", "leaves": "leaf", "wolves": "wolf", "knives": "knife"}
SUFFIX = ("fulness", "ically", "ations", "ation", "ments", "ment", "ness", "ions", "ion", "ings", "ing", "ies", "ied",
          "ers", "est", "ier", "iest", "ily", "ly", "ed", "es", "er", "s", "ful", "less", "ous", "ive", "ance", "ence",
          "ity", "al", "ise", "ize", "ised", "ized", "e", "y")


def lemma(w):
    w = IRREG.get(w, w)
    for suf in SUFFIX:
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[:-len(suf)]
    return w


def osa(a, b):
    """Damerau-Levenshtein distance (optimal string alignment): a swap of two letters counts once."""
    d = [[i + j if not i * j else 0 for j in range(len(b) + 1)] for i in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] != b[j - 1]))
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[-1][-1]


def squeeze(w):
    return re.sub(r"(.)\1+", r"\1", w)


def phon(w):
    """A simple sound key: common spellings of one sound made the same, then vowels after the first letter dropped."""
    w = re.sub(r"[^a-z]", "", w.lower())
    if not w:
        return ""
    for a, b in (("tch", "ch"), ("ph", "f"), ("ck", "k"), ("dge", "j"), ("gh", ""), ("wr", "r"), ("kn", "n"),
                 ("wh", "w"), ("sch", "sk"), ("qu", "kw"), ("x", "ks"), ("q", "k"), ("z", "s"), ("tion", "shn"),
                 ("sion", "shn"), ("cious", "shs"), ("tious", "shs")):
        w = w.replace(a, b)
    w = re.sub(r"c(?=[eiy])", "s", w).replace("c", "k")
    w = squeeze(w)
    return w[0] + re.sub(r"[aeiouyhw]", "", w[1:])


def in_swap(t, k):
    return any(t in s and k in s for s in SWAP)


def lex1(t, k):
    """How likely printed word t is the wrong word that key word k corrects (0..1); kinds: spell, sound, form, swap."""
    t, k = nw(t), nw(k)
    if not t or not k or t == k:
        return 0.0, ""
    if in_swap(t, k):
        return 0.6, "swap"
    if IRREG.get(t, t) == IRREG.get(k, k) or (lemma(t) == lemma(k) and len(lemma(k)) >= 3):
        return 0.85, "form"
    if squeeze(t) == squeeze(k):
        return 0.92, "spell"
    d = osa(t, k)
    s = 1 - d / max(len(t), len(k))
    kind = "spell"
    if len(k) >= 5 and phon(t) == phon(k):
        s, kind = max(s, 0.85), "sound"
    pre = len(__import__("os").path.commonprefix([t, k]))
    if pre >= 5 and pre >= 0.6 * min(len(t), len(k)):
        f = 0.8 if (len(t) > pre and len(k) > pre) else 0.75
        if f > s:
            s, kind = f, "form"
    if len(k) >= 5 and t[0] == k[0] and s < 0.6:
        r = difflib.SequenceMatcher(None, t, k).ratio()
        if r >= 0.6:
            s, kind = 0.8 * r, "wrong word"
        elif r >= 0.5 and min(len(t), len(k)) >= 7:
            s, kind = 0.5, "wrong word"  # "preserving" for "perseverance": weak, the order and the marks decide
    same_start = phon(t)[:1] == phon(k)[:1]
    if len(k) <= 3 or len(t) <= 3:
        return (s, kind) if s >= 0.66 and t[0] == k[0] else (0.0, "")
    if not same_start and s < 0.8:
        return 0.0, ""  # "down" is not a misspelling of "known"
    return (s, kind) if s >= 0.6 or (s >= 0.5 and t[0] == k[0]) else (0.0, "")


def lex(words, i, span, key):
    """Score of words[i:i+span] as the wrong text for one key spelling (a phrase key compares word by word)."""
    ws = words[i:i + span]
    if len(ws) < span:
        return 0.0, ""
    kt = key.split()
    readings = [[w["w"] for w in ws]]
    for x in range(max((len(w.get("alts") or []) for w in ws), default=0)):
        readings.append([w["alts"][x] if len(w.get("alts") or []) > x else w["w"] for w in ws])
    best = (0.0, "")
    for rd in readings:
        joined = "".join(nw(x) for x in rd)
        if len(kt) == span:
            diff = [(x, y) for x, y in zip(rd, kt) if nw(x) != nw(y)]
            if len(diff) == 1:
                best = max(best, lex1(*diff[0]))
            elif not diff and span == 1:
                pass
        if span == 2 and len(kt) == 1 and joined == nw(key):  # "a lot" printed for "alot" or the reverse
            best = max(best, (0.8, "spell"))
        if span == 1 and len(kt) == 2 and nw(rd[0]) == "".join(nw(x) for x in kt):
            best = max(best, (0.8, "spell"))
        if span == 1 and len(kt) > 1:  # "had eaten" for printed "ate"
            best = max(best, max((lex1(rd[0], x)[0] * 0.85, "form") for x in kt))
    if span == 1 and best[0] == 0 and nw(ws[0]["w"]) == nw(key) and marked(ws[0]):
        best = (0.45, "reader copied it correct")  # an underlined word a reader "corrected" while copying
    return best


def prior(w, n, prev_marked):
    """The readers' numbers as a weak hint: n+1 is the usual slip, n itself next; also the word just before a word marked n."""
    b = 0.0
    for lb in READERS:
        for x in w.get("m" + lb, []):
            b = max(b, {n + 1: 0.3, n: 0.2, n + 2: 0.12, n - 1: 0.1}.get(x, 0.05))
    if sum(bool(w.get("m" + lb)) for lb in READERS) >= 2:
        b += 0.03
    if n in prev_marked:
        b = max(b, 0.15)
    return b


def candidates(words, n, keys):
    out = []
    near = [i for i, w in enumerate(words) if {n, n + 1} & set(marked(w))]
    for i, w in enumerate(words):
        nxt = words[i + 1] if i + 1 < len(words) else {}
        pb = prior(w, n, set(marked(nxt)))
        if near:  # a tie-breaker: nearer the words the readers numbered n or n+1
            pb += 0.08 * 0.85 ** min(abs(i - j) for j in near)
        for span in (1, 2, 3):
            if span > 1 and not any(len(k.split()) > 1 or span == 2 for k in keys):
                continue
            s, kind = max((lex(words, i, span, k) for k in keys), default=(0.0, ""))
            if s >= 0.45:
                out.append({"i": i, "span": span, "lex": round(s, 3), "kind": kind, "prior": pb, "tot": s + pb,
                            "wrong": " ".join(w2["w"] for w2 in words[i:i + span])})
    return out


def assign(cands):
    """cands: [(n, [cand])] in question order -> {n: cand}: positions strictly increasing, total score highest (a number
    may stay unplaced)."""
    states = [(-1, 0.0, {})]  # (last end, total, assignment), kept Pareto (later end only if higher total)
    for n, cs in cands:
        new = list(states)
        for c in cs:
            ok = [s for s in states if s[0] < c["i"]]
            if ok:
                e, t, a = max(ok, key=lambda s: s[1])
                new.append((c["i"] + c["span"] - 1, t + c["tot"], {**a, n: c}))
        new.sort(key=lambda s: (s[0], -s[1]))
        states, best = [], -1.0
        for s in new:
            if s[1] > best + 1e-9:
                states.append(s)
                best = s[1]
    return max(states, key=lambda s: s[1])[2]


def band(c, margin):
    on = c["prior"] >= 0.1
    if c["lex"] >= 0.75 and margin >= 0.25 and on:
        return "high"
    if c["lex"] >= 0.55 and margin >= 0.1:
        return "medium"
    return "low"


# ------------------------------------------------------------------ commands

def sections():
    return [s for s in P.jl(P.WORK / "sections.jsonl") if s["st"] == "eng-editing"]


def text():
    raw = {lb: {r["sec"]: r["raw"] for r in P.jl(P.WORK / f)}
           for lb, f in zip(READERS, ("read.jsonl", "read2.jsonl", "read3.jsonl"))}
    Q = P.questions()
    rows, why = [], collections.Counter()
    for s in sections():
        reads = {lb: (P.parse(raw[lb].get(s["sec"])) or {}).get("passage") for lb in READERS}
        reads = {lb: p for lb, p in reads.items() if p}
        if not reads:
            why["not read"] += 1
            continue
        t, words, _, gap = merge_reads(reads)
        pl = [P.plain(p).split() for p in reads.values()]
        # the best agreement of any two reads (one read alone: 0)
        ratio = round(max((difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
                           for x, a in enumerate(pl) for b in pl[x + 1:]), default=0.0), 3)
        keys = collections.defaultdict(list)
        for i in sorted(s["ids"]):
            q = Q.get(i)
            if q and isinstance(q.get("qno"), int):
                keys[q["qno"]].append({"id": i, "raw": q.get("answer")})
        why[f"{len(reads)} reads"] += 1
        rows.append({"sec": s["sec"], "year": s["year"], "paper": s["paper"], "pages": s["pages"], "qnos": s["qnos"],
                     "ratio": ratio, "gap": gap, "readers": sorted(reads), "text": t, "words": words,
                     "keys": {str(n): v for n, v in sorted(keys.items())}})
    jw(OUT / "text.jsonl", rows)
    uns = sum(unsure(w) for r in rows for w in r["words"])
    cand = sum(bool(marked(w)) for r in rows for w in r["words"])
    print(f"{len(rows)} sections ({dict(why)}), {cand} underlined candidate words, {uns} words spelling_unsure; "
          f"text agreement >= 0.95: {sum(r['ratio'] >= .95 for r in rows)} -> {OUT / 'text.jsonl'}")


def text_hash(r):
    """What place.jsonl's word indices point into: the section's words, in order."""
    import hashlib
    return hashlib.sha1("\x1f".join(w["w"] for w in r["words"]).encode("utf-8")).hexdigest()[:16]


def stamp_place():
    """One-off, run deliberately: stamp the place.jsonl rows that have no text hash with the hash of the CURRENT text.jsonl.
    Only right if place.jsonl was built from this text.jsonl (a rows' hash that exists is never changed)."""
    rows = {r["sec"]: r for r in P.jl(OUT / "text.jsonl")}
    pl = P.jl(OUT / "place.jsonl")
    n = 0
    for o in pl:
        if "th" not in o and o["sec"] in rows:
            o["th"] = text_hash(rows[o["sec"]])
            n += 1
    jw(OUT / "place.jsonl", pl)
    print(f"stamped {n} of {len(pl)} place rows in {OUT / 'place.jsonl'}")


def place_one(r):
    words = r["words"]
    keyed, notes = [], {}
    for n, copies in r["keys"].items():
        got = [clean_key(c["raw"]) for c in copies]
        alts = [a for a, _ in got if a]
        if not alts:
            notes[int(n)] = got[0][1] if got else "no key"
            continue
        if any([x.lower() for x in a] != [x.lower() for x in alts[0]] for a in alts):
            notes[int(n)] = "copies of the key disagree"
            continue
        keyed.append((int(n), alts[0], next((nt for a, nt in got if a), "")))
    keyed.sort()
    cands = [(n, candidates(words, n, alts)) for n, alts, _ in keyed]
    asg = assign(cands)
    q, placed_pos = [], sorted((c["i"], n) for n, c in asg.items())
    for (n, alts, note), (_, cs) in zip(keyed, cands):
        c = asg.get(n)
        lo = max([c2["i"] + c2["span"] - 1 for n2, c2 in asg.items() if n2 < n] + [-1])
        hi = min([c2["i"] for n2, c2 in asg.items() if n2 > n] + [len(words)])
        others = sorted((x for x in cs if not c or x["i"] != c["i"]), key=lambda x: -x["tot"])
        win = [x for x in others if lo < x["i"] and x["i"] + x["span"] - 1 < hi]
        run = win[0] if win else (others[0] if others else None)
        item = {"n": n, "key": alts, "key_note": note}
        if c:
            margin = c["tot"] - (win[0]["tot"] if win else 0.0)
            unsure_w = any(unsure(w) for w in words[c["i"]:c["i"] + c["span"]])
            alts_w = sorted({a for w in words[c["i"]:c["i"] + c["span"]] for a in (w.get("alts") or [])})
            agree = [w.get("agree", []) for w in words[c["i"]:c["i"] + c["span"]]]
            conf = min(1.0, 0.5 * c["lex"] + 0.3 * min(1.0, max(0.0, margin) / 0.4) + 0.2 * (c["prior"] >= 0.1))
            item.update(span=c["i"], len=c["span"], wrong=c["wrong"], other_reading=alts_w, spelling_unsure=unsure_w, agree=agree,
                        kind=c["kind"], lex=c["lex"], prior=round(c["prior"], 2), conf=round(conf, 2),
                        band=band(c, margin))
        else:
            item.update(span=None, band="unplaced")
        item["runner"] = {"span": run["i"], "wrong": run["wrong"], "tot": round(run["tot"], 2),
                          "in_window": bool(win)} if run else None
        q.append(item)
    for n, why in notes.items():
        q.append({"n": n, "key": [], "key_note": why, "span": None, "band": "no usable key"})
    q.sort(key=lambda x: x["n"])
    return q, cands


def sanity(r, q, cands):
    """Why the keys may not belong to this passage (empty: fine)."""
    flags = []
    keyed = [x for x in q if x["key"]]
    raw = sum(len(v) for v in r["keys"].values())
    foreign = sum(1 for x in q if x["key_note"] not in ("", "caps", "no key"))
    if not keyed:
        return ["no usable key"]
    placed = [x for x in keyed if x["span"] is not None]
    good = [x for x in placed if x["band"] in ("high", "medium")]
    if len(placed) < 0.6 * len(keyed):
        flags.append(f"few placements ({len(placed)} of {len(keyed)} keys)")
    if len(good) < 0.4 * len(keyed):
        flags.append(f"few confident placements ({len(good)} of {len(keyed)})")
    if foreign and foreign >= 0.3 * raw:
        flags.append(f"{foreign} keys look like another section's (letters, MCQ numbers, sentences)")
    # strong matches out of order: each key's best word ignoring order
    best = []
    for (n, cs) in cands:
        strong = [c for c in cs if c["lex"] >= 0.8]
        if strong:
            best.append((n, max(strong, key=lambda c: c["tot"])["i"]))
    inv = sum(1 for a in range(len(best)) for b in range(a + 1, len(best)) if best[a][1] > best[b][1])
    if inv >= 4 and inv > 0.25 * max(1, len(best) * (len(best) - 1) / 2):
        flags.append(f"strong matches out of order ({inv} inversions)")
    on = [x for x in placed if x["prior"] >= 0.1]
    if placed and len(on) < 0.5 * len(placed):
        flags.append(f"placements not on underlined words ({len(on)} of {len(placed)})")
    marks = sorted({m for w in r["words"] for m in marked(w)})
    if marks and r["qnos"] and len([m for m in marks if r["qnos"][0] - 1 <= m <= r["qnos"][-1] + 3]) < 0.5 * len(marks):
        flags.append("the readers' numbers are outside the questions' range")
    if r["ratio"] < 0.85:
        flags.append(f"the two reads' text differs (agreement {r['ratio']})")
    return flags


def place():
    rows = P.jl(OUT / "text.jsonl")
    out, st = [], collections.Counter()
    sigs = collections.defaultdict(list)
    for r in rows:
        q, cands = place_one(r)
        flags = sanity(r, q, cands)
        sig = tuple((x["n"], tuple(k.lower() for k in x["key"])) for x in q if x["key"])
        if len(sig) >= 4:
            sigs[sig].append(r["sec"])
        out.append({"sec": r["sec"], "qnos": r["qnos"], "q": q, "flags": flags, "th": text_hash(r)})
    texts = {r["sec"]: " ".join(nw(w["w"]) for w in r["words"]) for r in rows}
    for sig, ss in sigs.items():
        if len(ss) > 1:
            for o in out:
                if o["sec"] in ss:
                    others = [x for x in ss if x != o["sec"]
                              and difflib.SequenceMatcher(None, texts[x][:600], texts[o["sec"]][:600]).ratio() < 0.8]
                    if others:
                        o["flags"].append(f"same keys as {others[0]} (a different passage)")
    jw(OUT / "place.jsonl", out)
    report(out, rows)


def report(out, rows):
    st = collections.Counter()
    for o in out:
        for x in o["q"]:
            if x["key"]:
                st["keyed"] += 1
                st[x["band"]] += 1
                st["placed"] += x["span"] is not None
                st["placed, spelling_unsure"] += bool(x.get("spelling_unsure"))
            else:
                st["unusable key: " + x["key_note"]] += 1
    full = [o for o in out if o["q"] and all(x["span"] is not None for x in o["q"])
            and {x["n"] for x in o["q"]} >= set(o["qnos"])]
    fullc = [o for o in full if all(x["band"] in ("high", "medium") for x in o["q"])]
    fl = [o for o in out if o["flags"]]
    print(f"keys {st['keyed']}: placed {st['placed']} ({st['placed'] / max(1, st['keyed']):.0%}; earlier matcher 74%, "
          f"1,369 of 1,849), high {st['high']}, medium {st['medium']}, low {st['low']}, unplaced {st['unplaced']}; "
          f"placed on a word the readers spell differently {st['placed, spelling_unsure']}")
    print("unusable keys: " + ", ".join(f"{k[14:]} {v}" for k, v in st.items() if k.startswith("unusable")))
    print(f"sections {len(out)}: every number placed {len(full)} (all high/medium {len(fullc)}), flagged {len(fl)}")
    fc = collections.Counter(re.sub(r"\s*\(.*|\s+\S+$" if False else r"\s*\(.*", "", f) for o in fl for f in o["flags"])
    print("flags: " + ", ".join(f"{k} {v}" for k, v in fc.most_common()))


def mark_text(r, q):
    """The section text with candidate words marked ⟦i|word⟧ (two readings shown a~b)."""
    words = r["words"]
    mk = {i for i, w in enumerate(words) if marked(w)}
    for x in q:
        for c in (x if x.get("span") is not None else None, x.get("runner")):
            if c and c.get("span") is not None:
                mk.update(range(c["span"], c["span"] + (c.get("len") or 1)))
    t, last = [], 0
    for i, w in enumerate(words):
        if i in mk:
            shown = "~".join([w["w"]] + (w.get("alts") or []))
            t.append(r["text"][last:w["s"]] + f"{OPEN}{i}|{shown}{CLOSE}")
            last = w["e"]
    return "".join(t) + r["text"][last:]


PROMPT = """Singapore PSLE English "Editing for Spelling and Grammar". In each passage the exam printed numbered underlined
words, each with ONE spelling or grammar error; the child writes the correct word. The text below was copied from the
page by two readers; words they underlined or a matcher proposes are marked ⟦i|word⟧ (i = word index; a~b = the two
readers saw the word differently: the page shows one of them, usually the misspelt one). For each key number, find the
printed wrong word that the key corrects. Questions follow text order. The keys may belong to another passage: say so in
"doubt". Reply with one JSON line per section and nothing else:
{"sec": "...", "q": [{"n": 39, "span": 12, "wrong": "grualing", "correct": "gruelling", "also": [], "doubt": ""}, ...]}
"span": the index of the wrong word (or null if you cannot place it; then put the wrong word with the 3 words before it in
"context" if it is in the text unmarked). "correct" repeats the key; "also": other corrections equally right (e.g.
"grueling" is not accepted in Singapore; "toward"/"towards" are both right)."""


def pack(per=12):
    rows = {r["sec"]: r for r in P.jl(OUT / "text.jsonl")}
    pl = P.jl(OUT / "place.jsonl")
    items = []
    for o in pl:
        r = rows[o["sec"]]
        keyed = [x for x in o["q"] if x["key"]]
        if not keyed or not any(x["span"] is not None for x in keyed):
            continue
        items.append({"sec": o["sec"], "text": mark_text(r, o["q"]),
                      "keys": [{"n": x["n"], "key": " / ".join(x["key"])} for x in keyed],
                      "matcher": [{"n": x["n"], "span": x["span"], "wrong": x.get("wrong"), "band": x["band"],
                                   "runner": x["runner"] and {"span": x["runner"]["span"], "wrong": x["runner"]["wrong"]}}
                                  for x in keyed],
                      "flags": o["flags"]})
    for f in OUT.glob("pack_*.jsonl"):
        f.unlink()
    n = 0
    for b in range(0, len(items), per):
        n += 1
        jw(OUT / f"pack_{n}.jsonl", items[b:b + per])
    (OUT / "confirm_prompt.txt").write_text(PROMPT + "\n")
    print(f"{len(items)} sections in {n} packs of up to {per} -> {OUT}/pack_N.jsonl (prompt: confirm_prompt.txt; "
          f"{len(pl) - len(items)} sections with nothing placed left out)")


# ------------------------------------------------------------------ final

def resolve_context(words, ctx):
    """The word index a confirmer's context ("... the 3 words before it and the word") names, if exactly one."""
    c = [nw(x) for x in WORD.findall(ctx or "")]
    if not c:
        return None
    ws = [nw(w["w"]) for w in words]
    hits = [i + len(c) - 1 for i in range(len(ws) - len(c) + 1) if ws[i:i + len(c)] == c]
    return hits[0] if len(hits) == 1 else None


def stem_for(text, words, kept):
    """The passage with each kept number's wrong word marked {{n|wrong}}; kept: {n: (span, len, wrong)}."""
    out, last = [], 0
    for n, (i, ln, wrong) in sorted(kept.items(), key=lambda kv: kv[1][0]):
        s, e = words[i]["s"], words[i + ln - 1]["e"]
        out.append(text[last:s] + f"{{{{{n}|{wrong}}}}}")
        last = e
    return "".join(out) + text[last:]


def owner():
    o = collections.defaultdict(lambda: {"add": collections.defaultdict(list), "drop": collections.defaultdict(list),
                                         "wrong": {}, "span": {}, "fix": [], "hold": None})
    for x in P.jl(OUT / "editing_owner.jsonl"):
        d = o[x["sec"]]
        if "fix" in x:
            d["fix"].append(tuple(x["fix"]))
        if "hold" in x:
            d["hold"] = x["hold"]
        if "n" in x:
            n = int(x["n"])
            d["add"][n] += x.get("add", [])
            d["drop"][n] += x.get("drop", [])
            if "wrong" in x:
                d["wrong"][n] = x["wrong"]
            if "span" in x:
                d["span"][n] = int(x["span"])
    return o


def decide(r, pq, conf, own):
    """(kept {n: (span, len, wrong, accept)}, reasons {n: why held}) for one section."""
    words, kept, held = r["words"], {}, {}
    cq = {int(x["n"]): x for x in (conf or {}).get("q", []) if str(x.get("n", "")).isdigit() or isinstance(x.get("n"), int)}
    for x in pq:
        n = x["n"]
        if not x["key"]:
            held[n] = "no usable key: " + x["key_note"]
            continue
        c = cq.get(n)
        span = own["span"].get(n)
        if span is None:
            if x["span"] is None:
                held[n] = "matcher could not place it"
                continue
            if c is None:
                held[n] = "no confirmer answer"
                continue
            cs = c.get("span")
            if cs is None and c.get("context"):
                cs = resolve_context(words, c["context"])
            if cs is None or int(cs) != x["span"]:
                held[n] = "confirmer places it elsewhere" if cs is not None else "confirmer could not place it"
                continue
            if (c.get("doubt") or "").strip():
                held[n] = "confirmer doubts the key"
                continue
            if nw(c.get("correct")) not in {nw(k) for k in x["key"]}:
                held[n] = "confirmer changed the key"
                continue
            span = x["span"]
        ln = x.get("len", 1) if span == x["span"] else 1
        ws = words[span:span + ln]
        wrong = own["wrong"].get(n)
        if wrong is None:
            if any(unsure(w) for w in ws):
                held[n] = "spelling_unsure (the readers spell the word differently)"
                continue
            wrong = r["text"][ws[0]["s"]:ws[-1]["e"]]
        gone = {d.lower() for d in own["drop"].get(n, [])}
        also = [a for a in ((c or {}).get("also") or []) if isinstance(a, str) and a.strip()]
        acc = [a for a in dict.fromkeys(list(x["key"]) + also) if a.lower() not in gone]
        for a in own["add"].get(n, []):
            if a.lower() not in {y.lower() for y in acc}:
                acc.append(a)
        if not acc:
            held[n] = "the owner dropped every answer"
            continue
        if nw(wrong) in {nw(a) for a in acc}:
            held[n] = "the printed word equals an accepted answer"
            continue
        kept[n] = (span, ln, wrong, acc)
    return kept, held


RELEASING = ("NOTE_ONLY", "UNSURE_SPELLING", "ALSO_RIGHT")  # triage classes that let a confirmer doubt through


def live_triage(tri, v):
    """The triage rows of one section that still apply: a row carries the confirmer doubt it classified, and applies only
    while the confirmer's doubt for that number is the same text (a re-run confirmer with another doubt is untriaged)."""
    cur = {}
    for x in (v or {}).get("q", []):
        try:
            cur[int(x.get("n"))] = " ".join(str(x.get("doubt") or "").split())
        except (TypeError, ValueError):
            pass
    return {n: t for n, t in (tri or {}).items() if " ".join(str(t.get("doubt") or "").split()) == cur.get(n, "")}


HARD = ("look like another section", "no usable key", "same keys as")


def hard_flag(f):
    """A sanity flag no page read can settle: the keys are not this passage's."""
    return any(h in f for h in HARD)


def decide_v(r, pq, v, own, tri=None, passed=None):
    """Like decide, from a page-read confirmer (vout): a number is kept when the confirmer's span is the matcher's (or a
    clear other span the key fits by the matching rules), the confirmer is sure of the printed spelling, the printed word
    is not the key, and at least one reader spelled it that way (else it waits for a second page read).
    tri: the triage sidecar of this section {n: row} (class of each non-empty doubt; None = every doubt holds, as before).
    A pq entry with "shifted" got its key from another box number (KEY_SHIFTED): the key must fit the page word.
    passed: a Counter that counts the doubts the triage let through, per class."""
    words, kept, held = r["words"], {}, {}
    cq = {}
    for x in (v or {}).get("q", []):
        try:
            cq[int(x.get("n"))] = x
        except (TypeError, ValueError):
            pass
    triage_also = []
    for x in pq:
        n = x["n"]
        tc = (tri or {}).get(n)
        cl = tc["class"] if tc else None
        shifted = bool(x.get("shifted"))
        if cl == "NOT_EDITING":  # the reader says this number is not an Editing question on this page
            if passed is not None:
                passed["NOT_EDITING"] += 1
            continue
        if not x["key"]:
            held[n] = "no usable key: " + x["key_note"]
            continue
        c = cq.get(n)
        span, ln = own["span"].get(n), 1
        if c is None and span is None:
            held[n] = "no confirmer answer"
            continue
        if c is not None and c.get("missing_word"):
            held[n] = "a missing-word box"
            continue
        triage_also = []
        if c is not None and (c.get("doubt") or "").strip() and not shifted:
            if tri is None or cl is None or cl not in RELEASING:  # KEY_WRONG, KEY_SHIFTED and any unknown class hold
                held[n] = "confirmer doubts the key"
                continue
            if cl == "UNSURE_SPELLING" and n not in own["wrong"]:
                held[n] = "confirmer unsure of the printed spelling"
                continue
            if cl == "ALSO_RIGHT":
                triage_also = [a for a in (tc.get("also") or []) if isinstance(a, str) and a.strip()]
            if passed is not None and cl != "UNSURE_SPELLING":
                passed[cl] += 1
        if c is not None and not shifted and nw(c.get("correct")) not in {nw(k) for k in x["key"]}:
            held[n] = "confirmer changed the key"
            continue
        if span is None:
            cs = c.get("span")
            if cs is None and c.get("context"):
                cs = resolve_context(words, c["context"])
            try:
                cs = int(cs) if cs is not None else None
            except (TypeError, ValueError):
                cs = None
            if cs is None or not 0 <= cs < len(words):
                held[n] = "confirmer could not place it"
                continue
            if cs == x["span"] and not shifted:
                span, ln = cs, x.get("len", 1)
            else:
                fit = max(lex(words, cs, 1, k)[0] for k in x["key"])  # the word there, as the readers spelled it
                if fit < 0.45:
                    held[n] = ("a key from another box number does not fit this word" if shifted else
                               "confirmer places it elsewhere and the key does not fit there")
                    continue
                span = cs
        ws = words[span:span + ln]
        wrong = own["wrong"].get(n)
        if wrong is None:
            if c is None or c.get("sure") is not True or not (c.get("printed") or "").strip():
                held[n] = "confirmer unsure of the printed spelling"
                continue
            pr = " ".join(c["printed"].split()).strip(" .,;:!?\"'“”‘’()")
            seen = {" ".join(rd) for rd in [[w["w"] for w in ws]]} | \
                {" ".join(w["reads"].get(lb, "") for w in ws) for lb in READERS if all(lb in w.get("reads", {}) for w in ws)} | \
                {" ".join(a) for a in zip(*[(w.get("alts") or []) for w in ws])}
            # a second, independent page read (OCRia-1, 28 Nov 2026: "printed2") that reads the same spelling at the same
            # word settles it, as two readers would
            if pr not in seen and nw(c.get("printed2")) != nw(pr):
                held[n] = "spelling_unsure (the page read matches no reader: a second page read)"
                continue
            wrong = pr
        gone = {d.lower() for d in own["drop"].get(n, [])}
        also = [] if shifted else [a for a in ((c or {}).get("also") or []) if isinstance(a, str) and a.strip()]
        also += triage_also
        acc = [a for a in dict.fromkeys(list(x["key"]) + also) if a.lower() not in gone]
        for a in own["add"].get(n, []):
            if a.lower() not in {y.lower() for y in acc}:
                acc.append(a)
        if not acc:
            held[n] = "the owner dropped every answer"
            continue
        if nw(wrong) in {nw(a) for a in acc}:
            held[n] = "the printed word equals an accepted answer"
            continue
        kept[n] = (span, ln, wrong, acc)
    return kept, held


def page_files(r):
    """The page images of a section's questions (the page before too when the passage may start there)."""
    Q = P.questions()
    qp = sorted({p for v in r["keys"].values() for c in v for p in (Q.get(c["id"]) or {}).get("pages") or []})
    qp = qp or r["pages"]
    base = TMP / "pastpapers" / "english" / str(r["year"]) / "pages"
    extra = [qp[0] - 1] if qp and qp[0] - 1 in r["pages"] else []
    return [base / f"p{p:04d}.jpg" for p in qp], [base / f"p{p:04d}.jpg" for p in extra]


def readable(p):
    from PIL import Image
    try:
        with Image.open(p) as im:
            im.verify()
        return True
    except Exception:
        return False


def vpack(per=8):
    """Page-read packs: every section with a placed key whose keys are its own (hard flags left out), the most uncertain
    first. OUT/vpack_N.jsonl; the brief is OUT/VCONFIRM.md (no crop boxes exist for Editing: whole pages)."""
    rows = {r["sec"]: r for r in P.jl(OUT / "text.jsonl")}
    items, missing = [], []
    for o in P.jl(OUT / "place.jsonl"):
        r = rows[o["sec"]]
        keyed = [x for x in o["q"] if x["key"]]
        if not any(x["span"] is not None for x in keyed) or any(hard_flag(f) for f in o["flags"]):
            continue
        pages, extra = page_files(r)
        bad = [str(p) for p in pages + extra if not readable(p)]
        if bad:
            missing += bad
            continue
        unc = sum({"high": 0, "medium": 1, "low": 2, "unplaced": 3}.get(x["band"], 3) for x in keyed) + \
            sum(2 for x in keyed if x.get("spelling_unsure")) + 3 * len(o["flags"])
        q = []
        for x in sorted(o["q"], key=lambda x: x["n"]):
            w = r["words"][x["span"]] if x.get("span") is not None else None
            q.append({"n": x["n"], "key": " / ".join(x["key"]) or None, "key_note": x["key_note"] or None,
                      "matcher": None if w is None else {"span": x["span"], "word": x["wrong"], "confidence": x["band"],
                                                         "readers": w.get("reads", {})}})
        items.append({"sec": o["sec"], "pages": [str(p) for p in pages], "page_before": [str(p) for p in extra],
                      "uncertainty": unc, "flags": o["flags"], "text": mark_text(r, o["q"]), "questions": q})
    items.sort(key=lambda x: -x["uncertainty"])
    for f in OUT.glob("vpack_*.jsonl"):
        f.unlink()
    n = 0
    for b in range(0, len(items), per):
        n += 1
        jw(OUT / f"vpack_{n}.jsonl", items[b:b + per])
    (OUT / "VCONFIRM.md").write_text(VBRIEF)
    print(f"{len(items)} sections in {n} vision packs of up to {per} -> {OUT}/vpack_N.jsonl; brief {OUT / 'VCONFIRM.md'}; "
          f"{sum(len(x['pages']) + len(x['page_before']) for x in items)} page images, all readable; "
          f"unreadable or missing: {len(missing)} {missing[:5]}")


VBRIEF = """# Editing page-read confirmation: pack N

You confirm Singapore PSLE English "Editing for Spelling and Grammar" questions against the exam page scans. In each
passage the paper prints numbered answer boxes, each belonging to ONE underlined word that has a spelling or grammar
error. Our text was copied by machine readers, which often put a number on the wrong word and often "correct" a
misspelling while copying. The page is the only truth.

Input: `/data/alvin/tmp/cookie-codex/editing/vpack_N.jsonl`, one JSON object per line (one section each):
- `pages`: page image paths (absolute). `page_before`: the previous page, only to look at if the passage starts there.
- `text`: the passage as copied; candidate words are marked `⟦i|word⟧` where `i` is the word index (`a~b` = readers
  disagreed). Any word's index can be given; unmarked words have indices too, but use `context` for them (below).
- `questions`: per number `n`, the school `key` (the corrected word), and `matcher` (the word we think it is: `span`,
  `word`, `confidence`, and `readers`: each machine reader's spelling).

For every section:
1. Read every image in `pages` with the Read tool (zoom is not available; read carefully).
2. For each question number, find its number and answer box on the page and the underlined word it belongs to (the box
   is usually printed just above or beside its word; follow the page, not the order of our text).
3. Copy that underlined word LETTER BY LETTER exactly as printed, misspelling included. Never correct it, never
   normalise it. If any letter is unclear, give your best reading and set `"sure": false`.
4. Say whether the matcher's placement is right; give the word index `span` from the text (the `⟦i|...⟧` index of
   that word). If the word is in the text but not marked, set `"span": null` and give `"context"`: the 3 words before
   it plus the word, exactly as in the text. If the text lacks the word entirely, `"span": null` and explain in `doubt`.
5. `doubt`: write the reason when the key does not fit the underlined word (wrong passage, wrong number, a different
   correction is needed); else "". `also`: other corrections that are equally right (rare).
6. `missing_word`: true when the box marks a missing word (no underlined word, a caret or gap) rather than a wrong word.
7. Section level: `numbers_on_page`: every question number printed in this passage. `unnumbered`: every underlined
   word on the page that has no question number (exact spelling), e.g. a worked example; [] if none.

Write `/data/alvin/tmp/cookie-codex/editing/vout_N.jsonl`, one JSON line per section, nothing else:
{"sec": "<sec>", "numbers_on_page": [39, 40, ...], "unnumbered": [],
 "q": [{"n": 39, "span": 24, "printed": "grualing", "sure": true, "placement_right": true, "wrong": "grualing",
        "correct": "gruelling", "also": [], "doubt": "", "missing_word": false}, ...]}
One object per number in `questions` (also those with no key or no matcher word: give `printed` and `span` anyway;
`correct` = the key, or "" when there is no key). `wrong` = `printed`. Use plain ASCII quotes in JSON.
Do not edit any other file. Report at the end: sections done, numbers where the matcher was wrong, numbers not sure.
"""


def load_triage(legacy=False):
    """The two triage sidecars (OUT/triage.jsonl per number, OUT/triage_sec.jsonl per section item). {} when legacy."""
    num, sec = collections.defaultdict(dict), collections.defaultdict(dict)
    if legacy:
        return num, sec
    for x in P.jl(OUT / "triage.jsonl") if (OUT / "triage.jsonl").exists() else []:
        num[x["sec"]][int(x["n"])] = x
    for x in P.jl(OUT / "triage_sec.jsonl") if (OUT / "triage_sec.jsonl").exists() else []:
        sec[x["sec"]][(x["kind"], str(x["item"]))] = x["class"]
    return num, sec


def shift_keys(pq, shifts):
    """KEY_SHIFTED: pq with each shifted key moved to the box number the reader says it belongs to. shifts {src: true_n}.
    A source box that receives nothing has no key; a box that receives one is marked "shifted". (None, why) when two keys
    claim one box or a key claims a box the passage does not have."""
    by = {x["n"]: x for x in pq}
    dest = collections.defaultdict(list)
    for src, t in shifts.items():
        dest[t].append(src)
    if any(len(v) > 1 for v in dest.values()):
        return None, "two shifted keys claim one box"
    if any(t not in by for t in dest) or any(s_ not in by for s_ in shifts):
        return None, "a shifted key names a box the passage has no question for"
    out = []
    for x in pq:
        y = dict(x)
        if x["n"] in dest:
            y.update(key=list(by[dest[x["n"]][0]]["key"]), span=None, shifted=True)
        elif x["n"] in shifts:
            y.update(key=[], key_note="its key belongs to another box number")
        out.append(y)
    return out, ""


def apply_text_fix(stem, fix):
    """A page-checked text (text_fixes.jsonl row) replaces a stem only if its marks (n, wrong word, in order) are
    identical and the words outside the marks change by a plausible amount. Returns (stem, reason or None)."""
    if fix["status"] == "hold":
        return stem, "text does not match the page"
    new = fix["text"]
    if [(int(n), w) for n, w in P.UNDER.findall(new)] != [(int(n), w) for n, w in P.UNDER.findall(stem)]:
        return stem, "text fix marks differ"
    a, b = len(P.UNDER.sub(" ", stem).split()), len(P.UNDER.sub(" ", new).split())
    if not a or abs(a - b) > 0.4 * a:
        return stem, "text fix changes too many words"
    return new, None


def final(legacy=False, write=True):
    """legacy=True: ignore the triage sidecars (the rules before the triage), to report before/after. Returns stats."""
    import glob
    from load_pp import pp_id, LEVEL, set_id
    rows = {r["sec"]: r for r in P.jl(OUT / "text.jsonl")}
    pl = {o["sec"]: o for o in P.jl(OUT / "place.jsonl")}
    if any("th" not in o for o in pl.values()):
        sys.exit("place.jsonl has no text stamp: run `editing.py stamp-place` once (only if it was built from this text.jsonl), "
                 "or re-run `place`")
    conf, vconf = {}, {}
    for f in sorted(glob.glob(str(OUT / "out_*.jsonl"))):
        for x in P.jl(f):
            conf[x.get("sec")] = x
    for f in sorted(glob.glob(str(OUT / "vout_*.jsonl"))):  # the page-read confirmers win over the text-only ones
        for x in P.jl(f):
            vconf[x.get("sec")] = x
    own = owner()
    Q = P.questions()
    tri_n, tri_s = load_triage(legacy)
    fixes = {x["sec"]: x for x in P.jl(OUT / "text_fixes.jsonl")} if (OUT / "text_fixes.jsonl").exists() else {}
    n_fixed = 0
    n_lower = [0]
    passed, rel_sec, in_complete = collections.Counter(), collections.Counter(), collections.Counter()
    out, why, nwhy, seen, grp_sec = [], collections.Counter(), collections.Counter(), set(), {}
    for sec, o in sorted(pl.items()):
        r, ow = rows[sec], own[sec]
        if o["th"] != text_hash(r):
            why["held: place.jsonl was built from another text.jsonl (re-run place)"] += 1
            continue
        if ow["hold"]:
            why["held by the owner"] += 1
            continue
        v = vconf.get(sec)
        # a page read settles the readers' disagreements; keys of another section it cannot
        flags = [f for f in o["flags"] if not v or hard_flag(f)]
        if flags and not any(o2 for o2 in ow["span"].values()):
            why["held: sanity flag (" + re.sub(r"\s*\(.*", "", flags[0]) + ")"] += 1
            continue
        nums = sorted(set(r["qnos"]) | {x["n"] for x in o["q"]})
        tri = live_triage(tri_n.get(sec), vconf.get(sec)) or None
        if tri:  # numbers the reader says are not Editing questions on this page (blanks of the cloze next door, ...)
            nums = [n for n in nums if (tri.get(n) or {}).get("class") != "NOT_EDITING"]
        if v:
            extra = [n for n in v.get("numbers_on_page") or [] if isinstance(n, int) and n not in nums
                     and (tri or {}).get(n, {}).get("class") != "NOT_EDITING"]
            items = [("word", str(u)) for u in v.get("unnumbered") or []] + [("number", str(n)) for n in extra]
            real = [it for it in items if tri_s.get(sec, {}).get(it) != "IGNORE"]
            if real:
                why["held: the page shows an underlined word or number that is not asked"] += 1
                continue
            if items:
                rel_sec["IGNORE"] += 1
        else:
            marks = {m for w in r["words"] for m in marked(w)}
            if marks and min(marks) < nums[0]:
                # an underlined word before the first question: an example or a question the first read missed;
                # either way the passage would show an error that is not asked
                why["held: a word is underlined before the first question"] += 1
                continue
        pq, bad = o["q"], ""
        shifts = {n_: int(t_["true_n"]) for n_, t_ in (tri or {}).items() if t_["class"] == "KEY_SHIFTED"}
        if shifts and v:
            pq, bad = shift_keys(o["q"], shifts)
        if bad:
            why["held: " + bad] += 1
            continue
        pass_sec = collections.Counter()
        kept, held = decide_v(r, pq, v, ow, tri, pass_sec) if v else decide(r, o["q"], conf.get(sec), ow)
        if shifts and v and pq is not o["q"]:
            pass_sec["KEY_SHIFTED"] += sum(1 for x in pq if x.get("shifted") and x["n"] in kept)
        for n in nums:
            if n not in kept and n not in held:
                held[n] = "no key for this number"
        for v in held.values():
            nwhy[v] += 1
        if held:
            why["held: a number not settled"] += 1
            continue
        passed.update(pass_sec)
        if any(it for it in tri_s.get(sec, {}).values() if it == "IGNORE"):
            rel_sec["IGNORE (section reached the end)"] += 1
        t = r["text"]
        try:
            for old, new in ow["fix"]:
                assert t.count(old) == 1, f"{sec}: text fix {old!r} must match exactly once"
                at = t.index(old)
                assert not any(at < words_e and at + len(old) > words_s for (i, ln, _, _) in kept.values()
                               for words_s, words_e in [(r["words"][i]["s"], r["words"][i + ln - 1]["e"])]), \
                    f"{sec}: text fix {old!r} touches a marked word"
        except AssertionError as e:
            print("WARNING", e)
            why["held: owner text fix does not apply"] += 1
            continue
        stem = stem_for(t, r["words"], {n: v[:3] for n, v in kept.items()})
        for old, new in ow["fix"]:
            stem = stem.replace(old, new)
        stem_orig = stem
        if sec in fixes:
            stem, bad = apply_text_fix(stem, fixes[sec])
            if bad:
                why["held: " + bad] += 1
                continue
            n_fixed += stem != stem_orig
        sig = P.plain(stem)
        if sig in seen:
            why["held: same passage in another paper"] += 1
            continue
        seen.add(sig)
        grp = None
        for n in nums:
            qid = next((i["id"] for i in r["keys"].get(str(n), [])), None)
            q = Q.get(qid) or {}
            if grp is None:
                base_g = set_id(q, "ed")
                grp, k = base_g, 2
                while grp in grp_sec and grp_sec[grp] != sec:
                    grp, k = f"{base_g}-{k}", k + 1
                grp_sec[grp] = sec
            meta = P.own_meta(qid)
            out.append({"id": pp_id(qid), "src_id": qid, "subject": "english", "subtopic": "eng-editing",
                        "level": meta["level"], "difficulty": meta["difficulty"], "pattern": None, "stem": stem,
                        "options": [], "answer": 0, "crops": [], "year": r["year"], "school": meta["school"],
                        "paper": meta["paper"], "qno": n, "marks": meta["marks"], "blind_src": "matcher+confirmer",
                        "kind": "typed", "accept": case_accept(kept[n][3], kept[n][2], n_lower), "scaffold": None, "grp": grp, "seq": n, "sec": sec,
                        "wrong": kept[n][2]})
        why["complete"] += 1
        for n in nums:
            c_ = (tri or {}).get(n, {}).get("class")
            if c_:
                in_complete[c_] += 1
    # the checks: one passage per set; every marked number in a stem is one of its set's questions
    asked = collections.defaultdict(set)
    for x in out:
        asked[x["grp"]].add(x["seq"])
    for x in out:
        shown = {int(n) for n, _ in P.UNDER.findall(x["stem"])}
        assert shown == asked[x["grp"]], f"{x['id']}: marked {sorted(shown)} but asked {sorted(asked[x['grp']])}"
    d = SHIP / "english"
    stats = {"fixed": n_fixed, "complete": sorted({x["sec"] for x in out}), "questions": len(out), "why": why, "nwhy": nwhy,
             "passed": passed, "rel_sec": rel_sec, "in_complete": in_complete}
    if not write:
        return stats
    jw(d / "selected.jsonl", out)
    print("sections: " + ", ".join(f"{k} {v}" for k, v in why.most_common()))
    print("numbers held: " + ", ".join(f"{k} {v}" for k, v in nwhy.most_common()))
    print(f"page-checked texts replaced: {n_fixed}; passages held for the text: "
          f"{sum(v for k, v in why.items() if k.startswith('held: text'))}")
    print(f"answers lower-cased to follow the printed wrong word: {n_lower[0]}")
    print(f"{len(out)} questions in {len(set(x['grp'] for x in out))} complete passages -> {d / 'selected.jsonl'}")
    if not legacy:
        old = final(legacy=True, write=False)
        new_secs = sorted(set(stats["complete"]) - set(old["complete"]))
        print("triage released, doubts let through per class (numbers reached): "
              + (", ".join(f"{k} {v}" for k, v in sorted(passed.items())) or "none"))
        print("triage released, section items ignored: " + (", ".join(f"{k} {v}" for k, v in sorted(rel_sec.items())) or "none"))
        print(f"before (no triage): {len(old['complete'])} passages, {old['questions']} questions; after: "
              f"{len(stats['complete'])} passages, {stats['questions']} questions; newly complete {len(new_secs)}: {new_secs}")
        print("numbers with a triaged doubt inside complete passages, per class: "
              + (", ".join(f"{k} {v}" for k, v in sorted(in_complete.items())) or "none"))


_CAPWORD = re.compile(r"^[A-Z][a-z'\u2019-]+$")


def case_accept(acc, wrong, cnt=None):
    """An accepted answer that is one capitalised word follows a lower-case printed wrong word (the school key
    lists answers capitalised); everything else is untouched. Duplicates made by this are dropped."""
    if not wrong or not wrong[0].islower():
        return acc
    out = []
    for a in acc:
        if _CAPWORD.match(a):
            a = a[0].lower() + a[1:]
            if cnt is not None:
                cnt[0] += 1
        if a not in out:
            out.append(a)
    return out


# ------------------------------------------------------------------ selftest

def selftest():
    assert case_accept(["Zorble", "zorble"], "blorf") == ["zorble"] and case_accept(["Zorble"], "Blorf") == ["Zorble"]
    assert case_accept(["I", "NASA", "Zo Blor", "Zorb's"], "blorf") == ["I", "NASA", "Zo Blor", "zorb's"]
    assert case_accept(["Zorble"], "") == ["Zorble"]
    st = "A {{1|grate}} day {{2|an}} more."
    ok = {"status": "verified", "text": "A {{1|grate}} day {{2|an}} more!"}
    assert apply_text_fix(st, ok) == (ok["text"], None)
    assert apply_text_fix(st, {"status": "hold", "text": ""})[1] == "text does not match the page"
    assert apply_text_fix(st, {"status": "corrected", "text": "A {{1|great}} day {{2|an}} more."})[1] == "text fix marks differ"
    assert apply_text_fix(st, {"status": "verified", "text": "{{1|grate}} {{2|an}}"})[1] == "text fix changes too many words"
    t, m = strip_marks("A {{3|grate}} day and {{4|}} more.")
    assert t == "A grate day and  more." and m == [(3, 2, 7), (4, 16, 16)]
    assert osa("variaty", "variety") == 1 and osa("recieve", "receive") == 1, "a swap of two letters counts once"
    assert squeeze("occured") == squeeze("occurred") and phon("fone") == phon("phone")
    assert lex1("recieve", "receive")[0] >= 0.8 and lex1("tooks", "took")[0] >= 0.8
    assert lex1("take", "took") == (0.85, "form") and lex1("child", "children")[1] == "form"
    assert lex1("is", "are")[1] == "swap" and lex1("in", "of")[1] == "swap" and lex1("their", "there")[1] == "swap"
    assert lex1("happily", "happiness")[0] >= 0.75, "part of speech"
    assert lex1("table", "receive")[0] == 0 and lex1("on", "receive")[0] == 0
    assert clean_key("(gruelling)") == (["gruelling"], "") and clean_key("attempt / attempts")[0] == ["attempt", "attempts"]
    assert clean_key("N")[0] == [] and clean_key("a")[0] == ["a"] and lex1("lie", "lay")[1] == "swap"
    assert clean_key("G (during)")[0] == [] and clean_key("3")[0] == [] and clean_key("G tense")[0] == []
    assert clean_key("Siti, whose painting was chosen, was very delighted.")[0] == []
    assert clean_key("(ITS)") == (["its"], "caps") and clean_key("be (become - not accepted)")[0] == ["be"]
    # two reads: same words, one read fixed a misspelling while copying, numbers one word late
    p1 = "We had a {{5|grate}} time. We {{6|go}} home {{7|quikly}} after the {{8|show}}."
    p2 = "We had a {{5|grate}} time. We {{6|go}} home {{7|quickly}} after the {{8|show}}. "
    text_, words, ratio, gap = merge_reads({"1": p1, "2": p2})
    assert text_.startswith("We had a grate time.") and not gap and ratio > 0.9
    qk = next(w for w in words if w["w"] == "quikly")
    assert qk["alts"] == ["quickly"] and unsure(qk), "two spellings, one each: spelling_unsure"
    assert next(w for w in words if w["w"] == "grate")["agree"] == ["1", "2"]
    # a third read: two of three give the same spelling, so it is trusted (and shown, even when the base read differs)
    t4, w4, _, _ = merge_reads({"1": p1, "2": p2, "3": p1.replace("{{7|quikly}}", "{{6|quikly}}")})
    q4 = next(w for w in w4 if w["w"] == "quikly")
    assert q4["trusted"] and q4["agree"] == ["1", "3"] and q4["m3"] == [6]
    t5, w5, _, _ = merge_reads({"1": p2, "2": p1, "3": p1})
    assert "home quikly after" in t5 and next(w for w in w5 if w["w"] == "quikly")["agree"] == ["2", "3"]
    assert t5[w5[7]["s"]:w5[7]["e"]] == w5[7]["w"], "offsets follow the shown spelling"
    t6, w6, _, _ = merge_reads({"3": "Only {{2|one}} read."})
    assert t6 == "Only one read." and all(unsure(w) for w in w6), "one read is never enough"
    # a word only one read has is put in, and the marks map through
    t3, w3, _, _ = merge("I went {{9|too}} the shop.", "I then went {{9|too}} the shop.")
    assert "then" in t3 and next(w for w in w3 if w["w"] == "then")["src"] == "one"
    assert next(w for w in w3 if w["w"] == "too")["m2"] == [9]
    # placing: keys 4..7 with the readers' numbers one late; order decides between two "the"s
    r = {"words": words, "text": text_, "qnos": [4, 5, 6, 7], "ratio": ratio,
         "keys": {"4": [{"id": "a", "raw": "great"}], "5": [{"id": "b", "raw": "went"}],
                  "6": [{"id": "c", "raw": "quickly"}], "7": [{"id": "d", "raw": "(a)"}]}}
    q, cands = place_one(r)
    got = {x["n"]: x.get("wrong") for x in q}
    assert got == {4: "grate", 5: "go", 6: "quikly", 7: "the"}, got
    assert q[2]["spelling_unsure"] and not q[0]["spelling_unsure"]
    assert assign([(1, [{"i": 5, "span": 1, "tot": 1.0}]), (2, [{"i": 3, "span": 1, "tot": 0.9},
                                                               {"i": 8, "span": 1, "tot": 0.5}])]) \
        == {1: {"i": 5, "span": 1, "tot": 1.0}, 2: {"i": 8, "span": 1, "tot": 0.5}}, "question order = text order"
    assert sanity(r, q, cands) == [], sanity(r, q, cands)
    wrongkeys = dict(r, keys={str(n): [{"id": "x", "raw": k}] for n, k in zip(range(4, 8), ["photosynthesis", "B", "1", "C (and)"])})
    q2, c2 = place_one(wrongkeys)
    assert sanity(wrongkeys, q2, c2), "keys of another section are flagged"
    # final: matcher and confirmer agree; a spelling_unsure word holds unless the owner gives the printed spelling
    conf = {"q": [{"n": 4, "span": q[0]["span"], "correct": "great"}, {"n": 5, "span": q[1]["span"], "correct": "went"},
                  {"n": 6, "span": q[2]["span"], "correct": "quickly"}, {"n": 7, "span": None, "context": "home quikly after the",
                                                                         "correct": "a", "also": []}]}
    blank = {"add": {}, "drop": {}, "wrong": {}, "span": {}, "fix": [], "hold": None}
    kept, held = decide(r, q, conf, blank)
    assert set(kept) == {4, 5, 7} and "spelling_unsure" in held[6], (kept, held)
    kept, held = decide(r, q, conf, dict(blank, wrong={6: "quikly"}, add={4: ["fantastic"]}))
    assert not held and kept[4][3] == ["great", "fantastic"]
    stem = stem_for(text_, words, {n: v[:3] for n, v in kept.items()})
    assert stem.startswith("We had a {{4|grate}} time. We {{5|go}} home {{6|quikly}} after {{7|the}} show.")
    assert P.markers(stem, "under") == {4: "grate", 5: "go", 6: "quikly", 7: "the"}
    _, held = decide(r, q, dict(conf, q=[dict(conf["q"][0], doubt="belongs to another passage")] + conf["q"][1:]), blank)
    assert held[4] == "confirmer doubts the key"
    _, held = decide(r, q, dict(conf, q=[dict(conf["q"][0], span=q[0]["span"] + 1)] + conf["q"][1:]), blank)
    assert held[4] == "confirmer places it elsewhere"
    m = mark_text(r, q)
    assert f"{OPEN}{q[2]['span']}|quikly~quickly{CLOSE}" in m
    # page-read confirmers (vout)
    sp = {x["n"]: x["span"] for x in q}
    v = {"q": [{"n": 4, "span": sp[4], "printed": "grate", "sure": True, "correct": "great"},
               {"n": 5, "span": sp[5], "printed": "go", "sure": True, "correct": "went"},
               {"n": 6, "span": sp[6], "printed": "quikly,", "sure": True, "correct": "quickly"},
               {"n": 7, "span": sp[7], "printed": "the", "sure": True, "correct": "a"}]}
    kept, held = decide_v(r, q, v, blank)
    assert not held and kept[6][2] == "quikly", (kept, held)
    def vh(n, **kw):
        return decide_v(r, q, dict(v, q=[dict(x, **kw) if x["n"] == n else x for x in v["q"]]), blank)[1].get(n)
    assert vh(6, printed="quickly") == "the printed word equals an accepted answer", "a reader-corrected word stays held"
    assert vh(6, printed="quikley").startswith("spelling_unsure"), "a page read no reader shares waits for a second read"
    assert vh(6, sure=False) == "confirmer unsure of the printed spelling"
    assert vh(4, missing_word=True) == "a missing-word box" and vh(4, doubt="another passage") == "confirmer doubts the key"
    assert vh(5, span=sp[5] + 2).startswith("confirmer places it elsewhere"), "the key must fit a different span"
    other = [i for i, w in enumerate(r["words"]) if w["w"] == "the"]
    assert vh(7, span=other[0]) is None, "a clear different span the key fits is taken"
    # triage sidecar: a doubt is a note, a key doubt, an unsure letter, or another section's number
    def tv(n, cl, doubt="a note", extra=None, **kw):
        vv = dict(v, q=[dict(x, doubt=doubt) if x["n"] == n else x for x in v["q"]])
        row = dict({"class": cl}, **kw)
        pass_ = collections.Counter()
        k_, h_ = decide_v(r, q, vv, blank, {n: row, **(extra or {})}, pass_)
        return k_, h_, pass_
    k_, h_, p_ = tv(4, "NOTE_ONLY")
    assert not h_ and p_["NOTE_ONLY"] == 1, "a note is no key doubt"
    assert tv(4, "KEY_WRONG")[1][4] == "confirmer doubts the key"
    assert tv(4, "UNSURE_SPELLING")[1][4] == "confirmer unsure of the printed spelling"
    assert tv(4, "KEY_SHIFTED")[1][4] == "confirmer doubts the key", "a shifted key without the shift applied holds"
    k_, h_, _ = tv(4, "ALSO_RIGHT", also=["fantastic"])
    assert not h_ and k_[4][3] == ["great", "fantastic"], "the extra answer is accepted"
    assert decide_v(r, q, dict(v, q=[dict(v["q"][0], doubt="x")] + v["q"][1:]), blank)[1][4] == "confirmer doubts the key", "no triage: as before"
    k_, h_, _ = tv(4, "NOT_EDITING")
    assert 4 not in k_ and 4 not in h_, "a number that is not an Editing question here is dropped"
    # KEY_SHIFTED: the key of 4 belongs to box 5 and the key of 5 to box 4; the page words fit the swapped keys
    sw, why_ = shift_keys(q, {4: 5, 5: 4})
    assert not why_ and sw[0]["key"] == ["went"] and sw[1]["key"] == ["great"] and sw[0]["shifted"] and sw[0]["span"] is None
    vs = dict(v, q=[dict(v["q"][0], span=sp[5], printed="go", correct="great", doubt="its key is box 5's"),
                    dict(v["q"][1], span=sp[4], printed="grate", correct="went", doubt="its key is box 4's")] + v["q"][2:])
    k_, h_ = decide_v(r, sw, vs, blank, {4: {"class": "KEY_SHIFTED"}, 5: {"class": "KEY_SHIFTED"}})[:2]
    assert not h_ and k_[4][2] == "go" and k_[4][3] == ["went"] and k_[5][3] == ["great"], (k_, h_)
    bad_, _ = shift_keys(q, {4: 5, 6: 5})
    assert bad_ is None, "two keys on one box"
    assert shift_keys(q, {4: 99})[0] is None, "a box the passage lacks"
    sw2, _ = shift_keys(q, {4: 5})  # the key of 5 goes nowhere: box 4 has no key
    assert decide_v(r, sw2, vs, blank, {4: {"class": "KEY_SHIFTED"}})[1][4].startswith("no usable key")
    assert decide_v(r, sw2, v, blank)[1][5] == "a key from another box number does not fit this word", "the key must fit the page word"
    assert hard_flag("6 keys look like another section's (letters)") and not hard_flag("the two reads' text differs (0.5)")
    # finding 2: a triage row applies only to the doubt it classified; an unknown class holds
    vq = {"q": [{"n": 4, "doubt": "key  looks  wrong"}, {"n": 5, "doubt": ""}]}
    tr = {4: {"class": "NOTE_ONLY", "doubt": "key looks wrong"}, 5: {"class": "NOTE_ONLY", "doubt": "other"}, 6: {"class": "X", "doubt": "z"}}
    assert set(live_triage(tr, vq)) == {4}, "same text (whitespace aside) applies; a different or unmatched doubt does not"
    assert live_triage(tr, None) == {} and live_triage(None, vq) == {}
    assert "NOTE_ONLY" in RELEASING and "KEY_WRONG" not in RELEASING and "NEW_CLASS" not in RELEASING
    # finding 3: the place stamp follows the words
    ra = {"words": [{"w": "a"}, {"w": "b"}]}
    assert text_hash(ra) == text_hash({"words": [{"w": "a"}, {"w": "b"}]}) != text_hash({"words": [{"w": "a"}, {"w": "c"}]})
    explain_selftest()
    print("editing selftest ok")


# ------------------------------------------------------------------ explanations (cloze_explain.py's machinery)

EXP = OUT / "explain"
EXP_PACK = 8      # about 4 passages per pack
EXP_PASSAGE = re.compile(r"\{\{(\d+)\|([^{}]*)\}\}")


def exp_norm(stem):
    """The passage as the writers and checkers see it: each asked word as '(n) wrong-word'."""
    return EXP_PASSAGE.sub(lambda m: f"({m.group(1)}) {m.group(2)}", stem)


def exp_wrong(r):
    """The printed wrong word of a row, read from its stem."""
    for m in EXP_PASSAGE.finditer(r["stem"]):
        if int(m.group(1)) == r["seq"]:
            return m.group(2)
    return r.get("wrong") or ""


def exp_passages(rs):
    by = collections.defaultdict(list)
    for r in rs.values():
        by[r["grp"]].append(r)
    out = []
    for g, ps in sorted(by.items()):
        ps.sort(key=lambda r: r["seq"])
        out.append({"grp": g, "section": "Editing", "passage": exp_norm(ps[0]["stem"]),
                    "blanks": [{"id": r["id"], "n": r["seq"], "wrong": exp_wrong(r), "accept": r["accept"]} for r in ps]})
    return out


def exp_lint(r, text):
    """Why an explanation fails the rules, or '' when it passes."""
    import cloze_explain as CE
    if not text:
        return "empty"
    if len(text) > CE.MAX:
        return f"longer than {CE.MAX}"
    if "!" in text or text.lower().startswith("the answer is"):
        return "style"
    if not CE.named(r["accept"][0], text):
        return "does not name the correct word"
    if not CE.named(exp_wrong(r), text):
        return "does not quote the printed wrong word"
    if len(r["accept"]) <= 3 and not all(CE.named(a, text) for a in r["accept"][1:]):
        return "an accepted answer is not mentioned"
    return ""


def exp_setup():
    import cloze_explain as CE
    CE.WORK, CE.SHIP, CE.N = EXP, SHIP / "english", EXP_PACK
    CE.passages, CE.norm, CE.lint_one = exp_passages, exp_norm, exp_lint
    EXP.mkdir(parents=True, exist_ok=True)
    return CE


def explain_pack():
    exp_setup().cmd_pack()


def exp_is_spelling(r):
    """A spelling item by rule: one printed word, a one-word accept, and the two words alike (ratio >= 0.6) but not the same."""
    w, a = exp_wrong(r), r["accept"]
    if not w or len(a) != 1 or " " in w.strip() or " " in a[0].strip() or w.lower() == a[0].lower():
        return False
    return difflib.SequenceMatcher(None, w.lower(), a[0].lower()).ratio() >= 0.6


def exp_spell_warn(r, text):
    """Rules (strings) an explanation of a SPELLING item breaks when a cheaply verifiable claim about the letters is false;
    [] for a grammar item or when nothing is certainly false. Conservative: only these patterns, no free-text reading."""
    if not exp_is_spelling(r) or not text:
        return []
    w, a = exp_wrong(r).lower(), r["accept"][0].lower()
    t = text.lower()
    q = r"'([a-z]{1,4})'"
    out = []
    ops = [o for o in difflib.SequenceMatcher(None, w, a).get_opcodes() if o[0] != "equal"]
    for g in re.findall(r"\b(?:double|two|twin)\s+" + q, t):
        if len(g) == 1 and g * 2 in w and g * 2 in a and not re.search(r"\b(?:single|one|extra|only|too many|not)\b", t):
            out.append(f"double '{g}' is in the printed word too")
    pos = r"(?!\s+(?:after|before|between|at|in|next)\b)"  # "missing 'r' after 'pe'" is about a place, not a count
    for g in re.findall(r"\b(?:missing|leaves? out|left out|lacks?|omits?)\s+(?:the\s+)?(?:letters?\s+)?" + q + pos, t):
        if w.count(g) >= a.count(g) and not any(g in a[j1:j2] for _, _, _, j1, j2 in ops):
            out.append(f"missing '{g}' but the printed word has as many")
    for g in re.findall(r"\b(?:extra|additional|too many)\s+(?:letters?\s+)?" + q, t):
        if w.count(g) <= a.count(g) and not any(g in w[i1:i2] for _, i1, i2, _, _ in ops):
            out.append(f"extra '{g}' but the printed word has no more of it")
    if sum(max(i2 - i1, j2 - j1) for _, i1, i2, j1, j2 in ops) == 1 and re.search(r"\b(?:wrong|different|incorrect)\s+(?:vowels|letters)\b", t):
        out.append("plural letters but exactly one differs")
    seen = {x.lower() for x in re.findall(r"[A-Za-z]+", r["stem"])}
    # an example word ("as in 'sure'", "like 'th' in 'path'") may be any word: only a bare quoted group is checked
    for g in dict.fromkeys(re.findall(r"(?<!\bas in )(?<!\blike )(?<!\bin )(?<!\bfrom )(?<!\bof )(?<![a-z])'([a-z]{1,4})'(?![a-z])", t)):
        if g not in w and g not in a and g not in seen:
            out.append(f"quoted '{g}' is in neither word")
    for g in re.findall(r"\b(?:starts?|begins?) with\s+(?:the\s+)?(?:letters?\s+)?" + q, t) + re.findall(q + r"\s+at the (?:start|beginning)\b", t):
        if not (w.startswith(g) or a.startswith(g)):
            out.append(f"'{g}' at the start of neither word")
    for g in re.findall(r"\bends?\s+(?:in|with)\s+(?:the\s+)?(?:letters?\s+)?" + q, t) + re.findall(q + r"\s+at the end\b", t):
        if not (w.endswith(g) or a.endswith(g)):
            out.append(f"'{g}' at the end of neither word")
    return out


def explain_lint():
    CE = exp_setup()
    rs, w = CE.cmd_lint()
    n, ids = 0, []
    for i, r in rs.items():
        for rule in exp_spell_warn(r, w.get(i, "")):
            n += 1
            ids.append(i)
            print(f"WARN {i} (q{r['seq']} '{exp_wrong(r)}' -> '{r['accept'][0]}'): {rule}")
    print(f"WARN count {n} on {len(set(ids))} explanations")


def checkpack_guard(work, tag, n=EXP_PACK):
    """Why a checkpack must not run (a string), or "": cloze_explain opens its pack files with 'w', so a re-run over packs the
    checkers have already filled empties them and every verdict loses its tie to its text. Never overwrite a pack file."""
    names = [tag] if tag else [str(k) for k in range(n)]
    have = [f"cpack_{x}.jsonl" for x in names if (work / f"cpack_{x}.jsonl").exists()]
    if have and tag:
        return f"{have[0]} exists: pick another tag"
    if have:
        return f"packs exist ({have[0]} ...): explain-recheck <new tag> packs what is still unchecked"
    return ""


def explain_checkpack(tag=None):
    CE = exp_setup()
    why = checkpack_guard(EXP, tag, EXP_PACK)
    if why:
        print("refused:", why)
        return
    CE.cmd_checkpack(tag)
    for name in ([tag] if tag else [str(k) for k in range(EXP_PACK)]):  # nothing to check: leave no empty pack
        f = EXP / f"cpack_{name}.jsonl"
        if f.exists() and not f.read_text().strip():
            f.unlink()
    if not list(EXP.glob("cpack_*.jsonl")) or (tag and not (EXP / f"cpack_{tag}.jsonl").exists()):
        print("nothing to check")


def explain_apply():
    exp_setup().cmd_apply()


WRITER_MD = """# Editing explanations: writer brief

You write the "Why this works" text a child sees after getting an Editing question wrong. Do packs A..B (N = the pack number).

Read /data/alvin/tmp/cookie-codex/editing/explain/pack_N.jsonl. Each line is one Editing passage: grp, passage (each asked word
shown as "(n) wrong-word"), and blanks: id, n, wrong (the printed wrong word), accept (the corrections; the first is the model answer).

Write /data/alvin/tmp/cookie-codex/editing/explain/out_N.jsonl: one JSON line per blank, {"id": "<id>", "right": "<text>"}, every blank of the pack.

Each text: 1-2 short sentences, at most 280 characters, for a 12-year-old. Quote the printed wrong word and the correct word in single
quotes (straight quotes, around the words only, never inside a word). If accept lists up to 3 answers, name each one in quotes.
- SPELLING error: say what is wrong with the spelling in a way that helps remember it: the letters swapped, doubled or missing, or the
  sound that fooled the writer ("'Recieve' has 'ie' the wrong way round; after 'c' it is 'ei': 'receive'.").
- GRAMMAR error: name the rule and quote the clue words in the sentence exactly as they are in the passage (tense marker,
  subject-verb agreement, preposition after a verb, pronoun, connector).
Example, passage "Tom (1) runned to school.", accept ["ran"]:
  {"id": "x1", "right": "'Runned' is not a word: 'run' is irregular, so the past tense is 'ran'. 'Tom' did it already."}
No "!", do not start with "The answer is", never invent facts about the passage. If the key looks wrong, still explain it and add a line
{"id", "reason"} to /data/alvin/tmp/cookie-codex/editing/explain/doubts_N.jsonl.
Write only these files. Do not touch the repo, and put no other files anywhere. Reply with one line: packs done and counts.
"""

CHECKER_MD = """# Editing explanations: checker brief

You check the "Why this works" texts for Editing questions. Do packs A..B (N = the pack number).

Read /data/alvin/tmp/cookie-codex/editing/explain/cpack_N.jsonl. Each line is one passage: passage (each asked word shown as
"(n) wrong-word") and blanks: id, n, wrong, accept (the first is the model answer), explanation.

Judge each explanation yourself, from the passage. ok is true only if ALL hold:
- the spelling or grammar point is true (the rule exists and applies; the letters or sound described are really so);
- every quoted word or phrase from the passage is exactly in the passage (and the quoted wrong word is the printed one);
- it supports the accepted correction (the first accept), and does not recommend a different one;
- a 12-year-old can follow it (plain words, 1-2 short sentences, no jargon left unexplained).
Anything doubtful is false: a wrong "ok" teaches a child something untrue, a wrong "false" only costs a rewrite.

Write /data/alvin/tmp/cookie-codex/editing/explain/check_N.jsonl: one JSON line per blank, {"id": "<id>", "ok": true|false, "reason": "<short>"},
every blank of the pack (reason says what is wrong when false). Write only that file; do not edit the explanations or the repo.
Reply with one line: packs done, ok and not ok counts.
"""


def explain_briefs():
    EXP.mkdir(parents=True, exist_ok=True)
    (EXP / "WRITER.md").write_text(WRITER_MD, encoding="utf-8")
    (EXP / "CHECKER.md").write_text(CHECKER_MD, encoding="utf-8")


def explain_selftest():
    rs = [{"id": "a1", "grp": "g", "seq": 1, "accept": ["ran"], "stem": "Tom {{1|runned}} to school and {{2|their}} home.", "wrong": "runned"},
          {"id": "a2", "grp": "g", "seq": 2, "accept": ["went", "walked"], "stem": "Tom {{1|runned}} to school and {{2|their}} home.", "wrong": "their"}]
    assert exp_norm(rs[0]["stem"]) == "Tom (1) runned to school and (2) their home."
    assert exp_wrong(rs[1]) == "their"
    ps = exp_passages({r["id"]: r for r in rs})
    assert ps[0]["blanks"][1] == {"id": "a2", "n": 2, "wrong": "their", "accept": ["went", "walked"]} and ps[0]["section"] == "Editing"
    ok = "'Runned' is not a word: 'run' is irregular, so the past tense is 'ran'."
    assert exp_lint(rs[0], ok) == ""
    assert exp_lint(rs[0], "Use 'ran' here.") == "does not quote the printed wrong word"
    assert exp_lint(rs[0], "'Runned' is wrong.") == "does not name the correct word"
    assert exp_lint(rs[1], "'Their' should be 'went' here.") == "an accepted answer is not mentioned"
    assert exp_lint(rs[1], "'Their' should be 'went' or 'walked'.") == ""
    assert exp_lint(rs[0], "'Runned' is wrong, say 'ran'!") == "style" and exp_lint(rs[0], "") == "empty"
    assert exp_lint(rs[0], "The answer is 'ran', not 'runned'.") == "style"
    assert exp_lint(rs[0], "'Runned' -> 'ran'. " + "x" * 300).startswith("longer than")
    sp = {"id": "s1", "grp": "g", "seq": 1, "accept": ["suffice"], "stem": "It will {{1|suficce}} for Zed.", "wrong": "suficce"}
    assert exp_is_spelling(sp) and not exp_is_spelling(rs[1]) and not exp_is_spelling(dict(sp, accept=["suffice", "enough"]))
    assert exp_spell_warn(rs[1], "'Their' should be 'went'.") == [], "a grammar item is not checked"
    def mk(wrong, accept):
        return {"id": "z", "grp": "g", "seq": 1, "accept": [accept], "stem": "{{1|" + wrong + "}}", "wrong": wrong}
    assert exp_spell_warn(mk("blufff", "bluff"), "'Blufff' should have double 'f': 'bluff'.") != [], "wrong word has the double too"
    z = mk("blof", "bluff")
    assert exp_spell_warn(z, "'Blof' needs a double 'f': 'bluff'.") == [] and exp_spell_warn(z, "'Blof' is missing an 'f': 'bluff'.") == []
    assert exp_spell_warn(mk("blofe", "blof"), "'Blofe' leaves out 'o': 'blof'.") != [], "wrong word has the letter as often"
    assert exp_spell_warn(z, "'Blof' has an extra 'f': 'bluff'.") != [] and exp_spell_warn(mk("bluffe", "bluff"), "'Bluffe' has an extra 'e': 'bluff'.") == []
    assert exp_spell_warn(mk("bluff", "blaff"), "Wrong vowels: 'bluff' has 'u'.") != [], "one letter differs"
    assert exp_spell_warn(mk("bluff", "blaff"), "The letter 'a' is wrong.") == [] and exp_spell_warn(mk("bluff", "blaff"), "Use 'ee' here.") != [], "quoted group in neither word"
    assert exp_spell_warn(z, "'Blof' ends in 'f' but needs 'bluff'.") == [] and exp_spell_warn(z, "'Blof' ends in 'x': 'bluff'.") != []
    assert exp_spell_warn(z, "'Bl' at the start is right: 'bluff'.") == [] and exp_spell_warn(z, "'Zz' starts with 'q': 'bluff'.") != []
    import tempfile
    with tempfile.TemporaryDirectory() as d:  # finding 1 and 10: a checkpack never overwrites a pack file
        w = Path(d)
        assert checkpack_guard(w, None) == "" and checkpack_guard(w, "t1") == ""
        (w / "cpack_3.jsonl").write_text("x\n")
        assert "packs exist" in checkpack_guard(w, None) and checkpack_guard(w, "t1") == ""
        (w / "cpack_t1.jsonl").write_text("x\n")
        assert checkpack_guard(w, "t1") == "cpack_t1.jsonl exists: pick another tag"
    print("editing explain selftest ok")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd in ("explain-checkpack", "explain-recheck"):
        explain_briefs()
        explain_checkpack(sys.argv[2] if len(sys.argv) > 2 else None) if cmd == "explain-checkpack" else explain_checkpack(sys.argv[2])
        sys.exit(0)
    if cmd == "explain-pack":
        explain_briefs()
    fn = {"text": text, "place": place, "pack": pack, "vpack": vpack, "final": final, "selftest": selftest,
          "explain-pack": explain_pack, "explain-lint": explain_lint, "explain-apply": explain_apply, "stamp-place": stamp_place}.get(cmd)  # final takes no args here
    if not fn:
        sys.exit(__doc__)
    fn()
