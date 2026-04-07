from fastapi.testclient import TestClient

from app.api.config import settings
from app.endpoints import endpoints
from app.main import app
from app.models.summonerModels import Match, MatchPage, Summoner


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
            mode="Ranked Solo",
            participants=[],
        )
        for i in range(settings.matches_per_page)
    ]
    return MatchPage(matches=matches, hasMore=True, nextOffset=settings.matches_per_page)


def test_summoner_page_found(monkeypatch):
    monkeypatch.setattr(endpoints, "get_summoner_service", lambda request, name, tagline, dao: make_summoner())
    monkeypatch.setattr(endpoints, "get_matches_service", lambda request, name, tagline, offset, count, dao: make_match_page())

    response = client.get("/summoner/test/euw")
    assert response.status_code == 200
    assert "test#euw" in response.text
    assert "Recent Matches" in response.text


def test_summoner_page_not_found_redirects(monkeypatch):
    monkeypatch.setattr(endpoints, "get_summoner_service", lambda request, name, tagline, dao: None)

    response = client.get("/summoner/nonexistent/euw", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/summoner/not-found?name=nonexistent&tagline=euw"


def test_summoner_matches_ajax_response(monkeypatch):
    monkeypatch.setattr(endpoints, "get_summoner_service", lambda request, name, tagline, dao: make_summoner())
    monkeypatch.setattr(endpoints, "get_matches_service", lambda request, name, tagline, offset, count, dao: make_match_page())

    response = client.get("/summoner/test/euw?offset=0&ajax=true")
    assert response.status_code == 200

    data = response.json()
    assert len(data["matches"]) == settings.matches_per_page
    assert data["nextOffset"] == settings.matches_per_page


def test_not_found_page_displays_searched_summoner():
    response = client.get("/summoner/not-found?name=missing&tagline=euw")
    assert response.status_code == 200
    assert "Summoner Not Found" in response.text
    assert "missing#euw" in response.text
