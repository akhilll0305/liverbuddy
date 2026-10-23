"""Extract liver-relevant analytes from lab reports (PDF or text), normalised to the units the scores use.

Rules first (predictable, unit-aware, handles Indian and US report formats); the LLM only fills gaps,
and every LLM value must fall inside a physiologically plausible range.
"""

from __future__ import annotations

import io
import re
from typing import Literal

from pydantic import BaseModel

from liverbuddy.llm import LLM, Message, StructuredOutputError, structured

Analyte = Literal["alt", "ast", "ggt", "platelets", "albumin", "triglycerides", "hdl", "fasting_glucose", "hba1c"]

ALIASES: dict[str, list[str]] = {
    "alt": [r"sgpt", r"\balt\b", r"alanine\s+(amino)?transaminase", r"alanine\s+aminotransferase"],
    "ast": [r"sgot", r"\bast\b", r"aspartate\s+(amino)?transaminase", r"aspartate\s+aminotransferase"],
    "ggt": [r"\bggtp?\b", r"gamma[\s-]*g(lutamyl)?\s*t(ransferase|ranspeptidase)?\b", r"gamma\s*gt\b"],
    "platelets": [r"platelet\s*count", r"\bplatelets?\b", r"\bplt\b"],
    "albumin": [r"\balbumin\b(?!\s*/)(?!.*globulin\s*ratio)"],
    "triglycerides": [r"triglycerides?", r"\btg\b"],
    "hdl": [r"(?<!non)(?<!non[\s-])hdl(\s*-?\s*c(holesterol)?)?\b", r"high\s+density\s+lipoprotein"],
    "fasting_glucose": [r"fasting\s+(blood\s+|plasma\s+)?(sugar|glucose)", r"glucose,?\s*fasting", r"\bfbs\b",
                        r"\bfpg\b"],
    "hba1c": [r"hb\s*a1c", r"glycated\s+ha?emoglobin", r"glycosylated\s+ha?emoglobin", r"\ba1c\b"],
}
PLAUSIBLE = {  # in output units
    "alt": (3, 3000), "ast": (3, 3000), "ggt": (3, 3000), "platelets": (5, 1500), "albumin": (1, 7),
    "triglycerides": (20, 5000), "hdl": (5, 200), "fasting_glucose": (30, 700), "hba1c": (3, 20),
}
UNITS_OUT = {"alt": "U/L", "ast": "U/L", "ggt": "U/L", "platelets": "10^9/L", "albumin": "g/dL",
             "triglycerides": "mg/dL", "hdl": "mg/dL", "fasting_glucose": "mg/dL", "hba1c": "%"}

_NUM = r"(\d{1,3}(?:,\d{2,3})+|\d+(?:\.\d+)?)"  # also Indian lakh grouping: 2,45,000
_RATIO = re.compile(r"\bratio\b|\b(a|tg|chol\w*|ldl|hdl|sgot|sgpt|ast|alt)\s*/\s*(g|hdl|ldl|sgpt|alt)\b")


class LabValue(BaseModel):
    analyte: Analyte
    value: float
    unit: str
    raw: str
    method: Literal["rule", "llm"]


class LabExtraction(BaseModel):
    values: dict[str, LabValue]
    missing: list[str]
    warnings: list[str] = []


def _normalise(analyte: str, value: float, unit_text: str) -> tuple[float, str | None]:
    u = unit_text.lower().replace("µ", "u").replace("μ", "u").replace(" ", "")
    if analyte == "platelets":
        if "lakh" in u or "lac" in u:
            return value * 100, None  # 2.5 lakh/cumm = 250 x10^9/L
        if value > 1500:  # absolute count per uL / cumm, e.g. 250000
            return value / 1000, None
        return value, None
    if analyte == "albumin" and ("g/l" in u and "g/dl" not in u or value > 10):
        return value / 10, None
    if analyte == "triglycerides" and ("mmol" in u or value < 15):
        return value * 88.57, "converted from mmol/L"
    if analyte == "hdl" and ("mmol" in u or value < 4):
        return value * 38.67, "converted from mmol/L"
    if analyte == "fasting_glucose" and ("mmol" in u or value < 25):
        return value * 18.016, "converted from mmol/L"
    if analyte == "hba1c" and ("mmol/mol" in u or value > 20):
        return value / 10.929 + 2.15, "converted from mmol/mol (IFCC)"
    return value, None


def extract_rules(text: str) -> tuple[dict[str, LabValue], list[str]]:
    found: dict[str, LabValue] = {}
    warnings: list[str] = []
    for line in text.splitlines():
        low = line.lower()
        if _RATIO.search(low):  # A/G, TG/HDL, SGOT/SGPT ratios are not the analytes themselves
            continue
        for analyte, pats in ALIASES.items():
            if analyte in found:
                continue
            m = next((re.search(p, low) for p in pats if re.search(p, low)), None)
            if not m:
                continue
            rest = line[m.end():]
            num = re.search(_NUM, rest)
            if not num:
                continue
            value = float(num.group(1).replace(",", ""))
            unit_text = rest[num.end():num.end() + 20]
            value, note = _normalise(analyte, value, unit_text)
            lo, hi = PLAUSIBLE[analyte]
            if not lo <= value <= hi:
                warnings.append(f"Ignored implausible {analyte} value from: {line.strip()[:80]}")
                continue
            if note:
                warnings.append(f"{analyte}: {note}")
            found[analyte] = LabValue(analyte=analyte, value=round(value, 2), unit=UNITS_OUT[analyte],
                                      raw=line.strip()[:120], method="rule")
    return found, warnings


class _LLMLabs(BaseModel):
    alt: float | None = None
    ast: float | None = None
    ggt: float | None = None
    platelets: float | None = None
    albumin: float | None = None
    triglycerides: float | None = None
    hdl: float | None = None
    fasting_glucose: float | None = None
    hba1c: float | None = None


LLM_PROMPT = """Extract these results from the lab report, converted to these units, or null if absent:
alt U/L, ast U/L, ggt U/L, platelets 10^9/L (2.5 lakh/cumm = 250; 250000/uL = 250), albumin g/dL, \
triglycerides mg/dL, hdl mg/dL, fasting_glucose mg/dL, hba1c %.
Use the patient's result, never the reference range. Report:
"""


def pdf_to_text(data: bytes) -> str:
    from pypdf import PdfReader

    return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages)


def extract_labs(text: str, llm: LLM | None = None) -> LabExtraction:
    found, warnings = extract_rules(text)
    missing = [a for a in ALIASES if a not in found]
    if llm is not None and missing:
        try:
            out = structured(llm, [Message("user", LLM_PROMPT + text[:12000])], _LLMLabs, span="lab_extract")
            for a in list(missing):
                v = getattr(out, a)
                lo, hi = PLAUSIBLE[a]
                if v is not None and lo <= v <= hi:
                    found[a] = LabValue(analyte=a, value=round(v, 2), unit=UNITS_OUT[a], raw="(LLM extraction)",
                                        method="llm")
                    missing.remove(a)
        except StructuredOutputError:
            warnings.append("LLM fallback extraction failed; only rule-based values are shown.")
    return LabExtraction(values=found, missing=missing, warnings=warnings)
