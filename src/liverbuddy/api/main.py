"""FastAPI backend. Run: `liverbuddy serve` (or `uvicorn liverbuddy.api.main:app`)."""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from collections.abc import Iterator
from datetime import date
from typing import Annotated, Literal

import httpx
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from liverbuddy import __version__
from liverbuddy.agent.copilot import CopilotReply, ask
from liverbuddy.agent.tools import ToolContext
from liverbuddy.auth import create_token, decode_token, hash_password, verify_password
from liverbuddy.db import (
    LabResult,
    MealLog,
    Measurement,
    Medication,
    User,
    get_sessionmaker,
    lab_timeline,
    latest_measures,
)
from liverbuddy.labs.extract import LabExtraction, extract_labs, pdf_to_text
from liverbuddy.llm import Message
from liverbuddy.ml.predict import RiskPrediction
from liverbuddy.nutrition.meal import MealAnalysis, analyze_meal
from liverbuddy.observability import summarize, trace
from liverbuddy.rag.qa import GroundedAnswer, answer_question
from liverbuddy.safety.guardrails import check_input
from liverbuddy.scoring.clinical import PatientMeasures, ScorePanel, compute_panel, fib4
from liverbuddy.services import ResourceMissing, Services

log = logging.getLogger("liverbuddy")
app = FastAPI(title="Liver Buddy API", version=__version__,
              description="Grounded clinical-AI copilot for MASLD. Educational use only; not a medical device.")
_services: Services | None = None
bearer = HTTPBearer(auto_error=False)


def services() -> Services:
    global _services
    if _services is None:
        _services = Services()
        if "insecure" in _services.settings.jwt_secret:
            log.warning("Using the development JWT secret. Set LB_JWT_SECRET in production.")
    return _services


def get_db(svc: Annotated[Services, Depends(services)]) -> Iterator[Session]:
    with get_sessionmaker(svc.settings.database_url)() as db:
        yield db


Svc = Annotated[Services, Depends(services)]
DB = Annotated[Session, Depends(get_db)]


def optional_user(db: DB, svc: Svc,
                  creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> User | None:
    if creds is None:
        return None
    uid = decode_token(creds.credentials, svc.settings.jwt_secret)
    user = db.get(User, uid) if uid else None
    if user is None:
        raise HTTPException(401, "Invalid or expired token")
    return user


def current_user(user: Annotated[User | None, Depends(optional_user)]) -> User:
    if user is None:
        raise HTTPException(401, "Sign in required")
    return user


Me = Annotated[User, Depends(current_user)]
MaybeMe = Annotated[User | None, Depends(optional_user)]


class RateLimiter:
    """Sliding one-minute window per client, so a public demo cannot exhaust the LLM or fill the database."""

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, per_minute: int, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= now - 60:
                hits.popleft()
            if len(hits) >= per_minute:
                return False
            hits.append(now)
            if len(self._hits) > 10_000:  # forget idle clients
                self._hits = {k: v for k, v in self._hits.items() if v and v[-1] > now - 60}
            return True


_limiter = RateLimiter()


def rate_limit(request: Request, svc: Svc) -> None:
    limit = svc.settings.rate_limit_per_minute
    if not limit:
        return
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    client = forwarded or (request.client.host if request.client else "unknown")
    if not _limiter.allow(client, limit):
        raise HTTPException(429, "Too many requests. Please wait a minute and try again.")


Limited = [Depends(rate_limit)]


@app.exception_handler(ResourceMissing)
async def _missing(_: Request, exc: ResourceMissing):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(httpx.HTTPError)
async def _llm_down(_: Request, exc: httpx.HTTPError):
    return JSONResponse(status_code=503, content={"detail": f"LLM provider unavailable: {exc}"})


@app.middleware("http")
async def _trace(request: Request, call_next):
    with trace(f"{request.method} {request.url.path}"):
        return await call_next(request)


# ---------- health & auth ----------

@app.get("/health")
def health(svc: Svc) -> dict:
    return {"status": "ok", "version": __version__, "llm_provider": svc.settings.llm_provider,
            "resources": svc.status()}


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = ""


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


@app.post("/auth/register", response_model=TokenOut, status_code=201, dependencies=Limited)
def register(body: RegisterIn, db: DB, svc: Svc) -> TokenOut:
    if db.scalar(select(User).where(User.email == body.email.lower())):
        raise HTTPException(409, "Email already registered")
    user = User(email=body.email.lower(), password_hash=hash_password(body.password),
                display_name=body.display_name)
    db.add(user)
    db.commit()
    return TokenOut(access_token=create_token(user.id, svc.settings.jwt_secret, svc.settings.jwt_ttl_minutes))


@app.post("/auth/demo", response_model=TokenOut, status_code=201, dependencies=Limited)
def demo_account(db: DB, svc: Svc) -> TokenOut:
    """Create a throwaway patient with nine months of realistic, improving history (one click for visitors)."""
    import uuid
    from datetime import UTC, datetime, timedelta

    today = date.today()
    user = User(email=f"demo-{uuid.uuid4().hex[:10]}@demo.liverbuddy.dev", password_hash=hash_password(uuid.uuid4().hex),
                display_name="Arjun (demo)", sex="male", birth_year=today.year - 47, height_cm=172,
                type2_diabetes=True, on_lipid_lowering=True, alcohol_g_per_week=14)
    db.add(user)
    db.flush()
    history = [
        (270, {"alt": 82, "ast": 55, "ggt": 104, "platelets": 188, "albumin": 4.3, "triglycerides": 262, "hdl": 35,
               "fasting_glucose": 138, "hba1c": 7.6}, (98.0, 110.0, 142.0, 90.0)),
        (160, {"alt": 64, "ast": 46, "ggt": 80, "platelets": 192, "triglycerides": 214, "hdl": 38,
               "fasting_glucose": 121, "hba1c": 7.0}, (94.0, 106.0, 134.0, 86.0)),
        (30, {"alt": 46, "ast": 35, "ggt": 57, "platelets": 197, "albumin": 4.4, "triglycerides": 171, "hdl": 41,
              "fasting_glucose": 108, "hba1c": 6.5}, (89.5, 101.0, 128.0, 82.0)),
    ]
    for days_ago, labs, (w, waist, sbp, dbp) in history:
        when = today - timedelta(days=days_ago)
        db.add(LabResult(user_id=user.id, taken_on=when, values=labs, source="report"))
        db.add(Measurement(user_id=user.id, taken_on=when, weight_kg=w, waist_cm=waist, systolic_bp=sbp,
                           diastolic_bp=dbp))
    for name, dose in (("Glycomet", "500 mg twice daily"), ("Atorvastatin", "20 mg at night"),
                       ("Telma", "40 mg daily")):
        try:
            rec = svc.livertox.lookup(name).record
        except ResourceMissing:
            rec = None
        db.add(Medication(user_id=user.id, name=name, dose_text=dose, livertox_name=rec.name if rec else None,
                          likelihood=rec.likelihood if rec else None))
    now = datetime.now(UTC)
    for hours_ago, desc, score, kcal in ((4, "2 rotis, dal, cucumber salad", 96, 420),
                                         (28, "Grilled fish, brown rice, sauteed spinach", 91, 560),
                                         (52, "Masala dosa with coconut chutney and filter coffee", 66, 610),
                                         (76, "Chicken biryani and a cola", 31, 1180),
                                         (100, "Oats with banana and walnuts", 88, 390)):
        db.add(MealLog(user_id=user.id, eaten_at=now - timedelta(hours=hours_ago), description=desc, score=score,
                       kcal=kcal, analysis={}))
    db.commit()
    return TokenOut(access_token=create_token(user.id, svc.settings.jwt_secret, svc.settings.jwt_ttl_minutes))


class LoginIn(BaseModel):
    email: EmailStr
    password: str


@app.post("/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: DB, svc: Svc) -> TokenOut:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return TokenOut(access_token=create_token(user.id, svc.settings.jwt_secret, svc.settings.jwt_ttl_minutes))


# ---------- profile & measurements ----------

class ProfileIO(BaseModel):
    display_name: str = ""
    sex: Literal["male", "female"] | None = None
    birth_year: int | None = Field(None, ge=1900, le=2015)
    height_cm: float | None = Field(None, gt=50, lt=260)
    asian_ethnicity: bool = False
    type2_diabetes: bool = False
    on_antihypertensives: bool = False
    on_lipid_lowering: bool = False
    alcohol_g_per_week: float | None = Field(None, ge=0)


@app.get("/me/profile", response_model=ProfileIO)
def get_profile(me: Me) -> ProfileIO:
    return ProfileIO.model_validate(me, from_attributes=True)


@app.put("/me/profile", response_model=ProfileIO)
def put_profile(body: ProfileIO, me: Me, db: DB) -> ProfileIO:
    for k, v in body.model_dump().items():
        setattr(me, k, v)
    db.merge(me)
    db.commit()
    return body


class LabsIn(BaseModel):
    taken_on: date
    values: dict[Literal["alt", "ast", "ggt", "platelets", "albumin", "triglycerides", "hdl", "fasting_glucose",
                         "hba1c"], float]
    source: Literal["manual", "report"] = "manual"


@app.post("/me/labs", status_code=201)
def add_labs(body: LabsIn, me: Me, db: DB) -> dict:
    db.add(LabResult(user_id=me.id, taken_on=body.taken_on, values=body.values, source=body.source))
    db.commit()
    return {"ok": True}


@app.get("/me/labs")
def get_labs(me: Me, db: DB) -> list[dict]:
    rows = lab_timeline(db, me)
    age_now = latest_measures(db, me).age
    for r in rows:
        age = age_now - (date.today().year - date.fromisoformat(r["taken_on"]).year) if age_now else None
        r["fib4"] = fib4(PatientMeasures(age=age, ast=r.get("ast"), alt=r.get("alt"),
                                         platelets=r.get("platelets"))).value
    return rows


class MeasurementIn(BaseModel):
    taken_on: date
    weight_kg: float | None = Field(None, gt=20, lt=400)
    waist_cm: float | None = Field(None, gt=30, lt=250)
    systolic_bp: float | None = None
    diastolic_bp: float | None = None


@app.post("/me/measurements", status_code=201)
def add_measurement(body: MeasurementIn, me: Me, db: DB) -> dict:
    db.add(Measurement(user_id=me.id, **body.model_dump()))
    db.commit()
    return {"ok": True}


@app.get("/me/measurements")
def get_measurements(me: Me, db: DB) -> list[dict]:
    rows = db.scalars(select(Measurement).where(Measurement.user_id == me.id).order_by(Measurement.taken_on))
    return [{"taken_on": m.taken_on.isoformat(), "weight_kg": m.weight_kg, "waist_cm": m.waist_cm,
             "systolic_bp": m.systolic_bp, "diastolic_bp": m.diastolic_bp} for m in rows]


class SummaryOut(BaseModel):
    measures: PatientMeasures
    panel: ScorePanel
    steatosis: RiskPrediction | None
    fibrosis: RiskPrediction | None


@app.get("/me/summary", response_model=SummaryOut)
def summary(me: Me, db: DB, svc: Svc) -> SummaryOut:
    m = latest_measures(db, me)
    try:
        st, fb = svc.risk.predict(m, "steatosis"), svc.risk.predict(m, "fibrosis")
    except (ResourceMissing, KeyError):
        st = fb = None
    return SummaryOut(measures=m, panel=compute_panel(m), steatosis=st, fibrosis=fb)


# ---------- stateless clinical tools ----------

@app.post("/scores", response_model=ScorePanel)
def scores(m: PatientMeasures) -> ScorePanel:
    return compute_panel(m)


class RiskIn(BaseModel):
    measures: PatientMeasures
    task: Literal["steatosis", "fibrosis"] = "steatosis"


@app.post("/risk", response_model=RiskPrediction)
def risk(body: RiskIn, svc: Svc) -> RiskPrediction:
    return svc.risk.predict(body.measures, body.task)


@app.get("/drugs/lookup")
def drug_lookup(q: str, svc: Svc) -> dict:
    return svc.livertox.lookup(q).model_dump()


class MedIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    dose_text: str = ""


@app.post("/me/medications", status_code=201)
def add_medication(body: MedIn, me: Me, db: DB, svc: Svc) -> dict:
    r = svc.livertox.lookup(body.name)
    med = Medication(user_id=me.id, name=body.name, dose_text=body.dose_text,
                     livertox_name=r.record.name if r.record else None,
                     likelihood=r.record.likelihood if r.record else None)
    db.add(med)
    db.commit()
    return {"id": med.id, "lookup": r.model_dump()}


@app.get("/me/medications")
def list_medications(me: Me, db: DB) -> list[dict]:
    meds = db.scalars(select(Medication).where(Medication.user_id == me.id, Medication.active))
    return [{"id": m.id, "name": m.name, "dose_text": m.dose_text, "livertox_name": m.livertox_name,
             "likelihood": m.likelihood} for m in meds]


@app.delete("/me/medications/{med_id}")
def remove_medication(med_id: int, me: Me, db: DB) -> dict:
    med = db.get(Medication, med_id)
    if not med or med.user_id != me.id:
        raise HTTPException(404, "Not found")
    med.active = False
    db.commit()
    return {"ok": True}


# ---------- AI features ----------

class AskIn(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


@app.post("/guidelines/ask", dependencies=Limited)
def guidelines_ask(body: AskIn, svc: Svc) -> dict:
    guard = check_input(body.question)
    if guard.action not in ("allow", "caution_medication"):
        return {"guardrail": guard.model_dump(), "answer": None}
    ans: GroundedAnswer = answer_question(body.question, svc.llm, [svc.guidelines, svc.livertox_index])
    return {"guardrail": guard.model_dump(), "answer": ans.model_dump()}


@app.post("/meals/analyze", response_model=MealAnalysis, dependencies=Limited)
async def meals_analyze(svc: Svc, db: DB, user: MaybeMe, description: Annotated[str | None, Form()] = None,
                        portion: Annotated[str | None, Form()] = None, save: Annotated[bool, Form()] = False,
                        image: Annotated[UploadFile | None, File()] = None) -> MealAnalysis:
    img = await image.read() if image else None
    if not description and not img:
        raise HTTPException(422, "Provide a description or a photo")
    if img and len(img) > 8 * 1024 * 1024:
        raise HTTPException(413, "Image too large (max 8 MB)")
    result = analyze_meal(svc.llm, svc.foods, text=description, image=img, portion_hint=portion)
    if save and user:
        db.add(MealLog(user_id=user.id, description=description or "(photo)", score=result.diet.score,
                       kcal=result.totals.kcal, analysis=result.model_dump(mode="json")))
        db.commit()
    return result


@app.get("/me/meals")
def list_meals(me: Me, db: DB, limit: int = 30) -> list[dict]:
    rows = db.scalars(select(MealLog).where(MealLog.user_id == me.id).order_by(MealLog.eaten_at.desc()).limit(limit))
    return [{"id": m.id, "eaten_at": m.eaten_at.isoformat(), "description": m.description, "score": m.score,
             "kcal": m.kcal} for m in rows]


class LabExtractOut(BaseModel):
    extraction: LabExtraction
    panel: ScorePanel | None


@app.post("/labs/extract", response_model=LabExtractOut, dependencies=Limited)
async def labs_extract(svc: Svc, db: DB, user: MaybeMe, file: Annotated[UploadFile | None, File()] = None,
                       text: Annotated[str | None, Form()] = None) -> LabExtractOut:
    if file is not None:
        data = await file.read()
        if len(data) > 10 * 1024 * 1024:
            raise HTTPException(413, "File too large (max 10 MB)")
        text = pdf_to_text(data) if data[:4] == b"%PDF" else data.decode("utf-8", errors="ignore")
    if not text:
        raise HTTPException(422, "Upload a PDF/text file or paste the report text")
    ext = extract_labs(text, svc.llm)
    base = latest_measures(db, user).model_dump() if user else {}
    base.update({k: v.value for k, v in ext.values.items()})
    return LabExtractOut(extraction=ext, panel=compute_panel(PatientMeasures(**base)))


class CopilotIn(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    history: list[dict] = Field(default_factory=list, description="[{role, content}] of previous turns")


@app.post("/copilot", response_model=CopilotReply, dependencies=Limited)
def copilot(body: CopilotIn, svc: Svc, db: DB, user: MaybeMe) -> CopilotReply:
    history = [Message(h["role"], h["content"]) for h in body.history[-6:]
               if h.get("role") in ("user", "assistant") and isinstance(h.get("content"), str)]
    return ask(ToolContext(services=svc, db=db, user=user), body.question, history)


@app.get("/metrics/llm")
def llm_metrics(svc: Svc) -> dict:
    return summarize(svc.settings.artifacts_dir / "traces.jsonl")
