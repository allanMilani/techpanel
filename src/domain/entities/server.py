from dataclasses import dataclass
from uuid import UUID, uuid4

from src.domain.errors import ValidationError

@dataclass(slots=True, frozen=True)
class Server:
    id: UUID
    name: str
    host: str
    port: int
    ssh_user: str
    private_key_enc: str
    created_by: UUID
    
    @staticmethod
    def create(
        name: str, 
        host: str, 
        port: int, 
        ssh_user: str, 
        private_key_enc: str,
        created_by: UUID | str,
    ) -> "Server":
        if not name.strip():
            raise ValidationError("Name is required")

        if not host.strip():
            raise ValidationError("Host is required")

        if port < 1 or port > 65535:
            raise ValidationError("Port is required")

        if not ssh_user.strip():
            raise ValidationError("SSH user is required")

        if not private_key_enc:
            raise ValidationError("Private key is required")

        created_uuid = created_by if isinstance(created_by, UUID) else UUID(str(created_by).strip())
        if not str(created_uuid).strip():
            raise ValidationError("Created by is required")

        return Server(
            id=uuid4(),
            name=name.strip(),
            host=host.strip(),
            port=port,
            ssh_user=ssh_user.strip(),
            private_key_enc=private_key_enc,
            created_by=created_uuid,
        )