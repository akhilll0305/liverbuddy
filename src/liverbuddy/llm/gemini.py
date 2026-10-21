"""Google Gemini via the `google-genai` SDK. Same interface as the Ollama adapter."""

from __future__ import annotations

import io
from typing import Literal

import numpy as np

from liverbuddy.llm.base import ChatResponse, Message, ToolCall


def _mime(img: bytes) -> str:
    from PIL import Image

    fmt = (Image.open(io.BytesIO(img)).format or "JPEG").lower()
    return f"image/{'jpeg' if fmt == 'jpg' else fmt}"


class GeminiLLM:
    name = "gemini"

    def __init__(self, api_key: str, chat_model: str, embed_model: str):
        from google import genai

        self.client = genai.Client(api_key=api_key)
        self.chat_model, self.embed_model = chat_model, embed_model

    def chat(self, messages: list[Message], *, tools: list[dict] | None = None, schema: dict | None = None,
             temperature: float = 0.1, vision: bool = False) -> ChatResponse:
        from google.genai import types

        system = "\n\n".join(m.content for m in messages if m.role == "system") or None
        contents = []
        for m in messages:
            if m.role == "system":
                continue
            if m.role == "tool":
                part = types.Part.from_function_response(name=m.tool_name, response={"result": m.content})
                contents.append(types.Content(role="user", parts=[part]))
                continue
            parts = [types.Part.from_text(text=m.content)] if m.content else []
            parts += [types.Part.from_bytes(data=i, mime_type=_mime(i)) for i in m.images]
            parts += [types.Part.from_function_call(name=t.name, args=t.arguments) for t in m.tool_calls]
            contents.append(types.Content(role="model" if m.role == "assistant" else "user", parts=parts))

        config = types.GenerateContentConfig(system_instruction=system, temperature=temperature)
        if tools:
            config.tools = [types.Tool(function_declarations=[
                types.FunctionDeclaration(name=t["function"]["name"], description=t["function"]["description"],
                                          parameters_json_schema=t["function"]["parameters"])
                for t in tools])]
        if schema:
            config.response_mime_type = "application/json"
            config.response_json_schema = schema
        resp = self.client.models.generate_content(model=self.chat_model, contents=contents, config=config)
        calls = [ToolCall(name=fc.name, arguments=dict(fc.args or {}), id=fc.id or "")
                 for fc in (resp.function_calls or [])]
        usage = resp.usage_metadata
        return ChatResponse(content=resp.text or "", tool_calls=calls, model=self.chat_model,
                            input_tokens=getattr(usage, "prompt_token_count", 0) or 0,
                            output_tokens=getattr(usage, "candidates_token_count", 0) or 0)

    def embed(self, texts: list[str], *, kind: Literal["query", "document"]) -> np.ndarray:
        from google.genai import types

        task = "RETRIEVAL_QUERY" if kind == "query" else "RETRIEVAL_DOCUMENT"
        out = []
        for i in range(0, len(texts), 100):
            r = self.client.models.embed_content(model=self.embed_model, contents=texts[i:i + 100],
                                                 config=types.EmbedContentConfig(task_type=task))
            out.extend(e.values for e in r.embeddings)
        arr = np.asarray(out, dtype=np.float32)
        return arr / np.linalg.norm(arr, axis=1, keepdims=True).clip(min=1e-9)
