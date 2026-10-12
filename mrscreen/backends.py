"""LLM backends. All return a Reply with the raw text and usage/latency data.

- ollama : native /api/chat. Preferred: it honours num_ctx (the OpenAI-compatible
           endpoint silently keeps Ollama's default context and truncates prompts).
- openai : any OpenAI-compatible server (llama.cpp llama-server, LM Studio, vLLM).
- llamacpp: in-process llama-cpp-python with a local GGUF file (used for CPU smoke tests).
- mock   : deterministic fake for tests; never used for results.
"""
import json
import re
import time
import urllib.request
from dataclasses import dataclass


@dataclass
class Reply:
    text: str
    prompt_tokens: int = None
    completion_tokens: int = None
    latency_s: float = None
    error: str = None


def parse_json(text: str):
    """Parse a JSON object from model text; tolerate code fences and stray prose."""
    if text is None:
        return None
    t = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t.strip())
    try:
        return json.loads(t)
    except Exception:
        pass
    start, depth = t.find("{"), 0
    if start < 0:
        return None
    for i in range(start, len(t)):
        depth += {"{": 1, "}": -1}.get(t[i], 0)
        if depth == 0:
            try:
                return json.loads(t[start:i + 1])
            except Exception:
                return None
    return None


def _post(url, payload, timeout):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


class OllamaBackend:
    def __init__(self, model, host="http://localhost:11434", num_ctx=8192, num_predict=512, think=None, timeout=600):
        self.model, self.host, self.num_ctx, self.num_predict, self.think, self.timeout = model, host, num_ctx, num_predict, think, timeout

    def chat(self, messages, schema=None, temperature=0.0, seed=0, max_new=None):
        payload = {"model": self.model, "messages": messages, "stream": False,
                   "options": {"temperature": temperature, "seed": seed, "num_ctx": self.num_ctx,
                               "num_predict": max_new or self.num_predict}}
        if schema is not None:
            payload["format"] = schema
        if self.think is not None:
            payload["think"] = self.think
        t0 = time.perf_counter()
        try:
            d = _post(f"{self.host}/api/chat", payload, self.timeout)
        except Exception as e:
            return Reply(None, latency_s=time.perf_counter() - t0, error=str(e))
        return Reply(d.get("message", {}).get("content"), d.get("prompt_eval_count"), d.get("eval_count"),
                     time.perf_counter() - t0)

    def describe(self):
        info = {"backend": "ollama", "model": self.model, "num_ctx": self.num_ctx, "think": self.think}
        try:
            with urllib.request.urlopen(f"{self.host}/api/tags", timeout=30) as r:
                for m in json.loads(r.read().decode()).get("models", []):
                    if m.get("name") == self.model or m.get("model") == self.model:
                        info.update(digest=m.get("digest"), size_bytes=m.get("size"), details=m.get("details"))
            with urllib.request.urlopen(f"{self.host}/api/version", timeout=30) as r:
                info["ollama_version"] = json.loads(r.read().decode()).get("version")
        except Exception as e:
            info["describe_error"] = str(e)
        return info


class OpenAICompatBackend:
    def __init__(self, model, base_url="http://localhost:8080/v1", max_tokens=512, timeout=600):
        self.model, self.base_url, self.max_tokens, self.timeout = model, base_url.rstrip("/"), max_tokens, timeout

    def chat(self, messages, schema=None, temperature=0.0, seed=0, max_new=None):
        payload = {"model": self.model, "messages": messages, "temperature": temperature, "seed": seed,
                   "max_tokens": max_new or self.max_tokens}
        if schema is not None:
            payload["response_format"] = {"type": "json_schema", "json_schema": {"name": "answer", "schema": schema}}
        t0 = time.perf_counter()
        try:
            d = _post(f"{self.base_url}/chat/completions", payload, self.timeout)
        except Exception as e:
            return Reply(None, latency_s=time.perf_counter() - t0, error=str(e))
        u = d.get("usage", {})
        return Reply(d["choices"][0]["message"]["content"], u.get("prompt_tokens"), u.get("completion_tokens"),
                     time.perf_counter() - t0)

    def describe(self):
        return {"backend": "openai-compatible", "model": self.model, "base_url": self.base_url}


class LlamaCppBackend:
    def __init__(self, model_path, n_ctx=4096, max_tokens=384, n_threads=None, n_gpu_layers=0):
        from llama_cpp import Llama
        self.model_path = model_path
        self.llm = Llama(model_path=model_path, n_ctx=n_ctx, n_threads=n_threads, n_gpu_layers=n_gpu_layers,
                         verbose=False, seed=0)
        self.n_ctx, self.max_tokens = n_ctx, max_tokens

    def chat(self, messages, schema=None, temperature=0.0, seed=0, max_new=None):
        kw = {"messages": messages, "temperature": temperature, "max_tokens": max_new or self.max_tokens, "seed": seed}
        if schema is not None:
            kw["response_format"] = {"type": "json_object", "schema": schema}
        t0 = time.perf_counter()
        try:
            d = self.llm.create_chat_completion(**kw)
        except Exception as e:
            return Reply(None, latency_s=time.perf_counter() - t0, error=str(e))
        u = d.get("usage", {})
        return Reply(d["choices"][0]["message"]["content"], u.get("prompt_tokens"), u.get("completion_tokens"),
                     time.perf_counter() - t0)

    def describe(self):
        import hashlib, os
        h = hashlib.sha256()
        with open(self.model_path, "rb") as f:
            h.update(f.read(1 << 24))  # first 16 MB is enough to identify the file
        return {"backend": "llama-cpp-python", "model": os.path.basename(self.model_path), "n_ctx": self.n_ctx,
                "sha256_first16MB": h.hexdigest()}


class MockBackend:
    """Deterministic fake: quotes the first sentence of the excerpt, picks a label by keyword. Tests only."""
    def chat(self, messages, schema=None, temperature=0.0, seed=0, max_new=None):
        user = messages[-1]["content"]
        body = user.split("<<<", 1)[-1].split(">>>", 1)[0]
        m = re.search(r"\n([A-Z][^.\n]{20,200}\.)", body)
        quote = m.group(1).strip() if m else ""
        props = (schema or {}).get("properties", {})
        if "label" in props:
            enum = props["label"].get("enum", ["UNCLEAR"])
            label = "RISK" if "RISK" in enum and "random" in body.lower() else enum[0]
            obj = {"evidence": [quote] if quote else [], "reasoning": "mock", "label": label}
        else:  # decomposed schema: first allowed value for enums, empty otherwise
            obj = {"evidence": [quote] if quote else []}
            for k, v in props.items():
                if k != "evidence":
                    obj[k] = v["enum"][0] if "enum" in v else ([] if v.get("type") == "array" else "")
        text = json.dumps(obj)
        return Reply(text, len(user) // 4, len(text) // 4, 0.001)

    def describe(self):
        return {"backend": "mock"}


def make_backend(kind, model=None, **kw):
    if kind == "ollama":
        return OllamaBackend(model, **kw)
    if kind == "openai":
        return OpenAICompatBackend(model, **kw)
    if kind == "llamacpp":
        return LlamaCppBackend(model, **kw)
    if kind == "mock":
        return MockBackend()
    raise ValueError(kind)
