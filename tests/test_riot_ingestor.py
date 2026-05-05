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


def test_ingestor_handles_api_failure_gracefully(monkeypatch):
    """Verify ingestor handles API call failures gracefully."""
    class FailingApiClient:
        def get_league_entries(self, queue, tier, division):
            raise Exception("API is down")

    app = SimpleNamespace()
    app.state = SimpleNamespace(api_client=FailingApiClient())

    fake_dao = FakeDAO()
    monkeypatch.setattr("app.services.riot_ingestor.DAO.get_dao", lambda: fake_dao)

    ingestor = RiotIngestor(app, interval_seconds=30)
    # Should not raise exception
    ingestor._iteration_sync()


def test_ingestor_handles_empty_league_entries(monkeypatch):
    """Verify ingestor handles empty league entries gracefully."""
    class EmptyApiClient:
        def get_league_entries(self, queue, tier, division):
            return []

    app = SimpleNamespace()
    app.state = SimpleNamespace(api_client=EmptyApiClient())

    fake_dao = FakeDAO()
    monkeypatch.setattr("app.services.riot_ingestor.DAO.get_dao", lambda: fake_dao)
    monkeypatch.setattr(
        "app.services.riot_ingestor.summonerServices.ingest_matches_from_puuid_service",
        MagicMock(),
    )

    ingestor = RiotIngestor(app, interval_seconds=30)
    # Should not raise exception and should not call ingest service
    ingestor._iteration_sync()


def test_ingestor_handles_ingest_service_failure(monkeypatch):
    """Verify ingestor handles failures in ingest_matches_from_puuid_service."""
    fake_dao = FakeDAO()
    monkeypatch.setattr("app.services.riot_ingestor.DAO.get_dao", lambda: fake_dao)

    def failing_ingest(*args, **kwargs):
        raise Exception("Ingest service failed")

    monkeypatch.setattr(
        "app.services.riot_ingestor.summonerServices.ingest_matches_from_puuid_service",
        failing_ingest,
    )

    app = SimpleNamespace()
    app.state = SimpleNamespace(api_client=FakeApiClient())
    monkeypatch.setattr("random.sample", lambda seq, k: seq[:k])

    ingestor = RiotIngestor(app, interval_seconds=30)
    # Should not raise exception even if ingest service fails
    ingestor._iteration_sync()


def test_ingestor_closes_dao_after_iteration(monkeypatch):
    """Verify ingestor closes DAO after iteration completes."""
    fake_dao = FakeDAO()
    monkeypatch.setattr("app.services.riot_ingestor.DAO.get_dao", lambda: fake_dao)

    app = SimpleNamespace()
    app.state = SimpleNamespace(api_client=FakeApiClient())
    monkeypatch.setattr("random.sample", lambda seq, k: seq[:k])

    # Mock close to track if it's called
    close_called = []
    original_close = fake_dao.close

    def tracked_close():
        close_called.append(True)
        original_close()

    fake_dao.close = tracked_close

    ingestor = RiotIngestor(app, interval_seconds=30)
    ingestor._iteration_sync()

    # Verify DAO close was called
    assert close_called, "DAO should be closed after iteration"


def test_ingestor_closes_dao_even_on_error(monkeypatch):
    """Verify ingestor closes DAO even when an error occurs."""
    fake_dao = FakeDAO()
    monkeypatch.setattr("app.services.riot_ingestor.DAO.get_dao", lambda: fake_dao)

    close_called = []

    def tracked_close():
        close_called.append(True)

    fake_dao.close = tracked_close

    class FailingApiClient:
        def get_league_entries(self, queue, tier, division):
            raise Exception("API error")

    app = SimpleNamespace()
    app.state = SimpleNamespace(api_client=FailingApiClient())

    ingestor = RiotIngestor(app, interval_seconds=30)
    ingestor._iteration_sync()

    # Verify DAO close was called even after error
    assert close_called, "DAO should be closed even when error occurs"


def test_ingestor_start_and_stop(monkeypatch):
    """Verify ingestor can start and stop scheduler."""
    app = SimpleNamespace()
    app.state = SimpleNamespace(api_client=FakeApiClient())

    ingestor = RiotIngestor(app, interval_seconds=10)
    assert ingestor.scheduler is not None
    assert not ingestor.scheduler.running

    ingestor.start()
    assert ingestor.scheduler.running

    ingestor.stop()
    assert not ingestor.scheduler.running


def test_ingestor_stop_handles_shutdown_error(monkeypatch):
    """Verify ingestor handles errors when stopping scheduler."""
    app = SimpleNamespace()
    app.state = SimpleNamespace(api_client=FakeApiClient())

    ingestor = RiotIngestor(app, interval_seconds=10)
    ingestor.start()

    # Mock scheduler.shutdown to raise exception
    def failing_shutdown(*args, **kwargs):
        raise Exception("Scheduler shutdown failed")

    original_shutdown = ingestor.scheduler.shutdown
    ingestor.scheduler.shutdown = failing_shutdown

    # Should not raise exception
    ingestor.stop()


def test_ingestor_sample_tier_by_gaussian(monkeypatch):
    """Verify _sample_tier_by_gaussian returns valid tiers."""
    from app.services.riot_ingestor import TIERS

    app = SimpleNamespace()
    ingestor = RiotIngestor(app, interval_seconds=30)

    for _ in range(20):
        tier = ingestor._sample_tier_by_gaussian()
        assert tier in TIERS, f"Sampled tier {tier} should be in TIERS list"


def test_ingestor_sample_tier_distribution(monkeypatch):
    """Verify _sample_tier_by_gaussian produces a distribution."""
    app = SimpleNamespace()
    ingestor = RiotIngestor(app, interval_seconds=30)

    # Sample many times
    samples = [ingestor._sample_tier_by_gaussian() for _ in range(100)]

    # All samples should be valid tiers
    from app.services.riot_ingestor import TIERS
    assert all(t in TIERS for t in samples)

    # Should have some variety (not just one tier)
    unique_tiers = set(samples)
    assert len(unique_tiers) > 1, "Should sample multiple different tiers"


def test_start_ingestor_creates_and_starts(monkeypatch):
    """Verify start_ingestor creates and starts ingestor if not exists."""
    from app.services.riot_ingestor import start_ingestor

    app = SimpleNamespace()
    app.state = SimpleNamespace()

    start_ingestor(app, interval_seconds=15)

    assert hasattr(app.state, "riot_ingestor"), "Ingestor should be attached to app.state"
    assert app.state.riot_ingestor.scheduler.running, "Scheduler should be running"

    # Cleanup
    app.state.riot_ingestor.stop()


def test_start_ingestor_does_not_recreate(monkeypatch):
    """Verify start_ingestor does not recreate ingestor if already exists."""
    from app.services.riot_ingestor import start_ingestor

    app = SimpleNamespace()
    first_ingestor = RiotIngestor(app, interval_seconds=20)
    app.state = SimpleNamespace(riot_ingestor=first_ingestor)
    first_ingestor.start()

    # Call start_ingestor again
    start_ingestor(app, interval_seconds=30)

    # Should be the same ingestor
    assert app.state.riot_ingestor is first_ingestor, "Should not recreate ingestor"

    # Cleanup
    first_ingestor.stop()


def test_stop_ingestor(monkeypatch):
    """Verify stop_ingestor stops and removes ingestor."""
    from app.services.riot_ingestor import start_ingestor, stop_ingestor

    app = SimpleNamespace()
    app.state = SimpleNamespace()

    start_ingestor(app, interval_seconds=15)
    assert hasattr(app.state, "riot_ingestor")

    stop_ingestor(app)

    assert not hasattr(app.state, "riot_ingestor"), "Ingestor should be removed from app.state"


def test_stop_ingestor_when_none_exists(monkeypatch):
    """Verify stop_ingestor handles case when no ingestor exists."""
    from app.services.riot_ingestor import stop_ingestor

    app = SimpleNamespace()
    app.state = SimpleNamespace()

    # Should not raise exception
    stop_ingestor(app)
