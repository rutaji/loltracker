from app.riot.riotParsers import MatchParser, MatchParticipantParser, SummonerParser, SummonerDivisionParser


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
        "item0": 1055,
        "item1": 3006,
        "item2": 3031,
        "item3": 3094,
        "item4": 3036,
        "item5": 2055,
        "item6": 3363,
        "roleBoundItem": 0,
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
    assert participant.item0 == 1055
    assert participant.item6 == 3363
    assert participant.roleBoundItem == 0
    assert participant.items == []
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


def test_match_parser_maps_bans_with_pick_turn():
    bans = MatchParser.parse_bans(
        {
            "metadata": {"matchId": "EUW1_123"},
            "info": {
                "teams": [
                    {
                        "teamId": 100,
                        "bans": [
                            {"championId": 799, "pickTurn": 4},
                            {"championId": 799, "pickTurn": 13},
                        ],
                    },
                ],
            },
        }
    )

    assert [(ban.match_id, ban.team, ban.ban_order, ban.champion_key) for ban in bans] == [
        ("EUW1_123", 100, 4, 799),
        ("EUW1_123", 100, 13, 799),
    ]


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


def test_summoner_division_parser_maps_ranked_entries():
    entries = [
        {
            "queueType": "RANKED_FLEX_SR",
            "tier": "EMERALD",
            "rank": "I",
            "leaguePoints": 96,
            "wins": 22,
            "losses": 33,
        },
        {
            "queueType": "RANKED_SOLO_5x5",
            "tier": "DIAMOND",
            "rank": "IV",
            "leaguePoints": 10,
            "wins": 21,
            "losses": 20,
        },
    ]

    divisions = SummonerDivisionParser.parse_many(entries)

    assert [(division.queueId, division.tier, division.rank) for division in divisions] == [
        (440, "EMERALD", "I"),
        (420, "DIAMOND", "IV"),
    ]


def test_summoner_division_parser_adds_unranked_placeholders_for_missing_queues():
    entries = [
        {
            "queueType": "RANKED_SOLO_5x5",
            "tier": "DIAMOND",
            "rank": "IV",
            "leaguePoints": 10,
            "wins": 21,
            "losses": 20,
        },
    ]

    divisions = SummonerDivisionParser.parse_many(entries)

    assert [(division.queueId, division.tier, division.rank) for division in divisions] == [
        (420, "DIAMOND", "IV"),
        (440, "UNRANKED", ""),
    ]
