"""Inference for the NHANES-trained models, with exact per-patient TreeSHAP explanations."""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
import xgboost as xgb
from pydantic import BaseModel

from liverbuddy.ml.cohort import BASIC_FEATURES, FULL_FEATURES
from liverbuddy.scoring.clinical import PatientMeasures

LAB_FEATURES = [f for f in FULL_FEATURES if f not in BASIC_FEATURES]
LABELS = {
    "age": "Age", "female": "Sex (female)", "bmi": "BMI", "waist_cm": "Waist circumference",
    "type2_diabetes": "Type 2 diabetes", "hypertension": "High blood pressure", "alt": "ALT",
    "ast": "AST", "ggt": "GGT", "triglycerides": "Triglycerides", "glucose": "Glucose",
    "albumin": "Albumin", "platelets": "Platelets", "hba1c": "HbA1c", "hdl": "HDL cholesterol",
}
TASK_TEXT = {
    "steatosis": "liver fat (CAP >= 274 dB/m on FibroScan)",
    "fibrosis": "raised liver stiffness (LSM >= 8 kPa on FibroScan)",
}


class Driver(BaseModel):
    feature: str
    label: str
    value: float | None
    contribution: float  # log-odds; positive raises risk


class RiskPrediction(BaseModel):
    task: Literal["steatosis", "fibrosis"]
    probability: float
    band: Literal["low", "moderate", "high"]
    model_variant: Literal["full", "basic"]
    outcome: str
    drivers: list[Driver]
    test_auroc: float
    note: str


def measures_to_features(m: PatientMeasures) -> dict[str, float]:
    nan = float("nan")

    def v(x):
        return nan if x is None else float(x)

    return {
        "age": v(m.age), "female": nan if m.sex is None else float(m.sex == "female"), "bmi": v(m.bmi),
        "waist_cm": v(m.waist_cm), "type2_diabetes": float(m.type2_diabetes),
        "hypertension": float(m.on_antihypertensives), "alt": v(m.alt), "ast": v(m.ast), "ggt": v(m.ggt),
        "triglycerides": v(m.triglycerides), "glucose": v(m.fasting_glucose), "albumin": v(m.albumin),
        "platelets": v(m.platelets), "hba1c": v(m.hba1c), "hdl": v(m.hdl),
    }


class RiskModels:
    def __init__(self, model_dir: Path):
        self.models: dict[tuple[str, str], tuple[xgb.XGBClassifier, dict]] = {}
        for meta_path in model_dir.glob("*.meta.json"):
            meta = json.loads(meta_path.read_text())
            model = xgb.XGBClassifier()
            model.load_model(meta_path.with_name(meta_path.name.replace(".meta.json", ".json")))
            self.models[(meta["task"], meta["variant"])] = (model, meta)
        if not self.models:
            raise FileNotFoundError(f"No trained models in {model_dir}. Run `liverbuddy train`.")

    def predict(self, m: PatientMeasures, task: Literal["steatosis", "fibrosis"]) -> RiskPrediction:
        feats = measures_to_features(m)
        has_labs = any(not math.isnan(feats[f]) for f in LAB_FEATURES)
        variant = "full" if has_labs else "basic"
        model, meta = self.models[(task, variant)]
        cols = meta["features"]
        X = pd.DataFrame([[feats[c] for c in cols]], columns=cols)
        prob = float(model.predict_proba(X)[0, 1])
        contribs = model.get_booster().predict(xgb.DMatrix(X), pred_contribs=True)[0][:-1]
        order = np.argsort(-np.abs(contribs))
        drivers = [Driver(feature=cols[i], label=LABELS[cols[i]],
                          value=None if math.isnan(feats[cols[i]]) else round(feats[cols[i]], 2),
                          contribution=round(float(contribs[i]), 3))
                   for i in order[:6] if abs(contribs[i]) > 1e-3]
        rule_out = meta["thresholds"]["rule_out_90_sens"]
        band = "low" if prob < rule_out else "high" if prob >= max(0.5, meta["thresholds"]["youden"]) else "moderate"
        note = ("Estimated from routine measurements with a model trained on 7,094 US adults (NHANES). "
                "It is not a diagnosis. Liver fat and stiffness are confirmed with imaging such as FibroScan.")
        if variant == "basic":
            note += " No blood tests were provided, so the less accurate no-labs model was used."
        return RiskPrediction(task=task, probability=round(prob, 3), band=band, model_variant=variant,
                              outcome=TASK_TEXT[task], drivers=drivers, test_auroc=round(meta["test"]["auroc"], 3),
                              note=note)


@lru_cache
def get_risk_models(model_dir: str) -> RiskModels:
    return RiskModels(Path(model_dir))
