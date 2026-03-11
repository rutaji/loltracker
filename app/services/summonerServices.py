from fastapi import HTTPException
from app.models.summonerModels import MatchPage

def get_summoner_service(name: str, dao, offset: int, count: int):
    summonerData=dao.get_summoner(name)

    if summonerData is None:
        raise HTTPException(status_code=404, detail=f"No summoner named {name} was found")

    matchData=get_matches_service(name, offset, count, dao)

    return {
        "summoner": summonerData,
        "matchData": matchData
    }

def get_matches_service(name: str, offset: int, count: int, dao):
    matches=dao.get_matches(name, offset, count)

    hasMore = len(matches) == count

    return MatchPage(
        matches=matches,
        hasMore=hasMore,
        nextOffset=offset+count
    )
