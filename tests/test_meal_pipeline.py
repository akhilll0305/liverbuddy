import json

import numpy as np
import pytest

from liverbuddy.llm import ChatResponse
from liverbuddy.llm.fake import FakeLLM
from liverbuddy.nutrition.fdc import Food, FoodMatcher, Nutrients
from liverbuddy.nutrition.meal import analyze_meal

FOODS = [
    Food(1, "Bananas, raw", "Fruits", Nutrients(kcal=89, carbs_g=23, sugars_g=12, fiber_g=2.6)),
    Food(2, "Bananas, dehydrated, or banana powder", "Fruits", Nutrients(kcal=346, sugars_g=47)),
    Food(3, "Beverages, carbonated, cola", "Beverages", Nutrients(kcal=37, sugars_g=9)),
    Food(4, "Rice, white, cooked", "Cereal Grains", Nutrients(kcal=130, carbs_g=28)),
]


def responder(msgs, tools, schema):
    props = (schema or {}).get("properties", {})
    if "items" in props:
        return ChatResponse(content=json.dumps({"items": [
            {"name": "banana", "usda_query": "Bananas, raw", "grams": 120, "food_group": "fruit", "cooking": "raw"},
            {"name": "cola", "usda_query": "Beverages, carbonated, cola", "grams": 330,
             "food_group": "sugary_drink", "ultra_processed": True},
        ]}))
    # rerank: choose the option whose text is the plain form
    user = msgs[-1].content
    choices = []
    for block in user.split("Food ")[1:]:
        opts = [line.strip() for line in block.splitlines()[1:] if line.strip()]
        pick = next((k for k, o in enumerate(opts, 1) if "dehydrated" not in o), 0)
        choices.append(pick)
    return ChatResponse(content=json.dumps({"choices": choices}))


@pytest.fixture
def matcher():
    return FoodMatcher(FOODS, None)


def test_meal_nutrients_come_from_usda_scaled_by_grams(matcher):
    a = analyze_meal(FakeLLM(responder), matcher, text="a banana and a can of coke")
    banana, cola = a.items
    assert banana.usda_match.fdc_id == 1  # plain, not dehydrated
    assert banana.nutrients.kcal == pytest.approx(89 * 1.2)
    assert cola.nutrients.kcal == pytest.approx(37 * 3.3)
    assert a.totals.kcal == pytest.approx(89 * 1.2 + 37 * 3.3, abs=0.1)
    assert any("Sugar-sweetened" in adj.reason for adj in a.diet.adjustments)


def test_without_rerank_uses_top_candidate(matcher):
    a = analyze_meal(FakeLLM(responder), matcher, text="banana and cola", use_rerank=False)
    assert all(it.usda_match is not None for it in a.items)
    assert not np.isnan(a.totals.kcal)


def test_unmatched_dish_is_decomposed_into_ingredients(matcher):
    calls = {"n": 0}

    def responder(msgs, tools, schema):
        props = (schema or {}).get("properties", {})
        user = msgs[-1].content
        if "items" in props and "no single entry" in user:
            return ChatResponse(content=json.dumps({"items": [
                {"name": "rice", "usda_query": "Rice, white, cooked", "grams": 250, "food_group": "refined_grain"}]}))
        if "items" in props:
            return ChatResponse(content=json.dumps({"items": [
                {"name": "biryani", "usda_query": "Biryani", "grams": 300, "food_group": "other", "cooking": "fried"}]}))
        calls["n"] += 1
        # first rerank: biryani -> none; second: rice -> option 1
        return ChatResponse(content=json.dumps({"choices": [0] if calls["n"] == 1 else [1]}))

    a = analyze_meal(FakeLLM(responder), matcher, text="chicken biryani")
    assert [i.name for i in a.items] == ["rice"]
    assert a.items[0].cooking == "fried"  # inherited from the dish
    assert a.totals.kcal == pytest.approx(130 * 2.5)
    assert a.unmatched == []
