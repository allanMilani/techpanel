"""server connection_kind and docker_container_name

Revision ID: b8c1d2e3f4a5
Revises: a71640253481
Create Date: 2026-05-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b8c1d2e3f4a5"
down_revision: Union[str, Sequence[str], None] = "a71640253481"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "servers",
        sa.Column(
            "connection_kind",
            sa.String(length=32),
            nullable=False,
            server_default="ssh",
        ),
    )
    op.add_column(
        "servers",
        sa.Column("docker_container_name", sa.String(length=255), nullable=True),
    )
    op.alter_column("servers", "connection_kind", server_default=None)


def downgrade() -> None:
    op.drop_column("servers", "docker_container_name")
    op.drop_column("servers", "connection_kind")
