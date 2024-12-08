from flask import Blueprint, render_template, request, jsonify
import subprocess
from flask_httpauth import HTTPBasicAuth
from dotenv import load_dotenv
import shutil
import psutil
import os
import re

auth = HTTPBasicAuth()

load_dotenv()

ADMIN = os.getenv("ADMIN")
ADMIN_PWORD = os.getenv("ADMIN_PWORD")
USER = os.getenv("USER")
USER_PWORD = os.getenv("USER_PWORD")

def all_disks_usage():
    """Retrieve disk usage for all available drives."""
    disks = []
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disks.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "total": usage.total // (2**30),
                "used": usage.used // (2**30),
                "free": usage.free // (2**30),
                "percent_used": usage.percent
            })
        except PermissionError:
            # Skip drives we don't have permission to access
            continue
    return disks

def disk_usage():
    total, used, free = shutil.disk_usage("C:/")
    return f"Total: {total // (2**30)} GiB, Used: {used // (2**30)} GiB, Free: {free // (2**30)} GiB"

# Predefined allowlist of commands
ALLOWED_COMMANDS = {
    "file_management": {
        "list_dir": "ls -lh",  # List directory with details
        "list_dir_windows": "dir",  # List directory on Windows
        "show_file_stats": "stat {file}",  # Show file stats (Linux/Unix)
        "create_temp_file": "mktemp",  # Create a temporary file
        "create_temp_file_windows": "echo > temp_file.txt",  # Create a temporary file on Windows
        "check_disk_usage": "du -sh *"  # Show disk usage for current directory
    },
    "system_info": {
        "disk_usage": "df -h",  # Show disk usage
        "disk_free_windows": "all_disks_usage",  # Show free disk space on Windows
        "current_user": "whoami",  # Display current user
        "current_user_windows": "echo %USERNAME%",  # Display current user on Windows
        "system_info_windows": "systeminfo",  # Display system information on Windows
        "kernel_version": "uname -r",  # Show kernel version (Linux/Unix)
        "uptime": "uptime",  # Show system uptime
        "hostname": "hostname",  # Show the hostname
    },
    "networking": {
        "ping_google": "ping -c 4 google.com" if os.name != 'nt' else "ping -n 4 google.com",  # Ping Google
        "show_ip": "ip a" if os.name != 'nt' else "ipconfig",  # Show IP configuration
        "traceroute_google": "traceroute google.com" if os.name != 'nt' else "tracert google.com",  # Trace route to Google
        "dns_check": "nslookup google.com",  # Check DNS resolution
        "netstat": "netstat -tuln" if os.name != 'nt' else "netstat -an",  # Show network connections
    },
    "process_management": {
        "list_processes": "ps aux",  # List running processes (Linux/Unix)
        "task_list_windows": "tasklist",  # List running tasks on Windows
        "top_processes": "top -n 1 -b",  # Show top processes (Linux/Unix)
    },
    "log_management": {
        "system_logs": "dmesg | tail -n 50",  # Show the last 50 system logs (Linux/Unix)
        "auth_logs": "tail -n 50 /var/log/auth.log",  # Show the last 50 authentication logs (Linux/Unix)
        "event_logs_windows": "wevtutil qe System /c:50 /f:text",  # Show the last 50 system logs on Windows
    },
}

USERS = {ADMIN: ADMIN_PWORD,USER: USER_PWORD}

@auth.verify_password
def verify_password(username, password):
    if username in USERS and USERS[username] == password:
        return username
    return None

def validate_input(command, params):
    if command == "show_file_stats":
        # Example: Validate file path
        file_path = params.get('file', '')
        if not re.match(r'^[\w\-\./]+$', file_path):
            raise ValueError("Invalid file path")
        return ALLOWED_COMMANDS['file_management'][command].format(file=file_path)
    return ALLOWED_COMMANDS['file_management'][command]

# Define the blueprint
commands_bp = Blueprint('commands', __name__, template_folder='templates')

# Route to render the command page
@commands_bp.route('/cmd')
@auth.login_required
def index():
    return render_template('cmd.html')

# Route to execute a command
@commands_bp.route('/run_command', methods=['POST'])
@auth.login_required
def run_command():
    command = request.form.get('command')

    # Find the command in the allowlist
    for category, commands in ALLOWED_COMMANDS.items():
        if command in commands:
            command_to_run = commands[command]
            break
    else:
        return jsonify({'success': False, 'error': 'Invalid or unauthorized command.'}), 400

    try:
        if command_to_run == "all_disks_usage":
            # Handle the special Python function call
            disks = all_disks_usage()
            result = "\n".join([
                f"Device: {disk['device']}, Mountpoint: {disk['mountpoint']}, "
                f"Total: {disk['total']} GiB, Used: {disk['used']} GiB, Free: {disk['free']} GiB, "
                f"Usage: {disk['percent_used']}%"
                for disk in disks
            ])
        else:
            # Execute the shell command
            result = subprocess.check_output(command_to_run, shell=True, text=True)
        return jsonify({'success': True, 'output': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500