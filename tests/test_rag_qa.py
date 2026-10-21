import json

import pytest

from liverbuddy.llm import ChatResponse
from liverbuddy.llm.fake import FakeLLM
from liverbuddy.rag.corpus import Chunk
from liverbuddy.rag.index import HybridIndex
from liverbuddy.rag.qa import answer_question

CHUNKS = [
    Chunk("g-0", "aasld2023", "AASLD", "Dyslipidemia", "Statins are safe in patients with fatty liver disease "
          "and recommended for cardiovascular risk reduction.", "u#1", "text"),
    Chunk("g-1", "aasld2023", "AASLD", "Lifestyle", "Weight loss of 7 to 10 percent improves liver fat, "
          "steatohepatitis and fibrosis in fatty liver disease.", "u#2", "text"),
    Chunk("g-2", "easl2024", "EASL", "Coffee", "Coffee consumption is associated with less liver fibrosis.",
          "u#3", "text"),
]


def make_llm(reply: dict) -> FakeLLM:
    return FakeLLM(lambda msgs, tools, schema: ChatResponse(content=json.dumps(reply), model="fake"))


@pytest.fixture
def index():
    return HybridIndex.build(CHUNKS, FakeLLM(), "fake")


def test_grounded_answer_keeps_valid_citations(index):
    llm = make_llm({"answer": "Yes, statins are safe [1].", "cited_sources": [1], "insufficient_evidence": False})
    a = answer_question("are statins safe in fatty liver disease", llm, [index], k=3, min_similarity=0.1)
    assert not a.abstained
    assert a.citations[0].chunk_id == "g-0"


def test_invented_citation_is_withheld(index):
    llm = make_llm({"answer": "Statins are safe [7].", "cited_sources": [7], "insufficient_evidence": False})
    a = answer_question("are statins safe in fatty liver disease", llm, [index], k=3, min_similarity=0.1)
    assert a.abstained and a.reason == "invented_citation"


def test_uncited_answer_is_withheld(index):
    llm = make_llm({"answer": "Statins are safe.", "cited_sources": [], "insufficient_evidence": False})
    a = answer_question("are statins safe in fatty liver disease", llm, [index], k=3, min_similarity=0.1)
    assert a.abstained and a.reason == "no_citations"


def test_low_similarity_abstains_without_calling_llm(index):
    llm = make_llm({"answer": "x [1]", "cited_sources": [1], "insufficient_evidence": False})
    a = answer_question("who won the football world cup", llm, [index], k=3, min_similarity=0.5)
    assert a.abstained and a.reason == "low_retrieval_similarity"
    assert llm.calls == []


def test_model_can_report_insufficient_evidence(index):
    llm = make_llm({"answer": "Not covered.", "cited_sources": [], "insufficient_evidence": True})
    a = answer_question("is coffee good for fatty liver disease", llm, [index], k=3, min_similarity=0.1)
    assert a.abstained and a.reason == "model_reported_insufficient_evidence"


def test_hybrid_search_ranks_lexical_match_first(index):
    hits = index.search("coffee fibrosis", FakeLLM(), k=3)
    assert hits[0].chunk.id == "g-2"
    assert index.search("coffee", FakeLLM(), k=3, sources=["aasld2023"])[0].chunk.source == "aasld2023"


def test_save_load_roundtrip(index, tmp_path):
    index.save(tmp_path, "t")
    loaded = HybridIndex.load(tmp_path, "t")
    assert [c.id for c in loaded.chunks] == [c.id for c in CHUNKS]
    assert loaded.search("statins", FakeLLM(), k=1)[0].chunk.id == "g-0"
