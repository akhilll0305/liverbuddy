"""Validated, deterministic non-invasive liver scores.

Every number shown to a user comes from here (or from the trained model), never from an LLM.
Formulas and cut-offs follow the cited primary sources and the EASL-EASD-EASO 2024 MASLD guideline.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, Field

Sex = Literal["male", "female"]
Category = Literal["low", "indeterminate", "high", "rule_out", "rule_in", "unknown"]


class PatientMeasures(BaseModel):
    """Routine clinical measurements. Units match what most labs report."""

    age: float | None = Field(None, ge=0, le=120, description="years")
    sex: Sex | None = None
    height_cm: float | None = Field(None, gt=50, lt=260)
    weight_kg: float | None = Field(None, gt=20, lt=400)
    waist_cm: float | None = Field(None, gt=30, lt=250)
    asian_ethnicity: bool = False

    alt: float | None = Field(None, gt=0, description="ALT / SGPT, U/L")
    ast: float | None = Field(None, gt=0, description="AST / SGOT, U/L")
    ggt: float | None = Field(None, gt=0, description="GGT, U/L")
    platelets: float | None = Field(None, gt=0, description="10^9/L (same as 10^3/uL)")
    albumin: float | None = Field(None, gt=0, description="g/dL")
    triglycerides: float | None = Field(None, gt=0, description="mg/dL")
    hdl: float | None = Field(None, gt=0, description="mg/dL")
    fasting_glucose: float | None = Field(None, gt=0, description="mg/dL")
    hba1c: float | None = Field(None, gt=0, description="%")
    systolic_bp: float | None = Field(None, gt=0)
    diastolic_bp: float | None = Field(None, gt=0)

    type2_diabetes: bool = False
    on_antihypertensives: bool = False
    on_lipid_lowering: bool = False
    alcohol_g_per_week: float | None = Field(None, ge=0)

    @property
    def bmi(self) -> float | None:
        if self.height_cm and self.weight_kg:
            return self.weight_kg / (self.height_cm / 100) ** 2
        return None


class ScoreResult(BaseModel):
    name: str
    value: float | None
    category: Category
    interpretation: str
    missing_inputs: list[str] = []
    reference: str


def _missing(m: PatientMeasures, *fields: str) -> list[str]:
    return [f for f in fields if (m.bmi if f == "bmi" else getattr(m, f)) is None]


def fib4(m: PatientMeasures) -> ScoreResult:
    """FIB-4 = age x AST / (platelets x sqrt(ALT)). Sterling et al., Hepatology 2006."""
    ref = "Sterling RK et al. Hepatology 2006;43:1317-25; cut-offs per EASL-EASD-EASO 2024 and AASLD 2023"
    missing = _missing(m, "age", "ast", "alt", "platelets")
    if missing:
        return ScoreResult(name="FIB-4", value=None, category="unknown", interpretation="Insufficient data",
                           missing_inputs=missing, reference=ref)
    value = (m.age * m.ast) / (m.platelets * math.sqrt(m.alt))
    low_cut = 2.0 if m.age >= 65 else 1.3  # age-adjusted lower cut-off (McPherson 2017)
    if value < low_cut:
        cat, txt = "low", f"Below {low_cut}: advanced fibrosis unlikely; reassess in 1-3 years."
    elif value > 2.67:
        cat, txt = "high", "Above 2.67: advanced fibrosis likely; refer to hepatology."
    else:
        cat, txt = "indeterminate", (f"Between {low_cut} and 2.67: needs a second-line test "
                                     "such as vibration-controlled transient elastography (VCTE/FibroScan).")
    if m.age < 35:
        txt += " FIB-4 is less reliable under age 35."
    return ScoreResult(name="FIB-4", value=round(value, 2), category=cat, interpretation=txt, reference=ref)


def nafld_fibrosis_score(m: PatientMeasures) -> ScoreResult:
    """NAFLD Fibrosis Score. Angulo et al., Hepatology 2007."""
    ref = "Angulo P et al. Hepatology 2007;45:846-54"
    missing = _missing(m, "age", "bmi", "ast", "alt", "platelets", "albumin")
    if missing:
        return ScoreResult(name="NAFLD Fibrosis Score", value=None, category="unknown",
                           interpretation="Insufficient data", missing_inputs=missing, reference=ref)
    ifg = m.type2_diabetes or (m.fasting_glucose is not None and m.fasting_glucose >= 110)
    value = (-1.675 + 0.037 * m.age + 0.094 * m.bmi + 1.13 * int(ifg) + 0.99 * (m.ast / m.alt)
             - 0.013 * m.platelets - 0.66 * m.albumin)
    low_cut = 0.12 if m.age >= 65 else -1.455
    if value < low_cut:
        cat, txt = "low", f"Below {low_cut}: advanced fibrosis unlikely."
    elif value > 0.676:
        cat, txt = "high", "Above 0.676: advanced fibrosis likely."
    else:
        cat, txt = "indeterminate", "Indeterminate: second-line test recommended."
    return ScoreResult(name="NAFLD Fibrosis Score", value=round(value, 3), category=cat,
                       interpretation=txt, reference=ref)


def fatty_liver_index(m: PatientMeasures) -> ScoreResult:
    """Fatty Liver Index. Bedogni et al., BMC Gastroenterology 2006."""
    ref = "Bedogni G et al. BMC Gastroenterol 2006;6:33"
    missing = _missing(m, "triglycerides", "bmi", "ggt", "waist_cm")
    if missing:
        return ScoreResult(name="Fatty Liver Index", value=None, category="unknown",
                           interpretation="Insufficient data", missing_inputs=missing, reference=ref)
    y = (0.953 * math.log(m.triglycerides) + 0.139 * m.bmi + 0.718 * math.log(m.ggt)
         + 0.053 * m.waist_cm - 15.745)
    value = math.exp(y) / (1 + math.exp(y)) * 100
    if value < 30:
        cat, txt = "rule_out", "Below 30: hepatic steatosis unlikely."
    elif value >= 60:
        cat, txt = "rule_in", "60 or above: hepatic steatosis likely."
    else:
        cat, txt = "indeterminate", "30-59: indeterminate for steatosis."
    return ScoreResult(name="Fatty Liver Index", value=round(value, 1), category=cat,
                       interpretation=txt, reference=ref)


def hepatic_steatosis_index(m: PatientMeasures) -> ScoreResult:
    """HSI = 8 x ALT/AST + BMI (+2 female, +2 diabetes). Lee et al., Dig Liver Dis 2010."""
    ref = "Lee JH et al. Dig Liver Dis 2010;42:503-8"
    missing = _missing(m, "alt", "ast", "bmi", "sex")
    if missing:
        return ScoreResult(name="Hepatic Steatosis Index", value=None, category="unknown",
                           interpretation="Insufficient data", missing_inputs=missing, reference=ref)
    value = 8 * m.alt / m.ast + m.bmi + 2 * (m.sex == "female") + 2 * m.type2_diabetes
    if value < 30:
        cat, txt = "rule_out", "Below 30: hepatic steatosis unlikely."
    elif value > 36:
        cat, txt = "rule_in", "Above 36: hepatic steatosis likely."
    else:
        cat, txt = "indeterminate", "30-36: indeterminate for steatosis."
    return ScoreResult(name="Hepatic Steatosis Index", value=round(value, 1), category=cat,
                       interpretation=txt, reference=ref)


def apri(m: PatientMeasures, ast_uln: float = 40.0) -> ScoreResult:
    """AST to Platelet Ratio Index. Wai et al., Hepatology 2003."""
    ref = "Wai CT et al. Hepatology 2003;38:518-26"
    missing = _missing(m, "ast", "platelets")
    if missing:
        return ScoreResult(name="APRI", value=None, category="unknown", interpretation="Insufficient data",
                           missing_inputs=missing, reference=ref)
    value = (m.ast / ast_uln) / m.platelets * 100
    if value < 0.5:
        cat, txt = "low", "Below 0.5: significant fibrosis unlikely."
    elif value > 1.5:
        cat, txt = "high", "Above 1.5: significant fibrosis likely."
    else:
        cat, txt = "indeterminate", "0.5-1.5: indeterminate."
    return ScoreResult(name="APRI", value=round(value, 3), category=cat, interpretation=txt, reference=ref)


class CardiometabolicCriteria(BaseModel):
    """The five adult cardiometabolic criteria from the 2023 multi-society MASLD nomenclature."""

    overweight_or_central_obesity: bool | None
    dysglycaemia: bool | None
    hypertension: bool | None
    hypertriglyceridaemia: bool | None
    low_hdl: bool | None
    met_count: int
    alcohol_category: Literal["MASLD-range", "MetALD-range", "ALD-range", "unknown"]
    summary: str
    reference: str = "Rinella ME et al. J Hepatol 2023;79:1542-56 (multi-society Delphi consensus)"


def cardiometabolic_criteria(m: PatientMeasures) -> CardiometabolicCriteria:
    def any_known(*vals: bool | None) -> bool | None:
        # met if any evidence says so; not met if we measured something and nothing triggered
        if any(v is True for v in vals):
            return True
        return False if any(v is False for v in vals) else None

    bmi_cut = 23 if m.asian_ethnicity else 25
    waist_cut = {"male": 90 if m.asian_ethnicity else 94, "female": 80}.get(m.sex or "")
    c1 = any_known(None if m.bmi is None else m.bmi >= bmi_cut,
                   None if (m.waist_cm is None or waist_cut is None) else m.waist_cm > waist_cut)
    c2 = any_known(m.type2_diabetes or None,
                   None if m.fasting_glucose is None else m.fasting_glucose >= 100,
                   None if m.hba1c is None else m.hba1c >= 5.7)
    c3 = any_known(m.on_antihypertensives or None,
                   None if m.systolic_bp is None else m.systolic_bp >= 130,
                   None if m.diastolic_bp is None else m.diastolic_bp >= 85)
    c4 = any_known(m.on_lipid_lowering or None,
                   None if m.triglycerides is None else m.triglycerides >= 150)
    hdl_cut = {"male": 40, "female": 50}.get(m.sex or "")
    c5 = any_known(m.on_lipid_lowering or None,
                   None if (m.hdl is None or hdl_cut is None) else m.hdl <= hdl_cut)
    met = sum(c is True for c in (c1, c2, c3, c4, c5))

    if m.alcohol_g_per_week is None or m.sex is None:
        alc = "unknown"
    else:
        lo, hi = (140, 350) if m.sex == "female" else (210, 420)
        g = m.alcohol_g_per_week
        alc = "MASLD-range" if g < lo else "MetALD-range" if g <= hi else "ALD-range"

    if met == 0:
        summary = ("No cardiometabolic criterion met with the data provided. If steatosis is present, "
                   "other causes should be considered.")
    else:
        summary = (f"{met} of 5 cardiometabolic criteria met. If steatosis is confirmed and alcohol intake "
                   f"is in the MASLD range, this fits the MASLD definition.")
    return CardiometabolicCriteria(overweight_or_central_obesity=c1, dysglycaemia=c2, hypertension=c3,
                                   hypertriglyceridaemia=c4, low_hdl=c5, met_count=met,
                                   alcohol_category=alc, summary=summary)


class ScorePanel(BaseModel):
    bmi: float | None
    scores: list[ScoreResult]
    criteria: CardiometabolicCriteria
    next_step: str


def compute_panel(m: PatientMeasures) -> ScorePanel:
    scores = [fib4(m), nafld_fibrosis_score(m), fatty_liver_index(m), hepatic_steatosis_index(m), apri(m)]
    f = scores[0]
    # Stepwise pathway from EASL-EASD-EASO 2024: FIB-4 first, then elastography if not low.
    if f.category == "low":
        step = "FIB-4 is low: manage in primary care, focus on lifestyle, repeat non-invasive testing in 1-3 years."
    elif f.category in ("indeterminate", "high"):
        step = ("FIB-4 is not low: a second-line test (VCTE/FibroScan or ELF) is recommended. "
                "Discuss referral with your doctor.")
    else:
        step = f"FIB-4 needs: {', '.join(f.missing_inputs)}. Ask your doctor for a liver panel and platelet count."
    return ScorePanel(bmi=round(m.bmi, 1) if m.bmi else None, scores=scores,
                      criteria=cardiometabolic_criteria(m), next_step=step)
