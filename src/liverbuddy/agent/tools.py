"""Tools the copilot agent can call. Each returns compact JSON-able data; numbers come from code."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from liverbuddy.db import MealLog, Medication, User, lab_timeline, latest_measures
from liverbuddy.nutrition.meal import analyze_meal
from liverbuddy.scoring.clinical import compute_panel
from liverbuddy.services import Services

MEASURE_FIELDS = {
    "age": "number", "sex": "string", "height_cm": "number", "weight_kg": "number", "waist_cm": "number",
    "alt": "number", "ast": "number", "ggt": "number", "platelets": "number", "albumin": "number",
    "triglycerides": "number", "hdl": "number", "fasting_glucose": "number", "hba1c": "number",
    "type2_diabetes": "boolean",
}


@dataclass
class Evidence:
    """Guideline/LiverTox passages shown to the model, numbered across the whole conversation turn."""

    passages: list[dict] = field(default_factory=list)

    def add(self, chunk) -> int:
        for p in self.passages:
            if p["chunk_id"] == chunk.id:
                return p["n"]
        n = len(self.passages) + 1
        self.passages.append({"n": n, "chunk_id": chunk.id, "title": chunk.doc_title, "section": chunk.section,
                              "url": chunk.url, "excerpt": chunk.text[:400]})
        return n


@dataclass
class ToolContext:
    services: Services
    db: Session | None = None
    user: User | None = None
    evidence: Evidence = field(default_factory=Evidence)


def _measures(ctx: ToolContext, overrides: dict[str, Any]):
    from liverbuddy.scoring.clinical import PatientMeasures

    base = latest_measures(ctx.db, ctx.user).model_dump() if ctx.user and ctx.db else {}
    base.update({k: v for k, v in overrides.items() if k in MEASURE_FIELDS and v is not None})
    return PatientMeasures(**{k: v for k, v in base.items() if v is not None})


def compute_liver_scores(ctx: ToolContext, **values) -> dict:
    panel = compute_panel(_measures(ctx, values))
    return {"bmi": panel.bmi,
            "scores": [{"name": s.name, "value": s.value, "category": s.category, "interpretation": s.interpretation,
                        "missing": s.missing_inputs} for s in panel.scores],
            "masld_criteria_met": panel.criteria.met_count, "criteria_summary": panel.criteria.summary,
            "next_step": panel.next_step}


def predict_liver_risk(ctx: ToolContext, task: str = "steatosis", **values) -> dict:
    p = ctx.services.risk.predict(_measures(ctx, values), "fibrosis" if task == "fibrosis" else "steatosis")
    return {"outcome": p.outcome, "probability": p.probability, "band": p.band, "model": p.model_variant,
            "top_drivers": [f"{d.label} ({'raises' if d.contribution > 0 else 'lowers'} risk)" for d in p.drivers[:4]],
            "model_test_auroc": p.test_auroc, "note": p.note}


def check_medication(ctx: ToolContext, name: str) -> dict:
    r = ctx.services.livertox.lookup(name)
    if not r.matched:
        return {"found": False, "query": name, "did_you_mean": r.alternatives, "note": r.note}
    rec = r.record
    return {"found": True, "drug": rec.name, "drug_class": rec.drug_class, "livertox_likelihood": rec.likelihood,
            "meaning": r.category_meaning, "summary": rec.summary[:600], "source": rec.url, "note": r.note}


def search_guidelines(ctx: ToolContext, query: str) -> dict:
    s = ctx.services
    hits = sorted(s.guidelines.search(query, s.llm, k=4) + s.livertox_index.search(query, s.llm, k=2),
                  key=lambda h: h.score, reverse=True)[:5]
    out = [{"cite_as": f"[{ctx.evidence.add(h.chunk)}]", "source": h.chunk.doc_title, "section": h.chunk.section,
            "text": h.chunk.text[:900]} for h in hits if h.dense >= 0.5]
    if not out:
        return {"passages": [], "note": "Nothing relevant found in the guidelines."}
    return {"passages": out, "instruction": "Cite passages with their cite_as marker. Do not cite anything else."}


def analyze_meal_tool(ctx: ToolContext, description: str) -> dict:
    a = analyze_meal(ctx.services.llm, ctx.services.foods, text=description)
    return {"score": a.diet.score, "verdict": a.diet.verdict, "kcal": round(a.totals.kcal),
            "items": [f"{i.name} ~{i.grams:.0f} g" for i in a.items],
            "reasons": [f"{x.points:+d}: {x.reason}" for x in a.diet.adjustments]}


def get_my_health_summary(ctx: ToolContext) -> dict:
    if not ctx.user or not ctx.db:
        return {"error": "No signed-in patient; ask the user for their values instead."}
    m = latest_measures(ctx.db, ctx.user)
    meds = ctx.db.scalars(select(Medication).where(Medication.user_id == ctx.user.id, Medication.active)).all()
    meals = ctx.db.scalars(select(MealLog).where(MealLog.user_id == ctx.user.id)
                           .order_by(MealLog.eaten_at.desc()).limit(14)).all()
    return {"measures": {k: v for k, v in m.model_dump().items() if v not in (None, False)},
            "bmi": round(m.bmi, 1) if m.bmi else None,
            "medications": [{"name": x.name, "livertox_likelihood": x.likelihood} for x in meds],
            "recent_meal_scores": [x.score for x in meals],
            "lab_dates": [r["taken_on"] for r in lab_timeline(ctx.db, ctx.user)]}


def get_lab_trend(ctx: ToolContext, analyte: str) -> dict:
    if not ctx.user or not ctx.db:
        return {"error": "No signed-in patient."}
    rows = lab_timeline(ctx.db, ctx.user)
    if analyte.lower() in ("fib4", "fib-4"):
        from liverbuddy.scoring.clinical import PatientMeasures, fib4

        age = latest_measures(ctx.db, ctx.user).age
        pts = [{"date": r["taken_on"], "value": fib4(PatientMeasures(age=age, ast=r.get("ast"), alt=r.get("alt"),
                                                                      platelets=r.get("platelets"))).value}
               for r in rows]
    else:
        pts = [{"date": r["taken_on"], "value": r.get(analyte.lower())} for r in rows]
    pts = [p for p in pts if p["value"] is not None]
    return {"analyte": analyte, "points": pts,
            "change": round(pts[-1]["value"] - pts[0]["value"], 2) if len(pts) > 1 else None}


def _schema(props: dict[str, str], required: list[str] | None = None, desc: dict[str, str] | None = None) -> dict:
    return {"type": "object", "required": required or [],
            "properties": {k: {"type": t, **({"description": desc[k]} if desc and k in desc else {})}
                           for k, t in props.items()}}


TOOLS: dict[str, tuple[Callable[..., dict], str, dict]] = {
    "get_my_health_summary": (get_my_health_summary,
                              "Get the signed-in patient's saved profile, latest labs, medications and recent "
                              "meal scores. Call this first for questions about 'my' health.", _schema({})),
    "compute_liver_scores": (compute_liver_scores,
                             "Compute validated scores (FIB-4, NAFLD fibrosis score, Fatty Liver Index, HSI, "
                             "APRI) and MASLD criteria. Saved patient data is used automatically; pass only "
                             "values the user just mentioned.", _schema(MEASURE_FIELDS)),
    "predict_liver_risk": (predict_liver_risk,
                           "Machine-learning estimate of liver fat ('steatosis') or raised liver stiffness "
                           "('fibrosis') with the main drivers.",
                           _schema({"task": "string", **MEASURE_FIELDS}, ["task"],
                                   {"task": "steatosis or fibrosis"})),
    "check_medication": (check_medication,
                         "Look up a medicine or supplement in NIH LiverTox for its liver-injury likelihood score.",
                         _schema({"name": "string"}, ["name"])),
    "search_guidelines": (search_guidelines,
                          "Search the AASLD 2023 and EASL-EASD-EASO 2024 fatty liver guidelines and LiverTox. "
                          "Use for any medical fact, recommendation or treatment question.",
                          _schema({"query": "string"}, ["query"])),
    "analyze_meal": (analyze_meal_tool, "Analyse a described meal for liver-friendliness with USDA nutrients.",
                     _schema({"description": "string"}, ["description"])),
    "get_lab_trend": (get_lab_trend, "Trend of one lab value or FIB-4 over the patient's saved results.",
                      _schema({"analyte": "string"}, ["analyte"],
                              {"analyte": "alt, ast, ggt, platelets, triglycerides, hba1c or fib4"})),
}

TOOL_SPECS = [{"type": "function", "function": {"name": n, "description": d, "parameters": p}}
              for n, (_, d, p) in TOOLS.items()]
