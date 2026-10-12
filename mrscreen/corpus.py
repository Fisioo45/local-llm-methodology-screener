"""Corpus access: parsed papers, passages, and the pilot/dev/test/sandbox sets.

Sets are recomputed from the workbook's `eligible` column with exactly the rule
the workbook formula uses (first 20 eligible = pilot, 21-40 = dev, 41-200 = test),
so the result does not depend on Excel having cached formula values.

SANDBOX = papers with order_no >= SANDBOX_START. They are never annotated (the
annotator stops after ~200 eligible papers, well before this point), so they are
the only papers used for building and smoke-testing before gold labels exist.
"""
import csv
import json
import os
import re
from dataclasses import dataclass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPER_DIR = os.path.join(ROOT, "data", "processed", "papers")
ORDER_CSV = os.path.join(ROOT, "data", "processed", "annotation_order.csv")
WORKBOOK = os.path.join(ROOT, "annotation_sheet_v1.3.xlsx")          # the frozen gold workbook (v1.3)
if not os.path.exists(WORKBOOK):
    WORKBOOK = os.path.join(ROOT, "annotation_sheet.xlsx")
SANDBOX_START = 301
PILOT_N, DEV_N, TEST_N = 20, 20, 80   # test reduced to 80 on 2026-09-26 (protocol v1.2 re-annotation)


@dataclass
class Passage:
    pid: int
    path: str       # section heading path, e.g. "Methods > Dataset"
    text: str
    in_back: bool   # back matter (availability statements etc.)


def approx_tokens(text: str) -> int:
    """Cheap token estimate (~4 characters per token for English scientific text)."""
    return max(1, len(text) // 4)


def load_paper(pmcid: str) -> dict:
    with open(os.path.join(PAPER_DIR, f"{pmcid}.json"), encoding="utf-8") as f:
        return json.load(f)


def passages(paper: dict, max_words: int = 180) -> list:
    """Split sections into paragraph-sized passages, keeping document order."""
    out = []
    def add(path, text, back):
        words = text.split()
        for i in range(0, len(words), max_words):
            chunk = " ".join(words[i:i + max_words])
            if chunk.strip():
                out.append(Passage(len(out), path, chunk, back))
    for sec in paper["sections"]:
        for para in sec["text"].split("\n"):
            add(sec["path"], para, False)
    for b in paper["back"]:
        add(f"Back matter: {b.get('title') or b.get('tag')}", b["text"], True)
    return out


def full_text(paper: dict) -> str:
    parts = [paper.get("title", ""), paper.get("abstract", "")]
    parts += [f"{s['path']}\n{s['text']}" for s in paper["sections"]]
    parts += [f"{b.get('title') or b.get('tag')}\n{b['text']}" for b in paper["back"]]
    return "\n\n".join(parts)


def read_order() -> list:
    with open(ORDER_CSV, encoding="utf-8") as f:
        return [dict(r, order_no=int(r["order_no"])) for r in csv.DictReader(f)]


def assign_sets(eligible_by_order: dict) -> dict:
    """eligible_by_order: {order_no: 'Y'|'N'|''} -> {order_no: set name}."""
    sets, n = {}, 0
    for order_no in sorted(eligible_by_order):
        if eligible_by_order[order_no] != "Y":
            continue
        n += 1
        sets[order_no] = ("pilot" if n <= PILOT_N else "dev" if n <= PILOT_N + DEV_N
                          else "test" if n <= PILOT_N + DEV_N + TEST_N else "extra")
    return sets


QC_FILE = os.path.join(ROOT, "configs", "qc_excluded.json")


def qc_excluded() -> set:
    """order_no values removed from the gold standard by quality control (configs/qc_excluded.json)."""
    if not os.path.exists(QC_FILE):
        return set()
    with open(QC_FILE, encoding="utf-8") as f:
        spec = json.load(f)
    return {o for e in spec.get("excluded", []) for o in range(e["orders"][0], e["orders"][1] + 1)}


def read_gold(workbook: str = WORKBOOK) -> dict:
    """Return {pmcid: {'order_no', 'set', 'eligible', <item>: label, <item>_evidence: text}}.
    The fictional EXAMPLE row (order_no 'EX') is ignored."""
    from openpyxl import load_workbook
    ws = load_workbook(workbook, read_only=True, data_only=True)["Annotation"]
    rows = ws.iter_rows(values_only=True)
    head = list(next(rows))
    recs = []
    for r in rows:
        rec = dict(zip(head, r))
        if not isinstance(rec.get("order_no"), (int, float)):
            continue
        rec["order_no"] = int(rec["order_no"])
        rec["eligible"] = (rec.get("eligible") or "").strip().upper()
        recs.append(rec)
    sets = assign_sets({r["order_no"]: r["eligible"] for r in recs})
    excluded = qc_excluded()
    gold = {}
    for r in recs:
        r["set"] = "qc_excluded" if r["order_no"] in excluded and r["eligible"] == "Y" else sets.get(r["order_no"], "")
        for k, v in list(r.items()):
            if isinstance(v, str):
                r[k] = v.strip()
        gold[r["pmcid"]] = r
    return gold


def select(which: str, gold: dict = None) -> list:
    """Return pmcids for 'pilot' | 'dev' (pilot+dev) | 'test' | 'sandbox[:N]' | 'PMC1,PMC2'."""
    order = read_order()
    if which.startswith("sandbox"):
        n = int(which.split(":")[1]) if ":" in which else None
        ids = [r["pmcid"] for r in order if r["order_no"] >= SANDBOX_START]
        return ids[:n] if n else ids
    if which.startswith("PMC"):
        return [p.strip() for p in which.split(",") if p.strip()]
    gold = gold if gold is not None else read_gold()
    wanted = {"pilot": {"pilot"}, "dev": {"pilot", "dev"}, "test": {"test"}}[which]
    ids = [p for p, g in gold.items() if g["set"] in wanted]
    return sorted(ids, key=lambda p: gold[p]["order_no"])


_WS = re.compile(r"\s+")
def norm_space(s: str) -> str:
    return _WS.sub(" ", s).strip()
