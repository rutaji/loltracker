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