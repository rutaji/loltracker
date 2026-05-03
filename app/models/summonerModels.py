from pydantic import BaseModel, Field
from datetime import datetime
from typing import List

class MatchParticipant(BaseModel):
    puuid: str
    name: str
    tagline: str
    kills: int
    deaths: int
    assists: int
    gold: int
    team: int
    position: str = ""
    champion: str
    championImagePath: str | None = None
    won: bool

class Match(BaseModel):
    match_id: str | int
    start: datetime
    end: datetime
    version: str
    queueId: int = Field(default=0, exclude=True)
    queueDescription: str
    participants: List[MatchParticipant]

class Ban(BaseModel):
    match_id: str
    team: int
    champion: str

class BanParsed(BaseModel):
    match_id: str
    team: int
    ban_order: int
    champion_key: int


class Summoner(BaseModel):
    puuid: str
    name: str
    tagline: str
    wins: int
    gamesPlayed: int
    kills: int
    deaths: int
    assists: int
    divisions: List["SummonerDivision"] = Field(default_factory=list)

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

class SummonerChampion(BaseModel):
    champion_name: str
    champion_id: str
    games_played: int
    wins: int

    @property
    def winrate(self):
        return (self.wins / self.games_played) * 100 if self.games_played else -1


class SummonerDivision(BaseModel):
    queueId: int = Field(default=0, exclude=True)
    queueDescription: str
    tier: str
    rank: str
    leaguePoints: int
    wins: int
    losses: int

    @property
    def winrate(self):
        total_games = self.wins + self.losses
        return (self.wins / total_games) * 100 if total_games else -1

    @property
    def displayTierRank(self):
        tier_label = (self.tier or "").replace("_", " ").title()
        rank_label = (self.rank or "").strip()
        return f"{tier_label} {rank_label}".strip()
