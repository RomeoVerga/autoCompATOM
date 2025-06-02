# ATOM Auto-Compounding Script

This script helps to automatically claim and restake ATOM (Cosmos Hub) staking rewards. It is designed to be run manually or scheduled as a cron job.

**Version:** 0.1.0 (Initial functional version)

## !!! IMPORTANT SECURITY WARNINGS !!!

*   **MNEMONIC HANDLING VIA ENVIRONMENT VARIABLE:** This script now requires your wallet's mnemonic phrase to be set as an environment variable named `ATOM_MNEMONIC`. While this is an improvement over direct console input, the security of your mnemonic now depends entirely on the security of this environment variable and the system it's set on.
*   **PROTECT YOUR ENVIRONMENT VARIABLE:** If an attacker gains access to your user account or system where this environment variable is set, they can potentially retrieve the mnemonic.
*   **MINIMIZE EXPOSURE:** Avoid setting the environment variable system-wide if possible. Prefer setting it in a way that limits its scope and lifetime (e.g., within a specific terminal session for manual runs, or carefully configured for a cron job's specific environment).
*   **FOR DEVELOPMENT & TESTING:** This method is an improvement, but for handling significant value, consider more advanced solutions like hardware wallets (not directly scriptable in this manner) or dedicated secrets management systems.
*   **USE AT YOUR OWN RISK.** You are solely responsible for the security of your private keys and any actions performed by this script.

## Prerequisites

*   Python 3.7+
*   pip (Python package installer)

## Installation

1.  **Clone the repository or download the script files.**
    ```bash
    # If it were a git repo:
    # git clone <repository_url>
    # cd <repository_directory_name>
    ```
    For now, ensure you have `atom_compounder.py`, `requirements.txt`, and `config.sample.json` in the same directory.

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Create your configuration file:**
    Copy the sample configuration file `config.sample.json` to `config.json`:
    ```bash
    cp config.sample.json config.json
    ```

2.  **Edit `config.json` with your details:**

    ```json
    {
      "atom_address": "YOUR_ATOM_ADDRESS_HERE",
      "validator_address": "YOUR_PREFERRED_VALIDATOR_ADDRESS_HERE (optional, for staking)",
      "rpc_endpoint": "https://rest.cosmos.directory/cosmoshub",
      "chain_id": "cosmoshub-4",
      "gas_price": "0.0025uatom",
      "gas_limit": "300000",
      "fee_denom": "uatom",
      "memo": "Auto-compounded by script"
    }
    ```

    *   `atom_address`: **Required.** Your Cosmos ATOM address (e.g., `cosmos1...`).
    *   `validator_address`: **Required for staking.** The address of the validator you want to delegate/re-delegate your claimed ATOM to (e.g., `cosmosvaloper1...`). If left empty or as the placeholder, staking will be skipped.
    *   `rpc_endpoint`: **Required.** The URL of a Cosmos Hub LCD/REST API endpoint. This is used for querying balances, rewards, account details, and broadcasting transactions.
        *   Public endpoints like `https://rest.cosmos.directory/cosmoshub` (used as default in sample) can work, but may have rate limits or not support transaction broadcasting reliably.
        *   For better reliability, consider running your own node or using a dedicated node provider.
        *   **Ensure this endpoint is for the correct network (Cosmos Hub mainnet for `cosmoshub-4`).**
    *   `chain_id`: **Required.** The chain ID of the network (e.g., `cosmoshub-4` for Cosmos Hub mainnet).
    *   `gas_price`: **Required.** The gas price to use for transactions (e.g., `"0.0025uatom"`). This determines the fee per unit of gas. Check current network conditions for optimal values.
    *   `gas_limit`: **Required.** The maximum gas units to allocate for a transaction (e.g., `"300000"` for claims, `"350000"` for delegations - adjust as needed). If set too low, transactions will fail.
    *   `fee_denom`: **Required.** The denomination for fees (usually `uatom` for Cosmos Hub, which is micro-ATOM).
    *   `memo`: Optional. A memo to include with your transactions.

## Secure Mnemonic Handling (Using Environment Variable)

This script requires your wallet's mnemonic phrase to perform transactions (claiming rewards and staking). It expects this mnemonic to be provided via an environment variable named `ATOM_MNEMONIC`.

### How to Set the `ATOM_MNEMONIC` Environment Variable

**Linux/macOS:**

*   **For the current terminal session only (temporary):**
    Open your terminal and type:
    ```bash
    export ATOM_MNEMONIC="word1 word2 word3 ... word24"
    ```
    Replace `"word1 word2 ... word24"` with your actual mnemonic phrase. The phrase should be enclosed in quotes if it contains spaces (which it will).
    **Note:** This variable will only be available in the current terminal session. If you close the terminal, you'll need to set it again.

*   **For persistent setting (add to shell configuration file):**
    You can add the `export` command to your shell's startup file (e.g., `~/.bashrc`, `~/.zshrc`, `~/.profile`). This way, the variable will be set every time you open a new terminal.
    1.  Open your shell configuration file with a text editor (e.g., `nano ~/.bashrc`).
    2.  Add the line: `export ATOM_MNEMONIC="your actual mnemonic phrase"`
    3.  Save the file and close the editor.
    4.  Apply the changes by sourcing the file (e.g., `source ~/.bashrc`) or by opening a new terminal session.
    **Security Note:** Storing the mnemonic directly in shell configuration files is convenient but means it's stored in plain text on your filesystem. Ensure your user account and home directory are well-protected.

**Windows:**

*   **For the current Command Prompt session only (temporary):**
    ```cmd
    set ATOM_MNEMONIC=word1 word2 word3 ... word24
    ```
    (No quotes are typically needed unless the mnemonic itself contains special CMD characters, which is unlikely for standard BIP39 mnemonics).

*   **For the current PowerShell session only (temporary):**
    ```powershell
    $Env:ATOM_MNEMONIC="word1 word2 word3 ... word24"
    ```

*   **For persistent setting (System Environment Variables):**
    1.  Search for "environment variables" in the Windows search bar and select "Edit the system environment variables".
    2.  In the System Properties window, click the "Environment Variables..." button.
    3.  Under "User variables for [your_username]" (recommended for user-specific) or "System variables" (for all users, less recommended for secrets), click "New...".
    4.  Variable name: `ATOM_MNEMONIC`
    5.  Variable value: `your actual mnemonic phrase`
    6.  Click OK on all windows. You may need to restart your Command Prompt, PowerShell, or even your computer for the changes to take full effect in all contexts.

### Security Best Practices for `ATOM_MNEMONIC`:

*   **Restrict Permissions:** If saving to a file like `.bashrc`, ensure the file has restrictive read/write permissions (e.g., only readable by your user).
*   **Avoid Shell History:** Be careful if typing the `export` command directly into your shell. Some shells might save this command (including the mnemonic) in their history file. Consider temporarily disabling history or using methods that don't save the command (e.g., prefixing with a space in some `bash` configurations).
*   **Understand Scope:** Be aware of where and how the environment variable is accessible. For scheduled tasks (cron jobs), ensure the environment for the job includes this variable securely.
*   **This method is a step up from direct console input but is not foolproof.** The mnemonic is still in plain text in the process's environment while the script runs. Protect the system running the script.

## Running the Script

1.  **Ensure your virtual environment is activated** (if you created one).
2.  **Set the `ATOM_MNEMONIC` Environment Variable:**
    *   Before running the script, you MUST set the `ATOM_MNEMONIC` environment variable to your wallet's 12 or 24-word mnemonic phrase. See the "Secure Mnemonic Handling (Using Environment Variable)" section above for details and security advice.
    *   **Example (Linux/macOS - temporary for current session):**
        ```bash
        export ATOM_MNEMONIC="your twelve twentyfour word mnemonic phrase just like this no commas"
        ```
3.  **Run the script from your terminal:**
    ```bash
    python atom_compounder.py
    ```
4.  **Monitor Output:** The script will log its actions to the console. It will no longer prompt for the mnemonic. If `ATOM_MNEMONIC` is not set, it will print an error and skip transactions.

## Script Workflow

The script performs the following actions:
1.  Loads configuration from `config.json`.
2.  Queries your ATOM account balance.
3.  Queries your available staking rewards and identifies validators you've delegated to.
4.  If rewards are available:
    *   Retrieves the mnemonic from the `ATOM_MNEMONIC` environment variable.
    *   If the mnemonic is found:
        *   Constructs and broadcasts a transaction to claim rewards from all validators.
        *   If claiming is successful and `validator_address` is configured:
            *   Constructs and broadcasts a transaction to stake the (just claimed) rewards to your specified validator.
    *   If the mnemonic is not found, it skips transaction-related operations.
5.  Prints logs of its actions and any errors to the console.

## Scheduling Weekly Execution

Once you have configured the script and successfully tested it manually (ensuring `ATOM_MNEMONIC` is set in your environment), you can automate its execution using your operating system's task scheduler.

**Important Considerations for Scheduled Tasks:**

*   **Environment Variables:** The `ATOM_MNEMONIC` environment variable (and any others like `PATH` if your Python installation isn't standard) must be available to the execution environment of the scheduled task. How you set this depends on the OS and scheduler. For cron, this often means setting variables within the crontab itself or in a script that the cron job calls.
*   **Full Paths:** It's best practice to use full absolute paths to the Python interpreter and the `atom_compounder.py` script in your scheduler configuration to avoid issues with `PATH` lookups.
*   **Logging:** When run as a scheduled task, console output might be mailed to you (cron) or logged to a file, depending on configuration. You might want to redirect the script's output to a dedicated log file. Example: `python /path/to/atom_compounder.py >> /path/to/atom_compounder.log 2>&1`.
*   **Permissions:** Ensure the user account under which the scheduled task runs has the necessary permissions to execute the script and access any required files (though this script primarily needs network access and its config).

### Linux/macOS (using cron)

Cron is a time-based job scheduler in Unix-like operating systems.

1.  **Open your crontab for editing:**
    ```bash
    crontab -e
    ```
    If it's your first time, it might ask you to choose an editor.

2.  **Add a line to schedule the script.** To run the script every Monday at 3:00 AM, for example:

    ```cron
    # Example: Run every Monday at 3:00 AM
    # Ensure ATOM_MNEMONIC is set in a way accessible by cron,
    # either directly here (less secure for crontab), or in a wrapper script,
    # or if the system user's environment is fully loaded by cron (less common).

    # Option 1: Define ATOM_MNEMONIC directly in crontab (use with caution)
    # ATOM_MNEMONIC="your actual mnemonic phrase"
    # 0 3 * * 1 /usr/bin/python3 /full/path/to/your/atom_compounder.py >> /full/path/to/your/atom_compounder.log 2>&1

    # Option 2: Load ATOM_MNEMONIC from .bashrc or similar (if your cron implementation sources it - check docs)
    # This is often NOT the default behavior for cron's minimal environment.
    # 0 3 * * 1 . $HOME/.bashrc; /usr/bin/python3 /full/path/to/your/atom_compounder.py >> /full/path/to/your/atom_compounder.log 2>&1

    # Option 3: Recommended - Use a wrapper script
    # Create a script like /full/path/to/your/run_atom_script.sh:
    #   #!/bin/bash
    #   export ATOM_MNEMONIC="your actual mnemonic phrase"
    #   # Or source a file that exports it:
    #   # source /path/to/my_secure_env_vars.sh
    #   /usr/bin/python3 /full/path/to/your/atom_compounder.py >> /full/path/to/your/atom_compounder.log 2>&1
    # Make it executable: chmod +x /full/path/to/your/run_atom_script.sh
    # Then in crontab:
    0 3 * * 1 /full/path/to/your/run_atom_script.sh
    ```

    *   **Breakdown of `0 3 * * 1`**:
        *   `0`: Minute (0-59) -> 0th minute
        *   `3`: Hour (0-23) -> 3 AM
        *   `*`: Day of the month (1-31) -> Every day
        *   `*`: Month (1-12) -> Every month
        *   `1`: Day of the week (0-7, where 0 and 7 are Sunday, 1 is Monday) -> Monday
    *   Replace `/usr/bin/python3` with the actual path to your Python 3 interpreter (you can find this with `which python3`).
    *   Replace `/full/path/to/your/atom_compounder.py` with the actual full path to the script.
    *   Replace `/full/path/to/your/atom_compounder.log` with your desired log file path.
    *   `>> ... 2>&1`: Appends both standard output (stdout) and standard error (stderr) to the log file.

3.  **Save and exit.** Cron will automatically apply the changes.

    **Managing `ATOM_MNEMONIC` for Cron:**
    Cron jobs run in a minimal environment. The most reliable way to ensure `ATOM_MNEMONIC` is available is often by:
    *   **Setting it in the crontab file itself** (as shown in Option 1). However, some consider this less secure as the crontab might be more accessible than user profile scripts.
    *   **Using a wrapper shell script** (Option 3, generally recommended). The wrapper script exports the variable and then calls your Python script. This keeps the crontab clean and centralizes environment setup for the job.
    *   Some cron systems might allow sourcing a user's profile, but this is not universally reliable.

### Windows (using Task Scheduler)

1.  **Open Task Scheduler:** Search for "Task Scheduler" in the Start Menu.
2.  **Create Basic Task (or Create Task for more control):**
    *   In the right-hand pane, click "Create Basic Task...".
    *   **Name:** Give your task a name (e.g., "Weekly ATOM Compounding").
    *   **Description:** (Optional)
    *   **Trigger:** Select "Weekly". Specify the start date, time, and "Recur every: 1 weeks on: Monday" (or your desired day).
    *   **Action:** Select "Start a program".
        *   **Program/script:** Enter the full path to your Python interpreter (e.g., `C:\Python39\python.exe` or `C:\Users\YourUser\venv\Scripts\python.exe` if using a venv).
        *   **Add arguments (optional):** Enter the full path to your `atom_compounder.py` script (e.g., `C:\path\to\your\atom_compounder.py`).
        *   **Start in (optional):** Enter the directory where your script is located (e.g., `C:\path\to\your\`). This helps the script find `config.json` if it's using relative paths (though this script opens `config.json` directly, so it should be fine, but good practice).
3.  **Set Environment Variable for the Task:**
    *   This is the crucial part for `ATOM_MNEMONIC`. After creating the task (or if you use "Create Task" for more options initially), find your task in the Task Scheduler Library, right-click it, and select "Properties".
    *   Under the "Actions" tab, select your "Start a program" action and click "Edit...".
    *   Unfortunately, Task Scheduler's GUI doesn't have a direct way to set environment variables *for just that specific task action*.
    *   **Recommended Solutions for `ATOM_MNEMONIC` with Task Scheduler:**
        1.  **System-wide or User Environment Variable:** Set `ATOM_MNEMONIC` as a persistent User environment variable (as described in the "Secure Mnemonic Handling" section). The Task Scheduler task, if run under your user account, will inherit these. This is the simplest if you're okay with the variable being generally available to your user session.
        2.  **Wrapper Batch/PowerShell Script:** Create a `.bat` or `.ps1` script that first sets `ATOM_MNEMONIC` and then calls the Python script.
            *   **Batch (`.bat`):**
                ```batch
                @echo off
                set ATOM_MNEMONIC=your actual mnemonic phrase
                C:\Path\To\Python\python.exe C:\Path\To\Your\atom_compounder.py >> C:\Path\To\Your\atom_compounder.log 2>&1
                ```
            *   **PowerShell (`.ps1`):**
                ```powershell
                $env:ATOM_MNEMONIC="your actual mnemonic phrase"
                & "C:\Path\To\Python\python.exe" "C:\Path\To\Your\atom_compounder.py" >> "C:\Path\To\Your\atom_compounder.log" # PowerShell redirection is different
                ```
            Then, schedule this wrapper script in Task Scheduler instead of directly calling Python.
4.  **Further Configuration (Properties):**
    *   Under the "General" tab, you might want to set "Run whether user is logged on or not" (may require password input). Ensure the user account has rights.
    *   Under "Conditions", you can specify power settings, etc.
    *   Under "Settings", configure retry attempts or what to do if the task fails.
5.  Click **OK** to save the task.

By following these steps, you can have your `atom_compounder.py` script run automatically on a weekly basis. Remember to test your scheduled task setup thoroughly to ensure it runs correctly and handles the environment variable as expected.

## Experimental: Running with Termux on Android

This section provides guidance on how to run the ATOM Auto-Compounding script on an Android device using Termux. Please note that this is an **experimental approach** and comes with significant limitations regarding reliability and security compared to running on a desktop or server.

**!!! IMPORTANT CAVEATS FOR TERMUX USAGE !!!**

*   **Reliability of Scheduling:** Android's aggressive battery optimization and process management can terminate Termux or its scheduled jobs, especially when the phone is idle or the Termux app is not in the foreground. `termux-job-scheduler` attempts to mimic cron, but its effectiveness can be inconsistent. For critical, precisely timed weekly execution, this is likely **not reliable enough**.
*   **Security of Mnemonic:** While Termux provides a Linux-like environment, managing your `ATOM_MNEMONIC` securely is still a concern. It will be an environment variable within Termux's sandboxed environment. Ensure your device is secure.
*   **Power Consumption:** Running tasks in Termux, especially if `termux-wake-lock` is used to improve reliability, can consume more battery.
*   **User Intervention:** Expect that this method may require more manual checking and potential intervention than a server-based cron job.
*   **Termux Source:** It is highly recommended to install Termux from **F-Droid** as the Google Play Store version is outdated and no longer maintained.

**Steps to Run the Script with Termux (Manual Execution):**

1.  **Install Termux:**
    *   Download and install Termux from F-Droid: [https://f-droid.org/packages/com.termux/](https://f-droid.org/packages/com.termux/)
    *   You may also want to install the "Termux:API" add-on from F-Droid if you plan to explore more advanced scripting later (not strictly needed for this script).

2.  **Open Termux and Update Packages:**
    ```bash
    pkg update && pkg upgrade
    ```

3.  **Install Python and Git:**
    ```bash
    pkg install python git
    ```
    (Git is needed if you plan to clone a repository. If you're manually transferring files, you might not need git immediately).

4.  **Get the Script Files:**
    *   **Option A (If the script is in a Git repository):**
        ```bash
        git clone <repository_url>
        cd <repository_directory_name>
        ```
    *   **Option B (Manual Transfer):**
        *   You'll need to transfer `atom_compounder.py`, `requirements.txt`, and `config.sample.json` to your phone's storage in a location accessible by Termux.
        *   Termux can access shared storage after you run `termux-setup-storage`. This usually creates a symlink at `~/storage`. You can then navigate, e.g., to `~/storage/shared/Download` if you downloaded files there.
        *   Example: `cp ~/storage/shared/Download/atom_compounder.py .`

5.  **Set up Virtual Environment (Optional but Recommended):**
    (Assuming you are in the directory where you placed/cloned the script files)
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

6.  **Install Dependencies:**
    (If using a virtual environment, ensure it's activated)
    ```bash
    pip install -r requirements.txt
    ```

7.  **Configure the Script:**
    *   Copy `config.sample.json` to `config.json`:
        ```bash
        cp config.sample.json config.json
        ```
    *   Edit `config.json` with your details using a command-line editor available in Termux (e.g., `nano`, `vim`, or `micro` - install with `pkg install nano` for example):
        ```bash
        nano config.json
        ```
        Fill in your ATOM address, validator address, RPC endpoint, etc., as described in the main "Configuration" section of this README.

8.  **Set the `ATOM_MNEMONIC` Environment Variable:**
    *   In your Termux session, set the variable:
        ```bash
        export ATOM_MNEMONIC="your twelve twentyfour word mnemonic phrase just like this"
        ```
    *   **Note:** This variable is only set for the current Termux session. For scheduled tasks, ensuring this variable is available is more complex (see scheduling section below). For manual runs, you'll set this each time you start a new session.

9.  **Run the Script Manually:**
    ```bash
    python atom_compounder.py
    ```
    Verify it runs correctly and interacts with the network as expected.

### Scheduling with `termux-job-scheduler` (Experimental)

Termux provides a package called `termux-job-scheduler` that allows you to schedule scripts to run periodically, similar to cron. However, due to Android's power-saving features, these jobs may not always run reliably or at the exact scheduled time, especially if the device is asleep or Termux is not in the foreground.

**1. Install `termux-job-scheduler`:**
   Open Termux and run:
   ```bash
   pkg install termux-job-scheduler
   ```

**2. Prepare the Wrapper Script for Execution:**
   This project now includes a template wrapper script named `run_atom_compounder.sh` designed for Termux.

   *   **Copy the Wrapper Script:**
       First, copy this script from the project directory (e.g., where you cloned or downloaded it) to a location in your Termux home directory. For example, if your project files are in `~/storage/shared/atom-script-project/` and you want to place the wrapper in your Termux home:
       ```bash
       cp ~/storage/shared/atom-script-project/run_atom_compounder.sh ~/run_atom_compounder.sh
       ```
       Adjust the source path based on where you have the project files accessible from Termux (you might need to run `termux-setup-storage` first if copying from shared storage).

   *   **Edit the Wrapper Script:**
       Open the copied `~/run_atom_compounder.sh` script with a text editor (e.g., `nano`):
       ```bash
       nano ~/run_atom_compounder.sh
       ```
       Carefully review and **edit the "USER CONFIGURATION REQUIRED" section** at the top of the script:
       *   Set your `ATOM_MNEMONIC` (ensure the phrase is correct and understand the security implications of storing it here).
       *   Update `SCRIPT_DIR` to the **full path** where your `atom_compounder.py` and `config.json` files are located *within Termux's filesystem* (e.g., `/data/data/com.termux/files/home/my-atom-script`).
       *   Verify `PYTHON_SCRIPT_NAME` (should be `atom_compounder.py`).
       *   Adjust `LOG_FILE` path if desired.
       *   Choose and uncomment the correct `PYTHON_EXEC` path (Termux's system Python or Python from a virtual environment within your `SCRIPT_DIR`).

   *   **Make the Wrapper Script Executable:**
       ```bash
       chmod +x ~/run_atom_compounder.sh
       ```

**3. Schedule the Wrapper Script:**
   To schedule the script to run, for example, every Sunday at 3:00 AM:
   ```bash
   termux-job-scheduler --script ~/run_atom_compounder.sh --period weekly --time 03:00 --weekday sun
   ```
   *   `--script ~/run_atom_compounder.sh`: Path to your executable wrapper script.
   *   `--period weekly`: Sets the job to run weekly. Other options: `hourly`, `daily`, `monthly`, `boot`.
   *   `--time 03:00`: Sets the time (24-hour format).
   *   `--weekday sun`: Sets the day for weekly jobs (mon, tue, wed, thu, fri, sat, sun).

   You can view scheduled jobs with `termux-job-scheduler -l` and cancel them with `termux-job-scheduler -c <JOB_ID>`.

**4. Improving Reliability (Optional - `termux-wake-lock`):**
   To prevent Termux from being killed by Android's battery optimizations, you might need to acquire a wake lock.
   *   Run `termux-wake-lock` in a separate Termux session before the job is expected to run. This keeps the CPU partially awake.
   *   Run `termux-wake-unlock` to release it.
   This will consume more battery. Automating the wake lock around the job execution time is complex and outside the scope of simple `termux-job-scheduler` usage.

**RELIABILITY WARNINGS (Reiteration):**

*   **Android Power Management:** Android is designed to save battery by stopping apps and processes that are not actively in the foreground. Scheduled jobs in Termux are highly susceptible to this. They might be delayed or not run at all, especially on heavily customized Android versions or with aggressive battery savers.
*   **Test Thoroughly:** If you choose to use this, test extensively to see if it works reliably on your specific device and Android version.
*   **Not for Critical Tasks:** Do not rely on this method for tasks that absolutely *must* run at a specific time without fail. For critical scheduling, a proper server environment is recommended.

This setup is offered as an option for users who understand and accept these limitations.

## Disclaimer

*   This script is provided "as is", without warranty of any kind.
*   The authors or contributors are not responsible for any financial loss or other damages resulting from the use of this script.
*   **Always review the code and understand the risks before running any script that handles cryptographic keys or interacts with blockchains.**
*   Test thoroughly with small amounts on a testnet or with a non-critical wallet before using with significant funds.

```
