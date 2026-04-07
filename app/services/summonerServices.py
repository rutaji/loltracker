from fastapi import Request
from typing import Optional
from app.models.summonerModels import Summoner, MatchPage
from app.database.DAO import DAO
from app.riot.riotParsers import MatchParser, SummonerParser

def get_summoner_service(request: Request, name: str, tagline: str, dao: DAO) -> Optional[Summoner]:
    summoner = dao.get_summoner(f"{name}#{tagline}")

    if summoner is not None:
        print(Summoner)
        return summoner

    try:
        account_data = request.app.state.api_client.get_summoner_by_riot_id(name, tagline)
        summoner = SummonerParser.parse(account_data)
        dao.add_summoner(summoner)
        return summoner
    except Exception:
        return None


def get_matches_service(
    request: Request,
    name: str,
    tagline: str,
    offset: int,
    count: int,
    dao: DAO,
) -> MatchPage:
    summoner_name = f"{name}#{tagline}"
    matches = dao.get_matches(summoner_name, offset, count)

    if len(matches) < count and request is not None:
        summoner = dao.get_summoner(summoner_name)

        puuid = summoner.puuid if summoner is not None else None

        if not puuid:
            account_data = request.app.state.api_client.get_summoner_by_riot_id(name, tagline)
            puuid = SummonerParser.parse(account_data).puuid

        if puuid:
            match_ids = request.app.state.api_client.get_match_ids_by_puuid(
                puuid,
                start=offset,
                count=count + len(matches),
            )

            existing_ids = {str(match.match_id) for match in matches}
            remote_matches = []

            for match_id in match_ids:
                if match_id in existing_ids:
                    continue

                match_data = request.app.state.api_client.get_match_info_by_match_id(match_id)
                match = MatchParser.parse(match_data)
                remote_matches.append(match)
                dao.add_match(match)
                if len(matches) + len(remote_matches) >= count:
                    break

            matches = matches + remote_matches

    hasMore = len(matches) == count

    return MatchPage(
        matches=matches,
        hasMore=hasMore,
        nextOffset=offset+count
    )
