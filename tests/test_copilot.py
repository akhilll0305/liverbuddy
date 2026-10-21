import pytest

from liverbuddy.agent.copilot import ask
from liverbuddy.agent.tools import ToolContext
from liverbuddy.config import Settings
from liverbuddy.llm import ChatResponse, ToolCall
from liverbuddy.llm.fake import FakeLLM
from liverbuddy.rag.corpus import Chunk
from liverbuddy.rag.index import HybridIndex
from liverbuddy.services import Services


def scripted(*responses):
    queue = list(responses)

    def responder(msgs, tools, schema):
        return queue.pop(0) if queue else ChatResponse(content="done")
    return responder


@pytest.fixture
def services(tmp_path):
    fake = FakeLLM()
    chunks = [Chunk("g-0", "aasld2023", "AASLD 2023", "Lifestyle", "Coffee consumption is associated with less "
                    "liver fibrosis in fatty liver disease.", "u", "text")]
    for name in ("guidelines", "livertox"):
        HybridIndex.build(chunks, fake, "fake").save(tmp_path / "index", name)
    return Services(Settings(artifacts_dir=tmp_path, llm_provider="fake"), llm=fake)


def test_emergency_short_circuits_without_llm(services):
    r = ask(ToolContext(services=services), "I am vomiting blood")
    assert r.guardrail == "emergency" and services.llm.calls == []


def test_tool_loop_keeps_valid_and_strips_invented_citations(services):
    services.llm.responder = scripted(
        ChatResponse(content="", tool_calls=[ToolCall("search_guidelines", {"query": "coffee liver fibrosis"})]),
        ChatResponse(content="Coffee is linked to less fibrosis [1]. It also cures cancer [5]."),
    )
    r = ask(ToolContext(services=services), "Is coffee good for my liver?")
    assert [t.name for t in r.tools] == ["search_guidelines"]
    assert r.removed_invalid_citations == [5]
    assert "[5]" not in r.answer and "[1]" in r.answer
    assert r.citations[0]["chunk_id"] == "g-0"


def test_ungrounded_first_answer_is_nudged_to_use_tools(services):
    services.llm.responder = scripted(
        ChatResponse(content="Coffee is great."),  # no tool call -> nudge
        ChatResponse(content="", tool_calls=[ToolCall("search_guidelines", {"query": "coffee liver fibrosis"})]),
        ChatResponse(content="Coffee is associated with less fibrosis [1]."),
    )
    r = ask(ToolContext(services=services), "Is coffee good for fatty liver?")
    assert r.steps == 3 and r.tools and r.citations


def test_tool_errors_are_reported_not_raised(services):
    services.llm.responder = scripted(
        ChatResponse(content="", tool_calls=[ToolCall("no_such_tool", {})]),
        ChatResponse(content="Sorry, I could not look that up."),
    )
    r = ask(ToolContext(services=services), "hello there, what's my risk")
    assert r.tools[0].error == "unknown_tool"


def test_start_stop_question_gets_notice_and_answer(services):
    services.llm.responder = scripted(
        ChatResponse(content="", tool_calls=[ToolCall("search_guidelines", {"query": "coffee liver fibrosis"})]),
        ChatResponse(content="Statins are considered safe [1]."),
    )
    r = ask(ToolContext(services=services), "Should I stop taking my statin?")
    assert r.guardrail == "caution_medication"
    assert r.answer.startswith("Please don't start or stop")
