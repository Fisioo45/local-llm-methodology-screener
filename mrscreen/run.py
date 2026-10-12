"""Run the screener (an LLM backend or the rule baseline) on a set of papers.

Examples
  python -m mrscreen.run --backend ollama --model qwen3:8b --set dev --energy
  python -m mrscreen.run --backend rules --set dev
  python -m mrscreen.run --backend llamacpp --model models/x.gguf --set sandbox:2 --num-ctx 4096

Writes runs/<run_name>/predictions.jsonl (one line per paper x item) and run_meta.json.
Re-running the same command resumes: finished papers are skipped.
The TEST set needs --frozen: prompts, models and settings must be final first.
"""
import argparse
import datetime
import hashlib
import json
import os
import platform
import sys
import time
from collections import Counter

from . import corpus, decomposed, prompts, retrieval
from .backends import make_backend, parse_json
from .energy import GpuMeter
from .items import ITEMS, ITEM_BY_CODE, ITEM_SETS
from .rules import predict_paper
from .verify import Verifier


def vote(labels, item):
    """Majority vote; ties go to the first (greedy) sample's label."""
    valid = [l for l in labels if l in item.labels]
    if not valid:
        return None, 0.0
    counts = Counter(valid)
    top = max(counts.values())
    winner = next(l for l in valid if counts[l] == top)
    return winner, top / len(labels)


def sample_plan(k, temp):
    return [(0.0, 0)] + [(temp, s) for s in range(1, k)]


def run_item(backend, item, messages, schema, plan, prompt="direct", max_new=1024):
    samples = []
    for temperature, seed in plan:
        r = backend.chat(messages, schema=schema, temperature=temperature, seed=seed)
        obj = parse_json(r.text) or {}
        retried = False
        if not obj and r.error is None and (r.completion_tokens or 0) >= max_new - 5:
            # output hit the length limit mid-JSON: retry once with double the budget
            r2 = backend.chat(messages, schema=schema, temperature=temperature, seed=seed, max_new=2 * max_new)
            obj, retried = parse_json(r2.text) or {}, True
            r.latency_s = (r.latency_s or 0) + (r2.latency_s or 0)
            r.prompt_tokens = (r.prompt_tokens or 0) + (r2.prompt_tokens or 0)
            r.completion_tokens = (r.completion_tokens or 0) + (r2.completion_tokens or 0)
        if prompt == "decomposed":
            facts = {k: v for k, v in obj.items() if k != "evidence"}
            label, reasoning = decomposed.map_label(item.code, facts), json.dumps(facts, ensure_ascii=False)
        else:
            label, reasoning = obj.get("label"), obj.get("reasoning")
        samples.append({"label": label, "evidence": obj.get("evidence") or [],
                        "reasoning": reasoning, "ok": bool(obj), "error": r.error, "retried": retried,
                        "prompt_tokens": r.prompt_tokens, "completion_tokens": r.completion_tokens,
                        "latency_s": r.latency_s})
    return samples


def summarise(item, samples, verifier, context_tokens):
    label, agree = vote([s["label"] for s in samples], item)
    chosen = [s for s in samples if s["label"] == label] or samples
    evidence = []
    for s in chosen:
        for q in s["evidence"]:
            if isinstance(q, str) and q.strip() and q not in evidence:
                evidence.append(q.strip())
    evidence = evidence[:3]
    return {"label_raw": label, "votes": [s["label"] for s in samples], "agreement": agree,
            "evidence": evidence, "evidence_status": [verifier.check(q) for q in evidence],
            "reasoning": chosen[0]["reasoning"], "parse_failures": sum(not s["ok"] for s in samples),
            "errors": [s["error"] for s in samples if s["error"]],
            "prompt_tokens": sum(s["prompt_tokens"] or 0 for s in samples),
            "completion_tokens": sum(s["completion_tokens"] or 0 for s in samples),
            "latency_s": sum(s["latency_s"] or 0 for s in samples), "context_tokens_est": context_tokens}


def screen_paper(pmcid, args, backend):
    paper = corpus.load_paper(pmcid)
    text = corpus.full_text(paper)
    verifier = Verifier(text)
    rows = []
    active = [ITEM_BY_CODE[c] for c in ITEM_SETS[getattr(args, "items", "all")]]
    if args.backend == "rules":
        t0 = time.perf_counter()
        pred = predict_paper(paper)
        for it in active:
            ev = pred[it.code]["evidence"]
            rows.append({"item": it.code, "label_raw": pred[it.code]["label"], "votes": [pred[it.code]["label"]],
                         "agreement": 1.0, "evidence": ev, "evidence_status": [verifier.check(q) for q in ev],
                         "reasoning": "rule", "parse_failures": 0, "errors": [], "prompt_tokens": 0,
                         "completion_tokens": 0, "latency_s": (time.perf_counter() - t0) / len(active),
                         "context_tokens_est": 0})
        return rows
    plan = sample_plan(args.k, args.sc_temperature)
    if args.mode == "per_item":
        psgs = corpus.passages(paper)
        for it in active:
            sel = retrieval.retrieve(it, psgs, args.budget)
            ctx = retrieval.render(sel) or "(no relevant passage found)"
            if args.prompt == "decomposed":
                msgs = decomposed.messages(it.code, ctx, paper["title"], prompts.SYSTEM_FACTS)
                schema = decomposed.schema(it.code)
            else:
                msgs, schema = prompts.per_item_messages(it, ctx, paper["title"]), prompts.item_schema(it)
            samples = run_item(backend, it, msgs, schema, plan, args.prompt, args.max_new)
            rows.append({"item": it.code, **summarise(it, samples, verifier, corpus.approx_tokens(ctx))})
    else:  # all_items: one call per sample covering every item
        body = retrieval.truncate_to_budget(text, args.budget)
        msgs = prompts.all_items_messages(body, paper["title"])
        raw = []
        for temperature, seed in plan:
            r = backend.chat(msgs, schema=prompts.all_items_schema(), temperature=temperature, seed=seed)
            raw.append((r, parse_json(r.text) or {}))
        for it in active:
            samples = []
            for r, obj in raw:
                o = obj.get(it.code) or {}
                samples.append({"label": o.get("label"), "evidence": o.get("evidence") or [], "reasoning": o.get("reasoning"),
                                "ok": bool(o), "error": r.error, "prompt_tokens": (r.prompt_tokens or 0) / len(ITEMS),
                                "completion_tokens": (r.completion_tokens or 0) / len(ITEMS),
                                "latency_s": (r.latency_s or 0) / len(ITEMS)})
            rows.append({"item": it.code, **summarise(it, samples, verifier, corpus.approx_tokens(body))})
    return rows


def preflight_ollama(host, model):
    import urllib.request
    try:
        with urllib.request.urlopen(f"{host}/api/tags", timeout=10) as resp:
            names = {m.get("name") for m in json.loads(resp.read().decode()).get("models", [])}
    except Exception as e:
        sys.exit(f"Cannot reach Ollama at {host} ({e}).\nStart the Ollama app (llama icon near the clock) and run the command again.")
    if model not in names and f"{model}:latest" not in names:
        sys.exit(f"Model '{model}' is not downloaded. Run:  ollama pull {model}\nInstalled: {', '.join(sorted(n for n in names if n))}")
    print(f"  Ollama OK, model {model} found")


def preflight_energy():
    import shutil
    import subprocess
    from .energy import probe_power_field
    if not shutil.which("nvidia-smi"):
        print("  WARNING: nvidia-smi not found on PATH - energy and VRAM will not be recorded")
        return
    field = probe_power_field()
    try:
        mem = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=15).stdout.strip()
    except Exception:
        mem = "?"
    if field:
        print(f"  nvidia-smi OK: power from '{field}', VRAM now {mem} MiB")
    else:
        print(f"  NOTE: this GPU does not report power (common on laptop GPUs) - energy will be missing; "
              f"VRAM is recorded (now {mem} MiB)")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", required=True, choices=["ollama", "openai", "llamacpp", "mock", "rules"])
    ap.add_argument("--model", default=None, help="Ollama tag, server model name, or GGUF path")
    ap.add_argument("--set", default="dev", help="pilot | dev | test | sandbox[:N] | PMC1,PMC2")
    ap.add_argument("--mode", default="per_item", choices=["per_item", "all_items"])
    ap.add_argument("--budget", type=int, default=None, help="context tokens (per item, or whole paper in all_items)")
    ap.add_argument("--num-ctx", type=int, default=8192)
    ap.add_argument("--max-new", type=int, default=1024)
    ap.add_argument("--items", default="all", choices=["all", "test5"], help="test5 = the five v1.3 test items only")
    ap.add_argument("--prompt", default="direct", choices=["direct", "decomposed"],
                    help="direct = model picks the label (p1); decomposed = model answers factual sub-questions, codebook logic picks the label (p2)")
    ap.add_argument("--k", type=int, default=1, help="self-consistency samples (1 = greedy only)")
    ap.add_argument("--sc-temperature", type=float, default=0.7)
    ap.add_argument("--think", choices=["default", "on", "off"], default="default",
                    help="only for thinking-capable models (e.g. qwen3); 'default' sends nothing")
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--base-url", default="http://localhost:8080/v1")
    ap.add_argument("--energy", action="store_true", help="sample GPU power with nvidia-smi")
    ap.add_argument("--run-name", default=None)
    ap.add_argument("--out", default=os.path.join(corpus.ROOT, "runs"))
    ap.add_argument("--frozen", action="store_true", help="required for --set test")
    ap.add_argument("--workbook", default=corpus.WORKBOOK, help="gold workbook that defines pilot/dev/test")
    args = ap.parse_args(argv)

    if args.mode == "all_items" and args.prompt == "decomposed":
        sys.exit("--prompt decomposed is implemented for --mode per_item only.")
    if args.set == "test" and not args.frozen:
        sys.exit("Refusing to run on the TEST set without --frozen (freeze prompts, models and settings first).")
    if args.set == "test":
        from . import lock
        probs = lock.check(args.workbook)
        if probs:
            sys.exit("Refusing to run on the TEST set: " + "; ".join(probs))
    if args.budget is None:
        args.budget = 1800 if args.mode == "per_item" else min(12000, args.num_ctx - 2500)
    if args.mode == "all_items" and args.budget + 2500 > args.num_ctx:
        sys.exit(f"--budget {args.budget} does not fit in --num-ctx {args.num_ctx} (prompt + {args.max_new} output tokens).")

    backend = None
    if args.backend == "ollama":
        think = None if args.think == "default" else args.think == "on"
        backend = make_backend("ollama", args.model, host=args.host, num_ctx=args.num_ctx, num_predict=args.max_new, think=think)
    elif args.backend == "openai":
        backend = make_backend("openai", args.model, base_url=args.base_url, max_tokens=args.max_new)
    elif args.backend == "llamacpp":
        backend = make_backend("llamacpp", args.model, n_ctx=args.num_ctx, max_tokens=args.max_new)
    elif args.backend == "mock":
        backend = make_backend("mock")

    if args.backend == "ollama":
        preflight_ollama(args.host, args.model)
    if args.energy:
        preflight_energy()

    ids = corpus.select(args.set, None if args.set.startswith(("sandbox", "PMC")) else corpus.read_gold(args.workbook))
    name = args.run_name or "_".join(x for x in [
        args.backend, os.path.basename(args.model or "").replace(":", "-").replace(".gguf", ""), args.mode,
        "" if args.backend == "rules" else ("p" + (decomposed.PROMPT_VERSION if args.prompt == "decomposed" else prompts.PROMPT_VERSION)[1:].replace(".", "")),
        "i5" if args.items == "test5" else "",
        f"b{args.budget}", f"k{args.k}", f"think-{args.think}" if args.backend == "ollama" else "", args.set.replace(":", "")] if x)
    run_dir = os.path.join(args.out, name)
    os.makedirs(run_dir, exist_ok=True)
    pred_path = os.path.join(run_dir, "predictions.jsonl")
    done = set()
    if os.path.exists(pred_path):
        with open(pred_path, encoding="utf-8") as f:
            old = [json.loads(l) for l in f if l.strip()]
        failed = {r["pmcid"] for r in old if r.get("errors")}
        keep = [r for r in old if r["pmcid"] not in failed]
        if failed:   # rewrite the file without papers that hit backend errors; they are re-run below
            with open(pred_path, "w", encoding="utf-8") as f:
                for r in keep:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(f"  {len(failed)} paper(s) had backend errors in an earlier attempt and will be re-run")
        done = {r["pmcid"] for r in keep}

    meta = {"run_name": name, "args": vars(args),
            "prompt_version": prompts.VERSION_TAG if args.prompt == "direct" else prompts.VERSION_TAG.replace(prompts.PROMPT_VERSION, decomposed.PROMPT_VERSION),
            "prompt_sha256": hashlib.sha256((prompts.SYSTEM + prompts.item_block(ITEMS[0])).encode()).hexdigest()[:16],
            "backend": backend.describe() if backend else {"backend": "rules"},
            "python": sys.version.split()[0], "platform": platform.platform(),
            "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "n_papers": len(ids), "already_done": len(done)}
    from . import lock as _lock
    meta["code_sha256"] = _lock.code_fingerprint()
    if args.set == "test" and backend is not None:
        probs = _lock.check(args.workbook, args.model, meta["backend"].get("digest"))
        if probs:
            sys.exit("Refusing to run on the TEST set: " + "; ".join(probs))
        meta["test_lock"] = "OK"
    with open(os.path.join(run_dir, "run_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)

    todo = [p for p in ids if p not in done]
    print(f"[{name}] {len(ids)} papers, {len(done)} done, {len(todo)} to go")
    with open(pred_path, "a", encoding="utf-8") as out:
        for n, pmcid in enumerate(todo, 1):
            meter = GpuMeter() if args.energy else None
            if meter:
                meter.__enter__()
            t0 = time.perf_counter()
            rows = screen_paper(pmcid, args, backend)
            wall = time.perf_counter() - t0
            if args.backend != "rules" and all(r["errors"] for r in rows):
                if meter:
                    meter.__exit__(None, None, None)
                sys.exit(f"\nSTOPPED at {pmcid}: every call failed ({rows[0]['errors'][0][:120]}).\n"
                         "Is Ollama running (llama icon near the clock)? Start it and run the same command again; "
                         "finished papers are kept.")
            energy = None
            if meter:
                meter.__exit__(None, None, None)
                energy = meter.summary()
            for r in rows:
                out.write(json.dumps({"pmcid": pmcid, **r, "paper_wall_s": wall, "paper_energy": energy},
                                     ensure_ascii=False) + "\n")
            out.flush()
            fails = sum(r["parse_failures"] for r in rows)
            print(f"  {n}/{len(todo)} {pmcid}  {wall:.1f}s  parse_failures={fails}")
    meta["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    with open(os.path.join(run_dir, "run_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    return run_dir


if __name__ == "__main__":
    main()
