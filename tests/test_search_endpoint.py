import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_page_renders():
    response = client.get("/")
    assert response.status_code == 200
    assert "Choose search:" in response.text

def test_search_redirects_to_summoner_page():
    response = client.post(
        "/",
        data={"summoner_name": "test", "summoner_tagline": "euw", "champion_name": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/summoner/test/euw"

def test_summoner_search_redirects_to_not_found_page():
    response = client.post(
        "/",
        data={"summoner_name": "missing", "summoner_tagline": "euw", "champion_name": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/summoner/not-found?name=missing&tagline=euw"

def test_search_redirects_to_champion_page():
    response = client.post(
        "/",
        data={"champion_name": "", "summoner_tagline": "", "champion_name": "ahri"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/champion/ahri"

def test_champion_search_redirects_to_not_found_page():
    response = client.post(
        "/",
        data={"summoner_name": "", "summoner_tagline": "", "champion_name": "nonexistent"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/champion/not-found?name=nonexistent"