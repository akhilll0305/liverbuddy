"""Lightweight tracing: every LLM call and tool call becomes a span with latency and token counts.

Spans are buffered per request (contextvar) so the API can return them, and appended to
artifacts/traces.jsonl for offline latency and cost analysis (`liverbuddy traces`).
"""

from __future__ import annotations

import json
import re
import threading
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any

_spans: ContextVar[list[dict] | None] = ContextVar("spans", default=None)
_trace_id: ContextVar[str] = ContextVar("trace_id", default="")
_lock = threading.Lock()
_sink: Path | None = None

_PII = [(re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "<email>"), (re.compile(r"\+?\d[\d\s-]{8,}\d"), "<phone>")]


def redact(text: str) -> str:
    for pat, repl in _PII:
        text = pat.sub(repl, text)
    return text


def configure_sink(path: Path) -> None:
    global _sink
    path.parent.mkdir(parents=True, exist_ok=True)
    _sink = path


@contextmanager
def trace(name: str) -> Iterator[list[dict]]:
    """Open a request-level trace; yields the list that collects its spans."""
    spans: list[dict] = []
    t_tok, s_tok = _trace_id.set(uuid.uuid4().hex[:12]), _spans.set(spans)
    start = time.perf_counter()
    try:
        yield spans
    finally:
        _emit({"kind": "trace", "name": name, "latency_ms": round((time.perf_counter() - start) * 1000, 1),
               "n_spans": len(spans)})
        _trace_id.reset(t_tok)
        _spans.reset(s_tok)


@contextmanager
def span(kind: str, name: str, **attrs: Any) -> Iterator[dict]:
    rec: dict[str, Any] = {"kind": kind, "name": name, **attrs}
    start = time.perf_counter()
    try:
        yield rec
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"[:300]
        raise
    finally:
        rec["latency_ms"] = round((time.perf_counter() - start) * 1000, 1)
        spans = _spans.get()
        if spans is not None:
            spans.append(rec)
        _emit(rec)


def record_llm_call(name: str, **attrs: Any):
    return span("llm", name, **attrs)


def _emit(rec: dict) -> None:
    if _sink is None:
        return
    line = json.dumps({"ts": time.time(), "trace_id": _trace_id.get(), **rec}, default=str)
    with _lock, _sink.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def summarize(path: Path) -> dict:
    """p50/p95 latency and token totals per span name, for the metrics page."""
    import numpy as np

    rows: dict[str, list[dict]] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            rows.setdefault(f"{r['kind']}:{r['name']}", []).append(r)
    out = {}
    for key, rs in sorted(rows.items()):
        lat = np.array([r["latency_ms"] for r in rs])
        out[key] = {"count": len(rs), "p50_ms": float(np.percentile(lat, 50)),
                    "p95_ms": float(np.percentile(lat, 95)),
                    "errors": sum(1 for r in rs if r.get("error")),
                    "input_tokens": sum(r.get("input_tokens", 0) for r in rs),
                    "output_tokens": sum(r.get("output_tokens", 0) for r in rs)}
    return out
