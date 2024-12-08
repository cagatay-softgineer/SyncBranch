from flask import Blueprint, request, jsonify
from flask_httpauth import HTTPBasicAuth
from utils import execute_query_with_logging
from dotenv import load_dotenv
import os
import pyodbc
import logging
from cmd_gui_kit import CmdGUI

# Initialize CmdGUI for visual feedback
gui = CmdGUI()

auth = HTTPBasicAuth()

load_dotenv()

ADMIN = os.getenv("ADMIN")
ADMIN_PWORD = os.getenv("ADMIN_PWORD")
USER = os.getenv("USER")
USER_PWORD = os.getenv("USER_PWORD")

# Example user credentials (replace with a more secure storage in production)
USERS = {ADMIN: ADMIN_PWORD,USER: USER_PWORD}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the Blueprint
api_bp = Blueprint('api', __name__)

PRIMARY_SQL_SERVER = os.getenv("PRIMARY_SQL_SERVER")
PRIMARY_SQL_SERVER_PORT = os.getenv("PRIMARY_SQL_SERVER_PORT")
PRIMARY_SQL_DATABASE = os.getenv("PRIMARY_SQL_DATABASE")
PRIMARY_SQL_USER = os.getenv("PRIMARY_SQL_USER")
PRIMARY_SQL_PASSWORD = os.getenv("PRIMARY_SQL_PASSWORD")

FLUTTER_SQL_SERVER = os.getenv("FLUTTER_SQL_SERVER")
FLUTTER_SQL_SERVER_PORT = os.getenv("FLUTTER_SQL_SERVER_PORT")
FLUTTER_SQL_DATABASE = os.getenv("FLUTTER_SQL_DATABASE")
FLUTTER_SQL_USER = os.getenv("FLUTTER_SQL_USER")
FLUTTER_SQL_PASSWORD = os.getenv("FLUTTER_SQL_PASSWORD")


# Store connection strings in a dictionary
DB_CONNECTION_STRINGS = {
    "primary": f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={PRIMARY_SQL_SERVER},{PRIMARY_SQL_SERVER_PORT};DATABASE={PRIMARY_SQL_DATABASE};UID={PRIMARY_SQL_USER};PWD={PRIMARY_SQL_PASSWORD}",
    "flutter": f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={FLUTTER_SQL_SERVER},{FLUTTER_SQL_SERVER_PORT};DATABASE={FLUTTER_SQL_DATABASE};UID={FLUTTER_SQL_USER};PWD={FLUTTER_SQL_PASSWORD}"
}

@auth.verify_password
def verify_password(username, password):
    if username in USERS and USERS[username] == password:
        return username
    return None


# Example Route: Fetch all records from a table
@api_bp.route('/table/<table_name>', methods=['GET'])
@auth.login_required
def get_table_records(table_name):
    try:
        # Fetch data using execute_query
        query = f"SELECT * FROM {table_name}"
        data, description = execute_query_with_logging(query, "flutter", fetch=True)
        
        columns = [desc[0] for desc in description]
        print(columns)
        # Convert rows to dictionaries
        result = [dict(zip(columns, row)) for row in data]
        print(result)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Example Route: Execute a custom query
@api_bp.route("/query", methods=["POST"])
@auth.login_required
def execute_custom_query():
    try:
        data = request.json
        print(request.json)
        query = data.get("query")
        db_name = data.get("db_name", "primary")  # Default to "primary" database
        if not query:
            return jsonify({"error": "Query not provided"}), 400

        # Log the query being executed
        gui.log(f"Executing query: {query}", level="info")

        # Execute the query
        rows, description = execute_query_with_logging(query, db_name, fetch=True)

        if rows is None:
            return jsonify({"message": "Query executed successfully but returned no results"}), 200

        # Convert rows to JSON using column descriptions
        columns = [desc[0] for desc in description]
        result = [dict(zip(columns, row)) for row in rows]
        return jsonify(result), 200

    except pyodbc.ProgrammingError as e:
        logger.error(f"Database programming error: {e}")
        return jsonify({"error": "Query execution failed. Check the function or query syntax."}), 500
    except pyodbc.Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"error": str(e)}), 500