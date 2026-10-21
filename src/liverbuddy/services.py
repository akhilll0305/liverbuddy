"""Lazily-loaded shared resources (LLM, indexes, drug table, food matcher, risk models)."""

from __future__ import annotations

from functools import cached_property

from liverbuddy.config import Settings, get_settings
from liverbuddy.drugs.livertox import LiverTox
from liverbuddy.llm import LLM, build_llm
from liverbuddy.ml.predict import RiskModels
from liverbuddy.nutrition.fdc import FoodMatcher
from liverbuddy.observability import configure_sink
from liverbuddy.rag.index import HybridIndex


class ResourceMissing(RuntimeError):
    """A built artifact is absent; the message says which CLI command creates it."""


class Services:
    def __init__(self, settings: Settings | None = None, llm: LLM | None = None):
        self.settings = settings or get_settings()
        self._llm = llm
        configure_sink(self.settings.artifacts_dir / "traces.jsonl")

    @cached_property
    def llm(self) -> LLM:
        return self._llm or build_llm(self.settings)

    def _need(self, path, cmd: str):
        if not path.exists():
            raise ResourceMissing(f"{path.name} not found. Run `liverbuddy {cmd}` first.")
        return path

    @cached_property
    def guidelines(self) -> HybridIndex:
        self._need(self.settings.index_dir / "guidelines.jsonl", "build-index")
        return HybridIndex.load(self.settings.index_dir, "guidelines")

    @cached_property
    def livertox_index(self) -> HybridIndex:
        self._need(self.settings.index_dir / "livertox.jsonl", "build-index")
        return HybridIndex.load(self.settings.index_dir, "livertox")

    @cached_property
    def livertox(self) -> LiverTox:
        return LiverTox(self._need(self.settings.index_dir / "livertox_drugs.json", "build-index"))

    @cached_property
    def foods(self) -> FoodMatcher:
        table = self._need(self.settings.index_dir / "foods.json", "build-index")
        return FoodMatcher.load(table, self.settings.index_dir / "foods.npy")

    @cached_property
    def risk(self) -> RiskModels:
        if not (self.settings.model_dir / "steatosis_full.json").exists():
            raise ResourceMissing("Risk models not found. Run `liverbuddy train` first.")
        return RiskModels(self.settings.model_dir)

    def status(self) -> dict[str, bool]:
        idx = self.settings.index_dir
        return {
            "guidelines_index": (idx / "guidelines.jsonl").exists(),
            "livertox_index": (idx / "livertox.jsonl").exists(),
            "livertox_table": (idx / "livertox_drugs.json").exists(),
            "food_table": (idx / "foods.json").exists(),
            "risk_models": (self.settings.model_dir / "steatosis_full.json").exists(),
        }
