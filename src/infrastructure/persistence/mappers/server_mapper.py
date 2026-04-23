from __future__ import annotations

from src.domain.entities import Server
from src.infrastructure.persistence.models import ServerModel


def server_model_to_entity(row: ServerModel) -> Server:
    return Server(
        id=row.id,
        name=row.name,
        host=row.host,
        port=row.port,
        ssh_user=row.ssh_user,
        private_key_enc=row.private_key_enc,
        created_by=row.created_by,
    )
