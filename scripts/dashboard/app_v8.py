#!/usr/bin/env python3
"""Mnemosyne V8 Dashboard - notebook style via iframe component.

Launch:
    streamlit run scripts/dashboard/app_v8.py --server.port 8501
"""

from pathlib import Path
import sys

import streamlit as st

scripts_dir = Path(__file__).resolve().parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

st.set_page_config(
    page_title="Mnemosyne V8",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from dashboard.v8_ui import render_dashboard


render_dashboard()
