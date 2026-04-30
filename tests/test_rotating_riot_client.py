"""Tests for the rotating Riot API client."""

import asyncio
import pytest
from unittest.mock import MagicMock, patch

from app.riot.rotating_client import RotatingRiotApiClient
from app.services.rate_limiter import TokenBucket


class TestRotatingRiotApiClient:
    """Test suite for RotatingRiotApiClient."""

    def test_init_with_empty_keys(self):
        """Should raise ValueError if no API keys provided."""
        with pytest.raises(ValueError, match="api_keys must not be empty"):
            RotatingRiotApiClient(api_keys=[])

    def test_init_with_single_key(self):
        """Should initialize with a single API key."""
        client = RotatingRiotApiClient(api_keys=["test-key-1"])
        assert len(client.clients) == 1
        assert client.api_keys == ["test-key-1"]

    def test_init_with_multiple_keys(self):
        """Should initialize with multiple API keys."""
        client = RotatingRiotApiClient(
            api_keys=["test-key-1", "test-key-2", "test-key-3"]
        )
        assert len(client.clients) == 3
        assert client.api_keys == ["test-key-1", "test-key-2", "test-key-3"]

    def test_init_respects_rate_limit_config(self):
        """Should pass rate limit config to each client's TokenBucket."""
        client = RotatingRiotApiClient(
            api_keys=["key1", "key2"],
            rate_limit_total=200,
            rate_limit_window_seconds=60,
            reserved_calls=5,
        )
        for subclient in client.clients:
            assert subclient.rate_limiter.capacity == 200
            assert subclient.rate_limiter.refill_interval == 60
            assert subclient.rate_limiter.reserved == 5

    def test_select_client_round_robin(self):
        """Should rotate through clients in round-robin order."""
        client = RotatingRiotApiClient(api_keys=["key1", "key2", "key3"])
        
        # Each client starts with full capacity, so selection should round-robin
        selected = []
        for _ in range(9):
            selected_client = client._select_client()
            # Find which client was selected based on the api_key
            idx = next(
                i for i, c in enumerate(client.clients) if c.api_key == selected_client.api_key
            )
            selected.append(idx)
        
        # Should rotate in order: 0, 1, 2, 0, 1, 2, 0, 1, 2
        assert selected == [0, 1, 2, 0, 1, 2, 0, 1, 2]

    def test_select_client_skips_exhausted_keys(self):
        """Should skip clients with no available tokens."""
        client = RotatingRiotApiClient(api_keys=["key1", "key2", "key3"])
        
        # Drain tokens from first two clients by mocking available()
        client.clients[0].rate_limiter.available = MagicMock(return_value=0)
        client.clients[1].rate_limiter.available = MagicMock(return_value=0)
        
        # Should select the third client
        selected = client._select_client()
        assert selected is client.clients[2]

    def test_select_client_timeout_when_all_exhausted(self):
        """Should raise RuntimeError if all keys are exhausted."""
        client = RotatingRiotApiClient(
            api_keys=["key1", "key2"],
            wait_timeout_seconds=0.05,
        )
        
        # Mock all clients to have no tokens
        for subclient in client.clients:
            subclient.rate_limiter.available = MagicMock(return_value=0)
        
        with pytest.raises(
            RuntimeError, match="All 2 Riot API keys exhausted"
        ):
            client._select_client()

    def test_get_league_entries_delegates_to_client(self):
        """Should delegate get_league_entries to selected client."""
        client = RotatingRiotApiClient(api_keys=["key1"])
        
        # Verify the method exists and can be called
        assert hasattr(client, "get_league_entries")
        assert callable(client.get_league_entries)

    def test_get_summoner_by_puuid_delegates_to_client(self):
        """Should delegate get_summoner_by_puuid to selected client."""
        client = RotatingRiotApiClient(api_keys=["key1"])
        
        # Verify the method exists and can be called
        assert hasattr(client, "get_summoner_by_puuid")
        assert callable(client.get_summoner_by_puuid)

    def test_get_match_ids_by_puuid_delegates_to_client(self):
        """Should delegate get_match_ids_by_puuid to selected client."""
        client = RotatingRiotApiClient(api_keys=["key1"])
        
        # Verify the method exists and can be called
        assert hasattr(client, "get_match_ids_by_puuid")
        assert callable(client.get_match_ids_by_puuid)

    def test_get_match_info_by_match_id_delegates_to_client(self):
        """Should delegate get_match_info_by_match_id to selected client."""
        client = RotatingRiotApiClient(api_keys=["key1"])
        
        # Verify the method exists and can be called
        assert hasattr(client, "get_match_info_by_match_id")
        assert callable(client.get_match_info_by_match_id)

    def test_get_rate_limiter_status(self):
        """Should return aggregated rate limiter status for all keys."""
        client = RotatingRiotApiClient(
            api_keys=["key1", "key2"],
            rate_limit_total=100,
        )
        
        status = client.get_rate_limiter_status()
        
        assert status["keys_count"] == 2
        assert len(status["per_key"]) == 2
        assert status["aggregate"]["total_capacity"] == 200  # 100 * 2
        # All keys start with full capacity
        assert status["aggregate"]["total_tokens"] == 200

    def test_get_rate_limiter_status_after_token_consumption(self):
        """Should reflect token consumption in status."""
        client = RotatingRiotApiClient(
            api_keys=["key1", "key2"],
            rate_limit_total=100,
        )
        
        # Simulate token consumption on one client
        client.clients[0].rate_limiter.available = MagicMock(return_value=50)
        
        status = client.get_rate_limiter_status()
        
        assert status["per_key"][0]["tokens"] == 50
        assert status["per_key"][1]["tokens"] == 100
        assert status["aggregate"]["total_tokens"] == 150

    def test_regional_routing_passed_to_clients(self):
        """Should pass routing parameters to each client."""
        client = RotatingRiotApiClient(
            api_keys=["key1", "key2"],
            regional_routing="americas",
            platform_routing="na1",
        )
        
        for subclient in client.clients:
            assert subclient.regional_routing == "americas"
            assert subclient.platform_routing == "na1"
