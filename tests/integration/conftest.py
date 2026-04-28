import json
import os
from pathlib import Path
from typing import Any, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("RIOT_API_KEY", "test-key")
os.environ.setdefault("PSI_OTEL_ENABLED", "false")

from app.database.DAO import DAO
from app.database.models import (
    Base,
    Champion,
    ChampionStats,
    Match,
    MatchParticipant,
    MatchesAnalyzed,
    Queue,
    Summoner,
)
from app.endpoints import endpoints

from app.main import app


class StubRiotApiClient:
    def __init__(self, account_data: dict[str, Any], match_ids: list[str], match_infos: dict[str, Any]) -> None:
        self._account_data = account_data
        self._match_ids = match_ids
        self._match_infos = match_infos
        self.raise_on_summoner_lookup = False

        self.get_summoner_calls = 0
        self.get_match_ids_calls = 0
        self.get_match_info_calls = 0

    def get_summoner_by_riot_id(self, _name: str, _tagline: str) -> dict[str, Any]:
        self.get_summoner_calls += 1
        if self.raise_on_summoner_lookup:
            raise RuntimeError("Simulated upstream failure")
        return self._account_data

    def get_summoner_by_puuid(self, _puuid: str) -> dict[str, Any]:
        self.get_summoner_calls += 1
        if self.raise_on_summoner_lookup:
            raise RuntimeError("Simulated upstream failure")
        return self._account_data

    def get_match_ids_by_puuid(self, _puuid: str, start: int, count: int) -> list[str]:
        self.get_match_ids_calls += 1
        return self._match_ids[start:start + count]

    def get_match_info_by_match_id(self, match_id: str) -> dict[str, Any]:
        self.get_match_info_calls += 1
        return self._match_infos[match_id]


@pytest.fixture(scope="function")
def stub_api_client() -> StubRiotApiClient:
    fixtures_root = Path(__file__).resolve().parents[1] / "fixtures" / "riot_api"

    account_data = json.loads((fixtures_root / "summoner.json").read_text(encoding="utf-8"))
    match_ids = json.loads((fixtures_root / "match_ids.json").read_text(encoding="utf-8"))
    match_infos = json.loads((fixtures_root / "match_infos.json").read_text(encoding="utf-8"))

    return StubRiotApiClient(account_data=account_data, match_ids=match_ids, match_infos=match_infos)


@pytest.fixture(scope="function")
def test_database_url() -> str:
    return os.getenv("TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")


@pytest.fixture(scope="function")
def db_engine(test_database_url: str) -> Iterator[Any]:
    if test_database_url.startswith("sqlite"):
        sqlite_options: dict[str, Any] = {"connect_args": {"check_same_thread": False}}
        if test_database_url.endswith(":memory:"):
            sqlite_options["poolclass"] = StaticPool
        engine = create_engine(test_database_url, **sqlite_options)
    else:
        engine = create_engine(test_database_url)

    try:
        with engine.connect():
            pass
    except Exception:
        engine.dispose()
        if test_database_url.startswith("sqlite"):
            raise
        engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine: Any) -> Iterator[Session]:
    test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = test_session_local()

    yield session

    session.close()


@pytest.fixture(scope="function")
def dao(db_session: Session) -> DAO:
    return DAO(db_session)


@pytest.fixture(scope="function")
def app_client(monkeypatch: pytest.MonkeyPatch, dao: DAO, stub_api_client: StubRiotApiClient) -> Iterator[TestClient]:
    app.dependency_overrides[endpoints.get_dao] = lambda: dao

    with TestClient(app) as client:
        client.app.state.api_client = stub_api_client
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seed_cached_summoner_data(db_session: Session) -> dict[str, str]:
    summoner_id = "cached-puuid"
    db_session.add(Champion(id="Ahri", champion_name="Ahri"))
    db_session.add_all(
        [
            Queue(queue_id=420, map="Summoner's Rift", description="Ranked Solo", notes=None),
            Queue(queue_id=450, map="Howling Abyss", description="ARAM", notes=None),
            Queue(queue_id=1700, map="Rings of Wrath", description="Arena", notes=None),
        ]
    )
    db_session.add(
        Summoner(
            id=summoner_id,
            summoner_name="cached#euw",
            games_played=10,
            games_won=6,
            kill=48,
            death=20,
            assist=35,
        )
    )

    queue_ids = [420, 450, 1700]
    for index in range(3):
        match_id = f"CACHED_{index + 1}"
        db_session.add(
            Match(
                id=match_id,
                created=1712000000 + (index * 1000),
                ended=1712001200 + (index * 1000),
                queue_id=queue_ids[index],
                patch="14.5",
            )
        )
        db_session.add(
            MatchParticipant(
                summoner_id=summoner_id,
                match_id=match_id,
                kill=5 + index,
                death=2,
                assist=7,
                gold=12000,
                team=100,
                won=True,
                champion="Ahri",
            )
        )

    db_session.commit()

    return {"name": "cached", "tagline": "euw", "puuid": summoner_id}


@pytest.fixture(scope="function")
def seed_partial_matches_data(db_session: Session) -> dict[str, str]:
    summoner_id = "partial-puuid"
    db_session.add(Champion(id="Lux", champion_name="Lux"))
    db_session.add(Queue(queue_id=420, map="Summoner's Rift", description="Ranked Solo", notes=None))
    db_session.add(
        Summoner(
            id=summoner_id,
            summoner_name="partial#euw",
            games_played=2,
            games_won=1,
            kill=12,
            death=6,
            assist=18,
        )
    )

    for index in range(2):
        match_id = f"PARTIAL_{index + 1}"
        db_session.add(
            Match(
                id=match_id,
                created=1712100000 + (index * 1000),
                ended=1712101200 + (index * 1000),
                queue_id=420,
                patch="14.5",
            )
        )
        db_session.add(
            MatchParticipant(
                summoner_id=summoner_id,
                match_id=match_id,
                kill=3 + index,
                death=4,
                assist=9,
                gold=9800,
                team=200,
                won=False,
                champion="Lux",
            )
        )

    db_session.commit()

    return {"name": "partial", "tagline": "euw", "puuid": summoner_id}


@pytest.fixture(scope="function")
def seed_champion_stats_data(db_session: Session) -> dict[str, str]:
    champion_id = "Ahri"
    champion_name = "ahri"

    db_session.add(Champion(id=champion_id, champion_name=champion_name))
    db_session.add(Queue(queue_id=420, map="Summoner's Rift", description="Ranked Solo", notes=None))
    db_session.add(
        ChampionStats(
            champion_id=champion_id,
            patch="14.5",
            queue_id=420,
            games_played=20,
            games_won=12,
            games_banned=8,
            kill=110,
            assist=90,
            death=50,
        )
    )
    db_session.add(
        ChampionStats(
            champion_id=champion_id,
            patch="14.4",
            queue_id=420,
            games_played=15,
            games_won=8,
            games_banned=4,
            kill=80,
            assist=70,
            death=45,
        )
    )
    db_session.add(MatchesAnalyzed(patch="14.5", queue_id=420, count=200))
    db_session.add(MatchesAnalyzed(patch="14.4", queue_id=420, count=150))

    db_session.commit()

    return {"name": champion_name}
