from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.DAO import DAO
from app.database.models import (
    Base,
    Ban as DaoBan,
    Champion,
    ChampionStats,
    Item,
    Match as DaoMatch,
    MatchParticipant as DaoMatchParticipant,
    MatchesAnalyzed,
    Queue,
    Summoner as DaoSummoner,
    SummonerQueue as DaoSummonerQueue,
)
from app.models.summonerModels import Match, MatchParticipant, Summoner, SummonerDivision
from app.models.summonerModels import BanParsed


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    session.add(Item(item_id=0, name=None, description=None))
    session.commit()
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


def test_replace_summoner_divisions_persists_and_returns_queue_descriptions(db_session):
    dao = DAO(db_session)
    db_session.add(DaoSummoner(id="player-1", summoner_name="ranked#euw", games_played=5, games_won=3, kill=10, death=5, assist=8))
    db_session.add_all(
        [
            Queue(queue_id=420, map="Summoner's Rift", description="Ranked Solo", notes=None),
            Queue(queue_id=440, map="Summoner's Rift", description="Ranked Flex", notes=None),
        ]
    )
    db_session.commit()

    dao.replace_summoner_divisions(
        "player-1",
        [
            SummonerDivision(queueId=440, queueDescription="", tier="EMERALD", rank="I", leaguePoints=96, wins=22, losses=33),
            SummonerDivision(queueId=420, queueDescription="", tier="DIAMOND", rank="IV", leaguePoints=10, wins=21, losses=20),
        ],
    )

    returned_summoner = dao.get_summoner("ranked#euw")

    assert returned_summoner is not None
    assert [(division.queueDescription, division.displayTierRank) for division in returned_summoner.divisions] == [
        ("Ranked Solo", "Diamond IV"),
        ("Ranked Flex", "Emerald I"),
    ]
    assert db_session.query(DaoSummonerQueue).filter(DaoSummonerQueue.summoner_id == "player-1").count() == 2


def test_get_summoner_adds_unranked_defaults_for_missing_ranked_queues(db_session):
    dao = DAO(db_session)
    db_session.add(DaoSummoner(id="player-1", summoner_name="ranked#euw", games_played=5, games_won=3, kill=10, death=5, assist=8))
    db_session.add_all(
        [
            Queue(queue_id=420, map="Summoner's Rift", description="Ranked Solo", notes=None),
            Queue(queue_id=440, map="Summoner's Rift", description="Ranked Flex", notes=None),
        ]
    )
    db_session.add(
        DaoSummonerQueue(
            summoner_id="player-1",
            queue_id=420,
            tier="DIAMOND",
            rank="IV",
            league_points=10,
            wins=21,
            losses=20,
        )
    )
    db_session.commit()

    returned_summoner = dao.get_summoner("ranked#euw")

    assert returned_summoner is not None
    assert [(division.queueDescription, division.displayTierRank) for division in returned_summoner.divisions] == [
        ("Ranked Solo", "Diamond IV"),
        ("Ranked Flex", "Unranked"),
    ]


def test_summoner_division_display_omits_rank_for_apex_tiers():
    master_division = SummonerDivision(
        queueId=420,
        queueDescription="Ranked Solo",
        tier="MASTER",
        rank="I",
        leaguePoints=250,
        wins=30,
        losses=20,
    )

    challenger_division = SummonerDivision(
        queueId=420,
        queueDescription="Ranked Solo",
        tier="CHALLENGER",
        rank="I",
        leaguePoints=900,
        wins=50,
        losses=10,
    )

    assert master_division.displayTierRank == "Master"
    assert challenger_division.displayTierRank == "Challenger"


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
    db_session.add(Item(item_id=1055, name="Doran's Blade", description="Starter item"))
    db_session.add(Item(item_id=3340, name="Stealth Ward", description="Trinket"))
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
                position="TOP",
                champion="Akali",
                item0=1055,
                item6=3340,
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
                position="JUNGLE",
                champion="Lux",
                roleBoundItem=1209,
                won=False,
            ),
        ],
    )

    dao.add_match(match)

    assert db_session.query(DaoMatch).filter(DaoMatch.id == "match-1").one()
    assert db_session.query(DaoMatchParticipant).filter(DaoMatchParticipant.match_id == "match-1").count() == 2
    persisted_participant = db_session.query(DaoMatchParticipant).filter(DaoMatchParticipant.summoner_id == "player-1").one()
    assert persisted_participant.position == "TOP"
    assert persisted_participant.item0 == 1055
    assert persisted_participant.item6 == 3340
    assert db_session.query(DaoSummoner).filter(DaoSummoner.id == "player-1").one()
    assert db_session.query(DaoSummoner).filter(DaoSummoner.id == "player-2").one()
    assert db_session.query(Champion).filter(Champion.id == "champ_akali").one()
    assert db_session.query(Champion).filter(Champion.id == "Lux").one()
    assert db_session.query(Item).filter(Item.item_id == 1209).one()


def test_get_matches_returns_item_ids(db_session):
    dao = DAO(db_session)
    db_session.add_all(
        [
            DaoSummoner(id="player-1", summoner_name="Alpha#EUW", games_played=1, games_won=1, kill=5, death=2, assist=7),
            Champion.create_default(id="Ahri", name="Ahri"),
            Queue(queue_id=420, map="Summoner's Rift", description="Ranked Solo", notes=None),
            Item(item_id=1055, name="Doran's Blade", description="Starter item"),
            Item(item_id=3340, name="Stealth Ward", description="Trinket"),
            DaoMatch(id="match-1", created=100, ended=130, queue_id=420, patch="14.5"),
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
                item0=1055,
                item6=3340,
            ),
        ]
    )
    db_session.commit()

    matches = dao.get_matches("Alpha#EUW", 0, 10)

    assert matches[0].participants[0].item0 == 1055
    assert matches[0].participants[0].item6 == 3340
    assert [item.id for item in matches[0].participants[0].items] == [1055, 0, 0, 0, 0, 0, 3340, 0]
    assert matches[0].participants[0].items[0].name == "Doran's Blade"


def test_add_match_updates_existing_summoner_name_from_complete_participant_identity(db_session):
    dao = DAO(db_session)
    db_session.add(DaoSummoner(id="player-1", summoner_name="OldName#EUW", games_played=0, games_won=0, kill=0, death=0, assist=0))
    db_session.add(Champion.create_default(id="Ahri", name="Ahri"))
    db_session.add(Queue(queue_id=420, map="Summoner's Rift", description="Ranked Solo", notes=None))
    db_session.commit()

    match = Match(
        match_id="match-name-update",
        start=datetime(2026, 4, 7, 12, 0, tzinfo=UTC),
        end=datetime(2026, 4, 7, 12, 30, tzinfo=UTC),
        version="1.27.2",
        queueId=420,
        queueDescription="Ranked Solo",
        participants=[
            MatchParticipant(
                puuid="player-1",
                name="NewName",
                tagline="EUW",
                kills=1,
                deaths=2,
                assists=3,
                gold=1000,
                team=100,
                champion="Ahri",
                won=True,
            ),
        ],
    )

    dao.add_match(match)

    assert db_session.query(DaoSummoner).filter(DaoSummoner.id == "player-1").one().summoner_name == "NewName#EUW"


def test_add_match_does_not_overwrite_existing_summoner_name_with_incomplete_identity(db_session):
    dao = DAO(db_session)
    db_session.add(DaoSummoner(id="player-1", summoner_name="KnownName#EUW", games_played=0, games_won=0, kill=0, death=0, assist=0))
    db_session.add(Champion.create_default(id="Ahri", name="Ahri"))
    db_session.add(Queue(queue_id=420, map="Summoner's Rift", description="Ranked Solo", notes=None))
    db_session.commit()

    match = Match(
        match_id="match-incomplete-name",
        start=datetime(2026, 4, 7, 12, 0, tzinfo=UTC),
        end=datetime(2026, 4, 7, 12, 30, tzinfo=UTC),
        version="1.27.2",
        queueId=420,
        queueDescription="Ranked Solo",
        participants=[
            MatchParticipant(
                puuid="player-1",
                name="",
                tagline="EUW",
                kills=1,
                deaths=2,
                assists=3,
                gold=1000,
                team=100,
                champion="Ahri",
                won=True,
            ),
        ],
    )

    dao.add_match(match)

    assert db_session.query(DaoSummoner).filter(DaoSummoner.id == "player-1").one().summoner_name == "KnownName#EUW"


def test_add_ban_allows_same_champion_banned_by_different_teams(db_session):
    dao = DAO(db_session)
    db_session.add(DaoMatch(id="match-cross-team-bans", created=100, ended=130, queue_id=None, patch="14.5"))
    db_session.commit()

    dao.add_ban(
        [
            BanParsed(match_id="match-cross-team-bans", team=100, ban_order=1, champion_key=799),
            BanParsed(match_id="match-cross-team-bans", team=200, ban_order=1, champion_key=799),
        ]
    )

    assert db_session.query(DaoBan).filter(DaoBan.match_id == "match-cross-team-bans").count() == 2


def test_add_ban_preserves_same_team_same_champion_in_different_ban_slots(db_session):
    dao = DAO(db_session)
    db_session.add(DaoMatch(id="match-arena-bans", created=100, ended=130, queue_id=None, patch="14.5"))
    db_session.commit()

    dao.add_ban(
        [
            BanParsed(match_id="match-arena-bans", team=100, ban_order=4, champion_key=799),
            BanParsed(match_id="match-arena-bans", team=100, ban_order=13, champion_key=799),
        ]
    )

    assert db_session.query(DaoBan).filter(DaoBan.match_id == "match-arena-bans").count() == 2


def test_get_matches_applies_pagination(db_session):
    dao = DAO(db_session)
    db_session.add(DaoSummoner(id="player-1", summoner_name="Alpha#EUW", games_played=3, games_won=2, kill=10, death=5, assist=8))
    db_session.add(Champion.create_default(id="Ahri", name="Ahri"))
    db_session.add_all(
        [
            Queue(queue_id=420, map="Summoner's Rift", description="Ranked Solo", notes=None),
            Queue(queue_id=450, map="Howling Abyss", description="ARAM", notes=None),
            Queue(queue_id=1700, map="Rings of Wrath", description="Arena", notes=None),
        ]
    )
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


def test_get_matches_filters_by_queue_category(db_session):
    dao = DAO(db_session)
    db_session.add(DaoSummoner(id="player-1", summoner_name="Alpha#EUW", games_played=4, games_won=2, kill=10, death=5, assist=8))
    db_session.add(Champion.create_default(id="Ahri", name="Ahri"))
    db_session.add_all(
        [
            Queue(queue_id=420, map="Summoner's Rift", description="Ranked Solo", notes=None),
            Queue(queue_id=440, map="Summoner's Rift", description="Ranked Flex", notes=None),
            Queue(queue_id=450, map="Howling Abyss", description="ARAM", notes=None),
            Queue(queue_id=1700, map="Rings of Wrath", description="Arena", notes=None),
        ]
    )
    db_session.add_all(
        [
            DaoMatch(id="match-solo", created=400, ended=430, queue_id=420, patch="14.5"),
            DaoMatch(id="match-flex", created=300, ended=330, queue_id=440, patch="14.5"),
            DaoMatch(id="match-aram", created=200, ended=230, queue_id=450, patch="14.5"),
            DaoMatch(id="match-other", created=100, ended=130, queue_id=1700, patch="14.5"),
        ]
    )
    db_session.add_all(
        [
            DaoMatchParticipant(summoner_id="player-1", match_id="match-solo", kill=1, death=2, assist=3, gold=1000, team=100, won=True, champion="Ahri"),
            DaoMatchParticipant(summoner_id="player-1", match_id="match-flex", kill=1, death=2, assist=3, gold=1000, team=100, won=True, champion="Ahri"),
            DaoMatchParticipant(summoner_id="player-1", match_id="match-aram", kill=1, death=2, assist=3, gold=1000, team=100, won=True, champion="Ahri"),
            DaoMatchParticipant(summoner_id="player-1", match_id="match-other", kill=1, death=2, assist=3, gold=1000, team=100, won=True, champion="Ahri"),
        ]
    )
    db_session.commit()

    ranked_solo_matches = dao.get_matches("Alpha#EUW", 0, 10, "ranked_solo")
    ranked_flex_matches = dao.get_matches("Alpha#EUW", 0, 10, "ranked_flex")
    aram_matches = dao.get_matches("Alpha#EUW", 0, 10, "aram")
    other_matches = dao.get_matches("Alpha#EUW", 0, 10, "other")

    assert [match.match_id for match in ranked_solo_matches] == ["match-solo"]
    assert [match.match_id for match in ranked_flex_matches] == ["match-flex"]
    assert [match.match_id for match in aram_matches] == ["match-aram"]
    assert [match.match_id for match in other_matches] == ["match-other"]


def test_get_matches_returns_participants_in_stable_order(db_session):
    dao = DAO(db_session)
    db_session.add_all(
        [
            DaoSummoner(id="player-1", summoner_name="Charlie#EUW", games_played=1, games_won=1, kill=7, death=3, assist=9),
            DaoSummoner(id="player-2", summoner_name="Alpha#EUW", games_played=1, games_won=1, kill=7, death=3, assist=9),
            DaoSummoner(id="player-3", summoner_name="Delta#EUW", games_played=1, games_won=0, kill=7, death=3, assist=9),
            DaoSummoner(id="player-4", summoner_name="Bravo#EUW", games_played=1, games_won=0, kill=7, death=3, assist=9),
        ]
    )
    db_session.add_all(
        [
            Champion.create_default(id="Ahri", name="Ahri"),
            Champion.create_default(id="Lux", name="Lux"),
            Champion.create_default(id="Garen", name="Garen"),
            Champion.create_default(id="Jinx", name="Jinx"),
            Queue(queue_id=420, map="Summoner's Rift", description="Ranked Solo", notes=None),
            DaoMatch(id="match-1", created=100, ended=130, queue_id=420, patch="14.5"),
        ]
    )
    db_session.add_all(
        [
            DaoMatchParticipant(summoner_id="player-3", match_id="match-1", kill=1, death=2, assist=3, gold=1000, team=200, position="TOP", won=False, champion="Garen"),
            DaoMatchParticipant(summoner_id="player-1", match_id="match-1", kill=1, death=2, assist=3, gold=1000, team=100, position="MIDDLE", won=True, champion="Ahri"),
            DaoMatchParticipant(summoner_id="player-4", match_id="match-1", kill=1, death=2, assist=3, gold=1000, team=200, position="JUNGLE", won=False, champion="Jinx"),
            DaoMatchParticipant(summoner_id="player-2", match_id="match-1", kill=1, death=2, assist=3, gold=1000, team=100, position="TOP", won=True, champion="Lux"),
        ]
    )
    db_session.commit()

    matches = dao.get_matches("Charlie#EUW", 0, 10)

    assert len(matches) == 1
    assert [(participant.team, participant.position, participant.name) for participant in matches[0].participants] == [
        (100, "TOP", "Alpha"),
        (100, "MIDDLE", "Charlie"),
        (200, "TOP", "Delta"),
        (200, "JUNGLE", "Bravo"),
    ]


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
