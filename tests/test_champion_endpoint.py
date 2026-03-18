import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_champion_page_found():
    response = client.get("/champion/ahri")
    assert response.status_code == 200
    assert "Ahri" in response.text
    assert "Banrate" in response.text

def test_champion_page_not_found_redirects():
    response = client.get("/champion/nonexistent", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/champion/not-found?name=nonexistent"

def test_not_found_page_displays_searched_champion():
    response = client.get("/champion/not-found?name=missing")
    assert response.status_code == 200
    assert "Champion Not Found" in response.text
    assert "missing" in response.text

def test_champion_ajax_response():
    response = client.get("/champion/ahri?version=14.5&ajax=true")

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Ahri"
    assert len(data["championStats"]) > 0

def test_champion_ajax_filters_version():
    response = client.get("/champion/ahri?version=14.4&ajax=true")

    data = response.json()

    for stat in data["championStats"]:
        assert stat["version"] == "14.4"

def test_champion_no_stats_for_version():
    response = client.get("/champion/ahri?version=99.9&ajax=true")

    data = response.json()

    assert data["championStats"] == []