import pytest
from app.services.summonerServices import get_summoner_service, get_matches, calc_winrate, calc_kda
from fastapi import HTTPException

class MockDAO:
    def get_matches(self, name, offset, count):
        all_matches = [{"match_id": i} for i in range(0, 5)]  # 5 mock matches
        return all_matches[offset:offset+count]
    
class MockSummonerDAO:
    def get_summoner(self, name):
        if name == "test":
            return {"name": "test", "wins": 5, "losses": 5, "kills": 10, "deaths": 5, "assists": 5}
        return None

    def get_matches(self, name, offset, count):
        return [{"match_id": i} for i in range(offset, offset+count)]

def test_calc_winrate_normal():
    assert calc_winrate(1, 1) == 50
    assert calc_winrate(75, 25) == 75
    assert calc_winrate(1, 0) == 100

def test_calc_winrate_edge():
    assert calc_winrate(0, 0) == -1

def test_calc_kda_normal():
    assert calc_kda(10, 5, 5) == 3

def test_calc_kda_edge():
    assert calc_kda(10, 0, 10) == 20

def test_get_matches_pagination():
    dao = MockDAO()
    
    result = get_matches("test", 0, 2, dao)
    assert result["matches"] == [{"match_id": 0}, {"match_id": 1}]
    assert result["hasMore"] is True
    assert result["nextOffset"] == 2
    
    result = get_matches("test", 4, 2, dao)
    assert result["matches"] == [{"match_id": 4}]
    assert result["hasMore"] is False
    assert result["nextOffset"] == 6

def test_get_summoner_service_found():
    dao = MockSummonerDAO()
    result = get_summoner_service("test", dao, 0, 3)
    
    assert result["summoner"]["name"] == "test"
    assert result["summoner"]["winrate"] == 50
    assert result["summoner"]["kda"] == 3
    assert len(result["matchData"]["matches"]) == 3
    assert result["matchData"]["hasMore"] is True

def test_get_summoner_service_not_found():
    dao = MockSummonerDAO()
    with pytest.raises(HTTPException) as excinfo:
        get_summoner_service("nope", dao, 0, 3)
    assert excinfo.value.status_code == 404