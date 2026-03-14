from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Summoner(Base):
    __tablename__ = "Summoner"

    id = Column(String, primary_key=True, index=True)
    summoner_name = Column(String)
    games_played = Column(Integer)
    games_won = Column(Integer)

class Match(Base):
    __tablename__ = "Match"
    id = Column(String, primary_key=True, index=True)
    created = Column(Integer)
    ended = Column(Integer)
    gametype=Column(String)
    patch=Column(String)

class MatchParticipant(Base):
    __tablename__ = "Match_Participant"
    summoner_id = Column(String, primary_key=True, index=True)
    match_id = Column(String, primary_key=True, index=True)
    kill = Column(Integer)
    assist = Column(Integer)
    death = Column(Integer)
    gold = Column(Integer)
    team = Column(Integer)
    won = Column(Integer)
    championship = Column(String)

class ChampionStats(Base):
    __tablename__ = "Champion_Stats"
    champion_name = Column(String, primary_key=True, index=True)
    patch = Column(String,primary_key=True, index=True)
    gametype = Column(String, primary_key=True, index=True)
    games_played = Column(Integer)
    games_won = Column(Integer)
    games_picked = Column(Integer)
    games_banned = Column(Integer)
    assists = Column(Integer)
    kill = Column(Integer)
    assist = Column(Integer)
    death = Column(Integer)

class Champion(Base):
    __tablename__ = "Champion"
    id = Column(String)
    champion_name = Column(String, primary_key=True, index=True)

class SummonerChampion(Base):
    __tablename__ = "Summoner_Champion"
    summoner_id = Column(String, primary_key=True, index=True)
    champion_name = Column(String, primary_key=True, index=True)
    games_played = Column(Integer)
    games_won = Column(Integer)


