"""server project_directory, pipeline git sync, execution workspace prep

Revision ID: d1e2f3a4b5c6
Revises: c7d8e9f0a1b2
Create Date: 2026-05-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "servers",
        sa.Column("project_directory", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "pipelines",
        sa.Column(
            "run_git_workspace_sync",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "executions",
        sa.Column("workspace_prepare_log", sa.Text(), nullable=True),
    )
    op.add_column(
        "executions",
        sa.Column("workspace_prepare_exit_code", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("executions", "workspace_prepare_exit_code")
    op.drop_column("executions", "workspace_prepare_log")
    op.drop_column("pipelines", "run_git_workspace_sync")
    op.drop_column("servers", "project_directory")
