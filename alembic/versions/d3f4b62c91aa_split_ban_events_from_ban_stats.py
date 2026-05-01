"""split ban events from ban stats

Revision ID: d3f4b62c91aa
Revises: 6aa7c7e8a98d
Create Date: 2026-05-01 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d3f4b62c91aa"
down_revision: Union[str, Sequence[str], None] = "6aa7c7e8a98d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS ban_trigger ON ban")

    op.add_column("ban", sa.Column("ban_order", sa.Integer(), nullable=True))
    op.execute(
        """
        WITH numbered AS (
            SELECT
                ctid,
                ROW_NUMBER() OVER (
                    PARTITION BY match_id, team
                    ORDER BY champion_key
                ) AS generated_ban_order
            FROM ban
        )
        UPDATE ban
        SET ban_order = numbered.generated_ban_order
        FROM numbered
        WHERE ban.ctid = numbered.ctid
        """
    )
    op.alter_column("ban", "ban_order", nullable=False)
    op.drop_constraint("ban_pkey", "ban", type_="primary")
    op.create_primary_key("ban_pkey", "ban", ["match_id", "team", "ban_order"])
    op.create_index(op.f("ix_ban_ban_order"), "ban", ["ban_order"], unique=False)

    op.drop_index(op.f("ix_champion_key"), table_name="champion")
    op.create_index(op.f("ix_champion_key"), "champion", ["key"], unique=True)

    op.create_table(
        "champion_match_ban",
        sa.Column("match_id", sa.String(), nullable=False),
        sa.Column("champion_key", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["match_id"], ["match.id"]),
        sa.ForeignKeyConstraint(["champion_key"], ["champion.key"]),
        sa.PrimaryKeyConstraint("match_id", "champion_key"),
    )
    op.create_index(op.f("ix_champion_match_ban_match_id"), "champion_match_ban", ["match_id"], unique=False)
    op.create_index(op.f("ix_champion_match_ban_champion_key"), "champion_match_ban", ["champion_key"], unique=False)

    op.execute(
        """
        INSERT INTO champion_match_ban (match_id, champion_key)
        SELECT DISTINCT match_id, champion_key
        FROM ban
        WHERE champion_key > -1
        ON CONFLICT (match_id, champion_key) DO NOTHING;

        UPDATE champion_stats
        SET games_banned = 0;

        INSERT INTO champion_stats (
            champion_id,
            patch,
            queue_id,
            games_played,
            games_won,
            games_banned,
            kill,
            assist,
            death
        )
        SELECT
            ch.id,
            m.patch,
            m.queue_id,
            0,
            0,
            COUNT(*),
            0,
            0,
            0
        FROM champion_match_ban cmb
        JOIN champion ch ON ch.key = cmb.champion_key
        JOIN "match" m ON m.id = cmb.match_id
        WHERE m.queue_id IS NOT NULL
        GROUP BY ch.id, m.patch, m.queue_id
        ON CONFLICT (champion_id, patch, queue_id)
        DO UPDATE
        SET games_banned = EXCLUDED.games_banned;

        CREATE OR REPLACE FUNCTION record_champion_match_ban()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO champion_match_ban (match_id, champion_key)
            VALUES (NEW.match_id, NEW.champion_key)
            ON CONFLICT (match_id, champion_key) DO NOTHING;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION increment_champion_ban()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO champion_stats (
                champion_id,
                patch,
                queue_id,
                games_played,
                games_won,
                games_banned,
                kill,
                assist,
                death
            )
            SELECT
                ch.id,
                m.patch,
                m.queue_id,
                0,
                0,
                1,
                0,
                0,
                0
            FROM champion ch
            JOIN "match" m ON m.id = NEW.match_id
            WHERE ch.key = NEW.champion_key
              AND m.queue_id IS NOT NULL
            ON CONFLICT (champion_id, patch, queue_id)
            DO UPDATE
            SET games_banned = champion_stats.games_banned + 1;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER ban_trigger
            AFTER INSERT
            ON ban
            FOR EACH ROW
            WHEN (NEW.champion_key > -1) EXECUTE FUNCTION record_champion_match_ban();

        CREATE TRIGGER champion_match_ban_trigger
            AFTER INSERT
            ON champion_match_ban
            FOR EACH ROW
            EXECUTE FUNCTION increment_champion_ban();
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS champion_match_ban_trigger ON champion_match_ban;
        DROP TRIGGER IF EXISTS ban_trigger ON ban;

        CREATE OR REPLACE FUNCTION increment_champion_ban()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO champion_stats (champion_id, patch, queue_id,games_played,games_won,games_banned,kill,assist,death)
            SELECT
                ch.id,
                m.patch,
                m.queue_id,
                0,
                0,
                1,
                0,
                0,
                0
            FROM champion ch
            JOIN "match" m ON m.id = NEW.match_id
            WHERE ch.key = NEW.champion_key
            ON CONFLICT (champion_id,queue_id, patch)
            DO UPDATE
            SET
                games_banned = champion_stats.games_banned + 1;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.drop_index(op.f("ix_champion_match_ban_champion_key"), table_name="champion_match_ban")
    op.drop_index(op.f("ix_champion_match_ban_match_id"), table_name="champion_match_ban")
    op.drop_table("champion_match_ban")

    op.drop_index(op.f("ix_champion_key"), table_name="champion")
    op.create_index(op.f("ix_champion_key"), "champion", ["key"], unique=False)

    op.drop_index(op.f("ix_ban_ban_order"), table_name="ban")
    op.drop_constraint("ban_pkey", "ban", type_="primary")
    op.create_primary_key("ban_pkey", "ban", ["match_id", "team", "champion_key"])
    op.drop_column("ban", "ban_order")

    op.execute(
        """
        CREATE TRIGGER ban_trigger
            AFTER INSERT
            ON ban
            FOR EACH ROW
            WHEN (NEW.champion_key > -1) EXECUTE FUNCTION increment_champion_ban();
        """
    )
