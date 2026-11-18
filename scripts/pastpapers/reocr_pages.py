"""Re-OCR pages whose margins carry a repeated school stamp (Henry Park's "HPPS" column down each side).

Tesseract reads each stamp row as a line of its own, merges it with the text line beside it ("HPPS roof as shown
below. -") and the question numbers and brackets are lost. This script re-renders the given pages from the PDF, finds
the stamp (a word that repeats 12+ times on the page, in one narrow column at the left or right edge), paints the stamp
columns white (the page edge up to the stamp, plus --pad px inward to take the rotated "Please do not write in the
margin" text too), and OCRs again exactly like catalogue.py (--psm 4, then the margin-number pass).

Pages with no repeated stamp word are skipped, so a page range can be given loosely.
The old files are kept as pNNNN.orig.tsv / pNNNN.m.orig.tsv (never overwritten twice); the page jpg is not touched.

    python3 scripts/pastpapers/reocr_pages.py --subject science --year 2024 --pages 315-355
    python3 scripts/pastpapers/reocr_pages.py --subject science --year 2024 --pages 870-956 --dry   # list, change nothing

Later it could become an option of the shared OCR: in catalogue.ocr_page, after pdftoppm, call strip_stamp(img, words)
on a first-pass TSV when a stamp is detected, then re-run tesseract on the cleaned image (see notes).
"""
import argparse, collections, os, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalogue as C


def stamp_columns(words, W, min_repeat=12):
    """-> (left_edge_x, right_edge_x): inner edges of the stamp columns, None where there is none. A stamp is the
    commonest word of 3+ letters that repeats min_repeat+ times and sits in the outer 12% of the page."""
    cnt = collections.Counter(w["text"] for w in words if len(w["text"]) >= 3 and w["conf"] >= 30)
    out = [None, None]
    for text, n in cnt.most_common(5):
        if n < min_repeat: break
        side = [w for w in words if w["text"] == text]
        left = [w for w in side if w["right"] < 0.12 * W]
        right = [w for w in side if w["left"] > 0.88 * W]
        if len(left) >= min_repeat // 2 and out[0] is None: out[0] = max(w["right"] for w in left)
        if len(right) >= min_repeat // 2 and out[1] is None: out[1] = min(w["left"] for w in right)
    return out


def strip_stamp(img, left_x, right_x, pad):
    """Paint the stamp columns white. img is a PIL image (mode L)."""
    from PIL import ImageDraw
    W, H = img.size
    d = ImageDraw.Draw(img)
    if left_x is not None: d.rectangle([0, 0, left_x + pad, H], fill=255)
    if right_x is not None: d.rectangle([right_x - pad, 0, W, H], fill=255)
    return img


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subject", required=True, choices=list(C.SUBJECTS))
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--pages", required=True, help="page range, e.g. 315-355")
    ap.add_argument("--pad", type=int, default=110, help="px painted inward past the stamp (default 110: rotated margin text)")
    ap.add_argument("--min-repeat", type=int, default=12)
    ap.add_argument("--keep-clean", action="store_true", help="keep the cleaned images in pages/clean/ for a look")
    ap.add_argument("--dry", action="store_true", help="only list the pages that have a stamp")
    a = ap.parse_args()

    from PIL import Image
    subject, year, pdf = next(C.pdfs(a.subject, a.year))
    d = C.OUT / subject / str(year) / "pages"
    clean = d / "clean"; clean.mkdir(exist_ok=True)
    env = {**os.environ, "OMP_THREAD_LIMIT": "1"}
    done = 0
    for p in C.page_range(a.pages, C.npages(pdf)):
        tsv, mtsv = d / f"p{p:04d}.tsv", d / f"p{p:04d}.m.tsv"
        if not tsv.exists(): continue
        W, H, words, _ = C.read_tsv(d / f"p{p:04d}.orig.tsv" if (d / f"p{p:04d}.orig.tsv").exists() else tsv)
        lx, rx = stamp_columns(words, W, a.min_repeat)
        if lx is None and rx is None: continue
        print(f"p{p}: stamp columns left<{lx} right>{rx}", flush=True)
        if a.dry: continue
        # re-render exactly as catalogue.ocr_page does
        raw = clean / f".r{p:04d}"
        subprocess.run([str(C.BIN / "pdftoppm"), "-r", str(C.DPI), "-gray", "-jpeg", "-jpegopt", "quality=90",
                        "-f", str(p), "-l", str(p), "-singlefile", str(pdf), str(raw)], check=True)
        img = Image.open(f"{raw}.jpg").convert("L")
        os.unlink(f"{raw}.jpg")
        jpg = clean / f"p{p:04d}.jpg"
        strip_stamp(img, lx, rx, a.pad).save(jpg, quality=90)
        # keep the first-pass files once
        orig, morig = d / f"p{p:04d}.orig.tsv", d / f"p{p:04d}.m.orig.tsv"
        if not orig.exists(): shutil.copy2(tsv, orig)
        if mtsv.exists() and not morig.exists(): shutil.copy2(mtsv, morig)
        tmp = d / f".t{p:04d}"
        subprocess.run([str(C.BIN / "tesseract"), str(jpg), str(tmp), "-l", C.LANG.get(subject, "eng"), "--psm", "4", "tsv"],
                       check=True, capture_output=True, env=env)
        os.replace(f"{tmp}.tsv", tsv)
        C.ocr_margin(jpg, tsv, mtsv)
        if not a.keep_clean: jpg.unlink()
        done += 1
    print(f"re-OCR'd {done} pages" + (" (dry run)" if a.dry else ""))


if __name__ == "__main__":
    main()
