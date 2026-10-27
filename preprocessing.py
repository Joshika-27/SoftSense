import pandas as pd

# Load the datasets
node_on = pd.read_csv("data/node_telemetry_pods_on.csv")
node_off = pd.read_csv("data/node_telemetry_pods_off.csv")

pod_on = pd.read_csv("data/pod_telemetry_pods_on.csv")
pod_off = pd.read_csv("data/pod_telemetry_pods_off.csv")

# Convert timestamp to proper date-time format
node_on["timestamp"] = pd.to_datetime(node_on["timestamp"])
node_off["timestamp"] = pd.to_datetime(node_off["timestamp"])

pod_on["timestamp"] = pd.to_datetime(pod_on["timestamp"])
pod_off["timestamp"] = pd.to_datetime(pod_off["timestamp"])

# Remove exact duplicate rows
node_on = node_on.drop_duplicates()
node_off = node_off.drop_duplicates()

pod_on = pod_on.drop_duplicates()
pod_off = pod_off.drop_duplicates()

print("Preprocessing completed successfully!")

print("\nAfter removing duplicates:")
print("Node ON:", node_on.shape)
print("Node OFF:", node_off.shape)
print("Pod ON:", pod_on.shape)
print("Pod OFF:", pod_off.shape)
# Save cleaned datasets
node_on.to_csv("processed/node_on_clean.csv", index=False)
node_off.to_csv("processed/node_off_clean.csv", index=False)

pod_on.to_csv("processed/pod_on_clean.csv", index=False)
pod_off.to_csv("processed/pod_off_clean.csv", index=False)

print("\nCleaned files saved successfully!")