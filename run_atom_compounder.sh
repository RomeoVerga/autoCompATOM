#!/data/data/com.termux/files/usr/bin/bash
# Wrapper script for running atom_compounder.py via Termux job scheduler

echo "--- Wrapper script started at $(date) ---"

# --- USER CONFIGURATION REQUIRED ---
# 1. Set your ATOM Mnemonic phrase below.
#    IMPORTANT: Storing the mnemonic directly in a script has security implications.
#    Ensure this script file is protected (e.g., chmod 600).
export ATOM_MNEMONIC="YOUR_WALLET_MNEMONIC_PHRASE_HERE"

# 2. Set the full path to the directory where atom_compounder.py and config.json are located.
#    Example: If you cloned/copied the script into a folder named "atom-script" in your Termux home:
#    SCRIPT_DIR="/data/data/com.termux/files/home/atom-script"
SCRIPT_DIR="/data/data/com.termux/files/home/YOUR_SCRIPT_DIRECTORY_HERE"

# 3. Set the name of your main Python script.
PYTHON_SCRIPT_NAME="atom_compounder.py"

# 4. Define a log file path (optional, but recommended for scheduled tasks).
#    Ensure the directory exists or adjust the path.
LOG_FILE="${SCRIPT_DIR}/atom_compounder_job.log"

# 5. Python executable path (Uncomment the one you need)
#    If using Termux's main Python:
PYTHON_EXEC="/data/data/com.termux/files/usr/bin/python"
#    If using a virtual environment named 'venv' inside SCRIPT_DIR:
# PYTHON_EXEC="${SCRIPT_DIR}/venv/bin/python"

# --- END OF USER CONFIGURATION ---

# Navigate to the script's directory
cd "${SCRIPT_DIR}"
if [ $? -ne 0 ]; then
  echo "Error: Could not navigate to SCRIPT_DIR: ${SCRIPT_DIR}" >> ${LOG_FILE}
  exit 1
fi

# Activate virtual environment if PYTHON_EXEC points to it
# (The venv python executable directly runs python, no separate activate needed here if path is correct)
# If you uncommented the venv PYTHON_EXEC, ensure venv exists and is setup.

echo "--- Running Python script: ${PYTHON_SCRIPT_NAME} at $(date) ---" >> ${LOG_FILE}
# Execute the Python script, redirecting stdout and stderr to the log file
${PYTHON_EXEC} ${PYTHON_SCRIPT_NAME} >> ${LOG_FILE} 2>&1
SCRIPT_EXIT_CODE=$?

if [ ${SCRIPT_EXIT_CODE} -eq 0 ]; then
  echo "--- Python script finished successfully at $(date) ---" >> ${LOG_FILE}
else
  echo "--- Python script exited with error code ${SCRIPT_EXIT_CODE} at $(date) ---" >> ${LOG_FILE}
fi

echo "--- Wrapper script finished at $(date) ---"

exit ${SCRIPT_EXIT_CODE}
