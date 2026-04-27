from app.models.championModels import Champion, ChampionStats
from app.services.championServices import (
    aggregate_stats_for_version,
    build_trend_series,
    get_available_versions,
    get_champion_service,
    serialize_stat,
)


class MockChampionDAO:
    def __init__(self, champion=None):
        self.champion = champion

    def get_champion(self, name: str, version: list[str]):
        return self.champion


def create_champion():
    stats = ChampionStats(
        version="14.5",
        queueDescription="Ranked Solo",
        wins=10,
        gamesPlayed=15,
        kills=100,
        deaths=50,
        assists=80,
        banned=10,
        matchesAnalyzed=200,
    )

    return Champion(
        name="Ahri",
        championStats=[stats],
        id="Ahri"
    )


def test_champion_service_returns_champion():
    champion = create_champion()
    dao = MockChampionDAO(champion)

    result = get_champion_service("Ahri", ["14.5"], dao)

    assert result is not None
    assert result.name == "Ahri"


def test_champion_service_passes_version():
    class SpyDAO:
        def __init__(self):
            self.called_with = None

        def get_champion(self, name, version):
            self.called_with = (name, version)
            return None

    dao = SpyDAO()

    get_champion_service("Ahri", ["14.4"], dao)

    assert dao.called_with == ("Ahri", ["14.4"])


def test_champion_service_returns_none_when_missing():
    dao = MockChampionDAO(None)

    result = get_champion_service("Nonexistent", ["14.5"], dao)

    assert result is None


def test_winrate():
    stats = ChampionStats(version="14.5", queueDescription="Ranked Solo", wins=7, gamesPlayed=10, kills=0, deaths=0, assists=0, banned=0, matchesAnalyzed=10)
    assert stats.winrate == 70


def test_winrate_edge():
    stats = ChampionStats(version="14.5", queueDescription="Ranked Solo", wins=0, gamesPlayed=0, kills=0, deaths=0, assists=0, banned=0, matchesAnalyzed=10)
    assert stats.winrate == -1


def test_kda():
    stats = ChampionStats(version="14.5", queueDescription="Ranked Solo", wins=1, gamesPlayed=0, kills=10, deaths=2, assists=6, banned=0, matchesAnalyzed=1)
    assert stats.kda == 8


def test_kda_zero_deaths():
    stats = ChampionStats(version="14.5", queueDescription="Ranked Solo", wins=1, gamesPlayed=0, kills=10, deaths=0, assists=5, banned=0, matchesAnalyzed=1)
    assert stats.kda == 15


def test_pickrate():
    stats = ChampionStats(version="14.5", queueDescription="Ranked Solo", wins=10, gamesPlayed=20, kills=0, deaths=0, assists=0, banned=0, matchesAnalyzed=200)
    assert stats.pickrate == 10


def test_pickrate_zero_games():
    stats = ChampionStats(version="14.5", queueDescription="Ranked Solo", wins=10, gamesPlayed=20, kills=0, deaths=0, assists=0, banned=0, matchesAnalyzed=0)
    assert stats.pickrate == 0


def test_banrate():
    stats = ChampionStats(version="14.5", queueDescription="Ranked Solo", wins=10, gamesPlayed=20, kills=0, deaths=0, assists=0, banned=20, matchesAnalyzed=100)
    assert stats.banrate == 20


def test_banrate_zero_games():
    stats = ChampionStats(version="14.5", queueDescription="Ranked Solo", wins=10, gamesPlayed=20, kills=0, deaths=0, assists=0, banned=20, matchesAnalyzed=0)
    assert stats.banrate == 0

def test_champion_stats_to_string():
    stats = ChampionStats(version="14.5", queueDescription="Ranked Solo", wins=10, gamesPlayed=20, kills=100, deaths=50, assists=80, banned=10, matchesAnalyzed=200)
    expected_str = " ChampionStats version=14.5 queueDescription=Ranked Solo wins=10"
    assert str(stats) == expected_str


def test_serialize_stat_has_expected_keys():
    stats = ChampionStats(
        version="14.5",
        queueDescription="Ranked Solo",
        wins=10,
        gamesPlayed=15,
        kills=100,
        deaths=50,
        assists=80,
        banned=10,
        matchesAnalyzed=200,
    )

    serialized = serialize_stat(stats)

    assert {
        "version",
        "queueDescription",
        "gamesPlayed",
        "totalMatchesPlayed",
        "winrate",
        "pickrate",
        "banrate",
        "kda",
    }.issubset(serialized.keys())


def test_get_available_versions_normalizes_major_minor():
    stats = [
        ChampionStats(version="16.8.777.3456", queueDescription="Ranked Solo", wins=1, gamesPlayed=1, kills=1, deaths=1, assists=1, banned=0, matchesAnalyzed=10),
        ChampionStats(version="16.8.778.9823", queueDescription="Ranked Solo", wins=1, gamesPlayed=1, kills=1, deaths=1, assists=1, banned=0, matchesAnalyzed=10),
        ChampionStats(version="16.9.100.1", queueDescription="Ranked Solo", wins=1, gamesPlayed=1, kills=1, deaths=1, assists=1, banned=0, matchesAnalyzed=10),
    ]

    assert get_available_versions(stats) == ["16.9", "16.8"]


def test_aggregate_stats_for_version_sums_modes():
    stats = [
        ChampionStats(version="16.8.777.3456", queueDescription="Ranked Solo", wins=4, gamesPlayed=10, kills=20, deaths=10, assists=15, banned=2, matchesAnalyzed=100),
        ChampionStats(version="16.8.778.9823", queueDescription="Ranked Solo", wins=6, gamesPlayed=10, kills=25, deaths=10, assists=20, banned=3, matchesAnalyzed=120),
        ChampionStats(version="16.8.778.9823", queueDescription="ARAM", wins=3, gamesPlayed=8, kills=18, deaths=9, assists=12, banned=1, matchesAnalyzed=120),
    ]

    aggregated = aggregate_stats_for_version(stats, "16.8")
    ranked = next(item for item in aggregated if item.queueDescription == "Ranked Solo")

    assert ranked.version == "16.8"
    assert ranked.wins == 10
    assert ranked.gamesPlayed == 20
    assert ranked.matchesAnalyzed == 220


def test_build_trend_series_groups_by_normalized_version():
    stats = [
        ChampionStats(version="16.8.777.3456", queueDescription="Ranked Solo", wins=4, gamesPlayed=10, kills=20, deaths=10, assists=15, banned=2, matchesAnalyzed=100),
        ChampionStats(version="16.8.778.9823", queueDescription="Ranked Solo", wins=6, gamesPlayed=10, kills=25, deaths=10, assists=20, banned=3, matchesAnalyzed=120),
        ChampionStats(version="16.9.100.1", queueDescription="Ranked Solo", wins=7, gamesPlayed=12, kills=30, deaths=12, assists=22, banned=4, matchesAnalyzed=140),
    ]

    trend_series = build_trend_series(stats)

    assert len(trend_series) == 1
    points = trend_series[0]["points"]
    assert [point["version"] for point in points] == ["16.8", "16.9"]
    assert points[0]["totalMatchesPlayed"] == 20
