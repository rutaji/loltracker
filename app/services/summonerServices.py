from typing import Optional
from app.models.summonerModels import Summoner, MatchPage
from app.services.stubDAO import stubDAO

def get_summoner_service(name: str, tagline: str, dao) -> Optional[Summoner]:
    summoner = dao.get_summoner(f"{name}#{tagline}")

    if summoner is None:
        return None

    print(Summoner)
    return summoner

def get_matches_service(name: str, tagline: str, offset: int, count: int, dao: stubDAO) -> MatchPage:
    matches=dao.get_matches(f"{name}#{tagline}", offset, count)

    hasMore = len(matches) == count

    return MatchPage(
        matches=matches,
        hasMore=hasMore,
        nextOffset=offset+count
    )
