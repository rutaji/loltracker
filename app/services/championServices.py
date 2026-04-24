import logging
from collections import defaultdict
from typing import Optional
from opentelemetry import trace
from app.models.championModels import Champion, ChampionStats
from app.database.DAO import DAO
from app.utils.versioning import normalize_version, version_sort_key

logger = logging.getLogger(__name__)

def get_champion_service(name: str, version: list[str], dao: DAO) -> Optional[Champion]:

def _empty_aggregate_bucket() -> dict[str, int]:
    return {
        "wins": 0,
        "gamesPlayed": 0,
        "kills": 0,
        "deaths": 0,
        "assists": 0,
        "banned": 0,
        "matchesAnalyzed": 0,
    }


def _accumulate_stat(entry: dict[str, int], stat: ChampionStats) -> None:
    entry["wins"] += stat.wins
    entry["gamesPlayed"] += stat.gamesPlayed
    entry["kills"] += stat.kills
    entry["deaths"] += stat.deaths
    entry["assists"] += stat.assists
    entry["banned"] += stat.banned
    entry["matchesAnalyzed"] += stat.matchesAnalyzed


def _aggregate_by_queue_and_version(stats: list[ChampionStats]) -> dict[str, dict[str, dict[str, int]]]:
    grouped: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(_empty_aggregate_bucket)
    )

    for stat in stats:
        normalized = normalize_version(stat.version)
        _accumulate_stat(grouped[stat.queueDescription][normalized], stat)

    return grouped


def get_available_versions(stats: list[ChampionStats]) -> list[str]:
    return sorted(
        {normalize_version(stat.version) for stat in stats},
        key=version_sort_key,
        reverse=True,
    )


def aggregate_stats_for_version(stats: list[ChampionStats], version: str) -> list[ChampionStats]:
    grouped = _aggregate_by_queue_and_version(stats)

    aggregated = []
    for queue_description in sorted(grouped):
        values = grouped[queue_description].get(version)
        if values is None:
            continue

        aggregated.append(
            ChampionStats(
                version=version,
                queueDescription=queue_description,
                wins=values["wins"],
                gamesPlayed=values["gamesPlayed"],
                kills=values["kills"],
                deaths=values["deaths"],
                assists=values["assists"],
                banned=values["banned"],
                matchesAnalyzed=values["matchesAnalyzed"],
            )
        )

    return aggregated


def serialize_stat(stat: ChampionStats) -> dict:
    return {
        "version": stat.version,
        "queueDescription": stat.queueDescription,
        "wins": stat.wins,
        "gamesPlayed": stat.gamesPlayed,
        "kills": stat.kills,
        "deaths": stat.deaths,
        "assists": stat.assists,
        "banned": stat.banned,
        "matchesAnalyzed": stat.matchesAnalyzed,
        "winrate": round(stat.winrate, 2),
        "pickrate": round(stat.pickrate, 2),
        "banrate": round(stat.banrate, 2),
        "kda": round(stat.kda, 2),
        "totalMatchesPlayed": stat.gamesPlayed,
    }


def build_trend_series(stats: list[ChampionStats]) -> list[dict]:
    grouped = _aggregate_by_queue_and_version(stats)

    trend_series = []
    for queue_description, by_version in grouped.items():
        ordered_versions = sorted(by_version, key=version_sort_key)
        trend_series.append(
            {
                "queueDescription": queue_description,
                "points": [
                    {
                        "version": version,
                        "winrate": round((values["wins"] / values["gamesPlayed"]) * 100, 2)
                        if values["gamesPlayed"]
                        else -1,
                        "pickrate": round((values["gamesPlayed"] / values["matchesAnalyzed"]) * 100, 2)
                        if values["matchesAnalyzed"]
                        else 0,
                        "banrate": round((values["banned"] / values["matchesAnalyzed"]) * 100, 2)
                        if values["matchesAnalyzed"]
                        else 0,
                        "kda": round((values["kills"] + values["assists"]) / (values["deaths"] or 1), 2),
                        "totalMatchesPlayed": values["gamesPlayed"],
                    }
                    for version in ordered_versions
                    for values in [by_version[version]]
                ],
            }
        )

    return sorted(trend_series, key=lambda series: series["queueDescription"])

def get_champion_service(name: str, version: list[str] | None, dao: DAO) -> Optional[Champion]:
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("service.champion.get") as span:
        span.set_attribute("champion.request.name_length", len(name))
        span.set_attribute("champion.request.versions", len(version or []))
        champion = dao.get_champion(name, version)

        if champion is None:
            span.set_attribute("champion.found", False)
            logger.debug("ChampionService: champion %s not found", name)
            return None

        span.set_attribute("champion.found", True)
        logger.debug("ChampionService: champion %s found", name)
        return champion
