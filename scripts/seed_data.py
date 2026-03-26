from unittest.mock import patch

from app.database.database import SessionLocal
from app.database import models

db = SessionLocal()

summoner = models.Summoner(
    id="001",
    summoner_name="test#eune",
    games_won=0,
    games_played=0
)
match = models.Match(
    id="m001",
    created=1773420397,
    ended=1773510436,
    gametype="summoners rift",
    patch="26.5"
)
match_participants = [
    models.MatchParticipant(
        summoner_id="asddas1",
        match_id="m001",
        kill=1,
        assist=2,
        death=3,
        gold=8000,
        team=1,
        won=0,
        championship="Lux",
    ),
    models.MatchParticipant(
        summoner_id="asttddas2",
        match_id="m001",
        kill=1,
        assist=2,
        death=3,
        gold=8090,
        team=1,
        won=0,
        championship="Zed",
    ),
models.MatchParticipant(
        summoner_id="asddas3",
        match_id="m001",
        kill=1,
        assist=2,
        death=3,
        gold=8000,
        team=1,
        won=0,
        championship="Lux"
    ),
models.MatchParticipant(
        summoner_id="asddas4",
        match_id="m001",
        kill=1,
        assist=2,
        death=3,
        gold=8000,
        team=1,
        won=0,
        championship="Yone"
    ),
models.MatchParticipant(
        summoner_id="asddas5",
        match_id="m001",
        kill=1,
        assist=2,
        death=3,
        gold=8000,
        team=1,
        won=0,
        championship="Pyke"
    ),
models.MatchParticipant(
        summoner_id="asddas6",
        match_id="m001",
        kill=1,
        assist=2,
        death=3,
        gold=8000,
        team=0,
        won=1,
        championship="Garen"
    ),
models.MatchParticipant(
        summoner_id="feeder7",
        match_id="m001",
        kill=0,
        assist=2,
        death=80,
        gold=8000,
        team=0,
        won=1,
        championship="Twitch"
),
models.MatchParticipant(
        summoner_id="001",
        match_id="m001",
        kill=11,
        assist=2,
        death=3,
        gold=8000,
        team=0,
        won=1,
        championship="Vi"
    ),
models.MatchParticipant(
        summoner_id="saddas9",
        match_id="m001",
        kill=15,
        assist=2,
        death=0,
        gold=900,
        team=0,
        won=1,
        championship="Evelyn"
),
models.MatchParticipant(
        summoner_id="fghhg10",
        match_id="m001",
        kill=0,
        assist=11,
        death=3,
        gold=1100,
        team=0,
        won=1,
        championship="Aatrox"
),]


db.add(summoner)
db.add(match)
db.add_all(match_participants)
db.commit()
db.close()

print("Seed data inserted")