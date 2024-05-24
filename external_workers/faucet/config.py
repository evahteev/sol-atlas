import os

DEFAULT_CONFIG = {
    "maxTasks": 1,
    "lockDuration": 10000,
    "asyncResponseTimeout": 5000,
    "retries": 3,
    "retryTimeout": 15000,
    "sleepSeconds": 30,
}
DELAY_TOPIC_NAME = os.getenv("DELAY_TOPIC_NAME", "check_delay")
CAMUNDA_URL = os.getenv("CAMUNDA_URL", "http://localhost:8080/engine-rest")
PRIVATE_KEY = os.getenv(
    "PRIVATE_KEY", "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
)
