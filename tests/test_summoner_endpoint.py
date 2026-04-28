from fastapi.testclient import TestClient

from app.api.config import settings
from app.endpoints import endpoints
from app.main import app
from app.models.summonerModels import Match, MatchPage, Summoner, SummonerChampion
from app.services.summonerServices import SummonerPageServiceResult, SummonerRefreshServiceResult


client = TestClient(app)


def make_summoner() -> Summoner:
    return Summoner(
        puuid="player-puuid",
        name="test",
        tagline="euw",
        wins=5,
        gamesPlayed=10,
        kills=10,
        deaths=5,
        assists=5,
    )


def make_match_page() -> MatchPage:
    matches = [
        Match(
            match_id=i,
            start=__import__("datetime").datetime.now(),
            end=__import__("datetime").datetime.now(),
            version="14.5",
            queueId=420,
            queueDescription="Ranked Solo",
            participants=[],
        )
        for i in range(settings.matches_per_page)
    ]
    return MatchPage(matches=matches, hasMore=True, nextOffset=settings.matches_per_page)

def make_SummonerChampion() -> list[SummonerChampion]:
    return [SummonerChampion(id="fake_id",champion_name="fake_name",games_played=3,wins=1)]


def make_page_data() -> SummonerPageServiceResult:
    return SummonerPageServiceResult(
        summoner=make_summoner(),
        match_page=make_match_page(),
    )


def test_summoner_page_found(monkeypatch):
    monkeypatch.setattr(endpoints, "load_summoner_page", lambda request, name, tagline, offset, count, dao: make_page_data())
    # Prevent creating a real DAO (avoids DB connection during tests)
    from app.main import app as _app
    _app.dependency_overrides[endpoints.get_dao] = lambda: None

    response = client.get("/summoner/test/euw")
    # clear override to avoid leaking state between tests
    _app.dependency_overrides.pop(endpoints.get_dao, None)

    assert response.status_code == 200
    assert "test#euw" in response.text
    assert "Recent Matches" in response.text


def test_summoner_page_not_found_redirects(monkeypatch):
    monkeypatch.setattr(
        endpoints,
        "load_summoner_page",
        lambda request, name, tagline, offset, count, dao: SummonerPageServiceResult(summoner=None, match_page=None),
    )
    from app.main import app as _app
    _app.dependency_overrides[endpoints.get_dao] = lambda: None

    response = client.get("/summoner/nonexistent/euw", follow_redirects=False)
    _app.dependency_overrides.pop(endpoints.get_dao, None)
    assert response.status_code == 303
    assert response.headers["location"] == "/summoner/not-found?name=nonexistent&tagline=euw"


def test_summoner_matches_ajax_response(monkeypatch):
    monkeypatch.setattr(endpoints, "load_summoner_page", lambda request, name, tagline, offset, count, dao: make_page_data())
    from app.main import app as _app
    _app.dependency_overrides[endpoints.get_dao] = lambda: None

    response = client.get("/summoner/test/euw?offset=0&ajax=true")
    _app.dependency_overrides.pop(endpoints.get_dao, None)
    assert response.status_code == 200

    data = response.json()
    assert len(data["matches"]) == settings.matches_per_page
    assert data["nextOffset"] == settings.matches_per_page
    assert data["matches"][0]["queueDescription"] == "Ranked Solo"
    assert "queueId" not in data["matches"][0]


def test_not_found_page_displays_searched_summoner():
    response = client.get("/summoner/not-found?name=missing&tagline=euw")
    assert response.status_code == 200
    assert "Summoner Not Found" in response.text
    assert "missing#euw" in response.text


def test_summoner_refresh_returns_json(monkeypatch):
    monkeypatch.setattr(
        endpoints,
        "refresh_summoner_matches_service",
        lambda request, name, tagline, dao: SummonerRefreshServiceResult(
            summoner=make_summoner(),
            inserted_count=2,
            failed_count=1,
        ),
    )
    from app.main import app as _app
    _app.dependency_overrides[endpoints.get_dao] = lambda: None

    response = client.post("/summoner/test/euw/refresh")
    _app.dependency_overrides.pop(endpoints.get_dao, None)
    assert response.status_code == 200
    assert response.json() == {
        "insertedCount": 2,
        "failedCount": 1,
        "summonerName": "test",
        "summonerTagline": "euw",
    }
