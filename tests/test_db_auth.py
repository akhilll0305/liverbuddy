from datetime import date

from liverbuddy.auth import create_token, decode_token, hash_password, verify_password
from liverbuddy.db import (
    LabResult,
    Measurement,
    User,
    get_sessionmaker,
    lab_timeline,
    latest_measures,
)


def test_password_hash_roundtrip():
    h = hash_password("correct horse")
    assert h.startswith("scrypt$") and "correct horse" not in h
    assert verify_password("correct horse", h)
    assert not verify_password("wrong", h)
    assert not verify_password("x", "garbage")


def test_jwt_roundtrip_and_tamper():
    tok = create_token(42, "a-test-secret-that-is-32-bytes-long!", 5)
    assert decode_token(tok, "a-test-secret-that-is-32-bytes-long!") == 42
    assert decode_token(tok, "another-secret-of-at-least-32-bytes!!") is None
    assert decode_token(create_token(1, "a-test-secret-that-is-32-bytes-long!", -1), "a-test-secret-that-is-32-bytes-long!") is None  # expired


def test_latest_measures_merges_most_recent_values(tmp_path):
    Session = get_sessionmaker(f"sqlite:///{(tmp_path / 't.db').as_posix()}")
    with Session() as db:
        u = User(email="a@b.c", password_hash="x", sex="male", birth_year=1980, height_cm=175,
                 type2_diabetes=True)
        db.add(u)
        db.flush()
        db.add_all([
            LabResult(user_id=u.id, taken_on=date(2026, 1, 1), values={"alt": 80, "ast": 50, "platelets": 200}),
            LabResult(user_id=u.id, taken_on=date(2026, 6, 1), values={"alt": 45}),
            Measurement(user_id=u.id, taken_on=date(2026, 6, 1), weight_kg=90, waist_cm=101),
        ])
        db.commit()
        m = latest_measures(db, u, today=date(2026, 10, 1))
        assert m.age == 46 and m.alt == 45 and m.ast == 50 and m.platelets == 200
        assert m.bmi is not None and m.type2_diabetes
        tl = lab_timeline(db, u)
        assert tl[0]["alt"] == 80 and tl[1]["alt"] == 45 and tl[1]["ast"] == 50
