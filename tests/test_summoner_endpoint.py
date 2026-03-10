import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_summoner_page_found():
    response = client.get("/summoner/test")
    assert response.status_code == 200
    assert "test" in response.text

def test_summoner_page_not_found():
    response = client.get("/summoner/nonexistent")
    assert response.status_code == 404

