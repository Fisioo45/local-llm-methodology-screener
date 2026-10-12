"""Evaluate one or more runs against the gold standard.

  python -m mrscreen.evaluate --set dev --runs runs/rules_per_item_b1800_k1_dev runs/ollama_qwen3-8b_...
  python -m mrscreen.evaluate --set test --runs ... --out results/test
  python -m mrscreen.evaluate --intra-rater annotation_sheet.xlsx rerating_sheet.xlsx

Each run is scored under two label policies: 'raw' (model label as given) and
'verified' (substantive labels without a verifiable quote are downgraded).
Outputs CSV tables and a markdown summary in --out.
"""
import argparse
import csv
import json
import math
import os
from collections import defaultdict

from . import corpus, stats
from .items import ITEMS, ITEM_BY_CODE, LEAKAGE_ITEMS, ITEM_SETS
from .verify import apply_policy

POSITIVE = {"A5_duplicate_check": "YES", "B1_external_validation": "YES", "B2_variability_reported": "YES",
            "B3_stat_test_for_claim": "YES", "C1_code_available": "YES", "C2_data_available": "PUBLIC"}


ACTIVE = list(ITEMS)          # set in main() from --items


def gold_labels(gold, ids):
    """Only eligible papers whose active-item labels are all filled count."""
    out = {}
    for p in ids:
        g = gold[p]
        if g["eligible"] != "Y":
            continue
        labs = {it.code: (g.get(it.code) or "").strip().upper() for it in ACTIVE}
        if all(labs.values()):
            out[p] = labs
    return out


def load_run(run_dir):
    preds = defaultdict(dict)
    with open(os.path.join(run_dir, "predictions.jsonl"), encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                preds[r["pmcid"]][r["item"]] = r
    meta = json.load(open(os.path.join(run_dir, "run_meta.json"), encoding="utf-8"))
    return meta, preds


def final_label(row, policy):
    it = ITEM_BY_CODE[row["item"]]
    lab = row["label_raw"] or it.absent_label          # unparseable output -> silence label
    return apply_policy(it, lab, row["evidence_status"], policy, row.get("evidence"))


def fmt(x, d=3):
    return "NA" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}"


def evaluate_run(name, preds, gold, policy, boot):
    ids = [p for p in gold if p in preds and all(it.code in preds[p] for it in ACTIVE)]
    rows, correct = [], {}
    leak = [c for c in LEAKAGE_ITEMS if c in {it.code for it in ACTIVE}]
    for it in ACTIVE:
        y = [gold[p][it.code] for p in ids]
        yh = [final_label(preds[p][it.code], policy) for p in ids]
        correct[it.code] = [a == b for a, b in zip(y, yh)]
        acc, kap, mf1 = stats.accuracy(y, yh), stats.cohen_kappa(y, yh), stats.macro_f1(y, yh)
        k_lo, k_hi = stats.bootstrap_ci(stats.cohen_kappa, y, yh, b=boot) if boot else (float("nan"),) * 2
        f_lo, f_hi = stats.bootstrap_ci(stats.macro_f1, y, yh, b=boot) if boot else (float("nan"),) * 2
        pos = "RISK" if it.kind == "risk" else POSITIVE[it.code]
        sp = stats.sens_ppv(y, yh, pos)
        rows.append({"run": name, "policy": policy, "item": it.code, "n": len(ids), "accuracy": acc,
                     "kappa": kap, "kappa_lo": k_lo, "kappa_hi": k_hi, "macro_f1": mf1, "macro_f1_lo": f_lo,
                     "macro_f1_hi": f_hi, "positive": pos, "sensitivity": sp["sensitivity"], "ppv": sp["ppv"],
                     "support": sp["support"], "specificity": float("nan")})
    # paper-level outcomes
    #  any_leakage_risk     : at least one of A1-A4 is RISK (rare; wide CIs expected)
    #  not_verifiably_safe  : at least one of A1-A4 is RISK or UNCLEAR, i.e. a reader cannot confirm
    #                         leak-free partitioning from the text (the screener's "flag for review")
    for pname, bad in (("PAPER_any_leakage_risk", {"RISK"}), ("PAPER_not_verifiably_safe", {"RISK", "UNCLEAR"})):
        y = ["FLAG" if any(gold[p][c] in bad for c in leak) else "OK" for p in ids]
        yh = ["FLAG" if any(final_label(preds[p][c], policy) in bad for c in leak) else "OK" for p in ids]
        sp, spec = stats.sens_ppv(y, yh, "FLAG"), stats.sens_ppv(y, yh, "OK")
        k_lo, k_hi = stats.bootstrap_ci(stats.cohen_kappa, y, yh, b=boot) if boot else (float("nan"),) * 2
        rows.append({"run": name, "policy": policy, "item": pname, "n": len(ids),
                     "accuracy": stats.accuracy(y, yh), "kappa": stats.cohen_kappa(y, yh), "kappa_lo": k_lo,
                     "kappa_hi": k_hi, "macro_f1": stats.macro_f1(y, yh), "macro_f1_lo": float("nan"),
                     "macro_f1_hi": float("nan"), "positive": "FLAG", "sensitivity": sp["sensitivity"], "ppv": sp["ppv"],
                     "support": sp["support"], "specificity": spec["sensitivity"]})
    return rows, correct, ids


def run_efficiency(name, preds, ids):
    act = {it.code for it in ACTIVE}
    quotes = [s for p in ids for r in preds[p].values() if r["item"] in act for s in r["evidence_status"]]
    per_paper = []
    for p in ids:
        r0 = next(iter(preds[p].values()))
        e = r0.get("paper_energy") or {}
        per_paper.append({"wall": r0.get("paper_wall_s") or 0, "energy": e.get("energy_j"), "vram": e.get("peak_vram_mib"),
                          "ptok": sum(r["prompt_tokens"] or 0 for r in preds[p].values() if r["item"] in act),
                          "ctok": sum(r["completion_tokens"] or 0 for r in preds[p].values() if r["item"] in act),
                          "fails": sum(r["parse_failures"] for r in preds[p].values() if r["item"] in act)})
    mean = lambda xs: sum(xs) / len(xs) if xs else float("nan")
    en = [x["energy"] for x in per_paper if x["energy"] is not None]
    vr = [x["vram"] for x in per_paper if x["vram"] is not None]
    return {"run": name, "papers": len(ids), "quotes": len(quotes),
            "quote_exact": quotes.count("exact") / len(quotes) if quotes else float("nan"),
            "quote_fuzzy": quotes.count("fuzzy") / len(quotes) if quotes else float("nan"),
            "quote_unverified": quotes.count("none") / len(quotes) if quotes else float("nan"),
            "sec_per_paper": mean([x["wall"] for x in per_paper]), "energy_j_per_paper": mean(en) if en else float("nan"),
            "peak_vram_mib": max(vr) if vr else float("nan"), "prompt_tokens_per_paper": mean([x["ptok"] for x in per_paper]),
            "completion_tokens_per_paper": mean([x["ctok"] for x in per_paper]),
            "parse_failures_total": sum(x["fails"] for x in per_paper)}


def prevalence(gold_sub):
    rows = []
    n = len(gold_sub)
    leak = [c for c in LEAKAGE_ITEMS if c in {it.code for it in ACTIVE}]
    for it in ACTIVE:
        for lab in it.labels:
            k = sum(1 for g in gold_sub.values() if g[it.code] == lab)
            lo, hi = stats.wilson(k, n)
            rows.append({"item": it.code, "label": lab, "k": k, "n": n, "prop": k / n if n else float("nan"), "lo": lo, "hi": hi})
    for pname, bad in (("PAPER_any_leakage_risk", {"RISK"}), ("PAPER_not_verifiably_safe", {"RISK", "UNCLEAR"})):
        k = sum(1 for g in gold_sub.values() if any(g[c] in bad for c in leak))
        lo, hi = stats.wilson(k, n)
        rows.append({"item": pname, "label": "FLAG", "k": k, "n": n, "prop": k / n if n else float("nan"), "lo": lo, "hi": hi})
    return rows


def write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows([{k: (fmt(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in rows])


def intra_rater(path_a, path_b):
    a, b = corpus.read_gold(path_a), corpus.read_gold(path_b)
    common = [p for p in b if p in a and b[p]["eligible"] == "Y" and a[p]["eligible"] == "Y"]
    out = []
    for it in ACTIVE:
        pairs = [(a[p].get(it.code), b[p].get(it.code)) for p in common if a[p].get(it.code) and b[p].get(it.code)]
        y, yh = [x for x, _ in pairs], [x for _, x in pairs]
        lo, hi = stats.bootstrap_ci(stats.cohen_kappa, y, yh)
        out.append({"item": it.code, "n": len(pairs), "agreement": stats.accuracy(y, yh), "kappa": stats.cohen_kappa(y, yh),
                    "kappa_lo": lo, "kappa_hi": hi})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="dev", choices=["pilot", "dev", "test"])
    ap.add_argument("--runs", nargs="*", default=[])
    ap.add_argument("--workbook", default=corpus.WORKBOOK)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--out", default=None)
    ap.add_argument("--intra-rater", nargs=2, metavar=("FIRST", "SECOND"))
    ap.add_argument("--items", default=None, choices=["all", "test5"],
                    help="items to score (default: test5 for --set test, all otherwise)")
    args = ap.parse_args(argv)
    global ACTIVE
    ACTIVE = [ITEM_BY_CODE[c] for c in ITEM_SETS[args.items or ("test5" if args.set == "test" else "all")]]
    out = args.out or os.path.join(corpus.ROOT, "results", args.set)
    os.makedirs(out, exist_ok=True)

    if args.intra_rater:
        rows = intra_rater(*args.intra_rater)
        write_csv(os.path.join(out, "intra_rater.csv"), rows)
        for r in rows:
            print(f"{r['item']:26s} n={r['n']:3d} agreement={fmt(r['agreement'])} kappa={fmt(r['kappa'])} [{fmt(r['kappa_lo'])}, {fmt(r['kappa_hi'])}]")
        return

    gold_all = corpus.read_gold(args.workbook)
    gold = gold_labels(gold_all, corpus.select(args.set, gold_all))
    print(f"gold papers with complete labels in '{args.set}': {len(gold)}")
    write_csv(os.path.join(out, "prevalence.csv"), prevalence(gold))

    metric_rows, eff_rows, correctness, common, labels_by = [], [], {}, None, {}
    for rd in args.runs:
        meta, preds = load_run(rd)
        name = meta["run_name"]
        policies = ["raw"] if meta["args"]["backend"] == "rules" else ["raw", "verified", "gated"]
        for pol in policies:
            rows, corr, ids = evaluate_run(name, preds, gold, pol, args.boot)
            metric_rows += rows
            correctness[(name, pol)] = dict(zip(ids, zip(*[corr[it.code] for it in ACTIVE]))) if ids else {}
            labels_by[(name, pol)] = {p: tuple(final_label(preds[p][it.code], pol) for it in ACTIVE) for p in ids}
            common = set(ids) if common is None else common & set(ids)
        eff_rows.append(run_efficiency(name, preds, [p for p in gold if p in preds]))
    write_csv(os.path.join(out, "metrics.csv"), metric_rows)
    write_csv(os.path.join(out, "efficiency.csv"), eff_rows)

    # pairwise exact McNemar per item on papers scored by every run; Holm within each pair
    cmp_rows, keys = [], list(correctness)
    common = sorted(common or [])
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            pv = {}
            for k, it in enumerate(ACTIVE):
                ca = [correctness[a][p][k] for p in common]
                cb = [correctness[b][p][k] for p in common]
                res = stats.mcnemar_exact(ca, cb)
                pv[it.code] = res["p"]
                cmp_rows.append({"run_a": f"{a[0]}[{a[1]}]", "run_b": f"{b[0]}[{b[1]}]", "item": it.code, "n": len(common),
                                 "a_only_correct": res["b"], "b_only_correct": res["c"], "p": res["p"]})
            adj = stats.holm(pv)
            for r in cmp_rows[-len(ACTIVE):]:
                r["p_holm"] = adj[r["item"]]
    write_csv(os.path.join(out, "comparisons.csv"), cmp_rows)

    # primary endpoint: mean kappa of every configuration minus the FIRST run given (the baseline),
    # paired bootstrap over papers (pre-registered; see docs/analysis_plan.md)
    diff_rows = []
    if keys and common:
        # baseline = first run under its pre-registered policy (raw for rules, gated for LLM systems)
        base = (keys[0][0], "gated") if (keys[0][0], "gated") in labels_by else keys[0]
        g_rows = [tuple(gold[p][it.code] for it in ACTIVE) for p in common]
        for key in keys:
            if key[0] == base[0]:
                continue
            r = stats.paired_mean_kappa_diff(g_rows, [labels_by[base][p] for p in common],
                                             [labels_by[key][p] for p in common], b=args.boot)
            diff_rows.append({"baseline": f"{base[0]}[{base[1]}]", "run": f"{key[0]}[{key[1]}]", **r})
    write_csv(os.path.join(out, "mean_kappa_diff.csv"), diff_rows)

    single_class = {it.code for it in ACTIVE if len({g[it.code] for g in gold.values()}) < 2}
    lines = [f"# Results on '{args.set}' ({len(gold)} gold papers)\n",
             f"Mean kappa excludes items whose gold labels have a single class (kappa undefined): {sorted(single_class) or 'none'}\n", "| run | policy | mean kappa | mean macro-F1 | any-RISK sens | any-RISK PPV | not-verifiable sens | not-verifiable spec |", "|---|---|---|---|---|---|---|---|"]
    by = defaultdict(list)
    for r in metric_rows:
        by[(r["run"], r["policy"])].append(r)
    for (run, pol), rs in by.items():
        items = [r for r in rs if not r["item"].startswith("PAPER")]
        paper = next(r for r in rs if r["item"] == "PAPER_any_leakage_risk")
        nvs = next(r for r in rs if r["item"] == "PAPER_not_verifiably_safe")
        mk = [r["kappa"] for r in items if not math.isnan(r["kappa"]) and r["item"] not in single_class]
        mf = [r["macro_f1"] for r in items if not math.isnan(r["macro_f1"])]
        lines.append(f"| {run} | {pol} | {fmt(sum(mk) / len(mk) if mk else float('nan'))} | {fmt(sum(mf) / len(mf) if mf else float('nan'))} | "
                     f"{fmt(paper['sensitivity'])} | {fmt(paper['ppv'])} | {fmt(nvs['sensitivity'])} | {fmt(nvs['specificity'])} |")
    with open(os.path.join(out, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"tables written to {out}")


if __name__ == "__main__":
    main()
