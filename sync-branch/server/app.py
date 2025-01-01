from flask import Flask, jsonify, render_template, request
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_swagger_ui import get_swaggerui_blueprint
from cmd_gui_kit import CmdGUI
from flask_cors import CORS
import logging
from auth import auth_bp
from profiles import profile_bp
from messaging import messaging_bp
from friendship import friendship_bp
from commands import commands_bp
from admin import admin_bp
from api import api_bp
from database import database_bp
from dotenv import load_dotenv
import argparse
import os

gui = CmdGUI()

load_dotenv()
app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")
app.config['SWAGGER_URL'] = '/api/docs'
app.config['API_URL'] = '/static/swagger.json'

jwt = JWTManager(app)
limiter = Limiter(app)

CORS(app, resources={r"/*": {"origins": "*"}})

# Setup logging
LOG_FILE = "logs/endpoint.log"

# Create a logger
logger = logging.getLogger("SyncBranchLogger")
logger.setLevel(logging.DEBUG)

# Create file handler
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.propagate = False

# Middleware to log all requests
def log_request():
    logger.info(f"Request received: {request.method} {request.url}")
app.before_request(log_request)

# Swagger documentation setup
swaggerui_blueprint = get_swaggerui_blueprint(
    app.config['SWAGGER_URL'],
    app.config['API_URL'],
    config={'app_name': "Endpoint Server API"}
)

# Add /healthcheck to each blueprint
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
    logger.info("API blueprint request received.")

@commands_bp.before_request
def log_commands_requests():
    logger.info("Commands blueprint request received.")

@admin_bp.before_request
def log_admin_requests():
    logger.info("Admin blueprint request received.")

# Add /healthcheck to each blueprint
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
    return jsonify({"status": "ok", "service": "API Service"}), 200

@commands_bp.route("/healthcheck", methods=["GET"])
def commands_healthcheck():
    gui.log("Console Service healthcheck requested")
    logger.info("Console Service healthcheck requested")
    return jsonify({"status": "ok", "service": "Console Service"}), 200

@app.route("/healthcheck", methods=['POST', 'GET'])
def app_healthcheck():
    #gui.log("App healthcheck requested")
    logger.info("App healthcheck requested")
    return jsonify({"status": "ok", "service": "Console Service"}), 200

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(profile_bp, url_prefix="/profile")
app.register_blueprint(messaging_bp, url_prefix="/messaging")
app.register_blueprint(friendship_bp, url_prefix="/friendship")
app.register_blueprint(api_bp, url_prefix="/api")
app.register_blueprint(database_bp, url_prefix="/database")
app.register_blueprint(commands_bp, url_prefix="/commands")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(swaggerui_blueprint, url_prefix=app.config['SWAGGER_URL'])

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_message="The Endpoint you are looking for does not exist."), 404

# 500 Error Handler
@app.errorhandler(500)
def internal_server_error(e):
    gui.log(f"Internal server error: {e}", level="error")
    logger.error(f"Internal server error: {e}")
    return render_template('error.html', error_message="An internal server error occurred. Please try again later."), 500

@jwt.unauthorized_loader
def unauthorized_loader(callback):
    return jsonify({"error": "Token missing or invalid", "message": callback}), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "Token expired"}), 401

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Flask on a specific port.")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the Flask app.")
    args = parser.parse_args()

    app.run(host="0.0.0.0", port=args.port)
