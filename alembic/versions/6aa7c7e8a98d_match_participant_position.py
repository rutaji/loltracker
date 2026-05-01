"""add match participant position

Revision ID: 6aa7c7e8a98d
Revises: ff8928baa8a1
Create Date: 2026-05-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6aa7c7e8a98d"
down_revision: Union[str, Sequence[str], None] = "ff8928baa8a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("match_participant", sa.Column("position", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("match_participant", "position")
