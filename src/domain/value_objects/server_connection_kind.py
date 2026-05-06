from enum import StrEnum


class ServerConnectionKind(StrEnum):
    """Como o TechPanel executa passos `ssh_command` neste alvo."""

    SSH = "ssh"
    LOCAL_DOCKER = "local_docker"
