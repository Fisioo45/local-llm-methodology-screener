"""Dependency-light statistics (numpy only) so the evaluation runs anywhere."""
import math
import random
from collections import Counter


def accuracy(y, p):
    return sum(a == b for a, b in zip(y, p)) / len(y) if y else float("nan")


def cohen_kappa(y, p):
    n = len(y)
    if n == 0:
        return float("nan")
    po = accuracy(y, p)
    cy, cp = Counter(y), Counter(p)
    pe = sum(cy[k] * cp.get(k, 0) for k in cy) / (n * n)
    if pe == 1:
        return 1.0 if po == 1 else 0.0
    return (po - pe) / (1 - pe)


def f1_for(y, p, label):
    tp = sum(a == label and b == label for a, b in zip(y, p))
    fp = sum(a != label and b == label for a, b in zip(y, p))
    fn = sum(a == label and b != label for a, b in zip(y, p))
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    return (2 * prec * rec / (prec + rec) if prec + rec else 0.0), prec, rec, tp + fn


def macro_f1(y, p):
    labels = sorted(set(y))          # macro over labels present in the gold standard
    return sum(f1_for(y, p, l)[0] for l in labels) / len(labels) if labels else float("nan")


def sens_ppv(y, p, positive):
    _, prec, rec, support = f1_for(y, p, positive)
    return {"sensitivity": rec if support else float("nan"), "ppv": prec, "support": support}


def bootstrap_ci(fn, y, p, b=2000, seed=12345, alpha=0.05):
    """Percentile CI, resampling papers (paired: the same indices for y and p)."""
    n = len(y)
    if n < 2:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    vals = []
    for _ in range(b):
        idx = [rng.randrange(n) for _ in range(n)]
        v = fn([y[i] for i in idx], [p[i] for i in idx])
        if not math.isnan(v):
            vals.append(v)
    vals.sort()
    lo, hi = vals[int(alpha / 2 * len(vals))], vals[int((1 - alpha / 2) * len(vals)) - 1]
    return lo, hi


def mcnemar_exact(correct_a, correct_b):
    """Two-sided exact McNemar test on paired correctness vectors."""
    b = sum(a and not c for a, c in zip(correct_a, correct_b))
    c = sum(c and not a for a, c in zip(correct_a, correct_b))
    n = b + c
    if n == 0:
        return {"b": b, "c": c, "p": 1.0}
    k = min(b, c)
    p = 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return {"b": b, "c": c, "p": min(1.0, p)}


def holm(pvals: dict) -> dict:
    """Holm-Bonferroni adjusted p-values for a dict {name: p}."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, adj, running = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        adj[k] = running
    return adj


def wilson(k, n, z=1.959964):
    if n == 0:
        return (float("nan"), float("nan"))
    ph = k / n
    d = 1 + z * z / n
    c = ph + z * z / (2 * n)
    r = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))
    return ((c - r) / d, (c + r) / d)


def paired_mean_kappa_diff(gold, pred_a, pred_b, b=2000, seed=12345, alpha=0.05):
    """Primary endpoint: difference in mean Cohen's kappa across items (B - A), paired bootstrap over papers.
    gold, pred_a, pred_b: lists (one entry per paper) of equal-length label tuples (one label per item).
    Returns observed diff, percentile CI and a two-sided bootstrap p-value."""
    n = len(gold)
    k = len(gold[0]) if n else 0

    def mean_kappa(idx, pred):
        vals = []
        for j in range(k):
            y = [gold[i][j] for i in idx]
            if len(set(y)) < 2:
                continue                      # kappa undefined for a single-class resample of this item
            vals.append(cohen_kappa(y, [pred[i][j] for i in idx]))
        return sum(vals) / len(vals) if vals else float("nan")

    full = list(range(n))
    obs = mean_kappa(full, pred_b) - mean_kappa(full, pred_a)
    rng = random.Random(seed)
    diffs = []
    for _ in range(b):
        idx = [rng.randrange(n) for _ in range(n)]
        d = mean_kappa(idx, pred_b) - mean_kappa(idx, pred_a)
        if not math.isnan(d):
            diffs.append(d)
    diffs.sort()
    lo, hi = diffs[int(alpha / 2 * len(diffs))], diffs[int((1 - alpha / 2) * len(diffs)) - 1]
    p = min(1.0, 2 * min(sum(d <= 0 for d in diffs), sum(d >= 0 for d in diffs)) / len(diffs))
    return {"diff": obs, "lo": lo, "hi": hi, "p_boot": p, "n": n}
