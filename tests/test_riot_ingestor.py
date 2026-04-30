import random
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.services.riot_ingestor import RiotIngestor


class FakeApiClient:
    """Simulates Riot API client for ingestor tests."""

    def __init__(self):
        self.calls = []

    def get_league_entries(self, queue, tier, division):
        """Return league entries with puuid (v4 endpoint returns puuid directly)."""
        self.calls.append(("get_league_entries", queue, tier, division))
        return [
            {
                "puuid": "valid-puuid-1",
                "leagueId": "league-1",
                "tier": tier,
                "rank": "I",
                "leaguePoints": 100,
            },
            {
                "puuid": "valid-puuid-2",
                "leagueId": "league-2",
                "tier": tier,
                "rank": "II",
                "leaguePoints": 50,
            },
            {
                "puuid": "valid-puuid-3",
                "leagueId": "league-3",
                "tier": tier,
                "rank": "III",
                "leaguePoints": 25,
            },
        ]

    def get_summoner_by_puuid(self, puuid):
        """Fetch summoner account data by PUUID."""
        self.calls.append(("get_summoner_by_puuid", puuid))
        return {"puuid": puuid, "gameName": "TestPlayer", "tagLine": "NA1"}

    def get_match_ids_by_puuid(self, puuid, start=0, count=20):
        """Return empty match list for testing."""
        self.calls.append(("get_match_ids_by_puuid", puuid, start, count))
        return []


class FakeDAO:
    """Simulates database DAO for ingestor tests."""

    def __init__(self):
        self.summoners_added = []

    def add_summoner(self, summoner):
        self.summoners_added.append(summoner)

    def get_match_ids_for_summoner(self, summoner_name):
        return set()

    def add_match(self, match):
        pass

    def match_exist(self, match_id):
        return False

    def add_ban(self, bans):
        pass

    def close(self):
        pass


def test_ingestor_uses_puuid_from_league_entries(monkeypatch):
    """Verify ingestor uses puuid directly from league entries response."""
    # Patch DAO.get_dao() to return our fake DAO
    fake_dao = FakeDAO()
    monkeypatch.setattr("app.services.riot_ingestor.DAO.get_dao", lambda: fake_dao)

    # Patch summonerServices to avoid complex setup
    mock_ingest_service = MagicMock()
    mock_ingest_service.return_value = SimpleNamespace(
        inserted_count=0, failed_count=0, summoner=None
    )
    monkeypatch.setattr(
        "app.services.riot_ingestor.summonerServices.ingest_matches_from_puuid_service",
        mock_ingest_service,
    )

    # Seed random sample to ensure we get predictable entries
    monkeypatch.setattr("random.sample", lambda seq, k: seq[:k])

    # Create app with fake state
    app = SimpleNamespace()
    app.state = SimpleNamespace(api_client=FakeApiClient())

    # Create and run ingestor iteration
    ingestor = RiotIngestor(app, interval_seconds=30)
    ingestor._iteration_sync()

    # Verify: ingestor should have called get_league_entries
    api_calls = app.state.api_client.calls
    league_calls = [c for c in api_calls if c[0] == "get_league_entries"]
    assert len(league_calls) == 1, "Should fetch league entries once"

    # Verify: ingestor should pass PUUIDs from league entries to match ingest service
    # The mock was called with (request, puuid, dao)
    assert mock_ingest_service.call_count >= 1, "Should call ingest service with PUUIDs"
    
    # Verify the PUUIDs passed match those from league entries
    for call in mock_ingest_service.call_args_list:
        args, kwargs = call
        puuid = args[1]  # second argument is puuid
        assert puuid.startswith("valid-puuid-"), f"Should use PUUIDs from league entries, got {puuid}"


def test_ingestor_skips_entries_without_puuid():
    """Verify ingestor skips league entries that lack puuid."""

    class BadApiClient:
        def get_league_entries(self, queue, tier, division):
            return [
                {
                    "leagueId": "league-1",
                    "tier": tier,
                    "rank": "I",
                },  # Missing puuid
            ]

        def get_match_ids_by_puuid(self, puuid, start=0, count=20):
            raise AssertionError("Should not be called for entries without puuid")

    app = SimpleNamespace()
    app.state = SimpleNamespace(api_client=BadApiClient())

    fake_dao = FakeDAO()

    # Patch DAO and service
    with patch("app.services.riot_ingestor.DAO.get_dao", return_value=fake_dao), patch(
        "app.services.riot_ingestor.summonerServices.ingest_matches_from_puuid_service"
    ) as mock_ingest:
        ingestor = RiotIngestor(app, interval_seconds=30)
        ingestor._iteration_sync()

        # Verify: ingest service should NOT have been called
        assert (
            mock_ingest.call_count == 0
        ), "Should skip entries without puuid and not call ingest service"
