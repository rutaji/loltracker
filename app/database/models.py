from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, null
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Summoner(Base):
    __tablename__ = "summoner"

    id = Column(String, primary_key=True, index=True)
    summoner_name = Column(String,nullable=True)
    games_played = Column(Integer)
    games_won = Column(Integer)
    kill=Column(Integer)
    death=Column(Integer)
    assist=Column(Integer)

    Summoner_MatchParticipant = relationship("MatchParticipant", back_populates="MatchParticipant_Summoner")
    Summoner_SummonerChampion = relationship("SummonerChampion", back_populates="SummonerChampion_Summoner")

    @classmethod
    def create_default(cls,id:str,name:str=None):
        return Summoner(id=id,summoner_name=name,games_played=0,games_won=0,kill=0,death=0,assist=0)

class Match(Base):
    __tablename__ = "match"
    id = Column(String, primary_key=True, index=True)
    created = Column(Integer)
    ended = Column(Integer)
    gametype=Column(String)
    patch=Column(String)

    Match_MatchParticipant = relationship("MatchParticipant", back_populates="MatchParticipant_Match")

class MatchParticipant(Base):
    __tablename__ = "match_participant"
    summoner_id = Column(String, ForeignKey("summoner.id"), primary_key=True, index=True)
    match_id = Column(String, ForeignKey("match.id"), primary_key=True, index=True)
    kill = Column(Integer)
    assist = Column(Integer)
    death = Column(Integer)
    gold = Column(Integer)
    team = Column(Integer)
    won = Column(Boolean)
    champion = Column(String,ForeignKey("champion.id"))

    MatchParticipant_Summoner = relationship("Summoner", back_populates="Summoner_MatchParticipant")
    MatchParticipant_Match = relationship("Match", back_populates="Match_MatchParticipant")
    MatchParticipant_Champion = relationship("Champion", back_populates="Champion_MatchParticipant")



class ChampionStats(Base):
    __tablename__ = "champion_stats"
    champion_id = Column(String, ForeignKey("champion.id"), primary_key=True, index=True)
    patch = Column(String,primary_key=True, index=True)
    gametype = Column(String, primary_key=True, index=True)
    games_played = Column(Integer)
    games_won = Column(Integer)
    games_banned = Column(Integer)
    kill = Column(Integer)
    assist = Column(Integer)
    death = Column(Integer)

    ChampionStats_Champion = relationship("Champion", back_populates="Champion_ChampionStats")

class Champion(Base):
    __tablename__ = "champion"
    id = Column(String, primary_key=True, index=True)
    champion_name = Column(String, index=True,nullable=True)

    Champion_ChampionStats = relationship("ChampionStats", back_populates="ChampionStats_Champion")
    Champion_MatchParticipant = relationship("MatchParticipant", back_populates="MatchParticipant_Champion")
    Champion_SummonerChampion = relationship("SummonerChampion", back_populates="SummonerChampion_Champion")

    @classmethod
    def create_default(cls, id: str,name:str = None):
        return Champion(id=id,champion_name=name)


class Queue(Base):
    __tablename__ = "queues"

    queue_id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    map = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

class SummonerChampion(Base):
    __tablename__ = "summoner_champion"
    summoner_id = Column(String,ForeignKey("summoner.id"), primary_key=True, index=True)
    champion_id = Column(String,ForeignKey("champion.id"), primary_key=True, index=True)
    games_played = Column(Integer)
    games_won = Column(Integer)

    SummonerChampion_Champion = relationship("Champion", back_populates="Champion_SummonerChampion")
    SummonerChampion_Summoner = relationship("Summoner", back_populates="Summoner_SummonerChampion")

class MatchesAnalyzed(Base):
    __tablename__ = "matches_analyzed"
    patch = Column(String,primary_key=True, index=True)
    gametype = Column(String, primary_key=True, index=True)
    count = Column(Integer)


