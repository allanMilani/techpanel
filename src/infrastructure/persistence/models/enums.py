import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    VIEWER = "viewer"


class EnvironmentType(str, enum.Enum):
    PRODUCTION = "production"
    STAGING = "staging"
    CUSTOM = "custom"


class OnFailurePolicy(str, enum.Enum):
    STOP = "stop"
    CONTINUE = "continue"
    NOTIFY_AND_STOP = "notify_and_stop"


class ExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"


class StepExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class PipelineStepType(str, enum.Enum):
    SSH_COMMAND = "ssh_command"
    HTTP_HEALTHCHECK = "http_healthcheck"
    NOTIFY_WEBHOOK = "notify_webhook"
