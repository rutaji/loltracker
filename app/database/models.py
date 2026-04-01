from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, null
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Summoner(Base):
    __tablename__ = "Summoner"

    id = Column(String, primary_key=True, index=True)
    summoner_name = Column(String,nullable=True)
    games_played = Column(Integer)
    games_won = Column(Integer)

    participants = relationship("MatchParticipant", back_populates="summoner")
    champion = relationship("SummonerChampion", back_populates="summoner")

    @classmethod
    def create_default(cls,id:str,name:str=None):
        return Summoner(id=id,summoner_name=name,games_played=0,games_won=0)

class Match(Base):
    __tablename__ = "Match"
    id = Column(String, primary_key=True, index=True)
    created = Column(Integer)
    ended = Column(Integer)
    gametype=Column(String)
    patch=Column(String)

    participants = relationship("MatchParticipant", back_populates="match")

class MatchParticipant(Base):
    __tablename__ = "Match_Participant"
    summoner_id = Column(String, ForeignKey("Summoner.id"), primary_key=True, index=True)
    match_id = Column(String, ForeignKey("Match.id"), primary_key=True, index=True)
    kill = Column(Integer)
    assist = Column(Integer)
    death = Column(Integer)
    gold = Column(Integer)
    team = Column(Integer)
    won = Column(Boolean)
    champion = Column(String,ForeignKey("Champion.id"))

    summoner = relationship("Summoner", back_populates="participants")
    match = relationship("Match", back_populates="participants")
    champion_relation = relationship("Champion", back_populates="participants")



class ChampionStats(Base):
    __tablename__ = "Champion_Stats"
    champion_id = Column(String, ForeignKey("Champion.id"), primary_key=True, index=True)
    patch = Column(String,primary_key=True, index=True)
    gametype = Column(String, primary_key=True, index=True)
    games_played = Column(Integer)
    games_won = Column(Integer)
    games_banned = Column(Integer)
    kill = Column(Integer)
    assist = Column(Integer)
    death = Column(Integer)

    champion = relationship("Champion", back_populates="stats")

class Champion(Base):
    __tablename__ = "Champion"
    id = Column(String, primary_key=True, index=True)
    champion_name = Column(String, index=True,nullable=True)

    stats = relationship("ChampionStats", back_populates="champion")
    participants = relationship("MatchParticipant", back_populates="champion_relation")
    summoner = relationship("SummonerChampion", back_populates="champion")

    @classmethod
    def create_default(cls, id: str,name:str = None):
        return Champion(id=id,champion_name=name)

class SummonerChampion(Base):
    __tablename__ = "Summoner_Champion"
    summoner_id = Column(String,ForeignKey("Summoner.id"), primary_key=True, index=True)
    champion_id = Column(String,ForeignKey("Champion.id"), primary_key=True, index=True)
    games_played = Column(Integer)
    games_won = Column(Integer)

    champion = relationship("Champion", back_populates="summoner")
    summoner = relationship("Summoner", back_populates="champion")

class MatchesAnalyzed(Base):
    __tablename__ = "matches_Analyzed"
    patch = Column(String,primary_key=True, index=True)
    gametype = Column(String, primary_key=True, index=True)
    count = Column(Integer)


