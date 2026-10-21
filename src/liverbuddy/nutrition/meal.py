"""Meal analysis pipeline.

  text or photo -> LLM extracts items + estimated grams (structured)
               -> USDA FoodData Central candidates per item (hybrid matcher)
               -> LLM picks the best candidate (or none)            [optional rerank]
               -> nutrients = USDA per-100 g x grams                 (deterministic)
               -> liver-diet score                                   (deterministic)

The LLM identifies foods and estimates portions; every nutrient number comes from USDA data.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from liverbuddy.llm import LLM, Message, structured
from liverbuddy.nutrition.fdc import FoodMatch, FoodMatcher, Nutrients
from liverbuddy.observability import span
from liverbuddy.scoring.diet import Cooking, DietItem, DietScore, FoodGroup, score_meal

EXTRACT_SYSTEM = """You are a dietitian's assistant. List every distinct food or drink in the meal.

For each item give:
- name: short everyday name
- usda_query: how the USDA FoodData Central database would name the plain food, as "Head, modifiers", \
for example "Rice, white, cooked", "Chicken, breast, roasted", "Lentils, cooked, boiled", "Bananas, raw", \
"Beverages, carbonated, cola". USDA has common Western composite foods (for example "Pizza, pepperoni \
topping, regular crust", "Fast foods, hamburger", "Sandwich"), so keep those whole and set food_group by \
the main component. Mixed dishes with no USDA equivalent (for example samosa, biryani, dal tadka) should \
be split into their main ingredients, each listed as its own item.
- grams: realistic edible weight in grams (drinks in ml). Use stated amounts if given; otherwise estimate \
a typical portion for the stated portion size.
- food_group, cooking, ultra_processed (industrially formulated: soda, chips, instant noodles, packaged \
sweets, processed meat).
Only list foods that are actually present. Do not invent side dishes."""

RERANK_SYSTEM = """Match each food to the single best USDA database entry. Prefer plain, generic forms over \
branded, dried, powdered or regional variants, unless the food clearly is one of those. Answer 0 if no \
option is a reasonable match."""


class ExtractedItem(BaseModel):
    name: str
    usda_query: str
    grams: float = Field(gt=0, le=3000)
    food_group: FoodGroup
    cooking: Cooking = "unknown"
    ultra_processed: bool = False


class ExtractedMeal(BaseModel):
    items: list[ExtractedItem]


class _Choices(BaseModel):
    choices: list[int] = Field(description="For each food in order, the chosen option number (0 = none)")


class AnalyzedItem(BaseModel):
    name: str
    grams: float
    food_group: FoodGroup
    cooking: Cooking
    ultra_processed: bool
    usda_match: FoodMatch | None
    nutrients: Nutrients


class MealAnalysis(BaseModel):
    items: list[AnalyzedItem]
    totals: Nutrients
    diet: DietScore
    unmatched: list[str]
    source: str = "Nutrients: USDA FoodData Central SR Legacy (public domain). Portions are AI estimates."


def extract_items(llm: LLM, text: str | None = None, image: bytes | None = None,
                  portion_hint: str | None = None) -> ExtractedMeal:
    prompt = "Meal description: " + (text or "(see photo)")
    if portion_hint:
        prompt += f"\nPortion size: {portion_hint}"
    msgs = [Message("system", EXTRACT_SYSTEM), Message("user", prompt, images=[image] if image else [])]
    return structured(llm, msgs, ExtractedMeal, vision=image is not None, span="meal_extract")


def rerank(llm: LLM, items: list[ExtractedItem], candidates: list[list[FoodMatch]]) -> list[FoodMatch | None]:
    lines = []
    for n, (it, cands) in enumerate(zip(items, candidates, strict=True), 1):
        opts = "\n".join(f"   {k}. {c.description}" for k, c in enumerate(cands, 1))
        lines.append(f"Food {n}: {it.name} ({it.cooking.replace('_', ' ')})\n{opts}")
    msgs = [Message("system", RERANK_SYSTEM), Message("user", "\n\n".join(lines))]
    out = structured(llm, msgs, _Choices, span="meal_rerank")
    picks: list[FoodMatch | None] = []
    for n, cands in enumerate(candidates):
        k = out.choices[n] if n < len(out.choices) else 1
        picks.append(cands[k - 1] if 1 <= k <= len(cands) else None)
    return picks


def match_items(items: list[ExtractedItem], matcher: FoodMatcher, llm: LLM,
                use_rerank: bool = True) -> list[FoodMatch | None]:
    with span("nutrition", "candidates", n_items=len(items)):
        candidates = [matcher.candidates(it.usda_query, llm, k=8) for it in items]
    if use_rerank and items:
        return rerank(llm, items, candidates)
    return [c[0] if c else None for c in candidates]


def analyze_meal(llm: LLM, matcher: FoodMatcher, text: str | None = None, image: bytes | None = None,
                 portion_hint: str | None = None, use_rerank: bool = True) -> MealAnalysis:
    meal = extract_items(llm, text, image, portion_hint)
    matches = match_items(meal.items, matcher, llm, use_rerank)
    analyzed, unmatched = [], []
    for it, m in zip(meal.items, matches, strict=True):
        nut = m.per_100g.scaled(it.grams) if m else Nutrients()
        if m is None:
            unmatched.append(it.name)
        analyzed.append(AnalyzedItem(name=it.name, grams=it.grams, food_group=it.food_group, cooking=it.cooking,
                                     ultra_processed=it.ultra_processed, usda_match=m, nutrients=nut))
    totals = sum((a.nutrients for a in analyzed), Nutrients())
    diet = score_meal([DietItem(name=a.name, grams=a.grams, food_group=a.food_group, cooking=a.cooking,
                                ultra_processed=a.ultra_processed, kcal=a.nutrients.kcal,
                                sugars_g=a.nutrients.sugars_g, sat_fat_g=a.nutrients.sat_fat_g,
                                fiber_g=a.nutrients.fiber_g, sodium_mg=a.nutrients.sodium_mg) for a in analyzed])
    return MealAnalysis(items=analyzed, totals=totals, diet=diet, unmatched=unmatched)
