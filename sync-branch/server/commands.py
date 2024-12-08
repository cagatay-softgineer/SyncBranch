from flask import Blueprint, render_template, request, jsonify
import subprocess
from flask_httpauth import HTTPBasicAuth
from dotenv import load_dotenv
import os

auth = HTTPBasicAuth()

load_dotenv()

ADMIN = os.getenv("ADMIN")
ADMIN_PWORD = os.getenv("ADMIN_PWORD")
USER = os.getenv("USER")
USER_PWORD = os.getenv("USER_PWORD")

USERS = {ADMIN: ADMIN_PWORD,USER: USER_PWORD}

@auth.verify_password
def verify_password(username, password):
    if username in USERS and USERS[username] == password:
        return username
    return None

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
    try:
        # Execute the command
        result = subprocess.check_output(command, shell=True, text=True)
        return jsonify({'success': True, 'output': result})
    except subprocess.CalledProcessError as e:
        return jsonify({'success': False, 'error': str(e)})
