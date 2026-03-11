import pytest
from datetime import datetime
from app.services.summonerServices import get_summoner_service, get_matches_service
from fastapi import HTTPException
from app.models.summonerModels import Summoner, Match, MatchParticipant

class MockDAO:
    def get_matches(self, name, offset, count):

        all_matches = [
            Match(
                match_id=i,
                start=datetime.now(),
                end=datetime.now(),
                version="14.5",
                mode="Ranked",
                participants=[]
            )
            for i in range(5)
        ]

        return all_matches[offset:offset+count]
    
class MockSummonerDAO:
    def get_summoner(self, name):
        if name == "test":
            return Summoner(
                name="test",
                wins=5,
                losses=5,
                kills=10,
                deaths=5,
                assists=5
            )
        return None

    def get_matches(self, name, offset, count):
        return [
            Match(
                match_id=i,
                start=datetime.now(),
                end=datetime.now(),
                version="14.5",
                mode="Ranked",
                participants=[]
            )
            for i in range(offset, offset + count)
        ]

def test_winrate_normal():
    s = Summoner(name="test", wins=1, losses=1, kills=0, deaths=1, assists=0)
    assert s.winrate == 50

    s = Summoner(name="test", wins=75, losses=25, kills=0, deaths=1, assists=0)
    assert s.winrate == 75

    s = Summoner(name="test", wins=1, losses=0, kills=0, deaths=1, assists=0)
    assert s.winrate == 100

def test_winrate_float():
    s = Summoner(name="test", wins=2, losses=1, kills=0, deaths=1, assists=0)
    assert round(s.winrate, 2) == 66.67

def test_winrate_edge():
    s = Summoner(name="test", wins=0, losses=0, kills=0, deaths=1, assists=0)
    assert s.winrate == -1

def test_kda_normal():
    s = Summoner(name="test", wins=0, losses=0, kills=10, deaths=5, assists=5)
    assert s.kda == 3

def test_kda_normal():
    s = Summoner(name="test", wins=0, losses=0, kills=10, deaths=5, assists=5)
    assert s.kda == 3

def test_get_matches_pagination():
    dao = MockDAO()
    
    result = get_matches_service("test", 0, 2, dao)
    assert result.matches[0].match_id == 0
    assert result.matches[1].match_id == 1
    assert result.hasMore is True
    assert result.nextOffset == 2
    
    result = get_matches_service("test", 4, 2, dao)
    assert result.matches[0].match_id == 4
    assert result.hasMore is False
    assert result.nextOffset == 6

def test_get_summoner_service_found():
    dao = MockSummonerDAO()
    result = get_summoner_service("test", dao, 0, 3)
    
    assert result["summoner"].name == "test"
    assert result["summoner"].winrate == 50
    assert result["summoner"].kda == 3
    assert len(result["matchData"].matches) == 3
    assert result["matchData"].hasMore is True

def test_get_summoner_service_not_found():
    dao = MockSummonerDAO()
    with pytest.raises(HTTPException) as excinfo:
        get_summoner_service("nope", dao, 0, 3)
    assert excinfo.value.status_code == 404