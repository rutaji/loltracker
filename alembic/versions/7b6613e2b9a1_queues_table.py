"""queues table

Revision ID: 7b6613e2b9a1
Revises: b53b79809d27
Create Date: 2026-04-22 20:30:00.000000

"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7b6613e2b9a1"
down_revision: Union[str, Sequence[str], None] = "b53b79809d27"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _normalize_description(description: str | None) -> str | None:
    if description is None:
        return None

    if description.endswith(" games"):
        return description[:-6]

    if description.endswith(" Games"):
        return description[:-6]

    return description


def _load_queues() -> list[dict[str, object]]:
    queues_path = Path(__file__).resolve().parents[2] / "tools" / "queues.json"
    with queues_path.open(encoding="utf-8") as file:
        raw_queues = json.load(file)

    return [
        {
            "queue_id": queue["queueId"],
            "map": queue["map"],
            "description": _normalize_description(queue["description"]),
            "notes": queue["notes"],
        }
        for queue in raw_queues
    ]


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "queues",
        sa.Column("queue_id", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("map", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("queue_id"),
    )
    op.create_index(op.f("ix_queues_queue_id"), "queues", ["queue_id"], unique=False)

    queue_table = sa.table(
        "queues",
        sa.column("queue_id", sa.Integer()),
        sa.column("map", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("notes", sa.Text()),
    )
    op.bulk_insert(queue_table, _load_queues())


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_queues_queue_id"), table_name="queues")
    op.drop_table("queues")
