from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from datetime import datetime
from threading import Thread
import requests
import pyodbc
import json
import time
import os

load_dotenv()

app = Flask(__name__)

# Define the services to monitor
SERVICES = [
    {"name": "Auth Service", "url": "http://localhost:5000/auth/healthcheck"},
    {"name": "Profile Service", "url": "http://localhost:5000/profile/healthcheck"},
    {"name": "Messaging Service", "url": "http://localhost:5000/messaging/healthcheck"},
    {"name": "Friendship Service", "url": "http://localhost:5000/friendship/healthcheck"},
    {"name": "API Service", "url": "http://localhost:5000/api/healthcheck"}
]

# Configuration
LOGS_FOLDER = "logs"  # Path to your logs folder
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

MSSQL_CONN_STRING = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_HOST},{DB_PORT};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD}"

ENDPOINTS = [
    {"name": "API Server", "url": "http://localhost:5000/healthcheck"},
]

STATUS_LOG_FILE = "sync-branch/admin/status_log.json"

# Initialize the log file if it doesn't exist
if not os.path.exists(STATUS_LOG_FILE):
    with open(STATUS_LOG_FILE, "w") as f:
        json.dump({"services": {}, "database": []}, f, indent=4)


def safe_read_json(filepath):
    """Reads JSON data from a file safely."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error reading JSON file: {filepath}. Resetting to default structure.")
    return {"services": {}, "database": []}


def safe_write_json(filepath, data):
    """Writes JSON data to a file safely."""
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error writing JSON file: {e}")


def check_service_status():
    """Checks the status of each service."""
    statuses = {}
    for service in SERVICES:
        try:
            response = requests.get(service["url"], timeout=5)
            status = "Healthy" if response.status_code == 200 else "Unhealthy"
        except requests.exceptions.RequestException:
            status = "Unreachable"
        statuses[service["name"]] = status
    return statuses

def check_database_status():
    """Checks the health of the database."""
    try:
        conn = pyodbc.connect(MSSQL_CONN_STRING)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return "Healthy"
    except Exception as e:
        print(f"Database error: {e}")
        return "Unhealthy"

def log_status():
    """Logs the status of each service and the database every 5 minutes."""
    while True:
        try:
            # Get statuses for all services
            service_statuses = check_service_status()

            # Simulate database status
            database_status = check_database_status()

            # Prepare the timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Load existing data
            data = safe_read_json(STATUS_LOG_FILE)

            # Update services log
            for service, status in service_statuses.items():
                if service not in data["services"]:
                    data["services"][service] = []
                data["services"][service].append({"timestamp": timestamp, "status": status})
                data["services"][service] = data["services"][service][-100:]  # Keep only the last 100 entries

            # Update database log
            data["database"].append({"timestamp": timestamp, "status": database_status})
            data["database"] = data["database"][-100:]  # Keep only the last 100 entries

            # Write updated data back to the file
            safe_write_json(STATUS_LOG_FILE, data)

            print(f"Logged status at {timestamp}")
        except Exception as e:
            print(f"Error logging status: {e}")

        # Wait for 5 minutes (300 seconds)
        time.sleep(300)


@app.route("/status/history")
def status_history():
    """Serves historical status data."""
    try:
        data = safe_read_json(STATUS_LOG_FILE)

        # Format response for easier graph plotting
        services_history = {
            service_name: [
                {"timestamp": log["timestamp"], "status": 1 if log["status"] == "Healthy" else 0}
                for log in logs
            ]
            for service_name, logs in data["services"].items()
        }

        database_history = [
            {"timestamp": log["timestamp"], "status": 1 if log["status"] == "Healthy" else 0}
            for log in data["database"]
        ]

        return jsonify({"status": "success", "data": {"services": services_history, "database": database_history}})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    
# Endpoint to fetch server status
@app.route("/status")
def server_status():
    statuses = []
    for endpoint in ENDPOINTS:
        try:
            response = requests.get(endpoint["url"], timeout=20)  # Increase timeout as needed
            if response.status_code == 200:
                response_json = response.json()
                # Handle list response
                if isinstance(response_json, list):
                    for service_status in response_json:
                        statuses.append({
                            "name": service_status.get("name", "Unknown"),
                            "url": service_status.get("url", "Unknown"),
                            "status": service_status.get("status", "Unknown")
                        })
                else:
                    # If not a list, handle it as a single dictionary
                    statuses.append({
                        "name": response_json.get("name", "Unknown"),
                        "url": response_json.get("url", "Unknown"),
                        "status": response_json.get("status", "Unknown")
                    })
            else:
                statuses.append({
                    "name": endpoint["name"],
                    "url": endpoint["url"],
                    "status": "Unhealthy",
                    "error": f"HTTP {response.status_code}"
                })
        except requests.exceptions.RequestException as e:
            statuses.append({
                "name": endpoint["name"],
                "url": endpoint["url"],
                "status": "Unreachable",
                "error": str(e)
            })
    return jsonify(statuses)

# Endpoint to check MSSQL database health
@app.route("/database")
def database_health():
    try:
        conn = pyodbc.connect(MSSQL_CONN_STRING)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return jsonify({"status": "Healthy"})
    except Exception as e:
        print(e)
        return jsonify({"status": "Unhealthy", "error": str(e)})

# Endpoint to list log files
@app.route("/logs")
def list_logs():
    try:
        files = [f for f in os.listdir(LOGS_FOLDER) if os.path.isfile(os.path.join(LOGS_FOLDER, f))]
        return jsonify({"status": "success", "files": files})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/logs/<filename>")
def view_log_file(filename):
    try:
        file_path = os.path.join(LOGS_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify({"status": "error", "message": "Log file not found."})

        # Read the log file
        with open(file_path, "r", encoding="utf-8") as f:
            logs = f.readlines()

        # Get query parameters for filtering and pagination
        query = request.args.get("query", "").lower()  # Filter query string
        start = int(request.args.get("start", 0))  # Pagination start
        limit = int(request.args.get("limit", 50))  # Pagination limit

        # Apply filter if query is provided
        if query:
            logs = [line for line in logs if query in line.lower()]

        # Apply pagination
        total_lines = len(logs)
        logs = logs[start:start + limit]

        return jsonify({
            "status": "success",
            "logs": logs,
            "total_lines": total_lines,
            "filtered": len(logs),
            "start": start,
            "limit": limit
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# Start the status logging in a separate thread
Thread(target=log_status, daemon=True).start()

# Home page
@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=8000)
