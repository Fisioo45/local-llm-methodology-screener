"""Test-set lock: the test set may only be run with the frozen gold, the frozen code and the frozen models.

  python -m mrscreen.lock --write      # (done once, when the analysis plan is frozen)
  python -m mrscreen.lock              # show whether this installation matches the lock

run.py refuses `--set test` unless gold hash, code fingerprint and model digest all match configs/test_lock.json.
"""
import argparse
import hashlib
import json
import os
import sys

from . import corpus

LOCK = os.path.join(corpus.ROOT, "configs", "test_lock.json")
# everything that decides what the model sees and how its answer becomes a label
CODE_FILES = ["backends.py", "decomposed.py", "items.py", "prompts.py", "retrieval.py", "rules.py", "verify.py", "hybrid.py"]


def code_fingerprint():
    h = hashlib.sha256()
    here = os.path.dirname(os.path.abspath(__file__))
    for name in CODE_FILES:
        with open(os.path.join(here, name), "rb") as f:
            h.update(name.encode() + b"\0" + f.read().replace(b"\r\n", b"\n") + b"\0")
    return h.hexdigest()


def gold_sha(workbook):
    from .freeze import canonical
    return canonical(workbook)[1]


def check(workbook, model=None, digest=None):
    """Return a list of problems (empty = OK)."""
    if not os.path.exists(LOCK):
        return ["configs/test_lock.json is missing (the analysis plan is not frozen yet)"]
    with open(LOCK, encoding="utf-8") as f:
        lock = json.load(f)
    problems = []
    if gold_sha(workbook) != lock["gold_sha256"]:
        problems.append("gold workbook differs from the frozen gold")
    if code_fingerprint() != lock["code_sha256"]:
        problems.append("prompt/label code differs from the frozen code (re-extract the frozen package)")
    if model is not None:
        want = lock["models"].get(model)
        if want is None:
            problems.append(f"model {model} is not in the frozen plan")
        elif digest and digest != want:
            problems.append(f"model {model} digest {digest[:12]} differs from the frozen digest {want[:12]} (do not 'ollama pull' again)")
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--workbook", default=corpus.WORKBOOK)
    ap.add_argument("--models-from", nargs="*", default=[], help="run folders whose run_meta.json give the model digests")
    a = ap.parse_args(argv)
    if a.write:
        models = {}
        for d in a.models_from:
            with open(os.path.join(d, "run_meta.json"), encoding="utf-8") as f:
                b = json.load(f)["backend"]
            models[b["model"]] = b["digest"]
        lock = {"gold_sha256": gold_sha(a.workbook), "code_sha256": code_fingerprint(), "models": models,
                "plan": "docs/analysis_plan.md v1.0"}
        with open(LOCK, "w", encoding="utf-8") as f:
            json.dump(lock, f, indent=2)
        print(json.dumps(lock, indent=2))
        return 0
    probs = check(a.workbook)
    print("test lock: " + ("OK" if not probs else "; ".join(probs)))
    return 0 if not probs else 1


if __name__ == "__main__":
    sys.exit(main())
