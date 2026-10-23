import pytest

from liverbuddy.safety.guardrails import check_input, check_output


@pytest.mark.parametrize("text,action", [
    ("I vomited blood this morning", "emergency"),
    ("my stool has been black and tarry for two days", "emergency"),
    ("my father seems confused and very drowsy, he has cirrhosis", "emergency"),
    ("I think I took too many paracetamol tablets", "emergency"),
    ("my eyes have turned yellow", "urgent"),
    ("my belly is swollen and tight", "urgent"),
    ("I want to end my life", "crisis"),
    ("how much metformin should I take?", "refuse_dosing"),
    ("can I stop taking my statin?", "caution_medication"),
    ("should I double my dose of vitamin E", "refuse_dosing"),
    ("is atorvastatin safe for my liver?", "allow"),
    ("what foods should I avoid with fatty liver?", "allow"),
    ("my FIB-4 is 1.8, what does that mean?", "allow"),
])
def test_input_routing(text, action):
    assert check_input(text).action == action


@pytest.mark.parametrize("text", [
    "I don't have yellow eyes or dark urine",
    "no black stools, no vomiting blood",
    "I have never fainted",
])
def test_negated_symptoms_are_not_flagged(text):
    assert check_input(text).action == "allow"


def test_crisis_takes_priority_over_other_flags():
    r = check_input("I vomited blood and I want to die")
    assert r.action == "crisis"


def test_output_dosing_sentences_are_removed():
    text = "Statins are generally safe [1]. You should take 40 mg of atorvastatin daily. Discuss with your doctor."
    cleaned, modified = check_output(text)
    assert modified
    assert "40 mg" not in cleaned
    assert "Statins are generally safe [1]." in cleaned


def test_output_without_dosing_is_untouched():
    text = "Weight loss of 7-10% improves liver fat [2]."
    assert check_output(text) == (text, False)


def test_negation_does_not_cross_clause_boundaries():
    assert check_input("I don't have jaundice but my stool is black and tarry").action == "emergency"


@pytest.mark.parametrize("text,action", [
    ("Not sure if this is serious, I'm vomiting blood", "emergency"),
    ("I don't know what's happening, I have chest pain", "emergency"),
    ("No idea why, my eyes have turned yellow", "urgent"),
    ("I'm not sure why but I feel confused", "emergency"),
])
def test_hedges_and_comma_clauses_do_not_negate_red_flags(text, action):
    assert check_input(text).action == action


def test_negation_still_applies_within_its_own_clause():
    assert check_input("I don't have chest pain, it's more of an ache in my side").action == "allow"
