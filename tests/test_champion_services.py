import sys, os
from app.services.championServices import get_champion_service
from app.models.championModels import Champion, ChampionStats

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.models.championModels import ChampionStats

class MockChampionDAO:

    def __init__(self, champion=None):
        self.champion = champion

    def get_champion(self, name: str, version: str):
        return self.champion


def create_champion():
    stats = ChampionStats(
        version="14.5",
        gamemode="Ranked",
        wins=10,
        gamesPlayed=15,
        kills=100,
        deaths=50,
        assists=80,
        banned=10,
        matchesAnalyzed=200
    )

    return Champion(
        name="Ahri",
        championStats=[stats]
    )


def test_champion_service_returns_champion():

    champion = create_champion()
    dao = MockChampionDAO(champion)

    result = get_champion_service("Ahri", "14.5", dao)

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

    get_champion_service("Ahri", "14.4", dao)

    assert dao.called_with == ("Ahri", "14.4")


def test_champion_service_returns_none_when_missing():

    dao = MockChampionDAO(None)

    result = get_champion_service("Nonexistent", "14.5", dao)

    assert result is None


def test_winrate():
    stats = ChampionStats(version="14.5", gamemode="Ranked", wins=7, gamesPlayed=10,
        kills=0, deaths=0, assists=0, banned=0, matchesAnalyzed=10
    )
    assert stats.winrate == 70

def test_winrate_edge():
    stats = ChampionStats(version="14.5", gamemode="Ranked", wins=0, gamesPlayed=0,
        kills=0, deaths=0, assists=0, banned=0, matchesAnalyzed=10
    )
    assert stats.winrate == -1


def test_kda():
    stats = ChampionStats(version="14.5", gamemode="Ranked", wins=1, gamesPlayed=0,
        kills=10, deaths=2, assists=6, banned=0, matchesAnalyzed=1
    )
    assert stats.kda == 8


def test_kda_zero_deaths():
    stats = ChampionStats(version="14.5", gamemode="Ranked", wins=1, gamesPlayed=0,
        kills=10, deaths=0, assists=5, banned=0, matchesAnalyzed=1
    )
    assert stats.kda == 15


def test_pickrate():
    stats = ChampionStats(version="14.5", gamemode="Ranked", wins=10, gamesPlayed=20,
        kills=0, deaths=0, assists=0, banned=0, matchesAnalyzed=200
    )
    assert stats.pickrate == 10

def test_pickrate_zero_games():
    stats = ChampionStats(version="14.5", gamemode="Ranked", wins=10, gamesPlayed=20,
        kills=0, deaths=0, assists=0, banned=0, matchesAnalyzed=0
    )
    assert stats.pickrate == 0

def test_banrate():
    stats = ChampionStats(version="14.5", gamemode="Ranked", wins=10, gamesPlayed=20,
        kills=0, deaths=0, assists=0, banned=20, matchesAnalyzed=100
    )
    assert stats.banrate == 20

def test_banrate_zero_games():
    stats = ChampionStats(version="14.5", gamemode="Ranked", wins=10, gamesPlayed=20,
        kills=0, deaths=0, assists=0, banned=20, matchesAnalyzed=0
    )
    assert stats.banrate == 0