from collections import defaultdict
from typing import Optional
from opentelemetry import trace
from app.models.championModels import Champion, ChampionStats
from app.database.DAO import DAO
from app.utils.versioning import version_sort_key


def serialize_stat(stat: ChampionStats) -> dict:
    return {
        "version": stat.version,
        "gamemode": stat.gamemode,
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
    grouped: dict[str, list[ChampionStats]] = defaultdict(list)
    for stat in stats:
        grouped[stat.gamemode].append(stat)

    trend_series = []
    for gamemode, mode_stats in grouped.items():
        ordered_stats = sorted(mode_stats, key=lambda item: version_sort_key(item.version))
        trend_series.append(
            {
                "gamemode": gamemode,
                "points": [
                    {
                        "version": stat.version,
                        "winrate": round(stat.winrate, 2),
                        "pickrate": round(stat.pickrate, 2),
                        "banrate": round(stat.banrate, 2),
                        "kda": round(stat.kda, 2),
                        "totalMatchesPlayed": stat.gamesPlayed,
                    }
                    for stat in ordered_stats
                ],
            }
        )

    return sorted(trend_series, key=lambda series: series["gamemode"])

def get_champion_service(name: str, version: list[str] | None, dao: DAO) -> Optional[Champion]:
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("service.champion.get") as span:
        span.set_attribute("champion.request.name_length", len(name))
        span.set_attribute("champion.request.versions", len(version or []))
        champion = dao.get_champion(name, version)

        if champion is None:
            span.set_attribute("champion.found", False)
            return None

        span.set_attribute("champion.found", True)
        return champion
