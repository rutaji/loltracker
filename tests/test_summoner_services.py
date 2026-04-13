from datetime import datetime
from types import SimpleNamespace

from app.models.summonerModels import Match, Summoner
from app.services.summonerServices import get_matches_service, get_summoner_service


class FakeApiClient:
    def __init__(self, account_data=None):
        self.account_data = account_data or {"puuid": "remote-puuid", "gameName": "remote", "tagLine": "euw"}

    def get_summoner_by_riot_id(self, name, tagline):
        return self.account_data

    def get_match_ids_by_puuid(self, puuid, start=0, count=20):
        return []

    def get_match_info_by_match_id(self, match_id):
        raise AssertionError("should not fetch remote match info in this test")


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

def test_losses_calculated():
    s = Summoner(puuid="s1", name="test", tagline="euw", wins=5, gamesPlayed=10, kills=0, deaths=1, assists=0)
    assert s.losses == 5


def test_get_matches_pagination():
    dao = MockDAO()
    request = make_request()

    result = get_matches_service(request, "test", "euw", 0, 2, dao)
    assert result.matches[0].match_id == 0
    assert result.matches[1].match_id == 1
    assert result.hasMore is True
    assert result.nextOffset == 2

    result = get_matches_service(request, "test", "euw", 4, 2, dao)
    assert result.matches[0].match_id == 4
    assert result.hasMore is False
    assert result.nextOffset == 6


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


def test_get_summoner_service_returns_none_on_exception():
    class FailingApiClient:
        def get_summoner_by_riot_id(self, name, tagline):
            raise RuntimeError("riot api error")

    dao = MockSummonerDAO()
    request = make_request(FailingApiClient())

    result = get_summoner_service(request, "unknown", "euw", dao)

    assert result is None
    assert dao.saved_summoner is None


def test_get_matches_service_fetches_puuid_when_cached_summoner_has_empty_puuid():
    class EmptyPuuidDAO:
        def __init__(self):
            self.puuid_used = None

        def get_matches(self, summoner_name, offset, count):
            return []

        def get_summoner(self, summoner_name):
            return Summoner(
                puuid="",
                name="unknown",
                tagline="euw",
                wins=0,
                gamesPlayed=0,
                kills=0,
                deaths=0,
                assists=0,
            )

    class TrackingApiClient:
        def __init__(self):
            self.puuid_used = None

        def get_summoner_by_riot_id(self, name, tagline):
            return {"puuid": "remote-puuid", "gameName": name, "tagLine": tagline}

        def get_match_ids_by_puuid(self, puuid, start=0, count=20):
            self.puuid_used = puuid
            return []

    dao = EmptyPuuidDAO()
    api_client = TrackingApiClient()
    request = make_request(api_client)

    result = get_matches_service(request, "unknown", "euw", 0, 2, dao)

    assert result.matches == []
    assert api_client.puuid_used == "remote-puuid"


def test_get_matches_service_adds_new_remote_matches_to_dao():
    class MatchSyncDAO:
        def __init__(self):
            self.added_matches = []

        def get_matches(self, summoner_name, offset, count):
            return [
                Match(
                    match_id="m1",
                    start=datetime.now(),
                    end=datetime.now(),
                    version="14.5",
                    mode="Ranked",
                    participants=[],
                )
            ]

        def get_summoner(self, summoner_name):
            return Summoner(
                puuid="cached-puuid",
                name="test",
                tagline="euw",
                wins=0,
                gamesPlayed=0,
                kills=0,
                deaths=0,
                assists=0,
            )

        def add_match(self, match):
            self.added_matches.append(match)

    class MatchSyncApiClient:
        def get_match_ids_by_puuid(self, puuid, start=0, count=20):
            return ["m1", "m2", "m3"]

        def get_match_info_by_match_id(self, match_id):
            return {
                "metadata": {"matchId": match_id},
                "info": {
                    "gameStartTimestamp": 1_700_000_000_000,
                    "gameEndTimestamp": 1_700_000_600_000,
                    "gameVersion": "14.5",
                    "gameMode": "Ranked",
                    "participants": [],
                },
            }

    dao = MatchSyncDAO()
    request = make_request(MatchSyncApiClient())

    result = get_matches_service(request, "test", "euw", 0, 3, dao)

    assert [match.match_id for match in dao.added_matches] == ["m2", "m3"]
    assert [match.match_id for match in result.matches] == ["m1", "m2", "m3"]

