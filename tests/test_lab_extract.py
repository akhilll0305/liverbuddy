import json

import pytest

from liverbuddy.labs.extract import extract_labs, extract_rules
from liverbuddy.llm import ChatResponse
from liverbuddy.llm.fake import FakeLLM

INDIAN_REPORT = """
LIVER FUNCTION TEST
Test Name                    Result     Unit        Bio. Ref. Interval
SGPT (ALT)                   68         U/L         0 - 40
SGOT (AST)                   45  H      U/L         0 - 37
Gamma GT (GGTP)              82         U/L         7 - 50
Albumin                      4.3        g/dL        3.5 - 5.2
A/G Ratio                    1.5                    1.1 - 2.2
COMPLETE BLOOD COUNT
Platelet Count               2.1        lakhs/cumm  1.5 - 4.1
LIPID PROFILE
Triglycerides                210        mg/dL       < 150
HDL Cholesterol              38         mg/dL       > 40
Fasting Blood Sugar          112        mg/dL       70 - 100
HbA1c                        6.1        %           4.0 - 5.6
"""

SI_REPORT = """
Alanine aminotransferase   35 U/L (7-56)
Aspartate aminotransferase 30 U/L
Platelets                  245 x10^9/L
Albumin                    42 g/L
Triglycerides              1.9 mmol/L
HDL-C                      1.1 mmol/L
Glucose, fasting           6.2 mmol/L
HbA1c                      48 mmol/mol
"""


def test_indian_report_units_and_values():
    found, _ = extract_rules(INDIAN_REPORT)
    v = {k: x.value for k, x in found.items()}
    assert v["alt"] == 68 and v["ast"] == 45 and v["ggt"] == 82
    assert v["platelets"] == 210  # 2.1 lakh/cumm
    assert v["albumin"] == 4.3  # not the A/G ratio
    assert v["triglycerides"] == 210 and v["hdl"] == 38
    assert v["fasting_glucose"] == 112 and v["hba1c"] == 6.1


def test_si_units_are_converted():
    found, warnings = extract_rules(SI_REPORT)
    v = {k: x.value for k, x in found.items()}
    assert v["albumin"] == pytest.approx(4.2)
    assert v["triglycerides"] == pytest.approx(168.3, abs=0.5)
    assert v["hdl"] == pytest.approx(42.5, abs=0.5)
    assert v["fasting_glucose"] == pytest.approx(111.7, abs=0.5)
    assert v["hba1c"] == pytest.approx(6.54, abs=0.05)
    assert any("mmol" in w for w in warnings)


def test_absolute_platelet_count():
    found, _ = extract_rules("Platelet count 2,45,000 /cumm")
    assert found["platelets"].value == 245


def test_llm_fills_gaps_but_implausible_values_are_rejected():
    reply = {"ggt": 55, "platelets": 99999}  # platelets implausible -> rejected
    llm = FakeLLM(lambda m, t, s: ChatResponse(content=json.dumps(reply)))
    out = extract_labs("ALT 40 U/L\nsome unusual GGT layout: fifty five", llm)
    assert out.values["alt"].method == "rule"
    assert out.values["ggt"].method == "llm" and out.values["ggt"].value == 55
    assert "platelets" in out.missing


def test_pdf_report_end_to_end():
    from pathlib import Path

    from liverbuddy.labs.extract import pdf_to_text

    pdf = Path(__file__).parent / "fixtures" / "sample_lab_report.pdf"
    out = extract_labs(pdf_to_text(pdf.read_bytes()))
    assert out.missing == []
    assert out.values["platelets"].value == 210 and out.values["albumin"].value == 4.3
