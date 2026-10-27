from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

LATEST_FILE = "live_telemetry.json"


@app.route("/", methods=["GET"])
def home():
    return "SoftSense Live Server is running."


@app.route("/telemetry", methods=["POST"])
def receive_telemetry():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "status": "error",
                "message": "No telemetry data received"
            }), 400

        data["received_at"] = datetime.now().isoformat()

        with open(LATEST_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        print("\n========================================")
        print("       SOFTSENSE TELEMETRY RECEIVED")
        print("========================================")

        print(f"Computer: {data.get('computer_name', 'Unknown')}")

        system = data.get("system", {})

        print(f"CPU:    {system.get('cpu_percent', 'N/A')}%")
        print(f"Memory: {system.get('memory_percent', 'N/A')}%")
        print(f"Disk:   {system.get('disk_percent', 'N/A')}%")

        print("----------------------------------------")
        print("Top Applications:")

        for app_data in data.get("applications", [])[:5]:
            name = app_data.get("name", "Unknown")
            cpu = app_data.get("cpu_percent", 0)
            ram = app_data.get("memory_percent", 0)

            print(
                f"  {name:<30}"
                f" CPU: {cpu:>5.1f}%"
                f" RAM: {ram:>5.1f}%"
            )

        print("========================================\n")

        return jsonify({
            "status": "success",
            "message": "Telemetry received"
        })

    except Exception as e:
        print("ERROR:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":

    print("========================================")
    print("       SOFTSENSE LIVE SERVER")
    print("========================================")
    print("Server starting...")
    print("Waiting for telemetry...")
    print("----------------------------------------")
    print("Local:   http://127.0.0.1:5000")
    print("Network: http://10.213.225.168:5000")
    print("========================================")
    print()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )