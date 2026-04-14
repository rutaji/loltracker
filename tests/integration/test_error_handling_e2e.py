import pytest


@pytest.mark.integration
def test_summoner_not_found_redirect_when_upstream_fails(app_client, stub_api_client):
    stub_api_client.raise_on_summoner_lookup = True

    response = app_client.get("/summoner/ghost/euw", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/summoner/not-found?name=ghost&tagline=euw"

    not_found_response = app_client.get(response.headers["location"])
    assert not_found_response.status_code == 200
    assert "Summoner Not Found" in not_found_response.text


@pytest.mark.integration
def test_champion_not_found_redirect_and_page(app_client):
    response = app_client.get("/champion/unknownchampion", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/champion/not-found?name=unknownchampion"

    not_found_response = app_client.get(response.headers["location"])
    assert not_found_response.status_code == 200
    assert "Champion Not Found" in not_found_response.text
