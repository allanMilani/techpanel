from enum import StrEnum


class StepType(StrEnum):
    SSH_COMMAND = "ssh_command"
    HTTP_HEALTHCHECK = "http_healthcheck"
    NOTIFY_WEBHOOK = "notify_webhook"
