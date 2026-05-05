from typing import Any
from urllib.parse import quote

import logging
import time
import random
import httpx
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)


class RiotApiClient:
    def __init__(
        self,
        api_key: str,
        regional_routing: str = "europe",
        platform_routing: str = "euw1",
        timeout: float = 10.0,
        *,
        rate_limiter: object | None = None,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.regional_routing = regional_routing
        self.platform_routing = platform_routing
        self.timeout = timeout
        self.rate_limiter = rate_limiter
        self.max_retries = max_retries
        # Log a safe identifier for the key (last 8 chars only for security)
        key_suffix = api_key[-8:] if api_key and len(api_key) > 8 else "UNKNOWN"
        self.key_identifier = f"key_ends_with_{key_suffix}"
        logger.debug(
            "RiotApiClient initialized: regional_routing=%s platform_routing=%s timeout=%s key=%s",
            self.regional_routing,
            self.platform_routing,
            self.timeout,
            self.key_identifier,
        )

    @property
    def _headers(self) -> dict[str, str]:
        return {"X-Riot-Token": self.api_key}

    def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        token_cost: int = 1,
        *,
        use_platform_routing: bool = False,
    ) -> Any:
        routing = self.platform_routing if use_platform_routing else self.regional_routing
        url = f"https://{routing}.api.riotgames.com{path}"
        logger.debug(
            "riot.api.request: url=%s params=%s key=%s",
            url,
            params,
            self.key_identifier,
        )
        logger.debug("riot.api.request: path_repr=%r url_repr=%r", path, url)
        tracer = trace.get_tracer(__name__)

        attempts = 0
        while True:
            attempts += 1

            # Acquire tokens if a rate limiter was provided
            if self.rate_limiter is not None:
                got = self.rate_limiter.acquire(tokens=token_cost, block=True, timeout=10)
                if not got:
                    logger.warning("Rate limiter denied tokens for request to %s", path)
                    raise httpx.RequestError("Rate limiter denied tokens")

            with tracer.start_as_current_span("riot.api.request") as span:
                span.set_attribute("http.method", "GET")
                span.set_attribute("riot.routing", routing)
                span.set_attribute("http.route", path)

                try:
                    with httpx.Client(timeout=self.timeout) as client:
                        response = client.get(url, headers=self._headers, params=params)
                    status_code = getattr(response, "status_code", None)
                    if status_code is not None:
                        span.set_attribute("http.status_code", status_code)
                    response.raise_for_status()
                    logger.debug("riot.api.request: success url=%s status=%s", url, status_code)
                    return response.json()
                except httpx.HTTPStatusError as exc:
                    status = getattr(exc.response, "status_code", None)
                    span.record_exception(exc)
                    span.set_status(Status(StatusCode.ERROR))
                    # Handle rate-limit specifically
                    if status == 429:
                        retry_after = None
                        try:
                            retry_after = int(exc.response.headers.get("Retry-After", "0"))
                        except Exception:
                            retry_after = None
                        sleep_for = retry_after if retry_after and retry_after > 0 else (2 ** (attempts - 1))
                        sleep_for = sleep_for + random.random() * 0.5
                        logger.warning("Riot API rate limited (429) - sleeping %.1fs (attempt %s) for %s", sleep_for, attempts, url)
                        time.sleep(sleep_for)
                        if attempts >= self.max_retries:
                            raise
                        continue
                    # Retry on server errors with backoff
                    if status is not None and 500 <= status < 600 and attempts < self.max_retries:
                        sleep_for = (2 ** (attempts - 1)) + random.random() * 0.5
                        logger.warning("Riot API server error %s - retrying in %.1fs (attempt %s)", status, sleep_for, attempts)
                        time.sleep(sleep_for)
                        continue
                    # Log response body for client errors to help debug
                    try:
                        error_body = exc.response.text[:500]  # Limit to first 500 chars
                    except Exception:
                        error_body = "(could not read response)"
                    logger.error(
                        "riot.api.request: HTTP error url=%s status=%s response=%s",
                        url,
                        status,
                        error_body,
                    )
                    raise
                except httpx.RequestError as exc:
                    span.record_exception(exc)
                    span.set_status(Status(StatusCode.ERROR))
                    if attempts < self.max_retries:
                        sleep_for = (2 ** (attempts - 1)) + random.random() * 0.5
                        logger.warning("riot.api.request: network error - retrying in %.1fs (attempt %s): %s", sleep_for, attempts, exc)
                        time.sleep(sleep_for)
                        continue
                    logger.error("riot.api.request: network error final failure: %s", exc)
                    raise

    def get_summoner_by_riot_id(
        self,
        game_name: str,
        tagline: str,
    ) -> dict[str, Any]:
        logger.debug("get_summoner_by_riot_id: game_name=%s tagline=%s", game_name, tagline)
        encoded_game_name = quote(game_name, safe="")
        encoded_tagline = quote(tagline, safe="")

        return self._get(
            f"/riot/account/v1/accounts/by-riot-id/{encoded_game_name}/{encoded_tagline}"
        )

    def get_summoner_by_puuid(self, puuid: str) -> dict[str, Any]:
        logger.debug("get_summoner_by_puuid: puuid=%s", puuid)
        return self._get(
            f"/riot/account/v1/accounts/by-puuid/{quote(puuid, safe='')}"
        )

    def get_match_ids_by_puuid(
        self,
        puuid: str,
        start: int = 0,
        count: int = 20,
    ) -> list[str]:
        logger.debug("get_match_ids_by_puuid: puuid=%s start=%s count=%s", puuid, start, count)
        return self._get(
            f"/lol/match/v5/matches/by-puuid/{quote(puuid, safe='')}/ids",
            params={"start": start, "count": count},
        )

    def get_match_info_by_match_id(self, match_id: str) -> dict[str, Any]:
        logger.debug("get_match_info_by_match_id: match_id=%s", match_id)
        return self._get(f"/lol/match/v5/matches/{quote(match_id, safe='')}")

    def get_league_entries_by_puuid(self, puuid: str) -> list[dict[str, Any]]:
        logger.debug("get_league_entries_by_puuid: puuid=%s", puuid)
        return self._get(
            f"/lol/league/v4/entries/by-puuid/{quote(puuid, safe='')}",
            use_platform_routing=True,
        ) or []

    def get_league_entries(self, queue: str, tier: str, division: str | None = None) -> list[dict[str, Any]]:
        """Fetch league entries.

        Handles special endpoints for tiers without divisions (CHALLENGER/GRANDMASTER/MASTER)
        and skips ARAM (no league entries available).
        """
        q = (queue or "").upper()
        t = (tier or "").upper()
        logger.debug("get_league_entries: queue=%s tier=%s division=%s", q, t, division)

        try:
            if t == "CHALLENGER":
                path = f"/lol/league/v4/challengerleagues/by-queue/{quote(queue, safe='')}"
                resp = self._get(path, use_platform_routing=True)
                return resp.get("entries") if isinstance(resp, dict) else resp or []

            if t == "GRANDMASTER":
                path = f"/lol/league/v4/grandmasterleagues/by-queue/{quote(queue, safe='')}"
                resp = self._get(path, use_platform_routing=True)
                return resp.get("entries") if isinstance(resp, dict) else resp or []

            if t == "MASTER":
                path = f"/lol/league/v4/masterleagues/by-queue/{quote(queue, safe='')}"
                resp = self._get(path, use_platform_routing=True)
                return resp.get("entries") if isinstance(resp, dict) else resp or []

            # Default: tiers with divisions
            if not division:
                logger.warning("No division provided for tier=%s; skipping league entries", t)
                return []

            return self._get(
                f"/lol/league/v4/entries/{quote(queue, safe='')}/{quote(tier, safe='')}/{quote(division, safe='')}",
                use_platform_routing=True,
            ) or []
        except Exception:
            logger.exception("Failed to fetch league entries for %s/%s/%s", queue, tier, division)
            return []

    def get_summoner_by_encrypted_id(self, encrypted_summoner_id: str) -> dict[str, Any]:
        logger.debug("get_summoner_by_encrypted_id")
        return self._get(
            f"/lol/summoner/v4/summoners/{quote(encrypted_summoner_id, safe='')}",
            use_platform_routing=True,
        )
