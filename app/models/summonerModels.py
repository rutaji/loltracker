from pydantic import BaseModel
from datetime import datetime
from typing import List

class MatchParticipant(BaseModel):
    name: str
    tagline: str
    kills: int
    deaths: int
    assists: int
    gold: int
    team: int
    champion: str
    won: bool

class Match(BaseModel):
    match_id: str | int
    start: datetime
    end: datetime
    version: str
    mode: str
    participants: List[MatchParticipant]

class Summoner(BaseModel):
    name: str
    tagline: str
    wins: int
    gamesPlayed: int
    kills: int
    deaths: int
    assists: int

    @property
    def losses(self):
        return self.gamesPlayed-self.wins
    
    @property
    def winrate(self):
        return (self.wins/self.gamesPlayed)*100 if self.gamesPlayed else -1
    
    @property
    def kda(self):
        if self.deaths==0:
            return (self.kills+self.assists)/1

        return (self.kills + self.assists)/self.deaths

class MatchPage(BaseModel):
    matches: List[Match]
    hasMore: bool
    nextOffset: int

class SummonerData(BaseModel):
    summoner: Summoner
    matchPage: MatchPage
