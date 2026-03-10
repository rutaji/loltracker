from fastapi import HTTPException

initOffset=0
initCount=20

def get_summoner_service(name: str, dao):
    summonerData=dao.get_summoner(name)

    if summonerData is None:
        raise HTTPException(status_code=404, detail=f"No summoner named {name} was found")

    summonerData["winrate"]=calc_winrate(summonerData["wins"], summonerData["losses"])
    summonerData["kda"]=calc_kda(summonerData["kills"], summonerData["deaths"], summonerData["assists"])
    
    matchData=get_matches(name, initOffset, initCount, dao)

    return {
        "summoner": summonerData,
        "matchData": matchData
    }

def get_matches(name: str, offset: int, count: int, dao):
    matches=dao.get_matches(name, offset, count)
    hasMore=True

    if len(matches) < count:
        hasMore=False

    return {
        "matches": matches,
        "hasMore": hasMore
    }

def calc_winrate(wins: int, losses: int):
    gamesPlayed=wins + losses

    if gamesPlayed==0:
        return -1

    return (wins/gamesPlayed)*100

def calc_kda(kills: int, deaths: int, assists: int):
    if deaths==0:
        deaths=1

    return (kills + assists)/deaths