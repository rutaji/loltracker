from pydantic import BaseModel
from typing import List

class ChampionStats(BaseModel):
    version: str
    gamemode: str
    wins: int
    losses: int
    kills: int
    deaths: int
    assists: int
    banned: int
    matchesAnalyzed: int
    rankedMatchesAnalyzed: int

    @property
    def gamesPlayed(self):
        return self.wins + self.losses
    
    @property
    def winrate(self):
        return (self.wins/self.gamesPlayed)*100 if self.gamesPlayed else -1
    
    @property
    def kda(self):
        if self.deaths==0:
            return (self.kills+self.assists)/1

        return (self.kills + self.assists)/self.deaths
    
    @property
    def banrate(self):
        return (self.banned/self.rankedMatchesAnalyzed)*100 if self.rankedMatchesAnalyzed else 0
    
    @property
    def pickrate(self):
        return (self.gamesPlayed/self.matchesAnalyzed)*100 if self.matchesAnalyzed else 0


class Champion(BaseModel):
    name: str
    championStats: List[ChampionStats]
