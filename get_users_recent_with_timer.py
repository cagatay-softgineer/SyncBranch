import time
import subprocess
import os
import sys
from cmd_gui_kit import CmdGUI  # Import the CmdGUI class for visual enhancements

# Check if '--debug' is passed as a command-line argument
DEBUG_MODE = '--debug' in sys.argv
WARNING_MODE = '--warning' in sys.argv
ERROR_MODE = '--error' in sys.argv

def run_python_file(file_path, gui):
    """Run a Python file and check its correctness."""
    if not os.path.exists(file_path):
        gui.status(f"[ERROR] The file {file_path} does not exist.", status="error")
        return False
    
    try:
        # Run the file and capture output
        gui.spinner(duration=2, message=f"Running {file_path}...")  # Show a spinner while running the file
        result = subprocess.run(['python', file_path], capture_output=True, text=True)
        
        # Check if there was any error during execution
        if result.returncode != 0:
            gui.status(f"[ERROR] running {file_path}:", status="error")
            gui.log(result.stderr, level="error")  # Log error if any
            return False
        else:
            gui.status(f"[INFO] Output of {file_path}:")
            gui.log(result.stdout, level="info")  # Log standard output if no error
            return True
        
    except Exception as e:
        gui.status(f"[ERROR] An error occurred while running {file_path}: {e}", status="error")
        return False

def start_timer(first_file_path, second_file_path, third_file_path,fourth_file_path, gui):
    """Start the timer and handle the execution flow based on the intervals."""
    first_file_last_run = 0  # Track when the first file was last run
    second_file_interval = 7200  # 7200 seconds (approximately 3 min 47 sec * 30)
    second_file_runs = 0
    max_runs = 12

    while second_file_runs < max_runs:
        current_time = time.time()
        
        # Check if the first file needs to run (every 3600 seconds)
        if current_time - first_file_last_run >= 3300:
            gui.status(f"[INFO] Running the first file: {first_file_path}...", status="info")
            if run_python_file(first_file_path, gui):
                first_file_last_run = current_time  # Update the last run time of the first file
                gui.status("[INFO] First file has completed. No need to run the second file.", status="info")
                second_file_runs = 0  # Reset the second file runs since the first file ran successfully
            else:
                if DEBUG_MODE or WARNING_MODE:
                    gui.status("[WARNING] First file failed. The second file will not run.", status="warning")
                break  # If the first file fails, stop the execution of the second file

        # If it's time to run the second file
        if second_file_runs < max_runs and (current_time - first_file_last_run < 3600):
            gui.status(f"[INFO] Running the second file: {second_file_path}...", status="info")
            if run_python_file(second_file_path, gui):
                second_file_runs += 1
            else:
                if DEBUG_MODE or WARNING_MODE:
                    gui.status(f"[WARNING] Second file run failed at attempt {second_file_runs + 1}.", status="warning")
        
        
        
        # Wait for the second file interval before checking again
        if second_file_runs < max_runs:
            run_python_file(fourth_file_path, gui)
            gui.status(f"[INFO] Waiting for {second_file_interval} seconds before running the second file again...\n", status="info")
            time.sleep(second_file_interval)

    # Run the third file after the first file completes successfully
    if run_python_file(first_file_path, gui):
        while not run_python_file(third_file_path, gui):
            return

if __name__ == "__main__":
    # Initialize CmdGUI for visual output
    gui = CmdGUI()

    # Paths to the Python files
    first_file = 'sync-branch/auth/update_tokens.py'  # Replace with your first Python file path
    second_file = 'sync-branch/api/get_recent.py'  # Replace with your second Python file path
    third_file = 'sync-branch/api/get_users_liked_tracks.py'  # Replace with your third Python file path
    fourth_file = 'sync-branch/api/update_audio_features.py'  # Replace with your fourth Python file path
    
    # Start the timer with specified intervals
    start_timer(first_file, second_file, third_file,fourth_file, gui)
