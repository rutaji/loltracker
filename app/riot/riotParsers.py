from datetime import UTC, datetime
from typing import Any

import logging

from app.models.summonerModels import Match, MatchParticipant, Summoner
from app.utils.versioning import normalize_version

logger = logging.getLogger(__name__)


class MatchParticipantParser:
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
