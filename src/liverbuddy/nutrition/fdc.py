"""USDA FoodData Central (SR Legacy, public domain) nutrient lookup with hybrid food matching."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from pydantic import BaseModel
from rapidfuzz import fuzz, process

from liverbuddy.llm import LLM

NUTRIENTS = {  # FDC nutrient_id -> field (amount per 100 g)
    1008: "kcal", 1003: "protein_g", 1004: "fat_g", 1005: "carbs_g", 1079: "fiber_g",
    2000: "sugars_g", 1258: "sat_fat_g", 1093: "sodium_mg",
}


class Nutrients(BaseModel):
    kcal: float = 0
    protein_g: float = 0
    fat_g: float = 0
    carbs_g: float = 0
    fiber_g: float = 0
    sugars_g: float = 0
    sat_fat_g: float = 0
    sodium_mg: float = 0

    def scaled(self, grams: float) -> Nutrients:
        f = grams / 100.0
        return Nutrients(**{k: round(v * f, 2) for k, v in self.model_dump().items()})

    def __add__(self, other: Nutrients) -> Nutrients:
        return Nutrients(**{k: round(getattr(self, k) + getattr(other, k), 2) for k in NUTRIENTS.values()})


@dataclass
class Food:
    fdc_id: int
    description: str
    category: str
    per_100g: Nutrients


class FoodMatch(BaseModel):
    fdc_id: int
    description: str
    category: str
    confidence: float  # 0-1, blended dense + fuzzy
    per_100g: Nutrients


def build_food_table(fdc_dir: Path, out_path: Path) -> int:
    cats = {}
    with (fdc_dir / "food_category.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cats[row["id"]] = row["description"]
    foods: dict[str, dict] = {}
    with (fdc_dir / "food.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            foods[row["fdc_id"]] = {"fdc_id": int(row["fdc_id"]), "description": row["description"],
                                    "category": cats.get(row["food_category_id"], ""),
                                    "per_100g": {v: 0.0 for v in NUTRIENTS.values()}}
    with (fdc_dir / "food_nutrient.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            field = NUTRIENTS.get(int(row["nutrient_id"]))
            if field and row["fdc_id"] in foods and row["amount"]:
                foods[row["fdc_id"]]["per_100g"][field] = float(row["amount"])
    rows = [r for r in foods.values() if r["per_100g"]["kcal"] or r["category"] == "Beverages"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rows), encoding="utf-8")
    return len(rows)


class FoodMatcher:
    """Dense (embedding) + fuzzy string matching over USDA descriptions."""

    def __init__(self, foods: list[Food], embeddings: np.ndarray | None):
        self.foods = foods
        self.embeddings = embeddings
        self._desc = [f.description.lower() for f in foods]
        self._by_head: dict[str, list[int]] = {}
        for i, d in enumerate(self._desc):
            head = d.split(",")[0].strip()
            if head:
                self._by_head.setdefault(_singular(head.split()[-1]), []).append(i)

    @classmethod
    def load(cls, table_path: Path, emb_path: Path | None = None) -> FoodMatcher:
        rows = json.loads(table_path.read_text(encoding="utf-8"))
        foods = [Food(r["fdc_id"], r["description"], r["category"], Nutrients(**r["per_100g"])) for r in rows]
        emb = np.load(emb_path).astype(np.float32) if emb_path and emb_path.exists() else None
        return cls(foods, emb)

    def embed_all(self, llm: LLM, out_path: Path) -> None:
        self.embeddings = llm.embed([f"{f.description} ({f.category})" for f in self.foods], kind="document")
        np.save(out_path, self.embeddings.astype(np.float16))

    def _score(self, i: int, q_tokens: list[str], dense: float, fuzzy: float, branded_query: bool) -> float:
        desc = self._desc[i]
        query_text = " ".join(q_tokens)
        segments = [s.strip() for s in desc.split(",")]
        head = _singular(segments[0].split()[-1]) if segments[0] else ""
        # USDA puts the food first ("Rice, brown, cooked"); agreeing on it matters more than any modifier
        head_match = max((fuzz.ratio(_singular(t), head) / 100 for t in q_tokens), default=0.0)
        head_match = head_match if head_match >= 0.85 else 0.0
        mods = set(" ".join(segments[1:]).replace("(", " ").replace(")", " ").split())
        mod_overlap = len(mods & {_singular(t) for t in q_tokens} | mods & set(q_tokens)) / max(len(q_tokens), 1)
        branded = any(w.isupper() and len(w) > 2 for w in self.foods[i].description.split()) \
            or desc.startswith(("fast foods", "restaurant", "babyfood", "infant formula"))
        penalty = 0.02 * max(len(segments) - 3, 0) + (0.25 if branded and not branded_query else 0.0)
        # unrequested processing ("dehydrated banana") or regional preparations ("(Navajo)") are rarely meant
        q_set = set(q_tokens)
        penalty += 0.12 * sum(1 for w in _PROCESSING if w in desc and w not in q_set)
        penalty += 0.15 if any(r in desc and r not in query_text for r in _REGIONAL) else 0.0
        return 0.40 * dense + 0.30 * head_match + 0.15 * mod_overlap + 0.15 * fuzzy - penalty

    def candidates(self, query: str, llm: LLM | None = None, k: int = 8) -> list[FoodMatch]:
        q = query.lower().strip()
        q_tokens = [t for t in q.replace(",", " ").split() if len(t) > 1]
        fuzzy = {i: s / 100 for _, s, i in process.extract(q, self._desc, scorer=fuzz.token_set_ratio, limit=150)}
        sims = np.zeros(len(self.foods), dtype=np.float32)
        dense_pool: set[int] = set()
        if llm is not None and self.embeddings is not None:
            sims = self.embeddings @ llm.embed([query], kind="query")[0]
            dense_pool = {int(i) for i in np.argsort(-sims)[:150]}
        branded_query = any(b in q for b in ("mcdonald", "burger king", "kfc", "subway", "domino", "pizza hut"))
        by_head = {i for t in q_tokens for i in self._by_head.get(_singular(t), [])}
        scores = {i: self._score(i, q_tokens, float(sims[i]), fuzzy.get(i, 0.0), branded_query)
                  for i in set(fuzzy) | dense_pool | by_head}
        best = sorted(scores, key=scores.get, reverse=True)[:k]
        return [FoodMatch(fdc_id=self.foods[i].fdc_id, description=self.foods[i].description,
                          category=self.foods[i].category, confidence=round(max(min(scores[i], 1.0), 0.0), 3),
                          per_100g=self.foods[i].per_100g) for i in best]

    def match(self, query: str, llm: LLM | None = None, k: int = 5) -> list[FoodMatch]:
        return self.candidates(query, llm, k=k)


_PROCESSING = ("dehydrated", "powder", "dried", "dry mix", "canned", "frozen", "smoked", "concentrate",
               "unprepared", "sprouted", "freeze-dried", "pickled", "candied")
_REGIONAL = ("alaska native", "navajo", "hopi", "northern plains", "apache", "shoshone", "chinese",
             "malabar", "new zealand")


def _singular(word: str) -> str:
    word = word.strip("()")
    for suffix, repl in (("ies", "y"), ("oes", "o"), ("ses", "s"), ("s", "")):
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            return word[: -len(suffix)] + repl
    return word
