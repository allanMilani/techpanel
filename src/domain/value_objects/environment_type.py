from enum import StrEnum


class EnvironmentType(StrEnum):
    PRODUCTION = "production"
    STAGING = "staging"
    CUSTOM = "custom"
