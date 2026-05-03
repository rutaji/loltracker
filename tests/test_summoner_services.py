from datetime import datetime
from types import SimpleNamespace

import httpx
from app.api.config import settings
from app.models.summonerModels import Match, Summoner
from app.services.summonerServices import (
    ingest_matches_from_puuid_service,
    get_matches_service,
    get_summoner_service,
    load_summoner_page,
    refresh_summoner_matches_service,
)
from app.utils.queue_filters import matches_queue_filter


class FakeApiClient:
    def __init__(self, account_data=None):
        self.account_data = account_data or {"puuid": "remote-puuid", "gameName": "remote", "tagLine": "euw"}
        self.match_ids = []
        self.match_info_by_id = {}
        self.division_entries = []

    def get_summoner_by_riot_id(self, name, tagline):
        return self.account_data

    def get_summoner_by_puuid(self, puuid):
        return self.account_data

    def get_match_ids_by_puuid(self, puuid, start=0, count=20):
        return self.match_ids[start:start + count]

    def get_match_info_by_match_id(self, match_id):
        return self.match_info_by_id[match_id]

    def get_league_entries_by_puuid(self, puuid):
        return self.division_entries


def make_request(api_client=None):
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(api_client=api_client or FakeApiClient())))


class MockDAO:
    def __init__(self):
        self.saved_divisions = []

    def get_matches(self, summoner_name, offset, count, queue_filter="all"):
        all_matches = [
            Match(
                match_id=i,
                start=datetime.now(),
                end=datetime.now(),
                version="14.5",
                queueId=420,
                queueDescription="Ranked Solo",
                participants=[],
            )
            for i in range(5)
        ]
        return all_matches[offset:offset + count]

    def summoner_has_matches(self, summoner_name, queue_filter="all"):
        return True

    def get_match_ids_for_summoner(self, summoner_name):
        return set()

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

    def replace_summoner_divisions(self, summoner_id, divisions):
        self.saved_divisions = divisions


class MockSummonerDAO:
    def __init__(self):
        self.saved_summoner = None
        self.saved_divisions = []

    def summoner_has_matches(self, summoner_name, queue_filter="all"):
        return True

    def get_match_ids_for_summoner(self, summoner_name):
        return set()

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

    def replace_summoner_divisions(self, summoner_id, divisions):
        self.saved_divisions = divisions


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


def test_get_matches_service_passes_queue_filter_to_dao():
    captured = {}

    class FilterSpyDAO(MockDAO):
        def get_matches(self, summoner_name, offset, count, queue_filter="all"):
            captured["get_matches_filter"] = queue_filter
            return super().get_matches(summoner_name, offset, count, queue_filter)

        def summoner_has_matches(self, summoner_name, queue_filter="all"):
            captured["has_matches_filter"] = queue_filter
            return super().summoner_has_matches(summoner_name, queue_filter)

    dao = FilterSpyDAO()

    result = get_matches_service(make_request(), "test", "euw", 0, 2, dao, "aram")

    assert len(result.match_page.matches) == 2
    assert captured["get_matches_filter"] == "aram"
    assert captured["has_matches_filter"] == "aram"


def test_get_matches_has_more_is_false_when_page_is_exactly_full():
    class ExactPageDAO:
        def get_matches(self, summoner_name, offset, count, queue_filter="all"):
            all_matches = [
                Match(
                    match_id=i,
                    start=datetime.now(),
                    end=datetime.now(),
                    version="14.5",
                    queueId=420,
                    queueDescription="Ranked Solo",
                    participants=[],
                )
                for i in range(20)
            ]
            return all_matches[offset:offset + count]

        def summoner_has_matches(self, summoner_name, queue_filter="all"):
            return True

        def get_match_ids_for_summoner(self, summoner_name):
            return set()

        def get_summoner(self, summoner_name):
            return Summoner(
                puuid="s1",
                name="test",
                tagline="euw",
                wins=5,
                gamesPlayed=20,
                kills=10,
                deaths=5,
                assists=5,
            )

    result = get_matches_service(make_request(), "test", "euw", 0, 20, ExactPageDAO())

    assert len(result.match_page.matches) == 20
    assert result.match_page.hasMore is False


def test_get_matches_service_fetches_remote_only_when_cache_empty():
    class EmptyMatchDAO:
        def __init__(self):
            self.saved_matches = []
            self.saved_bans= []

        def get_matches(self, summoner_name, offset, count, queue_filter="all"):
            return self.saved_matches[offset:offset + count]

        def summoner_has_matches(self, summoner_name, queue_filter="all"):
            return False

        def get_match_ids_for_summoner(self, summoner_name):
            return set()

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

        def match_exist(self, match_id):
            return False

        def add_match(self, match):
            self.saved_matches.append(match)
        def add_ban(self, bans):
            self.saved_bans.extend(bans)

    api_client = FakeApiClient()
    api_client.match_ids = ["EUW1_1"]
    api_client.match_info_by_id = {
        "EUW1_1": {
            "metadata": {"matchId": "EUW1_1"},
            "info": {
                "gameStartTimestamp": 1710000000000,
                "gameEndTimestamp": 1710001800000,
                "gameVersion": "14.5",
                "queueId": 420,
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


def test_get_matches_service_skips_failed_remote_match_detail():
    class EmptyMatchDAO:
        def __init__(self):
            self.saved_matches = []
            self.saved_bans = []

        def get_matches(self, summoner_name, offset, count, queue_filter="all"):
            return self.saved_matches[offset:offset + count]

        def summoner_has_matches(self, summoner_name, queue_filter="all"):
            return False

        def get_match_ids_for_summoner(self, summoner_name):
            return set()

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

        def match_exist(self, match_id):
            return False

        def add_match(self, match):
            self.saved_matches.append(match)
        def add_ban(self,bans):
            self.saved_bans.extend(bans)

    class FlakyApiClient(FakeApiClient):
        def get_match_info_by_match_id(self, match_id):
            if match_id == "EUW1_2":
                raise httpx.ConnectTimeout("handshake timed out")
            return self.match_info_by_id[match_id]

    api_client = FlakyApiClient()
    api_client.match_ids = ["EUW1_1", "EUW1_2"]
    api_client.match_info_by_id = {
        "EUW1_1": {
            "metadata": {"matchId": "EUW1_1"},
            "info": {
                "gameStartTimestamp": 1710000000000,
                "gameEndTimestamp": 1710001800000,
                "gameVersion": "14.5",
                "queueId": 420,
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
    assert result.match_page.hasMore is False
    assert len(dao.saved_matches) == 1


def test_get_matches_service_keeps_sync_cap_even_with_queue_filter():
    class EmptyMatchDAO:
        def __init__(self):
            self.saved_matches = []
            self.saved_bans = []

        def get_matches(self, summoner_name, offset, count, queue_filter="all"):
            filtered_matches = [
                match for match in self.saved_matches
                if matches_queue_filter(match.queueId, queue_filter)
            ]
            return filtered_matches[offset:offset + count]

        def summoner_has_matches(self, summoner_name, queue_filter="all"):
            return any(matches_queue_filter(match.queueId, queue_filter) for match in self.saved_matches)

        def get_match_ids_for_summoner(self, summoner_name):
            return set()

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

        def match_exist(self, match_id):
            return False

        def add_match(self, match):
            self.saved_matches.append(match)

        def add_ban(self, bans):
            self.saved_bans.extend(bans)

    api_client = FakeApiClient()
    api_client.match_ids = ["EUW1_1", "EUW1_2", "EUW1_3"]
    api_client.match_info_by_id = {
        "EUW1_1": {
            "metadata": {"matchId": "EUW1_1"},
            "info": {
                "gameStartTimestamp": 1710000000000,
                "gameEndTimestamp": 1710001800000,
                "gameVersion": "14.5",
                "queueId": 420,
                "participants": [],
            },
        },
        "EUW1_2": {
            "metadata": {"matchId": "EUW1_2"},
            "info": {
                "gameStartTimestamp": 1710002000000,
                "gameEndTimestamp": 1710003800000,
                "gameVersion": "14.5",
                "queueId": 440,
                "participants": [],
            },
        },
        "EUW1_3": {
            "metadata": {"matchId": "EUW1_3"},
            "info": {
                "gameStartTimestamp": 1710004000000,
                "gameEndTimestamp": 1710005800000,
                "gameVersion": "14.5",
                "queueId": 450,
                "participants": [],
            },
        },
    }

    dao = EmptyMatchDAO()
    request = make_request(api_client)

    result = get_matches_service(request, "test", "euw", 0, 1, dao, "aram")

    assert result.refreshed_from_remote is True
    assert result.match_page.matches == []
    assert len(dao.saved_matches) == 2


def test_load_summoner_page_returns_not_found_when_summoner_missing():
    class MissingSummonerDAO:
        def summoner_has_matches(self, summoner_name, queue_filter="all"):
            return False

        def get_match_ids_for_summoner(self, summoner_name):
            return set()

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
            self.added_bans = []

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

        def get_matches(self, summoner_name, offset, count, queue_filter="all"):
            return self.saved_matches[offset:offset + count]

        def summoner_has_matches(self, summoner_name, queue_filter="all"):
            return False

        def get_match_ids_for_summoner(self, summoner_name):
            return set()

        def match_exist(self, match_id):
            return False

        def add_match(self, match):
            self.saved_matches.append(match)
        def add_ban(self,bans):
            self.added_bans.extend(bans)

    api_client = FakeApiClient()
    api_client.match_ids = ["EUW1_1"]
    api_client.match_info_by_id = {
        "EUW1_1": {
            "metadata": {"matchId": "EUW1_1"},
            "info": {
                "gameStartTimestamp": 1710000000000,
                "gameEndTimestamp": 1710001800000,
                "gameVersion": "14.5",
                "queueId": 420,
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
    api_client = FakeApiClient({"puuid": "remote-puuid", "gameName": "nope", "tagLine": "euw"})
    api_client.division_entries = [{"queueType": "RANKED_SOLO_5x5", "tier": "DIAMOND", "rank": "IV", "leaguePoints": 10, "wins": 21, "losses": 20}]
    request = make_request(api_client)

    result = get_summoner_service(request, "nope", "euw", dao)

    assert result is not None
    assert result.puuid == "remote-puuid"
    assert result.name == "nope"
    assert dao.saved_summoner is not None
    assert dao.saved_summoner.puuid == "remote-puuid"
    assert len(dao.saved_divisions) == 1


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

        def get_matches(self, summoner_name, offset, count, queue_filter="all"):
            return []

        def summoner_has_matches(self, summoner_name, queue_filter="all"):
            return False

        def get_match_ids_for_summoner(self, summoner_name):
            return set()

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

    assert result.match_page.matches == []
    assert api_client.puuid_used == "remote-puuid"


def test_get_matches_service_does_not_fetch_remote_when_cache_exists():
    class CachedMatchDAO:
        def __init__(self):
            self.added_matches = []

        def get_matches(self, summoner_name, offset, count, queue_filter="all"):
            return [
                Match(
                    match_id="m1",
                    start=datetime.now(),
                    end=datetime.now(),
                    version="14.5",
                    queueId=420,
                    queueDescription="Ranked Solo",
                    participants=[],
                )
            ]

        def summoner_has_matches(self, summoner_name, queue_filter="all"):
            return True

        def get_match_ids_for_summoner(self, summoner_name):
            return {"m1"}

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

    class FailingRemoteApiClient:
        def get_match_ids_by_puuid(self, puuid, start=0, count=20):
            raise AssertionError("remote match ids should not be fetched when cache exists")

        def get_match_info_by_match_id(self, match_id):
            raise AssertionError("remote match details should not be fetched when cache exists")

    dao = CachedMatchDAO()
    request = make_request(FailingRemoteApiClient())

    result = get_matches_service(request, "test", "euw", 0, 3, dao)

    assert [match.match_id for match in result.match_page.matches] == ["m1"]
    assert dao.added_matches == []


def test_refresh_summoner_matches_service_inserts_only_missing_matches():
    class RefreshDAO:
        def __init__(self):
            self.added_matches = []
            self.added_bans = []

        def get_summoner(self, summoner_name):
            return Summoner(
                puuid="cached-puuid",
                name="test",
                tagline="euw",
                wins=1,
                gamesPlayed=2,
                kills=3,
                deaths=4,
                assists=5,
            )

        def get_match_ids_for_summoner(self, summoner_name):
            return {"m1"}

        def match_exist(self, match_id):
            return match_id == "m1"

        def add_match(self, match):
            self.added_matches.append(match)
        def add_ban(self, bans):
            self.added_bans.extend(bans)


    class RefreshApiClient:
        def get_summoner_by_puuid(self, puuid):
            return {"puuid": puuid, "gameName": "test", "tagLine": "euw"}

        def get_match_ids_by_puuid(self, puuid, start=0, count=20):
            return ["m1", "m2", "m3"]

        def get_match_info_by_match_id(self, match_id):
            return {
                "metadata": {"matchId": match_id},
                "info": {
                    "gameStartTimestamp": 1_700_000_000_000,
                    "gameEndTimestamp": 1_700_000_600_000,
                    "gameVersion": "14.5",
                    "queueId": 420,
                    "participants": [],
                },
            }

    dao = RefreshDAO()
    request = make_request(RefreshApiClient())

    result = refresh_summoner_matches_service(request, "test", "euw", dao)

    assert result.summoner is not None
    assert result.inserted_count == 2
    assert result.failed_count == 0
    assert [match.match_id for match in dao.added_matches] == ["m2", "m3"]


def test_refresh_summoner_matches_service_updates_renamed_summoner():
    class RefreshDAO:
        def __init__(self):
            self.saved_summoners = []
            self.lookup_names = []
            self.added_bans=[]
            self.saved_divisions = []

        def get_summoner(self, summoner_name):
            self.lookup_names.append(summoner_name)
            if summoner_name == "Renamed#EUW":
                return Summoner(
                    puuid="cached-puuid",
                    name="Renamed",
                    tagline="EUW",
                    wins=1,
                    gamesPlayed=2,
                    kills=3,
                    deaths=4,
                    assists=5,
                )
            return Summoner(
                puuid="cached-puuid",
                name="OldName",
                tagline="EUW",
                wins=1,
                gamesPlayed=2,
                kills=3,
                deaths=4,
                assists=5,
            )

        def get_match_ids_for_summoner(self, summoner_name):
            return set()

        def add_summoner(self, summoner):
            self.saved_summoners.append(summoner)

        def replace_summoner_divisions(self, summoner_id, divisions):
            self.saved_divisions = divisions

        def add_match(self, match):
            raise AssertionError("match insertion is not part of this test")
        def add_ban(self, bans):
            self.added_bans.extend(bans)

    class RefreshApiClient:
        def get_summoner_by_puuid(self, puuid):
            return {"puuid": puuid, "gameName": "Renamed", "tagLine": "EUW"}

        def get_match_ids_by_puuid(self, puuid, start=0, count=20):
            return []

        def get_league_entries_by_puuid(self, puuid):
            return [{"queueType": "RANKED_FLEX_SR", "tier": "EMERALD", "rank": "I", "leaguePoints": 96, "wins": 22, "losses": 33}]

    dao = RefreshDAO()
    request = make_request(RefreshApiClient())

    result = refresh_summoner_matches_service(request, "OldName", "EUW", dao)

    assert result.summoner is not None
    assert result.summoner.name == "Renamed"
    assert dao.saved_summoners[0].name == "Renamed"
    assert dao.lookup_names[-1] == "Renamed#EUW"
    assert len(dao.saved_divisions) == 1


def test_refresh_summoner_matches_service_pages_past_first_batch_for_older_matches(monkeypatch):
    monkeypatch.setattr(settings, "summoner_sync_batch_size", 3)
    monkeypatch.setattr(settings, "summoner_sync_stop_after", 2)

    class RefreshDAO:
        def __init__(self):
            self.added_matches = []
            self.added_bans = []

        def get_summoner(self, summoner_name):
            return Summoner(
                puuid="cached-puuid",
                name="test",
                tagline="euw",
                wins=1,
                gamesPlayed=2,
                kills=3,
                deaths=4,
                assists=5,
            )

        def get_match_ids_for_summoner(self, summoner_name):
            return {"m1", "m2", "m3", "m4"}

        def match_exist(self, match_id):
            return match_id in {"m1", "m2", "m3", "m4"}

        def add_match(self, match):
            self.added_matches.append(match)

        def add_ban(self,bans):
            self.added_bans.extend(bans)

    class RefreshApiClient:
        def __init__(self):
            self.starts = []

        def get_summoner_by_puuid(self, puuid):
            return {"puuid": puuid, "gameName": "test", "tagLine": "euw"}

        def get_match_ids_by_puuid(self, puuid, start=0, count=20):
            self.starts.append(start)
            all_match_ids = ["m1", "m2", "m3", "m4", "m5", "m6"]
            return all_match_ids[start:start + count]

        def get_match_info_by_match_id(self, match_id):
            return {
                "metadata": {"matchId": match_id},
                "info": {
                    "gameStartTimestamp": 1_700_000_000_000,
                    "gameEndTimestamp": 1_700_000_600_000,
                    "gameVersion": "14.5",
                    "queueId": 420,
                    "participants": [],
                },
            }

    dao = RefreshDAO()
    api_client = RefreshApiClient()
    request = make_request(api_client)

    result = refresh_summoner_matches_service(request, "test", "euw", dao)

    assert result.inserted_count == 2
    assert result.failed_count == 0
    assert [match.match_id for match in dao.added_matches] == ["m5", "m6"]
    assert api_client.starts == [0, 3]


def test_ingest_matches_from_puuid_service_retries_encrypted_identifier(monkeypatch):
    class RefreshDAO:
        def __init__(self):
            self.saved_summoner = None

        def get_summoner(self, summoner_name):
            return None

        def get_match_ids_for_summoner(self, summoner_name):
            return set()

        def add_summoner(self, summoner):
            self.saved_summoner = summoner

    class RefreshApiClient:
        def __init__(self):
            self.calls = []

        def get_summoner_by_puuid(self, puuid):
            self.calls.append(("get_summoner_by_puuid", puuid))
            if puuid == "encrypted-id":
                response = type("Resp", (), {"status_code": 400, "text": "Bad Request - Exception decrypting encrypted-id"})()
                raise httpx.HTTPStatusError("Bad Request", request=httpx.Request("GET", "https://example.com"), response=response)
            return {"puuid": puuid, "gameName": "resolved-player", "tagLine": "euw"}

        def get_summoner_by_encrypted_id(self, encrypted_id):
            self.calls.append(("get_summoner_by_encrypted_id", encrypted_id))
            return {"puuid": "resolved-puuid", "name": "resolved-player"}

        def get_match_ids_by_puuid(self, puuid, start=0, count=20):
            self.calls.append(("get_match_ids_by_puuid", puuid, start, count))
            return []

    monkeypatch.setattr(settings, "summoner_sync_batch_size", 20)
    monkeypatch.setattr(settings, "periodic_sync_stop_after", 5)

    dao = RefreshDAO()
    request = make_request(RefreshApiClient())

    result = ingest_matches_from_puuid_service(request, "encrypted-id", dao)

    assert result.summoner is not None
    assert result.summoner.puuid == "resolved-puuid"
    assert result.failed_count == 0
    assert dao.saved_summoner is not None
    assert dao.saved_summoner.puuid == "resolved-puuid"


def test_refresh_uses_snapshot_then_match_exists_for_candidates_only():
    class RefreshDAO:
        def __init__(self):
            self.added_matches = []
            self.match_exists_calls = []
            self.added_bans = []

        def get_summoner(self, summoner_name):
            return Summoner(
                puuid="cached-puuid",
                name="test",
                tagline="euw",
                wins=1,
                gamesPlayed=2,
                kills=3,
                deaths=4,
                assists=5,
            )

        def get_match_ids_for_summoner(self, summoner_name):
            return {"m1"}

        def match_exist(self, match_id):
            self.match_exists_calls.append(match_id)
            return match_id == "m2"

        def add_match(self, match):
            self.added_matches.append(match)
        def add_ban(self, bans):
            self.added_bans.extend(bans)

    class RefreshApiClient:
        def get_summoner_by_puuid(self, puuid):
            return {"puuid": puuid, "gameName": "test", "tagLine": "euw"}

        def get_match_ids_by_puuid(self, puuid, start=0, count=20):
            return ["m1", "m2", "m3"]

        def get_match_info_by_match_id(self, match_id):
            return {
                "metadata": {"matchId": match_id},
                "info": {
                    "gameStartTimestamp": 1_700_000_000_000,
                    "gameEndTimestamp": 1_700_000_600_000,
                    "gameVersion": "14.5",
                    "queueId": 420,
                    "participants": [],
                },
            }

    dao = RefreshDAO()
    request = make_request(RefreshApiClient())

    result = refresh_summoner_matches_service(request, "test", "euw", dao)

    assert result.inserted_count == 1
    assert dao.match_exists_calls == ["m2", "m3"]
    assert [match.match_id for match in dao.added_matches] == ["m3"]
