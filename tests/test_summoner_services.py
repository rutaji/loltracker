from datetime import datetime
from types import SimpleNamespace

from app.models.summonerModels import Match, Summoner
from app.services.summonerServices import get_matches_service, get_summoner_service, load_summoner_page


class FakeApiClient:
    def __init__(self, account_data=None):
        self.account_data = account_data or {"puuid": "remote-puuid", "gameName": "remote", "tagLine": "euw"}
        self.match_ids = []
        self.match_info_by_id = {}

    def get_summoner_by_riot_id(self, name, tagline):
        return self.account_data

    def get_match_ids_by_puuid(self, puuid, start=0, count=20):
        return self.match_ids[start:start + count]

    def get_match_info_by_match_id(self, match_id):
        return self.match_info_by_id[match_id]


def make_request(api_client=None):
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(api_client=api_client or FakeApiClient())))


class MockDAO:
    def get_matches(self, summoner_name, offset, count):
        all_matches = [
            Match(
                match_id=i,
                start=datetime.now(),
                end=datetime.now(),
                version="14.5",
                mode="Ranked",
                participants=[],
            )
            for i in range(5)
        ]
        return all_matches[offset:offset + count]

    def summoner_has_matches(self, summoner_name):
        return True

    def get_summoner(self, summoner_name):
        return Summoner(
            puuid="s1",
            name="test",
            tagline="euw",
            wins=5,
            gamesPlayed=10,
            kills=10,
            deaths=5,
            assists=5,
        )


class MockSummonerDAO:
    def __init__(self):
        self.saved_summoner = None

    def summoner_has_matches(self, summoner_name):
        return True

    def get_summoner(self, summoner_name):
        if summoner_name == "test#euw":
            return Summoner(
                puuid="s1",
                name="test",
                tagline="euw",
                wins=5,
                gamesPlayed=10,
                kills=10,
                deaths=5,
                assists=5,
            )
        return None

    def add_summoner(self, summoner):
        self.saved_summoner = summoner


def test_winrate_normal():
    s = Summoner(puuid="s1", name="test", tagline="euw", wins=1, gamesPlayed=2, kills=0, deaths=1, assists=0)
    assert s.winrate == 50

    s = Summoner(puuid="s1", name="test", tagline="euw", wins=75, gamesPlayed=100, kills=0, deaths=1, assists=0)
    assert s.winrate == 75

    s = Summoner(puuid="s1", name="test", tagline="euw", wins=1, gamesPlayed=1, kills=0, deaths=1, assists=0)
    assert s.winrate == 100


def test_winrate_float():
    s = Summoner(puuid="s1", name="test", tagline="euw", wins=2, gamesPlayed=3, kills=0, deaths=1, assists=0)
    assert round(s.winrate, 2) == 66.67


def test_winrate_edge():
    s = Summoner(puuid="s1", name="test", tagline="euw", wins=0, gamesPlayed=0, kills=0, deaths=1, assists=0)
    assert s.winrate == -1


def test_kda_normal():
    s = Summoner(puuid="s1", name="test", tagline="euw", wins=0, gamesPlayed=0, kills=10, deaths=5, assists=5)
    assert s.kda == 3


def test_kda_zero_deaths():
    s = Summoner(puuid="s1", name="test", tagline="euw", wins=0, gamesPlayed=0, kills=10, deaths=0, assists=5)
    assert s.kda == 15


def test_get_matches_pagination():
    dao = MockDAO()
    request = make_request()

    result = get_matches_service(request, "test", "euw", 0, 2, dao)
    assert result.match_page.matches[0].match_id == 0
    assert result.match_page.matches[1].match_id == 1
    assert result.match_page.hasMore is True
    assert result.match_page.nextOffset == 2
    assert result.refreshed_from_remote is False

    result = get_matches_service(request, "test", "euw", 4, 2, dao)
    assert result.match_page.matches[0].match_id == 4
    assert result.match_page.hasMore is False
    assert result.match_page.nextOffset == 6
    assert result.refreshed_from_remote is False


def test_get_matches_service_fetches_remote_only_when_cache_empty():
    class EmptyMatchDAO:
        def __init__(self):
            self.saved_matches = []

        def get_matches(self, summoner_name, offset, count):
            return []

        def summoner_has_matches(self, summoner_name):
            return False

        def get_summoner(self, summoner_name):
            return Summoner(
                puuid="remote-puuid",
                name="test",
                tagline="euw",
                wins=0,
                gamesPlayed=0,
                kills=0,
                deaths=0,
                assists=0,
            )

        def add_match(self, match):
            self.saved_matches.append(match)

    api_client = FakeApiClient()
    api_client.match_ids = ["EUW1_1"]
    api_client.match_info_by_id = {
        "EUW1_1": {
            "metadata": {"matchId": "EUW1_1"},
            "info": {
                "gameStartTimestamp": 1710000000000,
                "gameEndTimestamp": 1710001800000,
                "gameVersion": "14.5",
                "gameMode": "CLASSIC",
                "participants": [
                    {
                        "puuid": "remote-puuid",
                        "riotIdGameName": "test",
                        "riotIdTagline": "euw",
                        "kills": 5,
                        "deaths": 2,
                        "assists": 7,
                        "goldEarned": 12345,
                        "teamId": 100,
                        "championName": "Ahri",
                        "win": True,
                    }
                ],
            },
        }
    }

    dao = EmptyMatchDAO()
    request = make_request(api_client)

    result = get_matches_service(request, "test", "euw", 0, 2, dao)

    assert result.refreshed_from_remote is True
    assert len(result.match_page.matches) == 1
    assert len(dao.saved_matches) == 1


def test_load_summoner_page_returns_not_found_when_summoner_missing():
    class MissingSummonerDAO:
        def get_summoner(self, summoner_name):
            return None

        def add_summoner(self, summoner):
            raise AssertionError("should not save summoner in this test")

    request = make_request(FakeApiClient({"puuid": None, "gameName": "", "tagLine": ""}))
    dao = MissingSummonerDAO()

    result = load_summoner_page(request, "missing", "euw", 0, 2, dao)

    assert result.summoner is None
    assert result.match_page is None


def test_load_summoner_page_refreshes_summoner_after_remote_matches():
    class PageLoadDAO:
        def __init__(self):
            self.saved_matches = []
            self.get_summoner_calls = 0

        def get_summoner(self, summoner_name):
            self.get_summoner_calls += 1
            if self.get_summoner_calls == 1:
                return Summoner(
                    puuid="remote-puuid",
                    name="test",
                    tagline="euw",
                    wins=0,
                    gamesPlayed=0,
                    kills=0,
                    deaths=0,
                    assists=0,
                )
            return Summoner(
                puuid="remote-puuid",
                name="test",
                tagline="euw",
                wins=1,
                gamesPlayed=1,
                kills=5,
                deaths=2,
                assists=7,
            )

        def get_matches(self, summoner_name, offset, count):
            return []

        def summoner_has_matches(self, summoner_name):
            return False

        def add_match(self, match):
            self.saved_matches.append(match)

    api_client = FakeApiClient()
    api_client.match_ids = ["EUW1_1"]
    api_client.match_info_by_id = {
        "EUW1_1": {
            "metadata": {"matchId": "EUW1_1"},
            "info": {
                "gameStartTimestamp": 1710000000000,
                "gameEndTimestamp": 1710001800000,
                "gameVersion": "14.5",
                "gameMode": "CLASSIC",
                "participants": [
                    {
                        "puuid": "remote-puuid",
                        "riotIdGameName": "test",
                        "riotIdTagline": "euw",
                        "kills": 5,
                        "deaths": 2,
                        "assists": 7,
                        "goldEarned": 12345,
                        "teamId": 100,
                        "championName": "Ahri",
                        "win": True,
                    }
                ],
            },
        }
    }

    dao = PageLoadDAO()
    request = make_request(api_client)

    result = load_summoner_page(request, "test", "euw", 0, 2, dao)

    assert result.summoner is not None
    assert result.summoner.gamesPlayed == 1
    assert result.match_page is not None
    assert len(result.match_page.matches) == 1


def test_get_summoner_service_found():
    dao = MockSummonerDAO()
    request = make_request()

    result = get_summoner_service(request, "test", "euw", dao)

    assert result is not None
    assert result.name == "test"
    assert result.tagline == "euw"
    assert result.winrate == 50
    assert result.kda == 3
    assert dao.saved_summoner is None


def test_get_summoner_service_not_found_fetches_remote_and_saves():
    dao = MockSummonerDAO()
    request = make_request(FakeApiClient({"puuid": "remote-puuid", "gameName": "nope", "tagLine": "euw"}))

    result = get_summoner_service(request, "nope", "euw", dao)

    assert result is not None
    assert result.puuid == "remote-puuid"
    assert result.name == "nope"
    assert dao.saved_summoner is not None
    assert dao.saved_summoner.puuid == "remote-puuid"
