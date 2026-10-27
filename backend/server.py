from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TELEMETRY_FILE = os.path.join(
    BASE_DIR,
    "..",
    "live_telemetry.json"
)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "service": "SoftSense Backend",
        "message": "SoftSense backend is running"
    })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "SoftSense Backend",
        "time": datetime.now().isoformat()
    })


@app.route("/api/telemetry", methods=["POST"])
def receive_telemetry():

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "status": "error",
                "message": "No telemetry data received"
            }), 400

        data["received_at"] = datetime.now().isoformat()

        with open(
            TELEMETRY_FILE,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                data,
                file,
                indent=4
            )

        return jsonify({
            "status": "success",
            "message": "Telemetry received"
        })

    except Exception as error:

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


@app.route("/api/telemetry", methods=["GET"])
def get_telemetry():

    try:

        if not os.path.exists(TELEMETRY_FILE):
            return jsonify({
                "status": "waiting",
                "message": "No telemetry received yet"
            }), 200

        with open(
            TELEMETRY_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        return jsonify(data)

    except Exception as error:

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


if __name__ == "__main__":

    print("=" * 50)
    print("          SOFTSENSE BACKEND")
    print("=" * 50)
    print("Backend is starting...")
    print()
    print("Local:")
    print("http://127.0.0.1:5000")
    print()
    print("Network:")
    print("http://10.213.225.168:5000")
    print()
    print("Waiting for live telemetry...")
    print("=" * 50)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )