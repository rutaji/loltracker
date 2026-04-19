import pytest

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
def test_cache_miss_fetches_remote_once_and_persists(app_client, stub_api_client):
    first_response = app_client.get("/summoner/remoteplayer/euw?offset=0&ajax=true")

    assert first_response.status_code == 200
    first_payload = first_response.json()
    assert len(first_payload["matches"]) == 4
    assert first_payload["hasMore"] is False

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
