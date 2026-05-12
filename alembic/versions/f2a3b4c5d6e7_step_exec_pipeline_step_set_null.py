"""step_executions.pipeline_step_id nullable ON DELETE SET NULL

Permite remover definições de passos da pipeline sem apagar linhas de
step_executions (histórico de execuções).

Revision ID: f2a3b4c5d6e7
Revises: e7276261fb08
Create Date: 2026-05-12

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, Sequence[str], None] = "e7276261fb08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _drop_fk_to_pipeline_steps(inspector: sa.Inspector) -> None:
    for fk in inspector.get_foreign_keys("step_executions"):
        if fk.get("referred_table") != "pipeline_steps":
            continue
        cols = fk.get("constrained_columns") or ()
        if "pipeline_step_id" not in cols:
            continue
        name = fk.get("name")
        if name:
            op.drop_constraint(name, "step_executions", type_="foreignkey")
        return
    raise RuntimeError(
        "FK step_executions.pipeline_step_id → pipeline_steps não encontrado; "
        "ajuste a migração ao nome real da constraint."
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    _drop_fk_to_pipeline_steps(inspector)
    op.alter_column(
        "step_executions",
        "pipeline_step_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
    op.create_foreign_key(
        "step_executions_pipeline_step_id_fkey",
        "step_executions",
        "pipeline_steps",
        ["pipeline_step_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Remove linhas de histórico sem definição de passo antes de tornar a coluna NOT NULL."""
    op.execute("DELETE FROM step_executions WHERE pipeline_step_id IS NULL")
    op.drop_constraint(
        "step_executions_pipeline_step_id_fkey",
        "step_executions",
        type_="foreignkey",
    )
    op.alter_column(
        "step_executions",
        "pipeline_step_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.create_foreign_key(
        "step_executions_pipeline_step_id_fkey",
        "step_executions",
        "pipeline_steps",
        ["pipeline_step_id"],
        ["id"],
        ondelete="RESTRICT",
    )
