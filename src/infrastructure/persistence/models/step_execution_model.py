import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.models.base import Base
from src.infrastructure.persistence.models.enums import StepExecutionStatus


class StepExecutionModel(Base):
    __tablename__ = "step_executions"
    __table_args__ = (
        UniqueConstraint(
            "execution_id", "order", name="uq_step_executions_execution_id_order"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("executions.id", ondelete="CASCADE"),
        nullable=False,
    )
    pipeline_step_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pipeline_steps.id", ondelete="RESTRICT"),
        nullable=False,
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[StepExecutionStatus] = mapped_column(String(32), nullable=False)
    log_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
