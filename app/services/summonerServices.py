import logging
from fastapi import Request
from typing import NamedTuple, Optional
import httpx
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from app.models.summonerModels import Summoner, MatchPage
from app.database.DAO import DAO
from app.riot.riotParsers import MatchParser, SummonerParser
from app.api.config import settings
from app.utils.queue_filters import QUEUE_FILTER_ALL, normalize_queue_filter

LOGGER = logging.getLogger(__name__)


class MatchServiceResult(NamedTuple):
    match_page: MatchPage
    refreshed_from_remote: bool


class SummonerPageServiceResult(NamedTuple):
    summoner: Optional[Summoner]
    match_page: Optional[MatchPage]


class MatchSyncResult(NamedTuple):
    inserted_count: int
    failed_count: int


class SummonerRefreshServiceResult(NamedTuple):
    summoner: Optional[Summoner]
    inserted_count: int
    failed_count: int


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


def sync_remote_matches(
    request: Request,
    summoner_name: str,
    puuid: str,
    dao: DAO,
    *,
    start: int,
    batch_size: int,
    stop_after_total: int | None = None,
) -> MatchSyncResult:
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("service.matches.sync_remote") as span:
        span.set_attribute("matches.sync.start", start)
        span.set_attribute("matches.sync.batch_size", batch_size)
        if stop_after_total is not None:
            span.set_attribute("matches.sync.stop_after_total", stop_after_total)

        cached_match_ids = dao.get_match_ids_for_summoner(summoner_name)
        span.set_attribute("matches.cached_id_count", len(cached_match_ids))
        inserted_count = 0
        failed_count = 0
        current_start = start

        while True:
            try:
                match_ids = request.app.state.api_client.get_match_ids_by_puuid(
                    puuid,
                    start=current_start,
                    count=batch_size,
                )
            except httpx.RequestError as exc:
                span.record_exception(exc)
                span.set_attribute("matches.remote_fetch_failed", True)
                LOGGER.warning(
                    "Failed to fetch Riot match ids for %s: %s",
                    summoner_name,
                    exc,
                )
                failed_count += 1
                break

            if not match_ids:
                break

            for match_id in match_ids:
                if match_id in cached_match_ids:
                    continue

                if dao.match_exist(match_id):
                    cached_match_ids.add(match_id)
                    continue

                try:
                    match_data = request.app.state.api_client.get_match_info_by_match_id(match_id)
                    match = MatchParser.parse(match_data)
                    inserted_match = dao.add_match(match)
                    bans = MatchParser.parse_bans(match_data)
                    dao.add_ban(bans)
                    if inserted_match is not False:
                        inserted_count += 1
                        cached_match_ids.add(match_id)
                except httpx.RequestError as exc:
                    failed_count += 1
                    span.record_exception(exc)
                    LOGGER.warning(
                        "Failed to fetch Riot match detail %s for %s: %s",
                        match_id,
                        summoner_name,
                        exc,
                    )
                    continue

                if stop_after_total is not None and inserted_count >= stop_after_total:
                    break

            if len(match_ids) < batch_size:
                break

            if stop_after_total is not None and inserted_count >= stop_after_total:
                break

            current_start += batch_size

        span.set_attribute("matches.remote_count", inserted_count)
        span.set_attribute("matches.remote_failures", failed_count)
        return MatchSyncResult(inserted_count=inserted_count, failed_count=failed_count)


def get_matches_service(
    request: Request,
    name: str,
    tagline: str,
    offset: int,
    count: int,
    dao: DAO,
    queue_filter: str = QUEUE_FILTER_ALL,
) -> MatchServiceResult:
    tracer = trace.get_tracer(__name__)
    summoner_name = f"{name}#{tagline}"
    refreshed_from_remote = False
    query_count = count + 1
    normalized_queue_filter = normalize_queue_filter(queue_filter)

    with tracer.start_as_current_span("service.matches.get") as span:
        span.set_attribute("matches.offset", offset)
        span.set_attribute("matches.count", count)
        span.set_attribute("matches.queue_filter", normalized_queue_filter)
        matches = dao.get_matches(summoner_name, offset, query_count, normalized_queue_filter)
        span.set_attribute("matches.cached_count", len(matches))
        has_cached_matches = dao.summoner_has_matches(summoner_name, normalized_queue_filter)
        span.set_attribute("matches.cache_populated", has_cached_matches)

        if not has_cached_matches and request is not None:
            summoner = dao.get_summoner(summoner_name)

            puuid = summoner.puuid if summoner is not None else None

            if not puuid:
                account_data = request.app.state.api_client.get_summoner_by_riot_id(name, tagline)
                puuid = SummonerParser.parse(account_data).puuid

            if puuid:
                sync_result = sync_remote_matches(
                    request,
                    summoner_name,
                    puuid,
                    dao,
                    start=offset,
                    batch_size=settings.summoner_sync_batch_size,
                    stop_after_total=query_count,
                )
                refreshed_from_remote = sync_result.inserted_count > 0
                matches = dao.get_matches(summoner_name, offset, query_count, normalized_queue_filter)
                span.set_attribute("matches.remote_count", sync_result.inserted_count)
                span.set_attribute("matches.remote_failures", sync_result.failed_count)

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

def load_favorite_champions(summoner_id,dao,count):
    favorite_champions = dao.get_summoner_champions(summoner_id,count)
    return favorite_champions


def load_summoner_page(
    request: Request,
    name: str,
    tagline: str,
    offset: int,
    count: int,
    dao: DAO,
    queue_filter: str = QUEUE_FILTER_ALL,
) -> SummonerPageServiceResult:
    summoner = get_summoner_service(request, name, tagline, dao)
    if summoner is None:
        return SummonerPageServiceResult(summoner=None, match_page=None)

    match_result = get_matches_service(request, name, tagline, offset, count, dao, queue_filter)

    if match_result.refreshed_from_remote:
        refreshed_summoner = dao.get_summoner(f"{name}#{tagline}")
        if refreshed_summoner is not None:
            summoner = refreshed_summoner

    return SummonerPageServiceResult(
        summoner=summoner,
        match_page=match_result.match_page,
    )


def refresh_summoner_matches_service(
    request: Request,
    name: str,
    tagline: str,
    dao: DAO,
) -> SummonerRefreshServiceResult:
    summoner = get_summoner_service(request, name, tagline, dao)
    if summoner is None:
        return SummonerRefreshServiceResult(summoner=None, inserted_count=0, failed_count=0)

    puuid = summoner.puuid
    if not puuid:
        account_data = request.app.state.api_client.get_summoner_by_riot_id(name, tagline)
        summoner = SummonerParser.parse(account_data)
        puuid = summoner.puuid
    else:
        account_data = request.app.state.api_client.get_summoner_by_puuid(puuid)
        remote_summoner = SummonerParser.parse(account_data)
        
        # Possible riot ID refresh
        if (remote_summoner.name, remote_summoner.tagline) != (summoner.name, summoner.tagline):
            summoner = Summoner(
                puuid=summoner.puuid,
                name=remote_summoner.name,
                tagline=remote_summoner.tagline,
                wins=summoner.wins,
                gamesPlayed=summoner.gamesPlayed,
                kills=summoner.kills,
                deaths=summoner.deaths,
                assists=summoner.assists,
            )
            dao.add_summoner(summoner)

    sync_result = sync_remote_matches(
        request,
        f"{summoner.name}#{summoner.tagline}",
        puuid,
        dao,
        start=0,
        batch_size=settings.summoner_sync_batch_size,
        stop_after_total=settings.summoner_sync_stop_after,
    )

    refreshed_summoner = dao.get_summoner(f"{summoner.name}#{summoner.tagline}") or summoner
    return SummonerRefreshServiceResult(
        summoner=refreshed_summoner,
        inserted_count=sync_result.inserted_count,
        failed_count=sync_result.failed_count,
    )
