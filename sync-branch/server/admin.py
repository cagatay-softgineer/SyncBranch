from flask import render_template, jsonify, request, Blueprint
from flask_httpauth import HTTPBasicAuth
from dotenv import load_dotenv
from datetime import datetime
from threading import Thread
import requests
import psutil
import pyodbc
import json
import time
import os

auth = HTTPBasicAuth()

load_dotenv()

ADMIN = os.getenv("ADMIN")
ADMIN_PWORD = os.getenv("ADMIN_PWORD")

USERS = {ADMIN: ADMIN_PWORD}

@auth.verify_password
def verify_password(username, password):
    if username in USERS and USERS[username] == password:
        return username
    return None

admin_bp = Blueprint('admin', __name__)

# Define the services to monitor
SERVICES = [
    {"name": "Auth Service", "url": "http://localhost:8080/auth/healthcheck"},
    {"name": "Profile Service", "url": "http://localhost:8080/profile/healthcheck"},
    {"name": "Messaging Service", "url": "http://localhost:8080/messaging/healthcheck"},
    {"name": "Friendship Service", "url": "http://localhost:8080/friendship/healthcheck"},
    {"name": "API Service", "url": "http://localhost:8080/api/healthcheck"},
    {"name": "Console Service", "url": "http://localhost:8080/commands/healthcheck"}
]

# Configuration
LOGS_FOLDER = "logs"  # Path to your logs folder
DB_HOST = os.getenv("PRIMARY_SQL_SERVER")
DB_PORT = os.getenv("PRIMARY_SQL_SERVER_PORT")
DB_NAME = os.getenv("PRIMARY_SQL_DATABASE")
DB_USER = os.getenv("PRIMARY_SQL_USER")
DB_PASSWORD = os.getenv("PRIMARY_SQL_PASSWORD")

MSSQL_CONN_STRING = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_HOST},{DB_PORT};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD}"

ENDPOINTS = [
    {"name": "API Server", "url": "http://localhost:8080/healthcheck"},
]

STATUS_LOG_FILE = "sync-branch/server/status_log.json"

def check_service_status():
    """Checks the status of each service."""
    statuses = {}
    for service in SERVICES:
        try:
            response = requests.get(service["url"], timeout=10)
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

# Cache to store loaded JSON and the last modified time
cache = {
    "data": None,
    "last_loaded": None,
    "last_modified": None
}

def safe_read_json_with_cache(filepath):
    """Reads JSON data from a file with caching."""
    global cache
    if not os.path.exists(filepath):
        return {"services": {}, "database": []}

    # Check if the file has been modified since the last load
    last_modified = os.path.getmtime(filepath)
    if cache["data"] is not None and cache["last_modified"] == last_modified:
        return cache["data"]  # Return cached data if file is unchanged

    # Load the file and update the cache
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
            cache["data"] = data
            cache["last_loaded"] = datetime.now()
            cache["last_modified"] = last_modified
            return data
    except json.JSONDecodeError:
        print(f"Error reading JSON file: {filepath}. Resetting to default structure.")
        return {"services": {}, "database": []}


def safe_write_json(filepath, data):
    """Writes JSON data to a file safely."""
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
        # Update the cache after writing
        cache["data"] = data
        cache["last_loaded"] = datetime.now()
        cache["last_modified"] = os.path.getmtime(filepath)
    except Exception as e:
        print(f"Error writing JSON file: {e}")


def log_status():
    """Logs the status of each service and the database every 5 minutes."""
    while True:
        try:
            # Check statuses
            service_statuses = check_service_status()
            database_status = check_database_status()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Load current data
            data = safe_read_json_with_cache(STATUS_LOG_FILE)

            # Update service logs
            for service, status in service_statuses.items():
                if service not in data["services"]:
                    data["services"][service] = []
                data["services"][service].append({"timestamp": timestamp, "status": status})
                data["services"][service] = data["services"][service][-100:]

            # Update database log
            data["database"].append({"timestamp": timestamp, "status": database_status})
            data["database"] = data["database"][-100:]

            # Save updated data
            safe_write_json(STATUS_LOG_FILE, data)

            print(f"Logged status at {timestamp}")
        except Exception as e:
            print(f"Error logging status: {e}")

        # Wait for 5 minutes
        time.sleep(300)


@admin_bp.route("/system/metrics")
@auth.login_required
def system_metrics():
    """Fetch system metrics: disk usage, RAM usage, and CPU load."""
    try:
        # Disk Usage (Total, Used, Free in percentage)
        disks = [
            {
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "percent_used": psutil.disk_usage(partition.mountpoint).percent,
            }
            for partition in psutil.disk_partitions() if psutil.disk_usage(partition.mountpoint)
        ]
        
        # RAM Usage
        memory = psutil.virtual_memory()
        ram_used = memory.percent

        # CPU Load
        cpu_load = psutil.cpu_percent(interval=1)

        return jsonify({
            "status": "success",
            "metrics": {
                "disks": disks,
                "ram": ram_used,
                "cpu": cpu_load,
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@admin_bp.route("/status/history")
@auth.login_required
def status_history():
    """Serves historical status data."""
    try:
        data = safe_read_json_with_cache(STATUS_LOG_FILE)

        # Format response
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


@admin_bp.route("/status")
@auth.login_required
def server_status():
    """Fetches the latest status for each service."""
    try:
        data = safe_read_json_with_cache(STATUS_LOG_FILE)

        # Validate structure
        if not isinstance(data, dict) or "services" not in data:
            return jsonify({"error": "Invalid status log format"}), 500

        services = data["services"]
        latest_statuses = []

        for service_name, logs in services.items():
            if not logs or not isinstance(logs, list):
                latest_statuses.append({
                    "name": service_name,
                    "status": "No data available",
                    "timestamp": None
                })
                continue

            # Find the latest log
            latest_log = max(logs, key=lambda log: log["timestamp"])
            latest_statuses.append({
                "name": service_name,
                "status": latest_log.get("status", "Unknown"),
                "timestamp": latest_log.get("timestamp", "Unknown")
            })

        return jsonify(latest_statuses)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Endpoint to check MSSQL database health
@admin_bp.route("/database")
@auth.login_required
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
@admin_bp.route("/logs")
@auth.login_required
def list_logs():
    try:
        files = [f for f in os.listdir(LOGS_FOLDER) if os.path.isfile(os.path.join(LOGS_FOLDER, f))]
        return jsonify({"status": "success", "files": files})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@admin_bp.route("/logs/<filename>")
@auth.login_required
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
        limit = int(request.args.get("limit", 250))  # Pagination limit

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
@admin_bp.route("/")
@auth.login_required
def index():
    return render_template("admin.html")