
import os
import time
from pathlib import Path
from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from smart_features import (
    record_snapshot,
    predict_disk_full,
    get_resource_warnings,
    scan_large_files,
    scan_old_downloads,
    scan_duplicates,
    get_battery_insights,
    get_windows_battery_health,
    estimate_process_impact,
    build_telemetry_context,
    ask_ai_assistant,
)


# =========================================================
# CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="SoftSense | Smart PC Monitor",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = os.getenv(
    "SOFTSENSE_API_URL",
    "http://127.0.0.1:5000/api/telemetry",
)

REFRESH_SECONDS = 5
MAX_HISTORY = 60


# =========================================================
# STYLING
# =========================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b1120;
        color: #e5e7eb;
    }

    [data-testid="stMetric"] {
        background: #111c30;
        border: 1px solid #263750;
        padding: 18px;
        border-radius: 12px;
    }

    [data-testid="stMetricLabel"] {
        color: #9caec4;
    }

    h1, h2, h3 {
        color: #f8fafc;
    }

    .softsense-subtitle {
        color: #9caec4;
        font-size: 15px;
        margin-bottom: 20px;
    }

    div[data-testid="stTabs"] button {
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def to_number(value, default=0.0):
    """Convert telemetry values to numbers safely."""
    try:
        if value is None:
            def to_number(value, default=0.0):
    """Convert telemetry values to numbers safely."""
    try:
        if value is None:
            return default

        if isinstance(value, str):
            value = value.replace(",", "").replace("%", "").strip()

        if value == "":
            return default

        return float(value)

    except (ValueError, TypeError):
        return default