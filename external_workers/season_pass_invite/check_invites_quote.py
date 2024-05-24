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
    invited_wallets = requests.get(
        f"{API_URL}/invites/token/{token_id}", headers={"X-SYS-KEY": SYS_KEY}
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
    invited_wallets = invited_wallets.json()
    return task.complete({"available_invites": INVITES_LIMIT - len(invited_wallets)})


if __name__ == "__main__":
    ExternalTaskWorker(
        worker_id="1", base_url=CAMUNDA_URL, config=CAMUNDA_CLIENT_CONFIG
    ).subscribe(TOPIC_NAME, handle_task)
