from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.server import Server


class IServerRepository(ABC):
    @abstractmethod
    async def create(self, server: Server) -> Server: ...

    @abstractmethod
    async def update(self, server: Server) -> Server: ...

    @abstractmethod
    async def get_by_id(self, server_id: UUID) -> Server | None: ...

    @abstractmethod
    async def list_all(self) -> list[Server]: ...

    @abstractmethod
    async def list_all_page(self, limit: int, offset: int) -> tuple[list[Server], int]: ...

    @abstractmethod
    async def delete(self, server_id: UUID) -> None: ...
