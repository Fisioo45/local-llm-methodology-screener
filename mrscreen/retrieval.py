"""Item-targeted retrieval: pick the passages most relevant to one codebook item.

BM25 over paragraph-sized passages using the item's query terms, a small prior
for methods-like sections (or back matter for availability items), then the
selected passages are returned in DOCUMENT ORDER - sequencing cues such as
"after augmentation, the data were split" only survive if order is preserved.
"""
import math
import re
from collections import Counter

from .corpus import Passage, approx_tokens

_TOK = re.compile(r"[a-z0-9±%]+(?:-[a-z0-9]+)*")
METHODS_PATH = re.compile(r"method|material|dataset|data set|data collection|experiment|implementation|"
                          r"training|evaluation|preprocess|pre-process|study design|split|validation", re.I)


def tokenize(text: str) -> list:
    return _TOK.findall(text.lower())


class BM25:
    def __init__(self, docs: list, k1: float = 1.5, b: float = 0.75):
        self.docs = [tokenize(d) for d in docs]
        self.k1, self.b = k1, b
        self.avgdl = sum(len(d) for d in self.docs) / max(1, len(self.docs))
        df = Counter(t for d in self.docs for t in set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.tf = [Counter(d) for d in self.docs]

    def score(self, query_terms: list, i: int) -> float:
        tf, dl, s = self.tf[i], len(self.docs[i]), 0.0
        for q in query_terms:
            # prefix match lets stems like "normaliz" hit "normalized"/"normalization"
            f = tf.get(q, 0)
            if not f and len(q) >= 5:
                f = sum(c for t, c in tf.items() if t.startswith(q))
            if f:
                idf = self.idf.get(q, max((self.idf[t] for t in tf if t.startswith(q)), default=1.0))
                s += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return s


def phrase_bonus(text: str, phrases: list) -> float:
    low = text.lower()
    return sum(1.0 for p in phrases if " " in p and p in low)


def retrieve(item, psgs: list, budget_tokens: int = 1800) -> list:
    """Return selected passages (document order) whose total size fits the budget."""
    if not psgs:
        return []
    query = [t for term in item.query for t in tokenize(term)]
    bm = BM25([p.text for p in psgs])
    scored = []
    for i, p in enumerate(psgs):
        s = bm.score(query, i) + 0.5 * phrase_bonus(p.text, list(item.query))
        if item.prefer_back and (p.in_back or re.search(r"availab", p.path, re.I)):
            s = s * 1.5 + 2.0
        elif not item.prefer_back and METHODS_PATH.search(p.path):
            s *= 1.25
        scored.append((s, i))
    scored.sort(reverse=True)
    chosen, used = [], 0
    for s, i in scored:
        if s <= 0:
            break
        cost = approx_tokens(psgs[i].text) + 8
        if used + cost > budget_tokens:
            continue
        chosen.append(i); used += cost
    return [psgs[i] for i in sorted(chosen)]


def render(selected: list) -> str:
    return "\n\n".join(f"[P{p.pid}] ({p.path})\n{p.text}" for p in selected)


def truncate_to_budget(text: str, budget_tokens: int) -> str:
    """Whole-paper mode: keep the beginning of the paper up to the budget."""
    return text[: budget_tokens * 4]
