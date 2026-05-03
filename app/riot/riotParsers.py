from datetime import UTC, datetime
from typing import Any

import logging

from sqlalchemy.ext.asyncio import result

from app.models.summonerModels import Match, MatchParticipant, Summoner, Ban, BanParsed, SummonerDivision
from app.utils.versioning import normalize_version
logger = logging.getLogger(__name__)


RANKED_QUEUE_TYPE_TO_ID = {
    "RANKED_SOLO_5x5": 420,
    "RANKED_FLEX_SR": 440,
}


class MatchParticipantParser:
    @staticmethod
    def _parse_position(participant_data: dict[str, Any]) -> str:
        position = (
            participant_data.get("teamPosition")
            or participant_data.get("individualPosition")
            or ""
        )
        return "" if position == "INVALID" else position

    @staticmethod
    def parse(participant_data: dict[str, Any]) -> MatchParticipant:
        # Log the identity of the participant being parsed for easier tracing
        logger.debug(
            "MatchParticipantParser.parse: puuid=%s name=%s champion=%s",
            participant_data.get("puuid"),
            participant_data.get("riotIdGameName") or participant_data.get("summonerName"),
            participant_data.get("championName"),
        )
        return MatchParticipant(
            puuid=participant_data.get("puuid", ""),
            name=participant_data.get("riotIdGameName") or participant_data.get("summonerName", ""),
            tagline=participant_data.get("riotIdTagline", ""),
            kills=participant_data.get("kills", 0),
            deaths=participant_data.get("deaths", 0),
            assists=participant_data.get("assists", 0),
            gold=participant_data.get("goldEarned", 0),
            team=participant_data.get("teamId", 0),
            position=MatchParticipantParser._parse_position(participant_data),
            champion=participant_data.get("championName", ""),
            won=participant_data.get("win", False),
        )


class MatchParser:
    @staticmethod
    def parse(match_data: dict[str, Any]) -> Match:
        metadata = match_data.get("metadata", {})
        info = match_data.get("info", {})
        participants = info.get("participants", [])
        logger.debug("MatchParser.parse: match_id=%s",metadata.get("matchId", ""))

        return Match(
            match_id=metadata.get("matchId", ""),
            start=datetime.fromtimestamp(info.get("gameStartTimestamp", 0) / 1000, tz=UTC),
            end=datetime.fromtimestamp(info.get("gameEndTimestamp", 0) / 1000, tz=UTC),
            version=normalize_version(info.get("gameVersion", "")),
            queueId=info.get("queueId", 0),
            queueDescription="",
            participants=[
                MatchParticipantParser.parse(participant)
                for participant in participants
            ],
        )
    @staticmethod
    def parse_bans(match_data: dict[str, Any]) -> list[BanParsed]:
        result =[]
        metadata = match_data.get("metadata", {})
        match_id = metadata.get("matchId", "")
        info = match_data.get("info", {})
        teams = info.get("teams", [])
        for team in teams:
            id = team.get("teamId", 0)
            bans = team.get("bans", [])
            for index, ban in enumerate(bans, start=1):
                result.append(
                    BanParsed(
                        match_id=match_id,
                        team=id,
                        ban_order=ban.get("pickTurn") or index,
                        champion_key=ban.get("championId", 0),
                    )
                )
        return result




class SummonerParser:
    @staticmethod
    def parse(
        account_data: dict[str, Any],
    ) -> Summoner:
        puuid = account_data.get("puuid")
        logger.debug("SummonerParser.parse: puuid=%s name=%s", puuid, account_data.get("gameName"))
        kills = 0
        deaths = 0
        assists = 0
        wins = 0
        games_played = 0

        return Summoner(
            puuid=puuid or "",
            name=account_data.get("gameName", ""),
            tagline=account_data.get("tagLine", ""),
            wins=wins,
            gamesPlayed=games_played,
            kills=kills,
            deaths=deaths,
            assists=assists,
        )


class SummonerDivisionParser:
    @staticmethod
    def parse_many(entries: list[dict[str, Any]]) -> list[SummonerDivision]:
        divisions: list[SummonerDivision] = []

        for entry in entries or []:
            queue_type = entry.get("queueType", "")
            queue_id = RANKED_QUEUE_TYPE_TO_ID.get(queue_type)
            if queue_id is None:
                logger.debug("SummonerDivisionParser.parse_many: skipping unsupported queue_type=%s", queue_type)
                continue

            divisions.append(
                SummonerDivision(
                    queueId=queue_id,
                    queueDescription="",
                    tier=entry.get("tier", ""),
                    rank=entry.get("rank", ""),
                    leaguePoints=entry.get("leaguePoints", 0),
                    wins=entry.get("wins", 0),
                    losses=entry.get("losses", 0),
                )
            )

        return divisions
