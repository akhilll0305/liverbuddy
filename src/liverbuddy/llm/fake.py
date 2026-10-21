"""Deterministic offline LLM for tests and CI: scripted replies + hashed bag-of-words embeddings."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from typing import Literal

import numpy as np

from liverbuddy.llm.base import ChatResponse, Message

Responder = Callable[[list[Message], list[dict] | None, dict | None], ChatResponse]


class FakeLLM:
    name = "fake"

    def __init__(self, responder: Responder | None = None, dim: int = 256):
        self.responder = responder
        self.dim = dim
        self.calls: list[list[Message]] = []

    def chat(self, messages: list[Message], *, tools: list[dict] | None = None, schema: dict | None = None,
             temperature: float = 0.1, vision: bool = False) -> ChatResponse:
        self.calls.append(messages)
        if self.responder:
            return self.responder(messages, tools, schema)
        return ChatResponse(content="{}", model="fake")

    def embed(self, texts: list[str], *, kind: Literal["query", "document"]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, t in enumerate(texts):
            for tok in re.findall(r"[a-z0-9]+", t.lower()):
                h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
                out[i, h % self.dim] += 1.0
        return out / np.linalg.norm(out, axis=1, keepdims=True).clip(min=1e-9)
