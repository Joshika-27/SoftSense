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
            return default

        if isinstance(value, str):
            value = value.replace(",", "").replace("%", "").strip()

        if value == "":
            return default

        return float(value)

    except (ValueError, TypeError):
        return default


def first_value(source, keys, default=None):
    """Return the first non-empty value found in a dictionary."""
    if not isinstance(source, dict):
        return default

    for key in keys:
        value = source.get(key)

        if value is not None and value != "":
            return value

    return default


def get_section(payload, names):
    """Find a nested telemetry section."""
    if not isinstance(payload, dict):
        return {}

    for name in names:
        section = payload.get(name)

        if isinstance(section, dict):
            return section

    return {}


def get_application_list(payload):
    """Extract process/application records from common payload formats."""
    if not isinstance(payload, dict):
        return []

    candidates = [
        payload.get("applications"),
        payload.get("apps"),
        payload.get("processes"),
        payload.get("top_processes"),
        payload.get("top_applications"),
    ]

    system = get_section(
        payload,
        ["system", "system_metrics", "metrics"],
    )

    candidates.extend([
        system.get("applications"),
        system.get("apps"),
        system.get("processes"),
    ])

    for candidate in candidates:
        if isinstance(candidate, list):
            return candidate

        if isinstance(candidate, dict):
            records = []

            for name, details in candidate.items():
                if isinstance(details, dict):
                    record = details.copy()
                    record.setdefault("name", name)
                    records.append(record)

            if records:
                return records

    return []


def classify_process(name):
    """Basic process classification; unknown processes remain background."""
    name = Path(str(name)).name.lower()

    user_apps = {
        "chrome.exe", "msedge.exe", "firefox.exe",
        "code.exe", "winword.exe", "excel.exe",
        "powerpnt.exe", "teams.exe", "zoom.exe",
        "discord.exe", "spotify.exe", "notepad++.exe",
        "acrord32.exe", "vlc.exe",
    }

    system_processes = {
        "system", "system idle process", "smss.exe",
        "csrss.exe", "wininit.exe", "services.exe",
        "lsass.exe", "winlogon.exe", "svchost.exe",
        "dwm.exe", "fontdrvhost.exe", "registry",
        "memory compression",
    }

    if name in user_apps:
        return "User app"

    if name in system_processes:
        return "System process"

    return "Background process"


def normalise_applications(payload):
    """Convert application telemetry into consistent dashboard columns."""
    raw_apps = get_application_list(payload)
    cleaned = []

    for app in raw_apps:
        if not isinstance(app, dict):
            continue

        name = first_value(
            app,
            ["name", "application", "process_name", "process", "exe"],
            "Unknown process",
        )

        cpu = to_number(first_value(
            app,
            ["CPU (%)", "cpu_percent", "cpu", "cpu_usage", "CPU"],
            0,
        ))

        memory_percent = to_number(first_value(
            app,
            ["Memory (%)", "memory_percent", "memory_pct", "mem_percent"],
            0,
        ))

        memory_mb = to_number(first_value(
            app,
            [
                "Memory (MB)", "memory_mb", "memory_mb_used",
                "memory_used_mb", "mem_mb",
            ],
            0,
        ))

        process_count = to_number(first_value(
            app,
            ["Process count", "process_count", "count"],
            1,
        ), 1)

        impact = to_number(first_value(
            app,
            [
                "Impact score", "resource_impact_score",
                "impact_score", "resource_impact", "impact",
            ],
            cpu + memory_percent,
        ))

        cleaned.append({
            "Application": str(name),
            "Category": classify_process(name),
            "CPU (%)": round(cpu, 2),
            "Memory (%)": round(memory_percent, 2),
            "Memory (MB)": round(memory_mb, 2),
            "Process count": int(process_count),
            "Impact score": round(impact, 2),
        })

    return sorted(
        cleaned,
        key=lambda item: item["Impact score"],
        reverse=True,
    )


def normalise_telemetry(payload):
    """Convert live telemetry into a consistent structure."""
    if not isinstance(payload, dict):
        payload = {}

    system = get_section(
        payload,
        ["system", "system_metrics", "metrics", "telemetry"],
    )

    source = {**payload, **system}

    hostname = first_value(
        source,
        ["hostname", "host_name", "computer_name", "device_name", "computer"],
        "Unknown device",
    )

    cpu = to_number(first_value(
        source,
        ["cpu_percent", "cpu_usage", "cpu", "CPU (%)"],
        0,
    ))

    memory = to_number(first_value(
        source,
        ["memory_percent", "ram_percent", "memory_usage", "memory", "RAM (%)"],
        0,
    ))

    disk = to_number(first_value(
        source,
        ["disk_percent", "disk_usage", "disk", "Disk (%)"],
        0,
    ))

    if isinstance(source.get("cpu"), dict):
        cpu = to_number(first_value(
            source["cpu"],
            ["percent", "usage", "value"],
            cpu,
        ))

    if isinstance(source.get("memory"), dict):
        memory = to_number(first_value(
            source["memory"],
            ["percent", "usage", "value"],
            memory,
        ))

    if isinstance(source.get("disk"), dict):
        disk = to_number(first_value(
            source["disk"],
            ["percent", "usage", "value"],
            disk,
        ))

    download_kbs = to_number(first_value(
        source,
        ["network_download_kbs", "download_kbs", "rx_kbs"],
        0,
    ))

    upload_kbs = to_number(first_value(
        source,
        ["network_upload_kbs", "upload_kbs", "tx_kbs"],
        0,
    ))

    memory_used_gb = to_number(first_value(
        source,
        ["memory_used_gb", "ram_used_gb"],
        0,
    ))

    memory_available_gb = to_number(first_value(
        source,
        ["memory_available_gb", "ram_available_gb"],
        0,
    ))

    disk_used_gb = to_number(first_value(
        source,
        ["disk_used_gb", "used_disk_gb"],
        0,
    ))

    disk_free_gb = to_number(first_value(
        source,
        ["disk_free_gb", "free_disk_gb"],
        0,
    ))

    applications = normalise_applications(payload)

    return {
        "hostname": str(hostname),
        "cpu": cpu,
        "memory": memory,
        "disk": disk,
        "download_kbs": download_kbs,
        "upload_kbs": upload_kbs,
        "memory_used_gb": memory_used_gb,
        "memory_available_gb": memory_available_gb,
        "disk_used_gb": disk_used_gb,
        "disk_free_gb": disk_free_gb,
        "applications": applications,
        "timestamp": first_value(
            payload,
            ["timestamp", "time", "datetime", "collected_at"],
            datetime.now().isoformat(timespec="seconds"),
        ),
        "raw": payload,
    }


def get_demo_telemetry():
    """Return clearly labelled sample telemetry for cloud/demo use only."""
    return {
        "status": "demo",
        "hostname": "SoftSense Demo Device",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "system": {
            "cpu_percent": 42.5,
            "memory_percent": 68.0,
            "disk_percent": 73.0,
            "memory_used_gb": 5.44,
            "memory_available_gb": 2.56,
            "disk_used_gb": 365.0,
            "disk_free_gb": 135.0,
            "network_download_kbs": 120.5,
            "network_upload_kbs": 34.2,
        },
        "applications": [
            {
                "name": "chrome.exe",
                "cpu_percent": 18.5,
                "memory_percent": 22.0,
                "memory_mb": 1450.0,
                "process_count": 8,
                "impact_score": 40.5,
            },
            {
                "name": "code.exe",
                "cpu_percent": 12.0,
                "memory_percent": 14.0,
                "memory_mb": 920.0,
                "process_count": 4,
                "impact_score": 26.0,
            },
            {
                "name": "python.exe",
                "cpu_percent": 7.5,
                "memory_percent": 8.0,
                "memory_mb": 520.0,
                "process_count": 2,
                "impact_score": 15.5,
            },
        ],
    }


def fetch_telemetry():
    """Fetch current data from the Flask backend."""
    try:
        response = requests.get(API_URL, timeout=3)
        response.raise_for_status()
        payload = response.json()

        if not isinstance(payload, dict):
            return None, "The telemetry API returned an unexpected format."

        return normalise_telemetry(payload), None

    except requests.RequestException as error:
        return None, (
            f"Could not connect to the SoftSense backend at {API_URL}. "
            f"Start the backend and try again. Details: {error}"
        )

    except ValueError:
        return None, "The telemetry API returned invalid JSON."
    # =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("💻 SoftSense")
st.sidebar.caption("Smart PC monitoring and assistance")

developer_mode = st.sidebar.toggle(
    "Developer mode",
    value=False,
    help="Show the raw telemetry returned by the backend.",
)

auto_refresh = st.sidebar.toggle(
    "Auto-refresh",
    value=True,
    help="Refresh live system metrics automatically.",
)

refresh_seconds = st.sidebar.slider(
    "Refresh interval (seconds)",
    min_value=3,
    max_value=30,
    value=REFRESH_SECONDS,
    disabled=not auto_refresh,
)

if st.sidebar.button("Refresh now", use_container_width=True):
    st.rerun()


# =========================================================
# LOAD TELEMETRY
# =========================================================

data, telemetry_error = fetch_telemetry()
DEMO_MODE = data is None

if DEMO_MODE:
    demo_payload = get_demo_telemetry()
    data = normalise_telemetry(demo_payload)
    data["raw"] = demo_payload


# =========================================================
# PAGE HEADER
# =========================================================

st.title("SoftSense")

st.markdown(
    '<div class="softsense-subtitle">'
    'Live system monitoring, predictive warnings, and intelligent assistance'
    '</div>',
    unsafe_allow_html=True,
)

if DEMO_MODE:
    st.warning(
        "DEMO MODE — The backend is unavailable, so SoftSense is showing "
        "illustrative sample values. These are NOT readings from your computer. "
        "Live monitoring will resume when the backend is reachable."
    )
else:
    st.success(
        "LIVE MODE — Connected to the SoftSense telemetry backend."
    )

st.caption(
    f'Monitored device: **{data["hostname"]}**  ·  '
    f'Last telemetry timestamp: {data["timestamp"]}'
)

if DEMO_MODE and telemetry_error:
    with st.expander("Why am I seeing demo data?"):
        st.code(telemetry_error)
        st.write(
            "On Streamlit Cloud, 127.0.0.1 refers to the cloud app container, "
            "not your laptop. To monitor your actual PC remotely, the Flask "
            "backend and telemetry agent must be configured securely."
        )


# =========================================================
# LIVE SYSTEM OVERVIEW
# =========================================================

st.header("Live System Overview")

metric_columns = st.columns(5)

metric_columns[0].metric(
    "CPU Usage",
    f'{data["cpu"]:.1f}%',
)

metric_columns[1].metric(
    "RAM Usage",
    f'{data["memory"]:.1f}%',
)

metric_columns[2].metric(
    "Disk Usage",
    f'{data["disk"]:.1f}%',
)

metric_columns[3].metric(
    "Download Speed",
    f'{data["download_kbs"]:.2f} KB/s',
)

metric_columns[4].metric(
    "Upload Speed",
    f'{data["upload_kbs"]:.2f} KB/s',
)

if data["memory_used_gb"] or data["memory_available_gb"]:
    st.caption(
        f'RAM used: {data["memory_used_gb"]:.2f} GB  ·  '
        f'RAM available: {data["memory_available_gb"]:.2f} GB'
    )

if data["disk_used_gb"] or data["disk_free_gb"]:
    st.caption(
        f'Disk used: {data["disk_used_gb"]:.2f} GB  ·  '
        f'Free disk space: {data["disk_free_gb"]:.2f} GB'
    )


# =========================================================
# RESOURCE TRENDS
# =========================================================

st.divider()
st.header("Resource Trends")

if "softsense_history" not in st.session_state:
    st.session_state["softsense_history"] = []

history = st.session_state["softsense_history"]

history.append({
    "time": datetime.now(),
    "CPU": data["cpu"],
    "RAM": data["memory"],
    "Disk": data["disk"],
})

if len(history) > MAX_HISTORY:
    history[:] = history[-MAX_HISTORY:]

trend_metric = st.radio(
    "Choose a metric",
    ["CPU", "RAM", "Disk"],
    horizontal=True,
)

trend_df = pd.DataFrame(history)

if not trend_df.empty:
    fig = px.line(
        trend_df,
        x="time",
        y=trend_metric,
        markers=False,
        title=f"{trend_metric} usage over recent readings",
    )

    fig.update_layout(
        height=350,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis_title="Time",
        yaxis_title="Usage (%)",
        xaxis=dict(nticks=5, tickformat="%H:%M:%S"),
        yaxis=dict(range=[0, 100]),
        paper_bgcolor="#0b1120",
        plot_bgcolor="#0b1120",
        font=dict(color="#e5e7eb"),
    )

    st.plotly_chart(fig, use_container_width=True)
    # =========================================================
# APPLICATION MONITORING
# =========================================================

st.divider()
st.header("Application Monitoring")

apps_df = pd.DataFrame(data["applications"])

if apps_df.empty:
    st.info(
        "No application telemetry is available. Check that live_agent.py "
        "is sending application records."
    )
else:
    st.subheader("Applications by resource impact")

    chart_df = apps_df.head(10).copy()

    fig = px.bar(
        chart_df.sort_values("Impact score"),
        x="Impact score",
        y="Application",
        orientation="h",
        color="Category",
        title="Top applications by relative resource impact",
    )

    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="#0b1120",
        plot_bgcolor="#0b1120",
        font=dict(color="#e5e7eb"),
        yaxis_title="Application",
        xaxis_title="Impact score",
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Process details")

    st.dataframe(
        apps_df,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Recommended next steps")

    significant_apps = apps_df[
        (apps_df["CPU (%)"] >= 20)
        | (apps_df["Memory (%)"] >= 5)
        | (apps_df["Memory (MB)"] >= 500)
    ].head(5)

    if significant_apps.empty:
        st.success(
            "No monitored application crossed the selected thresholds."
        )

    for _, app in significant_apps.iterrows():
        name = app["Application"]
        category = app["Category"]

        with st.expander(f'{name} — {category}'):
            st.write(
                f'CPU: {app["CPU (%)"]:.1f}%  ·  '
                f'Memory: {app["Memory (MB)"]:.1f} MB  ·  '
                f'Impact score: {app["Impact score"]:.2f}'
            )

            if category == "System process":
                st.warning(
                    "This is classified as a system process. "
                    "Do not terminate it based on resource usage alone."
                )

            elif category == "Background process":
                st.info(
                    "Check whether this background process belongs to an "
                    "application you use. Its purpose cannot be determined "
                    "reliably from its name alone."
                )

            else:
                st.write(
                    "This is a recognized user application. Check its settings, "
                    "startup behavior, and available updates before considering "
                    "an alternative."
                )


# =========================================================
# SMART FEATURES
# =========================================================

st.divider()
st.header("SoftSense Intelligence")

tab_predict, tab_chat, tab_cleanup, tab_battery = st.tabs([
    "Predictive Warnings",
    "AI Assistant",
    "Cleanup Advisor",
    "Battery Insights",
])


# ---------------------------------------------------------
# PREDICTIVE WARNINGS
# ---------------------------------------------------------

with tab_predict:
    st.subheader("Disk-space prediction")

    # Set a default so the AI assistant can use it even if prediction
    # has not run or is unavailable.
    disk_prediction = {
        "message": "Disk prediction is not currently available."
    }

    if DEMO_MODE:
        st.info(
            "Predictive history is disabled in demo mode because the cloud "
            "host's disk is not your laptop's disk. Connect the real telemetry "
            "backend to use disk forecasting and live resource warnings."
        )

        st.subheader("Example resource warnings")

        if (
            data["cpu"] >= 80
            or data["memory"] >= 85
            or data["disk"] >= 90
        ):
            st.warning(
                "The sample values cross a resource-warning threshold."
            )
        else:
            st.success(
                "The sample values do not cross the configured "
                "high-usage thresholds."
            )

    else:
        try:
            snapshot = record_snapshot()
            disk_prediction = predict_disk_full()
            warnings = get_resource_warnings(snapshot)

            if disk_prediction.get("status") == "warning":
                st.warning(disk_prediction.get("message", "Disk warning"))
            elif disk_prediction.get("status") == "forecast":
                st.info(disk_prediction.get("message", "Disk forecast"))
            else:
                st.info(
                    disk_prediction.get(
                        "message",
                        "No disk forecast is currently available.",
                    )
                )

            if "free_gb" in disk_prediction:
                st.metric(
                    "Available disk space",
                    f'{disk_prediction["free_gb"]:.2f} GB',
                )

            st.caption(
                "Predictions depend on historical measurements collected "
                "while SoftSense is running. A reliable forecast may require "
                "several hours or days of data."
            )

            st.subheader("Current resource warnings")

            if warnings:
                for warning in warnings:
                    st.warning(warning)
            else:
                st.success(
                    "No high CPU, RAM, or disk usage warning detected."
                )

            if data["memory"] >= 85:
                st.warning(
                    "RAM usage is high. If it continues increasing, "
                    "memory pressure may become a problem."
                )

        except Exception as error:
            st.error(
                f"Predictive analysis could not run: {error}"
            )
            # ---------------------------------------------------------
# AI ASSISTANT
# ---------------------------------------------------------

with tab_chat:
    st.subheader("Ask SoftSense")

    st.caption(
        "Ask questions such as 'Why is my PC slow?' or "
        "'Which application uses the most RAM?'"
    )

    if "softsense_chat_history" not in st.session_state:
        st.session_state["softsense_chat_history"] = []

    for message in st.session_state["softsense_chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    context_snapshot = {
        "hostname": data["hostname"],
        "cpu_percent": data["cpu"],
        "ram_percent": data["memory"],
        "disk_percent": data["disk"],
        "download_kbs": data["download_kbs"],
        "upload_kbs": data["upload_kbs"],
        "timestamp": data["timestamp"],
    }

    context = build_telemetry_context(
        snapshot=context_snapshot,
        applications=data["applications"],
        disk_prediction=disk_prediction,
    )

    question = st.chat_input(
        "Ask a question about your PC...",
        key="softsense_chat_input",
    )

    if question:
        st.session_state["softsense_chat_history"].append({
            "role": "user",
            "content": question,
        })

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Analysing telemetry..."):
                try:
                    answer = ask_ai_assistant(question, context)

                    if not answer:
                        answer = (
                            "The assistant did not return a response. "
                            "Check your API configuration."
                        )

                except Exception as error:
                    answer = (
                        "The AI assistant could not respond. "
                        f"Details: {error}"
                    )

                st.markdown(answer)

        st.session_state["softsense_chat_history"].append({
            "role": "assistant",
            "content": answer,
        })

    if st.button("Clear chat history", key="clear_softsense_chat"):
        st.session_state["softsense_chat_history"] = []
        st.rerun()


# ---------------------------------------------------------
# CLEANUP ADVISOR
# ---------------------------------------------------------

with tab_cleanup:
    st.subheader(
        "Find files that may be using unnecessary storage"
    )

    if DEMO_MODE:
        st.info(
            "File scanning is disabled in demo mode. A cloud deployment "
            "can only see files on its own server, not the files on your "
            "laptop. Connect a secure live agent/backend before using "
            "this feature on your PC."
        )

    else:
        home = Path.home()
        downloads = home / "Downloads"
        desktop = home / "Desktop"

        folder_options = {}

        if downloads.exists():
            folder_options["Downloads"] = str(downloads)

        if desktop.exists():
            folder_options["Desktop"] = str(desktop)

        if folder_options:
            selected_names = st.multiselect(
                "Select folders to scan",
                options=list(folder_options.keys()),
                default=(
                    ["Downloads"]
                    if "Downloads" in folder_options
                    else []
                ),
            )

            selected_folders = [
                folder_options[name]
                for name in selected_names
            ]

            minimum_mb = st.slider(
                "Minimum file size (MB)",
                min_value=10,
                max_value=1000,
                value=100,
                step=10,
            )

            col_large, col_duplicate, col_old = st.columns(3)

            with col_large:
                scan_large = st.button(
                    "Find large files",
                    use_container_width=True,
                )

            with col_duplicate:
                scan_duplicate = st.button(
                    "Find duplicates",
                    use_container_width=True,
                )

            with col_old:
                scan_old = st.button(
                    "Find old downloads",
                    use_container_width=True,
                )

            if scan_large:
                if selected_folders:
                    with st.spinner("Scanning for large files..."):
                        results = scan_large_files(
                            selected_folders,
                            minimum_mb=minimum_mb,
                        )

                    if results:
                        st.dataframe(
                            pd.DataFrame(results),
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.info(
                            "No files matching that size were found."
                        )
                else:
                    st.warning("Select at least one folder.")

            if scan_duplicate:
                if selected_folders:
                    with st.spinner("Comparing file hashes..."):
                        results = scan_duplicates(selected_folders)

                    if results:
                        st.dataframe(
                            pd.DataFrame(results),
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.info("No duplicate files were detected.")
                else:
                    st.warning("Select at least one folder.")

            if scan_old:
                if downloads.exists():
                    with st.spinner("Checking old Downloads..."):
                        results = scan_old_downloads(
                            str(downloads),
                            older_than_days=90,
                        )

                    if results:
                        st.dataframe(
                            pd.DataFrame(results),
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.info(
                            "No Downloads files older than 90 days were found."
                        )
                else:
                    st.warning("Downloads folder not found.")

        else:
            st.info("No supported user folders were found.")

        st.warning(
            "SoftSense only reports files. Review them before deleting "
            "anything. No files are deleted automatically."
        )


# ---------------------------------------------------------
# BATTERY INSIGHTS
# ---------------------------------------------------------

with tab_battery:
    st.subheader("Battery status")

    if DEMO_MODE:
        st.info(
            "Battery readings are unavailable in demo mode because "
            "Streamlit Cloud cannot read your laptop's battery. The "
            "application impact table below uses sample application data."
        )

        if data["applications"]:
            impact = estimate_process_impact(data["applications"])

            if impact:
                st.dataframe(
                    pd.DataFrame(impact[:10]),
                    use_container_width=True,
                    hide_index=True,
                )

        st.caption(
            "Relative CPU/memory impact is not a measurement "
            "of actual battery drain."
        )

    else:
        try:
            battery = get_battery_insights()

            if not battery["available"]:
                st.info(battery["message"])

            else:
                b1, b2, b3 = st.columns(3)

                b1.metric(
                    "Battery level",
                    f'{battery["percent"]:.0f}%',
                )

                b2.metric(
                    "Power status",
                    (
                        "Plugged in"
                        if battery["plugged_in"]
                        else "On battery"
                    ),
                )

                b3.metric(
                    "Estimated remaining time",
                    battery["remaining_time"],
                )

            st.subheader("Battery health")

            health = get_windows_battery_health()

            if health["available"]:
                st.metric(
                    "Estimated battery health",
                    f'{health["health_percent"]:.1f}%',
                )

                st.caption(
                    f'Original capacity: '
                    f'{health["design_capacity_mwh"]:,} mWh · '
                    f'Current full-charge capacity: '
                    f'{health["full_charge_capacity_mwh"]:,} mWh'
                )

            else:
                st.info(health["message"])

            st.subheader(
                "Applications with the highest resource impact"
            )

            if data["applications"]:
                impact = estimate_process_impact(
                    data["applications"]
                )

                if impact:
                    st.dataframe(
                        pd.DataFrame(impact[:10]),
                        use_container_width=True,
                        hide_index=True,
                    )

                    st.caption(
                        "This ranking estimates relative CPU and memory "
                        "impact. It does not measure each application's "
                        "actual battery drain."
                    )

                else:
                    st.info(
                        "Application usage data is not available."
                    )

            else:
                st.info(
                    "No application telemetry is available."
                )

        except Exception as error:
            st.error(
                f"Battery analysis could not run: {error}"
            )


# =========================================================
# DEVELOPER MODE
# =========================================================

if developer_mode:
    with st.expander("Raw telemetry payload"):
        st.json(data["raw"])


# =========================================================
# HOW IT WORKS
# =========================================================

with st.expander("How SoftSense works"):
    st.markdown(
        """
        **Live monitoring:** In live mode, the agent collects system and
        application metrics and sends them to the Flask backend. In demo
        mode, displayed telemetry values are sample data, not readings
        from your PC.

        **Predictive warnings:** SoftSense stores historical measurements
        and estimates disk-space trends. Forecasts need sufficient history.

        **AI assistant:** The assistant uses current telemetry to explain
        potential performance problems. It requires a configured API key.

        **Cleanup advisor:** In local/live mode, scans selected folders
        for large files, older downloads, and duplicates. It is disabled
        in cloud demo mode because cloud hosting cannot access files on
        your laptop.

        **Battery insights:** In local/live mode, displays available
        battery data. It does not read your laptop's battery in cloud
        demo mode.

        SoftSense provides recommendations. It does not automatically
        terminate processes or delete files.
        """
    )


# =========================================================
# AUTO REFRESH
# =========================================================

if auto_refresh:
    time.sleep(refresh_seconds)
    st.rerun()