import sys, os
from datetime import datetime
from app.services.summonerServices import get_summoner_service, get_matches_service
from app.models.summonerModels import Summoner, Match, MatchParticipant

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

class MockDAO:
    def get_matches(self, name, tagline, offset, count):

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
    def get_summoner(self, name, tagline):
        if name == "test":
            return Summoner(
                puuid="s1",
                name="test",
                tagline=tagline,
                wins=5,
                gamesPlayed=10,
                kills=10,
                deaths=5,
                assists=5
            )
        return None

    def get_matches(self, name, tagline, offset, count):
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
    s = Summoner(puuid="s1", name="test", tagline="euw", wins=1, gamesPlayed=2, kills=0, deaths=1, assists=0)
    assert s.winrate == 50

    s = Summoner(puuid="s1", name="test", tagline="euw", wins=75, gamesPlayed=100, kills=0, deaths=1, assists=0)
    assert s.winrate == 75

    s = Summoner(puuid="s1", name="test", tagline="euw", wins=1, gamesPlayed=1, kills=0, deaths=1, assists=0)
    assert s.winrate == 100

def test_winrate_float():
    s = Summoner(puuid="s1", name="test", tagline="euw", wins=2, gamesPlayed=3, kills=0, deaths=1, assists=0)
    assert round(s.winrate, 2) == 66.67

def test_winrate_edge():
    s = Summoner(puuid="s1", name="test", tagline="euw", wins=0, gamesPlayed=0, kills=0, deaths=1, assists=0)
    assert s.winrate == -1

def test_kda_normal():
    s = Summoner(puuid="s1", name="test", tagline="euw", wins=0, gamesPlayed=0, kills=10, deaths=5, assists=5)
    assert s.kda == 3

def test_kda_zero_deaths():
    s = Summoner(puuid="s1", name="test", tagline="euw", wins=0, gamesPlayed=0, kills=10, deaths=0, assists=5)
    assert s.kda == 15

def test_get_matches_pagination():
    dao = MockDAO()
    
    result = get_matches_service("test", "euw", 0, 2, dao)
    assert result.matches[0].match_id == 0
    assert result.matches[1].match_id == 1
    assert result.hasMore is True
    assert result.nextOffset == 2
    
    result = get_matches_service("test", "euw", 4, 2, dao)
    assert result.matches[0].match_id == 4
    assert result.hasMore is False
    assert result.nextOffset == 6

def test_get_summoner_service_found():
    dao = MockSummonerDAO()
    result = get_summoner_service("test", "euw", dao)
    
    assert result is not None
    assert result.name == "test"
    assert result.tagline == "euw"
    assert result.winrate == 50
    assert result.kda == 3

def test_get_summoner_service_not_found():
    dao = MockSummonerDAO()
    result = get_summoner_service("nope", "euw", dao)
    assert result is None
