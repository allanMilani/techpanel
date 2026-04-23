from enum import StrEnum


class OnFailurePolicy(StrEnum):
    STOP = "stop"
    CONTINUE = "continue"
    NOTIFY_AND_STOP = "notify_and_stop"
