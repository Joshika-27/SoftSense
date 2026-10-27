import streamlit as st
import pandas as pd
import plotly.express as px

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="SoftSense | Resource Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

.stApp {
    background-color: #0b1120;
    color: #e5e7eb;
}

[data-testid="stSidebar"] {
    background-color: #111827;
    border-right: 1px solid #263449;
}

[data-testid="stSidebar"] * {
    color: #e5e7eb;
}

h1 {
    color: #f8fafc;
    font-size: 42px;
    font-weight: 700;
}

h2 {
    color: #f1f5f9;
    font-size: 28px;
    font-weight: 650;
}

h3 {
    color: #e2e8f0;
    font-size: 20px;
    font-weight: 600;
}

p {
    color: #cbd5e1;
    font-size: 16px;
}

[data-testid="stMetric"] {
    background-color: #111827;
    border: 1px solid #263449;
    padding: 18px;
    border-radius: 14px;
}

[data-testid="stMetricLabel"] {
    color: #94a3b8;
}

[data-testid="stMetricValue"] {
    color: #f8fafc;
}

.stDownloadButton button {
    border-radius: 8px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# LOAD DATA
# =========================================================

node_on = pd.read_csv("processed/node_on_clean.csv")
node_off = pd.read_csv("processed/node_off_clean.csv")

pod_on = pd.read_csv("processed/pod_on_clean.csv")
pod_off = pd.read_csv("processed/pod_off_clean.csv")

# Load ML results created by train_model.py
ml_results = pd.read_csv(
    "processed/node_ml_results.csv"
)


# =========================================================
# PREPARE TIMESTAMPS
# =========================================================

node_on["timestamp"] = pd.to_datetime(
    node_on["timestamp"]
)

node_off["timestamp"] = pd.to_datetime(
    node_off["timestamp"]
)

pod_on["timestamp"] = pd.to_datetime(
    pod_on["timestamp"]
)

pod_off["timestamp"] = pd.to_datetime(
    pod_off["timestamp"]
)

ml_results["timestamp"] = pd.to_datetime(
    ml_results["timestamp"]
)


# =========================================================
# COMMON VALUES
# =========================================================

cpu_on = node_on["CPU (%)"].mean()
cpu_off = node_off["CPU (%)"].mean()

memory_on = node_on["MEM (%)"].mean()
memory_off = node_off["MEM (%)"].mean()

fs_on = node_on["fs (%)"].mean()
fs_off = node_off["fs (%)"].mean()

energy_on = node_on["Energy (watts)"].mean()
energy_off = node_off["Energy (watts)"].mean()


# =========================================================
# ML SUMMARY
# =========================================================

total_ml_records = len(ml_results)

normal_records = (
    ml_results["Anomaly"] == "Normal"
).sum()

anomaly_records = (
    ml_results["Anomaly"] == "Anomaly"
).sum()

anomaly_percentage = (
    anomaly_records / total_ml_records
) * 100


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown("## ◈ SoftSense")
st.sidebar.caption("Resource Intelligence Dashboard")

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "Node Analysis",
        "Workload Analysis",
        "Time-Series Analysis",
        "Pods ON vs OFF",
        "Resource Detection",
        "ML Anomaly Detection",
        "Insights"
    ]
)

st.sidebar.markdown("---")

st.sidebar.caption(
    "Edge-Cloud Resource Usage Analysis"
)


# =========================================================
# OVERVIEW
# =========================================================

if page == "Overview":

    st.title("SoftSense")

    st.caption(
        "Edge-Cloud Resource Intelligence Dashboard"
    )

    st.write(
        "SoftSense analyses resource usage of computing "
        "nodes and workloads and converts raw telemetry "
        "into simple and understandable insights."
    )

    st.info(
        "The current implementation analyses the ENACT "
        "edge-cloud telemetry dataset. Resource patterns "
        "and anomaly detection are derived from the "
        "provided telemetry data."
    )

    st.markdown("---")

    # -----------------------------------------------------
    # SYSTEM SUMMARY
    # -----------------------------------------------------

    st.markdown("### System Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Edge Node",
            "rpi4"
        )

    with col2:
        st.metric(
            "Cloud Node",
            "vm-node"
        )

    with col3:
        st.metric(
            "Workloads",
            pod_on["pod_name"].nunique()
        )

    with col4:
        st.metric(
            "Telemetry Records",
            f"{len(node_on) + len(pod_on):,}"
        )

    st.markdown("---")

    # -----------------------------------------------------
    # RESOURCE SUMMARY
    # -----------------------------------------------------

    st.markdown(
        "### Overall Resource Usage — Pods ON"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "CPU",
            f"{cpu_on:.3f}%"
        )

    with col2:
        st.metric(
            "Memory",
            f"{memory_on:.3f}%"
        )

    with col3:
        st.metric(
            "Filesystem",
            f"{fs_on:.3f}%"
        )

    with col4:
        st.metric(
            "Energy",
            f"{energy_on:.2f} W"
        )

    st.markdown("---")

    # -----------------------------------------------------
    # ML SUMMARY
    # -----------------------------------------------------

    st.markdown("### ML Anomaly Detection Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Records Analysed",
            f"{total_ml_records:,}"
        )

    with col2:
        st.metric(
            "Normal",
            f"{normal_records:,}"
        )

    with col3:
        st.metric(
            "Anomalies",
            f"{anomaly_records:,}"
        )

    st.markdown("---")

    # -----------------------------------------------------
    # PROJECT WORKFLOW
    # -----------------------------------------------------

    st.markdown("### SoftSense Analysis Pipeline")

    st.info(
        "Telemetry Dataset → Preprocessing → "
        "Node Analysis → Workload Analysis → "
        "Time-Series Analysis → ON/OFF Comparison → "
        "Resource Detection → ML Anomaly Detection → "
        "Insights"
    )

    st.markdown("---")

    st.markdown("### What SoftSense Provides")

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            "✓ Node-level resource analysis"
        )

        st.write(
            "✓ Workload-level resource analysis"
        )

        st.write(
            "✓ CPU, memory, filesystem and network analysis"
        )

        st.write(
            "✓ ML-based anomaly detection"
        )

    with col2:

        st.write(
            "✓ Energy usage analysis"
        )

        st.write(
            "✓ Pods ON vs OFF comparison"
        )

        st.write(
            "✓ Data-driven resource pattern detection"
        )

        st.write(
            "✓ Automatic insights"
        )


# =========================================================
# NODE ANALYSIS
# =========================================================

elif page == "Node Analysis":

    st.title("Node Analysis")

    st.write(
        "Compare resource usage between the Edge node "
        "(rpi4) and Cloud node (vm-node)."
    )

    st.markdown("---")

    node_cpu = node_on.groupby(
        "node_name"
    )["CPU (%)"].mean()

    node_memory = node_on.groupby(
        "node_name"
    )["MEM (%)"].mean()

    node_fs = node_on.groupby(
        "node_name"
    )["fs (%)"].mean()

    node_energy = node_on.groupby(
        "node_name"
    )["Energy (watts)"].mean()

    st.markdown("### Node Summary")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("#### Edge Node — rpi4")

        st.metric(
            "Average CPU",
            f"{node_cpu['rpi4']:.3f}%"
        )

        st.metric(
            "Average Memory",
            f"{node_memory['rpi4']:.3f}%"
        )

        st.metric(
            "Average Energy",
            f"{node_energy['rpi4']:.2f} W"
        )

    with col2:

        st.markdown("#### Cloud Node — vm-node")

        st.metric(
            "Average CPU",
            f"{node_cpu['vm-node']:.3f}%"
        )

        st.metric(
            "Average Memory",
            f"{node_memory['vm-node']:.3f}%"
        )

        st.metric(
            "Average Energy",
            f"{node_energy['vm-node']:.2f} W"
        )

    st.markdown("---")

    st.markdown("### Average CPU Usage")

    fig_cpu = px.bar(
        x=node_cpu.index,
        y=node_cpu.values,
        labels={
            "x": "Node",
            "y": "CPU Usage (%)"
        },
        title="CPU Usage by Node"
    )

    st.plotly_chart(
        fig_cpu,
        use_container_width=True
    )

    st.markdown("### Average Memory Usage")

    fig_memory = px.bar(
        x=node_memory.index,
        y=node_memory.values,
        labels={
            "x": "Node",
            "y": "Memory Usage (%)"
        },
        title="Memory Usage by Node"
    )

    st.plotly_chart(
        fig_memory,
        use_container_width=True
    )

    st.markdown("### Average Energy Usage")

    fig_energy = px.bar(
        x=node_energy.index,
        y=node_energy.values,
        labels={
            "x": "Node",
            "y": "Energy (W)"
        },
        title="Energy Usage by Node"
    )

    st.plotly_chart(
        fig_energy,
        use_container_width=True
    )

    st.markdown("### Network Throughput")

    network = node_on.groupby(
        "node_name"
    )[[
        "rx (B/sec)",
        "tx (B/sec)"
    ]].mean()

    fig_network = px.bar(
        network,
        barmode="group",
        title="Average Network Throughput"
    )

    st.plotly_chart(
        fig_network,
        use_container_width=True
    )

    st.info(
        f"CPU: {node_cpu.idxmax()} has the higher "
        f"average CPU usage."
    )

    st.info(
        f"Memory: {node_memory.idxmax()} has the higher "
        f"average memory usage."
    )

    st.info(
        f"Energy: {node_energy.idxmax()} has the higher "
        f"average energy usage."
    )


# =========================================================
# WORKLOAD ANALYSIS
# =========================================================

elif page == "Workload Analysis":

    st.title("Workload Analysis")

    st.write(
        "Analyse resource usage of individual workloads "
        "running in the edge-cloud environment."
    )

    st.markdown("---")

    average_cpu = pod_on.groupby(
        "pod_name"
    )["CPU (%)"].mean()

    average_memory = pod_on.groupby(
        "pod_name"
    )["MEM (B)"].mean()

    average_memory_mb = (
        average_memory / (1024 * 1024)
    )

    average_energy = pod_on.groupby(
        "pod_name"
    )["Energy (watts)"].mean()

    st.markdown("### Average CPU Usage by Workload")

    fig_cpu = px.bar(
        x=average_cpu.index,
        y=average_cpu.values,
        labels={
            "x": "Workload",
            "y": "CPU Usage (%)"
        }
    )

    fig_cpu.update_layout(
        xaxis_tickangle=-30
    )

    st.plotly_chart(
        fig_cpu,
        use_container_width=True
    )

    st.markdown("### Average Memory Usage by Workload")

    fig_memory = px.bar(
        x=average_memory_mb.index,
        y=average_memory_mb.values,
        labels={
            "x": "Workload",
            "y": "Memory (MB)"
        }
    )

    fig_memory.update_layout(
        xaxis_tickangle=-30
    )

    st.plotly_chart(
        fig_memory,
        use_container_width=True
    )

    st.markdown("### Average Energy Usage by Workload")

    fig_energy = px.bar(
        x=average_energy.index,
        y=average_energy.values,
        labels={
            "x": "Workload",
            "y": "Energy (W)"
        }
    )

    fig_energy.update_layout(
        xaxis_tickangle=-30
    )

    st.plotly_chart(
        fig_energy,
        use_container_width=True
    )

    st.markdown("---")

    st.markdown("### Workload Leaders")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Highest CPU",
            average_cpu.idxmax()
        )

    with col2:
        st.metric(
            "Highest Memory",
            average_memory_mb.idxmax()
        )

    with col3:
        st.metric(
            "Highest Energy",
            average_energy.idxmax()
        )

    st.markdown("---")

    st.markdown("### Workload Data")

    workload_table = pd.DataFrame({
        "Workload": average_cpu.index,
        "Average CPU (%)": average_cpu.values,
        "Average Memory (MB)": average_memory_mb.values,
        "Average Energy (W)": average_energy.values
    })

    st.dataframe(
        workload_table,
        use_container_width=True
    )

    csv = workload_table.to_csv(
        index=False
    )

    st.download_button(
        "Download Workload Results",
        csv,
        "softsense_workload_results.csv",
        "text/csv"
    )


# =========================================================
# TIME-SERIES ANALYSIS
# =========================================================

elif page == "Time-Series Analysis":

    st.title("Time-Series Analysis")

    st.write(
        "Observe how resource usage changes over time "
        "during the Pods ON condition."
    )

    st.markdown("---")

    selected_node = st.selectbox(
        "Select Node",
        sorted(node_on["node_name"].unique())
    )

    selected_node_data = node_on[
        node_on["node_name"] == selected_node
    ].sort_values("timestamp")

    st.markdown(
        "### CPU Usage Over Time"
    )

    fig_cpu = px.line(
        selected_node_data,
        x="timestamp",
        y="CPU (%)",
        title=f"CPU Usage — {selected_node}"
    )

    st.plotly_chart(
        fig_cpu,
        use_container_width=True
    )

    st.markdown(
        "### Memory Usage Over Time"
    )

    fig_memory = px.line(
        selected_node_data,
        x="timestamp",
        y="MEM (%)",
        title=f"Memory Usage — {selected_node}"
    )

    st.plotly_chart(
        fig_memory,
        use_container_width=True
    )

    st.markdown(
        "### Energy Usage Over Time"
    )

    fig_energy = px.line(
        selected_node_data,
        x="timestamp",
        y="Energy (watts)",
        title=f"Energy Usage — {selected_node}"
    )

    st.plotly_chart(
        fig_energy,
        use_container_width=True
    )

    st.markdown(
        "### Network Traffic Over Time"
    )

    fig_network = px.line(
        selected_node_data,
        x="timestamp",
        y=[
            "rx (B/sec)",
            "tx (B/sec)"
        ],
        title=f"Network Traffic — {selected_node}"
    )

    st.plotly_chart(
        fig_network,
        use_container_width=True
    )


# =========================================================
# PODS ON VS OFF
# =========================================================

elif page == "Pods ON vs OFF":

    st.title("Pods ON vs Pods OFF")

    st.write(
        "Compare resource usage during active workloads "
        "with the baseline condition."
    )

    st.markdown("---")

    comparison = pd.DataFrame({
        "Metric": [
            "CPU (%)",
            "Memory (%)",
            "Filesystem (%)",
            "Energy (W)"
        ],
        "Pods ON": [
            cpu_on,
            memory_on,
            fs_on,
            energy_on
        ],
        "Pods OFF": [
            cpu_off,
            memory_off,
            fs_off,
            energy_off
        ]
    })

    st.markdown("### Overall Comparison")

    fig = px.bar(
        comparison,
        x="Metric",
        y=[
            "Pods ON",
            "Pods OFF"
        ],
        barmode="group",
        title="Pods ON vs Pods OFF"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    cpu_change = (
        (cpu_on - cpu_off)
        / cpu_off
    ) * 100

    memory_change = (
        (memory_on - memory_off)
        / memory_off
    ) * 100

    fs_change = (
        (fs_on - fs_off)
        / fs_off
    ) * 100

    energy_change = (
        (energy_on - energy_off)
        / energy_off
    ) * 100

    st.markdown("### Percentage Change")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "CPU",
            f"{cpu_change:+.2f}%"
        )

    with col2:
        st.metric(
            "Memory",
            f"{memory_change:+.2f}%"
        )

    with col3:
        st.metric(
            "Filesystem",
            f"{fs_change:+.2f}%"
        )

    with col4:
        st.metric(
            "Energy",
            f"{energy_change:+.2f}%"
        )

    st.markdown("---")

    st.info(
        "Pods ON represents the active workload condition. "
        "Pods OFF represents the baseline condition."
    )


# =========================================================
# RESOURCE DETECTION
# =========================================================

elif page == "Resource Detection":

    st.title("Resource Detection")

    st.write(
        "SoftSense identifies unusually high workload "
        "resource usage using data-driven thresholds."
    )

    st.markdown("---")

    cpu_threshold = pod_on[
        "CPU (%)"
    ].quantile(0.95)

    memory_threshold = pod_on[
        "MEM (B)"
    ].quantile(0.95)

    energy_threshold = pod_on[
        "Energy (watts)"
    ].quantile(0.95)

    st.markdown(
        "### Automatically Calculated Thresholds"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "High CPU",
            f"{cpu_threshold:.4f}%"
        )

    with col2:

        st.metric(
            "High Memory",
            f"{memory_threshold / (1024 * 1024):.2f} MB"
        )

    with col3:

        st.metric(
            "High Energy",
            f"{energy_threshold:.2f} W"
        )

    st.caption(
        "The thresholds use the 95th percentile of "
        "observed workload telemetry."
    )

    st.markdown("---")

    high_cpu = pod_on[
        pod_on["CPU (%)"] > cpu_threshold
    ]

    high_memory = pod_on[
        pod_on["MEM (B)"] > memory_threshold
    ]

    high_energy = pod_on[
        pod_on["Energy (watts)"] > energy_threshold
    ]

    st.markdown(
        "### Detection Results"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "High CPU Records",
            f"{len(high_cpu):,}"
        )

    with col2:

        st.metric(
            "High Memory Records",
            f"{len(high_memory):,}"
        )

    with col3:

        st.metric(
            "High Energy Records",
            f"{len(high_energy):,}"
        )

    st.markdown("---")

    st.markdown(
        "### Workloads Showing High Usage"
    )

    high_usage_summary = pd.DataFrame({
        "Resource": [
            "CPU",
            "Memory",
            "Energy"
        ],
        "Number of High-Usage Records": [
            len(high_cpu),
            len(high_memory),
            len(high_energy)
        ]
    })

    st.dataframe(
        high_usage_summary,
        use_container_width=True
    )

    st.info(
        "This detection does not mean that a workload is "
        "necessarily faulty. It indicates that the observed "
        "value is unusually high compared with the dataset."
    )


# =========================================================
# ML ANOMALY DETECTION
# =========================================================

elif page == "ML Anomaly Detection":

    st.title("ML Anomaly Detection")

    st.write(
        "SoftSense uses an Isolation Forest machine-learning "
        "model to identify unusual combinations of resource "
        "usage in the telemetry data."
    )

    st.info(
        "The model learns resource-usage patterns from the "
        "provided telemetry data. An anomaly means that the "
        "combination of resource values is unusual compared "
        "with the learned patterns. It does not automatically "
        "mean that the system is faulty."
    )

    st.markdown("---")

    # -----------------------------------------------------
    # ML SUMMARY
    # -----------------------------------------------------

    st.markdown("### ML Detection Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Records",
            f"{total_ml_records:,}"
        )

    with col2:
        st.metric(
            "Normal",
            f"{normal_records:,}"
        )

    with col3:
        st.metric(
            "Anomalies",
            f"{anomaly_records:,}"
        )

    with col4:
        st.metric(
            "Anomaly Rate",
            f"{anomaly_percentage:.2f}%"
        )

    st.markdown("---")

    # -----------------------------------------------------
    # NORMAL VS ANOMALY CHART
    # -----------------------------------------------------

    st.markdown("### Normal vs Anomaly")

    anomaly_summary = pd.DataFrame({
        "Status": [
            "Normal",
            "Anomaly"
        ],
        "Records": [
            normal_records,
            anomaly_records
        ]
    })

    fig_anomaly = px.bar(
        anomaly_summary,
        x="Status",
        y="Records",
        title="ML Classification of Telemetry Records"
    )

    st.plotly_chart(
        fig_anomaly,
        use_container_width=True
    )

    st.markdown("---")

    # -----------------------------------------------------
    # ANOMALIES BY NODE
    # -----------------------------------------------------

    st.markdown("### Anomalies by Node")

    anomaly_data = ml_results[
        ml_results["Anomaly"] == "Anomaly"
    ]

    anomaly_by_node = (
        anomaly_data
        .groupby("node_name")
        .size()
        .reset_index(name="Anomaly Records")
    )

    fig_node_anomaly = px.bar(
        anomaly_by_node,
        x="node_name",
        y="Anomaly Records",
        title="Detected Anomalies by Node",
        labels={
            "node_name": "Node",
            "Anomaly Records": "Number of Anomalies"
        }
    )

    st.plotly_chart(
        fig_node_anomaly,
        use_container_width=True
    )

    st.markdown("---")

    # -----------------------------------------------------
    # ANOMALOUS RECORDS
    # -----------------------------------------------------

    st.markdown("### Detected Anomalous Records")

    display_columns = [
        "node_name",
        "timestamp",
        "CPU (%)",
        "MEM (%)",
        "fs (%)",
        "Energy (watts)",
        "rx (B/sec)",
        "tx (B/sec)",
        "Anomaly"
    ]

    st.dataframe(
        anomaly_data[
            display_columns
        ].head(100),
        use_container_width=True
    )

    st.caption(
        "The table displays the first 100 detected anomalies."
    )

    # -----------------------------------------------------
    # DOWNLOAD
    # -----------------------------------------------------

    ml_csv = ml_results.to_csv(
        index=False
    )

    st.download_button(
        "Download ML Results",
        ml_csv,
        "softsense_ml_results.csv",
        "text/csv"
    )

    st.markdown("---")

    # -----------------------------------------------------
    # EXPLANATION
    # -----------------------------------------------------

    st.markdown("### How the ML Detection Works")

    st.write(
        "1. Resource telemetry is loaded from the cleaned dataset."
    )

    st.write(
        "2. CPU, memory, filesystem, energy and network "
        "features are selected."
    )

    st.write(
        "3. The features are scaled so that they can be "
        "processed together."
    )

    st.write(
        "4. Isolation Forest learns the resource-usage patterns."
    )

    st.write(
        "5. Records that differ significantly from the learned "
        "patterns are marked as anomalies."
    )

    st.write(
        "6. SoftSense displays the detected anomalies and "
        "resource patterns in the dashboard."
    )

    st.success(
        "ML anomaly detection has been trained using the "
        "current telemetry environment. Different telemetry "
        "data can produce different learned patterns and "
        "anomaly results."
    )


# =========================================================
# INSIGHTS
# =========================================================

elif page == "Insights":

    st.title("SoftSense Insights")

    st.write(
        "Automatically generated findings from the "
        "analysed telemetry data."
    )

    st.markdown("---")

    average_cpu = pod_on.groupby(
        "pod_name"
    )["CPU (%)"].mean()

    average_memory = pod_on.groupby(
        "pod_name"
    )["MEM (B)"].mean()

    average_energy = pod_on.groupby(
        "pod_name"
    )["Energy (watts)"].mean()

    highest_cpu = average_cpu.idxmax()
    highest_memory = average_memory.idxmax()
    highest_energy = average_energy.idxmax()

    node_energy = node_on.groupby(
        "node_name"
    )["Energy (watts)"].mean()

    highest_energy_node = node_energy.idxmax()

    cpu_change = (
        (cpu_on - cpu_off)
        / cpu_off
    ) * 100

    memory_change = (
        (memory_on - memory_off)
        / memory_off
    ) * 100

    energy_change = (
        (energy_on - energy_off)
        / energy_off
    ) * 100

    st.markdown("### Key Findings")

    st.info(
        f"CPU usage was {abs(cpu_change):.2f}% "
        f"{'lower' if cpu_change < 0 else 'higher'} "
        f"during Pods ON compared with Pods OFF."
    )

    st.info(
        f"Memory usage was {abs(memory_change):.2f}% "
        f"{'lower' if memory_change < 0 else 'higher'} "
        f"during Pods ON compared with Pods OFF."
    )

    st.info(
        f"Energy usage was {abs(energy_change):.2f}% "
        f"{'lower' if energy_change < 0 else 'higher'} "
        f"during Pods ON compared with Pods OFF."
    )

    st.info(
        f"The ML model detected {anomaly_records:,} "
        f"unusual telemetry records ({anomaly_percentage:.2f}%)."
    )

    st.markdown("---")

    st.markdown("### Workload Findings")

    st.info(
        f"Highest average CPU workload: **{highest_cpu}**"
    )

    st.info(
        f"Highest average memory workload: **{highest_memory}**"
    )

    st.info(
        f"Highest average energy workload: **{highest_energy}**"
    )

    st.info(
        f"Highest average node energy usage: **{highest_energy_node}**"
    )

    st.markdown("---")

    # -----------------------------------------------------
    # PROJECT CONCLUSION
    # -----------------------------------------------------

    st.markdown("### SoftSense Conclusion")

    st.success(
        "SoftSense converts raw edge-cloud telemetry into "
        "resource comparisons, workload analysis, "
        "time-based trends, data-driven resource detection "
        "and ML-based anomaly detection."
    )

    st.markdown("---")

    # -----------------------------------------------------
    # ENVIRONMENT DEPENDENCY
    # -----------------------------------------------------

    st.markdown("### Environment-Specific Analysis")

    st.write(
        "Resource usage depends on the hardware, workloads "
        "and operating environment. SoftSense therefore "
        "derives its analysis and anomaly patterns from the "
        "input telemetry instead of assuming that one fixed "
        "resource pattern applies to every computer."
    )

    st.markdown("---")

    # -----------------------------------------------------
    # FUTURE SCOPE
    # -----------------------------------------------------

    st.markdown("### Future Scope")

    st.warning(
        "SoftSense can be extended with live telemetry "
        "collection from different computers and an intelligent "
        "recommendation module that suggests alternative "
        "applications, workloads or configurations that provide "
        "similar functionality with lower resource or energy "
        "consumption."
    )

    st.caption(
        "Live computer monitoring and alternative application "
        "recommendation are future enhancements and are not "
        "claimed as current features."
    )