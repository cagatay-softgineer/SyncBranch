import time
import subprocess
import os
import streamlit as st

# Initialize or retrieve session state variables
if "first_file_last_run" not in st.session_state:
    st.session_state.first_file_last_run = 0
if "second_file_runs" not in st.session_state:
    st.session_state.second_file_runs = 0

# Adjust these intervals and max runs as needed
SECOND_FILE_INTERVAL = 7200   # 2 hours (example)
MAX_RUNS = 12                 # Limit for second file runs
FIRST_FILE_INTERVAL = 3300    # ~55 minutes (example)

# Replace with your file paths
FIRST_FILE = 'sync-branch/auth/update_tokens.py'
SECOND_FILE = 'sync-branch/api/get_recent.py'
THIRD_FILE = 'sync-branch/api/get_users_liked_tracks.py'
FOURTH_FILE = 'sync-branch/api/update_audio_features.py'

def run_python_file(file_path: str) -> bool:
    """Run a Python file and capture any output or errors with Streamlit."""
    if not os.path.exists(file_path):
        st.error(f"[ERROR] The file {file_path} does not exist.")
        return False
    
    try:
        with st.spinner(f"Running {file_path}..."):
            result = subprocess.run(['python', file_path], capture_output=True, text=True)
        
        if result.returncode != 0:
            st.error(f"[ERROR] running {file_path}:")
            st.error(result.stderr)
            return False
        else:
            st.info(f"[INFO] Output of {file_path}:")
            st.write(result.stdout)
            return True

    except Exception as e:
        st.error(f"[ERROR] An error occurred while running {file_path}: {e}")
        return False

def start_timer():
    """
    Start the timer-like logic and handle the execution flow based on intervals.
    Note: This function can potentially block the Streamlit app if it runs
    continuously. Use short waits or an alternative scheduling approach.
    """
    
    current_time = time.time()
    
    # 1) Check if FIRST_FILE needs to be run (every FIRST_FILE_INTERVAL seconds).
    if current_time - st.session_state.first_file_last_run >= FIRST_FILE_INTERVAL:
        st.info(f"[INFO] Running the first file: {FIRST_FILE}...")
        if run_python_file(FIRST_FILE):
            # Update last run time
            st.session_state.first_file_last_run = current_time
            st.info("[INFO] First file has completed. Resetting second file runs.")
            st.session_state.second_file_runs = 0
        else:
            st.warning("[WARNING] First file failed. Stopping further runs.")
            # If first file fails, we stop; you can customize this logic.
            return

    # 2) If we still have runs left for the second file and
    #    the first file doesn't need to run yet...
    if (st.session_state.second_file_runs < MAX_RUNS 
        and (current_time - st.session_state.first_file_last_run < FIRST_FILE_INTERVAL)):
        
        st.info(f"[INFO] Running the second file: {SECOND_FILE}...")
        if run_python_file(SECOND_FILE):
            st.session_state.second_file_runs += 1
        else:
            st.warning(f"[WARNING] Second file failed at attempt {st.session_state.second_file_runs + 1}.")
            return
        
        # 3) Run the fourth file right after second file each time (if that's desired)
        st.info(f"[INFO] Running the fourth file: {FOURTH_FILE}...")
        run_python_file(FOURTH_FILE)
        
        # 4) "Wait" for the second_file_interval.
        #    But in Streamlit, sleeping here will block the UI. 
        #    For demonstration, we do it anyway. 
        #    Consider a non-blocking approach (e.g., threading/async) for production.
        st.info(f"[INFO] Waiting for {SECOND_FILE_INTERVAL} seconds before running the second file again...")
        time.sleep(SECOND_FILE_INTERVAL)  # Reduced to 1 second for demonstration. 
                       # In a real scenario, you would do time.sleep(SECOND_FILE_INTERVAL).

    # 5) After the loop completes or if the first file completes successfully, run the third file:
    #    Below code is a simple "if/while" logic example:
    st.info("[INFO] Attempting to run the first file one more time before the third file...")
    if run_python_file(FIRST_FILE):
        st.info("[INFO] Now running the third file.")
        # If third file fails, you can decide how many attempts you want, etc.
        while not run_python_file(THIRD_FILE):
            st.warning("[WARNING] Third file failed. Retrying...")
            # For demonstration, we break to avoid infinite loop
            break
    else:
        st.error("[ERROR] Could not run first file again before third file.")

# ----------------------------------------------------------------------------
# Streamlit UI
# ----------------------------------------------------------------------------
st.title("Streamlit Scheduling/Timer Demo")

st.write("""
**Disclaimer:** 
This example uses `time.sleep` to illustrate scheduling in a naive manner, 
which will block the Streamlit UI. For production scheduling, consider:
- Running the scheduled tasks externally (e.g., cron job, Airflow, etc.).
- Using a background thread or asynchronous approach.
- Using Streamlit’s [experimental async features](https://docs.streamlit.io/library/api-reference/control-flow/st.experimental.asyncio).
""")

# Simple button to trigger the "timer" logic once
if st.button("Run Timer Logic"):
    start_timer()
    st.success("Timer logic has run (see logs above).")
