import subprocess
import threading
from flask import Flask, jsonify, render_template, stream_with_context, Response

# Configuration
PORTS = range(5001, 5051)  # Define the range of ports
SCRIPT_PATH = "sync-branch/server/app.py"  # Path to your Python script

# Global storage for process handles and logs
processes = {}
logs = {port: [] for port in PORTS}  # Store logs for each port

# Flask app for GUI
app = Flask(__name__)

def append_log(port, line):
    """Append a line to the log for a specific port."""
    logs[port].append(line)
    if len(logs[port]) > 500:  # Limit logs to the last 500 lines
        logs[port] = logs[port][-500:]

def start_process(port):
    """Start a Python process on the specified port."""
    try:
        command = f"python {SCRIPT_PATH} --port {port}"
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        processes[port] = process

        # Start a thread to capture logs
        threading.Thread(target=stream_process_logs, args=(port, process), daemon=True).start()

        return {"status": "success", "port": port}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def stop_process(port):
    """Stop the Python process running on the specified port."""
    process = processes.get(port)
    if process:
        process.terminate()
        process.wait()
        del processes[port]
        return {"status": "success", "port": port}
    return {"status": "error", "message": f"No process running on port {port}"}

def stream_process_logs(port, process):
    """Capture stdout and stderr of a process and append to logs."""
    try:
        for line in process.stdout:
            append_log(port, line)
        for line in process.stderr:
            append_log(port, f"ERROR: {line}")
    except Exception as e:
        append_log(port, f"Log stream error: {e}")

@app.route("/")
def index():
    """Render the HTML interface."""
    return render_template("index.html", ports=PORTS, processes=processes)

@app.route("/start/<int:port>", methods=["POST"])
def start_server(port):
    """Start a server on the given port."""
    if port in processes:
        return jsonify({"status": "error", "message": f"Server already running on port {port}"})
    return jsonify(start_process(port))

@app.route("/stop/<int:port>", methods=["POST"])
def stop_server(port):
    """Stop a server running on the given port."""
    return jsonify(stop_process(port))

@app.route("/status", methods=["GET"])
def status():
    """Get the status of all servers."""
    statuses = {
        port: "running" if port in processes else "stopped"
        for port in PORTS
    }
    return jsonify(statuses)

@app.route("/logs/<int:port>")
def get_logs(port):
    """Stream logs for a specific port."""
    def generate():
        if port in logs:
            for line in logs[port]:
                yield line + "\n"
        else:
            yield "No logs available for this port.\n"
    return Response(stream_with_context(generate()), content_type="text/plain")

if __name__ == "__main__":
    # Start Flask app in a separate thread to keep the main thread for process management
    threading.Thread(target=lambda: app.run(debug=True, use_reloader=False)).start()
