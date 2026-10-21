import json

import pytest
from fastapi.testclient import TestClient

from liverbuddy.api import main as api
from liverbuddy.config import Settings
from liverbuddy.llm import ChatResponse, ToolCall
from liverbuddy.llm.fake import FakeLLM
from liverbuddy.rag.corpus import Chunk
from liverbuddy.rag.index import HybridIndex
from liverbuddy.services import Services


@pytest.fixture
def client(tmp_path):
    fake = FakeLLM()
    chunk = Chunk("g-0", "aasld2023", "AASLD 2023", "Lifestyle",
                  "Weight loss of 7 to 10 percent improves fatty liver disease.", "u", "text")
    for name in ("guidelines", "livertox"):
        HybridIndex.build([chunk], fake, "fake").save(tmp_path / "index", name)
    (tmp_path / "index" / "livertox_drugs.json").write_text(json.dumps([{
        "id": "Atorvastatin", "name": "Atorvastatin", "trade_names": ["Lipitor"], "drug_class": "Statins",
        "likelihood": "A", "likelihood_all": ["A"], "summary": "", "url": "u"}]))
    settings = Settings(artifacts_dir=tmp_path, llm_provider="fake",
                        database_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
                        jwt_secret="a-test-secret-that-is-at-least-32-bytes")
    svc = Services(settings, llm=fake)
    api.app.dependency_overrides[api.services] = lambda: svc
    with TestClient(api.app) as c:
        c.fake = fake
        yield c
    api.app.dependency_overrides.clear()


def auth(client) -> dict:
    tok = client.post("/auth/register", json={"email": "p@example.com", "password": "longpassword"}).json()
    return {"Authorization": f"Bearer {tok['access_token']}"}


def test_health_reports_resources(client):
    r = client.get("/health").json()
    assert r["status"] == "ok" and r["resources"]["guidelines_index"]


def test_register_login_and_protected_routes(client):
    h = auth(client)
    assert client.post("/auth/register", json={"email": "p@example.com", "password": "longpassword"}).status_code == 409
    assert client.post("/auth/login", json={"email": "p@example.com", "password": "wrongpass1"}).status_code == 401
    assert client.get("/me/profile").status_code == 401
    assert client.get("/me/profile", headers={"Authorization": "Bearer junk"}).status_code == 401
    assert client.get("/me/profile", headers=h).status_code == 200


def test_profile_labs_and_summary_flow(client):
    h = auth(client)
    client.put("/me/profile", headers=h, json={"sex": "male", "birth_year": 1975, "height_cm": 175,
                                               "type2_diabetes": True})
    client.post("/me/measurements", headers=h, json={"taken_on": "2026-09-01", "weight_kg": 92, "waist_cm": 104})
    client.post("/me/labs", headers=h, json={"taken_on": "2026-09-01",
                                             "values": {"alt": 60, "ast": 45, "platelets": 190}})
    s = client.get("/me/summary", headers=h).json()
    assert s["panel"]["scores"][0]["name"] == "FIB-4" and s["panel"]["scores"][0]["value"] is not None
    labs = client.get("/me/labs", headers=h).json()
    assert labs[0]["fib4"] is not None


def test_stateless_scores_endpoint(client):
    r = client.post("/scores", json={"age": 50, "ast": 40, "alt": 36, "platelets": 200}).json()
    assert r["scores"][0]["value"] == pytest.approx(1.67, abs=0.01)


def test_medication_saved_with_livertox_category(client):
    h = auth(client)
    r = client.post("/me/medications", headers=h, json={"name": "Lipitor 20mg"}).json()
    assert r["lookup"]["record"]["name"] == "Atorvastatin"
    meds = client.get("/me/medications", headers=h).json()
    assert meds[0]["likelihood"] == "A"
    assert client.delete(f"/me/medications/{meds[0]['id']}", headers=h).json()["ok"]
    assert client.get("/me/medications", headers=h).json() == []


def test_guidelines_ask_emergency_is_intercepted(client):
    r = client.post("/guidelines/ask", json={"question": "I vomited blood, what now?"}).json()
    assert r["guardrail"]["action"] == "emergency" and r["answer"] is None


def test_copilot_endpoint_runs_tool_loop(client):
    queue = [ChatResponse(content="", tool_calls=[ToolCall("compute_liver_scores",
                                                           {"age": 50, "ast": 40, "alt": 36, "platelets": 200})]),
             ChatResponse(content="Your FIB-4 is 1.67 (indeterminate).")]
    client.fake.responder = lambda m, t, s: queue.pop(0)
    r = client.post("/copilot", json={"question": "what is my FIB-4?"}).json()
    assert r["tools"][0]["name"] == "compute_liver_scores" and '"value": 1.67' in r["tools"][0]["result_preview"]


def test_labs_extract_from_text(client):
    r = client.post("/labs/extract", data={"text": "SGPT 68 U/L\nSGOT 45 U/L\nPlatelet count 2.1 lakhs/cumm"})
    body = r.json()
    assert body["extraction"]["values"]["platelets"]["value"] == 210
    assert body["panel"]["scores"][0]["missing_inputs"] == ["age"]


def test_demo_account_has_history(client):
    tok = client.post("/auth/demo").json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    labs = client.get("/me/labs", headers=h).json()
    assert len(labs) == 3 and labs[0]["alt"] > labs[-1]["alt"]
    assert len(client.get("/me/meals", headers=h).json()) == 5
    assert client.get("/me/summary", headers=h).json()["panel"]["scores"][0]["value"] is not None


def test_root_server_mounts_api_under_prefix():
    from fastapi.testclient import TestClient

    from liverbuddy.api.server import root

    with TestClient(root) as c:
        assert c.post("/api/scores", json={"age": 50, "ast": 40, "alt": 36, "platelets": 200}).status_code == 200
        assert c.get("/some/client/route").status_code in (200, 404)
