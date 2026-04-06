from app.riot.riotParsers import MatchParser, MatchParticipantParser, SummonerParser


def test_match_participant_parser_maps_riot_fields():
    participant_data = {
        "riotIdGameName": "PlayerOne",
        "riotIdTagline": "EUW",
        "kills": 8,
        "deaths": 2,
        "assists": 10,
        "goldEarned": 14500,
        "teamId": 100,
        "championName": "Ahri",
        "win": True,
    }

    participant = MatchParticipantParser.parse(participant_data)

    assert participant.name == "PlayerOne"
    assert participant.tagline == "EUW"
    assert participant.kills == 8
    assert participant.deaths == 2
    assert participant.assists == 10
    assert participant.gold == 14500
    assert participant.team == 100
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
            "gameMode": "CLASSIC",
            "participants": [
                {
                    "riotIdGameName": "PlayerOne",
                    "riotIdTagline": "EUW",
                    "kills": 8,
                    "deaths": 2,
                    "assists": 10,
                    "goldEarned": 14500,
                    "teamId": 100,
                    "championName": "Ahri",
                    "win": True,
                }
            ],
        },
    }

    match = MatchParser.parse(match_data)

    assert match.match_id == "EUW1_123456789"
    assert match.version == "15.7.123.4567"
    assert match.mode == "CLASSIC"
    assert len(match.participants) == 1
    assert match.participants[0].name == "PlayerOne"


def test_summoner_parser_aggregates_player_stats_from_matches():
    account_data = {
        "puuid": "player-puuid",
        "gameName": "PlayerOne",
        "tagLine": "EUW",
    }
    matches_data = [
        {
            "info": {
                "participants": [
                    {
                        "puuid": "player-puuid",
                        "kills": 10,
                        "deaths": 2,
                        "assists": 5,
                        "win": True,
                    }
                ]
            }
        },
        {
            "info": {
                "participants": [
                    {
                        "puuid": "player-puuid",
                        "kills": 3,
                        "deaths": 7,
                        "assists": 9,
                        "win": False,
                    }
                ]
            }
        },
        {
            "info": {
                "participants": [
                    {
                        "puuid": "someone-else",
                        "kills": 99,
                        "deaths": 0,
                        "assists": 99,
                        "win": True,
                    }
                ]
            }
        },
    ]

    summoner = SummonerParser.parse(account_data, matches_data)

    assert summoner.name == "PlayerOne"
    assert summoner.tagline == "EUW"
    assert summoner.gamesPlayed == 2
    assert summoner.wins == 1
    assert summoner.kills == 13
    assert summoner.deaths == 9
    assert summoner.assists == 14
