"""Pre-specified hybrid screener: the keyword rules answer the LEXICAL items, the LLM answers the
JUDGEMENT items. Built from two finished runs on the same papers (no new model calls).

  python -m mrscreen.hybrid --llm runs/<llm_run> --rules runs/<rules_run>

Default split (fixed in docs/analysis_plan.md before any test run, by item type, not by test results):
  rules  -> B2_variability_reported, C1_code_available   (decided by surface signals: ±/CI, a repository link)
  LLM    -> A1_split_unit, A4_test_for_selection, C2_data_available   (need reading and judgement)
Writes runs/hybrid__<llm_run>/predictions.jsonl + run_meta.json, scored like any other run.
"""
import argparse
import json
import os
import sys

RULE_ITEMS_DEFAULT = ("B2_variability_reported", "C1_code_available")


def load(run_dir):
    with open(os.path.join(run_dir, "predictions.jsonl"), encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    with open(os.path.join(run_dir, "run_meta.json"), encoding="utf-8") as f:
        meta = json.load(f)
    return rows, meta


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", required=True)
    ap.add_argument("--rules", required=True)
    ap.add_argument("--rule-items", nargs="*", default=list(RULE_ITEMS_DEFAULT))
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    llm, mllm = load(a.llm)
    rules, mrules = load(a.rules)
    if mrules["args"]["backend"] != "rules":
        sys.exit("--rules must be a rules-baseline run")
    rule_rows = {(r["pmcid"], r["item"]): r for r in rules}
    out_rows, missing = [], 0
    for r in llm:
        if r["item"] in a.rule_items:
            rr = rule_rows.get((r["pmcid"], r["item"]))
            if rr is None:
                missing += 1
                continue
            rr = dict(rr)
            rr["paper_energy"] = None
            out_rows.append(rr)
        else:
            out_rows.append(r)
    # honest cost: a real hybrid only calls the LLM for its own items
    llm_time = {}
    for r in llm:
        if r["item"] not in a.rule_items:
            llm_time[r["pmcid"]] = llm_time.get(r["pmcid"], 0.0) + float(r.get("latency_s") or 0.0)
    for r in out_rows:
        r["paper_wall_s"] = round(llm_time.get(r["pmcid"], 0.0) + 0.1, 2)
        if r["item"] in a.rule_items:
            r["prompt_tokens"], r["completion_tokens"] = 0, 0
    if missing:
        sys.exit(f"{missing} paper/item pairs missing in the rules run: run the rules baseline on the same set first")
    name = "hybrid__" + mllm["run_name"]
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.llm)), name)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "predictions.jsonl"), "w", encoding="utf-8") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    meta = dict(mllm)
    meta.update({"run_name": name, "hybrid": {"llm_run": mllm["run_name"], "rules_run": mrules["run_name"],
                                               "rule_items": a.rule_items}})
    meta["args"] = dict(mllm["args"], backend="hybrid")
    with open(os.path.join(out, "run_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(f"hybrid run written: {out}  (rules on {', '.join(a.rule_items)})")
    return out


if __name__ == "__main__":
    main()
