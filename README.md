# ATOM Auto-Compounding Script

This script helps to automatically claim and restake ATOM (Cosmos Hub) staking rewards. It is designed to be run manually or scheduled as a cron job.

**Version:** 0.1.0 (Initial functional version)

## !!! IMPORTANT SECURITY WARNINGS !!!

*   **MNEMONIC HANDLING:** The current version of this script prompts for your wallet's mnemonic phrase directly in the console each time it needs to sign a transaction (claim or stake). **THIS IS EXTREMELY INSECURE.** Your mnemonic grants full control over your funds. Entering it into a script poses significant security risks, including exposure through shell history, shoulder surfing, or if the script's environment is compromised.
*   **FOR DEVELOPMENT & TESTING ONLY:** This method is intended strictly for development and testing with small, non-critical amounts.
*   **DO NOT USE WITH MAINNET ACCOUNTS CONTAINING SIGNIFICANT VALUE.**
*   Future versions should implement more secure key management (e.g., using environment variables, OS keychain, or integration with hardware wallets if feasible for a script).
*   **USE AT YOUR OWN RISK.** You are solely responsible for the security of your private keys and any actions performed by this script.

## Prerequisites

*   Python 3.7+
*   pip (Python package installer)

## Installation

1.  **Clone the repository or download the script files.**
    ```bash
    # If it were a git repo:
    # git clone <repository_url>
    # cd atom-auto-compounder
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

## Running the Script

1.  **Ensure your virtual environment is activated** (if you created one).
2.  **Run the script from your terminal:**
    ```bash
    python atom_compounder.py
    ```
3.  **Follow the prompts:**
    *   If you have claimable rewards and a validator configured for staking, the script will ask for your wallet's mnemonic phrase to authorize transactions. **Remember the security risks mentioned above.**

## Script Workflow

The script performs the following actions:
1.  Loads configuration from `config.json`.
2.  Queries your ATOM account balance.
3.  Queries your available staking rewards and identifies validators you've delegated to.
4.  If rewards are available:
    *   Prompts for your mnemonic phrase.
    *   Constructs and broadcasts a transaction to claim rewards from all validators.
    *   If claiming is successful and `validator_address` is configured:
        *   Constructs and broadcasts a transaction to stake the (just claimed) rewards to your specified validator.
5.  Prints logs of its actions and any errors to the console.

## Disclaimer

*   This script is provided "as is", without warranty of any kind.
*   The authors or contributors are not responsible for any financial loss or other damages resulting from the use of this script.
*   **Always review the code and understand the risks before running any script that handles cryptographic keys or interacts with blockchains.**
*   Test thoroughly with small amounts on a testnet or with a non-critical wallet before using with significant funds.

```
