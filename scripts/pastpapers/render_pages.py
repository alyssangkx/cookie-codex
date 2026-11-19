#!/usr/bin/env python3
"""Render every past-paper PDF to 300 dpi grey JPEG pages in parallel (for the VLM run on the GPU server).

  python3 render_pages.py SRC OUT [--jobs 60]
  SRC = folder with "P6 Maths/", "P6 Science/", ... ; OUT/<subject>/<year>/pages/pNNNN.jpg (existing pages skipped)
Only the four subject folders are read (one compiled book per subject and year), like catalogue.py."""
import argparse, re, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

SUBJECTS = {"maths": "P6 Maths", "science": "P6 Science", "english": "P6 English", "chinese": "P6 Chinese"}
CHUNK = 20


def npages(pdf):
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    return int(re.search(r"^Pages:\s+(\d+)", out, re.M).group(1))


def render(job):
    pdf, first, last, d = job
    if all((d / f"p{p:04d}.jpg").exists() for p in range(first, last + 1)): return 0
    tmp = d / f".tmp{first}"
    tmp.mkdir(exist_ok=True)
    subprocess.run(["pdftoppm", "-r", "300", "-gray", "-jpeg", "-f", str(first), "-l", str(last), str(pdf), str(tmp / "p")],
                   check=True)
    n = 0
    for f in tmp.glob("p-*.jpg"):
        f.rename(d / f"p{int(f.stem.split('-')[1]):04d}.jpg"); n += 1
    tmp.rmdir()
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("out"); ap.add_argument("--jobs", type=int, default=60)
    a = ap.parse_args()
    jobs = []
    for subject, folder in SUBJECTS.items():
        for pdf in sorted((Path(a.src) / folder).glob("*.pdf")):
            year = re.search(r"(20\d\d)", pdf.name)
            if not year: continue
            d = Path(a.out) / subject / year.group(1) / "pages"
            d.mkdir(parents=True, exist_ok=True)
            n = npages(pdf)
            jobs += [(pdf, s, min(s + CHUNK - 1, n), d) for s in range(1, n + 1, CHUNK)]
    with ProcessPoolExecutor(a.jobs) as ex:
        print(sum(ex.map(render, jobs)), "pages rendered", flush=True)


if __name__ == "__main__":
    sys.exit(main())
