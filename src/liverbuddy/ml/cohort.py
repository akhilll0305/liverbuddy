"""Build an adult MASLD-focused analysis cohort from NHANES 2017-March 2020 (pre-pandemic).

Outcome labels come from vibration-controlled transient elastography (FibroScan):
  * steatosis: controlled attenuation parameter (CAP) >= 274 dB/m  (Eddowes et al., Gastroenterology 2019)
  * fibrosis:  liver stiffness measurement (LSM) >= 8.0 kPa       (EASL-EASD-EASO 2024 rule-out threshold)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

NHANES_BASE = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles"
NHANES_FILES = ["P_LUX", "P_DEMO", "P_BMX", "P_BIOPRO", "P_CBC", "P_GHB", "P_DIQ", "P_ALQ",
                "P_HDL", "P_BPQ", "P_HEPC", "P_HEQ"]

CAP_STEATOSIS = 274.0
LSM_FIBROSIS = 8.0

# feature name -> (file, column)
RAW_COLUMNS = {
    "age": ("P_DEMO", "RIDAGEYR"),
    "sex_code": ("P_DEMO", "RIAGENDR"),
    "bmi": ("P_BMX", "BMXBMI"),
    "waist_cm": ("P_BMX", "BMXWAIST"),
    "alt": ("P_BIOPRO", "LBXSATSI"),
    "ast": ("P_BIOPRO", "LBXSASSI"),
    "ggt": ("P_BIOPRO", "LBXSGTSI"),
    "triglycerides": ("P_BIOPRO", "LBXSTR"),
    "glucose": ("P_BIOPRO", "LBXSGL"),
    "albumin": ("P_BIOPRO", "LBXSAL"),
    "platelets": ("P_CBC", "LBXPLTSI"),
    "hba1c": ("P_GHB", "LBXGH"),
    "hdl": ("P_HDL", "LBDHDD"),
}

FULL_FEATURES = ["age", "female", "bmi", "waist_cm", "type2_diabetes", "hypertension", "alt", "ast",
                 "ggt", "triglycerides", "glucose", "albumin", "platelets", "hba1c", "hdl"]
BASIC_FEATURES = ["age", "female", "bmi", "waist_cm", "type2_diabetes", "hypertension"]

# ALQ121 "past 12 months how often drink" code -> approximate drinking days per week
_ALQ121_DAYS_PER_WEEK = {0: 0, 1: 7, 2: 5.5, 3: 3.5, 4: 2, 5: 1, 6: 0.58, 7: 0.23, 8: 0.17, 9: 0.09,
                         10: 0.03}
GRAMS_PER_DRINK = 14.0


def _read(raw_dir: Path, name: str) -> pd.DataFrame:
    return pd.read_sas(raw_dir / f"{name}.xpt", format="xport").set_index("SEQN")


def alcohol_g_per_week(alq: pd.DataFrame) -> pd.Series:
    never = alq["ALQ111"] == 2
    days = alq["ALQ121"].map(_ALQ121_DAYS_PER_WEEK)
    drinks = alq["ALQ130"].where(alq["ALQ130"] < 100)  # 777/999 = refused / don't know
    grams = days * drinks * GRAMS_PER_DRINK
    grams = grams.where(~(alq["ALQ121"] == 0), 0.0)
    return grams.where(~never, 0.0)


def build_cohort(raw_dir: Path) -> tuple[pd.DataFrame, dict[str, int]]:
    """Return (cohort dataframe, CONSORT-style exclusion counts)."""
    files = {n: _read(raw_dir, n) for n in NHANES_FILES}
    lux = files["P_LUX"]
    df = pd.DataFrame(index=lux.index)
    for feat, (f, col) in RAW_COLUMNS.items():
        df[feat] = files[f][col].reindex(df.index)

    df["female"] = (df.pop("sex_code") == 2).astype(float)
    df["type2_diabetes"] = (files["P_DIQ"]["DIQ010"].reindex(df.index) == 1).astype(float)
    df["hypertension"] = (files["P_BPQ"]["BPQ020"].reindex(df.index) == 1).astype(float)
    df["alcohol_g_week"] = alcohol_g_per_week(files["P_ALQ"]).reindex(df.index)
    df["cap"] = lux["LUXCAPM"]
    df["lsm"] = lux["LUXSMED"]
    df["lsm_iqr_med"] = lux["LUXSIQRM"]
    df["exam_status"] = lux["LUAXSTAT"]
    hcv_rna = files["P_HEPC"]["LBXHCR"].reindex(df.index)
    told_hbv = files["P_HEQ"]["HEQ010"].reindex(df.index)
    told_hcv = files["P_HEQ"]["HEQ030"].reindex(df.index)

    counts = {"elastography_participants": len(df)}
    keep = df["exam_status"] == 1
    counts["after_complete_exam"] = int(keep.sum())
    keep &= df["age"] >= 18
    counts["after_adults_only"] = int(keep.sum())
    keep &= df["cap"].notna() & df["lsm"].notna()
    counts["after_cap_lsm_present"] = int(keep.sum())
    keep &= ~((hcv_rna == 1) | (told_hbv == 1) | (told_hcv == 1))
    counts["after_viral_hepatitis_excluded"] = int(keep.sum())
    heavy = np.where(df["female"] == 1, df["alcohol_g_week"] >= 140, df["alcohol_g_week"] >= 210)
    keep &= ~pd.Series(heavy, index=df.index)
    counts["after_significant_alcohol_excluded"] = int(keep.sum())

    out = df[keep].copy()
    out["steatosis"] = (out["cap"] >= CAP_STEATOSIS).astype(int)
    # LSM reliability: IQR/median <= 30% (Boursier criteria) for the fibrosis label
    out["lsm_reliable"] = out["lsm_iqr_med"] <= 30
    out["fibrosis"] = (out["lsm"] >= LSM_FIBROSIS).astype(int)
    counts["final_cohort"] = len(out)
    counts["fibrosis_cohort_reliable_lsm"] = int(out["lsm_reliable"].sum())
    return out, counts
