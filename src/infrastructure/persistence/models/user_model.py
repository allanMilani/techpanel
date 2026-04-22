from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.persistence.models.base import Base
from src.infrastructure.persistence.models.enums import UserRole
from src.infrastructure.persistence.models.execution_model import ExecutionModel
from src.infrastructure.persistence.models.pipeline_model import PipelineModel
from src.infrastructure.persistence.models.project_model import ProjectModel
from src.infrastructure.persistence.models.server_model import ServerModel


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    servers: Mapped[list[ServerModel]] = relationship(back_populates="creator")
    projects: Mapped[list[ProjectModel]] = relationship(back_populates="creator")
    pipelines: Mapped[list[PipelineModel]] = relationship(back_populates="creator")
    executions: Mapped[list[ExecutionModel]] = relationship(
        back_populates="triggered_by_user"
    )