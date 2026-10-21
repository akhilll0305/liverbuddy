"""Liver Buddy UI pages: a thin client over the FastAPI backend (`liverbuddy serve`)."""

from __future__ import annotations

import os
from datetime import date

import httpx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

API = os.environ.get("LB_API_URL", "http://localhost:8000")
CAT_COLOR = {"low": "#1a7f37", "rule_out": "#1a7f37", "indeterminate": "#9a6700", "high": "#cf222e",
             "rule_in": "#cf222e", "unknown": "#6e7781"}
LIKELIHOOD_COLOR = {"A": "#cf222e", "B": "#e16f24", "C": "#9a6700", "D": "#6e7781", "D*": "#6e7781",
                    "E": "#1a7f37", "E*": "#1a7f37", "X": "#6e7781"}


# ---------------------------------------------------------------- API client
def call(method: str, path: str, **kw):
    headers = kw.pop("headers", {})
    if tok := st.session_state.get("token"):
        headers["Authorization"] = f"Bearer {tok}"
    try:
        r = httpx.request(method, f"{API}{path}", headers=headers, timeout=300, **kw)
    except httpx.ConnectError:
        st.error(f"Can't reach the API at {API}. Start it with `liverbuddy serve`.")
        st.stop()
    if r.status_code == 401 and st.session_state.get("token"):
        st.session_state.pop("token", None)
        st.warning("Your session expired. Please sign in again.")
        st.stop()
    if r.status_code >= 400:
        detail = r.json().get("detail", r.text) if r.headers.get("content-type", "").startswith("application/json") \
            else r.text
        st.error(f"{r.status_code}: {detail}")
        st.stop()
    return r.json()


def signed_in() -> bool:
    return "token" in st.session_state


def disclaimer() -> None:
    st.caption("Educational tool, not a medical device. Always discuss results with your doctor.")


# ---------------------------------------------------------------- shared widgets
def score_cards(panel: dict) -> None:
    cols = st.columns(len(panel["scores"]))
    for col, s in zip(cols, panel["scores"], strict=True):
        with col:
            color = CAT_COLOR[s["category"]]
            value = "—" if s["value"] is None else s["value"]
            st.markdown(f"**{s['name']}**")
            st.markdown(f"<span style='font-size:1.8rem;font-weight:700;color:{color}'>{value}</span>",
                        unsafe_allow_html=True)
            st.caption(s["interpretation"] if s["value"] is not None else f"Needs: {', '.join(s['missing_inputs'])}")
    st.info(panel["next_step"])
    c = panel["criteria"]
    st.caption(f"MASLD cardiometabolic criteria met: {c['met_count']}/5. {c['summary']}")


def risk_block(pred: dict | None, title: str) -> None:
    if not pred:
        return
    st.markdown(f"**{title}**: estimated probability of {pred['outcome']}")
    st.progress(pred["probability"], text=f"{pred['probability'] * 100:.0f}% ({pred['band']})")
    if pred["drivers"]:
        d = pd.DataFrame(pred["drivers"]).iloc[::-1]
        fig = go.Figure(go.Bar(x=d["contribution"], y=[f"{a} = {v}" if v is not None else a
                                                        for a, v in zip(d["label"], d["value"], strict=True)],
                               orientation="h",
                               marker_color=["#cf222e" if x > 0 else "#1a7f37" for x in d["contribution"]]))
        fig.update_layout(height=60 + 32 * len(d), margin=dict(l=0, r=0, t=10, b=0),
                          xaxis_title="Contribution to risk (log-odds, TreeSHAP)")
        st.plotly_chart(fig, width="stretch")
    st.caption(f"{pred['note']} Held-out AUROC {pred['test_auroc']}.")


def measures_form(key: str, defaults: dict | None = None) -> dict | None:
    d = defaults or {}
    with st.form(key):
        c1, c2, c3, c4 = st.columns(4)
        age = c1.number_input("Age", 18, 100, int(d.get("age") or 45))
        sex = c2.selectbox("Sex", ["male", "female"], index=0 if d.get("sex", "male") == "male" else 1)
        height = c3.number_input("Height (cm)", 120.0, 220.0, float(d.get("height_cm") or 170))
        weight = c4.number_input("Weight (kg)", 30.0, 250.0, float(d.get("weight_kg") or 80))
        c1, c2, c3, c4 = st.columns(4)
        waist = c1.number_input("Waist (cm)", 0.0, 200.0, float(d.get("waist_cm") or 0), help="0 = unknown")
        diabetes = c2.checkbox("Type 2 diabetes", bool(d.get("type2_diabetes")))
        bp = c3.checkbox("Treated for high blood pressure", bool(d.get("on_antihypertensives")))
        asian = c4.checkbox("Asian ethnicity (BMI cut-off 23)", bool(d.get("asian_ethnicity")))
        st.markdown("**Blood tests** (leave 0 if unknown)")
        c = st.columns(5)
        labs = {}
        for i, (k, label) in enumerate([("alt", "ALT / SGPT (U/L)"), ("ast", "AST / SGOT (U/L)"),
                                        ("ggt", "GGT (U/L)"), ("platelets", "Platelets (10⁹/L)"),
                                        ("albumin", "Albumin (g/dL)"), ("triglycerides", "Triglycerides (mg/dL)"),
                                        ("hdl", "HDL (mg/dL)"), ("fasting_glucose", "Fasting glucose (mg/dL)"),
                                        ("hba1c", "HbA1c (%)")]):
            labs[k] = c[i % 5].number_input(label, 0.0, 2000.0, float(d.get(k) or 0))
        if not st.form_submit_button("Calculate", type="primary"):
            return None
    out = {"age": age, "sex": sex, "height_cm": height, "weight_kg": weight, "waist_cm": waist or None,
           "type2_diabetes": diabetes, "on_antihypertensives": bp, "asian_ethnicity": asian}
    out.update({k: (v or None) for k, v in labs.items()})
    return out


# ---------------------------------------------------------------- pages
def page_account():
    st.header("Your account")
    if signed_in():
        st.success("Signed in.")
        if st.button("Sign out"):
            st.session_state.clear()
            st.rerun()
        prof = call("GET", "/me/profile")
        with st.form("profile"):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("Display name", prof["display_name"])
            sex = c2.selectbox("Sex", ["male", "female"], index=0 if prof["sex"] != "female" else 1)
            by = c3.number_input("Birth year", 1920, 2008, prof["birth_year"] or 1980)
            c1, c2, c3 = st.columns(3)
            h = c1.number_input("Height (cm)", 120.0, 220.0, float(prof["height_cm"] or 170))
            alc = c2.number_input("Alcohol (grams/week)", 0.0, 1000.0, float(prof["alcohol_g_per_week"] or 0),
                                  help="One standard drink is about 10-14 g")
            asian = c3.checkbox("Asian ethnicity", prof["asian_ethnicity"])
            c1, c2, c3 = st.columns(3)
            dm = c1.checkbox("Type 2 diabetes", prof["type2_diabetes"])
            htn = c2.checkbox("On blood-pressure medicine", prof["on_antihypertensives"])
            lip = c3.checkbox("On cholesterol medicine", prof["on_lipid_lowering"])
            if st.form_submit_button("Save profile", type="primary"):
                call("PUT", "/me/profile", json={"display_name": name, "sex": sex, "birth_year": by, "height_cm": h,
                                                 "asian_ethnicity": asian, "type2_diabetes": dm,
                                                 "on_antihypertensives": htn, "on_lipid_lowering": lip,
                                                 "alcohol_g_per_week": alc})
                st.success("Saved.")
        with st.form("measure"):
            st.markdown("**Log weight / waist / blood pressure**")
            c = st.columns(5)
            when = c[0].date_input("Date", date.today())
            w = c[1].number_input("Weight (kg)", 0.0, 300.0, 0.0)
            wc = c[2].number_input("Waist (cm)", 0.0, 200.0, 0.0)
            sbp = c[3].number_input("Systolic", 0.0, 250.0, 0.0)
            dbp = c[4].number_input("Diastolic", 0.0, 150.0, 0.0)
            if st.form_submit_button("Add measurement"):
                call("POST", "/me/measurements", json={"taken_on": when.isoformat(), "weight_kg": w or None,
                                                       "waist_cm": wc or None, "systolic_bp": sbp or None,
                                                       "diastolic_bp": dbp or None})
                st.success("Added.")
        return
    tab_in, tab_up = st.tabs(["Sign in", "Create account"])
    with tab_in, st.form("login"):
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        if st.form_submit_button("Sign in", type="primary"):
            st.session_state.token = call("POST", "/auth/login", json={"email": email, "password": pw})["access_token"]
            st.rerun()
    with tab_up, st.form("register"):
        email = st.text_input("Email ")
        name = st.text_input("Display name")
        pw = st.text_input("Password (8+ characters)", type="password")
        if st.form_submit_button("Create account", type="primary"):
            st.session_state.token = call("POST", "/auth/register", json={"email": email, "password": pw,
                                                                           "display_name": name})["access_token"]
            st.rerun()


def page_dashboard():
    st.header("My liver dashboard")
    if not signed_in():
        st.info("Sign in on the Account page to track your results over time. You can still use the other tools.")
        return
    s = call("GET", "/me/summary")
    score_cards(s["panel"])
    c1, c2 = st.columns(2)
    with c1:
        risk_block(s["steatosis"], "Liver fat")
    with c2:
        risk_block(s["fibrosis"], "Liver stiffness")
    labs = call("GET", "/me/labs")
    if labs:
        df = pd.DataFrame(labs)
        st.subheader("Trends")
        cols = [c for c in ("fib4", "alt", "ast", "ggt", "triglycerides", "hba1c") if c in df]
        pick = st.multiselect("Show", cols, default=[c for c in ("fib4", "alt") if c in cols])
        if pick:
            fig = go.Figure([go.Scatter(x=df["taken_on"], y=df[c], mode="lines+markers", name=c) for c in pick])
            if "fib4" in pick:
                fig.add_hline(y=1.3, line_dash="dot", annotation_text="FIB-4 1.3")
            fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, width="stretch")
    meals = call("GET", "/me/meals")
    if meals:
        st.subheader("Recent meals")
        st.dataframe(pd.DataFrame(meals)[["eaten_at", "description", "score", "kcal"]], hide_index=True,
                     width="stretch")
    disclaimer()


def page_risk():
    st.header("Check liver scores and risk")
    st.caption("Validated scores (FIB-4, NFS, FLI, HSI, APRI) are calculated with published formulas. The ML "
               "estimate comes from a model trained on 7,094 NHANES adults with FibroScan results.")
    m = measures_form("risk_form")
    if m:
        score_cards(call("POST", "/scores", json=m))
        c1, c2 = st.columns(2)
        with c1:
            risk_block(call("POST", "/risk", json={"measures": m, "task": "steatosis"}), "Liver fat")
        with c2:
            risk_block(call("POST", "/risk", json={"measures": m, "task": "fibrosis"}), "Liver stiffness")
    disclaimer()


def page_copilot():
    st.header("Ask Liver Buddy")
    st.caption("A tool-using assistant. It calculates with validated scores, checks medicines in NIH LiverTox, and "
               "cites the AASLD 2023 and EASL 2024 guidelines.")
    hist = st.session_state.setdefault("chat", [])
    for turn in hist:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])
            if turn.get("meta"):
                _render_reply_meta(turn["meta"])
    if q := st.chat_input("e.g. My ALT is 65 and AST 40, platelets 210, I'm 48. What does that mean?"):
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"), st.spinner("Thinking..."):
            rep = call("POST", "/copilot", json={"question": q, "history": [{"role": t["role"], "content": t["content"]}
                                                                           for t in hist[-6:]]})
            st.markdown(rep["answer"])
            _render_reply_meta(rep)
        hist += [{"role": "user", "content": q}, {"role": "assistant", "content": rep["answer"], "meta": rep}]


def _render_reply_meta(rep: dict) -> None:
    if rep["guardrail"] in ("emergency", "crisis"):
        st.error("Safety response: this message was handled by fixed safety rules, not the AI.")
    if rep.get("citations"):
        with st.expander(f"Sources ({len(rep['citations'])})"):
            for c in rep["citations"]:
                st.markdown(f"**[{c['n']}] {c['title']}**, {c['section']}  \n{c['excerpt']}...  \n[open]({c['url']})")
    if rep.get("tools"):
        with st.expander(f"How I got this ({len(rep['tools'])} tool calls, {rep['steps']} steps)"):
            for t in rep["tools"]:
                st.code(f"{t['name']}({t['arguments']})  {t['latency_ms']} ms\n-> {t['result_preview']}",
                        language="text")


def page_guidelines():
    st.header("Ask the guidelines")
    st.caption("Answers come only from AASLD 2023, EASL-EASD-EASO 2024 and NIH LiverTox, with citations. "
               "If the sources don't cover the question, it says so.")
    q = st.text_input("Question", placeholder="Is coffee good for fatty liver?")
    if q and st.button("Ask", type="primary"):
        with st.spinner("Searching guidelines..."):
            r = call("POST", "/guidelines/ask", json={"question": q})
        if r["answer"] is None:
            st.error(r["guardrail"]["message"])
            return
        a = r["answer"]
        if r["guardrail"]["action"] == "caution_medication":
            st.warning(r["guardrail"]["message"])
        (st.warning if a["abstained"] else st.markdown)(a["answer"])
        for c in a["citations"]:
            with st.expander(f"[{c['n']}] {c['title']}: {c['section']}"):
                st.write(c["excerpt"] + "...")
                st.markdown(f"[Open source]({c['url']})")
        st.caption(f"Top retrieval similarity {a['top_similarity']}")


def page_meals():
    st.header("Meal analyser")
    st.caption("The AI identifies foods and estimates portions. Nutrients come from USDA FoodData Central, and the "
               "liver-diet score follows explicit guideline-based rules.")
    with st.form("meal"):
        text = st.text_area("Describe your meal", placeholder="2 rotis, a bowl of dal, cucumber salad")
        img = st.file_uploader("...or upload a photo", type=["jpg", "jpeg", "png"])
        portion = st.select_slider("Portion size", ["small", "medium", "large"], value="medium")
        save = st.checkbox("Save to my log", value=signed_in(), disabled=not signed_in())
        go_ = st.form_submit_button("Analyse", type="primary")
    if go_:
        files = {"image": (img.name, img.getvalue(), img.type)} if img else None
        with st.spinner("Analysing..."):
            a = call("POST", "/meals/analyze", data={"description": text or "", "portion": portion,
                                                     "save": str(save).lower()}, files=files)
        d = a["diet"]
        color = {"Excellent": "#1a7f37", "Good": "#1a7f37", "Fair": "#9a6700", "Poor": "#cf222e"}[d["verdict"]]
        st.markdown(f"<span style='font-size:2rem;font-weight:700;color:{color}'>{d['score']}/100 · "
                    f"{d['verdict']}</span>", unsafe_allow_html=True)
        for adj in d["adjustments"]:
            st.markdown(f"{'🟢' if adj['points'] > 0 else '🔴'} **{adj['points']:+d}** {adj['reason']}")
        t = a["totals"]
        c = st.columns(5)
        for col, (k, lab) in zip(c, [("kcal", "kcal"), ("protein_g", "protein g"), ("sat_fat_g", "sat fat g"),
                                     ("sugars_g", "sugars g"), ("fiber_g", "fibre g")], strict=True):
            col.metric(lab, f"{t[k]:.0f}")
        st.dataframe(pd.DataFrame([{"food": i["name"], "grams": round(i["grams"]),
                                    "USDA match": i["usda_match"]["description"] if i["usda_match"] else "-",
                                    "kcal": round(i["nutrients"]["kcal"])} for i in a["items"]]),
                     hide_index=True, width="stretch")
        st.caption(a["source"] + " " + d["basis"])


def page_labs():
    st.header("Upload a lab report")
    st.caption("Reads ALT/SGPT, AST/SGOT, GGT, platelets, albumin, lipids, glucose and HbA1c. It handles Indian "
               "report formats (lakh/cumm) and SI units, then calculates your scores.")
    f = st.file_uploader("Lab report (PDF or text)", type=["pdf", "txt"])
    txt = st.text_area("...or paste the report text")
    if (f or txt) and st.button("Extract", type="primary"):
        with st.spinner("Reading report..."):
            r = call("POST", "/labs/extract", files={"file": (f.name, f.getvalue())} if f else None,
                     data={"text": txt} if not f else None)
        st.session_state.extracted = r
    if r := st.session_state.get("extracted"):
        vals = r["extraction"]["values"]
        st.dataframe(pd.DataFrame([{"test": k, "value": v["value"], "unit": v["unit"], "how": v["method"],
                                    "from line": v["raw"]} for k, v in vals.items()]), hide_index=True,
                     width="stretch")
        for w in r["extraction"]["warnings"]:
            st.caption(f"⚠️ {w}")
        if r["panel"]:
            score_cards(r["panel"])
        if signed_in():
            when = st.date_input("Report date", date.today())
            if st.button("Save to my results"):
                call("POST", "/me/labs", json={"taken_on": when.isoformat(), "source": "report",
                                               "values": {k: v["value"] for k, v in vals.items()}})
                st.success("Saved. See your dashboard for trends.")
    disclaimer()


def page_meds():
    st.header("Medicines and supplements")
    st.caption("Liver-injury likelihood from NIH LiverTox (A = well-known cause ... E = unlikely). Never stop a "
               "prescribed medicine without your doctor.")
    q = st.text_input("Look up a medicine (brand or generic)", placeholder="Lipitor, Crocin, ashwagandha...")
    if q:
        r = call("GET", "/drugs/lookup", params={"q": q})
        if r["matched"]:
            rec = r["record"]
            color = LIKELIHOOD_COLOR.get(rec["likelihood"], "#6e7781")
            st.markdown(f"### {rec['name']} <span style='color:{color}'>· LiverTox {rec['likelihood']}</span>",
                        unsafe_allow_html=True)
            st.write(r["category_meaning"])
            st.caption(f"{rec['drug_class']} · brands: {', '.join(rec['trade_names'][:6]) or '-'}")
            st.write(rec["summary"])
            st.markdown(f"[Read the LiverTox monograph]({rec['url']})")
            if signed_in() and st.button(f"Add {rec['name']} to my list"):
                call("POST", "/me/medications", json={"name": q})
                st.rerun()
        else:
            st.warning(r["note"] + (f" Did you mean: {', '.join(r['alternatives'])}?" if r["alternatives"] else ""))
    if signed_in():
        meds = call("GET", "/me/medications")
        if meds:
            st.subheader("My list")
            for m in meds:
                c1, c2 = st.columns([5, 1])
                c1.markdown(f"**{m['name']}** → {m['livertox_name'] or 'not in LiverTox'} "
                            f"(LiverTox {m['likelihood'] or '-'})")
                if c2.button("Remove", key=f"rm{m['id']}"):
                    call("DELETE", f"/me/medications/{m['id']}")
                    st.rerun()


def page_about():
    st.header("How Liver Buddy works")
    st.markdown("""
- **Numbers come from code, not the LLM.** FIB-4, NFS, FLI, HSI and APRI use published formulas. Meal nutrients
  come from USDA. Drug liver risk comes from NIH LiverTox expert scores.
- **The ML risk model** is XGBoost trained on NHANES 2017-2020 FibroScan data, benchmarked against clinical scores.
  Per-patient explanations use TreeSHAP.
- **Grounded answers.** Hybrid retrieval (dense + BM25) over the AASLD 2023 and EASL-EASD-EASO 2024 guidelines.
  Citations are verified in code, and the assistant abstains when the evidence is missing.
- **Safety first.** Emergencies, crisis messages and dose questions are handled by fixed rules before any AI runs.
- **Evaluated.** See `docs/EVALS.md` and `docs/MODEL_CARD.md`.
""")
    h = call("GET", "/health")
    st.json(h)
    disclaimer()
