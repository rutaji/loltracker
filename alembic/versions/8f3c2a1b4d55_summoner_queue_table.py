"""add summoner queue table

Revision ID: 8f3c2a1b4d55
Revises: d3f4b62c91aa
Create Date: 2026-05-03 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8f3c2a1b4d55"
down_revision: Union[str, Sequence[str], None] = "d3f4b62c91aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "summoner_queue",
        sa.Column("summoner_id", sa.String(), nullable=False),
        sa.Column("queue_id", sa.Integer(), nullable=False),
        sa.Column("tier", sa.String(), nullable=True),
        sa.Column("rank", sa.String(), nullable=True),
        sa.Column("league_points", sa.Integer(), nullable=True),
        sa.Column("wins", sa.Integer(), nullable=True),
        sa.Column("losses", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["queue_id"], ["queues.queue_id"]),
        sa.ForeignKeyConstraint(["summoner_id"], ["summoner.id"]),
        sa.PrimaryKeyConstraint("summoner_id", "queue_id"),
    )
    op.create_index(op.f("ix_summoner_queue_summoner_id"), "summoner_queue", ["summoner_id"], unique=False)
    op.create_index(op.f("ix_summoner_queue_queue_id"), "summoner_queue", ["queue_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_summoner_queue_queue_id"), table_name="summoner_queue")
    op.drop_index(op.f("ix_summoner_queue_summoner_id"), table_name="summoner_queue")
    op.drop_table("summoner_queue")
