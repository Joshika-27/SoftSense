
import os
import csv
import time
import hashlib
from pathlib import Path
from datetime import datetime

import psutil
import requests
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
HISTORY_FILE = BASE_DIR / "smart_history.csv"


# --------------------------------------------------
# 1. RECORD HISTORICAL CPU, RAM AND DISK DATA
# --------------------------------------------------

def record_snapshot():
    """Save one local system measurement for future predictions."""
    drive = os.environ.get("SystemDrive", "C:") + "\\"

    try:
        disk = psutil.disk_usage(drive)
    except Exception:
        disk = psutil.disk_usage(os.path.abspath(os.sep))

    memory = psutil.virtual_memory()

    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "cpu_percent": psutil.cpu_percent(interval=None),
        "ram_percent": memory.percent,
        "disk_percent": disk.percent,
        "disk_free_gb": round(disk.free / (1024 ** 3), 3),
        "disk_total_gb": round(disk.total / (1024 ** 3), 3),
    }

    file_exists = HISTORY_FILE.exists()

    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=row.keys())

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)

    return row


def read_history():
    """Read saved historical measurements."""
    if not HISTORY_FILE.exists():
        return []

    try:
        with open(HISTORY_FILE, "r", newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))
    except (OSError, csv.Error):
        return []


# --------------------------------------------------
# 2. PREDICTIVE WARNINGS
# --------------------------------------------------

def predict_disk_full():
    """
    Estimate when disk space may run out based on historical
    free-space readings. Returns a message and supporting data.
    """
    history = read_history()

    if len(history) < 10:
        return {
            "status": "insufficient_data",
            "message": "Collecting disk history. A reliable prediction is not available yet.",
        }

    try:
        points = [
            (
                datetime.fromisoformat(row["timestamp"]).timestamp(),
                float(row["disk_free_gb"]),
            )
            for row in history[-500:]
        ]
    except (ValueError, KeyError, TypeError):
        return {
            "status": "insufficient_data",
            "message": "Historical disk data is incomplete.",
        }

    # Compare the first and last measurements over time.
    first_time, first_free = points[0]
    last_time, last_free = points[-1]

    elapsed_days = (last_time - first_time) / 86400
    used_increase = first_free - last_free

    if elapsed_days < 0.25:
        return {
            "status": "collecting",
            "message": "More time is needed to estimate the disk usage trend.",
        }

    daily_increase = used_increase / elapsed_days

    if daily_increase <= 0.01:
        return {
            "status": "stable",
            "message": "Disk space is not showing a clear increasing-usage trend.",
        }

    days_left = last_free / daily_increase

    if days_left < 1:
        message = "Warning: disk space may run out in less than a day at the recent rate."
    else:
        message = (
            f"At the recent rate, disk space may run out in approximately "
            f"{days_left:.0f} days."
        )

    return {
        "status": "warning" if days_left < 7 else "forecast",
        "message": message,
        "estimated_days": round(days_left, 1),
        "free_gb": last_free,
        "daily_usage_increase_gb": round(daily_increase, 3),
    }


def get_resource_warnings(snapshot):
    """Generate basic warnings from the latest readings."""
    warnings = []

    if snapshot["cpu_percent"] >= 90:
        warnings.append("CPU usage is very high.")

    if snapshot["ram_percent"] >= 85:
        warnings.append("RAM usage is high and may be approaching exhaustion.")

    if snapshot["disk_percent"] >= 90:
        warnings.append("Disk storage is nearly full.")

    return warnings


# --------------------------------------------------
# 3. CLEANUP ADVISOR
# --------------------------------------------------

def scan_large_files(folders, minimum_mb=100, max_results=100):
    """Find large files in selected folders without changing them."""
    results = []
    minimum_bytes = minimum_mb * 1024 * 1024

    for folder in folders:
        root = Path(folder).expanduser()

        if not root.exists() or not root.is_dir():
            continue

        for current_root, dirs, files in os.walk(root, onerror=lambda _error: None):
            # Avoid scanning hidden folders and common system folders.
            dirs[:] = [
                name for name in dirs
                if not name.startswith(".")
                and name.lower() not in {
                    "windows", "system32", "program files",
                    "program files (x86)", "$recycle.bin"
                }
            ]

            for filename in files:
                path = Path(current_root) / filename

                try:
                    size = path.stat().st_size

                    if size >= minimum_bytes:
                        results.append({
                            "File": str(path),
                            "Size (MB)": round(size / (1024 ** 2), 2),
                            "Modified": datetime.fromtimestamp(
                                path.stat().st_mtime
                            ).strftime("%Y-%m-%d"),
                        })
                except (OSError, PermissionError):
                    continue

                if len(results) >= max_results:
                    return sorted(
                        results,
                        key=lambda item: item["Size (MB)"],
                        reverse=True,
                    )

    return sorted(
        results,
        key=lambda item: item["Size (MB)"],
        reverse=True,
    )


def scan_old_downloads(folder, older_than_days=90):
    """List old files in Downloads; do not delete them."""
    root = Path(folder).expanduser()
    cutoff = time.time() - older_than_days * 86400
    results = []

    if not root.exists() or not root.is_dir():
        return results

    for current_root, _dirs, files in os.walk(root, onerror=lambda _error: None):
        for filename in files:
            path = Path(current_root) / filename

            try:
                stats = path.stat()

                if stats.st_mtime < cutoff:
                    results.append({
                        "File": str(path),
                        "Size (MB)": round(stats.st_size / (1024 ** 2), 2),
                        "Last modified": datetime.fromtimestamp(
                            stats.st_mtime
                        ).strftime("%Y-%m-%d"),
                    })
            except OSError:
                continue

    return sorted(results, key=lambda item: item["Size (MB)"], reverse=True)


def scan_duplicates(folders, max_results=100):
    """Find likely duplicate files by size and SHA-256 hash."""
    candidates = {}
    duplicates = []

    for folder in folders:
        root = Path(folder).expanduser()

        if not root.exists() or not root.is_dir():
            continue

        for current_root, dirs, files in os.walk(root, onerror=lambda _error: None):
            dirs[:] = [
                name for name in dirs
                if not name.startswith(".")
                and name.lower() not in {
                    "windows", "system32", "program files",
                    "program files (x86)", "$recycle.bin"
                }
            ]

            for filename in files:
                path = Path(current_root) / filename

                try:
                    size = path.stat().st_size

                    # Ignore empty and tiny files.
                    if size < 1024:
                        continue

                    candidates.setdefault(size, []).append(path)
                except OSError:
                    continue

    for size, paths in candidates.items():
        if len(paths) < 2:
            continue

        hashes = {}

        for path in paths:
            try:
                digest = hashlib.sha256()

                with open(path, "rb") as file:
                    for chunk in iter(lambda: file.read(1024 * 1024), b""):
                        digest.update(chunk)

                hashes.setdefault(digest.hexdigest(), []).append(str(path))
            except OSError:
                continue

        for matching_paths in hashes.values():
            if len(matching_paths) > 1:
                duplicates.append({
                    "Size (MB)": round(size / (1024 ** 2), 2),
                    "Matching files": " | ".join(matching_paths),
                })

                if len(duplicates) >= max_results:
                    return duplicates

    return duplicates


# --------------------------------------------------
# 4. BATTERY INSIGHTS
# --------------------------------------------------

def get_battery_insights():
    """Return battery data supported by the current computer."""
    battery = psutil.sensors_battery()

    if battery is None:
        return {
            "available": False,
            "message": "Battery information is unavailable. This may be a desktop PC or unsupported device.",
        }

    seconds = battery.secsleft

    if seconds in (psutil.POWER_TIME_UNKNOWN, psutil.POWER_TIME_UNLIMITED):
        remaining = "Unavailable"
    else:
        remaining = f"{seconds // 3600} h {(seconds % 3600) // 60} min"

    return {
        "available": True,
        "percent": battery.percent,
        "plugged_in": battery.power_plugged,
        "remaining_time": remaining,
        "message": (
            "Plugged in" if battery.power_plugged
            else "Running on battery"
        ),
    }


def estimate_process_impact(applications):
    """
    Rank processes by CPU and memory usage.
    This is a relative resource-impact estimate, NOT measured battery drain.
    """
    results = []

    for app in applications or []:
        try:
            cpu = float(app.get("CPU", app.get("cpu_percent", app.get("cpu", 0))) or 0)
            memory = float(
                app.get(
                    "Memory (MB)",
                    app.get("memory_mb", app.get("memory_mb_used", 0)),
                ) or 0
            )
        except (TypeError, ValueError):
            continue

        results.append({
            "Application": app.get("Application", app.get("name", "Unknown")),
            "CPU (%)": round(cpu, 2),
            "Memory (MB)": round(memory, 2),
            "Relative resource impact": round(cpu + memory / 100, 2),
        })

    return sorted(
        results,
        key=lambda item: item["Relative resource impact"],
        reverse=True,
    )


# --------------------------------------------------
# 5. AI ASSISTANT CHAT
# --------------------------------------------------

def build_telemetry_context(snapshot, applications, disk_prediction):
    """Create a compact summary for the AI assistant."""
    top_apps = estimate_process_impact(applications)[:5]

    return {
        "current_metrics": snapshot,
        "disk_prediction": disk_prediction,
        "highest_resource_applications": top_apps,
    }


def ask_ai_assistant(question, telemetry_context):
    """
    Ask the OpenAI API about the supplied telemetry.
    Set OPENAI_API_KEY in your environment before using this feature.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return (
            "AI chat is not configured yet. Set the OPENAI_API_KEY "
            "environment variable and restart SoftSense."
        )

    if not question or not question.strip():
        return "Please enter a question about your computer."

    prompt = (
        "You are the SoftSense PC troubleshooting assistant. "
        "Answer in simple language using the supplied telemetry. "
        "Distinguish measured facts from possible causes. "
        "Do not claim an application is the cause unless the data supports it. "
        "Never recommend deleting system files or terminating critical processes. "
        "If the data is insufficient, say so. Keep the answer concise.\n\n"
        f"Telemetry:\n{telemetry_context}\n\n"
        f"User question: {question}"
    )

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a careful computer performance assistant.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            },
            timeout=30,
        )

        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()

    except requests.RequestException as error:
        return (
            "I could not reach the AI service. Check your internet connection "
            f"and API configuration. Details: {error}"
        )
    except (KeyError, IndexError, ValueError):
        return "The AI service returned an unexpected response."

def get_windows_battery_health():
    """Estimate battery health using the Windows battery report."""
    import os
    import re
    import subprocess
    import tempfile
    from pathlib import Path

    if os.name != "nt":
        return {
            "available": False,
            "message": "Battery health reporting is supported here only on Windows.",
        }

    report_path = Path(tempfile.gettempdir()) / "softsense_battery_report.html"

    try:
        result = subprocess.run(
            [
                "powercfg",
                "/batteryreport",
                "/output",
                str(report_path),
            ],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )

        if result.returncode != 0 or not report_path.exists():
            return {
                "available": False,
                "message": "Windows could not generate the battery report.",
            }

        html = report_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        def find_capacity(label):
            pattern = (
                re.escape(label)
                + r".{0,500}?([0-9,]+)\s*mWh"
            )
            match = re.search(
                pattern,
                html,
                flags=re.IGNORECASE | re.DOTALL,
            )

            if not match:
                return None

            return int(match.group(1).replace(",", ""))

        design = find_capacity("DESIGN CAPACITY")
        full_charge = find_capacity("FULL CHARGE CAPACITY")

        if not design or not full_charge or design <= 0:
            return {
                "available": False,
                "message": (
                    "Battery capacity could not be extracted from the report."
                ),
            }

        health = min(100.0, (full_charge / design) * 100)

        return {
            "available": True,
            "health_percent": round(health, 1),
            "design_capacity_mwh": design,
            "full_charge_capacity_mwh": full_charge,
            "message": "Estimated remaining battery capacity.",
        }

    except (OSError, subprocess.SubprocessError) as error:
        return {
            "available": False,
            "message": f"Could not read battery health: {error}",
        }
