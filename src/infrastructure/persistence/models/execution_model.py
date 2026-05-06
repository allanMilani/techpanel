from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.persistence.models.base import Base
from src.infrastructure.persistence.models.enums import ExecutionStatus

if TYPE_CHECKING:
    from src.infrastructure.persistence.models.user_model import UserModel


class ExecutionModel(Base):
    __tablename__ = "executions"
    __table_args__ = (
        Index("ix_executions_pipeline_id_started_at", "pipeline_id", "started_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pipelines.id", ondelete="RESTRICT"),
        nullable=False,
    )
    triggered_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    branch_or_tag: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[ExecutionStatus] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    triggered_by_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)

    triggered_by_user: Mapped[UserModel] = relationship(back_populates="executions")
