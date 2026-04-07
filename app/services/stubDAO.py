from app.models.summonerModels import Summoner, Match, MatchParticipant
from app.models.championModels import Champion, ChampionStats
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
                        puuid="s1",
                        name="test",
                        tagline="euw",
                        kills=10+i,
                        deaths=2,
                        assists=5,
                        gold=12000+i*100,
                        team=1,
                        champion="Ahri",
                        won=True
                    ),
                    MatchParticipant(
                        puuid="s2",
                        name="enemy",
                        tagline="euw",
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

        self.champions = {
            "ahri": Champion(
                name="Ahri",
                championStats=[
                    ChampionStats(
                        version="14.5",
                        gamemode="Ranked Solo",
                        wins=520,
                        gamesPlayed=1000,
                        kills=7200,
                        deaths=4100,
                        assists=6900,
                        banned=230,
                        matchesAnalyzed=12000
                    ),
                    ChampionStats(
                        version="14.5",
                        gamemode="ARAM",
                        wins=310,
                        gamesPlayed=600,
                        kills=4500,
                        deaths=3000,
                        assists=6100,
                        banned=0,
                        matchesAnalyzed=7000
                    ),
                    ChampionStats(
                        version="14.4",
                        gamemode="Ranked Solo",
                        wins=490,
                        gamesPlayed=1000,
                        kills=6900,
                        deaths=4200,
                        assists=6500,
                        banned=260,
                        matchesAnalyzed=11500
                    )
                ]
            ),

            "zed": Champion(
                name="Zed",
                championStats=[
                    ChampionStats(
                        version="14.5",
                        gamemode="Ranked Solo",
                        wins=610,
                        gamesPlayed=900,
                        kills=8800,
                        deaths=4200,
                        assists=3100,
                        banned=800,
                        matchesAnalyzed=1200
                    )
                ]
            )
        }

    def get_summoner(self, name: str, tagline: str):
        if name == "test":
            return Summoner(
                puuid="s1",
                name="test",
                tagline=tagline,
                wins=53,
                gamesPlayed=100,
                kills=300,
                deaths=100,
                assists=500
            )
        return None

    def get_matches(self, name: str, tagline: str, offset: int, count: int):
        return self.matches[offset:offset+count]
    
    def get_champion(self, name: str, version: str):
        champ = self.champions.get(name.lower())

        if not champ:
            return None

        filtered_stats = [
            stat for stat in champ.championStats
            if stat.version == version
        ]

        return Champion(
            name=champ.name,
            championStats=filtered_stats
        )
