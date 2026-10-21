from liverbuddy.scoring.diet import DietItem, score_meal


def item(name, group, grams=100, **kw):
    return DietItem(name=name, grams=grams, food_group=group, **kw)


def test_mediterranean_meal_scores_excellent():
    meal = [item("grilled salmon", "fish_seafood", 150, cooking="grilled_baked_roasted", kcal=310, sat_fat_g=2.5),
            item("steamed broccoli", "vegetable", 160, cooking="boiled_steamed", kcal=55, fiber_g=5),
            item("lentils", "legume", 120, kcal=140, fiber_g=9),
            item("olive oil", "added_fat_oil", 10, kcal=88, sat_fat_g=1.4)]
    s = score_meal(meal)
    assert s.verdict == "Excellent"
    assert s.score >= 90


def test_fast_food_meal_scores_poor_with_reasons():
    meal = [item("cheeseburger", "red_meat", 220, cooking="fried", ultra_processed=True, kcal=600, sat_fat_g=14,
                 sodium_mg=1100),
            item("french fries", "refined_grain", 150, cooking="deep_fried", kcal=470, sat_fat_g=3),
            item("cola", "sugary_drink", 500, kcal=210, sugars_g=53)]
    s = score_meal(meal)
    assert s.verdict == "Poor"
    reasons = " ".join(a.reason for a in s.adjustments)
    for word in ("Sugar-sweetened", "Fried", "Ultra-processed", "sodium"):
        assert word in reasons


def test_alcohol_is_penalised():
    s = score_meal([item("beer", "alcohol", 330, kcal=140)])
    assert any(a.points == -25 for a in s.adjustments)


def test_fruit_sugar_is_not_counted_as_free_sugar():
    s = score_meal([item("apple", "fruit", 200, kcal=104, sugars_g=20, fiber_g=5)])
    assert not any("sugar" in a.reason.lower() for a in s.adjustments)


def test_score_is_clamped():
    meal = [item(f"x{i}", "processed_meat", cooking="deep_fried", ultra_processed=True, kcal=500, sat_fat_g=20,
                 sodium_mg=900) for i in range(4)] + [item("beer", "alcohol"), item("soda", "sugary_drink",
                                                                                     sugars_g=60)]
    assert score_meal(meal).score == 0
