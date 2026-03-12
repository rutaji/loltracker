from sqlalchemy import Column, Integer, String
from app.database.database import Base

class User(Base):
    __tablename__ = "Summoner"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    games_played = Column(Integer)
    games_won = Column(Integer)