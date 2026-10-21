"""Generate a synthetic Indian-format lab report PDF for demos and tests (no real patient data)."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42  # embed TrueType so text stays extractable
import matplotlib.pyplot as plt  # noqa: E402

ROWS = [
    ("LIVER FUNCTION TEST", None, None, None),
    ("SGPT (ALT)", "68", "U/L", "0 - 40"),
    ("SGOT (AST)", "45", "U/L", "0 - 37"),
    ("Gamma GT (GGTP)", "82", "U/L", "7 - 50"),
    ("Albumin", "4.3", "g/dL", "3.5 - 5.2"),
    ("A/G Ratio", "1.5", "", "1.1 - 2.2"),
    ("COMPLETE BLOOD COUNT", None, None, None),
    ("Platelet Count", "2.1", "lakhs/cumm", "1.5 - 4.1"),
    ("LIPID PROFILE", None, None, None),
    ("Triglycerides", "210", "mg/dL", "< 150"),
    ("HDL Cholesterol", "38", "mg/dL", "> 40"),
    ("DIABETES PANEL", None, None, None),
    ("Fasting Blood Sugar", "112", "mg/dL", "70 - 100"),
    ("HbA1c", "6.1", "%", "4.0 - 5.6"),
]


def main(out: Path) -> Path:
    fig = plt.figure(figsize=(8.27, 11.69))  # A4
    fig.text(0.08, 0.95, "SAMPLE DIAGNOSTICS LAB (synthetic demo report)", fontsize=14, weight="bold")
    fig.text(0.08, 0.92, "Patient: Demo Patient   Age/Sex: 48/M   Date: 01-10-2026", fontsize=10)
    fig.text(0.08, 0.88, "Test Name", weight="bold", fontsize=10)
    for x, h in ((0.45, "Result"), (0.58, "Unit"), (0.75, "Bio. Ref. Interval")):
        fig.text(x, 0.88, h, weight="bold", fontsize=10)
    y = 0.85
    for name, val, unit, ref in ROWS:
        if val is None:
            y -= 0.012
            fig.text(0.08, y, name, weight="bold", fontsize=10)
        else:
            for x, t in ((0.08, name), (0.45, val), (0.58, unit), (0.75, ref)):
                fig.text(x, y, t, fontsize=10)
        y -= 0.03
    fig.text(0.08, 0.05, "This is a synthetic report generated for software testing.", fontsize=8, style="italic")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    return out


if __name__ == "__main__":
    print(main(Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "sample_lab_report.pdf"))
