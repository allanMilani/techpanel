from __future__ import annotations

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.ports.repositories import IServerRepository
from src.domain.entities import Server
from src.infrastructure.persistence.models import ServerModel
from src.infrastructure.persistence.mappers import server_model_to_entity


class PgServerRepository(IServerRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, server: Server) -> Server:
        row = ServerModel(
            id=server.id,
            name=server.name,
            host=server.host,
            port=server.port,
            ssh_user=server.ssh_user,
            private_key_enc=server.private_key_enc,
            created_by=server.created_by,
        )

        self._session.add(row)
        await self._session.flush()
        return server_model_to_entity(row)

    async def update(self, server: Server) -> Server:
        result = await self._session.execute(
            select(ServerModel).where(ServerModel.id == server.id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise ValueError(f"Server with id {server.id} not found")

        row.name = server.name
        row.host = server.host
        row.port = server.port
        row.ssh_user = server.ssh_user
        row.private_key_enc = server.private_key_enc
        row.created_by = server.created_by

        await self._session.flush()
        return server_model_to_entity(row)

    async def get_by_id(self, server_id: UUID) -> Server | None:
        result = await self._session.execute(
            select(ServerModel).where(ServerModel.id == server_id)
        )
        row = result.scalar_one_or_none()
        return server_model_to_entity(row) if row else None

    async def list_all(self) -> list[Server]:
        result = await self._session.execute(select(ServerModel))
        return [server_model_to_entity(row) for row in result.scalars().all()]

    async def delete(self, server_id: UUID) -> None:
        result = await self._session.execute(
            select(ServerModel).where(ServerModel.id == server_id)
        )
        row = result.scalar_one_or_none()
        if row:
            await self._session.delete(row)
