"""items table and participant item slots

Revision ID: c2f4a8d01f11
Revises: 8f3c2a1b4d55
Create Date: 2026-05-03 20:30:00.000000

"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2f4a8d01f11"
down_revision: Union[str, Sequence[str], None] = "8f3c2a1b4d55"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _load_items() -> list[dict[str, object]]:
    items_path = Path(__file__).resolve().parents[2] / "tools" / "item.json"
    with items_path.open(encoding="utf-8") as file:
        raw_items = json.load(file)

    rows = [
        {
            "item_id": 0,
            "name": None,
            "description": None,
        }
    ]

    for item_id, item in raw_items.get("data", {}).items():
        rows.append(
            {
                "item_id": int(item_id),
                "name": item.get("name"),
                "description": item.get("description"),
            }
        )

    return rows


def upgrade() -> None:
    op.create_table(
        "item",
        sa.Column("item_id", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("item_id"),
    )
    op.create_index(op.f("ix_item_item_id"), "item", ["item_id"], unique=False)

    item_table = sa.table(
        "item",
        sa.column("item_id", sa.Integer()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
    )
    op.bulk_insert(item_table, _load_items())

    op.add_column("match_participant", sa.Column("item0", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("match_participant", sa.Column("item1", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("match_participant", sa.Column("item2", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("match_participant", sa.Column("item3", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("match_participant", sa.Column("item4", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("match_participant", sa.Column("item5", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("match_participant", sa.Column("item6", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("match_participant", sa.Column("role_bound_item", sa.Integer(), nullable=False, server_default=sa.text("0")))

    op.create_foreign_key("fk_match_participant_item0", "match_participant", "item", ["item0"], ["item_id"])
    op.create_foreign_key("fk_match_participant_item1", "match_participant", "item", ["item1"], ["item_id"])
    op.create_foreign_key("fk_match_participant_item2", "match_participant", "item", ["item2"], ["item_id"])
    op.create_foreign_key("fk_match_participant_item3", "match_participant", "item", ["item3"], ["item_id"])
    op.create_foreign_key("fk_match_participant_item4", "match_participant", "item", ["item4"], ["item_id"])
    op.create_foreign_key("fk_match_participant_item5", "match_participant", "item", ["item5"], ["item_id"])
    op.create_foreign_key("fk_match_participant_item6", "match_participant", "item", ["item6"], ["item_id"])
    op.create_foreign_key("fk_match_participant_role_bound_item", "match_participant", "item", ["role_bound_item"], ["item_id"])


def downgrade() -> None:
    op.drop_constraint("fk_match_participant_role_bound_item", "match_participant", type_="foreignkey")
    op.drop_constraint("fk_match_participant_item6", "match_participant", type_="foreignkey")
    op.drop_constraint("fk_match_participant_item5", "match_participant", type_="foreignkey")
    op.drop_constraint("fk_match_participant_item4", "match_participant", type_="foreignkey")
    op.drop_constraint("fk_match_participant_item3", "match_participant", type_="foreignkey")
    op.drop_constraint("fk_match_participant_item2", "match_participant", type_="foreignkey")
    op.drop_constraint("fk_match_participant_item1", "match_participant", type_="foreignkey")
    op.drop_constraint("fk_match_participant_item0", "match_participant", type_="foreignkey")

    op.drop_column("match_participant", "role_bound_item")
    op.drop_column("match_participant", "item6")
    op.drop_column("match_participant", "item5")
    op.drop_column("match_participant", "item4")
    op.drop_column("match_participant", "item3")
    op.drop_column("match_participant", "item2")
    op.drop_column("match_participant", "item1")
    op.drop_column("match_participant", "item0")

    op.drop_index(op.f("ix_item_item_id"), table_name="item")
    op.drop_table("item")
