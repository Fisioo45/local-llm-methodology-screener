"""Freeze the gold standard so it cannot change unnoticed.

  python -m mrscreen.freeze annotation_sheet_v1.3.xlsx            # write data/gold/gold_frozen.csv + configs/gold_freeze.json
  python -m mrscreen.freeze annotation_sheet_v1.3.xlsx --verify   # check the workbook still matches the frozen labels

The hash covers the LABELS and EVIDENCE of every eligible pilot/dev/test paper, written to a
canonical CSV (fixed column order, sorted by order_no, normalised whitespace). Re-saving the
workbook in Excel does not change the hash; changing any label or quote does.
"""
import argparse
import csv
import datetime
import hashlib
import io
import json
import os
import re
import sys

from . import corpus
from .items import ITEMS, TEST_ITEMS

OUT_CSV = os.path.join(corpus.ROOT, "data", "gold", "gold_frozen.csv")
OUT_JSON = os.path.join(corpus.ROOT, "configs", "gold_freeze.json")


def canonical(workbook):
    gold = corpus.read_gold(workbook)
    rows = sorted((g for g in gold.values() if g["eligible"] == "Y" and g["set"] in ("pilot", "dev", "test")),
                  key=lambda g: g["order_no"])
    cols = ["order_no", "pmcid", "set"]
    for it in ITEMS:
        cols += [it.code, it.code[:2] + "_evidence"]
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(cols)
    counts = {}
    for g in rows:
        active = [it.code for it in ITEMS] if g["set"] != "test" else list(TEST_ITEMS)
        out = [g["order_no"], g["pmcid"], g["set"]]
        for it in ITEMS:
            lab = (g.get(it.code) or "").strip().upper() if it.code in active else ""
            ev = re.sub(r"\s+", " ", str(g.get(it.code[:2] + "_evidence") or "")).strip() if it.code in active else ""
            out += [lab, ev]
        w.writerow(out)
        counts[g["set"]] = counts.get(g["set"], 0) + 1
    text = buf.getvalue()
    return text, hashlib.sha256(text.encode("utf-8")).hexdigest(), counts


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("workbook")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)
    text, sha, counts = canonical(a.workbook)
    if a.verify:
        with open(OUT_JSON, encoding="utf-8") as f:
            ref = json.load(f)
        ok = ref["sha256"] == sha
        print(f"frozen {ref['sha256'][:16]}  now {sha[:16]}  ->  {'OK, gold unchanged' if ok else 'CHANGED since freeze'}")
        return 0 if ok else 1
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    meta = {"sha256": sha, "papers": counts, "codebook": "v1.3 (test: A1, A4, B2, C1, C2)",
            "workbook": os.path.basename(a.workbook),
            "frozen_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "rule": "No label or quote may change after this point. Any correction must be logged with a reason "
                    "and reported in the paper; the original frozen file is kept."}
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"gold frozen: {counts}  sha256 {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
