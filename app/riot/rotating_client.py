import logging
import time
from typing import List, Optional

import httpx

from app.riot.riotApiClient import RiotApiClient
from app.services.rate_limiter import TokenBucket

LOGGER = logging.getLogger(__name__)


class RotatingRiotApiClient:
    def __init__(
        self,
        api_keys: List[str],
        regional_routing: str = "europe",
        platform_routing: str = "euw1",
        rate_limit_total: int = 100,
        rate_limit_window_seconds: int = 120,
        reserved_calls: int = 0,
        wait_timeout_seconds: float = 5.0,
    ):
        if not api_keys:
            raise ValueError("api_keys must not be empty")

        self.api_keys = api_keys
        self.key_index = 0
        self.wait_timeout_seconds = wait_timeout_seconds
        self.clients: List[RiotApiClient] = []
        self._disabled_client_indexes: set[int] = set()

        for api_key in api_keys:
            rate_limiter = TokenBucket(
                capacity=rate_limit_total,
                refill_interval_seconds=rate_limit_window_seconds,
                reserved=reserved_calls,
            )
            client = RiotApiClient(
                api_key=api_key,
                regional_routing=regional_routing,
                platform_routing=platform_routing,
                rate_limiter=rate_limiter,
            )
            self.clients.append(client)

        LOGGER.info(
            "RotatingRiotApiClient initialized with %d keys, "
            "rate limit: %d/%ds per key",
            len(self.api_keys),
            rate_limit_total,
            rate_limit_window_seconds,
        )

    def _is_disabled(self, client_index: int) -> bool:
        return client_index in self._disabled_client_indexes

    def _mark_disabled(self, client_index: int, reason: str) -> None:
        if client_index not in self._disabled_client_indexes:
            self._disabled_client_indexes.add(client_index)
            LOGGER.warning("Disabling Riot API key #%d: %s", client_index + 1, reason)

    def _is_decrypt_error(self, exc: httpx.HTTPStatusError) -> bool:
        response = getattr(exc, "response", None)
        status = getattr(response, "status_code", None)
        if status != 400:
            return False
        body = getattr(response, "text", "") or ""
        return "decrypt" in body.lower()

    def _select_client_with_index(self) -> tuple[int, RiotApiClient]:
        num_clients = len(self.clients)
        start_time = time.time()
        
        while True:
            # Try to find a client with available tokens in round-robin order
            for _ in range(num_clients):
                key_index = self.key_index
                self.key_index = (self.key_index + 1) % num_clients

                if self._is_disabled(key_index):
                    LOGGER.debug("Skipping key #%d (disabled)", key_index + 1)
                    continue

                client = self.clients[key_index]
                
                # Check if this client has available tokens
                available = client.rate_limiter.available()
                if available > 0:
                    LOGGER.debug(
                        "Selected key #%d (available tokens: %d)",
                        key_index + 1,
                        available,
                    )
                    return key_index, client
                else:
                    LOGGER.debug(
                        "Skipping key #%d (exhausted, available: %d)",
                        key_index + 1,
                        available,
                    )
            
            # All clients exhausted; check if we should wait
            elapsed = time.time() - start_time
            if elapsed >= self.wait_timeout_seconds:
                raise RuntimeError(
                    f"All {num_clients} Riot API keys exhausted after {elapsed:.1f}s; "
                    f"increase rate limit or reduce request frequency"
                )
            
            # Wait briefly before retrying
            time.sleep(0.1)

    def _select_client(self) -> RiotApiClient:
        _, client = self._select_client_with_index()
        return client

    def _with_client_retry(self, operation_name: str, call) -> object:
        last_error: Exception | None = None

        for _ in range(len(self.clients)):
            client_index, client = self._select_client_with_index()
            try:
                return call(client)
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if self._is_decrypt_error(exc):
                    self._mark_disabled(
                        client_index,
                        f"decrypt error on {operation_name} endpoint",
                    )
                    continue
                raise

        if last_error is not None:
            raise last_error

        raise RuntimeError(f"No Riot API clients available for {operation_name}")

    def get_league_entries(
        self,
        queue: str,
        tier: str,
        division: str,
    ) -> List[dict]:
        """Get league entries. Delegates to a selected client."""
        return self._with_client_retry(
            "get_league_entries",
            lambda client: client.get_league_entries(queue=queue, tier=tier, division=division),
        )

    def get_summoner_by_puuid(self, puuid: str) -> dict:
        """Get summoner by PUUID. Delegates to a selected client."""
        return self._with_client_retry(
            "get_summoner_by_puuid",
            lambda client: client.get_summoner_by_puuid(puuid=puuid),
        )

    def get_match_ids_by_puuid(
        self,
        puuid: str,
        start: int = 0,
        count: int = 20,
    ) -> List[str]:
        """Get match IDs by PUUID. Delegates to a selected client."""
        return self._with_client_retry(
            "get_match_ids_by_puuid",
            lambda client: client.get_match_ids_by_puuid(puuid=puuid, start=start, count=count),
        )

    def get_match_info_by_match_id(self, match_id: str) -> dict:
        """Get match info by match ID. Delegates to a selected client."""
        return self._with_client_retry(
            "get_match_info_by_match_id",
            lambda client: client.get_match_info_by_match_id(match_id=match_id),
        )

    def get_rate_limiter_status(self) -> dict:
        """Get rate limiter status for all keys.
        
        Returns:
            dict: Status dict with per-key token info and aggregate totals.
        """
        status = {
            "keys_count": len(self.clients),
            "per_key": [],
            "aggregate": {
                "total_tokens": 0,
                "total_capacity": 0,
            },
        }

        for i, client in enumerate(self.clients):
            key_status = {
                "key_index": i,
                "tokens": client.rate_limiter.available(),
                "capacity": client.rate_limiter.capacity,
                "reserved": client.rate_limiter.reserved,
            }
            status["per_key"].append(key_status)
            status["aggregate"]["total_tokens"] += key_status["tokens"]
            status["aggregate"]["total_capacity"] += key_status["capacity"]

        return status
