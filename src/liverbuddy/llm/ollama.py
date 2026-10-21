"""Local inference through Ollama's REST API (chat, tool calling, JSON-schema output, vision, embeddings)."""

from __future__ import annotations

import base64
import io
from typing import Literal

import httpx
import numpy as np

from liverbuddy.llm.base import ChatResponse, Message, ToolCall


class OllamaLLM:
    name = "ollama"

    def __init__(self, url: str, chat_model: str, vision_model: str, embed_model: str, timeout: float = 300):
        self.url = url.rstrip("/")
        self.chat_model, self.vision_model, self.embed_model = chat_model, vision_model, embed_model
        self.http = httpx.Client(timeout=timeout)

    @staticmethod
    def _downscale(img: bytes, max_side: int = 768) -> bytes:
        """Vision token count grows with resolution; 768px keeps food detail and fits 8 GB machines."""
        from PIL import Image

        im = Image.open(io.BytesIO(img)).convert("RGB")
        im.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=90)
        return buf.getvalue()

    def _msg(self, m: Message) -> dict:
        d: dict = {"role": m.role, "content": m.content}
        if m.images:
            d["images"] = [base64.b64encode(self._downscale(i)).decode() for i in m.images]
        if m.tool_calls:
            d["tool_calls"] = [{"function": {"name": t.name, "arguments": t.arguments}} for t in m.tool_calls]
        if m.role == "tool":
            d["tool_name"] = m.tool_name
        return d

    def chat(self, messages: list[Message], *, tools: list[dict] | None = None, schema: dict | None = None,
             temperature: float = 0.1, vision: bool = False) -> ChatResponse:
        model = self.vision_model if vision else self.chat_model
        if vision:  # free the text model first so both never compete for RAM/VRAM
            self.http.post(f"{self.url}/api/generate", json={"model": self.chat_model, "keep_alive": 0})
        payload: dict = {"model": model, "messages": [self._msg(m) for m in messages], "stream": False,
                         "options": {"temperature": temperature, "num_ctx": 4096 if vision else 8192}}
        if tools:
            payload["tools"] = tools
        if schema:
            payload["format"] = schema
        r = self.http.post(f"{self.url}/api/chat", json=payload)
        r.raise_for_status()
        data = r.json()
        msg = data.get("message", {})
        calls = [ToolCall(name=c["function"]["name"], arguments=c["function"].get("arguments") or {})
                 for c in msg.get("tool_calls") or []]
        return ChatResponse(content=msg.get("content", ""), tool_calls=calls, model=model,
                            input_tokens=data.get("prompt_eval_count", 0),
                            output_tokens=data.get("eval_count", 0))

    def embed(self, texts: list[str], *, kind: Literal["query", "document"]) -> np.ndarray:
        # nomic-embed-text is trained with task prefixes
        prefix = "search_query: " if kind == "query" else "search_document: "
        out = []
        for i in range(0, len(texts), 64):
            batch = [prefix + t for t in texts[i:i + 64]]
            r = self.http.post(f"{self.url}/api/embed", json={"model": self.embed_model, "input": batch})
            r.raise_for_status()
            out.extend(r.json()["embeddings"])
        arr = np.asarray(out, dtype=np.float32)
        return arr / np.linalg.norm(arr, axis=1, keepdims=True).clip(min=1e-9)
