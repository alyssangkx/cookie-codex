"""Helpers shared by the reviewed-item bank builds (Chinese, English, Science)."""
import hashlib
import json
import re

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
