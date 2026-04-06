from datetime import datetime

from sqlalchemy.orm import joinedload

import app.models.championModels
from app.database.database import SessionLocal
from app.database.models import Match, Summoner, MatchParticipant, Champion, ChampionStats, MatchesAnalyzed


class DAO:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def get_dao():
        return DAO(SessionLocal())

    def get_champion(self,champion_name :str,patch :list[str]):
        dao_champions = self.db.query(ChampionStats).join(Champion).filter(Champion.champion_name == champion_name).filter(ChampionStats.patch.in_(patch)).all()
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
        return result

    def get_summoner(self,summoner_name:str):
        summoner = self.db.query(Summoner).filter(Summoner.summoner_name == summoner_name).first()
        name = self.splitname(summoner.name)
        return app.models.summonerModels.Summoner(
            name = name[0],
            tagline = name[1],
            wins = summoner.games_won,
            gamesPlayed = summoner.games_played,
            kills = summoner.kill,
            deaths = summoner.death,
            assists = summoner.assist,

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
                name = self.splitname(p.MatchParticipant_Summoner.summoner_name)
                participants_list.append(
                    app.models.summonerModels.MatchParticipant(
                        name=name[0] or "",
                        tagline=name[1] or "",  # if your Summoner model has a tagline field, use it
                        kills=p.kill,
                        deaths=p.death,
                        assists=p.assist,
                        gold=p.gold,
                        team=p.team,
                        champion=p.MatchParticipant_Champion.champion_name,
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
        return name.split('#')









    def add_match(self, match:Match, participants:list[MatchParticipant]):
            if self.match_exist(match.id):
                return False
            self.db.add(match)
            for participant in participants:
                self.db.add(participant)
                if not self.summoner_exist(participant.summoner_id):
                    self.db.add(Summoner.create_default(id=participant.summoner_id))
                if not self.champion_exist(participant.champion):
                    self.db.add(Champion.create_default(id=participant.champion))
            self.db.commit()

    def add_summoner(self, summoner:Summoner):
            self.db.add(summoner)
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



