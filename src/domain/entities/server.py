import re
from dataclasses import dataclass
from uuid import UUID, uuid4

from src.domain.errors import ValidationError
from src.domain.value_objects.server_connection_kind import ServerConnectionKind

# Nome estilo compose / DNS parcial
_CONTAINER_NAME_STYLE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")
# ID curto ou completo retornado por `docker ps` / `docker inspect`
_HEX_CONTAINER_ID = re.compile(r"^[0-9a-fA-F]{12,64}$")


def normalize_docker_container_ref(value: str | None) -> str:
    """Remove espaços e barra inicial (comum ao copiar nomes de `docker ps`)."""
    return (value or "").strip().lstrip("/")


def is_valid_docker_container_ref(value: str) -> bool:
    """Aceita nome de container ou ID hexadecimal (12 a 64 caracteres)."""
    s = normalize_docker_container_ref(value)
    if not s:
        return False
    if _HEX_CONTAINER_ID.fullmatch(s):
        return True
    return bool(_CONTAINER_NAME_STYLE.fullmatch(s))


@dataclass(slots=True, frozen=True)
class Server:
    id: UUID
    name: str
    host: str
    port: int
    ssh_user: str
    private_key_enc: str
    created_by: UUID
    connection_kind: ServerConnectionKind
    docker_container_name: str | None
    ssh_strict_host_key_checking: bool
    project_directory: str | None = None

    @staticmethod
    def _validate(
        name: str,
        host: str,
        port: int,
        ssh_user: str,
        private_key_enc: str,
        connection_kind: ServerConnectionKind,
        docker_container_name: str | None,
    ) -> None:
        if not name.strip():
            raise ValidationError("Name is required")

        if not host.strip():
            raise ValidationError("Host is required")

        if port < 1 or port > 65535:
            raise ValidationError("Port is required")

        if connection_kind == ServerConnectionKind.SSH:
            if not ssh_user.strip():
                raise ValidationError("SSH user is required")
        else:
            dc = normalize_docker_container_ref(docker_container_name)
            if not dc:
                raise ValidationError("Identificador do container é obrigatório.")
            if not is_valid_docker_container_ref(dc):
                raise ValidationError(
                    "Identificador do container inválido: informe o nome ou o ID "
                    "(hexadecimal) exibido em docker ps."
                )

        if not private_key_enc:
            raise ValidationError("Private key is required")

    @staticmethod
    def create(
        name: str,
        host: str,
        port: int,
        ssh_user: str,
        private_key_enc: str,
        created_by: UUID | str,
        *,
        connection_kind: ServerConnectionKind = ServerConnectionKind.SSH,
        docker_container_name: str | None = None,
        ssh_strict_host_key_checking: bool = False,
        project_directory: str | None = None,
    ) -> "Server":
        docker_arg = (
            docker_container_name
            if connection_kind == ServerConnectionKind.LOCAL_DOCKER
            else None
        )
        Server._validate(
            name=name,
            host=host,
            port=port,
            ssh_user=ssh_user,
            private_key_enc=private_key_enc,
            connection_kind=connection_kind,
            docker_container_name=docker_arg,
        )

        created_uuid = (
            created_by
            if isinstance(created_by, UUID)
            else UUID(str(created_by).strip())
        )
        if not str(created_uuid).strip():
            raise ValidationError("Created by is required")

        docker_clean: str | None = None
        if connection_kind == ServerConnectionKind.LOCAL_DOCKER:
            docker_clean = normalize_docker_container_ref(docker_container_name)

        strict_host = (
            bool(ssh_strict_host_key_checking)
            if connection_kind == ServerConnectionKind.SSH
            else False
        )

        proj_dir = (project_directory or "").strip() or None

        return Server(
            id=uuid4(),
            name=name.strip(),
            host=host.strip(),
            port=port,
            ssh_user=ssh_user.strip(),
            private_key_enc=private_key_enc,
            created_by=created_uuid,
            connection_kind=connection_kind,
            docker_container_name=docker_clean,
            ssh_strict_host_key_checking=strict_host,
            project_directory=proj_dir,
        )
