import logging
from fastapi import Request
from typing import NamedTuple, Optional
import httpx
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from app.models.summonerModels import Summoner, MatchPage
from app.database.DAO import DAO
from app.riot.riotParsers import MatchParser, SummonerParser

LOGGER = logging.getLogger(__name__)


class MatchServiceResult(NamedTuple):
    match_page: MatchPage
    refreshed_from_remote: bool


class SummonerPageServiceResult(NamedTuple):
    summoner: Optional[Summoner]
    match_page: Optional[MatchPage]


def get_summoner_service(request: Request, name: str, tagline: str, dao: DAO) -> Optional[Summoner]:
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("service.summoner.get") as span:
        span.set_attribute("summoner.lookup.cache", True)
        span.set_attribute("summoner.request.name_length", len(name))
        summoner = dao.get_summoner(f"{name}#{tagline}")

        if summoner is not None:
            span.set_attribute("summoner.cache_hit", True)
            return summoner

        span.set_attribute("summoner.cache_hit", False)

        try:
            account_data = request.app.state.api_client.get_summoner_by_riot_id(name, tagline)
            summoner = SummonerParser.parse(account_data)
            dao.add_summoner(summoner)
            return summoner
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR))
            return None


def get_matches_service(
    request: Request,
    name: str,
    tagline: str,
    offset: int,
    count: int,
    dao: DAO,
) -> MatchServiceResult:
    tracer = trace.get_tracer(__name__)
    summoner_name = f"{name}#{tagline}"
    refreshed_from_remote = False
    query_count = count + 1

    with tracer.start_as_current_span("service.matches.get") as span:
        span.set_attribute("matches.offset", offset)
        span.set_attribute("matches.count", count)
        matches = dao.get_matches(summoner_name, offset, query_count)
        span.set_attribute("matches.cached_count", len(matches))
        has_cached_matches_method = getattr(dao, "summoner_has_matches", None)
        has_cached_matches = (
            has_cached_matches_method(summoner_name)
            if callable(has_cached_matches_method)
            else len(matches) > 0
        )
        span.set_attribute("matches.cache_populated", has_cached_matches)

        if not has_cached_matches and request is not None:
            summoner = dao.get_summoner(summoner_name)

            puuid = summoner.puuid if summoner is not None else None

            if not puuid:
                account_data = request.app.state.api_client.get_summoner_by_riot_id(name, tagline)
                puuid = SummonerParser.parse(account_data).puuid

            if puuid:
                try:
                    match_ids = request.app.state.api_client.get_match_ids_by_puuid(
                        puuid,
                        start=offset,
                        count=query_count,
                    )
                except httpx.RequestError as exc:
                    span.record_exception(exc)
                    span.set_attribute("matches.remote_fetch_failed", True)
                    LOGGER.warning(
                        "Failed to fetch Riot match ids for %s: %s",
                        summoner_name,
                        exc,
                    )
                    match_ids = []

                existing_ids = {str(match.match_id) for match in matches}
                remote_matches = []
                remote_failures = 0

                for match_id in match_ids:
                    if match_id in existing_ids:
                        continue

                    try:
                        match_data = request.app.state.api_client.get_match_info_by_match_id(match_id)
                        match = MatchParser.parse(match_data)
                        remote_matches.append(match)
                        dao.add_match(match)
                        refreshed_from_remote = True
                    except httpx.RequestError as exc:
                        remote_failures += 1
                        span.record_exception(exc)
                        LOGGER.warning(
                            "Failed to fetch Riot match detail %s for %s: %s",
                            match_id,
                            summoner_name,
                            exc,
                        )
                        continue
                    if len(matches) + len(remote_matches) >= query_count:
                        break

                matches = matches + remote_matches
                span.set_attribute("matches.remote_count", len(remote_matches))
                span.set_attribute("matches.remote_failures", remote_failures)

        hasMore = len(matches) > count
        span.set_attribute("matches.has_more", hasMore)
        visible_matches = matches[:count]

        return MatchServiceResult(
            match_page=MatchPage(
                matches=visible_matches,
                hasMore=hasMore,
                nextOffset=offset+count
            ),
            refreshed_from_remote=refreshed_from_remote,
        )


def load_summoner_page(
    request: Request,
    name: str,
    tagline: str,
    offset: int,
    count: int,
    dao: DAO,
) -> SummonerPageServiceResult:
    summoner = get_summoner_service(request, name, tagline, dao)
    if summoner is None:
        return SummonerPageServiceResult(summoner=None, match_page=None)

    match_result = get_matches_service(request, name, tagline, offset, count, dao)

    if match_result.refreshed_from_remote:
        refreshed_summoner = dao.get_summoner(f"{name}#{tagline}")
        if refreshed_summoner is not None:
            summoner = refreshed_summoner

    return SummonerPageServiceResult(
        summoner=summoner,
        match_page=match_result.match_page,
    )
