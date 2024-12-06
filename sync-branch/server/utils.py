import pyodbc
import logging
from dotenv import load_dotenv
import os
from datetime import datetime
from cmd_gui_kit import CmdGUI

# Initialize CmdGUI for visual feedback
gui = CmdGUI()

# Logging setup
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.log")
logging.basicConfig(level=logging.INFO, filename=log_file, filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")


load_dotenv()

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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store connection strings in a dictionary
DB_CONNECTION_STRINGS = {
    "primary": f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={PRIMARY_SQL_SERVER},{PRIMARY_SQL_SERVER_PORT};DATABASE={PRIMARY_SQL_DATABASE};UID={PRIMARY_SQL_USER};PWD={PRIMARY_SQL_PASSWORD}",
    "flutter": f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={FLUTTER_SQL_SERVER},{FLUTTER_SQL_SERVER_PORT};DATABASE={FLUTTER_SQL_DATABASE};UID={FLUTTER_SQL_USER};PWD={FLUTTER_SQL_PASSWORD}"
}

def get_db_connection(db_name):
    """Get a connection to the specified database."""
    if db_name not in DB_CONNECTION_STRINGS:
        raise ValueError(f"Unknown database name: {db_name}")

    try:
        conn = pyodbc.connect(DB_CONNECTION_STRINGS[db_name])
        logger.info(f"Connected to {db_name} database successfully.")
        return conn
    except pyodbc.Error as e:
        gui.log(f"Database connection failed: {e}", level="error")
        logging.error(f"Database connection failed: {e}")
        raise

def execute_query_with_logging(query, db_name, params=(), fetch=False):
    """
    Executes a query on the specified database with logging and visual feedback.
    """
    conn = None
    try:
        gui.status(f"Connecting to {db_name} database...", status="info")
        conn = get_db_connection(db_name)
        cursor = conn.cursor()

        # Log and display query execution
        gui.log(f"Executing query: {query} with params: {params}", level="info")
        logging.info(f"Executing query: {query} with params: {params}")

        # Ensure params are in the correct format if using TVP
        if isinstance(params, tuple) and len(params) == 1 and isinstance(params[0], (tuple, list)):
            params = params[0]  # Unwrap the sequence if necessary

        cursor.execute(query, params)

        if fetch:
            rows = cursor.fetchall()
            gui.status("Query executed successfully, fetching results...", status="success")
            logging.info(f"Query succeeded. Columns: {[column[0] for column in cursor.description]}")
            return rows, cursor.description

        conn.commit()
        gui.status("Query executed successfully and committed.", status="success")
        logging.info("Query executed successfully and committed.")
        return None
    except pyodbc.Error as e:
        gui.status(f"Query execution failed: {e}", status="error")
        logging.error(f"Query execution error: {e}")
        raise
    finally:
        if conn:
            conn.close()
            gui.status(f"Connection to {db_name} database closed.", status="info")
