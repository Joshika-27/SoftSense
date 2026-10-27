import psutil
import requests
import time
import os
from datetime import datetime


SERVER_URL = "http://10.213.225.168:5000/api/telemetry"

INTERVAL = 3

MY_PID = os.getpid()


def collect_process_data():

    applications = {}

    for process in psutil.process_iter(
        ["pid", "name", "cpu_percent", "memory_percent", "memory_info"]
    ):

        try:

            pid = process.info["pid"]

            if pid == MY_PID:
                continue

            name = process.info["name"]

            if not name:
                continue

            cpu = process.info["cpu_percent"] or 0.0
            memory_percent = process.info["memory_percent"] or 0.0

            memory_mb = 0.0

            if process.info["memory_info"]:
                memory_mb = process.info["memory_info"].rss / (1024 * 1024)

            if name not in applications:

                applications[name] = {
                    "name": name,
                    "cpu_percent": 0.0,
                    "memory_percent": 0.0,
                    "memory_mb": 0.0,
                    "process_count": 0
                }

            applications[name]["cpu_percent"] += cpu
            applications[name]["memory_percent"] += memory_percent
            applications[name]["memory_mb"] += memory_mb
            applications[name]["process_count"] += 1

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):
            continue

    application_list = list(applications.values())

    for app in application_list:

        cpu_score = min(app["cpu_percent"] / 100, 1.0)
        memory_score = min(app["memory_percent"] / 100, 1.0)

        app["resource_impact_score"] = round(
            (cpu_score * 0.6) + (memory_score * 0.4),
            3
        )

    application_list.sort(
        key=lambda x: x["resource_impact_score"],
        reverse=True
    )

    return application_list[:10]


def collect_telemetry():

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(os.path.abspath(os.sep))
    network = psutil.net_io_counters()

    applications = collect_process_data()

    telemetry = {

        "timestamp": datetime.now().isoformat(),

        "hostname": os.environ.get(
            "COMPUTERNAME",
            "Unknown"
        ),

        "cpu_percent": psutil.cpu_percent(
            interval=1
        ),

        "memory_percent": memory.percent,

        "memory_used_gb": round(
            memory.used / (1024 ** 3),
            2
        ),

        "memory_available_gb": round(
            memory.available / (1024 ** 3),
            2
        ),

        "disk_percent": disk.percent,

        "network_tx_mb": round(
            network.bytes_sent / (1024 ** 2),
            2
        ),

        "network_rx_mb": round(
            network.bytes_recv / (1024 ** 2),
            2
        ),

        "applications": applications
    }

    return telemetry


def send_telemetry(data):

    try:

        response = requests.post(
            SERVER_URL,
            json=data,
            timeout=5
        )

        if response.status_code == 200:

            print(
                "✓ Telemetry sent to SoftSense server"
            )

        else:

            print(
                f"✗ Server returned HTTP {response.status_code}"
            )

            print(response.text)

    except requests.exceptions.ConnectionError:

        print(
            "✗ Could not connect to SoftSense backend"
        )

    except requests.exceptions.Timeout:

        print(
            "✗ Backend request timed out"
        )

    except Exception as error:

        print(
            f"✗ Sending error: {error}"
        )


def print_telemetry(data):

    print()
    print("=" * 60)

    print(
        "Time:",
        data["timestamp"]
    )

    print(
        "Computer:",
        data["hostname"]
    )

    print()

    print(
        f"CPU:              {data['cpu_percent']:.1f}%"
    )

    print(
        f"Memory:           {data['memory_percent']:.1f}%"
    )

    print(
        f"Memory Used:      {data['memory_used_gb']:.2f} GB"
    )

    print(
        f"Memory Available:  {data['memory_available_gb']:.2f} GB"
    )

    print(
        f"Disk:             {data['disk_percent']:.1f}%"
    )

    print(
        f"Network TX:       {data['network_tx_mb']:.2f} MB"
    )

    print(
        f"Network RX:       {data['network_rx_mb']:.2f} MB"
    )

    print()

    print("Top Applications:")

    for app in data["applications"]:

        print(
            f"  {app['name']:<30}"
            f" CPU: {app['cpu_percent']:>6.1f}%"
            f" RAM: {app['memory_percent']:>6.1f}%"
            f" {app['memory_mb']:>9.1f} MB"
            f" Processes: {app['process_count']}"
        )

    print("=" * 60)


def main():

    print("=" * 60)
    print("              SOFTSENSE LIVE AGENT")
    print("=" * 60)

    print()
    print(
        "Sending telemetry to:",
        SERVER_URL
    )

    print()
    print("Agent is monitoring this computer...")
    print()

    # Initialize process CPU measurements
    for process in psutil.process_iter():

        try:
            process.cpu_percent(None)
        except:
            pass

    time.sleep(1)

    while True:

        try:

            telemetry = collect_telemetry()

            print_telemetry(telemetry)

            send_telemetry(telemetry)

            time.sleep(INTERVAL)

        except KeyboardInterrupt:

            print()
            print("SoftSense Live Agent stopped.")
            break

        except Exception as error:

            print(
                f"Agent error: {error}"
            )

            time.sleep(INTERVAL)


if __name__ == "__main__":
    main()