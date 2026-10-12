"""Evidence verification.

A quote is checked against the article's full text after light normalisation
(whitespace, typographic quotes/dashes, numeric citation markers). Levels:
  exact - normalised quote is a substring of the normalised article
  fuzzy - >= 90 % of the quote's characters align with one article window
  none  - not found (likely paraphrased or invented)
Policy "verified": a substantive label (e.g. SAFE/RISK/YES) with no exact or fuzzy
quote is downgraded to the item's silence label (see Item.downgrade).
"""
import re
import unicodedata
from difflib import SequenceMatcher

_CIT = re.compile(r"\s*\[(?:\d+(?:[,\u2013\-–]\s*\d+)*)\]")
_TRANS = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-",
                        "\u2212": "-", "\u00a0": " ", "\u2009": " ", "\u00d7": "x"})


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").translate(_TRANS)
    s = _CIT.sub("", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s.strip(" .;:,\"'")


class Verifier:
    def __init__(self, article_text: str):
        self.text = normalize(article_text)

    def check(self, quote: str) -> str:
        q = normalize(quote)
        if len(q) < 12:
            return "none"          # too short to count as evidence
        if q in self.text:
            return "exact"
        words = sorted(set(re.findall(r"[a-z0-9]{5,}", q)), key=len, reverse=True)[:3]
        best = 0.0
        for w in words:
            for m in re.finditer(re.escape(w), self.text):
                lo = max(0, m.start() - len(q)); hi = min(len(self.text), m.end() + len(q))
                window = self.text[lo:hi]
                sm = SequenceMatcher(None, q, window, autojunk=False)
                matched = sum(b.size for b in sm.get_matching_blocks())
                best = max(best, matched / len(q))
                if best >= 0.9:
                    return "fuzzy"
        return "none"


def apply_policy(item, label: str, statuses: list, policy: str, quotes: list = None) -> str:
    """raw: label as given. verified: substantive labels need a quote found in the paper.
    gated: verified + for some labels the verified quote must contain the key signal
    (e.g. B2=YES needs a quote with ±/SD/CI; C1=YES needs a link) - Item.gate."""
    if policy == "raw" or label is None:
        return label
    if label in item.no_evidence_ok or label == item.absent_label:
        return label
    ok = [q for q, s in zip(quotes or [None] * len(statuses), statuses) if s in ("exact", "fuzzy")]
    if not ok:
        return item.downgrade.get(label, label)
    if policy == "gated" and label in item.gate:
        if not any(q and re.search(item.gate[label], q, re.I) for q in ok):
            return item.downgrade.get(label, label)
    return label
