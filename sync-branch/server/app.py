from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_swagger_ui import get_swaggerui_blueprint
import requests
import logging
from auth import auth_bp
from profiles import profile_bp
from messaging import messaging_bp
from friendship import friendship_bp
from api import api_bp
from dotenv import load_dotenv
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
    return jsonify({"status": "ok", "service": "Auth Service"}), 200

@profile_bp.route("/healthcheck", methods=["GET"])
def profile_healthcheck():
    return jsonify({"status": "ok", "service": "Profile Service"}), 200

@messaging_bp.route("/healthcheck", methods=["GET"])
def messaging_healthcheck():
    return jsonify({"status": "ok", "service": "Messaging Service"}), 200

@friendship_bp.route("/healthcheck", methods=["GET"])
def friendship_healthcheck():
    return jsonify({"status": "ok", "service": "Friendship Service"}), 200

@api_bp.route("/healthcheck", methods=["GET"])
def api_healthcheck():
    return jsonify({"status": "ok", "service": "API Service"}), 200

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(profile_bp, url_prefix="/profile")
app.register_blueprint(messaging_bp, url_prefix="/messaging")
app.register_blueprint(friendship_bp, url_prefix="/friendship")
app.register_blueprint(api_bp, url_prefix="/api")
app.register_blueprint(swaggerui_blueprint, url_prefix=app.config['SWAGGER_URL'])

# Central Healthcheck for All Services
@app.route("/healthcheck", methods=["GET"])
def overall_healthcheck():
    services = [
        {"name": "Auth Service", "url": "/auth/healthcheck"},
        {"name": "Profile Service", "url": "/profile/healthcheck"},
        {"name": "Messaging Service", "url": "/messaging/healthcheck"},
        {"name": "Friendship Service", "url": "/friendship/healthcheck"},
        {"name": "API Service", "url": "/api/healthcheck"}
    ]
    statuses = []
    for service in services:
        try:
            response = requests.get(f"http://localhost:5000{service['url']}", timeout=5)
            status = "Healthy" if response.status_code == 200 else "Unhealthy"
        except requests.exceptions.RequestException as e:
            status = f"Unreachable: {str(e)}"
        statuses.append({"name": service["name"], "url": service["url"], "status": status})
    return jsonify(statuses), 200

# Error handling
@app.errorhandler(404)
def not_found(e):
    return {"error": "Endpoint not found"}, 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Internal server error: {e}")
    return {"error": "Internal server error"}, 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
