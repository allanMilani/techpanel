from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True, frozen=True)
class CreateServerInputDTO:
    name: str
    host: str
    port: int
    ssh_user: str
    private_key_plain: str
    created_by: UUID


@dataclass(slots=True, frozen=True)
class ServerOutputDTO:
    id: UUID
    name: str
    host: str
    port: int
    ssh_user: str
    created_by: UUID


@dataclass(slots=True, frozen=True)
class UpdateServerInputDTO:
    name: str
    host: str
    port: int
    ssh_user: str
    private_key_plain: str | None = None
