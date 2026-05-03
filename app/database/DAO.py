import logging
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import joinedload

import app.models.championModels
import app.models.summonerModels
from app.database.database import SessionLocal
from app.database.models import Match, Summoner, MatchParticipant, Champion, ChampionStats, MatchesAnalyzed, Queue, Ban, SummonerChampion, SummonerQueue, Item
from app.utils.champion_assets import resolve_champion_image_path
from app.utils.utils import split_name
from app.utils.queue_filters import (
    FILTER_TO_QUEUE_ID,
    PRIMARY_QUEUE_IDS,
    QUEUE_FILTER_ALL,
    QUEUE_FILTER_OTHER,
    normalize_queue_filter,
)
from app.utils.versioning import version_sort_key

logger = logging.getLogger(__name__)
RANKED_QUEUE_DESCRIPTIONS = {
    420: "Ranked Solo",
    440: "Ranked Flex",
}

class DAO:
    POSITION_ORDER = {
        "TOP": 1,
        "JUNGLE": 2,
        "MIDDLE": 3,
        "MID": 3,
        "BOTTOM": 4,
        "BOT": 4,
        "UTILITY": 5,
        "SUPPORT": 5,
    }
    SUMMONER_QUEUE_ORDER = {
        420: 1,
        440: 2,
    }

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
        logger.debug("_get_summoner_row: found=%s for name=%s", bool(result), summoner_name)
        return result

    @staticmethod
    def _get_queue_description(queue: Queue | None, queue_id: int | None) -> str:
        if queue is not None and queue.description:
            return queue.description
        if queue is not None and queue.map:
            return queue.map
        if queue_id is not None:
            return "Unknown Queue"
        return ""

    def _build_summoner_divisions(self, summoner: Summoner) -> list[app.models.summonerModels.SummonerDivision]:
        ordered_divisions = sorted(
            summoner.Summoner_SummonerQueue,
            key=lambda division: (self.SUMMONER_QUEUE_ORDER.get(division.queue_id, 99), division.queue_id),
        )
        division_by_queue_id = {
            division.queue_id: app.models.summonerModels.SummonerDivision(
                queueId=division.queue_id,
                queueDescription=self._get_queue_description(division.SummonerQueue_Queue, division.queue_id),
                tier=division.tier or "",
                rank=division.rank or "",
                leaguePoints=division.league_points or 0,
                wins=division.wins or 0,
                losses=division.losses or 0,
            )
            for division in ordered_divisions
        }

        divisions = []
        for queue_id in self.SUMMONER_QUEUE_ORDER:
            division = division_by_queue_id.pop(queue_id, None)
            if division is None:
                divisions.append(
                    app.models.summonerModels.SummonerDivision(
                        queueId=queue_id,
                        queueDescription=RANKED_QUEUE_DESCRIPTIONS.get(queue_id, ""),
                        tier="UNRANKED",
                        rank="",
                        leaguePoints=0,
                        wins=0,
                        losses=0,
                    )
                )
            else:
                divisions.append(division)

        divisions.extend(division_by_queue_id.values())
        return divisions

    @staticmethod
    def _has_complete_riot_id(name: str | None, tagline: str | None) -> bool:
        return bool((name or "").strip() and (tagline or "").strip())

    @staticmethod
    def _participant_sort_key(participant: MatchParticipant) -> tuple[int, int, str, str, str, str]:
        summoner_name = ""
        tagline = ""
        champion_name = ""
        position = (participant.position or "").upper()

        if participant.MatchParticipant_Summoner and participant.MatchParticipant_Summoner.summoner_name:
            name_parts = split_name(participant.MatchParticipant_Summoner.summoner_name)
            summoner_name = (name_parts[0] or "").lower()
            tagline = (name_parts[1] or "").lower()

        if participant.MatchParticipant_Champion and participant.MatchParticipant_Champion.champion_name:
            champion_name = participant.MatchParticipant_Champion.champion_name.lower()

        return (
            participant.team or 0,
            DAO.POSITION_ORDER.get(position, 99),
            position,
            summoner_name,
            tagline,
            champion_name,
        )

    @staticmethod
    def _participant_item_slots(participant: MatchParticipant) -> list[tuple[str, int, bool]]:
        return [
            ("item0", participant.item0 or 0, False),
            ("item1", participant.item1 or 0, False),
            ("item2", participant.item2 or 0, False),
            ("item3", participant.item3 or 0, False),
            ("item4", participant.item4 or 0, False),
            ("item5", participant.item5 or 0, False),
            ("item6", participant.item6 or 0, False),
            ("roleBoundItem", participant.role_bound_item or 0, True),
        ]

    def _build_participant_items(
        self,
        participant: MatchParticipant,
        item_lookup: dict[int, Item],
    ) -> list[app.models.summonerModels.MatchParticipantItem]:
        items: list[app.models.summonerModels.MatchParticipantItem] = []

        for slot, item_id, is_role_bound in self._participant_item_slots(participant):
            item_row = item_lookup.get(item_id)
            items.append(
                app.models.summonerModels.MatchParticipantItem(
                    id=item_id,
                    name=(item_row.name if item_row and item_row.name else "") or "",
                    description=(item_row.description if item_row and item_row.description else "") or "",
                    slot=slot,
                    isRoleBound=is_role_bound,
                )
            )

        return items

    @staticmethod
    def _apply_queue_filter_to_match_query(query, queue_filter: str):
        normalized = normalize_queue_filter(queue_filter)

        if normalized == QUEUE_FILTER_ALL:
            return query

        if normalized == QUEUE_FILTER_OTHER:
            return query.filter(
                or_(
                    Match.queue_id.is_(None),
                    Match.queue_id.notin_(PRIMARY_QUEUE_IDS),
                )
            )

        queue_id = FILTER_TO_QUEUE_ID.get(normalized)
        if queue_id is None:
            return query

        return query.filter(Match.queue_id == queue_id)

    def get_champion_versions(self, champion_name: str) -> list[str]:
        versions = (
            self.db.query(ChampionStats.patch)
            .join(Champion)
            .filter(Champion.champion_name.ilike(champion_name))
            .distinct()
            .all()
        )
        return sorted(
            [patch for (patch,) in versions],
            key=version_sort_key,
            reverse=True,
        )

    def get_champion(self, champion_name: str, patch: list[str] | None):
        query = (
            self.db.query(ChampionStats)
            .join(Champion)
            .filter(Champion.champion_name.ilike(champion_name))
        )
        if patch:
            query = query.filter(ChampionStats.patch.in_(patch))

        dao_champions = query.all()
        if not dao_champions:
            return None

        matches_analyzed_query = self.db.query(MatchesAnalyzed)
        if patch:
            matches_analyzed_query = matches_analyzed_query.filter(MatchesAnalyzed.patch.in_(patch))

        matches_analyzed = matches_analyzed_query.all()
        analyzed_lookup = {(ma.patch, ma.queue_id): ma.count for ma in matches_analyzed}
        result = []
        for dao_champion in dao_champions:
            result.append(
                app.models.championModels.ChampionStats(
                    version=dao_champion.patch,
                    queueId=dao_champion.queue_id,
                    queueDescription=self._get_queue_description(dao_champion.ChampionStats_Queue, dao_champion.queue_id),
                    wins=dao_champion.games_won,
                    gamesPlayed=dao_champion.games_played,
                    kills=dao_champion.kill,
                    deaths=dao_champion.death,
                    assists=dao_champion.assist,
                    banned=dao_champion.games_banned,
                    matchesAnalyzed=analyzed_lookup.get((dao_champion.patch, dao_champion.queue_id), 0)
                )
            )
        return app.models.championModels.Champion(
            name=dao_champions[0].ChampionStats_Champion.champion_name or champion_name,
            championStats=result,
            id= dao_champions[0].champion_id
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
            name=name[0],
            tagline=name[1],
            wins=summoner.games_won or 0,
            gamesPlayed=summoner.games_played or 0,
            kills=summoner.kill or 0,
            deaths=summoner.death or 0,
            assists=summoner.assist or 0,
            divisions=self._build_summoner_divisions(summoner),
        )
        logger.debug("get_summoner: returning summoner puuid=%s", result.puuid)
        return result

    def get_matches(self, summoner_name, offset, count, queue_filter: str = QUEUE_FILTER_ALL):
        logger.debug("get_matches: summoner=%s offset=%s count=%s", summoner_name, offset, count)
        summoner = self._get_summoner_row(summoner_name)
        if not summoner:
            logger.info("get_matches: no summoner found=%s", summoner_name)
            return []
        match_query = (
            self.db.query(Match)
            .join(MatchParticipant)
            .filter(MatchParticipant.summoner_id == summoner.id)
        )
        match_query = self._apply_queue_filter_to_match_query(match_query, queue_filter)
        matches = (
            match_query
            .order_by(desc(Match.created), desc(Match.id))
            .offset(offset)
            .limit(count)
            .options(
                joinedload(Match.Match_MatchParticipant)  # load participants for each match
                .joinedload(MatchParticipant.MatchParticipant_Summoner),  # load participant's summoner info
                joinedload(Match.Match_MatchParticipant)
                .joinedload(MatchParticipant.MatchParticipant_Champion),  # load participant's champion info
                joinedload(Match.Match_Queue),
            )
            .all()
        )
        logger.debug("get_matches: retrieved %d matches for summoner=%s", len(matches), summoner_name)

        item_ids = {
            item_id
            for match in matches
            for participant in match.Match_MatchParticipant
            for _, item_id, _ in self._participant_item_slots(participant)
            if item_id
        }
        item_lookup = {
            item.item_id: item
            for item in self.db.query(Item).filter(Item.item_id.in_(item_ids)).all()
        } if item_ids else {}

        result = []
        for match in matches:
            participants_list = []
            ordered_participants = sorted(match.Match_MatchParticipant, key=self._participant_sort_key)
            for p in ordered_participants:
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
                        championImagePath=resolve_champion_image_path(p.champion),
                        position=p.position or "",
                        champion=(p.MatchParticipant_Champion.champion_name if p.MatchParticipant_Champion else "") or "",
                        item0=p.item0 or 0,
                        item1=p.item1 or 0,
                        item2=p.item2 or 0,
                        item3=p.item3 or 0,
                        item4=p.item4 or 0,
                        item5=p.item5 or 0,
                        item6=p.item6 or 0,
                        roleBoundItem=p.role_bound_item or 0,
                        items=self._build_participant_items(p, item_lookup),
                        won=p.won
                    )
                )

            result.append(
                app.models.summonerModels.Match(
                    match_id=match.id,
                    start=datetime.fromtimestamp(match.created),
                    end=datetime.fromtimestamp(match.ended),
                    version=match.patch,
                    queueDescription=self._get_queue_description(match.Match_Queue, match.queue_id),
                    participants=participants_list
                )
            )
        logger.debug("get_matches: returning %d formatted matches for summoner=%s", len(result), summoner_name)
        return result

    def summoner_has_matches(self, summoner_name: str, queue_filter: str = QUEUE_FILTER_ALL) -> bool:
        summoner = self._get_summoner_row(summoner_name)
        if not summoner:
            return False

        match_query = (
            self.db.query(MatchParticipant)
            .join(Match, Match.id == MatchParticipant.match_id)
            .filter(MatchParticipant.summoner_id == summoner.id)
        )
        match_query = self._apply_queue_filter_to_match_query(match_query, queue_filter)
        match = match_query.first()
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

                if match.queueId and not self.queue_exist(match.queueId):
                    logger.debug("add_match: creating placeholder queue row queue_id=%s", match.queueId)
                    self.db.merge(Queue(queue_id=match.queueId, map=None, description=None, notes=None))

                dao_match = Match(
                    id=match_id,
                    created=int(match.start.timestamp()),
                    ended=int(match.end.timestamp()),
                    queue_id=match.queueId,
                    patch=match.version,
                )

                dao_participants = []
                queued_summoner_ids = set()
                queued_champion_ids = set()
                queued_item_ids = set()

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
                                position=(participant.position or "").upper(),
                                won=participant.won,
                                champion=champion_id,
                                item0=participant.item0,
                                item1=participant.item1,
                                item2=participant.item2,
                                item3=participant.item3,
                                item4=participant.item4,
                                item5=participant.item5,
                                item6=participant.item6,
                                role_bound_item=participant.roleBoundItem,
                            ),
                            summoner_name,
                        )
                    )

                self.db.add(dao_match)
                for participant, summoner_name in dao_participants:
                    self.db.add(participant)
                    existing_summoner = self.get_summoner_dao(participant.summoner_id)
                    if participant.summoner_id not in queued_summoner_ids and existing_summoner is None:
                        logger.debug("add_match: creating default summoner id=%s name=%s", participant.summoner_id, summoner_name)
                        self.db.merge(Summoner.create_default(id=participant.summoner_id, name=summoner_name))
                        queued_summoner_ids.add(participant.summoner_id)
                    elif existing_summoner is not None:
                        name, tagline = split_name(summoner_name)
                        if self._has_complete_riot_id(name, tagline) and existing_summoner.summoner_name != summoner_name:
                            logger.debug(
                                "add_match: updating summoner name id=%s old=%s new=%s",
                                participant.summoner_id,
                                existing_summoner.summoner_name,
                                summoner_name,
                            )
                            existing_summoner.summoner_name = summoner_name
                    if participant.champion not in queued_champion_ids and not self.champion_exist(participant.champion):
                        logger.debug("add_match: creating default champion id=%s", participant.champion)
                        self.db.merge(Champion.create_default(id=participant.champion, name=participant.champion))
                        queued_champion_ids.add(participant.champion)
                    for item_id in (
                        participant.item0,
                        participant.item1,
                        participant.item2,
                        participant.item3,
                        participant.item4,
                        participant.item5,
                        participant.item6,
                        participant.role_bound_item,
                    ):
                        if item_id in queued_item_ids or self.item_exist(item_id):
                            continue
                        logger.debug("add_match: creating default item id=%s", item_id)
                        self.db.merge(Item.create_default(item_id=item_id))
                        queued_item_ids.add(item_id)
                self.db.commit()
                logger.info("add_match: successfully added match_id=%s", match_id)
            except SQLAlchemyError:
                logger.error("add_match: failed to add match_id=%s", match_id)
                self.db.rollback()
                raise

            
    def add_ban(self, bans: list[app.models.summonerModels.BanParsed] | app.models.summonerModels.BanParsed):
        """Add one or multiple ban records. Accepts a single BanParsed or a list of them."""
        # normalize to list
        if not isinstance(bans, list):
            bans = [bans]

        dao_bans = []
        for ban in bans:
            dao_bans.append(
                Ban(
                    match_id=ban.match_id,
                    team=ban.team,
                    ban_order=ban.ban_order,
                    champion_key=ban.champion_key,
                )
            )

        try:
            self.db.add_all(dao_bans)
            self.db.commit()
            logger.info("add_ban: added %d ban(s)", len(dao_bans))
        except SQLAlchemyError:
            logger.exception("add_ban: failed to add bans=%s", bans)
            self.db.rollback()
            raise
        return True


    def add_summoner(self, summoner: app.models.summonerModels.Summoner):
        logger.info("add_summoner: adding summoner puuid=%s", summoner.puuid)
        try:
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
        except SQLAlchemyError:
            logger.error("add_summoner: failed to add summoner puuid=%s", getattr(summoner, 'puuid', None))
            self.db.rollback()
            raise
        logger.info("add_summoner: committed summoner puuid=%s", summoner.puuid)

    def replace_summoner_divisions(
        self,
        summoner_id: str,
        divisions: list[app.models.summonerModels.SummonerDivision],
    ):
        logger.info("replace_summoner_divisions: summoner_id=%s count=%s", summoner_id, len(divisions))
        try:
            self.db.query(SummonerQueue).filter(SummonerQueue.summoner_id == summoner_id).delete()

            for division in divisions:
                if division.queueId and not self.queue_exist(division.queueId):
                    logger.debug("replace_summoner_divisions: creating placeholder queue row queue_id=%s", division.queueId)
                    self.db.merge(Queue(queue_id=division.queueId, map=None, description=None, notes=None))

                self.db.add(
                    SummonerQueue(
                        summoner_id=summoner_id,
                        queue_id=division.queueId,
                        tier=division.tier,
                        rank=division.rank,
                        league_points=division.leaguePoints,
                        wins=division.wins,
                        losses=division.losses,
                    )
                )

            self.db.commit()
        except SQLAlchemyError:
            logger.exception("replace_summoner_divisions: failed for summoner_id=%s", summoner_id)
            self.db.rollback()
            raise

    def get_summoner_divisions_dao(self, summoner_id: str) -> list[SummonerQueue]:
        return (
            self.db.query(SummonerQueue)
            .filter(SummonerQueue.summoner_id == summoner_id)
            .options(joinedload(SummonerQueue.SummonerQueue_Queue))
            .all()
        )

    def get_summoner_dao(self, summoner_id) -> Summoner:
        return self.db.query(Summoner).filter(Summoner.id == summoner_id).first()

    def add_champion(self,champion:Champion):
        logger.info("add_champion: merging champion id=%s", getattr(champion, 'id', None))
        try:
            self.db.merge(champion)
            self.db.commit()
        except SQLAlchemyError:
            logger.error("add_champion: failed for champion id=%s", getattr(champion, 'id', None))
            self.db.rollback()
            raise
        logger.info("add_champion: committed champion id=%s", getattr(champion, 'id', None))

    def get_champion_dao(self, champion_id) -> Champion:
        return self.db.query(Champion).filter(Champion.id == champion_id).first()

    def add_item(self, item: Item):
        logger.info("add_item: merging item id=%s", getattr(item, "item_id", None))
        try:
            self.db.merge(item)
            self.db.commit()
        except SQLAlchemyError:
            logger.error("add_item: failed for item id=%s", getattr(item, "item_id", None))
            self.db.rollback()
            raise
        logger.info("add_item: committed item id=%s", getattr(item, "item_id", None))

    def get_item_dao(self, item_id: int) -> Item | None:
        return self.db.query(Item).filter(Item.item_id == item_id).first()

    def get_summoner_champions(self,summoner_id,count) -> list[app.models.summonerModels.SummonerChampion]:
        result = []
        db_favorite_champions = (self.db.query(SummonerChampion)
                                 .join(Champion)
                                 #.filter(Champion.id == SummonerChampion.champion_id)
                                 .filter(SummonerChampion.summoner_id == summoner_id)
                                 .order_by(SummonerChampion.games_played.desc()).
                                 limit(count).all())
        for champion in db_favorite_champions:
            result.append(app.models.summonerModels.SummonerChampion(
                games_played=champion.games_played,
                wins=champion.games_won,
                champion_id=champion.champion_id,
                champion_name=champion.SummonerChampion_Champion.champion_name,
            ))
        return result


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

    def queue_exist(self, queue_id: int) -> bool:
        exists = self.db.query(Queue).filter(Queue.queue_id == queue_id).first() is not None
        logger.debug("queue_exist: queue_id=%s exists=%s", queue_id, exists)
        return exists

    def item_exist(self, item_id: int) -> bool:
        if item_id == 0:
            return True
        exists = self.db.query(Item).filter(Item.item_id == item_id).first() is not None
        logger.debug("item_exist: item_id=%s exists=%s", item_id, exists)
        return exists



