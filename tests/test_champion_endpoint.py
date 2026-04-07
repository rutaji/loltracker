from fastapi.testclient import TestClient

from app.endpoints import endpoints
from app.main import app
from app.models.championModels import Champion, ChampionStats


client = TestClient(app)


def make_champion(name: str = "Ahri") -> Champion:
    return Champion(
        name=name,
        championStats=[
            ChampionStats(
                version="14.5",
                gamemode="Ranked Solo",
                wins=10,
                gamesPlayed=20,
                kills=100,
                deaths=40,
                assists=80,
                banned=5,
                matchesAnalyzed=100,
            )
        ],
    )


def test_champion_page_found(monkeypatch):
    monkeypatch.setattr(endpoints, "get_champion_service", lambda name, version, dao: make_champion("Ahri"))

    response = client.get("/champion/ahri")
    assert response.status_code == 200
    assert "Ahri" in response.text
    assert "Banrate" in response.text


def test_champion_page_not_found_redirects(monkeypatch):
    monkeypatch.setattr(endpoints, "get_champion_service", lambda name, version, dao: None)

    response = client.get("/champion/nonexistent", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/champion/not-found?name=nonexistent"


def test_not_found_page_displays_searched_champion():
    response = client.get("/champion/not-found?name=missing")
    assert response.status_code == 200
    assert "Champion Not Found" in response.text
    assert "missing" in response.text


def test_champion_ajax_response(monkeypatch):
    monkeypatch.setattr(endpoints, "get_champion_service", lambda name, version, dao: make_champion("Ahri"))

    response = client.get("/champion/ahri?version=14.5&ajax=true")
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Ahri"
    assert len(data["championStats"]) == 1


def test_champion_ajax_filters_version(monkeypatch):
    champion = Champion(
        name="Ahri",
        championStats=[
            ChampionStats(
                version="14.4",
                gamemode="Ranked Solo",
                wins=8,
                gamesPlayed=16,
                kills=80,
                deaths=32,
                assists=64,
                banned=4,
                matchesAnalyzed=100,
            )
        ],
    )
    monkeypatch.setattr(endpoints, "get_champion_service", lambda name, version, dao: champion)

    response = client.get("/champion/ahri?version=14.4&ajax=true")
    data = response.json()

    for stat in data["championStats"]:
        assert stat["version"] == "14.4"


def test_champion_no_stats_for_version(monkeypatch):
    monkeypatch.setattr(endpoints, "get_champion_service", lambda name, version, dao: Champion(name="Ahri", championStats=[]))

    response = client.get("/champion/ahri?version=99.9&ajax=true")
    data = response.json()

    assert data["championStats"] == []
