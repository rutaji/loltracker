from datetime import datetime
from unittest.mock import patch

from app.database.database import SessionLocal
from app.database import models
from app.database.models import Summoner,Champion,Match,MatchParticipant

session = SessionLocal()

summoners = [
        Summoner.create_default(id="s1", name="Faker#korea"),
        Summoner.create_default(id="s2", name="Doublelift#12345"),
        Summoner.create_default(id="s3", name="Uzi#eune"),
    ]
session.add_all(summoners)

# --- Create Champions ---
champions = [
        Champion.create_default(id="c1", name="Ahri"),
        Champion.create_default(id="c2", name="Yasuo"),
        Champion.create_default(id="c3", name="Lux"),
    ]
session.add_all(champions)

# --- Create Matches ---
now = int(datetime.now().timestamp())
matches = [
    Match(id="m1", created=1775331054, ended=1775331054 + 1200, gametype="Ranked", patch="14.4"),
    Match(id="m2", created=1775331054 + 3600, ended=1775331054 + 4800, gametype="Normal", patch="14.5"),
]
session.add_all(matches)

# --- Create MatchParticipants ---
participants = [
        # Match 1
        MatchParticipant(summoner_id="s1", match_id="m1", kill=10, assist=5, death=2, gold=15000, team=100, won=True, champion="c1"),
        MatchParticipant(summoner_id="s2", match_id="m1", kill=8, assist=7, death=4, gold=14000, team=100, won=True, champion="c2"),
        MatchParticipant(summoner_id="s3", match_id="m1", kill=5, assist=10, death=6, gold=13000, team=200, won=False, champion="c3"),
        # Match 2
        MatchParticipant(summoner_id="s1", match_id="m2", kill=7, assist=8, death=3, gold=14500, team=200, won=False, champion="c2"),
        MatchParticipant(summoner_id="s2", match_id="m2", kill=12, assist=4, death=5, gold=15500, team=100, won=True, champion="c3"),
        MatchParticipant(summoner_id="s3", match_id="m2", kill=3, assist=6, death=7, gold=12000, team=200, won=False, champion="c1"),
    ]
session.add_all(participants)

session.commit()
session.close()

print("Seed data inserted")