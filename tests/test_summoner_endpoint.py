from fastapi.testclient import TestClient

from app.api.config import settings
from app.endpoints import endpoints
from app.main import app
from app.models.summonerModels import Match, MatchPage, MatchParticipant, Summoner
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


def make_page_data() -> SummonerPageServiceResult:
    return SummonerPageServiceResult(
        summoner=make_summoner(),
        match_page=make_match_page(),
    )


def test_summoner_page_found(monkeypatch):
    monkeypatch.setattr(endpoints, "load_summoner_page", lambda request, name, tagline, offset, count, dao, queue_filter: make_page_data())

    response = client.get("/summoner/test/euw")
    assert response.status_code == 200
    assert "test#euw" in response.text
    assert "Recent Matches" in response.text
    assert "Games Shown" in response.text


def test_summoner_page_links_match_participants(monkeypatch):
    page_data = make_page_data()
    page_data.match_page.matches[0].participants = [
        MatchParticipant(
            puuid="participant-puuid",
            name="Other Player",
            tagline="EUW",
            kills=1,
            deaths=2,
            assists=3,
            gold=1000,
            team=100,
            position="TOP",
            champion="Ahri",
            won=True,
        )
    ]
    monkeypatch.setattr(endpoints, "load_summoner_page", lambda request, name, tagline, offset, count, dao, queue_filter: page_data)

    response = client.get("/summoner/test/euw")

    assert response.status_code == 200
    assert 'href="/summoner/Other%20Player/EUW"' in response.text


def test_summoner_page_not_found_redirects(monkeypatch):
    monkeypatch.setattr(
        endpoints,
        "load_summoner_page",
        lambda request, name, tagline, offset, count, dao, queue_filter: SummonerPageServiceResult(summoner=None, match_page=None),
    )

    response = client.get("/summoner/nonexistent/euw", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/summoner/not-found?name=nonexistent&tagline=euw"


def test_summoner_matches_ajax_response(monkeypatch):
    monkeypatch.setattr(endpoints, "load_summoner_page", lambda request, name, tagline, offset, count, dao, queue_filter: make_page_data())

    response = client.get("/summoner/test/euw?offset=0&ajax=true")
    assert response.status_code == 200

    data = response.json()
    assert len(data["matches"]) == settings.matches_per_page
    assert data["nextOffset"] == settings.matches_per_page
    assert data["matches"][0]["queueDescription"] == "Ranked Solo"
    assert "queueId" not in data["matches"][0]


def test_summoner_queue_filter_is_forwarded(monkeypatch):
    captured = {}

    def fake_load_summoner_page(request, name, tagline, offset, count, dao, queue_filter):
        captured["queue_filter"] = queue_filter
        return make_page_data()

    monkeypatch.setattr(endpoints, "load_summoner_page", fake_load_summoner_page)

    response = client.get("/summoner/test/euw?queue_filter=aram")

    assert response.status_code == 200
    assert captured["queue_filter"] == "aram"


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

    response = client.post("/summoner/test/euw/refresh")
    assert response.status_code == 200
    assert response.json() == {
        "insertedCount": 2,
        "failedCount": 1,
        "summonerName": "test",
        "summonerTagline": "euw",
    }
