from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_swagger_ui import get_swaggerui_blueprint
import logging
from auth import auth_bp
from profiles import profile_bp
from messaging import messaging_bp
from friendship import friendship_bp
from commands import commands_bp
from admin import admin_bp
from api import api_bp
from dotenv import load_dotenv
import argparse
import os

load_dotenv()
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")
app.config['SWAGGER_URL'] = '/api/docs'
app.config['API_URL'] = '/static/swagger.json'

jwt = JWTManager(app)
limiter = Limiter(app)

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Swagger documentation setup
swaggerui_blueprint = get_swaggerui_blueprint(
    app.config['SWAGGER_URL'],
    app.config['API_URL'],
    config={'app_name': "Endpoint Server API"}
)

# Add /healthcheck to each blueprint
@auth_bp.route("/healthcheck", methods=["GET"])
def auth_healthcheck():
    logger.info("Auth Service healthcheck requested")
    return jsonify({"status": "ok", "service": "Auth Service"}), 200

@profile_bp.route("/healthcheck", methods=["GET"])
def profile_healthcheck():
    logger.info("Profile Service healthcheck requested")
    return jsonify({"status": "ok", "service": "Profile Service"}), 200

@messaging_bp.route("/healthcheck", methods=["GET"])
def messaging_healthcheck():
    logger.info("Messaging Service healthcheck requested")
    return jsonify({"status": "ok", "service": "Messaging Service"}), 200

@friendship_bp.route("/healthcheck", methods=["GET"])
def friendship_healthcheck():
    logger.info("Friendship Service healthcheck requested")
    return jsonify({"status": "ok", "service": "Friendship Service"}), 200

@api_bp.route("/healthcheck", methods=["GET"])
def api_healthcheck():
    logger.info("API Service healthcheck requested")
    return jsonify({"status": "ok", "service": "API Service"}), 200

@commands_bp.route("/healthcheck", methods=["GET"])
def commands_healthcheck():
    logger.info("Console Service healthcheck requested")
    return jsonify({"status": "ok", "service": "Console Service"}), 200

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(profile_bp, url_prefix="/profile")
app.register_blueprint(messaging_bp, url_prefix="/messaging")
app.register_blueprint(friendship_bp, url_prefix="/friendship")
app.register_blueprint(api_bp, url_prefix="/api")
app.register_blueprint(commands_bp, url_prefix="/commands")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(swaggerui_blueprint, url_prefix=app.config['SWAGGER_URL'])

# Error handling
@app.errorhandler(404)
def not_found(e):
    return {"error": "Endpoint not found"}, 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Internal server error: {e}")
    return {"error": "Internal server error"}, 500

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
