import math

import pytest

from liverbuddy.scoring.clinical import (
    PatientMeasures,
    apri,
    cardiometabolic_criteria,
    compute_panel,
    fatty_liver_index,
    fib4,
    hepatic_steatosis_index,
    nafld_fibrosis_score,
)


def test_fib4_formula_and_low_category():
    m = PatientMeasures(age=50, ast=40, alt=36, platelets=200)
    r = fib4(m)
    assert r.value == pytest.approx(50 * 40 / (200 * 6), abs=0.01)  # 1.67
    assert r.category == "indeterminate"


def test_fib4_age_adjusted_cutoff_over_65():
    # 1.6 is indeterminate under 65 but low at/over 65 (lower cut-off 2.0)
    m = PatientMeasures(age=66, ast=24, alt=25, platelets=198)
    r = fib4(m)
    assert 1.3 < r.value < 2.0
    assert r.category == "low"


def test_fib4_high():
    r = fib4(PatientMeasures(age=60, ast=80, alt=49, platelets=120))
    assert r.value == pytest.approx(60 * 80 / (120 * 7), abs=0.01)
    assert r.category == "high"


def test_fib4_reports_missing_inputs():
    r = fib4(PatientMeasures(age=40, ast=30))
    assert r.value is None and r.category == "unknown"
    assert set(r.missing_inputs) == {"alt", "platelets"}


def test_nfs_matches_published_equation():
    m = PatientMeasures(age=55, height_cm=170, weight_kg=95, ast=45, alt=50, platelets=180,
                        albumin=4.2, type2_diabetes=True)
    bmi = 95 / 1.7**2
    expected = -1.675 + 0.037 * 55 + 0.094 * bmi + 1.13 + 0.99 * 45 / 50 - 0.013 * 180 - 0.66 * 4.2
    r = nafld_fibrosis_score(m)
    assert r.value == pytest.approx(expected, abs=1e-3)
    assert r.category == "indeterminate"


def test_fli_equation_and_rule_in():
    m = PatientMeasures(height_cm=175, weight_kg=98, waist_cm=108, triglycerides=210, ggt=65)
    bmi = 98 / 1.75**2
    y = 0.953 * math.log(210) + 0.139 * bmi + 0.718 * math.log(65) + 0.053 * 108 - 15.745
    r = fatty_liver_index(m)
    assert r.value == pytest.approx(100 * math.exp(y) / (1 + math.exp(y)), abs=0.1)
    assert r.category == "rule_in"


def test_fli_rule_out_lean():
    r = fatty_liver_index(PatientMeasures(height_cm=170, weight_kg=60, waist_cm=74, triglycerides=70, ggt=14))
    assert r.category == "rule_out"


def test_hsi_female_diabetes_bonus():
    base = dict(height_cm=160, weight_kg=64, alt=30, ast=30)
    male = hepatic_steatosis_index(PatientMeasures(sex="male", **base))
    fem_dm = hepatic_steatosis_index(PatientMeasures(sex="female", type2_diabetes=True, **base))
    assert fem_dm.value - male.value == pytest.approx(4, abs=0.01)


def test_apri():
    assert apri(PatientMeasures(ast=80, platelets=100)).value == pytest.approx(2.0)


def test_cardiometabolic_criteria_and_alcohol():
    m = PatientMeasures(sex="male", height_cm=170, weight_kg=85, triglycerides=180, hdl=38,
                        hba1c=5.9, systolic_bp=125, diastolic_bp=80, alcohol_g_per_week=250)
    c = cardiometabolic_criteria(m)
    assert c.overweight_or_central_obesity and c.dysglycaemia and c.hypertriglyceridaemia and c.low_hdl
    assert c.hypertension is False
    assert c.met_count == 4
    assert c.alcohol_category == "MetALD-range"


def test_asian_bmi_cutoff():
    m = PatientMeasures(height_cm=170, weight_kg=69, asian_ethnicity=True)  # BMI 23.9
    assert cardiometabolic_criteria(m).overweight_or_central_obesity is True
    m2 = PatientMeasures(height_cm=170, weight_kg=69)
    assert cardiometabolic_criteria(m2).overweight_or_central_obesity is False


def test_panel_next_step_follows_fib4():
    p = compute_panel(PatientMeasures(age=45, ast=22, alt=30, platelets=260))
    assert p.scores[0].category == "low"
    assert "primary care" in p.next_step
