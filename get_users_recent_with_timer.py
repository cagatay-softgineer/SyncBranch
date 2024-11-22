import time
import subprocess
import os
import sys

# Check if '--debug' is passed as a command-line argument
DEBUG_MODE = '--debug' in sys.argv
WARNING_MODE = '--warning' in sys.argv
ERROR_MODE = '--error' in sys.argv

def run_python_file(file_path):
    """Run a Python file and check its correctness."""
    if not os.path.exists(file_path):
        print(f"[ERROR] The file {file_path} does not exist.")
        return False
    
    try:
        # Run the file and capture output
        result = subprocess.run(['python', file_path], capture_output=True, text=True)
        
        # Check if there was any error during execution
        if result.returncode != 0:
            print(f"[ERROR] running {file_path}:")
            print(result.stderr)  # Print error if any
            return False
        else:
            print(f"[INFO] Output of {file_path}:")
            print(result.stdout)  # Print standard output if no error
            return True
        
    except Exception as e:
        print(f"[ERROR] An error occurred while running {file_path}: {e}")
        return False

def start_timer(first_file_path, second_file_path):
    """Start the timer and handle the execution flow based on the intervals."""
    first_file_last_run = 0  # Track when the first file was last run
    second_file_interval = 7200  # 7200 seconds (approximately 3 min 47 sec * 30)
    second_file_runs = 0
    max_runs = 12

    while second_file_runs < max_runs:
        current_time = time.time()
        
        # Check if the first file needs to run (every 3600 seconds)
        if current_time - first_file_last_run >= 3300:
            print(f"[INFO] Running the first file: {first_file_path}...")
            if run_python_file(first_file_path):
                first_file_last_run = current_time  # Update the last run time of the first file
                print("[INFO] First file has completed. No need to run the second file.")
                second_file_runs = 0  # Reset the second file runs since the first file ran successfully
            else:
                if DEBUG_MODE or WARNING_MODE:
                    print("[WARNING] First file failed. The second file will not run.")
                break  # If the first file fails, stop the execution of the second file

        # If it's time to run the second file
        if second_file_runs < max_runs and (current_time - first_file_last_run < 3600):
            print(f"[INFO] Running the second file: {second_file_path}...")
            if run_python_file(second_file_path):
                second_file_runs += 1
            else:
                if DEBUG_MODE or WARNING_MODE:
                    print(f"[WARNING] Second file run failed at attempt {second_file_runs + 1}.")
        
        # Wait for the second file interval before checking again
        if second_file_runs < max_runs:
            print(f"[INFO] Waiting for {second_file_interval} seconds before running the second file again...\n")
            time.sleep(second_file_interval)
    if run_python_file(first_file_path):
        while not run_python_file(third_file):
            return

if __name__ == "__main__":
    # Paths to the Python files
    first_file = 'sync-branch/auth/update_tokens.py'  # Replace with your first Python file path
    second_file = 'sync-branch/api/get_recent.py'  # Replace with your second Python file path
    third_file = 'sync-branch/api/get_users_liked_tracks.py'
    
    # Start the timer with specified intervals
    start_timer(first_file, second_file)
