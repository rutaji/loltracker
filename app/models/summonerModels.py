from pydantic import BaseModel
from datetime import datetime
from typing import List

class MatchParticipant(BaseModel):
    name: str
    kills: int
    deaths: int
    assists: int
    gold: int
    team: int
    champion: str
    won: bool

class Match(BaseModel):
    match_id: int
    start: datetime
    end: datetime
    version: str
    mode: str
    participants: List[MatchParticipant]

class Summoner(BaseModel):
    name: str
    wins: int
    losses: int
    kills: int
    deaths: int
    assists: int
    
    @property
    def winrate(self):
        games=self.wins + self.losses
        return (self.wins/games)*100 if games else -1
    
    @property
    def kda(self):
        if self.deaths==0:
            return (self.kills+self.assists)/1

        return (self.kills + self.assists)/self.deaths

class MatchPage(BaseModel):
    matches: List[Match]
    hasMore: bool
    nextOffset: int