"""Prompt templates and JSON schemas.

Output order inside the JSON is deliberate: evidence quotes first, a short
justification second, the label last ("quote, then decide").
"""
from .items import ITEMS, CODEBOOK_VERSION

PROMPT_VERSION = "p1.1"

SYSTEM = (
    "You are a meticulous methods reviewer auditing published deep-learning studies on medical image classification. "
    "Judge ONLY from the article text you are given; do not use outside knowledge about datasets or authors. "
    "Copy evidence quotes VERBATIM from the text (no paraphrasing, no ellipses inside a quote, at most 40 words each). "
    "If the text does not settle the question, choose the label the rules reserve for silence. "
    "Answer with a single JSON object and nothing else."
)


SYSTEM_FACTS = (
    "You are a meticulous methods reviewer auditing published deep-learning studies on medical image classification. "
    "You answer short factual questions about the article text you are given. Judge ONLY from that text; do not use outside knowledge. "
    "Copy evidence quotes VERBATIM (no paraphrasing, no ellipses inside a quote, at most 40 words each). "
    "When the text does not say something, answer not_stated / no / empty rather than guessing. "
    "Answer with a single JSON object and nothing else."
)


def item_block(item) -> str:
    return (f"ITEM {item.code}\nQuestion: {item.question}\n"
            f"Allowed labels: {', '.join(item.labels)}\nRules:\n{item.rules}\n"
            f"If the text is silent on this question, the label is {item.absent_label}.")


def item_schema(item) -> dict:
    return {
        "type": "object",
        "properties": {
            "evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
            "reasoning": {"type": "string"},
            "label": {"type": "string", "enum": list(item.labels)},
        },
        "required": ["evidence", "reasoning", "label"],
    }


def per_item_messages(item, context: str, title: str) -> list:
    user = (
        f"{item_block(item)}\n\n"
        f"ARTICLE: {title}\nEXCERPTS (selected passages, in document order; [P#] are passage ids):\n"
        f"<<<\n{context}\n>>>\n\n"
        "Return JSON with keys in this order: "
        '"evidence" (list of 0-3 verbatim quotes that justify the label; empty list if the text is silent), '
        '"reasoning" (at most two sentences), "label" (one allowed label).'
    )
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


def all_items_schema() -> dict:
    props = {it.code: item_schema(it) for it in ITEMS}
    return {"type": "object", "properties": props, "required": [it.code for it in ITEMS]}


def all_items_messages(text: str, title: str) -> list:
    blocks = "\n\n".join(item_block(it) for it in ITEMS)
    user = (
        f"Assess the article below on all {len(ITEMS)} items.\n\n{blocks}\n\n"
        f"ARTICLE: {title}\n<<<\n{text}\n>>>\n\n"
        "Return one JSON object with one key per item code; each value is an object with keys "
        '"evidence" (0-3 verbatim quotes), "reasoning" (at most two sentences), "label".'
    )
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


VERSION_TAG = f"codebook{CODEBOOK_VERSION}-{PROMPT_VERSION}"
