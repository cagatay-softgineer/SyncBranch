import streamlit as st
import altair as alt
import pandas as pd
import sqlite3
import requests
from datetime import datetime, timedelta

# Define the endpoints you want to check
SERVICES = {
    "Main App": "/healthcheck",
    "Auth Service": "/auth/healthcheck",
    "Profile Service": "/profile/healthcheck",
    "Messaging Service": "/messaging/healthcheck",
    "Friendship Service": "/friendship/healthcheck",
    "API Service": "/api/healthcheck",
    "Database Service": "/database/healthcheck",
    "Console Commands Service": "/commands/healthcheck",
}

BASE_URL = "http://api-sync-branch.yggbranch.dev"

def init_db(db_path='health_data.db'):
    """
    Initialize the SQLite database and create the health_checks table if it doesn't exist.
    """
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS health_checks (
                timestamp TEXT,
                service TEXT,
                status_code INTEGER,
                success BOOLEAN,
                response_time REAL
            )
        ''')
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        st.error(f"Database initialization error: {e}")

def check_services(db_path='health_data.db'):
    """
    Perform healthcheck requests to all services and store results in the database.
    """
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        for service_name, endpoint in SERVICES.items():
            url = f"{BASE_URL}{endpoint}"
            start_time = datetime.now()
            try:
                response = requests.get(url, timeout=5)
                elapsed = (datetime.now() - start_time).total_seconds()
                status_code = response.status_code
                success = 200 <= status_code < 300
            except requests.exceptions.RequestException:
                # Failed request
                elapsed = None
                status_code = None
                success = False

            c.execute('''
                INSERT INTO health_checks (timestamp, service, status_code, success, response_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), service_name, status_code, success, elapsed))

        # Prune data older than 2 days
        cutoff = datetime.now() - timedelta(days=2)
        c.execute('''
            DELETE FROM health_checks WHERE timestamp < ?
        ''', (cutoff.isoformat(),))

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        st.error(f"Database error during health checks: {e}")
    except Exception as e:
        st.error(f"Unexpected error during health checks: {e}")

def get_db_connection(db_path='health_data.db'):
    """
    Establish a connection to the SQLite database.
    """
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        st.error(f"Database connection error: {e}")
        return None

def create_chart(db_path='health_data.db'):
    """
    Create separate Altair charts for each service's healthcheck success ratio.
    """
    conn = get_db_connection(db_path)
    if conn is None:
        st.error("Failed to connect to the database.")
        return

    try:
        df = pd.read_sql_query("SELECT * FROM health_checks", conn, parse_dates=['timestamp'])
    except pd.io.sql.DatabaseError as e:
        st.error(f"Database read error: {e}")
        df = pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        st.info("No healthcheck data available yet.")
        return

    # Convert timestamp to 1-minute grouping
    df["time_group"] = df["timestamp"].dt.floor("1min")

    # Get unique services
    services = sorted(df["service"].unique())

    # Create tabs for each service
    tabs = st.tabs(services)
    for tab, service_name in zip(tabs, services):
        with tab:
            # Filter data for this specific service
            service_df = df[df["service"] == service_name].copy()
            if service_df.empty:
                st.write(f"No data available for **{service_name}**.")
                continue
            grouped = (
                service_df.groupby(["time_group"], as_index=False)
                          .agg(success_ratio=("success", "mean"))
            )

            chart = (
                alt.Chart(grouped)
                .mark_line(point=True)
                .encode(
                    x=alt.X("time_group:T", title="Time"),
                    y=alt.Y("success_ratio:Q", title="Success Ratio"),
                    tooltip=["time_group", "success_ratio"]
                )
                .properties(title=f"{service_name} — Healthcheck Success Ratio")
                .interactive()
            )

            st.altair_chart(chart, use_container_width=True)

def auto_refresh(interval_sec=300):
    """
    Manually trigger a rerun after `interval_sec` seconds have passed.
    """
    now = datetime.now()
    if "last_refresh" not in st.session_state:
        st.session_state["last_refresh"] = now
        # Perform the initial health check
        check_services()
    else:
        last_refresh = st.session_state["last_refresh"]
        elapsed = (now - last_refresh).total_seconds()
        if elapsed >= interval_sec:
            st.session_state["last_refresh"] = now
            # Perform health check
            check_services()
            st.experimental_rerun()

def main():
    # Initialize the database
    init_db()

    # Auto-refresh logic: check every 5 minutes (300 seconds)
    auto_refresh(interval_sec=300)

    # Set the title of the dashboard
    st.title("Backend Health Check Dashboard")

    st.write("""
        This dashboard visualizes the health status of various backend services.
        Health checks are performed every 5 minutes and stored in a SQLite database.
    """)

    # Display the healthcheck charts
    create_chart()

    # Display information about the last refresh and next refresh
    conn = get_db_connection()
    if conn:
        try:
            last_update = pd.read_sql_query("SELECT MAX(timestamp) as last_update FROM health_checks", conn)
            conn.close()

            if not last_update.empty and pd.notnull(last_update['last_update'][0]):
                last_refresh_time = datetime.fromisoformat(last_update['last_update'][0])
                st.write(f"**Last refresh:** {last_refresh_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                next_refresh_time = last_refresh_time + timedelta(seconds=300)
                time_left = next_refresh_time - datetime.now()
                if time_left.total_seconds() > 0:
                    minutes, seconds = divmod(int(time_left.total_seconds()), 60)
                    st.write(f"**Next refresh in:** ~{minutes} minutes and {seconds} seconds")
                else:
                    st.write("**Next refresh in:** ~0 minutes and 0 seconds")
            else:
                st.write("**No health check data available yet.**")
        except Exception as e:
            st.error(f"Error fetching last update: {e}")
    else:
        st.write("**No health check data available yet.**")

if __name__ == "__main__":
    main()
