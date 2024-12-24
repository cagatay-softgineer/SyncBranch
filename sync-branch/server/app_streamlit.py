import streamlit as st
import threading
import logging
from flask import Flask, jsonify, request, Blueprint
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from cmd_gui_kit import CmdGUI
from auth import auth_bp
from profiles import profile_bp
from messaging import messaging_bp
from friendship import friendship_bp
from commands import commands_bp
from admin import admin_bp
from api import api_bp
from database import database_bp
from dotenv import load_dotenv
import os

# --- Initialize your GUI/logger ---
gui = CmdGUI()

load_dotenv()


# --------------------------------------------------------------------
# Blueprints (Put their setup BEFORE registration)
# --------------------------------------------------------------------
auth_bp = Blueprint("auth", __name__)  # noqa: F811
profile_bp = Blueprint("profile", __name__)  # noqa: F811
messaging_bp = Blueprint("messaging", __name__)  # noqa: F811
friendship_bp = Blueprint("friendship", __name__)  # noqa: F811
commands_bp = Blueprint("commands", __name__)  # noqa: F811
admin_bp = Blueprint("admin", __name__)  # noqa: F811
api_bp = Blueprint("api", __name__)  # noqa: F811
database_bp = Blueprint("database", __name__)  # noqa: F811


# --- Blueprint request logs ---
@auth_bp.before_request
def log_auth_requests():
    logger.info("Auth blueprint request received.")

@profile_bp.before_request
def log_profile_requests():
    logger.info("Profile blueprint request received.")

@messaging_bp.before_request
def log_messaging_requests():
    logger.info("Messaging blueprint request received.")

@friendship_bp.before_request
def log_friendship_requests():
    logger.info("Friendship blueprint request received.")

@api_bp.before_request
def log_api_requests():
    logger.info("API blueprint request received.")

@database_bp.before_request
def log_database_requests():
    logger.info("Database blueprint request received.")

@commands_bp.before_request
def log_commands_requests():
    logger.info("Commands blueprint request received.")

@admin_bp.before_request
def log_admin_requests():
    logger.info("Admin blueprint request received.")


# --- Create the Flask app ---
app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY", "super-secret-key")
app.config['SWAGGER_URL'] = '/api/docs'
app.config['API_URL'] = '/static/swagger.json'

# --- Extensions ---
jwt = JWTManager(app)
limiter = Limiter(app)

# Allow CORS for all domains on all routes
CORS(app, resources={r"/*": {"origins": "*"}})

# --- Set up logging ---
LOG_FILE = "logs/endpoint.log"

logger = logging.getLogger("SyncBranchLogger")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.propagate = False




# --- Middleware to log all requests ---
@app.before_request
def log_request():
    logger.info(f"Request received: {request.method} {request.url}")

# --- Swagger UI setup ---
swaggerui_blueprint = get_swaggerui_blueprint(
    app.config['SWAGGER_URL'],
    app.config['API_URL'],
    config={'app_name': "Endpoint Server API"}
)

# --- Healthcheck endpoints ---
@auth_bp.route("/healthcheck", methods=["GET"])
def auth_healthcheck():
    gui.log("Auth Service healthcheck requested")
    logger.info("Auth Service healthcheck requested")
    return jsonify({"status": "ok", "service": "Auth Service"}), 200

@profile_bp.route("/healthcheck", methods=["GET"])
def profile_healthcheck():
    gui.log("Profile Service healthcheck requested")
    logger.info("Profile Service healthcheck requested")
    return jsonify({"status": "ok", "service": "Profile Service"}), 200

@messaging_bp.route("/healthcheck", methods=["GET"])
def messaging_healthcheck():
    gui.log("Messaging Service healthcheck requested")
    logger.info("Messaging Service healthcheck requested")
    return jsonify({"status": "ok", "service": "Messaging Service"}), 200

@friendship_bp.route("/healthcheck", methods=["GET"])
def friendship_healthcheck():
    gui.log("Friendship Service healthcheck requested")
    logger.info("Friendship Service healthcheck requested")
    return jsonify({"status": "ok", "service": "Friendship Service"}), 200

@api_bp.route("/healthcheck", methods=["GET"])
def api_healthcheck():
    gui.log("API Service healthcheck requested")
    logger.info("API Service healthcheck requested")
    return jsonify({"status": "ok", "service": "API Service"}), 200

@database_bp.route("/healthcheck", methods=["GET"])
def database_healthcheck():
    gui.log("Database Service healthcheck requested")
    logger.info("Database Service healthcheck requested")
    return jsonify({"status": "ok", "service": "Database Service"}), 200

@commands_bp.route("/healthcheck", methods=["GET"])
def commands_healthcheck():
    gui.log("Console Service healthcheck requested")
    logger.info("Console Service healthcheck requested")
    return jsonify({"status": "ok", "service": "Console Service"}), 200

@app.route("/healthcheck", methods=['POST', 'GET'])
def app_healthcheck():
    logger.info("App healthcheck requested")
    return jsonify({"status": "ok", "service": "Main Flask App"}), 200

# --- Register Blueprints ---
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(profile_bp, url_prefix="/profile")
app.register_blueprint(messaging_bp, url_prefix="/messaging")
app.register_blueprint(friendship_bp, url_prefix="/friendship")
app.register_blueprint(api_bp, url_prefix="/api")
app.register_blueprint(database_bp, url_prefix="/database")
app.register_blueprint(commands_bp, url_prefix="/commands")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(swaggerui_blueprint, url_prefix=app.config['SWAGGER_URL'])

# --- Error handlers ---
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404

@app.errorhandler(500)
def internal_server_error(e):
    gui.log(f"Internal server error: {e}", level="error")
    logger.error(f"Internal server error: {e}")
    return jsonify({"error": "Internal Server Error"}), 500

# --- JWT handlers ---
@jwt.unauthorized_loader
def unauthorized_loader(callback):
    return jsonify({"error": "Token missing or invalid", "message": callback}), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "Token expired"}), 401

# ----------------------------------------------------------------
#    Streamlit Integration
# ----------------------------------------------------------------

def run_flask_server(port: int = 8080):
    """
    Run the Flask server on a specified port.
    This function is intended to be launched in a background thread.
    """
    logger.info(f"Starting Flask server on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)  # debug=False to avoid double reload.


def main():
    """
    The main Streamlit app function.
    """
    st.title("Endpoint Server API (Flask + Streamlit)")
    st.markdown(
        """
        This Streamlit app starts a Flask server (with JWT, Swagger docs, etc.) in the background.
        You can use Streamlit to invoke the various endpoints or monitor logs.
        """
    )

    # Let the user pick a port (just an example)
    default_port = 8080
    port = st.number_input("Choose a port to run the Flask server on", min_value=1, max_value=65535, value=default_port)

    if "server_thread" not in st.session_state:
        st.session_state["server_thread"] = None

    # Button to start the server
    if st.button("Start Flask Server"):
        if st.session_state["server_thread"] is None or not st.session_state["server_thread"].is_alive():
            # Start the server in a separate thread so Streamlit doesn't block
            thread = threading.Thread(target=run_flask_server, args=(port,), daemon=True)
            thread.start()
            st.session_state["server_thread"] = thread
            st.success(f"Flask server is starting on port {port}...")
        else:
            st.warning("Flask server is already running!")

    st.markdown("---")

    # Simple way to call the Flask healthcheck from Streamlit
    st.subheader("Test Healthcheck Endpoints")
    base_url = f"http://localhost:{port}"

    service = st.selectbox(
        "Select a service to healthcheck:",
        [
            "Main App (/healthcheck)",
            "Auth Service (/auth/healthcheck)",
            "Profile Service (/profile/healthcheck)",
            "Messaging Service (/messaging/healthcheck)",
            "Friendship Service (/friendship/healthcheck)",
            "API Service (/api/healthcheck)",
            "Database Service (/database/healthcheck)",
            "Console Commands Service (/commands/healthcheck)",
        ],
    )

    if st.button("Send Healthcheck Request"):
        import requests

        # Match the selection to an actual endpoint
        endpoints_map = {
            "Main App (/healthcheck)": "/healthcheck",
            "Auth Service (/auth/healthcheck)": "/auth/healthcheck",
            "Profile Service (/profile/healthcheck)": "/profile/healthcheck",
            "Messaging Service (/messaging/healthcheck)": "/messaging/healthcheck",
            "Friendship Service (/friendship/healthcheck)": "/friendship/healthcheck",
            "API Service (/api/healthcheck)": "/api/healthcheck",
            "Database Service (/database/healthcheck)": "/database/healthcheck",
            "Console Commands Service (/commands/healthcheck)": "/commands/healthcheck",
        }

        endpoint = endpoints_map[service]
        full_url = base_url + endpoint

        try:
            response = requests.get(full_url, timeout=5)
            st.write(f"**Status Code:** {response.status_code}")
            st.json(response.json())
        except requests.exceptions.RequestException as e:
            st.error(f"Error requesting {full_url}: {e}")


# --- Streamlit entry point ---
if __name__ == "__main__":
    main()
