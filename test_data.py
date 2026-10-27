import pandas as pd

pod_on = pd.read_csv("processed/pod_on_clean.csv")

resources = ["CPU (%)", "MEM (B)", "Energy (watts)"]

average_usage = pod_on.groupby("pod_name")[resources].mean()

print("========== SOFTSENSE WORKLOAD INSIGHTS ==========\n")

highest_cpu = average_usage["CPU (%)"].idxmax()
highest_memory = average_usage["MEM (B)"].idxmax()
highest_energy = average_usage["Energy (watts)"].idxmax()

print(
    f"Highest average CPU usage: {highest_cpu} "
    f"({average_usage.loc[highest_cpu, 'CPU (%)']:.6f}%)"
)

print(
    f"Highest average memory usage: {highest_memory} "
    f"({average_usage.loc[highest_memory, 'MEM (B)'] / (1024 * 1024):.2f} MB)"
)

print(
    f"Highest average energy usage: {highest_energy} "
    f"({average_usage.loc[highest_energy, 'Energy (watts)']:.2f} W)"
)



