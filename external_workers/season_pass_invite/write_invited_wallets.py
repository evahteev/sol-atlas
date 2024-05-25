from datetime import datetime, timedelta

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
        f"{API_URL}/invites/token/{token_id}",
        headers={"X-SYS-KEY": SYS_KEY},
        json=list(wallets_to_invite),
    )
    try:
        invited_wallets.raise_for_status()
    except Exception as e:
        logging.error(e)
        return task.bpmn_error(
            error_code="FAILED_TO_UPDATE_INVITED_WALLETS",
            error_message=str(e),
            variables={"next_invite_date_iso": None}
        )
    
    # Calculate next invite date
    next_invite_date = datetime.utcnow() + timedelta(hours=24)
    next_invite_date_iso = next_invite_date.isoformat() + 'Z'  # Ensure it's in UTC and ISO8601 format
    
    return task.complete({"next_invite_date_iso": next_invite_date_iso})


if __name__ == "__main__":
    ExternalTaskWorker(
        worker_id="2", base_url=CAMUNDA_URL, config=CAMUNDA_CLIENT_CONFIG
    ).subscribe(TOPIC_NAME, handle_task)
