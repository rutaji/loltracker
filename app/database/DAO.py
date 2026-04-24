import logging
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, func
from sqlalchemy.orm import joinedload

import app.models.championModels
import app.models.summonerModels
from app.database.database import SessionLocal
from app.database.models import Match, Summoner, MatchParticipant, Champion, ChampionStats, MatchesAnalyzed
from app.utils.utils import split_name

logger = logging.getLogger(__name__)

class DAO:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def get_dao():
        return DAO(SessionLocal())

    def rollback(self):
        self.db.rollback()

    def close(self):
        self.db.close()

    def _get_summoner_row(self, summoner_name: str):
        logger.debug("_get_summoner_row: looking up summoner=%s", summoner_name)
        result = (
            self.db.query(Summoner)
            .filter(func.lower(Summoner.summoner_name) == summoner_name.lower())
            .first()
        )
        logger.debug("_get_summoner_row: found=%s for name=%s id=%s", bool(result), summoner_name,result.id)
        return result

    def get_champion(self,champion_name :str,patch :list[str]):
        dao_champions = (
            self.db.query(ChampionStats)
            .join(Champion)
            .filter(Champion.champion_name.ilike(champion_name))
            .filter(ChampionStats.patch.in_(patch))
            .all()
        )
        if not dao_champions:
            logger.debug("Get_champion: champion not found for champion_name=%s patch=%r " , champion_name,patch)
            return None
        logger.debug("Get_champion: champion found for champion_name=%s patch=%r " , champion_name,patch)

        matches_analyzed = self.db.query(MatchesAnalyzed).filter(MatchesAnalyzed.patch.in_(patch)).all()
        analyzed_lookup = {(ma.patch, ma.gametype): ma.count for ma in matches_analyzed}
        result = []
        for dao_champion in dao_champions:
            result.append(
                app.models.championModels.ChampionStats(
                    version=dao_champion.patch,
                    gamemode=dao_champion.gametype,
                    wins=dao_champion.games_won,
                    gamesPlayed=dao_champion.games_played,
                    kills=dao_champion.kill,
                    deaths=dao_champion.death,
                    assists=dao_champion.assist,
                    banned=dao_champion.games_banned,
                    matchesAnalyzed=analyzed_lookup.get((dao_champion.patch, dao_champion.gametype), 0)
                )
            )
        logger.debug("get_champion: returning %d championStats for %s", len(result), champion_name)
        return app.models.championModels.Champion(
            name=dao_champions[0].ChampionStats_Champion.champion_name or champion_name,
            championStats=result,
        )

    def get_summoner(self,summoner_name:str):
        logger.debug("get_summoner: looking up summoner=%s", summoner_name)
        summoner = self._get_summoner_row(summoner_name)
        if summoner is None:
            logger.info("get_summoner: summoner not found=%s", summoner_name)
            return None

        name = split_name(summoner.summoner_name)
        result = app.models.summonerModels.Summoner(
            puuid=summoner.id,
            name = name[0],
            tagline = name[1],
            wins = summoner.games_won or 0,
            gamesPlayed = summoner.games_played or 0,
            kills = summoner.kill or 0,
            deaths = summoner.death or 0,
            assists = summoner.assist or 0,
        )
        logger.debug("get_summoner: returning summoner puuid=%s", result.puuid)
        return result

    def get_matches(self, summoner_name, offset, count):
        logger.debug("get_matches: summoner=%s offset=%s count=%s", summoner_name, offset, count)
        summoner = self._get_summoner_row(summoner_name)
        if not summoner:
            logger.info("get_matches: no summoner found=%s", summoner_name)
            return []
        matches = (
            self.db.query(Match)
            .join(MatchParticipant)
            .filter(MatchParticipant.summoner_id == summoner.id)
            .order_by(desc(Match.created), desc(Match.id))
            .offset(offset)
            .limit(count)
            .options(
                joinedload(Match.Match_MatchParticipant)  # load participants for each match
                .joinedload(MatchParticipant.MatchParticipant_Summoner),  # load participant's summoner info
                joinedload(Match.Match_MatchParticipant)
                .joinedload(MatchParticipant.MatchParticipant_Champion)  # load participant's champion info
            )
            .all()
        )
        logger.debug("get_matches: retrieved %d matches for summoner=%s", len(matches), summoner_name)
        result = []
        for match in matches:
            participants_list = []
            for p in match.Match_MatchParticipant:
                summoner_name = p.MatchParticipant_Summoner.summoner_name if p.MatchParticipant_Summoner else ""
                name = split_name(summoner_name)
                participants_list.append(
                    app.models.summonerModels.MatchParticipant(
                        puuid=p.summoner_id,
                        name=name[0] or "",
                        tagline=name[1] or "",  # if your Summoner model has a tagline field, use it
                        kills=p.kill,
                        deaths=p.death,
                        assists=p.assist,
                        gold=p.gold,
                        team=p.team,
                        champion=(p.MatchParticipant_Champion.champion_name if p.MatchParticipant_Champion else "") or "",
                        won=p.won
                    )
                )

            result.append(
                app.models.summonerModels.Match(
                    match_id=match.id,
                    start=datetime.fromtimestamp(match.created),
                    end=datetime.fromtimestamp(match.ended),
                    version=match.patch,
                    mode=match.gametype,
                    participants=participants_list
                )
            )
        logger.debug("get_matches: returning %d formatted matches for summoner=%s", len(result), summoner_name)
        return result

    def summoner_has_matches(self, summoner_name: str) -> bool:
        summoner = self._get_summoner_row(summoner_name)
        if not summoner:
            return False

        match = (
            self.db.query(MatchParticipant)
            .filter(MatchParticipant.summoner_id == summoner.id)
            .first()
        )
        return match is not None

    def get_match_ids_for_summoner(self, summoner_name: str) -> set[str]:
        summoner = self._get_summoner_row(summoner_name)
        if not summoner:
            return set()

        match_ids = (
            self.db.query(MatchParticipant.match_id)
            .filter(MatchParticipant.summoner_id == summoner.id)
            .all()
        )
        return {match_id for (match_id,) in match_ids}











    def add_match(self, match: app.models.summonerModels.Match):
            try:
                match_id = str(match.match_id)
                logger.info("add_match: attempting to add match_id=%s", match_id)
                if self.match_exist(match_id):
                    logger.debug("add_match: match already exists match_id=%s", match_id)
                    return False

                dao_match = Match(
                    id=match_id,
                    created=int(match.start.timestamp()),
                    ended=int(match.end.timestamp()),
                    gametype=match.mode,
                    patch=match.version,
                )

                dao_participants = []
                queued_summoner_ids = set()
                queued_champion_ids = set()

                for participant in match.participants:
                    summoner_name = f"{participant.name}#{participant.tagline}"
                    summoner_id = participant.puuid
                    champion = self.db.query(Champion).filter(Champion.champion_name == participant.champion).first()

                    if not summoner_id:
                        summoner = self.db.query(Summoner).filter(Summoner.summoner_name == summoner_name).first()
                        summoner_id = summoner.id if summoner is not None else summoner_name

                    champion_id = champion.id if champion is not None else participant.champion

                    dao_participants.append(
                        (
                            MatchParticipant(
                                summoner_id=summoner_id,
                                match_id=match_id,
                                kill=participant.kills,
                                death=participant.deaths,
                                assist=participant.assists,
                                gold=participant.gold,
                                team=participant.team,
                                won=participant.won,
                                champion=champion_id,
                            ),
                            summoner_name,
                        )
                    )

                self.db.add(dao_match)
                for participant, summoner_name in dao_participants:
                    self.db.add(participant)
                    if participant.summoner_id not in queued_summoner_ids and not self.summoner_exist(participant.summoner_id):
                        logger.debug("add_match: creating default summoner id=%s name=%s", participant.summoner_id, summoner_name)
                        self.db.merge(Summoner.create_default(id=participant.summoner_id, name=summoner_name))
                        queued_summoner_ids.add(participant.summoner_id)
                    if participant.champion not in queued_champion_ids and not self.champion_exist(participant.champion):
                        logger.debug("add_match: creating default champion id=%s", participant.champion)
                        self.db.merge(Champion.create_default(id=participant.champion, name=participant.champion))
                        queued_champion_ids.add(participant.champion)
                self.db.commit()
                logger.info("add_match: successfully added match_id=%s", match_id)
            except SQLAlchemyError:
                logger.error("add_match: failed to add match_id=%s", match_id)
                self.db.rollback()
                raise

    def add_summoner(self, summoner: app.models.summonerModels.Summoner):
            try:
                logger.info("add_summoner: adding summoner puuid=%s", summoner.puuid)
                dao_summoner = Summoner(
                    id=summoner.puuid,
                    summoner_name=f"{summoner.name}#{summoner.tagline}",
                    games_played=summoner.gamesPlayed,
                    games_won=summoner.wins,
                    kill=summoner.kills,
                    death=summoner.deaths,
                    assist=summoner.assists,
                )
                self.db.merge(dao_summoner)
                self.db.commit()
                logger.info("add_summoner: committed summoner puuid=%s", summoner.puuid)
            except SQLAlchemyError:
                logger.error("add_summoner: failed to add summoner puuid=%s", getattr(summoner, 'puuid', None))
                self.db.rollback()
                raise

    def get_summoner_dao(self, summoner_id) -> Summoner:
        return self.db.query(Summoner).filter(Summoner.id == summoner_id).first()

    def add_champion(self,champion:Champion):
            try:
                logger.info("add_champion: merging champion id=%s", getattr(champion, 'id', None))
                self.db.merge(champion)
                self.db.commit()
                logger.info("add_champion: committed champion id=%s", getattr(champion, 'id', None))
            except SQLAlchemyError:
                logger.error("add_champion: failed for champion id=%s", getattr(champion, 'id', None))
                self.db.rollback()
                raise

    def get_champion_dao(self, champion_id) -> Champion:
        return self.db.query(Champion).filter(Champion.id == champion_id).first()




    def match_exist(self,id) -> bool:
        exists = self.db.query(Match).filter(Match.id == id).first() is not None
        logger.debug("match_exist: id=%s exists=%s", id, exists)
        return exists

    def summoner_exist(self,id) -> bool:
        exists = self.db.query(Summoner).filter(Summoner.id == id).first() is not None
        logger.debug("summoner_exist: id=%s exists=%s", id, exists)
        return exists

    def champion_exist(self,id) -> bool:
        exists = self.db.query(Champion).filter(Champion.id == id).first() is not None
        logger.debug("champion_exist: id=%s exists=%s", id, exists)
        return exists



