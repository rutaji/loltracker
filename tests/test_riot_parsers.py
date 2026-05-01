from app.riot.riotParsers import MatchParser, MatchParticipantParser, SummonerParser


def test_match_participant_parser_maps_riot_fields():
    participant_data = {
        "puuid": "player-puuid",
        "riotIdGameName": "PlayerOne",
        "riotIdTagline": "EUW",
        "kills": 8,
        "deaths": 2,
        "assists": 10,
        "goldEarned": 14500,
        "teamId": 100,
        "teamPosition": "MIDDLE",
        "championName": "Ahri",
        "win": True,
    }

    participant = MatchParticipantParser.parse(participant_data)

    assert participant.puuid == "player-puuid"
    assert participant.name == "PlayerOne"
    assert participant.tagline == "EUW"
    assert participant.kills == 8
    assert participant.deaths == 2
    assert participant.assists == 10
    assert participant.gold == 14500
    assert participant.team == 100
    assert participant.position == "MIDDLE"
    assert participant.champion == "Ahri"
    assert participant.won is True


def test_match_parser_maps_match_and_participants():
    match_data = {
        "metadata": {
            "matchId": "EUW1_123456789",
        },
        "info": {
            "gameStartTimestamp": 1710000000000,
            "gameEndTimestamp": 1710002100000,
            "gameVersion": "15.7.123.4567",
            "queueId": 420,
            "participants": [
                {
                    "puuid": "player-puuid",
                    "riotIdGameName": "PlayerOne",
                    "riotIdTagline": "EUW",
                    "kills": 8,
                    "deaths": 2,
                    "assists": 10,
                    "goldEarned": 14500,
                    "teamId": 100,
                    "teamPosition": "MIDDLE",
                    "championName": "Ahri",
                    "win": True,
                }
            ],
        },
    }

    match = MatchParser.parse(match_data)

    assert match.match_id == "EUW1_123456789"
    assert match.version == "15.7"
    assert match.queueId == 420
    assert len(match.participants) == 1
    assert match.participants[0].name == "PlayerOne"
    assert match.participants[0].puuid == "player-puuid"
    assert match.participants[0].position == "MIDDLE"


def test_match_parser_keeps_short_version_untouched():
    match_data = {
        "metadata": {"matchId": "EUW1_123"},
        "info": {
            "gameStartTimestamp": 1710000000000,
            "gameEndTimestamp": 1710002100000,
            "gameVersion": "15.8",
            "queueId": 440,
            "participants": [],
        },
    }

    match = MatchParser.parse(match_data)

    assert match.version == "15.8"


def test_match_participant_parser_treats_invalid_position_as_unknown():
    participant = MatchParticipantParser.parse(
        {
            "puuid": "player-puuid",
            "riotIdGameName": "PlayerOne",
            "riotIdTagline": "EUW",
            "teamPosition": "",
            "individualPosition": "INVALID",
        }
    )

    assert participant.position == ""


def test_summoner_parser_maps_account_data():
    account_data = {
        "puuid": "player-puuid",
        "gameName": "PlayerOne",
        "tagLine": "EUW",
    }

    summoner = SummonerParser.parse(account_data)

    assert summoner.puuid == "player-puuid"
    assert summoner.name == "PlayerOne"
    assert summoner.tagline == "EUW"
    assert summoner.gamesPlayed == 0
    assert summoner.wins == 0
    assert summoner.kills == 0
    assert summoner.deaths == 0
    assert summoner.assists == 0
