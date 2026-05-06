from __future__ import annotations

from src.domain.entities import Server
from src.domain.value_objects.server_connection_kind import ServerConnectionKind
from src.infrastructure.persistence.models import ServerModel


def server_model_to_entity(row: ServerModel) -> Server:
    kind_raw = getattr(row, "connection_kind", None) or ServerConnectionKind.SSH.value
    try:
        kind = ServerConnectionKind(kind_raw)
    except ValueError:
        kind = ServerConnectionKind.SSH
    return Server(
        id=row.id,
        name=row.name,
        host=row.host,
        port=row.port,
        ssh_user=row.ssh_user,
        private_key_enc=row.private_key_enc,
        created_by=row.created_by,
        connection_kind=kind,
        docker_container_name=getattr(row, "docker_container_name", None),
    )
