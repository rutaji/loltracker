import os
import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()
from app.database.DAO import DAO
from app.database.models import Base, Summoner, Champion

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
engine = create_engine(TEST_DATABASE_URL)
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

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
        session.close()
        transaction.rollback()
        connection.close()



def test_add_summoner(db_session):
    dao = DAO(db_session)

    summoner = Summoner.create_default(id="testid123",name="testname#1234")
    dao.add_summoner(summoner)

    returned_summoner = dao.get_summoner(summoner.id)
    assert summoner.id == returned_summoner.id
    assert returned_summoner.summoner_name == summoner.summoner_name
    assert  returned_summoner.games_played == 0

def test_add_champion(db_session):
    dao = DAO(db_session)

    id = "monkey_king"
    champion = Champion.create_default(id=id)

    dao.add_champion(champion)

    returned = dao.get_champion(id)
    assert returned.id == id
    assert returned.champion_name is None

    name = "wukong"
    champion.champion_name =  name

    dao.add_champion(champion)

    returned_champion = dao.get_champion(champion.id)
    assert returned_champion.champion_name == name

