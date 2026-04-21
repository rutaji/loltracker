from typing import Any
from urllib.parse import quote

import httpx
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode


class RiotApiClient:
    def __init__(
        self,
        api_key: str,
        regional_routing: str = "europe",
        timeout: float = 10.0,
    ):
        self.api_key = api_key
        self.regional_routing = regional_routing
        self.timeout = timeout

    @property
    def _headers(self) -> dict[str, str]:
        return {"X-Riot-Token": self.api_key}

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"https://{self.regional_routing}.api.riotgames.com{path}"
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span("riot.api.request") as span:
            span.set_attribute("http.method", "GET")
            span.set_attribute("riot.routing", self.regional_routing)
            span.set_attribute("http.route", path)

            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=self._headers, params=params)
                status_code = getattr(response, "status_code", None)
                if status_code is not None:
                    span.set_attribute("http.status_code", status_code)
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    span.record_exception(exc)
                    span.set_status(Status(StatusCode.ERROR))
                    raise
                return response.json()

    def get_summoner_by_riot_id(
        self,
        game_name: str,
        tagline: str,
    ) -> dict[str, Any]:
        encoded_game_name = quote(game_name, safe="")
        encoded_tagline = quote(tagline, safe="")

        return self._get(
            f"/riot/account/v1/accounts/by-riot-id/{encoded_game_name}/{encoded_tagline}"
        )

    def get_summoner_by_puuid(self, puuid: str) -> dict[str, Any]:
        return self._get(
            f"/riot/account/v1/accounts/by-puuid/{quote(puuid, safe='')}"
        )

    def get_match_ids_by_puuid(
        self,
        puuid: str,
        start: int = 0,
        count: int = 20,
    ) -> list[str]:
        return self._get(
            f"/lol/match/v5/matches/by-puuid/{quote(puuid, safe='')}/ids",
            params={"start": start, "count": count},
        )

    def get_match_info_by_match_id(self, match_id: str) -> dict[str, Any]:
        return self._get(f"/lol/match/v5/matches/{quote(match_id, safe='')}")
