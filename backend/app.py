import streamlit as st
import requests
import time

# =========================================================
# SOFTSENSE LIVE DASHBOARD
# =========================================================

st.set_page_config(
    page_title="SoftSense",
    page_icon="🧠",
    layout="wide"
)

BACKEND_URL = "http://127.0.0.1:5000/api/telemetry"


# =========================================================
# STYLE
# =========================================================

st.html("""
<style>

.stApp {
    background: linear-gradient(135deg, #07111f, #0d1729, #111b32);
    color: white;
}

.block-container {
    padding-top: 2rem;
    padding-left: 3rem;
    padding-right: 3rem;
}

.title {
    font-size: 42px;
    font-weight: 800;
    letter-spacing: 3px;
}

.subtitle {
    color: #9aa8bd;
    font-size: 16px;
    margin-bottom: 20px;
}

.live {
    display: inline-block;
    padding: 7px 15px;
    border-radius: 20px;
    background: rgba(50, 220, 140, 0.15);
    border: 1px solid rgba(50, 220, 140, 0.35);
    color: #4ade80;
    font-weight: 600;
}

.card {
    background: rgba(20, 31, 52, 0.80);
    border: 1px solid rgba(150, 170, 200, 0.18);
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 15px;
}

.card-title {
    color: #9aa8bd;
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.card-value {
    font-size: 30px;
    font-weight: 750;
    margin-top: 8px;
}

.card-info {
    color: #8e9bb0;
    font-size: 13px;
    margin-top: 5px;
}

.section {
    font-size: 24px;
    font-weight: 700;
    margin-top: 25px;
    margin-bottom: 15px;
}

.diagnosis {
    background: rgba(80, 60, 150, 0.18);
    border: 1px solid rgba(150, 120, 255, 0.25);
    border-radius: 18px;
    padding: 25px;
}

.warning {
    color: #facc15;
    font-size: 21px;
    font-weight: 700;
}

.good {
    color: #4ade80;
    font-size: 21px;
    font-weight: 700;
}

</style>
""")


# =========================================================
# GET LIVE TELEMETRY
# =========================================================

def get_telemetry():

    try:

        response = requests.get(
            BACKEND_URL,
            timeout=3
        )

        if response.status_code == 200:

            data = response.json()

            if data.get("status") == "waiting":
                return None

            return data

        return None

    except Exception:
        return None


data = get_telemetry()


# =========================================================
# HEADER
# =========================================================

st.html("""
<div class="title">SOFTSENSE</div>

<div class="subtitle">
AI-POWERED SYSTEM RESOURCE INTELLIGENCE
</div>

<div class="live">
● LIVE MONITORING
</div>
""")


# =========================================================
# CONNECTION
# =========================================================

if data is None:

    st.error(
        "SoftSense is not receiving live telemetry."
    )

    st.info(
        "Make sure the SoftSense Backend and Live Agent are running."
    )

    st.stop()


# =========================================================
# SYSTEM VALUES
# =========================================================

cpu = float(data.get("cpu_percent", 0))
memory = float(data.get("memory_percent", 0))
disk = float(data.get("disk_percent", 0))

memory_used = float(
    data.get("memory_used_gb", 0)
)

memory_available = float(
    data.get("memory_available_gb", 0)
)

network_tx = float(
    data.get("network_tx_mb", 0)
)

network_rx = float(
    data.get("network_rx_mb", 0)
)

applications = data.get(
    "applications",
    []
)


# =========================================================
# HEALTH
# =========================================================

if cpu >= 85 or memory >= 90:

    health = "High Pressure"

elif cpu >= 70 or memory >= 75:

    health = "Moderate Pressure"

else:

    health = "Normal"


# =========================================================
# SYSTEM OVERVIEW
# =========================================================

st.html("""
<div class="section">
SYSTEM OVERVIEW
</div>
""")

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.html(f"""
    <div class="card">

        <div class="card-title">
            CPU USAGE
        </div>

        <div class="card-value">
            {cpu:.1f}%
        </div>

        <div class="card-info">
            Processor utilization
        </div>

    </div>
    """)


with col2:

    st.html(f"""
    <div class="card">

        <div class="card-title">
            MEMORY
        </div>

        <div class="card-value">
            {memory:.1f}%
        </div>

        <div class="card-info">
            {memory_used:.2f} GB used
        </div>

    </div>
    """)


with col3:

    st.html(f"""
    <div class="card">

        <div class="card-title">
            DISK
        </div>

        <div class="card-value">
            {disk:.1f}%
        </div>

        <div class="card-info">
            Storage utilization
        </div>

    </div>
    """)


with col4:

    st.html(f"""
    <div class="card">

        <div class="card-title">
            SYSTEM HEALTH
        </div>

        <div class="card-value">
            {health}
        </div>

        <div class="card-info">
            Current system condition
        </div>

    </div>
    """)


# =========================================================
# FIND HIGH IMPACT APPLICATION
# =========================================================

top_app = None

if applications:

    top_app = max(
        applications,
        key=lambda x: float(
            x.get("resource_impact_score", 0)
        )
    )


# =========================================================
# DIAGNOSIS
# =========================================================

if memory >= cpu and memory >= disk:

    primary_resource = "MEMORY"
    resource_value = memory

    explanation = (
        "Memory usage is currently high. Limited available "
        "memory may reduce resources available to other "
        "applications and may contribute to slower responsiveness."
    )

elif cpu >= memory and cpu >= disk:

    primary_resource = "CPU"
    resource_value = cpu

    explanation = (
        "CPU usage is currently the largest resource pressure. "
        "Applications using significant processor time may "
        "affect overall system responsiveness."
    )

else:

    primary_resource = "DISK"
    resource_value = disk

    explanation = (
        "Disk utilization is currently the largest monitored "
        "resource factor."
    )


if resource_value >= 75:

    diagnosis_title = "⚠ POSSIBLE RESOURCE PRESSURE"
    diagnosis_class = "warning"

else:

    diagnosis_title = "✓ SYSTEM OPERATING NORMALLY"
    diagnosis_class = "good"


if top_app:

    contributor = top_app.get(
        "name",
        "Unknown"
    )

    contributor_cpu = float(
        top_app.get("cpu_percent", 0)
    )

    contributor_memory = float(
        top_app.get("memory_mb", 0)
    )

else:

    contributor = "No application identified"
    contributor_cpu = 0
    contributor_memory = 0


# =========================================================
# DIAGNOSIS DISPLAY
# =========================================================

st.html("""
<div class="section">
SYSTEM DIAGNOSIS
</div>
""")

st.html(f"""
<div class="diagnosis">

    <div class="{diagnosis_class}">
        {diagnosis_title}
    </div>

    <br>

    <b>Primary Resource:</b>
    {primary_resource}

    <br><br>

    <b>Current Usage:</b>
    {resource_value:.1f}%

    <br><br>

    <b>Likely Contributing Application:</b>
    {contributor}

    <br><br>

    <b>Application CPU:</b>
    {contributor_cpu:.1f}%

    <br>

    <b>Application Memory:</b>
    {contributor_memory:.1f} MB

    <br><br>

    <b>Why is the computer slow?</b>

    <br><br>

    {explanation}

</div>
""")


# =========================================================
# NETWORK
# =========================================================

st.html("""
<div class="section">
NETWORK ACTIVITY
</div>
""")

net1, net2 = st.columns(2)


with net1:

    st.html(f"""
    <div class="card">

        <div class="card-title">
            DATA RECEIVED
        </div>

        <div class="card-value">
            {network_rx:.2f} MB
        </div>

    </div>
    """)


with net2:

    st.html(f"""
    <div class="card">

        <div class="card-title">
            DATA SENT
        </div>

        <div class="card-value">
            {network_tx:.2f} MB
        </div>

    </div>
    """)


# =========================================================
# APPLICATIONS
# =========================================================

st.html("""
<div class="section">
TOP RESOURCE-CONSUMING APPLICATIONS
</div>
""")


if applications:

    display_apps = []

    for app in applications:

        display_apps.append({
            "Application":
                app.get("name", "Unknown"),

            "CPU %":
                round(
                    float(
                        app.get("cpu_percent", 0)
                    ),
                    1
                ),

            "RAM %":
                round(
                    float(
                        app.get("memory_percent", 0)
                    ),
                    1
                ),

            "Memory MB":
                round(
                    float(
                        app.get("memory_mb", 0)
                    ),
                    1
                ),

            "Processes":
                app.get(
                    "process_count",
                    0
                ),

            "Impact Score":
                round(
                    float(
                        app.get(
                            "resource_impact_score",
                            0
                        )
                    ),
                    3
                )
        })


    display_apps.sort(
        key=lambda x: x["Impact Score"],
        reverse=True
    )

    st.table(display_apps)

else:

    st.info(
        "No application data available."
    )


# =========================================================
# RECOMMENDATION
# =========================================================

st.html("""
<div class="section">
SOFTSENSE RECOMMENDATION
</div>
""")


if top_app:

    st.html(f"""
    <div class="card">

        <div class="card-title">
            CURRENT HIGH-IMPACT APPLICATION
        </div>

        <h3>
            {contributor}
        </h3>

        <p>
            CPU Usage: {contributor_cpu:.1f}%
        </p>

        <p>
            Memory Usage: {contributor_memory:.1f} MB
        </p>

        <br>

        <b>Recommendation Engine</b>

        <p class="card-info">
            SoftSense will identify the application's category
            and compare suitable alternatives using resource
            usage evidence before making a recommendation.
        </p>

        <p class="card-info">
            No recommendation is shown when reliable evidence
            is insufficient.
        </p>

    </div>
    """)


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "SoftSense • Live System Resource Intelligence"
)


# =========================================================
# AUTO REFRESH
# =========================================================

time.sleep(3)

st.rerun()