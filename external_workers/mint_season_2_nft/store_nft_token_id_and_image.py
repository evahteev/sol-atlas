import logging

from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker
from web3 import Web3
import os


CAMUNDA_URL = os.getenv("CAMUNDA_URL", "http://localhost:8080/engine-rest")
CAMUNDA_USERNAME = os.getenv("CAMUNDA_USERNAME", "demo")
CAMUNDA_PASSWORD = os.getenv("CAMUNDA_PASSWORD", "demo")
logger = logging.getLogger(__name__)

# configuration for the Client
default_config = {
    "auth_basic": {"username": CAMUNDA_USERNAME, "password": CAMUNDA_PASSWORD},
    "maxTasks": 1,
    "lockDuration": 10000,
    "asyncResponseTimeout": 5000,
    "retries": 3,
    "retryTimeout": 15000,
    "sleepSeconds": 30,
}

NFT_ADDRESSES = (
    '0x872ef2bfe4efc19ba4e21e36f4cadac4f8c92ede',
    '0xe41eab3053ddf33ebe071fecfe42ae5332a9eea3',
)


def set_web3_by_chain_id(chain_id: int):
    global w3
    if chain_id == 261:
        url = "http://new-rpc-gw-prod.dexguru.biz/archive/261"
    elif chain_id == 8453:
        url = "https://base-rpc.publicnode.com"
    else:
        url = f"http://rpc-gw-stage.dexguru.biz/full/{chain_id}"
    w3 = Web3(Web3.HTTPProvider(url))


def get_nft_token_id(tx_hash: str) -> int:
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    logs = receipt["logs"]
    for log in logs:
        if (
            log["topics"][0].hex().lower()
            == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            and log['address'].lower() in NFT_ADDRESSES
        ):
            return int(log.topics[3].hex(), 16)
    logger.info("No NFT token id found in the transaction logs")


def handle_task(task: ExternalTask) -> TaskResult:
    variables = task.get_variables()
    tx_hash = variables.get("transactionHash")
    art_id = variables.get("gen_art_id")
    chain_id = variables.get("chain_id")
    set_web3_by_chain_id(chain_id)
    logger.info(
        f"Getting NFT token id. art_id: {art_id} tx_hash: {tx_hash} chain_id: {chain_id}",
    )
    if not tx_hash or not art_id or not chain_id:
        logger.error("transactionHash or get_art_id or chain_id is missing")
        return task.bpmn_error(
            "VARIABLE_MISSING",
            "transactionHash or get_art_id is missing",
            variables,
        )
    try:
        token_id = get_nft_token_id(tx_hash)
    except Exception as e:
        logger.error(f"Failed to get NFT token id: {e}")
        return task.bpmn_error(
            "FAILED_TO_GET_NFT_TOKEN_ID",
            f"Failed to get NFT token id: {e}",
            variables,
        )
    if token_id is None:
        return task.bpmn_error(
            "FAILED_TO_GET_NFT_TOKEN_ID",
            "Failed to get NFT token id",
            variables,
        )
    logger.info(f"Got NFT token id: {token_id}")
    variables["nft_token_id"] = token_id
    variables["transactionHash"] = tx_hash
    variables["chain_id"] = chain_id
    logger.info(f"Returning variables: {variables}")
    return task.complete(variables)


if __name__ == "__main__":
    logger.info("Starting the worker...")
    ExternalTaskWorker(
        worker_id="1", base_url=CAMUNDA_URL, config=default_config
    ).subscribe(
        [
            'StoreTokenIdAndImage',
        ],
        handle_task,
    )
