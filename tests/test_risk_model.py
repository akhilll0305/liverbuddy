import pytest

from liverbuddy.config import get_settings
from liverbuddy.scoring.clinical import PatientMeasures

model_dir = get_settings().model_dir
pytestmark = pytest.mark.skipif(not (model_dir / "steatosis_full.json").exists(),
                                reason="models not trained (run `liverbuddy train`)")


@pytest.fixture(scope="module")
def models():
    from liverbuddy.ml.predict import RiskModels
    return RiskModels(model_dir)


def test_high_risk_profile_scores_higher_than_lean(models):
    obese = PatientMeasures(age=55, sex="male", height_cm=172, weight_kg=105, waist_cm=118, alt=68,
                            ast=45, ggt=80, triglycerides=260, hba1c=6.8, type2_diabetes=True)
    lean = PatientMeasures(age=30, sex="female", height_cm=165, weight_kg=55, waist_cm=70, alt=14,
                           ast=18, ggt=12, triglycerides=70, hba1c=5.1)
    hi, lo = models.predict(obese, "steatosis"), models.predict(lean, "steatosis")
    assert hi.probability > 0.7 > 0.3 > lo.probability
    assert hi.band == "high" and lo.band == "low"
    assert hi.model_variant == "full"
    assert any(d.feature in {"waist_cm", "bmi", "triglycerides", "alt"} for d in hi.drivers[:3])


def test_no_labs_uses_basic_model(models):
    p = models.predict(PatientMeasures(age=45, sex="male", height_cm=175, weight_kg=90, waist_cm=100),
                       "fibrosis")
    assert p.model_variant == "basic"
    assert "no-labs" in p.note
