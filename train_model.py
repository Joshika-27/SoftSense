import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os

print("=" * 60)
print("SOFTSENSE - ML ANOMALY DETECTION")
print("=" * 60)

# ---------------------------------------------------------
# 1. LOAD CLEANED DATA
# ---------------------------------------------------------

node_on = pd.read_csv("processed/node_on_clean.csv")
node_off = pd.read_csv("processed/node_off_clean.csv")

print("\nNode ON data:", node_on.shape)
print("Node OFF data:", node_off.shape)

# Combine both conditions
data = pd.concat([node_on, node_off], ignore_index=True)

print("Combined data:", data.shape)


# ---------------------------------------------------------
# 2. SELECT RESOURCE FEATURES
# ---------------------------------------------------------

features = [
    "CPU (%)",
    "MEM (%)",
    "fs (%)",
    "Energy (watts)",
    "rx (B/sec)",
    "tx (B/sec)"
]

X = data[features].copy()

print("\nFeatures used for ML:")
for feature in features:
    print("-", feature)


# ---------------------------------------------------------
# 3. HANDLE INVALID VALUES
# ---------------------------------------------------------

X = X.replace([np.inf, -np.inf], np.nan)

X = X.fillna(X.median())

print("\nMissing values after preprocessing:")
print(X.isnull().sum())


# ---------------------------------------------------------
# 4. SCALE THE FEATURES
# ---------------------------------------------------------

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)

print("\nFeature scaling completed.")


# ---------------------------------------------------------
# 5. TRAIN ISOLATION FOREST
# ---------------------------------------------------------

print("\nTraining Isolation Forest model...")

model = IsolationForest(
    n_estimators=200,
    contamination=0.05,
    random_state=42
)

model.fit(X_scaled)

print("Model training completed.")


# ---------------------------------------------------------
# 6. DETECT ANOMALIES
# ---------------------------------------------------------

predictions = model.predict(X_scaled)

# Isolation Forest:
#  1  = normal
# -1  = anomaly

data["Anomaly"] = predictions

data["Anomaly"] = data["Anomaly"].map({
    1: "Normal",
    -1: "Anomaly"
})


# ---------------------------------------------------------
# 7. DISPLAY RESULTS
# ---------------------------------------------------------

normal_count = (data["Anomaly"] == "Normal").sum()
anomaly_count = (data["Anomaly"] == "Anomaly").sum()

total = len(data)

print("\n" + "=" * 60)
print("ML RESULTS")
print("=" * 60)

print("Total records :", total)
print("Normal records:", normal_count)
print("Anomalies     :", anomaly_count)

print(
    "Anomaly percentage:",
    round((anomaly_count / total) * 100, 2),
    "%"
)


# ---------------------------------------------------------
# 8. SHOW TOP ANOMALOUS RECORDS
# ---------------------------------------------------------

print("\nSample anomalous records:")

anomalies = data[data["Anomaly"] == "Anomaly"]

print(
    anomalies[
        ["node_name", "timestamp"] + features + ["Anomaly"]
    ].head(10).to_string(index=False)
)


# ---------------------------------------------------------
# 9. SAVE ML RESULTS
# ---------------------------------------------------------

os.makedirs("processed", exist_ok=True)

data.to_csv(
    "processed/node_ml_results.csv",
    index=False
)

print("\nML results saved to:")
print("processed/node_ml_results.csv")


# ---------------------------------------------------------
# 10. SAVE MODEL AND SCALER
# ---------------------------------------------------------

joblib.dump(
    model,
    "processed/softsense_anomaly_model.pkl"
)

joblib.dump(
    scaler,
    "processed/softsense_scaler.pkl"
)

print("\nModel saved to:")
print("processed/softsense_anomaly_model.pkl")

print("\nScaler saved to:")
print("processed/softsense_scaler.pkl")


# ---------------------------------------------------------
# 11. FINAL MESSAGE
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("SOFTSENSE ML TRAINING COMPLETED SUCCESSFULLY")
print("=" * 60)