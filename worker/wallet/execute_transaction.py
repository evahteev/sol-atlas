import logging

from camunda.external_task.external_task import ExternalTask

from settings.worker import worker_settings as settings
from common.utils import setup_worker
from wallet.utils import (
    get_web3_client_by_chain_id,
)
from wallet.wallet_interfaces import Wallet

ADMIN_TOPIC = "execute_admin_transaction"  # Execute tx from thirdweb backend wallet
EXECUTE_TOPIC = "execute_transaction"
TOPICS = [EXECUTE_TOPIC, ADMIN_TOPIC]


def validate_transaction_data(data: dict):
    """
    Validate the transaction data
    Args:
        data (dict): The transaction data
    Returns:
        dict: The validated transaction data
    """
    required_fields = ["camunda_user_id", "to", "data", "chain_id"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Field '{field}' is required")
    return data


def handle_task(task: ExternalTask):
    variables = task.get_variables()
    camunda_user_id = variables.get("camunda_user_id")
    to_address = variables.get("to")
    wallet_type = variables.get("wallet_type")
    try:
        gas = int(variables.get("gas", 0))
    except ValueError:
        gas = 0
    try:
        gas_price = int(variables.get("gas_price", 0))
    except ValueError:
        gas_price = 0

    value = str(variables.get("value", 0))
    if value.startswith("0x"):
        value = int(value, 16)
    else:
        # handle scientific notation
        value = int(float(value))
    data = variables.get("data")
    chain_id = variables.get("chain_id") or settings.CHAIN_ID
    chain_id = int(chain_id)

    try:
        validate_transaction_data(variables)
    except ValueError as e:
        logging.error(f"Invalid transaction data: {e}")
        return task.bpmn_error(
            "INVALID_DATA",
            str(e),
            variables={"error": str(e)},
        )

    if task.get_topic_name() == ADMIN_TOPIC:
        account = Wallet.admin(chain_id)
    else:
        account = Wallet.from_user_id(
            camunda_user_id, "camunda_user_id", chain_id, wallet_type
        )
    if not account:
        logging.error(f"wallet for user {camunda_user_id} not found")
        return task.bpmn_error(
            "PRIVATE_KEY_NOT_FOUND",
            f"Private key not found.",
            variables={"error": f"Private key not found."},
        )
    try:
        w3 = get_web3_client_by_chain_id(chain_id)

        if not gas_price:
            gas_price = w3.eth.gas_price

        tx = {
            "to": w3.to_checksum_address(to_address),
            "from": account.address,
            "value": value,
            "nonce": account.nonce,
            "gas": int(gas) + 5000,
            "gasPrice": int(int(gas_price) * 1.6),
            "chainId": chain_id,
            "data": data,
        }
    except Exception as e:
        logging.error(f"Failed to prepare transaction: {e}")
        return task.bpmn_error(
            "TRANSACTION_FAILED",
            str(e),
            variables={"error": str(e)},
        )
    try:
        if not gas:
            tx["gas"] = w3.eth.estimate_gas(tx) + 5000
    except Exception as e:
        logging.error(f"Failed to estimate gas: {e}")
        return task.bpmn_error(
            "GAS_ESTIMATION_FAILED",
            str(e),
            variables={"error": str(e)},
        )
    try:
        tx_hash = account.send_transaction(tx)
    except Exception as e:
        logging.error(f"Failed to send transaction: {e}")
        return task.bpmn_error(
            "TRANSACTION_FAILED",
            str(e),
            variables={"error": str(e)},
        )

    return task.complete(
        {"tx_hash": tx_hash},
    )


if __name__ == "__main__":
    setup_worker(TOPICS, handle_task)
