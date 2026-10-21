"""Provider-agnostic LLM interface. Tools use the OpenAI/Ollama JSON-schema function format."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, TypeVar

import numpy as np
from pydantic import BaseModel, ValidationError

from liverbuddy.observability import record_llm_call

T = TypeVar("T", bound=BaseModel)


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]
    id: str = ""


@dataclass
class Message:
    role: Literal["system", "user", "assistant", "tool"]
    content: str = ""
    images: list[bytes] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_name: str = ""  # for role == "tool"


@dataclass
class ChatResponse:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0


class LLM(Protocol):
    name: str

    def chat(self, messages: list[Message], *, tools: list[dict] | None = None,
             schema: dict | None = None, temperature: float = 0.1, vision: bool = False) -> ChatResponse: ...

    def embed(self, texts: list[str], *, kind: Literal["query", "document"]) -> np.ndarray: ...


class StructuredOutputError(RuntimeError):
    pass


def structured(llm: LLM, messages: list[Message], model: type[T], *, retries: int = 2,
               temperature: float = 0.0, vision: bool = False, span: str = "structured") -> T:
    """Ask for JSON matching `model`'s schema; validate, and feed validation errors back on failure."""
    msgs = list(messages)
    schema = model.model_json_schema()
    last_err = ""
    for _ in range(retries + 1):
        resp = traced_chat(llm, msgs, schema=schema, temperature=temperature, vision=vision, span=span)
        try:
            return model.model_validate_json(_extract_json(resp.content))
        except (ValidationError, ValueError) as e:
            last_err = str(e)[:800]
            msgs = msgs + [Message("assistant", resp.content),
                           Message("user", f"That JSON was invalid: {last_err}\nReturn only corrected JSON.")]
    raise StructuredOutputError(last_err)


def traced_chat(llm: LLM, messages: list[Message], *, span: str, **kw) -> ChatResponse:
    with record_llm_call(span, provider=llm.name) as rec:
        resp = llm.chat(messages, **kw)
        rec.update(model=resp.model, input_tokens=resp.input_tokens, output_tokens=resp.output_tokens,
                   tool_calls=[t.name for t in resp.tool_calls])
    return resp


def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):]
    start = min((i for i in (text.find("{"), text.find("[")) if i >= 0), default=-1)
    if start < 0:
        raise ValueError("no JSON object in response")
    json.loads(text[start:])  # raises ValueError with position info
    return text[start:]
