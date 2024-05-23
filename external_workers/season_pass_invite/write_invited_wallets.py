import logging

import requests
from camunda.external_task.external_task_worker import ExternalTaskWorker, ExternalTask

from external_workers.season_pass_invite.config import (
    CAMUNDA_URL,
    CAMUNDA_CLIENT_CONFIG,
    TOPIC_NAME,
    API_URL,
    SYS_KEY,
    INVITES_LIMIT,
)


def handle_task(task: ExternalTask):
    variables = task.get_variables()
    token_id = variables.get("token_id")
    wallets_to_invite = set()
    for i in range(1, INVITES_LIMIT + 1):
        wallet = variables.get(f"wallet_{i}")
        if wallet:
            wallets_to_invite.add(wallet)
    invited_wallets = requests.post(
        f"{API_URL}/invite/{token_id}",
        headers={"X-SYS-KEY": SYS_KEY},
        json=list(wallets_to_invite),
    )
    try:
        invited_wallets.raise_for_status()
    except Exception as e:
        logging.error(e)
        return task.failure(
            error_message="failed to fetch invited wallets",
            error_details=str(e),
            max_retries=3,
            retry_timeout=5,
        )
    return task.complete()


if __name__ == "__main__":
    ExternalTaskWorker(
        worker_id="2", base_url=CAMUNDA_URL, config=CAMUNDA_CLIENT_CONFIG
    ).subscribe("writeIvitedWallets", handle_task)
