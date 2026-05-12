"""placeholder: alinha alembic_version órfão (g2h3i4j5k6l7)

Algumas bases tinham esta revisão registada sem ficheiro correspondente no repo,
o que impedia `alembic upgrade head`. Esta migração é intencionalmente vazia.

Revision ID: g2h3i4j5k6l7
Revises: f2a3b4c5d6e7
Create Date: 2026-05-12

"""

from typing import Sequence, Union

from alembic import op

revision: str = "g2h3i4j5k6l7"
down_revision: Union[str, Sequence[str], None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
