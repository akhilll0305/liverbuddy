"""Liver Buddy web UI entry point: `liverbuddy ui` or `streamlit run app/streamlit_app.py`."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
st.set_page_config(page_title="Liver Buddy", page_icon="🫀", layout="wide")

from ui import (  # noqa: E402
    page_about,
    page_account,
    page_copilot,
    page_dashboard,
    page_guidelines,
    page_labs,
    page_meals,
    page_meds,
    page_risk,
)

pages = [st.Page(page_dashboard, title="Dashboard", icon="📊", default=True),
         st.Page(page_copilot, title="Ask Liver Buddy", icon="💬"),
         st.Page(page_risk, title="Scores & risk", icon="🧮"),
         st.Page(page_labs, title="Lab report", icon="🧪"),
         st.Page(page_meals, title="Meals", icon="🥗"),
         st.Page(page_meds, title="Medicines", icon="💊"),
         st.Page(page_guidelines, title="Guidelines Q&A", icon="📚"),
         st.Page(page_account, title="Account", icon="👤"),
         st.Page(page_about, title="About", icon="ℹ️")]
st.navigation(pages).run()
