import json
import sys
import requests
import base64 # For encoding Tx bytes for broadcasting

# Imports from cosmospy-protobuf (or compatible cosmospy)
from cosmospy_protobuf.cosmos.distribution.v1beta1.tx_pb2 import MsgWithdrawDelegatorReward
from cosmospy_protobuf.cosmos.staking.v1beta1.tx_pb2 import MsgDelegate # New import
from cosmospy_protobuf.cosmos.base.v1beta1.coin_pb2 import Coin as ProtoCoin
from cosmospy import Transaction, Wallet
# SyncMode from cosmospy.typing is for its own broadcast() method.
# We are manually POSTing, so we'll use string modes like "BROADCAST_MODE_SYNC".

CONFIG_FILE_NAME = "config.json"

def load_config():
    """Loads configuration from config.json."""
    try:
        with open(CONFIG_FILE_NAME, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Configuration file '{CONFIG_FILE_NAME}' not found.")
        print(f"Please copy 'config.sample.json' to '{CONFIG_FILE_NAME}' and fill in your details.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"ERROR: Could not decode JSON from '{CONFIG_FILE_NAME}'. Please ensure it is valid JSON.")
        sys.exit(1)

    required_keys = ["atom_address", "rpc_endpoint", "chain_id"]
    missing_keys = [key for key in required_keys if key not in config or not config[key]]
    if missing_keys:
        print(f"ERROR: Missing or empty essential configuration keys in '{CONFIG_FILE_NAME}': {', '.join(missing_keys)}")
        sys.exit(1)

    if config.get("atom_address") == "YOUR_ATOM_ADDRESS_HERE":
        print(f"WARNING: Please update 'atom_address' in '{CONFIG_FILE_NAME}' with your actual ATOM address.")

    config.setdefault("validator_address", "") # Optional, can be empty
    config.setdefault("gas_price", "0.025uatom")
    config.setdefault("gas_limit", "300000")
    config.setdefault("fee_denom", "uatom")
    config.setdefault("memo", "Auto-compounded by script")

    return config

def get_account_details(atom_address: str, lcd_endpoint: str):
    """Queries account number and sequence for a given ATOM address."""
    url = f"{lcd_endpoint}/cosmos/auth/v1beta1/accounts/{atom_address}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        account_data = data.get("account", {})

        if account_data.get("@type") == "/cosmos.auth.v1beta1.BaseAccount" or \
           account_data.get("account_number") is not None:
            account_number = int(account_data.get("account_number", 0))
            sequence = int(account_data.get("sequence", 0))
            return account_number, sequence
        else:
            if account_data.get("account_number") is None:
                 print(f"ERROR: Could not determine account_number for {atom_address}. The account might not exist on chain or is not a typical account. Type: {account_data.get('@type')}")
                 return None, None
            print(f"WARN: Account {atom_address} data found but might not be a BaseAccount or account_number is None. Type: {account_data.get('@type')}. Using found values.")
            return int(account_data.get("account_number",0)), int(account_data.get("sequence",0))

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Could not query account details from {url}: {e}")
        return None, None
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        print(f"ERROR: Could not decode or parse JSON for account details from {url}: {e}")
        return None, None

def get_account_balance(atom_address: str, lcd_endpoint: str):
    """Queries the account balance for a given ATOM address via LCD endpoint."""
    url = f"{lcd_endpoint}/cosmos/bank/v1beta1/balances/{atom_address}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        for balance in data.get("balances", []):
            if balance.get("denom") == "uatom": # Assuming fee_denom from config is 'uatom'
                return int(balance.get("amount", 0))
        return 0
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Could not query account balance from {url}: {e}")
        return None
    except json.JSONDecodeError:
        print(f"ERROR: Could not decode JSON response from {url}.")
        return None

def get_staking_rewards(delegator_address: str, lcd_endpoint: str):
    """Queries total staking rewards and the list of validators with rewards."""
    url = f"{lcd_endpoint}/cosmos/distribution/v1beta1/delegators/{delegator_address}/rewards"
    total_uatom_rewards = 0
    validators_with_rewards = []
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        for reward_entry in data.get("rewards", []):
            validator_address = reward_entry.get("validator_address")
            if validator_address:
                current_validator_reward = 0
                for reward_coin in reward_entry.get("reward", []):
                    if reward_coin.get("denom") == "uatom": # Assuming fee_denom is 'uatom'
                        try:
                            amount_float = float(reward_coin.get("amount", 0))
                            current_validator_reward += int(amount_float)
                        except ValueError:
                            print(f"WARN: Could not parse uatom reward amount for validator {validator_address}: {reward_coin.get('amount')}")
                if current_validator_reward > 0:
                     validators_with_rewards.append(validator_address)
                     total_uatom_rewards += current_validator_reward

        return total_uatom_rewards, list(set(validators_with_rewards))
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Could not query staking rewards from {url}: {e}")
        return None, []
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        print(f"ERROR: Could not decode or parse JSON reward data from {url}: {e}")
        return None, []

def claim_staking_rewards_tx(wallet: Wallet, lcd_endpoint: str, chain_id: str,
                               gas_limit: int, gas_price_str: str, fee_denom: str, memo: str,
                               validators_to_claim_from: list[str], delegator_address: str):
    """Creates, signs, and broadcasts a transaction to claim staking rewards."""
    if not validators_to_claim_from:
        print("INFO: No validators with rewards to claim from.")
        return None

    try:
        acc_num, acc_seq = get_account_details(delegator_address, lcd_endpoint)
        if acc_num is None or acc_seq is None:
            print("ERROR: Could not get account details (number/sequence). Cannot proceed with claiming rewards.")
            return None

        fee_amount_str = gas_price_str.replace(fee_denom, '')
        try:
            fee_price = float(fee_amount_str)
        except ValueError:
            print(f"ERROR: Invalid gas_price format in config: '{gas_price_str}'. Expected e.g. '0.025uatom'.")
            return None
        calculated_fee_amount = int(gas_limit * fee_price)
        final_fee_str = f"{calculated_fee_amount}{fee_denom}"

        tx = Transaction(
            privkey=wallet.private_key,
            account_num=acc_num,
            sequence=acc_seq,
            fee=final_fee_str,
            gas=gas_limit,
            memo=memo,
            chain_id=chain_id
        )

        print(f"INFO: Preparing to claim rewards from {len(validators_to_claim_from)} validator(s): {', '.join(validators_to_claim_from)}")
        for val_addr in validators_to_claim_from:
            msg = MsgWithdrawDelegatorReward(
                delegator_address=delegator_address,
                validator_address=val_addr
            )
            tx.add_message(msg, type_url="/cosmos.distribution.v1beta1.MsgWithdrawDelegatorReward")

        signed_tx_bytes = tx.form_signed_tx()

        broadcast_url = f"{lcd_endpoint}/cosmos/tx/v1beta1/txs"
        broadcast_payload = {
            "tx_bytes": base64.b64encode(signed_tx_bytes).decode('utf-8'),
            "mode": "BROADCAST_MODE_SYNC"
        }

        print(f"INFO: Broadcasting claim transaction to {broadcast_url}...")
        response = requests.post(broadcast_url, json=broadcast_payload, timeout=30)
        response.raise_for_status()

        tx_response_data = response.json()

        if tx_response_data.get("tx_response") and tx_response_data["tx_response"].get("code") == 0:
            print(f"SUCCESS: Claim rewards transaction broadcasted successfully!")
            print(f"  Tx Hash: {tx_response_data['tx_response'].get('txhash')}")
            return tx_response_data["tx_response"]
        else:
            code = tx_response_data.get('tx_response', {}).get('code', 'N/A')
            raw_log = tx_response_data.get('tx_response', {}).get('raw_log', 'No log available')
            txhash = tx_response_data.get('tx_response', {}).get('txhash', 'N/A')
            print(f"ERROR: Claim rewards transaction failed on chain.")
            print(f"  Tx Hash: {txhash}")
            print(f"  Code: {code}")
            print(f"  Raw Log: {raw_log}")
            return None

    except requests.exceptions.HTTPError as http_err:
        print(f"ERROR: HTTP error broadcasting claim rewards transaction: {http_err}")
        if http_err.response is not None:
            try:
                error_details = http_err.response.json()
                print(f"  Response Code: {error_details.get('code', 'N/A')}")
                print(f"  Response Message: {error_details.get('message', 'N/A')}")
                print(f"  Response Details: {error_details.get('details', 'N/A')}")
            except json.JSONDecodeError:
                print(f"  Raw Response: {http_err.response.text}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"ERROR: Network error broadcasting claim rewards transaction: {req_err}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred in claim_staking_rewards_tx: {e}")
        import traceback
        traceback.print_exc()
        return None

def stake_atom_tx(wallet: Wallet, lcd_endpoint: str, chain_id: str,
                     gas_limit: int, gas_price_str: str, fee_denom: str, memo: str,
                     delegator_address: str, validator_address: str, amount_uatom_to_stake: int):
    """Creates, signs, and broadcasts a transaction to stake ATOM."""
    if not validator_address:
        print("ERROR: Validator address not provided. Cannot stake.")
        return None
    if amount_uatom_to_stake <= 0:
        print("INFO: Amount to stake must be positive.")
        return None

    try:
        acc_num, acc_seq = get_account_details(delegator_address, lcd_endpoint)
        if acc_num is None or acc_seq is None:
            print("ERROR: Could not get account details (number/sequence). Cannot proceed with staking.")
            return None

        fee_amount_str = gas_price_str.replace(fee_denom, '')
        try:
            fee_price = float(fee_amount_str)
        except ValueError:
            print(f"ERROR: Invalid gas_price format in config: '{gas_price_str}'. Expected e.g. '0.025uatom'.")
            return None
        calculated_fee_amount = int(gas_limit * fee_price)
        final_fee_str = f"{calculated_fee_amount}{fee_denom}"

        tx = Transaction(
            privkey=wallet.private_key,
            account_num=acc_num,
            sequence=acc_seq,
            fee=final_fee_str,
            gas=gas_limit,
            memo=memo, # Using the passed memo, which might be "Auto-compounded by script - Staking"
            chain_id=chain_id
        )

        stake_amount_coin = ProtoCoin(denom=fee_denom, amount=str(amount_uatom_to_stake))

        msg = MsgDelegate(
            delegator_address=delegator_address,
            validator_address=validator_address,
            amount=stake_amount_coin
        )
        tx.add_message(msg, type_url="/cosmos.staking.v1beta1.MsgDelegate")

        signed_tx_bytes = tx.form_signed_tx()

        broadcast_url = f"{lcd_endpoint}/cosmos/tx/v1beta1/txs"
        broadcast_payload = {
            "tx_bytes": base64.b64encode(signed_tx_bytes).decode('utf-8'),
            "mode": "BROADCAST_MODE_SYNC"
        }

        print(f"INFO: Broadcasting stake transaction to {broadcast_url} for {amount_uatom_to_stake} {fee_denom} to validator {validator_address}...")
        response = requests.post(broadcast_url, json=broadcast_payload, timeout=30)
        response.raise_for_status()

        tx_response_data = response.json()

        if tx_response_data.get("tx_response") and tx_response_data["tx_response"].get("code") == 0:
            print(f"SUCCESS: Stake transaction broadcasted successfully!")
            print(f"  Tx Hash: {tx_response_data['tx_response'].get('txhash')}")
            return tx_response_data["tx_response"]
        else:
            code = tx_response_data.get('tx_response', {}).get('code', 'N/A')
            raw_log = tx_response_data.get('tx_response', {}).get('raw_log', 'No log available')
            txhash = tx_response_data.get('tx_response', {}).get('txhash', 'N/A')
            print(f"ERROR: Stake transaction failed on chain.")
            print(f"  Tx Hash: {txhash}")
            print(f"  Code: {code}")
            print(f"  Raw Log: {raw_log}")
            return None

    except requests.exceptions.HTTPError as http_err:
        print(f"ERROR: HTTP error broadcasting stake transaction: {http_err}")
        if http_err.response is not None:
            try:
                error_details = http_err.response.json()
                print(f"  Response Code: {error_details.get('code', 'N/A')}")
                print(f"  Response Message: {error_details.get('message', 'N/A')}")
                print(f"  Full Response: {error_details}")
            except json.JSONDecodeError:
                print(f"  Raw Response: {http_err.response.text}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"ERROR: Network error broadcasting stake transaction: {req_err}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred in stake_atom_tx: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    config = load_config()
    print("--- Configuration Loaded ---")

    lcd_endpoint = config["rpc_endpoint"]
    if lcd_endpoint.endswith('/'):
        lcd_endpoint = lcd_endpoint[:-1]

    atom_address = config["atom_address"]
    chain_id = config["chain_id"]
    gas_limit = int(config["gas_limit"])
    gas_price_str = config["gas_price"]
    fee_denom = config["fee_denom"] # Should be 'uatom' for staking ATOM
    base_memo = config.get("memo", "Auto-compounded by script")


    print(f"--- Querying Account Balance for {atom_address} ---")
    uatom_balance = get_account_balance(atom_address, lcd_endpoint)
    if uatom_balance is not None:
        print(f"Balance: {uatom_balance / 1_000_000:.6f} ATOM ({uatom_balance} uatom)")
    else:
        print("Could not retrieve account balance.")

    print(f"--- Querying Staking Rewards for {atom_address} ---")
    # Pass fee_denom to get_staking_rewards if it needs to be dynamic, for now it assumes 'uatom'
    uatom_rewards, validators_to_claim_from = get_staking_rewards(atom_address, lcd_endpoint)

    if uatom_rewards is not None:
        print(f"Total Staking Rewards: {uatom_rewards / 1_000_000:.6f} ATOM ({uatom_rewards} uatom)")

        if uatom_rewards > 0 and validators_to_claim_from:
            print(f"  Rewards available from validators: {', '.join(validators_to_claim_from)}")

            print("\n" + "="*40)
            print("!!! WARNING: MNEMONIC INPUT REQUIRED !!!")
            # ... (warnings remain the same)
            print("="*40 + "\n")

            mnemonic_phrase = input(f"Enter your 12/24-word mnemonic for {atom_address} to claim and potentially stake rewards (or press Enter to skip): ")

            if not mnemonic_phrase.strip():
                print("INFO: Mnemonic not provided. Skipping reward claim and staking.")
            else:
                try:
                    wallet = Wallet(mnemonic_phrase)
                    if wallet.address != atom_address:
                        print(f"WARNING: Mnemonic generated address {wallet.address}, but config address is {atom_address}.")
                        print("Ensure this is the correct mnemonic for the configured address, or update config.")

                    print(f"--- Attempting to Claim Rewards for {atom_address} ---")
                    claim_memo = base_memo + " - Claiming Rewards"
                    claim_tx_response = claim_staking_rewards_tx(
                        wallet=wallet,
                        lcd_endpoint=lcd_endpoint,
                        chain_id=chain_id,
                        gas_limit=gas_limit,
                        gas_price_str=gas_price_str,
                        fee_denom=fee_denom,
                        memo=claim_memo,
                        validators_to_claim_from=validators_to_claim_from,
                        delegator_address=atom_address
                    )

                    if claim_tx_response: # If claim was successful
                        print("INFO: Claim rewards transaction processed.")
                        print("--- Attempting to Stake Newly Claimed Rewards ---")

                        validator_to_stake_to = config.get("validator_address")
                        if not validator_to_stake_to or validator_to_stake_to == "YOUR_PREFERRED_VALIDATOR_ADDRESS_HERE (optional)" or validator_to_stake_to.strip() == "":
                            print("INFO: 'validator_address' not configured in config.json or still set to placeholder/empty. Skipping staking.")
                        else:
                            amount_to_stake = uatom_rewards # Use the rewards amount queried before claiming

                            if amount_to_stake > 0:
                                print(f"Attempting to stake {amount_to_stake / 1_000_000:.6f} ATOM to validator {validator_to_stake_to}")

                                stake_memo = base_memo + " - Staking Rewards"

                                stake_tx_res = stake_atom_tx(
                                    wallet=wallet,
                                    lcd_endpoint=lcd_endpoint,
                                    chain_id=chain_id,
                                    gas_limit=gas_limit, # Consider a separate gas_limit for staking if needed
                                    gas_price_str=gas_price_str,
                                    fee_denom=fee_denom,
                                    memo=stake_memo,
                                    delegator_address=atom_address,
                                    validator_address=validator_to_stake_to,
                                    amount_uatom_to_stake=amount_to_stake
                                )
                                if stake_tx_res:
                                    print("INFO: Stake transaction processed successfully.")
                                else:
                                    print("INFO: Stake transaction seemed to fail. Check logs above.")
                            else:
                                print("INFO: No rewards amount recorded to stake (uatom_rewards is zero or less).")
                    else:
                        print("INFO: Reward claim was not successful or skipped. Skipping staking step.")

                except Exception as e:
                    print(f"ERROR: An error occurred during wallet initialization, reward claim, or staking process: {e}")
                    import traceback
                    traceback.print_exc()
        elif uatom_rewards == 0:
            print("INFO: No staking rewards available to claim.")
        else:
            print("INFO: Rewards reported (or None), but no specific validators found or rewards amount is not positive. Check reward query logic or balance.")
    else:
        print("Could not retrieve staking rewards information.")

    print("--- Script Finished ---")
