"""Deterministic safety layer that runs before and after every LLM call.

Red-flag symptoms and medication-change requests are handled by rules, not by the model, so the
behaviour is predictable, testable, and cannot be talked out of by prompt injection.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel

Action = Literal["allow", "emergency", "urgent", "crisis", "refuse_dosing"]

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
    (r"(vomit\w*|throw\w* up|puk\w*)\W+(\w+\W+){0,3}blood|blood\W+(\w+\W+){0,3}(vomit|throw)", "vomiting blood"),
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
    (r"\bdark (urine|pee)\b|\bpale (stool|poo)\b", "dark urine or pale stool"),
    (r"\b(fever|temperature)\b.*\b(liver|cirrhosis)\b", "fever with liver disease"),
]
CRISIS = [
    (r"\b(kill myself|suicid\w*|end my life|want to die|self[- ]harm|hurt myself)\b", "self-harm"),
]
DOSING = [
    r"\bhow (much|many)\b.{0,40}\b(should|can|do) i (take|use|have)\b",
    r"\b(can|should) i\b.{0,20}\b(stop|quit|skip|discontinue|come off)\b.{0,30}\b(taking|my|the)\b",
    r"\b(increase|decrease|double|halve|reduce|change|adjust)\b.{0,15}\b(my )?(dose|dosage)\b",
    r"\bwhat (dose|dosage)\b.{0,30}\b(should|can) i\b",
    r"\b(start|stop) taking\b",
]
NEGATION = re.compile(r"\b(no|not|don'?t|doesn'?t|didn'?t|never|without|denies|haven'?t|isn'?t)\b")
CLAUSE_BREAK = re.compile(r"[.;!?]|\bbut\b|\bhowever\b|\band now\b")

# Output-side check: personal dosing instructions the model should never produce.
OUTPUT_DOSING = re.compile(
    r"\b(you should|i recommend|take|increase to|reduce to)\b[^.]{0,40}\b\d+(\.\d+)?\s?(mg|mcg|g|iu|tablets?|pills?)\b"
    r"|\b(stop|discontinue) (taking )?(your|the) (medicine|medication|tablets?)\b", re.I)


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
            if not NEGATION.search(clause):
                found.append(label)
                break
    return found


def check_input(text: str) -> GuardrailResult:
    t = " ".join(text.lower().split())
    if hits := _hits(t, CRISIS):
        return GuardrailResult(action="crisis", message=CRISIS_MSG, matched=hits)
    if hits := _hits(t, EMERGENCY):
        return GuardrailResult(action="emergency", message=EMERGENCY_MSG, matched=hits)
    if hits := _hits(t, URGENT):
        return GuardrailResult(action="urgent", message=URGENT_MSG, matched=hits)
    if any(re.search(p, t) for p in DOSING):
        return GuardrailResult(action="refuse_dosing", message=DOSING_MSG, matched=["medication change request"])
    return GuardrailResult(action="allow")


def check_output(text: str) -> tuple[str, bool]:
    """Strip sentences containing personal dosing instructions. Returns (text, was_modified)."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    kept = [s for s in sentences if not OUTPUT_DOSING.search(s)]
    if len(kept) == len(sentences):
        return text, False
    note = "(Dosing details were removed. Please confirm any medication change with your prescriber.)"
    return " ".join(kept + [note]).strip(), True
