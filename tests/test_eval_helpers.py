from liverbuddy.evals.run import _facts_ok, _n5k_dishes, _sentences, _typo


def test_facts_ok_requires_every_group_any_alternative():
    assert _facts_ok("Aim for 5% weight loss, and 10% for fibrosis.", [["5%", "3%"], ["10%"]])
    assert not _facts_ok("Aim for 5% weight loss.", [["5%"], ["10%"]])
    assert _facts_ok("FIBROSCAN is useful", [["fibroscan"]])  # case-insensitive


def test_n5k_parser_reads_ingredient_triplets(tmp_path):
    line = ("dish_1,300.0,193.0,12.3,28.2,18.6,"
            "ingr_1,white rice,100.0,130.0,0.3,28.0,2.7,"
            "ingr_2,soy sauce,10.0,5.3,0.0,0.5,0.8")
    p = tmp_path / "m.csv"
    p.write_text(line + "\n")
    [d] = _n5k_dishes(p, 5)
    assert d["kcal"] == 300.0
    assert [i["name"] for i in d["ingredients"]] == ["white rice", "soy sauce"]
    assert d["ingredients"][0]["grams"] == 100.0 and d["ingredients"][1]["kcal"] == 5.3


def test_sentence_split_ignores_short_fragments():
    s = _sentences("Statins are safe in MASLD [1]. Yes. Weight loss of 10% improves fibrosis [2].")
    assert len(s) == 2


def test_typo_swaps_adjacent_letters_deterministically():
    import random

    t = _typo("atorvastatin", random.Random(1))
    assert sorted(t) == sorted("atorvastatin") and t != "atorvastatin"
