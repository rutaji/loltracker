from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.DAO import DAO
from app.database.models import (
    Base,
    Champion,
    ChampionStats,
    Match as DaoMatch,
    MatchParticipant as DaoMatchParticipant,
    MatchesAnalyzed,
    Queue,
    Summoner as DaoSummoner,
)
from app.models.summonerModels import Match, MatchParticipant, Summoner


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_add_summoner(db_session):
    dao = DAO(db_session)
    summoner = Summoner(
        puuid="testid123",
        name="testname",
        tagline="1234",
        wins=0,
        gamesPlayed=0,
        kills=0,
        deaths=0,
        assists=0,
    )

    dao.add_summoner(summoner)

    returned_summoner = dao.get_summoner_dao("testid123")
    assert returned_summoner.id == "testid123"
    assert returned_summoner.summoner_name == "testname#1234"
    assert returned_summoner.games_played == 0
    assert returned_summoner.kill == 0
    assert returned_summoner.death == 0
    assert returned_summoner.assist == 0


def test_get_summoner_coalesces_null_stats(db_session):
    dao = DAO(db_session)
    db_session.add(
        DaoSummoner(
            id="legacy-null-stats",
            summoner_name="legacy#euw",
            games_played=5,
            games_won=2,
            kill=None,
            death=None,
            assist=None,
        )
    )
    db_session.commit()

    returned_summoner = dao.get_summoner("legacy#euw")

    assert returned_summoner is not None
    assert returned_summoner.kills == 0
    assert returned_summoner.deaths == 0
    assert returned_summoner.assists == 0


def test_add_champion(db_session):
    dao = DAO(db_session)

    champion = Champion.create_default(id="monkey_king")
    dao.add_champion(champion)

    returned = dao.get_champion_dao("monkey_king")
    assert returned.id == "monkey_king"
    assert returned.champion_name is None

    champion.champion_name = "wukong"
    dao.add_champion(champion)

    returned_champion = dao.get_champion_dao("monkey_king")
    assert returned_champion.champion_name == "wukong"


def test_add_match(db_session):
    dao = DAO(db_session)
    db_session.add(Champion.create_default(id="champ_akali", name="Akali"))
    db_session.add(Queue(queue_id=420, map="Summoner's Rift", description="Ranked Solo", notes=None))
    db_session.commit()

    match = Match(
        match_id="match-1",
        start=datetime(2026, 4, 7, 12, 0, tzinfo=UTC),
        end=datetime(2026, 4, 7, 12, 30, tzinfo=UTC),
        version="1.27.2",
        queueId=420,
        queueDescription="Ranked Solo",
        participants=[
            MatchParticipant(
                puuid="player-1",
                name="Alpha",
                tagline="EUW",
                kills=5,
                deaths=0,
                assists=2,
                gold=555,
                team=1,
                champion="Akali",
                won=True,
            ),
            MatchParticipant(
                puuid="player-2",
                name="Bravo",
                tagline="EUW",
                kills=3,
                deaths=2,
                assists=2,
                gold=444,
                team=2,
                champion="Lux",
                won=False,
            ),
        ],
    )

    dao.add_match(match)

    assert db_session.query(DaoMatch).filter(DaoMatch.id == "match-1").one()
    assert db_session.query(DaoMatchParticipant).filter(DaoMatchParticipant.match_id == "match-1").count() == 2
    assert db_session.query(DaoSummoner).filter(DaoSummoner.id == "player-1").one()
    assert db_session.query(DaoSummoner).filter(DaoSummoner.id == "player-2").one()
    assert db_session.query(Champion).filter(Champion.id == "champ_akali").one()
    assert db_session.query(Champion).filter(Champion.id == "Lux").one()


def test_get_matches_applies_pagination(db_session):
    dao = DAO(db_session)
    db_session.add(DaoSummoner(id="player-1", summoner_name="Alpha#EUW", games_played=3, games_won=2, kill=10, death=5, assist=8))
    db_session.add(Champion.create_default(id="Ahri", name="Ahri"))
    db_session.add(Queue(queue_id=420, map="Summoner's Rift", description="Ranked Solo", notes=None))
    db_session.commit()

    matches = [
        DaoMatch(id="match-1", created=100, ended=130, queue_id=420, patch="14.5"),
        DaoMatch(id="match-2", created=200, ended=230, queue_id=420, patch="14.5"),
        DaoMatch(id="match-3", created=300, ended=330, queue_id=420, patch="14.5"),
    ]
    db_session.add_all(matches)
    db_session.add_all(
        [
            DaoMatchParticipant(summoner_id="player-1", match_id="match-1", kill=1, death=2, assist=3, gold=1000, team=100, won=True, champion="Ahri"),
            DaoMatchParticipant(summoner_id="player-1", match_id="match-2", kill=4, death=5, assist=6, gold=2000, team=100, won=False, champion="Ahri"),
            DaoMatchParticipant(summoner_id="player-1", match_id="match-3", kill=7, death=8, assist=9, gold=3000, team=100, won=True, champion="Ahri"),
        ]
    )
    db_session.commit()

    first_page = dao.get_matches("Alpha#EUW", 0, 2)
    second_page = dao.get_matches("Alpha#EUW", 2, 2)

    assert [match.match_id for match in first_page] == ["match-3", "match-2"]
    assert [match.match_id for match in second_page] == ["match-1"]


def test_summoner_lookups_are_case_insensitive(db_session):
    dao = DAO(db_session)
    db_session.add(DaoSummoner(id="player-1", summoner_name="Alpha#EUW", games_played=2, games_won=1, kill=7, death=3, assist=9))
    db_session.add(Champion.create_default(id="Ahri", name="Ahri"))
    db_session.add(Queue(queue_id=420, map="Summoner's Rift", description="Ranked Solo", notes=None))
    db_session.add(DaoMatch(id="match-1", created=100, ended=130, queue_id=420, patch="14.5"))
    db_session.add(
        DaoMatchParticipant(
            summoner_id="player-1",
            match_id="match-1",
            kill=1,
            death=2,
            assist=3,
            gold=1000,
            team=100,
            won=True,
            champion="Ahri",
        )
    )
    db_session.commit()

    summoner = dao.get_summoner("alpha#euw")
    matches = dao.get_matches("ALPHA#euw", 0, 10)
    has_matches = dao.summoner_has_matches("alpha#EUW")
    match_ids = dao.get_match_ids_for_summoner("aLpHa#EuW")

    assert summoner is not None
    assert summoner.name == "Alpha"
    assert [match.match_id for match in matches] == ["match-1"]
    assert has_matches is True
    assert match_ids == {"match-1"}


def test_get_champion_versions_returns_descending_order(db_session):
    dao = DAO(db_session)
    db_session.add(Champion(id="Ahri", champion_name="Ahri"))
    db_session.add(Queue(queue_id=420, map="Summoner's Rift", description="Ranked Solo", notes=None))
    db_session.add_all(
        [
            ChampionStats(champion_id="Ahri", patch="14.4", queue_id=420, games_played=10, games_won=5, games_banned=1, kill=30, assist=20, death=10),
            ChampionStats(champion_id="Ahri", patch="14.10", queue_id=420, games_played=12, games_won=6, games_banned=2, kill=36, assist=24, death=12),
            ChampionStats(champion_id="Ahri", patch="14.5", queue_id=420, games_played=11, games_won=5, games_banned=1, kill=33, assist=22, death=11),
        ]
    )
    db_session.commit()

    versions = dao.get_champion_versions("Ahri")

    assert versions == ["14.10", "14.5", "14.4"]


def test_get_champion_without_patch_returns_all_versions(db_session):
    dao = DAO(db_session)
    db_session.add(Champion(id="Ahri", champion_name="Ahri"))
    db_session.add_all(
        [
            Queue(queue_id=420, map="Summoner's Rift", description="Ranked Solo", notes=None),
            Queue(queue_id=450, map="Howling Abyss", description="ARAM", notes=None),
        ]
    )
    db_session.add_all(
        [
            ChampionStats(champion_id="Ahri", patch="14.5", queue_id=420, games_played=10, games_won=5, games_banned=1, kill=30, assist=20, death=10),
            ChampionStats(champion_id="Ahri", patch="14.4", queue_id=450, games_played=7, games_won=4, games_banned=0, kill=18, assist=25, death=9),
            MatchesAnalyzed(patch="14.5", queue_id=420, count=100),
            MatchesAnalyzed(patch="14.4", queue_id=450, count=70),
        ]
    )
    db_session.commit()

    champion = dao.get_champion("Ahri", None)

    assert champion is not None
    assert len(champion.championStats) == 2


def test_get_champion_rates_use_matches_analyzed(db_session):
    dao = DAO(db_session)
    db_session.add(Champion(id="Ahri", champion_name="Ahri"))
    db_session.add(Queue(queue_id=420, map="Summoner's Rift", description="Ranked Solo", notes=None))
    db_session.add(
        ChampionStats(
            champion_id="Ahri",
            patch="14.5",
            queue_id=420,
            games_played=20,
            games_won=10,
            games_banned=5,
            kill=30,
            assist=20,
            death=10,
        )
    )
    db_session.add(MatchesAnalyzed(patch="14.5", queue_id=420, count=200))
    db_session.commit()

    champion = dao.get_champion("Ahri", ["14.5"])

    assert champion is not None
    stats = champion.championStats[0]
    assert stats.pickrate == 10
    assert stats.banrate == 2.5
