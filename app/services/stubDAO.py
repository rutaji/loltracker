from app.models.summonerModels import Summoner, Match, MatchParticipant
from datetime import datetime

class stubDAO:

    def __init__(self):
        self.matches = [
            Match(
                match_id=i,
                start=datetime.fromisoformat(f"2026-03-0{i}T18:00:00"),
                end=datetime.fromisoformat(f"2026-03-0{i}T18:35:00"),
                version="14.5",
                mode="Ranked Solo",
                participants=[
                    MatchParticipant(
                        name="test",
                        kills=10+i,
                        deaths=2,
                        assists=5,
                        gold=12000+i*100,
                        team=1,
                        champion="Ahri",
                        won=True
                    ),
                    MatchParticipant(
                        name="enemy",
                        kills=3,
                        deaths=8,
                        assists=4,
                        gold=9000,
                        team=2,
                        champion="Zed",
                        won=False
                    )
                ]
            )
            for i in range(1, 9)
        ]

    def get_summoner(self, name: str, tagline: str):
        if name == "test":
            return Summoner(
                name="test",
                tagline=tagline,
                wins=53,
                losses=47,
                kills=300,
                deaths=100,
                assists=500
            )
        return None

    def get_matches(self, name: str, tagline: str, offset: int, count: int):
        return self.matches[offset:offset+count]