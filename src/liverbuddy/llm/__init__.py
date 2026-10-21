from functools import lru_cache

from liverbuddy.config import Settings, get_settings
from liverbuddy.llm.base import (
    LLM,
    ChatResponse,
    Message,
    StructuredOutputError,
    ToolCall,
    structured,
    traced_chat,
)


def build_llm(settings: Settings) -> LLM:
    if settings.llm_provider == "gemini":
        from liverbuddy.llm.gemini import GeminiLLM

        if not settings.gemini_api_key:
            raise RuntimeError("LB_GEMINI_API_KEY is required when LB_LLM_PROVIDER=gemini")
        return GeminiLLM(settings.gemini_api_key, settings.gemini_chat_model, settings.gemini_embed_model)
    if settings.llm_provider == "fake":
        from liverbuddy.llm.fake import FakeLLM

        return FakeLLM()
    from liverbuddy.llm.ollama import OllamaLLM

    return OllamaLLM(settings.ollama_url, settings.ollama_chat_model, settings.ollama_vision_model,
                     settings.ollama_embed_model)


@lru_cache
def get_llm() -> LLM:
    return build_llm(get_settings())


__all__ = ["LLM", "ChatResponse", "Message", "StructuredOutputError", "ToolCall", "build_llm", "get_llm",
           "structured", "traced_chat"]
