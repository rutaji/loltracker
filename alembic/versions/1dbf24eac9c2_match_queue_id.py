"""replace match gametype with queue_id

Revision ID: 1dbf24eac9c2
Revises: 7b6613e2b9a1
Create Date: 2026-04-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1dbf24eac9c2"
down_revision: Union[str, Sequence[str], None] = "7b6613e2b9a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("match", sa.Column("queue_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_match_queue_id"), "match", ["queue_id"], unique=False)
    op.create_foreign_key(
        "fk_match_queue_id_queues",
        "match",
        "queues",
        ["queue_id"],
        ["queue_id"],
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION increment_analyzed_count()
        RETURNS TRIGGER AS $$
        DECLARE
            resolved_gametype TEXT;
        BEGIN
            SELECT q.description
            INTO resolved_gametype
            FROM queues q
            WHERE q.queue_id = NEW.queue_id;

            IF resolved_gametype IS NULL THEN
                RETURN NEW;
            END IF;

            INSERT INTO matches_analyzed (gametype, patch, count)
            VALUES (resolved_gametype, NEW.patch, 1) ON CONFLICT (gametype, patch)
            DO UPDATE
            SET count = matches_analyzed.count + 1;

            RETURN NEW;
        END;
        $$  LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION increment_champion_stats()
        RETURNS TRIGGER AS $$
        DECLARE
            resolved_gametype TEXT;
        BEGIN
            SELECT q.description
            INTO resolved_gametype
            FROM match m
            JOIN queues q ON q.queue_id = m.queue_id
            WHERE m.id = NEW.match_id;

            IF resolved_gametype IS NULL THEN
                RETURN NEW;
            END IF;

            INSERT INTO champion_stats (champion_id, patch, gametype,games_played,games_won,games_banned,kill,assist,death)
            SELECT
                NEW.champion,
                m.patch,
                resolved_gametype,
                1,
                CASE WHEN NEW.won THEN 1 ELSE 0 END,
                0,
                NEW.kill,
                NEW.assist,
                NEW.death
            FROM match m
            WHERE m.id = NEW.match_id
            ON CONFLICT (champion_id,gametype, patch)
            DO UPDATE
            SET
                games_played = champion_stats.games_played + 1,
                games_won = COALESCE(champion_stats.games_won, 0) +
                    CASE WHEN NEW.won THEN 1 ELSE 0 END,
                kill = champion_stats.kill + NEW.kill,
                assist = champion_stats.assist + NEW.assist,
                death = champion_stats.death + NEW.death;

            RETURN NEW;
        END;
        $$  LANGUAGE plpgsql;
        """
    )
    op.drop_column("match", "gametype")


def downgrade() -> None:
    op.add_column("match", sa.Column("gametype", sa.String(), nullable=True))
    op.drop_constraint("fk_match_queue_id_queues", "match", type_="foreignkey")
    op.drop_index(op.f("ix_match_queue_id"), table_name="match")
    op.drop_column("match", "queue_id")
