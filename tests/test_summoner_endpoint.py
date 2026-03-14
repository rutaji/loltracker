import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_summoner_page_found():
    response = client.get("/summoner/test/euw")
    assert response.status_code == 200
    assert "test" in response.text
    assert "Matches" in response.text

def test_summoner_page_not_found_redirects():
    response = client.get("/summoner/nonexistent/euw", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/summoner/not-found?name=nonexistent&tagline=euw"

def test_summoner_matches_ajax_response():
    response = client.get("/summoner/test/euw?offset=0&ajax=true")
    assert response.status_code == 200

    data = response.json()
    assert len(data["matches"]) == 3
    assert data["nextOffset"] == 3

def test_not_found_page_displays_searched_summoner():
    response = client.get("/summoner/not-found?name=missing&tagline=euw")
    assert response.status_code == 200
    assert "Summoner Not Found" in response.text
    assert "missing#euw" in response.text

