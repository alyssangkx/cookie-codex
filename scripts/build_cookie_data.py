"""Build site/src/data/cookies.json: rarity from noff.gg, lore from the CRK fandom wiki API."""
import csv
import html
import json
import re
import shutil
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT / "downloads" / "crk_cookies"
SITE = ROOT / "site"
OUT = SITE / "src" / "data" / "cookies.json"
LIST_PAGE = "https://www.noff.gg/cookie-run-kingdom/cookies"
WIKI_API = "https://cookierunkingdom.fandom.com/api.php"
WIKI_PAGE = "https://cookierunkingdom.fandom.com/wiki/"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}

# Fixed vocabulary. A tag applies only if one of its words appears in the cookie's Personality text.
TAGS = {
    "Brave": ["brave", "courage", "courageous", "fearless", "valiant", "heroic", "bold"],
    "Gentle": ["gentle", "kind", "kindness", "caring", "compassionate", "warm-hearted", "soft-spoken", "tender"],
    "Cheerful": ["cheerful", "bubbly", "upbeat", "optimistic", "energetic", "happy-go-lucky", "lively", "enthusiastic"],
    "Mysterious": ["mysterious", "enigmatic", "secretive", "cryptic", "aloof"],
    "Proud": ["proud", "arrogant", "pride", "vain", "haughty", "egotistical", "conceited"],
    "Wise": ["wise", "wisdom", "knowledgeable", "intelligent", "scholarly", "intellectual"],
    "Mischievous": ["mischievous", "prankster", "pranks", "playful", "troublemaker", "cheeky"],
    "Shy": ["shy", "timid", "introverted", "nervous", "reserved", "anxious"],
    "Hot-headed": ["hot-headed", "short-tempered", "temper", "impulsive", "reckless", "aggressive", "hot-tempered"],
    "Calm": ["calm", "composed", "collected", "serene", "stoic", "level-headed", "patient"],
    "Loyal": ["loyal", "loyalty", "devoted", "dedicated", "faithful", "protective"],
    "Curious": ["curious", "curiosity", "adventurous", "inquisitive", "explore", "exploring"],
}


def get(session, url, **params):
    for attempt in range(3):
        r = session.get(url, params=params or None, timeout=30)
        if r.status_code == 429:
            raise SystemExit(f"429 from {url}: stopping, as the brief asks")
        if r.ok:
            return r
        time.sleep(2 * (attempt + 1))
    r.raise_for_status()


def noff_cookies(session):
    page = get(session, LIST_PAGE).text
    rarity_map = json.loads(re.search(r"rarityMap\s*=\s*(\{[^}]*\})", page).group(1))
    pattern = re.compile(
        r'<a href="/cookie-run-kingdom/cookie/([^"]+)" class="([^"]+)"[^>]*>.*?'
        r'<img src="([^"]+)" alt="([^"]+)"', re.S)
    cookies = [{"slug": slug, "rarity": rarity, "src": src, "name": html.unescape(alt)}
               for slug, rarity, src, alt in pattern.findall(page)]
    return cookies, rarity_map


def section_text(page_html, anchor):
    """Plain text between the heading with this anchor id and the next heading."""
    m = re.search(rf'<h[234][^>]*>\s*<span[^>]*id="{anchor}"', page_html)
    if not m:
        return ""
    body = page_html[m.end():]
    body = body[body.find("</h") :]
    body = body[body.find(">") + 1 :]
    nxt = re.search(r"<h[234][\s>]", body)
    body = body[: nxt.start()] if nxt else body
    body = re.sub(r"<(style|script|table)\b.*?</\1>", "", body, flags=re.S)
    body = re.sub(r'<sup[^>]*class="reference".*?</sup>', "", body, flags=re.S)
    body = re.sub(r"<br\s*/?>|</p>|</li>|</div>", "\n", body)
    text = html.unescape(re.sub(r"<[^>]+>", "", body))
    text = re.sub(r"\[\d+\]|\[edit\]", "", text)
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines()]
    return "\n\n".join(ln for ln in lines if ln)


def wiki_lore(session, name):
    data = get(session, WIKI_API, action="parse", page=name, prop="text",
               redirects=1, format="json").json()
    if "error" in data:  # title mismatch: fall back to the wiki's own search
        hits = get(session, WIKI_API, action="query", list="search", srsearch=name,
                   srlimit=1, format="json").json()["query"]["search"]
        if not hits:
            return None
        data = get(session, WIKI_API, action="parse", page=hits[0]["title"], prop="text",
                   redirects=1, format="json").json()
        if "error" in data:
            return None
    page_html = data["parse"]["text"]["*"]
    title = data["parse"]["title"]
    return {
        "backstory": section_text(page_html, "Game_Description"),
        "personality": section_text(page_html, "Personality"),
        "wikiUrl": WIKI_PAGE + title.replace(" ", "_"),
    }


def tags_for(personality):
    words = personality.lower()
    hits = []
    for tag, keys in TAGS.items():
        n = sum(len(re.findall(rf"\b{re.escape(k)}\b", words)) for k in keys)
        if n:
            hits.append((n, tag))
    hits.sort(key=lambda h: (-h[0], list(TAGS).index(h[1])))
    return [tag for _, tag in hits[:3]]


def main():
    s = requests.Session()
    s.headers.update(UA)
    cookies, rarity_map = noff_cookies(s)
    with open(IMAGES / "manifest.csv") as f:
        by_url = {row["image_url"]: row["filename"] for row in csv.DictReader(f)}

    public = SITE / "public" / "cookies"
    public.mkdir(parents=True, exist_ok=True)
    out, misses = [], {"image": [], "backstory": [], "personality": [], "page": []}
    for i, c in enumerate(cookies, 1):
        filename = by_url.get("https://www.noff.gg" + c["src"])
        if filename and (IMAGES / filename).exists():
            shutil.copy2(IMAGES / filename, public / filename)
        else:
            misses["image"].append(c["name"])
        lore = wiki_lore(s, c["name"]) or {"backstory": "", "personality": "", "wikiUrl": ""}
        if not lore["wikiUrl"]:
            misses["page"].append(c["name"])
        for k in ("backstory", "personality"):
            if not lore[k]:
                misses[k].append(c["name"])
        out.append({
            "slug": c["slug"], "name": c["name"], "rarity": c["rarity"],
            "image": f"/cookies/{filename}" if filename else "",
            "backstory": lore["backstory"], "personality": lore["personality"],
            "personalityTags": tags_for(lore["personality"]), "wikiUrl": lore["wikiUrl"],
        })
        print(f"[{i}/{len(cookies)}] {c['name']}", flush=True)
        time.sleep(0.5)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    order = sorted(rarity_map, key=rarity_map.get, reverse=True)
    OUT.write_text(json.dumps({"rarityOrder": order, "tags": list(TAGS), "cookies": out},
                              indent=1, ensure_ascii=False))

    n = len(out)
    print(f"\ncookies: {n}")
    print("rarity map:", rarity_map)
    counts = {}
    for c in out:
        counts[c["rarity"]] = counts.get(c["rarity"], 0) + 1
    print("per rarity:", dict(sorted(counts.items(), key=lambda kv: -kv[1])))
    for k, v in misses.items():
        print(f"with {k}: {n - len(v)}/{n}" + (f"  missing: {', '.join(v)}" if v else ""))
    tag_counts = {t: sum(t in c["personalityTags"] for c in out) for t in TAGS}
    print("tags:", tag_counts, "| untagged:", sum(not c["personalityTags"] for c in out))


if __name__ == "__main__":
    main()
