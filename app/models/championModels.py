from pydantic import BaseModel, Field
from typing import List

class ChampionStats(BaseModel):
    version: str
    queueId: int = Field(default=0, exclude=True)
    queueDescription: str
    wins: int
    gamesPlayed: int
    kills: int
    deaths: int
    assists: int
    banned: int
    matchesAnalyzed: int

    def __str__(self):
        return f" ChampionStats version={self.version} queueDescription={self.queueDescription} wins={self.wins}"
    
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
        return (self.banned/self.matchesAnalyzed)*100 if self.matchesAnalyzed else 0
    
    @property
    def pickrate(self):
        return (self.gamesPlayed/self.matchesAnalyzed)*100 if self.matchesAnalyzed else 0


class Champion(BaseModel):
    name: str
    championStats: List[ChampionStats]
