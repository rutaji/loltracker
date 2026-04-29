from urllib.parse import quote

from app.riot.riotApiClient import RiotApiClient


class DummyResponse:
    def __init__(self, payload):
        self.payload = payload
        self.raise_called = False

    def raise_for_status(self):
        self.raise_called = True

    def json(self):
        return self.payload


class DummyClient:
    def __init__(self, response, capture):
        self.response = response
        self.capture = capture

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, headers=None, params=None):
        self.capture["url"] = url
        self.capture["headers"] = headers
        self.capture["params"] = params
        return self.response


def test_init_stores_configuration():
    client = RiotApiClient(
        api_key="test-key",
        regional_routing="asia",
        platform_routing="kr",
        timeout=15.0,
    )

    assert client.api_key == "test-key"
    assert client.regional_routing == "asia"
    assert client.platform_routing == "kr"
    assert client.timeout == 15.0
    assert client._headers == {"X-Riot-Token": "test-key"}


def test_get_summoner_by_riot_id_builds_expected_request(monkeypatch):
    capture = {}
    response = DummyResponse({"puuid": "player-puuid"})

    def fake_client(*, timeout):
        capture["timeout"] = timeout
        return DummyClient(response, capture)

    monkeypatch.setattr("app.riot.riotApiClient.httpx.Client", fake_client)

    client = RiotApiClient(api_key="test-key", regional_routing="europe", timeout=15.0)
    result = client.get_summoner_by_riot_id("Player Name", "EU/W")

    assert result == {"puuid": "player-puuid"}
    assert response.raise_called is True
    assert capture["timeout"] == 15.0
    assert capture["url"] == (
        "https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/"
        f"{quote('Player Name', safe='')}/{quote('EU/W', safe='')}"
    )
    assert capture["headers"] == {"X-Riot-Token": "test-key"}
    assert capture["params"] is None


def test_get_match_ids_by_puuid_passes_query_params(monkeypatch):
    capture = {}
    response = DummyResponse(["EUW1_1", "EUW1_2"])

    def fake_client(*, timeout):
        capture["timeout"] = timeout
        return DummyClient(response, capture)

    monkeypatch.setattr("app.riot.riotApiClient.httpx.Client", fake_client)

    client = RiotApiClient(api_key="test-key", regional_routing="americas")
    result = client.get_match_ids_by_puuid("puuid/value", start=10, count=5)

    assert result == ["EUW1_1", "EUW1_2"]
    assert response.raise_called is True
    assert capture["url"] == (
        "https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/"
        f"{quote('puuid/value', safe='')}/ids"
    )
    assert capture["headers"] == {"X-Riot-Token": "test-key"}
    assert capture["params"] == {"start": 10, "count": 5}


def test_get_match_info_by_match_id_requests_single_match(monkeypatch):
    capture = {}
    response = DummyResponse({"metadata": {"matchId": "EUW1_123"}})

    def fake_client(*, timeout):
        capture["timeout"] = timeout
        return DummyClient(response, capture)

    monkeypatch.setattr("app.riot.riotApiClient.httpx.Client", fake_client)

    client = RiotApiClient(api_key="test-key", regional_routing="asia")
    result = client.get_match_info_by_match_id("KR_123/456")

    assert result == {"metadata": {"matchId": "EUW1_123"}}
    assert response.raise_called is True
    assert capture["url"] == (
        "https://asia.api.riotgames.com/lol/match/v5/matches/"
        f"{quote('KR_123/456', safe='')}"
    )
    assert capture["headers"] == {"X-Riot-Token": "test-key"}
    assert capture["params"] is None


def test_get_league_entries_uses_platform_routing(monkeypatch):
    capture = {}
    response = DummyResponse([{"summonerId": "enc"}])

    def fake_client(*, timeout):
        capture["timeout"] = timeout
        return DummyClient(response, capture)

    monkeypatch.setattr("app.riot.riotApiClient.httpx.Client", fake_client)

    client = RiotApiClient(api_key="test-key", regional_routing="europe", platform_routing="euw1")
    result = client.get_league_entries("RANKED_SOLO_5x5", "GOLD", "II")

    assert result == [{"summonerId": "enc"}]
    assert capture["url"] == "https://euw1.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/GOLD/II"


def test_get_summoner_by_encrypted_id_uses_platform_routing(monkeypatch):
    capture = {}
    response = DummyResponse({"puuid": "p"})

    def fake_client(*, timeout):
        capture["timeout"] = timeout
        return DummyClient(response, capture)

    monkeypatch.setattr("app.riot.riotApiClient.httpx.Client", fake_client)

    client = RiotApiClient(api_key="test-key", regional_routing="europe", platform_routing="euw1")
    result = client.get_summoner_by_encrypted_id("abc/123")

    assert result == {"puuid": "p"}
    assert capture["url"] == f"https://euw1.api.riotgames.com/lol/summoner/v4/summoners/{quote('abc/123', safe='')}"


def test_get_consumes_rate_limiter_tokens(monkeypatch):
    capture = {}
    response = DummyResponse({"ok": True})

    def fake_client(*, timeout):
        return DummyClient(response, capture)

    class DummyRateLimiter:
        def __init__(self):
            self.calls = []

        def acquire(self, tokens=1, block=True, timeout=None):
            self.calls.append((tokens, block, timeout))
            return True

    monkeypatch.setattr("app.riot.riotApiClient.httpx.Client", fake_client)
    limiter = DummyRateLimiter()
    client = RiotApiClient(api_key="test-key", regional_routing="europe", rate_limiter=limiter)

    result = client.get_match_info_by_match_id("EUW1_1")

    assert result == {"ok": True}
    assert limiter.calls == [(1, True, 10)]
