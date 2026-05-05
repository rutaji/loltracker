from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_page_renders():
    response = client.get("/")
    assert response.status_code == 200
    assert "Choose search" in response.text
    assert "LoL Tracker" in response.text


def test_search_redirects_to_summoner_page():
    response = client.post(
        "/",
        data={"summoner_name": "test", "summoner_tagline": "euw", "champion_name": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/summoner/test/euw"


def test_search_redirects_to_champion_page():
    response = client.post(
        "/",
        data={"summoner_name": "", "summoner_tagline": "", "champion_name": "ahri"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/champion/ahri"


def test_empty_search_redirects_back_home():
    response = client.post(
        "/",
        data={"summoner_name": "", "summoner_tagline": "", "champion_name": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
