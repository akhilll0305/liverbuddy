"""Evaluation suites. `liverbuddy eval [suite ...] [--limit N]`

Deterministic suites (safety, drugs) run in CI. Model-dependent suites (retrieval, rag, nutrition, agent)
run against the configured provider and record which models produced the numbers.
Results: evals/results/latest.json and docs/EVALS.md.
"""

from __future__ import annotations

import json
import random
import re
import statistics as st
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from liverbuddy.config import ROOT, get_settings

DATASETS = ROOT / "evals" / "datasets"
RESULTS = ROOT / "evals" / "results"
SEED = 7


def _jsonl(name: str) -> list[dict]:
    return [json.loads(line) for line in (DATASETS / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def _pct(x: float) -> float:
    return round(float(100 * x), 1)


# ---------------------------------------------------------------- safety
def eval_safety(_svc=None, limit=None) -> dict:
    from liverbuddy.safety.guardrails import check_input

    rows = _jsonl("safety_redteam.jsonl")
    preds = [(r, check_input(r["text"]).action) for r in rows]
    by_class: dict[str, list[bool]] = {}
    for r, p in preds:
        by_class.setdefault(r["expected"], []).append(p == r["expected"])
    escalate = {"emergency", "urgent", "crisis"}
    must_escalate = [p in escalate for r, p in preds if r["expected"] in escalate]
    benign = [p == "allow" for r, p in preds if r["expected"] == "allow"]
    held = _jsonl("safety_heldout.jsonl")
    held_preds = [(r, check_input(r["text"]).action) for r in held]
    return {
        "heldout_n": len(held),
        "heldout_accuracy": _pct(np.mean([p == r["expected"] for r, p in held_preds])),
        "heldout_escalation_recall": _pct(np.mean([p in escalate for r, p in held_preds if r["expected"] in escalate])),
        "heldout_failures": [{"text": r["text"], "expected": r["expected"], "got": p}
                             for r, p in held_preds if p != r["expected"]],
        "n": len(rows),
        "accuracy": _pct(np.mean([p == r["expected"] for r, p in preds])),
        "escalation_recall": _pct(np.mean(must_escalate)),
        "benign_pass_rate": _pct(np.mean(benign)),
        "per_class_accuracy": {k: _pct(np.mean(v)) for k, v in sorted(by_class.items())},
        "failures": [{"text": r["text"], "expected": r["expected"], "got": p} for r, p in preds if p != r["expected"]],
    }


# ---------------------------------------------------------------- drugs
def _typo(word: str, rng: random.Random) -> str:
    if len(word) < 6:
        return word
    i = rng.randrange(1, len(word) - 2)
    return word[:i] + word[i + 1] + word[i] + word[i + 2:]  # swap adjacent letters


def eval_drugs(svc, limit=None) -> dict:
    lt = svc.livertox
    rng = random.Random(SEED)
    recs = [r for r in lt.records if "," not in r.name and len(r.name) < 30]
    sample = rng.sample(recs, min(limit or 300, len(recs)))
    cases = []
    for r in sample:
        cases.append(("generic", r.name.lower(), r.name))
        cases.append(("typo", _typo(r.name.lower(), rng), r.name))
        if r.trade_names:
            cases.append(("brand", rng.choice(r.trade_names), r.name))
    from liverbuddy.drugs.synonyms import ALIASES

    cases += [("alias", a, t) for a, t in ALIASES.items()]
    negatives = ["xyzzy", "banana bread", "running shoes", "the weather", "qwertyuiop", "liverwurst sandwich",
                 "football", "blue car", "hello there", "grandma's soup"]
    by_kind: dict[str, list[bool]] = {}
    for kind, q, expected in cases:
        r = lt.lookup(q)
        by_kind.setdefault(kind, []).append(bool(r.matched and r.record and r.record.name == expected))
    false_matches = [q for q in negatives if lt.lookup(q).matched]
    return {
        "n_cases": len(cases), "n_negative": len(negatives),
        "top1_accuracy": {k: _pct(np.mean(v)) for k, v in by_kind.items()},
        "overall_accuracy": _pct(np.mean([x for v in by_kind.values() for x in v])),
        "false_match_rate": _pct(len(false_matches) / len(negatives)), "false_matches": false_matches,
    }


# ---------------------------------------------------------------- retrieval
def eval_retrieval(svc, limit=None) -> dict:
    from liverbuddy.rag.index import RRF_K

    idx = svc.guidelines
    rows = [r for r in _jsonl("guideline_qa.jsonl") if r.get("in_scope", True)][:limit]
    pos = {c.id: i for i, c in enumerate(idx.chunks)}
    results: dict[str, dict] = {}
    rankings: dict[str, list[list[int]]] = {"dense": [], "bm25": [], "hybrid": []}
    for r in rows:
        q = svc.llm.embed([r["question"]], kind="query")[0]
        dense = np.argsort(-(idx.embeddings @ q))
        lex = np.argsort(-idx.bm25.scores(r["question"]))
        fused: dict[int, float] = {}
        for ranking in (dense[:50], lex[:50]):
            for rank, i in enumerate(ranking):
                fused[int(i)] = fused.get(int(i), 0.0) + 1 / (RRF_K + rank + 1)
        rankings["dense"].append([int(i) for i in dense[:20]])
        rankings["bm25"].append([int(i) for i in lex[:20]])
        rankings["hybrid"].append(sorted(fused, key=fused.get, reverse=True)[:20])
    for name, ranks in rankings.items():
        hits = {1: [], 3: [], 6: []}
        rr = []
        for r, ranked in zip(rows, ranks, strict=True):
            gold = {pos[g] for g in r["gold_chunks"] if g in pos}
            first = next((k for k, i in enumerate(ranked, 1) if i in gold), None)
            rr.append(1 / first if first else 0.0)
            for k in hits:
                hits[k].append(first is not None and first <= k)
        results[name] = {f"hit@{k}": _pct(np.mean(v)) for k, v in hits.items()} | {"mrr": round(float(np.mean(rr)), 3)}
    return {"n": len(rows), "embed_model": idx.embed_model, "methods": results}


# ---------------------------------------------------------------- rag answers
def _facts_ok(answer: str, groups: list[list[str]]) -> bool:
    low = answer.lower()
    return all(any(alt.lower() in low for alt in g) for g in groups)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", re.sub(r"\s+", " ", text.strip()))
    return [p for p in parts if len(p) > 25]


def eval_rag(svc, limit=None) -> dict:
    from liverbuddy.rag.qa import answer_question

    rows = _jsonl("guideline_qa.jsonl")
    ins = [r for r in rows if r.get("in_scope", True)][:limit]
    outs = [r for r in rows if not r.get("in_scope", True)][:limit]
    per, lat = [], []
    for r in ins:
        t = time.perf_counter()
        a = answer_question(r["question"], svc.llm, [svc.guidelines, svc.livertox_index])
        lat.append(time.perf_counter() - t)
        sents = _sentences(a.answer) if not a.abstained else []
        per.append({
            "id": r["id"], "answered": not a.abstained, "reason": a.reason,
            "facts_ok": (not a.abstained) and _facts_ok(a.answer, r["key_facts"]),
            "retrieved_gold": any(g in a.retrieved_ids for g in r["gold_chunks"]),
            "cited_gold": any(c.chunk_id in r["gold_chunks"] for c in a.citations),
            "citation_precision": (np.mean([c.chunk_id in r["gold_chunks"] for c in a.citations])
                                   if a.citations else None),
            "sentence_coverage": (np.mean([bool(re.search(r"\[\d+\]", s)) for s in sents]) if sents else None),
        })
    abst = []
    for r in outs:
        a = answer_question(r["question"], svc.llm, [svc.guidelines, svc.livertox_index])
        abst.append({"id": r["id"], "abstained": a.abstained, "reason": a.reason})
    answered = [p for p in per if p["answered"]]
    prec = [p["citation_precision"] for p in answered if p["citation_precision"] is not None]
    cov = [p["sentence_coverage"] for p in answered if p["sentence_coverage"] is not None]
    return {
        "n_in_scope": len(ins), "n_out_of_scope": len(outs),
        "answer_rate": _pct(len(answered) / max(len(ins), 1)),
        "key_fact_accuracy": _pct(np.mean([p["facts_ok"] for p in per])),
        "key_fact_accuracy_when_answered": _pct(np.mean([p["facts_ok"] for p in answered])) if answered else None,
        "retrieval_contains_gold": _pct(np.mean([p["retrieved_gold"] for p in per])),
        "cites_a_gold_passage": _pct(np.mean([p["cited_gold"] for p in answered])) if answered else None,
        "citation_precision": _pct(np.mean(prec)) if prec else None,
        "sentence_citation_coverage": _pct(np.mean(cov)) if cov else None,
        "invented_citations_shown": 0,  # enforced in code: answers with unknown [n] are withheld
        "out_of_scope_abstention": _pct(np.mean([x["abstained"] for x in abst])) if abst else None,
        "latency_s_p50": round(st.median(lat), 2) if lat else None,
        "failures": [p for p in per if not p["facts_ok"]],
        "out_of_scope_detail": abst,
    }


# ---------------------------------------------------------------- nutrition (Nutrition5k)
def _n5k_dishes(path: Path, n: int) -> list[dict]:
    dishes = []
    for line in path.read_text(encoding="utf-8").splitlines():
        p = line.split(",")
        ingr = [{"name": p[i + 1], "grams": float(p[i + 2]), "kcal": float(p[i + 3])}
                for i in range(6, len(p) - 6, 7)]
        if 1 <= len(ingr) <= 8 and float(p[1]) > 20:
            dishes.append({"id": p[0], "kcal": float(p[1]), "mass": float(p[2]), "ingredients": ingr})
    return random.Random(SEED).sample(dishes, min(n, len(dishes)))


def eval_nutrition(svc, limit=None) -> dict:
    from liverbuddy.nutrition.meal import ExtractedItem, analyze_meal, rerank

    dishes = _n5k_dishes(get_settings().raw_dir / "nutrition5k" / "dish_metadata_cafe1.csv", limit or 40)
    det_err, rr_err, det_dish, rr_dish, true_dish, e2e = [], [], [], [], [], []
    for d in dishes:
        cands = [svc.foods.candidates(i["name"], svc.llm, k=8) for i in d["ingredients"]]
        items = [ExtractedItem(name=i["name"], usda_query=i["name"], grams=max(i["grams"], 0.1), food_group="other")
                 for i in d["ingredients"]]
        picks = rerank(svc.llm, items, cands)
        dk = rk = 0.0
        for ing, c, pick in zip(d["ingredients"], cands, picks, strict=True):
            det_kcal = c[0].per_100g.kcal * ing["grams"] / 100 if c else 0.0
            rr_kcal = pick.per_100g.kcal * ing["grams"] / 100 if pick else 0.0
            det_err.append(abs(det_kcal - ing["kcal"]))
            rr_err.append(abs(rr_kcal - ing["kcal"]))
            dk += det_kcal
            rk += rr_kcal
        det_dish.append(dk)
        rr_dish.append(rk)
        true_dish.append(d["kcal"])
        # end-to-end: only ingredient names are given; the LLM must estimate portions
        names = ", ".join(i["name"] for i in d["ingredients"])
        try:
            a = analyze_meal(svc.llm, svc.foods, text=f"A cafeteria plate with: {names}.")
            e2e.append(a.totals.kcal)
        except Exception:
            e2e.append(float("nan"))
    t = np.array(true_dish)

    def dish_stats(pred) -> dict:
        p = np.array(pred, dtype=float)
        ok = ~np.isnan(p)
        ape = np.abs(p[ok] - t[ok]) / t[ok]
        return {"mae_kcal": round(float(np.mean(np.abs(p[ok] - t[ok]))), 1),
                "median_ape_pct": _pct(float(np.median(ape))), "within_20pct": _pct(float(np.mean(ape <= 0.2))),
                "n": int(ok.sum())}

    return {
        "dataset": "Nutrition5k cafe1 metadata (Thames et al., CVPR 2021)", "n_dishes": len(dishes),
        "n_ingredients": len(det_err),
        "ingredient_kcal_mae": {"deterministic_top1": round(float(np.mean(det_err)), 1),
                                "llm_rerank": round(float(np.mean(rr_err)), 1)},
        "dish_true_grams": {"deterministic_top1": dish_stats(det_dish), "llm_rerank": dish_stats(rr_dish)},
        "dish_llm_estimated_portions": dish_stats(e2e),
        "naive_baseline_predict_mean": dish_stats([float(np.mean(t))] * len(t)),
    }


# ---------------------------------------------------------------- agent
def eval_agent(svc, limit=None) -> dict:
    from liverbuddy.agent.copilot import ask
    from liverbuddy.agent.tools import ToolContext

    rows = _jsonl("agent_scenarios.jsonl")[:limit]
    per, lat = [], []
    for r in rows:
        t = time.perf_counter()
        rep = ask(ToolContext(services=svc), r["question"])
        lat.append(time.perf_counter() - t)
        called = [x.name for x in rep.tools]
        per.append({"id": r["id"], "tool_ok": any(e in called for e in r["expect_tools"]), "called": called,
                    "facts_ok": _facts_ok(rep.answer, r["must_contain"]), "steps": rep.steps,
                    "tool_errors": sum(1 for x in rep.tools if x.error),
                    "invalid_citations_removed": len(rep.removed_invalid_citations)})
    return {
        "n": len(rows),
        "tool_selection_accuracy": _pct(np.mean([p["tool_ok"] for p in per])),
        "answer_fact_accuracy": _pct(np.mean([p["facts_ok"] for p in per])),
        "task_success": _pct(np.mean([p["tool_ok"] and p["facts_ok"] for p in per])),
        "mean_steps": round(float(np.mean([p["steps"] for p in per])), 2),
        "tool_error_rate": _pct(np.mean([p["tool_errors"] > 0 for p in per])),
        "turns_with_invalid_citations_caught": sum(p["invalid_citations_removed"] > 0 for p in per),
        "latency_s_p50": round(st.median(lat), 2), "latency_s_p95": round(float(np.percentile(lat, 95)), 2),
        "detail": per,
    }


# ---------------------------------------------------------------- ml (from training artifacts)
def eval_ml(svc=None, limit=None) -> dict:
    out = {}
    for p in sorted(get_settings().model_dir.glob("*.meta.json")):
        m = json.loads(p.read_text())
        out[f"{m['task']}_{m['variant']}"] = {
            "auroc": round(m["test"]["auroc"], 3), "ci": [round(x, 3) for x in m["test"]["auroc_ci"]],
            "auprc": round(m["test"]["auprc"], 3), "brier": round(m["test"]["brier"], 3), "n_test": m["n_test"],
            "baselines": {k: round(v["auroc"], 3) for k, v in m["baselines"].items()}}
    return out


SUITES = {"safety": eval_safety, "drugs": eval_drugs, "ml": eval_ml, "retrieval": eval_retrieval,
          "rag": eval_rag, "nutrition": eval_nutrition, "agent": eval_agent}
OFFLINE = ("safety", "ml")


def main(suites: list[str] | None = None, limit: int | None = None) -> dict:
    from liverbuddy.services import Services

    s = get_settings()
    chosen = suites or list(SUITES)
    svc = None if all(x in OFFLINE for x in chosen) else Services()
    RESULTS.mkdir(parents=True, exist_ok=True)
    latest_path = RESULTS / "latest.json"
    report = json.loads(latest_path.read_text()) if latest_path.exists() else {"suites": {}}
    for name in chosen:
        t = time.time()
        print(f"== {name}")
        res = SUITES[name](svc, limit)
        res["_meta"] = {"ran_at": datetime.now(UTC).isoformat(timespec="seconds"), "seconds": round(time.time() - t, 1),
                        "provider": s.llm_provider,
                        "chat_model": s.gemini_chat_model if s.llm_provider == "gemini" else s.ollama_chat_model,
                        "limit": limit}
        report["suites"][name] = res
        print(json.dumps({k: v for k, v in res.items() if k not in ("failures", "detail", "out_of_scope_detail")},
                         indent=1)[:1500])
    latest_path.write_text(json.dumps(report, indent=2, default=float))
    write_markdown(report, ROOT / "docs" / "EVALS.md")
    return report


def write_markdown(report: dict, path: Path) -> None:
    S = report["suites"]
    L = ["# Evaluation results", "", "_Generated by `liverbuddy eval`. Numbers come from "
         "`evals/results/latest.json`. Do not edit by hand._", ""]

    def meta(name):
        m = S[name]["_meta"]
        return f"_Ran {m['ran_at']} · provider `{m['provider']}` · chat model `{m['chat_model']}` · {m['seconds']}s_"

    if "ml" in S:
        L += ["## Risk models (NHANES 2017-2020, held-out test)", "",
              "| Model | AUROC (95% CI) | AUPRC | Brier | Clinical-score AUROC |", "|---|---|---|---|---|"]
        for k, v in S["ml"].items():
            if k.startswith("_"):
                continue
            base = ", ".join(f"{n} {a}" for n, a in v["baselines"].items())
            L.append(f"| {k} | {v['auroc']} ({v['ci'][0]}-{v['ci'][1]}) | {v['auprc']} | {v['brier']} | {base} |")
        L += ["", "See [MODEL_CARD.md](MODEL_CARD.md) for cohort, limitations and calibration.", ""]
    if "safety" in S:
        x = S["safety"]
        L += ["## Safety guardrails", "", meta("safety"), "",
              f"- **Held-out set** ({x['heldout_n']} new phrasings, never used for tuning): routing accuracy "
              f"**{x['heldout_accuracy']}%**, escalation recall **{x['heldout_escalation_recall']}%**",
              f"- Misses: {[f['text'] for f in x['heldout_failures']] or 'none'}",
              "- History: the first blind run scored 20/22 (90.9%). Its two misses (coffee-ground vomit, \"I "
              "don't want to live anymore\") were fixed and moved into the regression set, so the held-out set "
              "is now smaller and its score is no longer fully blind. Treat 90.9% as the honest estimate.",
              f"- Regression set ({x['n']} prompts, used during development, so optimistic): "
              f"accuracy {x['accuracy']}%",
              f"- Escalation recall (emergency, urgent, crisis) **{x['escalation_recall']}%**",
              f"- Benign prompts passed through: **{x['benign_pass_rate']}%**",
              f"- Per class: {x['per_class_accuracy']}", ""]
    if "drugs" in S:
        x = S["drugs"]
        L += ["## Drug lookup (NIH LiverTox)", "", meta("drugs"), "",
              f"- {x['n_cases']} queries. Top-1 accuracy by query type: {x['top1_accuracy']}",
              f"- False matches on {x['n_negative']} non-drug queries: **{x['false_match_rate']}%**", ""]
    if "retrieval" in S:
        x = S["retrieval"]
        L += ["## Retrieval ablation (guidelines, gold-passage hit rate)", "", meta("retrieval"), "",
              "| Method | hit@1 | hit@3 | hit@6 | MRR |", "|---|---|---|---|---|"]
        for mth, v in x["methods"].items():
            L.append(f"| {mth} | {v['hit@1']}% | {v['hit@3']}% | {v['hit@6']}% | {v['mrr']} |")
        L += [""]
    if "rag" in S:
        x = S["rag"]
        L += ["## Grounded answers", "", meta("rag"), "",
              "| Metric | Value |", "|---|---|",
              f"| In-scope questions answered | {x['answer_rate']}% of {x['n_in_scope']} |",
              f"| Key facts correct (all questions) | {x['key_fact_accuracy']}% |",
              f"| Key facts correct (when answered) | {x['key_fact_accuracy_when_answered']}% |",
              f"| Retrieved a gold passage | {x['retrieval_contains_gold']}% |",
              f"| Answer cites a gold passage | {x['cites_a_gold_passage']}% |",
              f"| Citation precision (cited passages that are gold) | {x['citation_precision']}% |",
              f"| Sentences carrying a citation | {x['sentence_citation_coverage']}% |",
              f"| Out-of-scope questions abstained | {x['out_of_scope_abstention']}% of {x['n_out_of_scope']} |",
              f"| Invented citations shown to users | {x['invented_citations_shown']} (blocked in code) |",
              f"| Median latency | {x['latency_s_p50']} s |", ""]
    if "nutrition" in S:
        x = S["nutrition"]
        L += ["## Nutrition grounding (Nutrition5k)", "", meta("nutrition"), "",
              f"{x['n_dishes']} dishes, {x['n_ingredients']} ingredients. Ground truth: Nutrition5k lab-weighed "
              "portions and calories.", "",
              "| Setting | Dish kcal MAE | Median abs % error | Within 20% |", "|---|---|---|---|"]
        for label, k in (("True grams, top-1 USDA match", ("dish_true_grams", "deterministic_top1")),
                         ("True grams, LLM re-ranked match", ("dish_true_grams", "llm_rerank")),
                         ("LLM-estimated portions (names only)", ("dish_llm_estimated_portions",)),
                         ("Naive baseline (predict mean)", ("naive_baseline_predict_mean",))):
            v = x[k[0]][k[1]] if len(k) == 2 else x[k[0]]
            L.append(f"| {label} | {v['mae_kcal']} | {v['median_ape_pct']}% | {v['within_20pct']}% |")
        L += ["", f"Ingredient-level kcal MAE: top-1 {x['ingredient_kcal_mae']['deterministic_top1']}, "
              f"re-ranked {x['ingredient_kcal_mae']['llm_rerank']}.", ""]
    if "agent" in S:
        x = S["agent"]
        L += ["## Copilot agent (tool use)", "", meta("agent"), "",
              "| Metric | Value |", "|---|---|",
              f"| Scenarios | {x['n']} |", f"| Correct tool selected | {x['tool_selection_accuracy']}% |",
              f"| Required facts in answer | {x['answer_fact_accuracy']}% |",
              f"| Task success (both) | {x['task_success']}% |", f"| Mean steps | {x['mean_steps']} |",
              f"| Turns where invented citations were caught | {x['turns_with_invalid_citations_caught']} |",
              f"| Latency p50 / p95 | {x['latency_s_p50']} s / {x['latency_s_p95']} s |", ""]
    path.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])
