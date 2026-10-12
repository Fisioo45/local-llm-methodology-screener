"""Self-check an annotation workbook before sending a batch.  (v0.13)

  python -m mrscreen.check_annotations annotation_sheet.xlsx
  python -m mrscreen.check_annotations annotation_sheet.xlsx --from 47 --to 120

For every eligible, labelled paper it reports:
  INVALID_LABEL   label not allowed for the item (codebook v1.1)
  MISSING_LABEL   one of the 11 labels is empty
  NO_EVIDENCE     SAFE/RISK/YES/PUBLIC/RESTRICTED/REQUEST with ABSENT or empty evidence
  NOT_IN_PAPER    a quote that cannot be found in THIS paper's text
  IN_OTHER_PAPER  the quote is not in this paper but is found in another annotated paper
                  (usually copied from the wrong browser tab)
  NO_VERSION      codebook_version not set
  NOT_CODE        C1 is YES/REQUEST but the quote does not mention code (e.g. it is a DATA statement)
  OTHERS_CODE     C1 is YES but the quoted link is a known library/framework (MONAI, PyTorch, timm...)
                  - YES only if the paper links ITS OWN code
  POSSIBLE_MISS   the label says "not reported" but the text contains a clear signal
                  (a code-repository link, a metric with 95% CI or ±, the word duplicate,
                  a data-availability statement). Re-read that passage and decide; the
                  flag never changes a label by itself. If you re-read it and your label
                  stays, write "checked C1" (or the item's code) in notes to silence it.
Fuzzy matches (small typography differences) are accepted.
Writes <workbook>_check.csv and exits with code 1 if anything needs fixing.
"""
import argparse
import csv
import os
import re
import sys

from . import corpus
from .items import ITEMS, ITEM_BY_CODE, TEST_ITEMS
from .verify import Verifier

SUBSTANTIVE = {"SAFE", "RISK", "YES", "PUBLIC", "RESTRICTED", "REQUEST"}
ABSENT_WORDS = {"", "ABSENT", "NO EVIDENCE", "NONE", "N/A", "NA", "-", "NOT REPORTED", "NOT STATED"}
CODE_WORDS = r"\b(codes?|software|scripts?|implementation|programs?|github|gitlab|bitbucket|source code|model weights|notebooks?)\b"

# (item, labels that claim "not reported", signal regex) - used only to prompt a re-read
MISS_SIGNALS = [
    ("C1_code_available", {"NO"}, r".{0,120}((github\.com|gitlab\.com|zenodo\.org|bitbucket\.org|huggingface\.co|codeocean\.com)/[\w\-./]+|doi\.org/10\.5281/zenodo\.\d+)"),
    ("B2_variability_reported", {"NO"}, r".{0,60}(auc|auroc|accuracy|sensitivity|specificity|f1|dice|precision|recall|iou|kappa)(?:[^.]|\.\d){0,80}(95\s?%\s?(ci|confidence)|±).{0,40}"),
    ("A5_duplicate_check", {"NO"}, r".{0,80}duplicat.{0,80}"),
    ("C2_data_available", {"NO"}, r"(data availability|availability of data|data sharing)( statement)?.{0,160}"),
]


# v0.12: fewer false alarms
REFUSAL = r"(cannot|can ?not|could not|unable to|will not|are not|is not|not be)\s+(be\s+)?(publicly\s+|openly\s+)?(shared|available|made available|released|distributed|disclosed)|not (readily|publicly) available|no (new )?(data|datasets?) (were|was) (generated|analy[sz]ed)|\bunavailable\b|not available|prohibit"
ACCESS = r"availab|request|access|deposit|download|provided|included|kaggle|https?://|repositor|supplementa"
THIRD_PARTY_CONTEXT = r"(librar|toolkit|toolbox|package|framework|open[- ]source|pre-?trained|implementation (of|from|by)|we (used|utili[sz]ed|adopted|employed)|based on|official (code|implementation))"
KNOWN_LIBS = r"(github\.com/(project-monai|pytorch|huggingface|tensorflow|keras-team|scikit-learn|ultralytics|facebookresearch|google-research|google|openai|microsoft|mit-han-lab|open-mmlab|milesial|qubvel|rwightman|huggingface|jacobgil|mic-dkfz|nvidia|nvlabs|isbi|albumentations-team|opencv)/)"


def c1_link_miss(text):
    """First repository link whose context does not look like a third-party tool, else None."""
    rx = r"((github\.com|gitlab\.com|zenodo\.org|bitbucket\.org|huggingface\.co|codeocean\.com)/[\w\-./]+|doi\.org/10\.5281/zenodo\.\d+)"
    for m in re.finditer(rx, text, re.I):
        before = text[max(0, m.start() - 160):m.start()]
        if re.search(KNOWN_LIBS, m.group(0), re.I) or re.search(THIRD_PARTY_CONTEXT, before, re.I):
            continue
        near = before[-120:]
        if re.search(r"\b(data|datasets?|database|images|spectra|scans|repositor(y|ies))\b", near, re.I) and not re.search(r"\bcodes?\b|software|implementation", near, re.I):
            continue                                       # a data repository, not code
        return text[max(0, m.start() - 120):m.end()]
    return None


def c2_statement_miss(text):
    """A data statement that offers access (not a refusal), else None."""
    rx = r"(data availability|availability of data( and materials?)?|data sharing)( statement)?"
    for m in re.finditer(rx, text, re.I):
        window = re.sub(r"^\s*((data availability|availability of data)( statement)?:?\s*)+", "", text[m.end():m.end() + 300], flags=re.I)
        if re.match(r"\s*(challenge|issue|problem|constraint|limitation|is (a|often)|remains)", window, re.I):
            continue                                       # prose about data availability, not a statement
        head = window[:140]
        if re.search(r"\bcodes?\b", head, re.I) and not re.search(r"\bdata(set)?s?\b", head, re.I):
            continue                                       # a code statement filed under "data availability"
        if re.search(REFUSAL, window, re.I):
            return None                                    # the statement refuses sharing -> NO is plausible
        if re.search(ACCESS, window, re.I):
            return m.group(0) + window[:200]
    return None


def spans(evidence: str) -> list:
    return [s.strip() for s in evidence.split("||") if s.strip()]


def check(workbook, lo=None, hi=None, items=None):
    gold = corpus.read_gold(workbook)
    rows = sorted((g for g in gold.values() if g["eligible"] == "Y" and g["set"] != "qc_excluded"), key=lambda g: g["order_no"])
    rows = [g for g in rows if (lo is None or g["order_no"] >= lo) and (hi is None or g["order_no"] <= hi)]
    verifiers = {}
    def ver(pmcid):
        if pmcid not in verifiers:
            verifiers[pmcid] = Verifier(corpus.full_text(corpus.load_paper(pmcid)))
        return verifiers[pmcid]
    problems, n_quotes, n_ok = [], 0, 0
    for g in rows:
        required = [ITEM_BY_CODE[c] for c in TEST_ITEMS] if (items == "test5" or g["set"] not in ("pilot", "dev")) else ITEMS
        labelled = [it for it in required if (g.get(it.code) or "").strip()]
        if not labelled:
            continue                                   # not started yet
        notes = str(g.get("notes") or "").lower()
        text = re.sub(r"\s+", " ", corpus.full_text(corpus.load_paper(g["pmcid"])))
        for code, absent, rx in MISS_SIGNALS:
            if f"checked {code[:2].lower()}" in notes:
                continue                                   # annotator re-read this and kept the label
            if code in {it.code for it in required} and (g.get(code) or "").strip().upper() in absent:
                if code == "C1_code_available":
                    hit = c1_link_miss(text)
                elif code == "C2_data_available":
                    hit = c2_statement_miss(text)
                else:
                    m = re.search(rx, text, re.I)
                    hit = m.group(0) if m else None
                if hit:
                    problems.append((g, code, "POSSIBLE_MISS", "text says: ..." + hit[:200]))
        if not str(g.get("codebook_version") or "").strip():
            problems.append((g, "-", "NO_VERSION", "type 1.3 in the codebook_version column"))

        for it in required:
            lab = (g.get(it.code) or "").strip().upper()
            ev = (g.get(it.code[:2] + "_evidence") or "").strip()
            if not lab:
                problems.append((g, it.code, "MISSING_LABEL", "")); continue
            if lab not in it.labels:
                problems.append((g, it.code, "INVALID_LABEL", f"{lab} not in {'/'.join(it.labels)}")); continue
            if ev.upper() in ABSENT_WORDS:
                if lab in SUBSTANTIVE:
                    problems.append((g, it.code, "NO_EVIDENCE", f"{lab} needs a quote"))
                continue
            if it.code == "C1_code_available" and lab in ("YES", "REQUEST") and not re.search(CODE_WORDS, ev, re.I):
                problems.append((g, it.code, "NOT_CODE", "C1 is about CODE; this quote is about data. Data on request does not make C1 = REQUEST."))
            if it.code == "C1_code_available" and lab == "YES" and re.search(KNOWN_LIBS, ev, re.I):
                problems.append((g, it.code, "OTHERS_CODE", "this link is a known library/framework, not this study's code; YES only if the paper links its own code (write 'checked C1' if it is theirs)"))
            for q in spans(ev):
                n_quotes += 1
                if ver(g["pmcid"]).check(q) in ("exact", "fuzzy"):
                    n_ok += 1; continue
                other = [o["order_no"] for o in rows if o["pmcid"] != g["pmcid"] and ver(o["pmcid"]).check(q) in ("exact", "fuzzy")]
                if other:
                    problems.append((g, it.code, "IN_OTHER_PAPER", f"quote found in paper #{other[0]}: {q[:90]}"))
                else:
                    problems.append((g, it.code, "NOT_IN_PAPER", q[:120]))
    return rows, problems, n_quotes, n_ok


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("workbook")
    ap.add_argument("--from", dest="lo", type=int, default=None)
    ap.add_argument("--to", dest="hi", type=int, default=None)
    ap.add_argument("--items", default=None, choices=["test5"], help="check only the 5 test items (use for the re-rating sheet)")
    a = ap.parse_args(argv)
    rows, problems, nq, ok = check(a.workbook, a.lo, a.hi, a.items)
    out = os.path.splitext(a.workbook)[0] + "_check.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["order_no", "pmcid", "item", "problem", "detail"])
        for g, item, kind, detail in problems:
            w.writerow([g["order_no"], g["pmcid"], item, kind, detail])
    print(f"papers checked: {len(rows)} | quotes: {nq}, found in the paper: {ok}")
    if not problems:
        print("OK - nothing to fix.")
        return 0
    for g, item, kind, detail in problems:
        print(f"  #{g['order_no']:<4} {item:26s} {kind:15s} {detail}")
    print(f"{len(problems)} problem(s); list saved to {out}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
