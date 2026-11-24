#!/usr/bin/env python3
"""Explanations for past-paper MCQs (owner, 23 Nov 2026: "why is the answer correct ... for all applicable English
questions"; Maths and Science next): why the key is right, and why each other option does not fit, for a 12-year-old.

  explain.py pack [SEL ...]        dev: items.jsonl from the selections (default: English grammar and vocabulary)
  explain.py write ITEMS           server: Qwen2.5-72B writes one per item (PP_LLM, PP_TP) -> written.jsonl (resumable)
  explain.py judge ITEMS           server: a second model of another family (Llama-3.1-70B, PP_JUDGE) checks each one
                                   against the question and its key -> judged.jsonl (resumable)
  explain.py calib                 dev: calib.jsonl = 60 passed explanations + 60 planted wrong ones (another question's
                                   reason, or the reason argued for a wrong option): the judge must reject >= 90% of the
                                   planted ones before its verdicts count (`judge` on calib.jsonl, then `calib-score`)
  explain.py revise ITEMS          server: the writer rewrites every rejected one, given the judge's objection ->
                                   revised.jsonl; `judge2` checks those -> judged2.jsonl (a second rejection drops it)
  explain.py apply [--sample N]    dev: the passed ones -> <selection>/<subject>/explain.jsonl (read by load_pp upload);
                                   prints N random passed ones for the owner's spot check
  explain.py apply-opus [--sample N]  dev: the Claude Opus agents' files (opus/out_NN_partN.jsonl, owner's choice A,
                                   23 Nov 2026) -> each selection's explain.jsonl; lines that doubt the key go to
                                   opus/doubts.jsonl for the owner, never to the site
  explain.py selftest
A key is never questioned here (the keys are settled); an explanation that argues for another option, or that the judge
calls wrong, is dropped, and that question simply shows no explanation. Past-paper text stays off the repo and the site."""
import collections
import json
import os
import random
import re
import sys
from pathlib import Path

TMP = Path("/data/alvin/tmp/cookie-codex")
WORK = Path(os.environ.get("PP_WORK", str(TMP / "explain")))  # the server sets its own folder
SELS = [TMP / "ppimport/eng1826d/english"]
# Chinese (owner, 24 Nov 2026: option B, Qwen writes and InternLM checks): the single-question sections
SELS_ZH = [TMP / "ppimport/chi1826e/chinese"]
SUBS = {"english": {"eng-grammar-mcq", "eng-vocab-mcq"},
        "chinese": {"chi-pinyin-sound", "chi-zixing-form", "chi-ciyu-choose", "chi-ciyu-idiom", "chi-juzi-choose", "chi-juzi-guanlian"}}
LLM = os.environ.get("PP_LLM", "Qwen/Qwen2.5-72B-Instruct-AWQ")
JUDGE = os.environ.get("PP_JUDGE", "hugging-quants/Meta-Llama-3.1-70B-Instruct-AWQ-INT4")
SYS = ("You are a kind, precise Singapore primary school English teacher. You explain PSLE English MCQ answers to a "
       "12-year-old in simple words.")
WRITE = ("Question: {stem}\nOptions:\n{opts}\nThe correct answer is ({k}) {ans}.\n\n"
         "Explain in one or two short sentences why ({k}) is correct: name the grammar rule, or say what the word means "
         "and why it fits this sentence. Then, for each other option, write one short sentence saying why it does not fit. "
         "Quote the words themselves, use simple language, and never say another option could also be right.\n"
         "Reply with JSON only: {{\"right\": \"...\", \"wrong\": {{\"<option number>\": \"...\"}}}}")
REVISE = ("Question: {stem}\nOptions:\n{opts}\nThe correct answer (already confirmed) is ({k}) {ans}.\n"
          "Your earlier explanation:\n{old}\nA reviewer objected: {problem}\n\n"
          "If the objection is right, fix the explanation; if it is wrong, keep what was right but make the wording "
          "clearer. Keep it short and simple for a 12-year-old, quote the words, never say another option could also be "
          "right. Reply with JSON only: {{\"right\": \"...\", \"wrong\": {{\"<option number>\": \"...\"}}}}")
SYS_ZH = "你是一位亲切、严谨的新加坡小学华文老师，为12岁的学生解释小六华文选择题的答案。"
WRITE_ZH = ("题目：{stem}\n选项：\n{opts}\n正确答案是（{k}）{ans}。\n\n"
            "先用一两句简单的中文说明为什么（{k}）是对的：说明词语的意思、用法或搭配，或者字音、字形的分别；后面用括号加一句英文翻译。"
            "然后为每个其他选项写一句话，说明它为什么不对（中文，后面用括号加简短英文）。不要说别的选项也可以。\n"
            "只回复JSON：{{\"right\": \"中文说明（English: ...）\", \"wrong\": {{\"<选项号>\": \"...\"}}}}")
CHECK_ZH = ("题目：{stem}\n选项：\n{opts}\n正确答案（已确认）是（{k}）{ans}。\n老师为12岁学生写的解释：\n为什么（{k}）对：{right}\n{wrongs}\n\n"
            "这个解释里的每一句都正确吗？它是否支持（{k}），而没有暗示别的选项也对？"
            "只回复JSON：{{\"ok\": true 或 false, \"problem\": \"...\"}}")
JUDGE_ZH = os.environ.get("PP_JUDGE_ZH", "internlm/internlm2_5-20b-chat")
CHECK = ("Question: {stem}\nOptions:\n{opts}\nThe correct answer (already confirmed) is ({k}) {ans}.\n"
         "A teacher wrote this explanation for a 12-year-old:\nWhy ({k}) is right: {right}\n{wrongs}\n\n"
         "Is every statement in the explanation true English grammar or meaning, and does it support ({k}) without "
         "suggesting any other option is correct? Reply with JSON only: {{\"ok\": true or false, \"problem\": \"...\"}}")


def jl(p):
    p = Path(p)
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if p.exists() else []


def parse(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        return json.loads(m.group(0)) if m else None
    except Exception:
        return None


def fp(r):
    """The question as the explanation was written for it: an explanation is used only while stem, options and key match."""
    import hashlib
    key = [r["stem"], r["options"], r["answer"]] + ([r.get("accept"), r.get("scaffold")] if r.get("kind") == "typed" else [])
    return hashlib.sha1(json.dumps(key, ensure_ascii=False).encode()).hexdigest()[:12]  # typed: a new model answer needs a new why


def opts_text(opts):
    return "\n".join(f"({i}) {o}" for i, o in enumerate(opts, 1))


def shape(read, opts, k):
    """The written explanation as {right, wrong[]} (null at the key), or None when it is incomplete."""
    if not isinstance(read, dict) or not isinstance(read.get("right"), str) or not read["right"].strip():
        return None
    w = read.get("wrong") if isinstance(read.get("wrong"), dict) else {}
    wrong = []
    for i in range(len(opts)):
        if i == k:
            wrong.append(None)
            continue
        s = w.get(str(i + 1))
        if not isinstance(s, str) or not s.strip():
            return None  # every other option needs its reason
        wrong.append(s.strip()[:400])
    right = read["right"].strip()
    return {"right": right[:600], "wrong": wrong} if len(right) >= 15 else None


def pack(sels):
    WORK.mkdir(parents=True, exist_ok=True)
    out = []
    for sel in sels:
        subject = sel.name
        for r in jl(sel / "selected.jsonl"):
            # a question with a picture is left out: the model reads text only and would explain what it cannot see
            if r["subtopic"] in SUBS.get(subject, set()) and not r.get("grp") and not r.get("crops") and not r.get("set_pages"):
                x = {"id": r["id"], "sel": str(sel), "subject": subject, "stem": r["stem"], "options": r["options"], "answer": r["answer"]}
                out.append(dict(x, fp=fp(x)))
    (WORK / "items.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in out))
    print(f"{len(out)} questions -> {WORK / 'items.jsonl'}")


def llm(model):
    from vllm import LLM, SamplingParams
    return LLM(model=model, tensor_parallel_size=int(os.environ.get("PP_TP", "4")), gpu_memory_utilization=0.9,
               max_model_len=4096, enforce_eager=bool(os.environ.get("PP_EAGER")), trust_remote_code=True,
               # InternLM's fast tokenizer is built from its sentencepiece model through protobuf, which the server's
               # protobuf 4.25 cannot do (runtime_version); the slow tokenizer reads the model file directly
               tokenizer_mode="slow" if "internlm" in model.lower() else "auto"), SamplingParams(temperature=0, max_tokens=500)


def run(items_file, phase):
    """write: items -> written.jsonl; judge: written -> judged.jsonl (for calib.jsonl: the explanations inside it ->
    calib_judged.jsonl); revise: rejected -> revised.jsonl; judge2: revised -> judged2.jsonl. All resumable."""
    items_file = Path(items_file)
    items = jl(items_file)
    d = items_file.parent
    calib = items_file.name == "calib.jsonl"
    names = {"write": "written", "judge": "calib_judged" if calib else "judged", "revise": "revised", "judge2": "judged2"}
    out = d / f"{names[phase]}.jsonl"
    key = lambda r: (r["id"], r.get("fp"))
    done = {key(r) for r in jl(out)}
    if phase == "write":
        src = {}
    elif phase == "judge":
        src = {key(r): r for r in items} if calib else {key(r): r for r in jl(d / "written.jsonl")}
    elif phase == "revise":
        bad = {key(r): r for r in jl(d / "judged.jsonl") if not r["ok"]}
        wr = {key(r): r for r in jl(d / "written.jsonl")}
        src = {k: dict(wr[k], problem=bad[k]["problem"]) for k in bad if (wr.get(k) or {}).get("explain")}
    else:
        src = {key(r): r for r in jl(d / "revised.jsonl")}
    todo = [r for r in items if key(r) not in done and (phase == "write" or (src.get(key(r)) or {}).get("explain"))]
    print(len(todo), "to", phase, flush=True)
    if not todo:
        return
    zh = bool(items) and items[0].get("subject") == "chinese"
    model, sp = llm((JUDGE_ZH if zh else JUDGE) if phase in ("judge", "judge2") else LLM)
    sys_p, write_p, check_p = (SYS_ZH, WRITE_ZH, CHECK_ZH) if zh else (SYS, WRITE, CHECK)
    with open(out, "a", encoding="utf-8") as f:
        for i in range(0, len(todo), 64):
            ch, msgs = todo[i:i + 64], []
            for r in ch:
                k, o = r["answer"], r["options"]
                if phase == "write":
                    p = write_p.format(stem=r["stem"], opts=opts_text(o), k=k + 1, ans=o[k])
                elif phase == "revise":
                    s = src[key(r)]
                    p = REVISE.format(stem=r["stem"], opts=opts_text(o), k=k + 1, ans=o[k], old=say(s["explain"]), problem=s["problem"])
                else:
                    e = src[key(r)]["explain"]
                    wr = "\n".join(f"{'为什么（' + str(j + 1) + '）不对' if zh else 'Why (' + str(j + 1) + ') does not fit'}: {w}" for j, w in enumerate(e["wrong"]) if w)
                    p = check_p.format(stem=r["stem"], opts=opts_text(o), k=k + 1, ans=o[k], right=e["right"], wrongs=wr)
                msgs.append([{"role": "system", "content": sys_p}, {"role": "user", "content": p}])
            for r, res in zip(ch, model.chat(msgs, sp, use_tqdm=False)):
                raw = res.outputs[0].text
                if phase in ("write", "revise"):
                    rec = {"id": r["id"], "fp": r.get("fp"), "explain": shape(parse(raw), r["options"], r["answer"]), "raw": raw}
                else:
                    v = parse(raw) or {}
                    rec = {"id": r["id"], "fp": r.get("fp"), "ok": v.get("ok") is True, "problem": str(v.get("problem") or "")[:300], "raw": raw}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{min(i + 64, len(todo))}/{len(todo)}", flush=True)


def say(e):
    return f"Why it is right: {e['right']}\n" + "\n".join(f"Why ({j + 1}) does not fit: {w}" for j, w in enumerate(e["wrong"]) if w)


def calib():
    """60 passed explanations kept as they are, and 60 planted wrong ones: half take another question's reason, half say
    the reason for a wrong option (its words put where the answer's were)."""
    items = {r["id"]: r for r in jl(WORK / "items.jsonl")}
    wr = {r["id"]: r["explain"] for r in jl(WORK / "written.jsonl") if r.get("explain")}
    judged = jl(WORK / "judged.jsonl")
    pool = [r["id"] for r in judged if r["ok"]] if judged else list(wr)  # no judge yet: the written ones (only the planted catch rate counts)
    ok = [i for i in pool if i in wr and i in items]
    rng = random.Random(11)
    pick = rng.sample(ok, min(120, len(ok)))
    good, plant = pick[:60], pick[60:]
    out = [dict(items[i], id=f"good-{i}", explain=wr[i], planted=False) for i in good]
    for n, i in enumerate(plant):
        it, e = items[i], dict(wr[i])
        if n % 2:  # another question's reason
            other = wr[plant[(n + 1) % len(plant)]]
            e = dict(e, right=other["right"])
        else:  # argue for a wrong option: its words where the answer's were
            wrong = next(j for j in range(len(it["options"])) if j != it["answer"])
            tail = f"所以答案是（{wrong + 1}）。" if it.get("subject") == "chinese" else f" So the answer is ({wrong + 1})."
            e = dict(e, right=e["right"].replace(it["options"][it["answer"]], it["options"][wrong]) + tail)
        out.append(dict(it, id=f"plant-{i}", explain=e, planted=True))
    (WORK / "calib.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in out))
    print(f"{len(out)} calibration rows -> {WORK / 'calib.jsonl'}")


def calib_score(path=WORK / "calib_judged.jsonl", bar=0.9):
    rows = {r["id"]: r for r in jl(WORK / "calib.jsonl")}
    j = jl(path)
    caught = sum(1 for x in j if rows[x["id"]]["planted"] and not x["ok"])
    planted = sum(1 for x in j if rows[x["id"]]["planted"])
    kept = sum(1 for x in j if not rows[x["id"]]["planted"] and x["ok"])
    good = len(j) - planted
    rate = caught / max(1, planted)
    print(f"judge caught {caught}/{planted} planted wrong explanations ({rate:.0%}); passed {kept}/{good} good ones "
          f"-> {'PASSED' if rate >= bar else 'FAILED'} (bar {bar:.0%})")
    return rate >= bar


def apply(sample=0):
    """Only rows of the current items.jsonl count, matched by id and fingerprint (rows from before fingerprints, fp None,
    are taken as written for the current version); every selection in the items gets a fresh explain.jsonl, empty when
    none passed, so a file from an earlier run never outlives it."""
    items = {r["id"]: r for r in jl(WORK / "items.jsonl")}
    cur = lambda r: r["id"] in items and r.get("fp") in (None, items[r["id"]]["fp"])
    written = {r["id"]: r.get("explain") for r in jl(WORK / "written.jsonl") if cur(r)}
    judged = {r["id"]: r for r in jl(WORK / "judged.jsonl") if cur(r)}
    revised = {r["id"]: r.get("explain") for r in jl(WORK / "revised.jsonl") if cur(r)}
    judged2 = {r["id"]: r for r in jl(WORK / "judged2.jsonl") if cur(r)}
    passed = {i: e for i, e in written.items() if e and judged.get(i, {}).get("ok")}
    passed.update({i: e for i, e in revised.items() if e and judged2.get(i, {}).get("ok") and i not in passed})
    by = {r["sel"]: [] for r in items.values()}
    for i, e in passed.items():
        by[items[i]["sel"]].append({"id": i, "fp": items[i]["fp"], "explain": e})
    for sel, rows in by.items():
        (Path(sel) / "explain.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows))
    n, w, j = len(items), sum(bool(e) for e in written.values()), len(judged)
    print(f"{n} questions: {w} written, {j} judged, {len(passed)} passed ({len(passed) / max(1, n):.0%}); "
          f"incomplete {len(written) - w}, judged wrong {sum(1 for x in judged.values() if not x['ok'])}")
    for i in random.Random(7).sample(sorted(passed), min(sample, len(passed))):
        r, e = items[i], passed[i]
        print(f"\n{r['stem']}\n  " + "  ".join(f"({k + 1}) {o}" for k, o in enumerate(r["options"])) + f"\n  answer ({r['answer'] + 1})")
        print(f"  why right: {e['right']}")
        for k, w in enumerate(e["wrong"]):
            if w:
                print(f"  ({k + 1}) does not fit: {w}")


def mentions(text, opt):
    """The explanation talks about the option: for each part ("had...rushed" -> had, rushed) most of its words appear in
    the text in some form ("incurred" ~ "incur", "backed off" ~ "back off", "blow over" ~ "blows over")."""
    words = lambda s: re.findall(r"[a-z']+", (s or "").lower().replace("’", "'"))
    tw = words(text)

    def near(w):
        if len(w) <= 3:
            return w in tw
        return any(len(x) >= 3 and (x == w or (x[:3] == w[:3] and len(os.path.commonprefix([x, w])) >= max(3, min(len(x), len(w)) - 3))) for x in tw)
    parts = [p for p in re.split(r"\.{2,}|…|/", opt or "") if p.strip()]
    if not parts:
        return False
    for part in parts:
        ws = words(part)
        if not ws or sum(near(w) for w in ws) * 2 < len(ws):
            return False
    return True


OPTNUM = re.compile(r"[（(]\s*[1-4]\s*[)）]\s*")  # "（4）担": options are shuffled on screen, so a number may name another option


def denum(t, options):
    """An option cited by its printed number followed by its words becomes the words alone: "正确答案是（4）担" ->
    "正确答案是「担」" ("(2) hasn't" -> "\"hasn't\"" in English). A number not followed by its option is left in place, and
    opus_row rejects the line (owner's site shuffles options, 24 Nov 2026: the Qwen drafts kept "（3）" and the first Opus
    check missed 247)."""
    zh = any(ZH_OPT.search(o) for o in options)
    for k, o in enumerate(options):
        core = OPTNUM.sub("", o, count=1).strip()
        if core:
            q = f"「{core}」" if zh else f'"{core}"'
            t = re.sub(rf"[（(]\s*{k + 1}\s*[)）]\s*[「“\"'‘]?{re.escape(core)}[」”\"'’]?", lambda _m: q, t)
            # "选项（2）中的“这本书虽然很薄”… (English: Option (2) 'he will…')": the line names the option in words, so its number
            # adds nothing and goes
            if core in t:
                t = re.sub(rf"\s?[（(]\s*{k + 1}\s*[)）]", "", t)
    return t.strip()


ZH_OPT = re.compile(r"[\u3400-\u9fff]|[āáǎàōóǒòēéěèīíǐìūúǔùǖǘǚǜ]")


def mentions_zh(text, opt):
    """Chinese or pinyin options. Pinyin: one of the option's syllables appears as a whole word in the line. Chinese: the
    line has two of the option's characters in a row (all of a one-character option), "……" not counted. It catches an
    explanation written for another question (its words differ), not one shifted between this question's look-alike options
    (ponytail: a per-option check would need the reasons parsed; the fp copy by script guards that)."""
    from difflib import SequenceMatcher
    core = re.sub(r"…+|\.{2,}", " ", OPTNUM.sub("", opt or "", count=1)).strip()
    if not core:
        return False
    if not re.search(r"[\u3400-\u9fff]", core):
        return any(re.search(rf"(?<![\w]){re.escape(syl)}(?![\w])", text or "") for syl in core.split() if len(syl) >= 2)
    t = re.sub(r"…+", " ", text or "")
    parts = [p for p in core.split() if p]
    return any(SequenceMatcher(None, t, p).find_longest_match(0, len(t), 0, len(p)).size >= min(2, len(p)) for p in parts)


COMMON_ZH = set("的了是在不有和一这那我你他她它们个也就都很要会说上下来去着过把被给对")


def aligned(e, item):
    """The explanation is about this question (an agent once re-took ids by position): its reason quotes the answer,
    and at least two of the wrong-option lines quote their own option."""
    o, k = item["options"], item["answer"]
    if all(not re.search(r"[\u3400-\u9fff]", x) and ZH_OPT.search(x) for x in o):
        # pinyin options look alike and the reasons name the sound ("声母是 ch，不是 zh"), so text matching cannot tell them
        # apart; an explanation is about this question when its reason quotes a character of this question's sentence
        # (or quotes the key's whole syllable, where the sentence blanks the word out: 深刻的____)
        return bool(set(re.findall(r"[\u3400-\u9fff]", e["right"])) & (set(re.findall(r"[\u3400-\u9fff]", item.get("stem") or "")) - COMMON_ZH)) \
            or mentions_zh(e["right"], o[k])
    zh = any(ZH_OPT.search(x) for x in o)
    mentions_ = mentions_zh if zh else mentions
    hits = sum(mentions_(w, o[j]) for j, w in enumerate(e["wrong"]) if j != k and w)
    return mentions_(e["right"], o[k]) and hits >= len(o) - 2


CEDICT = Path("/data/alvin/tmp/cookie-codex/cedict/cedict_ts.u8")
_CED = None


def ced():
    """CC-CEDICT as {simplified: [[pinyin, sense], ...]} (the site's gloss uses the same file and credit)."""
    global _CED
    if _CED is None:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "quiz" / "chinese"))
        from build_gloss import load_cedict
        _CED = load_cedict(CEDICT) if CEDICT.exists() else {}
    return _CED


# a connective in a 关联词 pair has one reading, whatever else the character can be read as
CONNECTIVE = {"都": "dōu", "还": "hái", "便": "biàn", "只": "zhǐ", "得": "de", "要": "yào", "将": "jiāng", "为": "wèi", "和": "hé",
              "与": "yǔ", "否": "fǒu", "则": "zé", "假": "jiǎ", "倘": "tǎng", "尽": "jǐn", "管": "guǎn", "更": "gèng", "宁": "nìng",
              "省": "shěng"}


_ALLR = None


def all_readings():
    """{simplified: {pinyin, ...}} with every CC-CEDICT reading, including the "used in ..." / "see ..." entries the gloss
    loader drops (似 is sì, and shì in 似的): a character counts as having one reading only when it truly has one."""
    global _ALLR
    if _ALLR is None:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "quiz" / "chinese"))
        from build_gloss import pinyin as tones
        _ALLR = collections.defaultdict(set)
        for line in open(CEDICT, encoding="utf-8") if CEDICT.exists() else ():
            m = re.match(r"\S+ (\S+) \[([^\]]+)\]", line)
            if m and not line.startswith("#") and not m.group(2)[:1].isupper():
                _ALLR[m.group(1)].add(tones(m.group(2)).lower())
    return _ALLR


def reading(word, stem="", own=False, pair=False):
    """The pinyin of an option word: its dictionary reading when it has one; a character with several readings takes the one
    of the word it forms in the sentence (only for the key, own=True: a wrong character forms no word); a word missing from
    the dictionary is spelled character by character when every character has one reading. None when unsure."""
    rs = set(all_readings().get(word, ()))
    if len(rs) == 1:
        return rs.pop()
    if pair and word in CONNECTIVE:
        return CONNECTIVE[word]
    if pair and len(word) > 1 and len(rs) > 1:
        import unicodedata
        bare = lambda r: unicodedata.normalize("NFD", r).encode("ascii", "ignore").decode()
        if len({bare(r) for r in rs}) == 1:  # a connective (不是…而是: bù shì, not bù shi); elsewhere 东西 dōng xī / dōng xi
            return max(rs, key=lambda r: sum(c in "āáǎàōóǒòēéěèīíǐìūúǔùǖǘǚǜ" for c in r))  # are two words: unsure
    if len(word) == 1 and 1 < len(rs) <= 3 and not own:
        return " / ".join(sorted(rs))  # a wrong 字形 character forms no word here: all its readings are true
    if len(word) == 1 and len(rs) > 1 and own:
        from build_gloss import windows
        parts = re.split(r"[_＿]{2,}", stem, maxsplit=1)
        if len(parts) == 2:
            seen = set()  # the character's syllable in every dictionary word around the blank: one reading, or unsure
            for w in windows(parts[0], word, parts[1]):
                for r in all_readings().get(w, ()):
                    syl = r.split()
                    if len(syl) == len(w):
                        seen.add(syl[w.index(word)])
            return seen.pop() if len(seen) == 1 else None
        return None
    if not rs and len(word) > 1:
        syl = [reading(c, pair=pair) for c in word]
        return " ".join(syl) if all(x and "/" not in x for x in syl) else None  # each character sure of its reading
    return None


ZH_WORDOPT = re.compile(r"[\u3400-\u9fff]{1,6}(?:(?:……|…|\.{2,})[\u3400-\u9fff]{1,4})?(?:……|…|\.{2,})?")  # "每逢……" too


def add_pinyin(e, item):
    """Owner, 24 Nov 2026: a Chinese explanation gives the pinyin of the word it is about. After the first mention of each
    option in its own line (the key in the reason): 「打扰」（dǎ rǎo）, 「虽然……但是」（suī rán……dàn shì）. Pinyin and sentence
    options are left as they are; a word whose reading is unsure gets none rather than a wrong one."""
    if not CEDICT.exists():
        sys.exit(f"{CEDICT} is missing: Chinese explanations need it for their pinyin (owner, 24 Nov 2026)")
    o = [OPTNUM.sub("", x, count=1).strip() for x in item["options"]]
    out = dict(e, wrong=list(e["wrong"]))
    if not all(ZH_WORDOPT.fullmatch(x) for x in o):
        return quoted_pinyin(out) if any(re.search(r"[\u3400-\u9fff]", x) for x in o) or ZH_OPT.search("".join(o)) else out
    for k, opt in enumerate(o):
        parts = [p for p in re.split(r"……|…|\.{2,}", opt) if p]
        pys = [reading(p, item.get("stem") or "", own=(k == item["answer"]), pair=len(parts) > 1) for p in parts]
        if not all(pys):
            continue
        py = "……".join(pys)
        key = "right" if k == item["answer"] else None
        line = out["right"] if key else out["wrong"][k]
        if not line:
            continue
        zh, sep, en = line.partition("（English")
        if re.search(re.escape(opt) + r"[」”\"’']?\s*[（(]\s*[a-zāáǎàōóǒòēéěèīíǐìūúǔùǖǘǚǜü]", zh):
            continue  # already there
        whole = r"(?:……|…|\.{2,}|、)".join(map(re.escape, parts))  # a pair however its ellipsis is written
        m = re.search(rf"[「“\"‘]{whole}[」”\"’]", zh) or re.search(whole, zh)
        for part, pp in (zip(parts, pys) if not m and len(parts) > 1 else ()):
            m = re.search(rf"{re.escape(part)}[」”\"’]?", zh)  # one half named alone (「而且」): after its closing quote
            if m:
                py = pp
                break
        if not m or re.match(r"\s*[（(]\s*[a-zāáǎàōóǒòēéěèīíǐìūúǔùǖǘǚǜü]", zh[m.end():]):
            continue  # not named, or its pinyin is already there (a re-run adds nothing)
        zh = zh[:m.end()] + f"（{py}）" + zh[m.end():]
        if key:
            out["right"] = zh + sep + en
        else:
            out["wrong"][k] = zh + sep + en
    return quoted_pinyin(out)


PINYIN_AFTER = r"[」”\"’]?\s*[（(]\s*[a-zāáǎàōóǒòēéěèīíǐìūúǔùǖǘǚǜü]"


def quoted_pinyin(e):
    """Every other word the explanation quotes in 「…」 (2 to 4 characters, or one character with a single reading) gets its
    pinyin once per line: sentence-choice and pinyin questions name their key words this way (「紧急」, 「耻」). A word with
    more than one possible reading gets none."""
    def fix(line):
        if not line:
            return line
        zh, sep, en = line.partition("（English")
        # words already given their pinyin in this line (by the option pass) are not given it again
        done = set(re.findall(r"「([\u3400-\u9fff…]{1,9})」\s*（\s*[a-zāáǎàōóǒòēéěèīíǐìūúǔùǖǘǚǜü]", zh)) | \
            set(re.findall(r"([\u3400-\u9fff]{1,4})[」”\"’]?\s*（\s*[a-zāáǎàōóǒòēéěèīíǐìūúǔùǖǘǚǜü]", zh))

        def one(m):
            w = m.group(1)
            if w in done or re.match(PINYIN_AFTER, zh[m.end() - 1:]) or re.match(r"\s*[（(]\s*[a-zāáǎàōóǒòēéěèīíǐìūúǔùǖǘǚǜü]", zh[m.end():]):
                return m.group(0)
            r = reading(w)
            if not r or "/" in r:
                return m.group(0)
            done.add(w)
            return f"{m.group(0)}（{r}）"
        return re.sub(r"「([\u3400-\u9fff]{1,4})」", one, zh) + sep + en
    return dict(e, right=fix(e["right"]), wrong=[fix(w) for w in e["wrong"]])


def opus_row(x, item):
    """An Opus agent's line as {right, wrong[]}, or None when its shape does not fit the question it names."""
    if not item or x.get("fp") != item["fp"] or "doubt" in x:
        return None
    w, k = x.get("wrong"), item["answer"]
    if not isinstance(x.get("right"), str) or len(x["right"].strip()) < 15 or not isinstance(w, list) or len(w) != len(item["options"]):
        return None
    if w[k] is not None or not all(isinstance(s, str) and s.strip() for j, s in enumerate(w) if j != k):
        return None
    o = item["options"]
    e = {"right": denum(x["right"], o)[:600], "wrong": [None if j == k else denum(s, o)[:400] for j, s in enumerate(w)]}
    if any(OPTNUM.search(t) for t in [e["right"], *e["wrong"]] if t):
        return None  # an option number denum could not map to its words: never shipped, never silently cut
    return add_pinyin(e, item) if aligned(e, item) else None


def apply_opus(sample=0):
    import glob
    items = {r["id"]: r for r in jl(WORK / "items.jsonl")}
    got, doubts, bad = {}, [], 0
    # a second Opus review (recheck/, owner OK 24 Nov 2026: the first review kept wrong drafts) overrides the first
    for f in sorted(glob.glob(str(WORK / "opus/out_*_part*.jsonl"))) + sorted(glob.glob(str(WORK / "recheck/out_*_part*.jsonl"))):
        for l in open(f, encoding="utf-8"):
            if not l.strip():
                continue
            try:
                x = json.loads(l)
            except Exception:
                bad += 1
                continue
            if "doubt" in x and x.get("id") in items:
                doubts = [d for d in doubts if d["id"] != x["id"]] + [{"id": x["id"], "doubt": x["doubt"], "stem": items[x["id"]]["stem"],
                                                                        "options": items[x["id"]]["options"], "answer": items[x["id"]]["answer"]}]
                got.pop(x["id"], None)  # a later review's doubt withdraws an earlier explanation
                continue
            e = opus_row(x, items.get(x.get("id")))
            if e:
                got[x["id"]] = e
                doubts = [d for d in doubts if d["id"] != x["id"]]
            else:
                bad += 1
                got.pop(x.get("id"), None)  # a later review that fails the checks withdraws the earlier one too
    by = {r["sel"]: [] for r in items.values()}
    for i, e in got.items():
        by[items[i]["sel"]].append({"id": i, "fp": items[i]["fp"], "explain": e, "src": "claude-opus"})
    for sel, rows in by.items():
        (Path(sel) / "explain.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows))
    (WORK / "opus/doubts.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in doubts))
    print(f"{len(items)} questions: {len(got)} explained, {len(doubts)} key doubts (opus/doubts.jsonl), {bad} lines unusable, "
          f"{len(items) - len(got) - len(doubts)} not covered")
    for i in random.Random(7).sample(sorted(got), min(sample, len(got))):
        r, e = items[i], got[i]
        print(f"\n{r['stem']}\n  " + "  ".join(f"({k + 1}) {o}" for k, o in enumerate(r["options"])) + f"\n  answer ({r['answer'] + 1})")
        print(f"  why right: {e['right']}")
        for k, w in enumerate(e["wrong"]):
            if w:
                print(f"  ({k + 1}) does not fit: {w}")


def selftest():
    assert CEDICT.exists(), f"{CEDICT} missing: the pinyin rules cannot be tested (and apply-opus refuses Chinese without it)"
    if CEDICT.exists():
        it = {"options": ["打扰", "打听", "打算", "打开"], "answer": 0, "stem": "对不起，____你了。"}
        got = add_pinyin({"right": "「打扰」是麻烦别人。（English: to disturb）", "wrong": [None, "「打听」是问消息。（English: ask）", "这个不对。", "「打开」不行。"]}, it)
        assert got["right"].startswith("「打扰」（dǎ rǎo）是") and (got["wrong"][1].startswith("「打听」（dǎ ting）") or got["wrong"][1].startswith("「打听」（dǎ tīng）")), got
        assert reading("东西") is None, "东西 dōng xī / dōng xi are two words: unsure, no pinyin"
        assert reading("似") is None or "/" in reading("似"), "似 is sì and shì (似的)"
        assert reading("长太") is None, "a character with two readings is never spelled out inside an unknown word"
        assert reading("不是", pair=True) == "bù shì"
        assert got["wrong"][2] == "这个不对。", "a line that never names its option is left alone"
        assert add_pinyin(got, it) == got, "added once"
        gl = add_pinyin({"right": "「虽然……但是」表示转折。（English: contrast）", "wrong": [None, "x", "y", "z"]},
                        {"options": ["虽然……但是", "因为……所以", "不但……而且", "如果……就"], "answer": 0, "stem": "s"})
        assert gl["right"].startswith("「虽然……但是」（suī rán……dàn shì）"), gl["right"]
        assert reading("长", "小树慢慢____大了。", own=True) in ("zhǎng", None), "never a wrong reading"
        assert reading("长") == "cháng / zhǎng", "a wrong character: all its readings"
        assert reading("都", pair=True) == "dōu" and reading("还", pair=True) == "hái"
        assert reading("项", "奶奶戴了一条非常漂亮的____链。", own=True) == "xiàng"
        half = add_pinyin({"right": "「虽然」后面要说事实。（English: x）", "wrong": [None, "a", "b", "c"]},
                          {"options": ["虽然……但是", "因为……所以", "不但……而且", "如果……就"], "answer": 0, "stem": "s"})
        assert half["right"].startswith("「虽然」（suī rán）后面"), half["right"]
        dot = add_pinyin({"right": "「虽然…但是」表示转折。（English: x）", "wrong": [None, "a", "b", "c"]},
                         {"options": ["虽然……但是", "因为……所以", "不但……而且", "如果……就"], "answer": 0, "stem": "s"})
        assert dot["right"].startswith("「虽然…但是」（suī rán……dàn shì）"), dot["right"]
        pr = {"options": ["虽然……但是", "因为……所以", "不但……而且", "如果……就"], "answer": 0, "stem": "s"}
        assert add_pinyin(dot, pr) == dot and add_pinyin(half, pr) == half, "a re-run adds no second pinyin"
        two = add_pinyin({"right": "r", "wrong": [None, "「而且」后面少了动词。（English: x）", "b", "c"]},
                         {"options": ["虽然……但是……", "不仅……而且", "每逢……", "如果……就……"], "answer": 0, "stem": "s"})
        assert two["wrong"][1].startswith("「而且」（ér qiě）"), two["wrong"][1]
        sen = add_pinyin({"right": "「紧急」是说情况很急，「紧急」不能这样用。（English: x）", "wrong": [None, "「长」不对。", "b", "c"]},
                         {"options": ["警察紧急赶往现场。", "x", "y", "z"], "answer": 0, "stem": "s"})
        assert sen["right"] == "「紧急」（jǐn jí）是说情况很急，「紧急」不能这样用。（English: x）", sen["right"]
        assert sen["wrong"][1] == "「长」不对。", "a character with two readings gets none"
        twice = add_pinyin({"right": "r", "wrong": [None, "「请求」是礼貌地请人帮忙，不说「请求」。（English: x）", "b", "c"]},
                           {"options": ["吩咐", "请求", "提问", "盼望"], "answer": 0, "stem": "s"})
        assert twice["wrong"][1].count("qǐng qiú") == 1, twice["wrong"][1]
        assert add_pinyin({"right": "r", "wrong": [None, "a", "b", "c"]}, {"options": ["他很好。", "x", "y", "z"], "answer": 0})["right"] == "r"
    zo = ["挑", "担", "抬", "提"]
    assert denum("正确答案是（2）担，因为要用扁担。（English: The answer is (2) 担.）", zo) == "正确答案是「担」，因为要用扁担。（English: The answer is 「担」.）"
    assert OPTNUM.search(denum("选（3）不对", zo)), "a number without its option stays, so opus_row rejects the line"
    assert denum("The answer is (2) hasn't.", ["doesn't", "hasn't", "isn't", "didn't"]) == 'The answer is "hasn\'t".'
    assert mentions_zh("「sǐ」是平舌音", "sǐ jìn") and not mentions_zh("「shǐ」是翘舌音", "sǐ jìn")
    assert not mentions_zh("这个句子用……不对", "不是……就是"), "the ellipsis alone is not a mention"
    assert denum("选项（3）中的“抬”不对。（English: Option (3) 'lift' is wrong.）", zo) == "选项中的“抬”不对。（English: Option 'lift' is wrong.）"
    pi = {"options": ["zhǐ xiào", "zǐ xiào", "chǐ xiào", "cǐ xiào"], "answer": 2, "stem": "大家都耻笑他的行为。"}
    assert aligned({"right": "「耻」读 chǐ，是翘舌送气音。", "wrong": ["声母是 ch，不是 zh。", "不是 z。", None, "不是 c。"]}, pi)
    assert not aligned({"right": "「担」读 dān。", "wrong": ["x", "y", None, "z"]}, pi), "a pinyin reason about another sentence"
    assert mentions_zh("「zù」这个读音不正确", "zù míng") and mentions_zh("「担」是挑东西的工具", "担") and not mentions_zh("意思不对", "担")
    zi = {"options": zo, "answer": 1}
    assert aligned({"right": "「担」是扁担的担。", "wrong": ["「挑」是动作。", None, "「抬」要两个人。", "「提」用手。"]}, zi)
    assert not aligned({"right": "这是对的。", "wrong": ["不对。", None, "不对。", "不对。"]}, zi), "Chinese lines must quote their options"
    opts = ["doesn't", "hasn't", "isn't", "didn't"]
    good = {"right": "Prefers is present simple, so the tag uses does: doesn't he?", "wrong": {"2": "Hasn't needs has as a helper.", "3": "Isn't needs is.", "4": "Didn't is past tense."}}
    assert shape(good, opts, 0) == {"right": good["right"], "wrong": [None, "Hasn't needs has as a helper.", "Isn't needs is.", "Didn't is past tense."]}
    assert shape(dict(good, wrong={"2": "x", "3": "y"}), opts, 0) is None, "every wrong option needs a reason"
    assert shape({"right": "ok", "wrong": good["wrong"]}, opts, 0) is None, "too short to explain anything"
    assert shape(parse("```json\n" + json.dumps(good) + "\n```"), opts, 0)["right"].startswith("Prefers")
    q = {"stem": "s", "options": opts, "answer": 0}
    assert fp(q) == fp(dict(q)) and fp(q) != fp(dict(q, answer=1)) and fp(q) != fp(dict(q, options=opts[::-1])), "a changed key or options is another version"
    it = {"fp": "f", "answer": 0, "options": opts}
    wl = [None, "\"Hasn't\" needs has.", "\"Isn't\" needs is.", "\"Didn't\" is past."]
    ok = {"id": "x", "fp": "f", "right": "A question tag repeats the helper, so \"doesn't he?\"", "wrong": wl}
    assert opus_row(ok, it)["wrong"] == wl
    assert opus_row(dict(ok, fp="g"), it) is None, "another question version"
    assert opus_row(dict(ok, wrong=["x"] + wl[1:]), it) is None, "the key's slot must be null"
    assert opus_row(dict(ok, wrong=wl[:3]), it) is None and opus_row(dict(ok, doubt="key?"), it) is None
    it2 = {"fp": "f", "answer": 2, "options": ["had...rush", "have...rush", "had...rushed", "have...rushed"]}
    e2 = {"id": "y", "fp": "f", "right": "\"Had I not rushed\" means if I had not rushed.", "wrong": ["\"Rush\" after had is wrong.", "\"Have\" cannot mean if; \"rush\" too.", None, "\"Have\" with \"rushed\" is wrong."]}
    assert opus_row(e2, it2), "multi-part options are matched part by part"
    assert opus_row(dict(e2, right="Fatigue means extreme tiredness."), it2) is None, "a reason about another question is dropped"
    assert mentions('To "incur" a fine means', "incurred") and mentions('When a storm "blows over"', "blow over")
    assert mentions('"Come across as" means', "came across") and not mentions("Fatigue means tiredness.", "incurred")
    print("explain selftest ok")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "pack":
        pack([Path(s) for s in sys.argv[2:] if s != "--zh"] or (SELS_ZH if "--zh" in sys.argv else SELS))
    elif cmd in ("write", "judge", "revise", "judge2"):
        run(sys.argv[2], cmd)
    elif cmd == "apply-opus":
        apply_opus(int(sys.argv[sys.argv.index("--sample") + 1]) if "--sample" in sys.argv else 0)
    elif cmd == "calib":
        calib()
    elif cmd == "calib-score":
        sys.exit(0 if calib_score() else 1)
    elif cmd == "apply":
        apply(int(sys.argv[sys.argv.index("--sample") + 1]) if "--sample" in sys.argv else 0)
    elif cmd == "selftest":
        selftest()
    else:
        sys.exit(__doc__)
