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
                queueDescription="Ranked Solo",
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
    assert data["selectedVersion"] == "14.5"
    assert data["availableVersions"] == ["14.5"]
    assert "trendSeriesByQueue" in data
    assert "selectedVersionStats" in data
    assert "championImagePath" in data
    assert data["selectedVersionStats"][0]["queueDescription"] == "Ranked Solo"
    assert "gamemode" not in data["selectedVersionStats"][0]


def test_champion_ajax_filters_version(monkeypatch):
    champion = Champion(
        name="Ahri",
        championStats=[
            ChampionStats(
                version="14.4",
                queueDescription="Ranked Solo",
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
    assert data["selectedVersionStats"] == []


def test_champion_ajax_switches_stats_between_versions(monkeypatch):
    champion = Champion(
        name="Ahri",
        championStats=[
            ChampionStats(
                version="16.8.777.3456",
                queueDescription="Ranked Solo",
                wins=8,
                gamesPlayed=20,
                kills=80,
                deaths=30,
                assists=60,
                banned=5,
                matchesAnalyzed=200,
            ),
            ChampionStats(
                version="16.8.778.9823",
                queueDescription="Ranked Solo",
                wins=12,
                gamesPlayed=20,
                kills=110,
                deaths=35,
                assists=70,
                banned=6,
                matchesAnalyzed=220,
            ),
            ChampionStats(
                version="16.9.100.1",
                queueDescription="Ranked Solo",
                wins=15,
                gamesPlayed=20,
                kills=130,
                deaths=40,
                assists=80,
                banned=8,
                matchesAnalyzed=250,
            ),
        ],
    )
    monkeypatch.setattr(endpoints, "get_champion_service", lambda name, version, dao: champion)

    response_168 = client.get("/champion/ahri?version=16.8&ajax=true")
    response_169 = client.get("/champion/ahri?version=16.9&ajax=true")

    data_168 = response_168.json()
    data_169 = response_169.json()

    assert data_168["selectedVersion"] == "16.8"
    assert data_169["selectedVersion"] == "16.9"
    assert data_168["selectedVersionStats"][0]["wins"] == 20
    assert data_169["selectedVersionStats"][0]["wins"] == 15
    assert data_168["availableVersions"] == ["16.9", "16.8"]
    assert "trendSeriesByQueue" in data_168
    assert "championImagePath" in data_168
