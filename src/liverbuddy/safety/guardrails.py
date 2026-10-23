"""Deterministic safety layer that runs before and after every LLM call.

Red-flag symptoms and medication-change requests are handled by rules, not by the model, so the
behaviour is predictable, testable, and cannot be talked out of by prompt injection.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel

Action = Literal["allow", "caution_medication", "emergency", "urgent", "crisis", "refuse_dosing"]

EMERGENCY_MSG = (
    "This could be a medical emergency. Please call your local emergency number now (112 in India and "
    "Europe, 911 in the US) or go to the nearest emergency department. Don't wait for an app.")
URGENT_MSG = (
    "This symptom needs a doctor's assessment today. Please contact your doctor or visit a clinic or "
    "emergency department as soon as possible. If it gets worse, call your local emergency number.")
CRISIS_MSG = (
    "I'm really sorry you're feeling this way. You deserve support right now. In India you can call "
    "Tele-MANAS on 14416 (24/7, free). Elsewhere, call your local emergency number or a crisis line. If you "
    "are in immediate danger, call 112 (or 911 in the US).")
DOSING_MSG = (
    "I can't advise on starting, stopping or changing the dose of a medicine. That depends on your full "
    "medical history and needs your prescriber or pharmacist. I can tell you what NIH LiverTox and the "
    "guidelines say about a medicine's liver safety, which you can take to that conversation.")

# (pattern, label). Patterns are matched on lowercase text.
EMERGENCY = [
    (r"(vomit\w*|throw\w* up|threw up|puk\w*)\W+(\w+\W+){0,6}(blood|coffee[- ]grounds?)"
     r"|blood\W+(\w+\W+){0,3}(vomit|throw)|coffee[- ]grounds?\W+(\w+\W+){0,3}(vomit|throw|threw)",
     "vomiting blood"),
    (r"(black|tarry|maroon)\W+(\w+\W+){0,2}(stools?|poo|poop)|(stools?|poo|poop)\W+(\w+\W+){0,3}(black|tarry|maroon)"
     r"|blood\W+(in|with)\W+(my\W+)?(stools?|poo)",
     "black or bloody stool"),
    (r"\b(confus\w*|disorient\w*|can'?t think straight|very drowsy|hard to wake|unresponsive)\b",
     "confusion or drowsiness"),
    (r"\b(overdos\w*|took too many|swallowed (a lot|too many|the whole))\b", "possible overdose"),
    (r"\bchest pain\b|\bcan'?t breathe\b|\bshort(ness)? of breath\b", "chest pain or breathlessness"),
    (r"\b(faint\w*|pass(ed)? out|collapsed?)\b", "fainting or collapse"),
    (r"\bsevere\W+(\w+\W+){0,2}(abdominal|stomach|belly|tummy) pain\b", "severe abdominal pain"),
]
URGENT = [
    (r"\b(yellow\w*)\W+(\w+\W+){0,2}(eyes?|skin)\b|\b(eyes?|skin)\W+(\w+\W+){0,3}yellow|\bjaundice\w*\b",
     "yellowing of eyes or skin"),
    (r"\b(swollen|swelling|bloated|distended)\W+(\w+\W+){0,2}(belly|abdomen|stomach|tummy|legs?|ankles?)\b"
     r"|\b(belly|abdomen|stomach|tummy|legs?|ankles?)\W+(\w+\W+){0,2}(swollen|swelling|distended)\b",
     "abdominal or leg swelling"),
    (r"\bdark (urine|pee)\b|\bpale (stool|poo)\b|\b(urine|pee)\W+(\w+\W+){0,3}(dark|brown|cola|tea[- ]colou?red)\b",
     "dark urine or pale stool"),
    (r"\b(fever|temperature)\b.*\b(liver|cirrhosis)\b|\bcirrhosis\b.*\b(fever|temperature)\b",
     "fever with liver disease"),
]
CRISIS = [
    (r"\b(kill(ing)? myself|suicid\w*|end(ing)? my life|want to die|self[- ]harm\w*|hurt(ing)? myself"
     r"|(don'?t|do not) want to (live|be alive|wake up)|better off dead|no reason to live)\b",
     "self-harm"),
]
# "How much X can I have" asks for a dose only when X is a medicine, not a food, drink or activity.
AMOUNT = [
    r"\bhow (much|many)\b.{0,40}\b(should|can|do) i (take|use|have)\b",
    r"\bhow (much|many)\b.{0,30}\bto (take|inject|use)\b",
]
DIET = re.compile(
    r"\b(alcohol|drinks?|beer|wine|spirits?|coffee|tea|water|juice|soda|cola|sugar|salt|sodium|fibre|fiber|"
    r"protein|fat|carbs?|carbohydrates?|calories|kcal|food|meals?|diet|eggs?|fruits?|vegetables?|rice|roti|"
    r"bread|nuts|oil|milk|meat|fish|sweets?|steps|exercise|sleep|weight)\b")
MEDICINE = re.compile(
    r"\b(mg|mcg|iu|dose|dosage|tablets?|pills?|capsules?|medicines?|medications?|drugs?|supplements?|"
    r"vitamins?|insulin|inject\w*|syrup|fish oil|omega[- ]?3)\b")
# Dose changes: always declined.
DOSING = [
    r"\b(increase|decrease|double|halve|reduce|change|adjust)\b.{0,15}\b(my )?(dose|dosage)\b",
    r"\bwhat (dose|dosage)\b.{0,30}\b(should|can) i\b",
]
# Start/stop questions: answered from evidence, with a fixed "talk to your prescriber" notice.
MED_CHANGE = [
    r"\b(can|should) i\b.{0,20}\b(stop|quit|skip|discontinue|come off|start)\b.{0,30}\b(taking|my|the|a|an)\b",
    r"\b(start|stop) taking\b",
]
MED_CHANGE_NOTICE = ("Please don't start or stop a prescribed medicine without talking to your prescriber. "
                     "Here is what the evidence says, to help that conversation:")
NEGATION = re.compile(r"\b(no|not|don'?t|doesn'?t|didn'?t|never|without|denies|haven'?t|isn'?t)\b")
# a comma followed by a new subject starts a new clause: "not sure if it's serious, I'm vomiting blood"
CLAUSE_BREAK = re.compile(r"[.;!?]|\bbut\b|\bhowever\b|\band now\b"
                          r"|,\s*(?=(?:i|i'm|im|my|he|she|he's|she's|his|her|it|it's|there|they|now)\b)")
# uncertainty, not denial: "not sure", "no idea", "don't know" never negate a symptom
HEDGE = re.compile(r"\b(not (sure|certain)|no idea|no clue|don'?t (know|understand)|not knowing)\b")

# Output-side check: personal dosing instructions the model should never produce. Grams are also how
# diet advice is given ("keep added sugar under 25 g"), so a gram amount only counts outside diet sentences.
_ADVICE = r"\b(you should|i recommend|take|increase to|reduce to)\b[^.]{0,40}\b\d+(\.\d+)?\s?"
OUTPUT_DOSING = re.compile(
    _ADVICE + r"(mg|mcg|iu|tablets?|pills?)\b"
    r"|\b(stop|discontinue) (taking )?(your|the) (medicine|medication|tablets?)\b", re.I)
OUTPUT_DOSING_GRAMS = re.compile(_ADVICE + r"g\b", re.I)


class GuardrailResult(BaseModel):
    action: Action
    message: str | None = None
    matched: list[str] = []


def _hits(text: str, rules: list[tuple[str, str]]) -> list[str]:
    found = []
    for pattern, label in rules:
        for m in re.finditer(pattern, text):
            # negation applies within the same clause ("no X or Y"), not across "but" or a full stop
            clause = CLAUSE_BREAK.split(text[max(0, m.start() - 60):m.start()])[-1]
            if not NEGATION.search(HEDGE.sub(" ", clause)):
                found.append(label)
                break
    return found


def _is_dose_amount(span: str) -> bool:
    return bool(MEDICINE.search(span)) or not DIET.search(span)


def _gives_dose(sentence: str) -> bool:
    if OUTPUT_DOSING.search(sentence):
        return True
    return bool(OUTPUT_DOSING_GRAMS.search(sentence)) and not DIET.search(sentence.lower())


def check_input(text: str) -> GuardrailResult:
    t = " ".join(text.lower().split())
    if hits := _hits(t, CRISIS):
        return GuardrailResult(action="crisis", message=CRISIS_MSG, matched=hits)
    if hits := _hits(t, EMERGENCY):
        return GuardrailResult(action="emergency", message=EMERGENCY_MSG, matched=hits)
    if hits := _hits(t, URGENT):
        return GuardrailResult(action="urgent", message=URGENT_MSG, matched=hits)
    if any(re.search(p, t) for p in DOSING) or any(_is_dose_amount(m.group()) for p in AMOUNT
                                                   for m in re.finditer(p, t)):
        return GuardrailResult(action="refuse_dosing", message=DOSING_MSG, matched=["dose request"])
    if any(re.search(p, t) for p in MED_CHANGE):
        return GuardrailResult(action="caution_medication", message=MED_CHANGE_NOTICE,
                               matched=["medication start/stop question"])
    return GuardrailResult(action="allow")


def check_output(text: str) -> tuple[str, bool]:
    """Strip sentences containing personal dosing instructions. Returns (text, was_modified)."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    kept = [s for s in sentences if not _gives_dose(s)]
    if len(kept) == len(sentences):
        return text, False
    note = "(Dosing details were removed. Please confirm any medication change with your prescriber.)"
    return " ".join(kept + [note]).strip(), True
