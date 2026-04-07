from datetime import datetime

from sqlalchemy.orm import joinedload

import app.models.championModels
import app.models.summonerModels
from app.database.database import SessionLocal
from app.database.models import Match, Summoner, MatchParticipant, Champion, ChampionStats, MatchesAnalyzed


class DAO:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def get_dao():
        return DAO(SessionLocal())

    def get_champion(self,champion_name :str,patch :list[str]):
        dao_champions = (
            self.db.query(ChampionStats)
            .join(Champion)
            .filter(Champion.champion_name.ilike(champion_name))
            .filter(ChampionStats.patch.in_(patch))
            .all()
        )
        if not dao_champions:
            return None

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
        return app.models.championModels.Champion(
            name=dao_champions[0].ChampionStats_Champion.champion_name or champion_name,
            championStats=result,
        )

    def get_summoner(self,summoner_name:str):
        summoner = self.db.query(Summoner).filter(Summoner.summoner_name == summoner_name).first()
        if summoner is None:
            return None

        name = self.splitname(summoner.summoner_name)
        return app.models.summonerModels.Summoner(
            puuid=summoner.id,
            name = name[0],
            tagline = name[1],
            wins = summoner.games_won,
            gamesPlayed = summoner.games_played,
            kills = 0,
            deaths = 0,
            assists = 0,

        )

    def get_matches(self, summoner_name, offset, count):
        summoner = self.db.query(Summoner).filter(Summoner.summoner_name == summoner_name).first()
        if not summoner:
            return []
        matches = (
            self.db.query(Match)
            .join(MatchParticipant)
            .filter(MatchParticipant.summoner_id == summoner.id)
            .options(
                joinedload(Match.Match_MatchParticipant)  # load participants for each match
                .joinedload(MatchParticipant.MatchParticipant_Summoner),  # load participant's summoner info
                joinedload(Match.Match_MatchParticipant)
                .joinedload(MatchParticipant.MatchParticipant_Champion)  # load participant's champion info
            )
            .all()
        )
        result = []
        for match in matches:
            participants_list = []
            for p in match.Match_MatchParticipant:
                summoner_name = p.MatchParticipant_Summoner.summoner_name if p.MatchParticipant_Summoner else ""
                name = self.splitname(summoner_name)
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

        return result

    #todo move
    def splitname(self,name):
        if not name:
            return ["", ""]

        parts = name.split('#', 1)
        if len(parts) == 1:
            return [parts[0], ""]

        return parts









    def add_match(self, match: app.models.summonerModels.Match):
            match_id = str(match.match_id)
            if self.match_exist(match_id):
                return False

            dao_match = Match(
                id=match_id,
                created=int(match.start.timestamp()),
                ended=int(match.end.timestamp()),
                gametype=match.mode,
                patch=match.version,
            )

            dao_participants = []

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
                if not self.summoner_exist(participant.summoner_id):
                    self.db.add(Summoner.create_default(id=participant.summoner_id, name=summoner_name))
                if not self.champion_exist(participant.champion):
                    self.db.add(Champion.create_default(id=participant.champion, name=participant.champion))
            self.db.commit()

    def add_summoner(self, summoner: app.models.summonerModels.Summoner):
            dao_summoner = Summoner(
                id=summoner.puuid,
                summoner_name=f"{summoner.name}#{summoner.tagline}",
                games_played=summoner.gamesPlayed,
                games_won=summoner.wins,
            )
            self.db.merge(dao_summoner)
            self.db.commit()

    def get_summoner_dao(self, summoner_id) -> Summoner:
        return self.db.query(Summoner).filter(Summoner.id == summoner_id).first()

    def add_champion(self,champion:Champion):
            self.db.merge(champion)
            self.db.commit()

    def get_champion_dao(self, champion_id) -> Champion:
        return self.db.query(Champion).filter(Champion.id == champion_id).first()




    def match_exist(self,id) -> bool:
        match = self.db.query(Match).filter(Match.id == id).first()
        return match is not None

    def summoner_exist(self,id) -> bool:
        summoner = self.db.query(Summoner).filter(Summoner.id == id).first()
        return summoner is not None

    def champion_exist(self,id) -> bool:
        champion = self.db.query(Champion).filter(Champion.id == id).first()
        return champion is not None



