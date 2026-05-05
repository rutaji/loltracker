"""replace derived gametype columns with queue_id

Revision ID: 5c2b9f7f7a11
Revises: 1dbf24eac9c2
Create Date: 2026-04-23 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5c2b9f7f7a11"
down_revision: Union[str, Sequence[str], None] = "1dbf24eac9c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f("ix_champion_stats_champion_id"), table_name="champion_stats")
    op.drop_index(op.f("ix_champion_stats_gametype"), table_name="champion_stats")
    op.drop_index(op.f("ix_champion_stats_patch"), table_name="champion_stats")
    op.drop_table("champion_stats")

    op.drop_index(op.f("ix_matches_analyzed_gametype"), table_name="matches_analyzed")
    op.drop_index(op.f("ix_matches_analyzed_patch"), table_name="matches_analyzed")
    op.drop_table("matches_analyzed")

    op.create_table(
        "champion_stats",
        sa.Column("champion_id", sa.String(), nullable=False),
        sa.Column("patch", sa.String(), nullable=False),
        sa.Column("queue_id", sa.Integer(), nullable=False),
        sa.Column("games_played", sa.Integer(), nullable=True),
        sa.Column("games_won", sa.Integer(), nullable=True),
        sa.Column("games_banned", sa.Integer(), nullable=True),
        sa.Column("kill", sa.Integer(), nullable=True),
        sa.Column("assist", sa.Integer(), nullable=True),
        sa.Column("death", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["champion_id"], ["champion.id"]),
        sa.ForeignKeyConstraint(["queue_id"], ["queues.queue_id"]),
        sa.PrimaryKeyConstraint("champion_id", "patch", "queue_id"),
    )
    op.create_index(op.f("ix_champion_stats_champion_id"), "champion_stats", ["champion_id"], unique=False)
    op.create_index(op.f("ix_champion_stats_patch"), "champion_stats", ["patch"], unique=False)
    op.create_index(op.f("ix_champion_stats_queue_id"), "champion_stats", ["queue_id"], unique=False)

    op.create_table(
        "matches_analyzed",
        sa.Column("patch", sa.String(), nullable=False),
        sa.Column("queue_id", sa.Integer(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["queue_id"], ["queues.queue_id"]),
        sa.PrimaryKeyConstraint("patch", "queue_id"),
    )
    op.create_index(op.f("ix_matches_analyzed_patch"), "matches_analyzed", ["patch"], unique=False)
    op.create_index(op.f("ix_matches_analyzed_queue_id"), "matches_analyzed", ["queue_id"], unique=False)

    op.execute(
        """
        INSERT INTO matches_analyzed (patch, queue_id, count)
        SELECT
            m.patch,
            m.queue_id,
            COUNT(*)
        FROM match m
        WHERE m.queue_id IS NOT NULL
        GROUP BY m.patch, m.queue_id;

        INSERT INTO champion_stats (champion_id, patch, queue_id, games_played, games_won, games_banned, kill, assist, death)
        SELECT
            mp.champion,
            m.patch,
            m.queue_id,
            COUNT(*) AS games_played,
            SUM(CASE WHEN mp.won THEN 1 ELSE 0 END) AS games_won,
            0 AS games_banned,
            SUM(mp.kill) AS kill,
            SUM(mp.assist) AS assist,
            SUM(mp.death) AS death
        FROM match_participant mp
        JOIN match m ON m.id = mp.match_id
        WHERE m.queue_id IS NOT NULL
        GROUP BY mp.champion, m.patch, m.queue_id;

        CREATE OR REPLACE FUNCTION increment_analyzed_count()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.queue_id IS NULL THEN
                RETURN NEW;
            END IF;

            INSERT INTO matches_analyzed (patch, queue_id, count)
            VALUES (NEW.patch, NEW.queue_id, 1) ON CONFLICT (patch, queue_id)
            DO UPDATE
            SET count = matches_analyzed.count + 1;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION increment_champion_stats()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO champion_stats (champion_id, patch, queue_id, games_played, games_won, games_banned, kill, assist, death)
            SELECT
                NEW.champion,
                m.patch,
                m.queue_id,
                1,
                CASE WHEN NEW.won THEN 1 ELSE 0 END,
                0,
                NEW.kill,
                NEW.assist,
                NEW.death
            FROM match m
            WHERE m.id = NEW.match_id
              AND m.queue_id IS NOT NULL
            ON CONFLICT (champion_id, patch, queue_id)
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
        $$ LANGUAGE plpgsql;
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_champion_stats_queue_id"), table_name="champion_stats")
    op.drop_index(op.f("ix_champion_stats_patch"), table_name="champion_stats")
    op.drop_index(op.f("ix_champion_stats_champion_id"), table_name="champion_stats")
    op.drop_table("champion_stats")

    op.drop_index(op.f("ix_matches_analyzed_queue_id"), table_name="matches_analyzed")
    op.drop_index(op.f("ix_matches_analyzed_patch"), table_name="matches_analyzed")
    op.drop_table("matches_analyzed")

    op.create_table(
        "champion_stats",
        sa.Column("champion_id", sa.String(), nullable=False),
        sa.Column("patch", sa.String(), nullable=False),
        sa.Column("gametype", sa.String(), nullable=False),
        sa.Column("games_played", sa.Integer(), nullable=True),
        sa.Column("games_won", sa.Integer(), nullable=True),
        sa.Column("games_banned", sa.Integer(), nullable=True),
        sa.Column("kill", sa.Integer(), nullable=True),
        sa.Column("assist", sa.Integer(), nullable=True),
        sa.Column("death", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["champion_id"], ["champion.id"]),
        sa.PrimaryKeyConstraint("champion_id", "patch", "gametype"),
    )
    op.create_index(op.f("ix_champion_stats_champion_id"), "champion_stats", ["champion_id"], unique=False)
    op.create_index(op.f("ix_champion_stats_gametype"), "champion_stats", ["gametype"], unique=False)
    op.create_index(op.f("ix_champion_stats_patch"), "champion_stats", ["patch"], unique=False)

    op.create_table(
        "matches_analyzed",
        sa.Column("patch", sa.String(), nullable=False),
        sa.Column("gametype", sa.String(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("patch", "gametype"),
    )
    op.create_index(op.f("ix_matches_analyzed_gametype"), "matches_analyzed", ["gametype"], unique=False)
    op.create_index(op.f("ix_matches_analyzed_patch"), "matches_analyzed", ["patch"], unique=False)
