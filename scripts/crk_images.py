"""Download every Cookie Run: Kingdom cookie portrait from noff.gg."""
import csv
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import requests

PAGE = "https://www.noff.gg/cookie-run-kingdom/cookies"
IMG_DIR = "/cookie-run-kingdom/res/img/cookies-standing/"
OUT = Path(__file__).resolve().parent.parent / "downloads" / "crk_cookies"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}


class CookieImgs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.found = {}  # url -> name; dict keeps page order and dedupes

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "img" and IMG_DIR in a.get("src", ""):
            self.found.setdefault(urljoin(PAGE, a["src"]), a.get("alt") or "")


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def main():
    s = requests.Session()
    s.headers.update(HEADERS)
    r = s.get(PAGE, timeout=30)
    r.raise_for_status()
    p = CookieImgs()
    p.feed(r.text)
    print(f"found {len(p.found)} cookies")

    OUT.mkdir(parents=True, exist_ok=True)
    rows, failed = [], []
    for url, name in p.found.items():
        ext = Path(url).suffix
        base = slug(name) or Path(url).stem
        dest = OUT / f"{base}{ext}"
        n = 2
        while any(row[2] == dest.name for row in rows):  # two cookies, same slug
            dest = OUT / f"{base}_{n}{ext}"
            n += 1
        rows.append((name, url, dest.name))
        if dest.exists():
            continue
        try:
            img = s.get(url, timeout=30)
            img.raise_for_status()
            dest.write_bytes(img.content)
        except requests.RequestException as e:
            failed.append((url, str(e)))
        time.sleep(0.5)

    with open(OUT / "manifest.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "image_url", "filename"])
        w.writerows(rows)

    print(f"downloaded/present {len(rows) - len(failed)}/{len(rows)}")
    for url, err in failed:
        print("FAILED", url, err)


if __name__ == "__main__":
    main()
