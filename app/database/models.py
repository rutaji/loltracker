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
    Summoner_SummonerQueue = relationship("SummonerQueue", back_populates="SummonerQueue_Summoner", cascade="all, delete-orphan")

    @classmethod
    def create_default(cls,id:str,name:str=None):
        return Summoner(id=id,summoner_name=name,games_played=0,games_won=0,kill=0,death=0,assist=0)

class Match(Base):
    __tablename__ = "match"
    id = Column(String, primary_key=True, index=True)
    created = Column(Integer)
    ended = Column(Integer)
    queue_id = Column(Integer, ForeignKey("queues.queue_id"), nullable=True, index=True)
    patch=Column(String)

    Match_MatchParticipant = relationship("MatchParticipant", back_populates="MatchParticipant_Match")
    Match_Queue = relationship("Queue", back_populates="Queue_Match")
    Match_Ban = relationship("Ban", back_populates="Ban_Match")
    Match_ChampionMatchBan = relationship("ChampionMatchBan", back_populates="ChampionMatchBan_Match")

class MatchParticipant(Base):
    __tablename__ = "match_participant"
    summoner_id = Column(String, ForeignKey("summoner.id"), primary_key=True, index=True)
    match_id = Column(String, ForeignKey("match.id"), primary_key=True, index=True)
    kill = Column(Integer)
    assist = Column(Integer)
    death = Column(Integer)
    gold = Column(Integer)
    team = Column(Integer)
    position = Column(String)
    won = Column(Boolean)
    champion = Column(String,ForeignKey("champion.id"))
    item0 = Column(Integer, ForeignKey("item.item_id"), default=0, nullable=False)
    item1 = Column(Integer, ForeignKey("item.item_id"), default=0, nullable=False)
    item2 = Column(Integer, ForeignKey("item.item_id"), default=0, nullable=False)
    item3 = Column(Integer, ForeignKey("item.item_id"), default=0, nullable=False)
    item4 = Column(Integer, ForeignKey("item.item_id"), default=0, nullable=False)
    item5 = Column(Integer, ForeignKey("item.item_id"), default=0, nullable=False)
    item6 = Column(Integer, ForeignKey("item.item_id"), default=0, nullable=False)
    role_bound_item = Column(Integer, ForeignKey("item.item_id"), default=0, nullable=False)

    MatchParticipant_Summoner = relationship("Summoner", back_populates="Summoner_MatchParticipant")
    MatchParticipant_Match = relationship("Match", back_populates="Match_MatchParticipant")
    MatchParticipant_Champion = relationship("Champion", back_populates="Champion_MatchParticipant")



class ChampionStats(Base):
    __tablename__ = "champion_stats"
    champion_id = Column(String, ForeignKey("champion.id"), primary_key=True, index=True)
    patch = Column(String,primary_key=True, index=True)
    queue_id = Column(Integer, ForeignKey("queues.queue_id"), primary_key=True, index=True)
    games_played = Column(Integer)
    games_won = Column(Integer)
    games_banned = Column(Integer)
    kill = Column(Integer)
    assist = Column(Integer)
    death = Column(Integer)

    ChampionStats_Champion = relationship("Champion", back_populates="Champion_ChampionStats")
    ChampionStats_Queue = relationship("Queue")

class Champion(Base):
    __tablename__ = "champion"
    id = Column(String, primary_key=True, index=True)
    champion_name = Column(String, index=True,nullable=True)
    key=Column(Integer,index=True,unique=True,nullable=True)

    Champion_ChampionStats = relationship("ChampionStats", back_populates="ChampionStats_Champion")
    Champion_MatchParticipant = relationship("MatchParticipant", back_populates="MatchParticipant_Champion")
    Champion_SummonerChampion = relationship("SummonerChampion", back_populates="SummonerChampion_Champion")
    Champion_ChampionMatchBan = relationship("ChampionMatchBan", back_populates="ChampionMatchBan_Champion")

    @classmethod
    def create_default(cls, id: str,name:str = None):
        return Champion(id=id,champion_name=name,key=None)


class Queue(Base):
    __tablename__ = "queues"

    queue_id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    map = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    Queue_MatchesAnalyzed= relationship("MatchesAnalyzed", back_populates="MatchesAnalyzed_Queue")
    Queue_Match = relationship("Match", back_populates="Match_Queue")
    Queue_SummonerQueue = relationship("SummonerQueue", back_populates="SummonerQueue_Queue")
    Queue_SummonerChampion = relationship("SummonerChampion", back_populates="SummonerChampion_Queue")


class Item(Base):
    __tablename__ = "item"

    item_id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    name = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    @classmethod
    def create_default(cls, item_id: int):
        return Item(item_id=item_id, name=None, description=None)


class SummonerQueue(Base):
    __tablename__ = "summoner_queue"

    summoner_id = Column(String, ForeignKey("summoner.id"), primary_key=True, index=True)
    queue_id = Column(Integer, ForeignKey("queues.queue_id"), primary_key=True, index=True)
    tier = Column(String, nullable=True)
    rank = Column(String, nullable=True)
    league_points = Column(Integer, nullable=True)
    wins = Column(Integer, nullable=True)
    losses = Column(Integer, nullable=True)

    SummonerQueue_Summoner = relationship("Summoner", back_populates="Summoner_SummonerQueue")
    SummonerQueue_Queue = relationship("Queue", back_populates="Queue_SummonerQueue")

class SummonerChampion(Base):
    __tablename__ = "summoner_champion"
    summoner_id = Column(String,ForeignKey("summoner.id"), primary_key=True, index=True)
    champion_id = Column(String,ForeignKey("champion.id"), primary_key=True, index=True)
    queue_id = Column(Integer, ForeignKey("queues.queue_id"), primary_key=True, index=True)
    games_played = Column(Integer)
    games_won = Column(Integer)
    kill = Column(Integer)
    death = Column(Integer)
    assist = Column(Integer)

    SummonerChampion_Champion = relationship("Champion", back_populates="Champion_SummonerChampion")
    SummonerChampion_Summoner = relationship("Summoner", back_populates="Summoner_SummonerChampion")
    SummonerChampion_Queue = relationship("Queue", back_populates="Queue_SummonerChampion")

class MatchesAnalyzed(Base):
    __tablename__ = "matches_analyzed"
    patch = Column(String,primary_key=True, index=True)
    queue_id = Column(Integer, ForeignKey("queues.queue_id"), primary_key=True, index=True)
    count = Column(Integer)

    MatchesAnalyzed_Queue = relationship("Queue", back_populates="Queue_MatchesAnalyzed")

class Ban(Base):
    __tablename__ = "ban"
    match_id = Column(String, ForeignKey("match.id"), primary_key=True, index=True)
    team = Column(Integer,primary_key=True, index=True)
    ban_order = Column(Integer, primary_key=True, index=True)
    champion_key = Column(Integer, index=True)

    Ban_Match = relationship("Match", back_populates="Match_Ban")

class ChampionMatchBan(Base):
    __tablename__ = "champion_match_ban"
    match_id = Column(String, ForeignKey("match.id"), primary_key=True, index=True)
    champion_key = Column(Integer, ForeignKey("champion.key"), primary_key=True, index=True)

    ChampionMatchBan_Match = relationship("Match", back_populates="Match_ChampionMatchBan")
    ChampionMatchBan_Champion = relationship("Champion", back_populates="Champion_ChampionMatchBan")

