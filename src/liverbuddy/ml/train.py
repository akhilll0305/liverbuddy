"""Train and evaluate steatosis / fibrosis risk models on NHANES, benchmarked against clinical scores.

Run: `liverbuddy train`  (writes models + metrics to artifacts/models, model card to docs/)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.calibration import calibration_curve
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedKFold, train_test_split

from liverbuddy.ml.cohort import BASIC_FEATURES, FULL_FEATURES, build_cohort

SEED = 42
PARAM_GRID = [
    {"max_depth": d, "learning_rate": lr, "min_child_weight": mcw, "subsample": 0.8,
     "colsample_bytree": 0.8, "reg_lambda": 1.0}
    for d in (2, 3, 4) for lr in (0.03, 0.1) for mcw in (1, 5)
]


@dataclass
class Task:
    name: str
    label: str
    baselines: dict[str, str]  # display name -> column with the clinical score


TASKS = [
    Task("steatosis", "steatosis", {"Fatty Liver Index": "fli", "Hepatic Steatosis Index": "hsi"}),
    Task("fibrosis", "fibrosis", {"FIB-4": "fib4", "NAFLD Fibrosis Score": "nfs", "APRI": "apri"}),
]


def add_clinical_scores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    y = (0.953 * np.log(df.triglycerides) + 0.139 * df.bmi + 0.718 * np.log(df.ggt)
         + 0.053 * df.waist_cm - 15.745)
    df["fli"] = 100 * np.exp(y) / (1 + np.exp(y))
    df["hsi"] = 8 * df.alt / df.ast + df.bmi + 2 * df.female + 2 * df.type2_diabetes
    df["fib4"] = df.age * df.ast / (df.platelets * np.sqrt(df.alt))
    ifg = ((df.type2_diabetes == 1) | (df.glucose >= 110)).astype(float)
    df["nfs"] = (-1.675 + 0.037 * df.age + 0.094 * df.bmi + 1.13 * ifg + 0.99 * df.ast / df.alt
                 - 0.013 * df.platelets - 0.66 * df.albumin)
    df["apri"] = (df.ast / 40) / df.platelets * 100
    return df


def bootstrap_auc(y: np.ndarray, p: np.ndarray, n: int = 1000, seed: int = SEED) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    mask = ~np.isnan(p)
    y, p = y[mask], p[mask]
    stats = []
    for _ in range(n):
        idx = rng.integers(0, len(y), len(y))
        if y[idx].min() == y[idx].max():
            continue
        stats.append(roc_auc_score(y[idx], p[idx]))
    return float(roc_auc_score(y, p)), float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


def paired_bootstrap_delta(y, p_model, p_base, n: int = 1000, seed: int = SEED) -> tuple[float, float, float]:
    """AUROC(model) - AUROC(baseline) on the rows where the baseline is computable."""
    rng = np.random.default_rng(seed)
    mask = ~np.isnan(p_base)
    y, a, b = y[mask], p_model[mask], p_base[mask]
    deltas = []
    for _ in range(n):
        idx = rng.integers(0, len(y), len(y))
        if y[idx].min() == y[idx].max():
            continue
        deltas.append(roc_auc_score(y[idx], a[idx]) - roc_auc_score(y[idx], b[idx]))
    return (float(roc_auc_score(y, a) - roc_auc_score(y, b)),
            float(np.percentile(deltas, 2.5)), float(np.percentile(deltas, 97.5)))


def _fit(params: dict, X, y, X_val, y_val) -> xgb.XGBClassifier:
    model = xgb.XGBClassifier(n_estimators=2000, early_stopping_rounds=50, eval_metric="logloss",
                              random_state=SEED, tree_method="hist", **params)
    model.fit(X, y, eval_set=[(X_val, y_val)], verbose=False)
    return model


def select_params(X: pd.DataFrame, y: pd.Series) -> tuple[dict, float]:
    """5-fold CV over a small grid; returns best params and their mean CV AUROC."""
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    best, best_auc = PARAM_GRID[0], -1.0
    for params in PARAM_GRID:
        aucs = []
        for tr, va in skf.split(X, y):
            m = _fit(params, X.iloc[tr], y.iloc[tr], X.iloc[va], y.iloc[va])
            aucs.append(roc_auc_score(y.iloc[va], m.predict_proba(X.iloc[va])[:, 1]))
        if np.mean(aucs) > best_auc:
            best, best_auc = params, float(np.mean(aucs))
    return best, best_auc


def threshold_metrics(y: np.ndarray, p: np.ndarray, thr: float) -> dict:
    pred = p >= thr
    tp, fn = int((pred & (y == 1)).sum()), int((~pred & (y == 1)).sum())
    tn, fp = int((~pred & (y == 0)).sum()), int((pred & (y == 0)).sum())
    return {"threshold": round(float(thr), 4), "sensitivity": tp / max(tp + fn, 1),
            "specificity": tn / max(tn + fp, 1), "ppv": tp / max(tp + fp, 1), "npv": tn / max(tn + fn, 1)}


def train_task(df: pd.DataFrame, task: Task, features: list[str], variant: str, out_dir: Path) -> dict:
    data = df.dropna(subset=["bmi"])
    train_df, test_df = train_test_split(data, test_size=0.2, stratify=data[task.label], random_state=SEED)
    X, y = train_df[features], train_df[task.label]
    params, cv_auc = select_params(X, y)

    # final model: hold out 15% of train for early stopping
    X_tr, X_es, y_tr, y_es = train_test_split(X, y, test_size=0.15, stratify=y, random_state=SEED)
    model = _fit(params, X_tr, y_tr, X_es, y_es)

    # operating points chosen on the early-stopping split, never on test
    p_es = model.predict_proba(X_es)[:, 1]
    fpr, tpr, thr = roc_curve(y_es, p_es)
    youden_thr = float(thr[np.argmax(tpr - fpr)])
    rule_out_thr = float(thr[np.argmax(tpr >= 0.90)])

    y_test = test_df[task.label].to_numpy()
    p_test = model.predict_proba(test_df[features])[:, 1]
    auc, lo, hi = bootstrap_auc(y_test, p_test)
    frac_pos, mean_pred = calibration_curve(y_test, p_test, n_bins=10, strategy="quantile")
    fpr_t, tpr_t, _ = roc_curve(y_test, p_test)

    baselines = {}
    for name, col in task.baselines.items():
        b = test_df[col].to_numpy(dtype=float)
        b_auc, b_lo, b_hi = bootstrap_auc(y_test, b)
        d, d_lo, d_hi = paired_bootstrap_delta(y_test, p_test, b)
        fb, tb, _ = roc_curve(y_test[~np.isnan(b)], b[~np.isnan(b)])
        baselines[name] = {"auroc": b_auc, "ci": [b_lo, b_hi], "delta_vs_model": [d, d_lo, d_hi],
                           "n": int((~np.isnan(b)).sum()),
                           "roc": {"fpr": fb[::max(1, len(fb) // 200)].tolist(),
                                   "tpr": tb[::max(1, len(tb) // 200)].tolist()}}

    subgroups = {}
    for name, mask in {"female": test_df.female == 1, "male": test_df.female == 0,
                       "age<50": test_df.age < 50, "age>=50": test_df.age >= 50,
                       "BMI<25 (lean)": test_df.bmi < 25, "BMI>=25": test_df.bmi >= 25}.items():
        m = mask.to_numpy()
        if y_test[m].min() != y_test[m].max():
            subgroups[name] = {"n": int(m.sum()), "auroc": float(roc_auc_score(y_test[m], p_test[m]))}

    gain = model.get_booster().get_score(importance_type="gain")
    importance = sorted(((f, round(gain.get(f, 0.0), 3)) for f in features), key=lambda t: -t[1])

    stem = f"{task.name}_{variant}"
    model.save_model(out_dir / f"{stem}.json")
    meta = {
        "task": task.name, "variant": variant, "label_definition": task.label, "features": features,
        "params": params, "cv_auroc": cv_auc, "best_iteration": int(model.best_iteration),
        "n_train": len(train_df), "n_test": len(test_df), "prevalence_test": float(y_test.mean()),
        "test": {"auroc": auc, "auroc_ci": [lo, hi], "auprc": float(average_precision_score(y_test, p_test)),
                 "brier": float(brier_score_loss(y_test, p_test)),
                 "youden": threshold_metrics(y_test, p_test, youden_thr),
                 "rule_out_90_sens": threshold_metrics(y_test, p_test, rule_out_thr),
                 "calibration": {"mean_pred": mean_pred.tolist(), "frac_pos": frac_pos.tolist()},
                 "roc": {"fpr": fpr_t[::max(1, len(fpr_t) // 200)].tolist(),
                         "tpr": tpr_t[::max(1, len(tpr_t) // 200)].tolist()}},
        "baselines": baselines, "subgroups": subgroups, "gain_importance": importance,
        "thresholds": {"youden": youden_thr, "rule_out_90_sens": rule_out_thr},
    }
    (out_dir / f"{stem}.meta.json").write_text(json.dumps(meta, indent=2))
    return meta


def _fmt_ci(v: float, ci: list[float]) -> str:
    return f"{v:.3f} ({ci[0]:.3f}-{ci[1]:.3f})"


def write_model_card(results: list[dict], counts: dict, path: Path, fig_dir: Path) -> None:
    lines = ["# Model card: NHANES MASLD risk models", "",
             "_Generated by `liverbuddy train`. Do not edit by hand._", "",
             "## Intended use",
             "Educational risk estimate of hepatic steatosis (CAP >= 274 dB/m) and clinically significant "
             "liver stiffness (LSM >= 8 kPa) from routine measurements. **Not a diagnostic device.** "
             "It is meant to explain *why* a person might discuss non-invasive testing with their doctor.", "",
             "## Data",
             "NHANES 2017-March 2020 pre-pandemic cycle (CDC, public domain). Labels come from "
             "vibration-controlled transient elastography. Cohort flow:", "",
             "| Step | n |", "|---|---|"]
    lines += [f"| {k.replace('_', ' ')} | {v:,} |" for k, v in counts.items()]
    lines += ["", "Exclusions: incomplete elastography, age < 18, viral hepatitis (HCV RNA+ or self-reported "
              "HBV/HCV), and alcohol intake of 140 g/week or more (women) or 210 g/week or more (men), which "
              "falls outside the MASLD alcohol range.", "",
              "## Results (held-out 20% test split, 95% bootstrap CI)", "",
              "| Model | Features | AUROC | AUPRC | Brier | Sens / Spec @ Youden |",
              "|---|---|---|---|---|---|"]
    for r in results:
        t = r["test"]
        lines.append(f"| {r['task']} ({r['variant']}) | {len(r['features'])} | {_fmt_ci(t['auroc'], t['auroc_ci'])}"
                     f" | {t['auprc']:.3f} | {t['brier']:.3f} | {t['youden']['sensitivity']:.2f} / "
                     f"{t['youden']['specificity']:.2f} |")
    lines += ["", "### Against established clinical scores (same test rows)", "",
              "| Task | Score | AUROC (95% CI) | Model minus score, delta AUROC (95% CI) |", "|---|---|---|---|"]
    for r in results:
        if r["variant"] != "full":
            continue
        for name, b in r["baselines"].items():
            d = b["delta_vs_model"]
            lines.append(f"| {r['task']} | {name} | {_fmt_ci(b['auroc'], b['ci'])} | "
                         f"{d[0]:+.3f} ({d[1]:+.3f} to {d[2]:+.3f}) |")
    lines += ["", "### Subgroups (full models)", "", "| Task | Subgroup | n | AUROC |", "|---|---|---|---|"]
    for r in results:
        if r["variant"] == "full":
            lines += [f"| {r['task']} | {g} | {v['n']} | {v['auroc']:.3f} |" for g, v in r["subgroups"].items()]
    lines += ["", "![ROC curves](figures/roc.png)", "![Calibration](figures/calibration.png)", "",
              "## Limitations",
              "- Analysis is unweighted. NHANES survey weights are not applied, so prevalence is not a "
              "US population estimate.",
              "- CAP and LSM are imperfect reference standards. Biopsy is the gold standard.",
              "- Triglycerides and glucose come from non-fasting serum biochemistry.",
              "- One US cohort only. Calibration in other populations (for example South Asian patients) "
              "is unknown and likely to differ.",
              "- Race and ethnicity are deliberately excluded as features.",
              "- The fibrosis comparison is not like-for-like. FIB-4, NFS and APRI were designed to detect "
              "*advanced* fibrosis (F3-F4), while the label here is LSM >= 8 kPa, a broader rule-out "
              "threshold. The model is optimised for this label and the scores are not, so the large "
              "delta overstates any clinical advantage. FIB-4 stays the guideline first-line test, and the "
              "app always shows it.",
              "- The basic variant (no blood tests) is intended for people without recent labs. Its "
              "accuracy is lower.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    _plot(results, fig_dir)


def _plot(results: list[dict], fig_dir: Path) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    fig_dir.mkdir(parents=True, exist_ok=True)
    full = [r for r in results if r["variant"] == "full"]
    fig, axes = plt.subplots(1, len(full), figsize=(6 * len(full), 5))
    for ax, r in zip(np.atleast_1d(axes), full, strict=True):
        ax.plot(r["test"]["roc"]["fpr"], r["test"]["roc"]["tpr"], lw=2.5,
                label=f"XGBoost (AUROC {r['test']['auroc']:.3f})")
        for name, b in r["baselines"].items():
            ax.plot(b["roc"]["fpr"], b["roc"]["tpr"], lw=1.5, label=f"{name} ({b['auroc']:.3f})")
        ax.plot([0, 1], [0, 1], "k:", lw=1)
        ax.set(title=f"{r['task'].title()} - held-out test", xlabel="1 - specificity", ylabel="Sensitivity")
        ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    fig.savefig(fig_dir / "roc.png", dpi=130)
    plt.close(fig)

    fig, axes = plt.subplots(1, len(full), figsize=(6 * len(full), 5))
    for ax, r in zip(np.atleast_1d(axes), full, strict=True):
        c = r["test"]["calibration"]
        ax.plot(c["mean_pred"], c["frac_pos"], "o-", lw=2)
        ax.plot([0, 1], [0, 1], "k:", lw=1)
        ax.set(title=f"{r['task'].title()} calibration (Brier {r['test']['brier']:.3f})",
               xlabel="Predicted probability", ylabel="Observed fraction")
    fig.tight_layout()
    fig.savefig(fig_dir / "calibration.png", dpi=130)
    plt.close(fig)


def train_all(raw_dir: Path, out_dir: Path, docs_dir: Path) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    df, counts = build_cohort(raw_dir)
    df = add_clinical_scores(df)
    results = []
    for task in TASKS:
        for variant, feats in (("full", FULL_FEATURES), ("basic", BASIC_FEATURES)):
            meta = train_task(df, task, feats, variant, out_dir)
            print(f"{task.name:10s} {variant:6s} AUROC {meta['test']['auroc']:.3f} "
                  f"CI {meta['test']['auroc_ci'][0]:.3f}-{meta['test']['auroc_ci'][1]:.3f}")
            results.append(meta)
    (out_dir / "cohort_counts.json").write_text(json.dumps(counts, indent=2))
    write_model_card(results, counts, docs_dir / "MODEL_CARD.md", docs_dir / "figures")
    return results


if __name__ == "__main__":  # pragma: no cover
    from liverbuddy.config import ROOT, get_settings

    s = get_settings()
    train_all(s.raw_dir / "nhanes", s.model_dir, ROOT / "docs")
