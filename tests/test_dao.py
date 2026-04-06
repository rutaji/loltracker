import os
import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()
from app.database.DAO import DAO
from app.database.models import Base, Summoner, Champion, Match, MatchParticipant

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
engine = create_engine(TEST_DATABASE_URL)
#Base.metadata.drop_all(bind=engine)
#Base.metadata.create_all(bind=engine)

@pytest.fixture()
def db_session():
    """Provides a fresh SQLAlchemy session for a test."""
    connection = engine.connect()
    transaction = connection.begin()

    session = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=connection
    )()
    try:
        yield session  # injects session into the test
         # undo changes after test
    finally:
        transaction.commit()
        session.close()
        #transaction.rollback()
        connection.close()



def test_add_summoner(db_session):
    dao = DAO(db_session)

    summoner = Summoner.create_default(id="testid123",name="testname#1234")
    dao.add_summoner(summoner)

    returned_summoner = dao.get_summoner_dao(summoner.id)
    assert summoner.id == returned_summoner.id
    assert returned_summoner.summoner_name == summoner.summoner_name
    assert  returned_summoner.games_played == 0

def test_add_champion(db_session):
    dao = DAO(db_session)

    id = "monkey_king"
    champion = Champion.create_default(id=id)

    dao.add_champion(champion)

    returned = dao.get_champion_dao(id)
    assert returned.id == id
    assert returned.champion_name is None

    name = "wukong"
    champion.champion_name =  name

    dao.add_champion(champion)

    returned_champion = dao.get_champion_dao(champion.id)
    assert returned_champion.champion_name == name

def test_add_match(db_session):
    dao = DAO(db_session)

    match = Match(id="1",created=12,ended=25,gametype="summoners rift",patch="1.27.2")
    participants=[
        MatchParticipant(summoner_id="1",match_id="1",kill=5,death=0,assist=2,gold=555,team=1,won=True,champion="Zed"),
        MatchParticipant(summoner_id="2", match_id="1", kill=3, death=2, assist=2, gold=555, team=2, won=False, champion="Lux"),

    ]

    dao.add_match(match,participants)

    pass

