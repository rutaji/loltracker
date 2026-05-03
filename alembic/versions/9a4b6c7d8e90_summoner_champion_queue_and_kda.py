"""add queue and kda totals to summoner champion

Revision ID: 9a4b6c7d8e90
Revises: c2f4a8d01f11
Create Date: 2026-05-03 23:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9a4b6c7d8e90"
down_revision: Union[str, Sequence[str], None] = "c2f4a8d01f11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS Summoner_champion_trigger ON match_participant")

    op.drop_index(op.f("ix_summoner_champion_champion_id"), table_name="summoner_champion")
    op.drop_index(op.f("ix_summoner_champion_summoner_id"), table_name="summoner_champion")
    op.drop_table("summoner_champion")

    op.create_table(
        "summoner_champion",
        sa.Column("summoner_id", sa.String(), nullable=False),
        sa.Column("champion_id", sa.String(), nullable=False),
        sa.Column("queue_id", sa.Integer(), nullable=False),
        sa.Column("games_played", sa.Integer(), nullable=True),
        sa.Column("games_won", sa.Integer(), nullable=True),
        sa.Column("kill", sa.Integer(), nullable=True),
        sa.Column("death", sa.Integer(), nullable=True),
        sa.Column("assist", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["champion_id"], ["champion.id"]),
        sa.ForeignKeyConstraint(["queue_id"], ["queues.queue_id"]),
        sa.ForeignKeyConstraint(["summoner_id"], ["summoner.id"]),
        sa.PrimaryKeyConstraint("summoner_id", "champion_id", "queue_id"),
    )
    op.create_index(op.f("ix_summoner_champion_champion_id"), "summoner_champion", ["champion_id"], unique=False)
    op.create_index(op.f("ix_summoner_champion_queue_id"), "summoner_champion", ["queue_id"], unique=False)
    op.create_index(op.f("ix_summoner_champion_summoner_id"), "summoner_champion", ["summoner_id"], unique=False)

    op.execute(
        """
        INSERT INTO summoner_champion (
            summoner_id,
            champion_id,
            queue_id,
            games_played,
            games_won,
            kill,
            death,
            assist
        )
        SELECT
            mp.summoner_id,
            mp.champion,
            m.queue_id,
            COUNT(*) AS games_played,
            SUM(CASE WHEN mp.won THEN 1 ELSE 0 END) AS games_won,
            SUM(mp.kill) AS kill,
            SUM(mp.death) AS death,
            SUM(mp.assist) AS assist
        FROM match_participant mp
        JOIN "match" m ON m.id = mp.match_id
        WHERE m.queue_id IS NOT NULL
        GROUP BY mp.summoner_id, mp.champion, m.queue_id;

        CREATE OR REPLACE FUNCTION increment_summoner_champion()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO summoner_champion (
                summoner_id,
                champion_id,
                queue_id,
                games_played,
                games_won,
                kill,
                death,
                assist
            )
            SELECT
                NEW.summoner_id,
                NEW.champion,
                m.queue_id,
                1,
                CASE WHEN NEW.won THEN 1 ELSE 0 END,
                NEW.kill,
                NEW.death,
                NEW.assist
            FROM "match" m
            WHERE m.id = NEW.match_id
              AND m.queue_id IS NOT NULL
            ON CONFLICT (summoner_id, champion_id, queue_id)
            DO UPDATE
            SET
                games_played = summoner_champion.games_played + 1,
                games_won = COALESCE(summoner_champion.games_won, 0) +
                    CASE WHEN NEW.won THEN 1 ELSE 0 END,
                kill = summoner_champion.kill + NEW.kill,
                death = summoner_champion.death + NEW.death,
                assist = summoner_champion.assist + NEW.assist;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER Summoner_champion_trigger
            AFTER INSERT
            ON match_participant
            FOR EACH ROW
            EXECUTE FUNCTION increment_summoner_champion();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS Summoner_champion_trigger ON match_participant")

    op.drop_index(op.f("ix_summoner_champion_summoner_id"), table_name="summoner_champion")
    op.drop_index(op.f("ix_summoner_champion_queue_id"), table_name="summoner_champion")
    op.drop_index(op.f("ix_summoner_champion_champion_id"), table_name="summoner_champion")
    op.drop_table("summoner_champion")

    op.create_table(
        "summoner_champion",
        sa.Column("summoner_id", sa.String(), nullable=False),
        sa.Column("champion_id", sa.String(), nullable=False),
        sa.Column("games_played", sa.Integer(), nullable=True),
        sa.Column("games_won", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["champion_id"], ["champion.id"]),
        sa.ForeignKeyConstraint(["summoner_id"], ["summoner.id"]),
        sa.PrimaryKeyConstraint("summoner_id", "champion_id"),
    )
    op.create_index(op.f("ix_summoner_champion_champion_id"), "summoner_champion", ["champion_id"], unique=False)
    op.create_index(op.f("ix_summoner_champion_summoner_id"), "summoner_champion", ["summoner_id"], unique=False)

    op.execute(
        """
        INSERT INTO summoner_champion (
            summoner_id,
            champion_id,
            games_played,
            games_won
        )
        SELECT
            mp.summoner_id,
            mp.champion,
            COUNT(*) AS games_played,
            SUM(CASE WHEN mp.won THEN 1 ELSE 0 END) AS games_won
        FROM match_participant mp
        GROUP BY mp.summoner_id, mp.champion;

        CREATE OR REPLACE FUNCTION increment_summoner_champion()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO summoner_champion (summoner_id, champion_id, games_played, games_won)
            SELECT
                NEW.summoner_id,
                NEW.champion,
                1,
                CASE WHEN NEW.won THEN 1 ELSE 0 END
            ON CONFLICT (summoner_id, champion_id)
            DO UPDATE
            SET
                games_played = summoner_champion.games_played + 1,
                games_won = COALESCE(summoner_champion.games_won, 0) +
                    CASE WHEN NEW.won THEN 1 ELSE 0 END;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER Summoner_champion_trigger
            AFTER INSERT
            ON match_participant
            FOR EACH ROW
            EXECUTE FUNCTION increment_summoner_champion();
        """
    )
