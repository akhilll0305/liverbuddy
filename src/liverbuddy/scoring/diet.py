"""Transparent, rule-based liver-diet score for a single meal (0-100).

Rules encode the dietary advice shared by the EASL-EASD-EASO 2024 and AASLD 2023 guidance:
a Mediterranean-style pattern (vegetables, legumes, whole grains, fish, nuts, olive oil); limiting
ultra-processed food, sugar-sweetened beverages, free sugars, saturated fat and red/processed meat;
and avoiding alcohol. Each adjustment is reported so the user sees exactly why a meal scored as it did.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

FoodGroup = Literal["vegetable", "fruit", "whole_grain", "refined_grain", "legume", "nuts_seeds",
                    "fish_seafood", "poultry", "red_meat", "processed_meat", "dairy", "egg", "added_fat_oil",
                    "sweets_dessert", "sugary_drink", "alcohol", "other_beverage", "other"]
Cooking = Literal["raw", "boiled_steamed", "grilled_baked_roasted", "sauteed", "fried", "deep_fried", "unknown"]

BASE = 75


class DietItem(BaseModel):
    name: str
    grams: float
    food_group: FoodGroup
    cooking: Cooking = "unknown"
    ultra_processed: bool = False
    kcal: float = 0
    sugars_g: float = 0
    sat_fat_g: float = 0
    fiber_g: float = 0
    sodium_mg: float = 0


class Adjustment(BaseModel):
    points: int
    reason: str


class DietScore(BaseModel):
    score: int
    verdict: Literal["Excellent", "Good", "Fair", "Poor"]
    adjustments: list[Adjustment]
    basis: str = ("Rules derived from the EASL-EASD-EASO 2024 MASLD guideline and the AASLD 2023 practice "
                  "guidance (Mediterranean pattern; limit ultra-processed food, sugary drinks, free sugars, "
                  "saturated fat, red and processed meat; avoid alcohol).")


def score_meal(items: list[DietItem]) -> DietScore:
    adj: list[Adjustment] = []

    def add(points: int, reason: str) -> None:
        adj.append(Adjustment(points=points, reason=reason))

    groups = [i.food_group for i in items]
    grams_in = lambda *gs: sum(i.grams for i in items if i.food_group in gs)  # noqa: E731
    kcal = sum(i.kcal for i in items)
    sat = sum(i.sat_fat_g for i in items)
    fiber = sum(i.fiber_g for i in items)
    sodium = sum(i.sodium_mg for i in items)
    # free-sugar proxy: sugars outside whole fruit, vegetables and plain dairy
    free_sugar = sum(i.sugars_g for i in items if i.food_group not in ("fruit", "vegetable", "dairy"))

    if "alcohol" in groups:
        add(-25, "Contains alcohol. Guidelines advise people with MASLD to minimise or avoid alcohol.")
    if "sugary_drink" in groups:
        add(-20, "Sugar-sweetened drink. Fructose-sweetened beverages are strongly linked to liver fat.")
    fried = [i.name for i in items if i.cooking in ("fried", "deep_fried")]
    if fried:
        add(-min(8 * len(fried), 16), f"Fried food ({', '.join(fried)}). Grilling, baking or steaming is better.")
    upf = [i.name for i in items if i.ultra_processed]
    if upf:
        add(-min(8 * len(upf), 16), f"Ultra-processed items ({', '.join(upf)}).")
    if "processed_meat" in groups:
        add(-10, "Processed meat. Guidelines advise limiting it.")
    elif "red_meat" in groups:
        add(-5, "Red meat. Keep it occasional and choose fish, poultry or legumes more often.")
    if "refined_grain" in groups and "whole_grain" not in groups:
        add(-5, "Refined grains only. Swapping in whole grains adds fibre.")
    if free_sugar > 25:
        add(-10, f"About {free_sugar:.0f} g of sugar from non-fruit sources, which is high for one meal.")
    elif free_sugar > 15:
        add(-5, f"About {free_sugar:.0f} g of sugar from non-fruit sources.")
    if kcal > 0:
        sat_pct = 9 * sat / kcal * 100
        if sat_pct > 15:
            add(-12, f"Saturated fat is about {sat_pct:.0f}% of energy (aim for under 10%).")
        elif sat_pct > 10:
            add(-6, f"Saturated fat is about {sat_pct:.0f}% of energy (aim for under 10%).")
    if sodium > 1000:
        add(-5, f"About {sodium:.0f} mg of sodium, which is high for one meal.")
    if kcal > 1000:
        add(-8, f"About {kcal:.0f} kcal, a large portion. Calorie reduction is central to MASLD care.")

    veg = grams_in("vegetable")
    if veg >= 150:
        add(8, f"Generous vegetables (about {veg:.0f} g).")
    elif veg >= 75:
        add(4, f"Some vegetables (about {veg:.0f} g). Aim for half the plate.")
    if "legume" in groups:
        add(5, "Legumes are a good source of fibre and plant protein.")
    if "whole_grain" in groups:
        add(5, "Whole grains.")
    if "fish_seafood" in groups:
        add(5, "Fish or seafood, part of the Mediterranean pattern.")
    if "nuts_seeds" in groups:
        add(3, "Nuts or seeds.")
    if any(i.food_group == "added_fat_oil" and "olive" in i.name.lower() for i in items):
        add(3, "Olive oil as the added fat.")
    if fiber >= 8:
        add(5, f"About {fiber:.0f} g of fibre.")

    score = max(0, min(100, BASE + sum(a.points for a in adj)))
    verdict = "Excellent" if score >= 80 else "Good" if score >= 65 else "Fair" if score >= 50 else "Poor"
    return DietScore(score=score, verdict=verdict, adjustments=adj)
