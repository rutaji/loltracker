import pytest

from app.database.models import Item

from app.api.config import settings


@pytest.mark.integration
def test_search_redirects_to_summoner(app_client):
    response = app_client.post(
        "/",
        data={"summoner_name": "cached", "summoner_tagline": "euw", "champion_name": ""},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/summoner/cached/euw"


@pytest.mark.integration
def test_cached_summoner_flow_html_and_ajax(app_client, seed_cached_summoner_data, stub_api_client):
    response = app_client.get("/summoner/cached/euw")

    assert response.status_code == 200
    assert "cached#euw" in response.text
    assert "Recent Matches" in response.text

    ajax_response = app_client.get("/summoner/cached/euw?offset=0&ajax=true")

    assert ajax_response.status_code == 200
    payload = ajax_response.json()
    assert len(payload["matches"]) == 3
    assert payload["hasMore"] is False
    assert payload["nextOffset"] == settings.matches_per_page

    assert stub_api_client.get_summoner_calls == 0
    assert stub_api_client.get_match_ids_calls == 0
    assert stub_api_client.get_match_info_calls == 0


@pytest.mark.integration
def test_cached_summoner_flow_filters_by_queue(app_client, seed_cached_summoner_data):
    aram_response = app_client.get("/summoner/cached/euw?offset=0&ajax=true&match_queue_filter=aram")
    other_response = app_client.get("/summoner/cached/euw?offset=0&ajax=true&match_queue_filter=other")

    assert aram_response.status_code == 200
    assert other_response.status_code == 200

    aram_payload = aram_response.json()
    other_payload = other_response.json()

    assert [match["queueDescription"] for match in aram_payload["matches"]] == ["ARAM"]
    assert [match["queueDescription"] for match in other_payload["matches"]] == ["Arena"]
    assert aram_payload["hasMore"] is False
    assert other_payload["hasMore"] is False


@pytest.mark.integration
def test_cached_summoner_lookup_is_case_insensitive(app_client, seed_cached_summoner_data, stub_api_client):
    response = app_client.get("/summoner/CACHED/EUW")

    assert response.status_code == 200
    assert "cached#euw" in response.text
    assert stub_api_client.get_summoner_calls == 0
    assert stub_api_client.get_match_ids_calls == 0
    assert stub_api_client.get_match_info_calls == 0


@pytest.mark.integration
def test_cache_miss_fetches_remote_once_and_persists(app_client, stub_api_client, db_session):
    for match_info in stub_api_client._match_infos.values():
        participant = match_info["info"]["participants"][0]
        participant["item0"] = 1055
        participant["item1"] = 3006
        participant["item6"] = 3363
        participant["roleBoundItem"] = 0
    db_session.add_all(
        [
            Item(item_id=1055, name="Doran's Blade", description="Starter item"),
            Item(item_id=3006, name="Berserker's Greaves", description="Boots"),
            Item(item_id=3363, name="Farsight Alteration", description="Trinket"),
        ]
    )
    db_session.commit()

    first_response = app_client.get("/summoner/remoteplayer/euw?offset=0&ajax=true")

    assert first_response.status_code == 200
    first_payload = first_response.json()
    assert len(first_payload["matches"]) == 4
    assert first_payload["hasMore"] is False
    assert first_payload["matches"][0]["participants"][0]["items"][0]["id"] == 1055
    assert first_payload["matches"][0]["participants"][0]["items"][0]["name"] == "Doran's Blade"

    first_calls = (
        stub_api_client.get_summoner_calls,
        stub_api_client.get_match_ids_calls,
        stub_api_client.get_match_info_calls,
    )

    second_response = app_client.get("/summoner/remoteplayer/euw?offset=0&ajax=true")

    assert second_response.status_code == 200
    second_payload = second_response.json()
    assert len(second_payload["matches"]) == 4

    second_calls = (
        stub_api_client.get_summoner_calls,
        stub_api_client.get_match_ids_calls,
        stub_api_client.get_match_info_calls,
    )

    assert first_calls == second_calls


@pytest.mark.integration
def test_manual_refresh_skips_existing_matches(app_client, stub_api_client):
    first_response = app_client.get("/summoner/remoteplayer/euw?offset=0&ajax=true")
    assert first_response.status_code == 200

    match_info_calls_before_refresh = stub_api_client.get_match_info_calls
    match_id_calls_before_refresh = stub_api_client.get_match_ids_calls

    refresh_response = app_client.post("/summoner/remoteplayer/euw/refresh")

    assert refresh_response.status_code == 200
    assert refresh_response.json() == {
        "insertedCount": 0,
        "failedCount": 0,
        "summonerName": "remoteplayer",
        "summonerTagline": "euw",
    }
    assert stub_api_client.get_match_ids_calls == match_id_calls_before_refresh + 1
    assert stub_api_client.get_match_info_calls == match_info_calls_before_refresh
