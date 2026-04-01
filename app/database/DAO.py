from app.database.database import SessionLocal
from app.database.models import Match, Summoner, MatchParticipant, Champion


class DAO:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def get_dao():
        return DAO(SessionLocal())





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

    def get_summoner(self, summoner_id) -> Summoner:
        return self.db.query(Summoner).filter(Summoner.id == summoner_id).first()

    def add_champion(self,champion:Champion):
            self.db.merge(champion)
            self.db.commit()

    def get_champion(self, champion_id) -> Champion:
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



