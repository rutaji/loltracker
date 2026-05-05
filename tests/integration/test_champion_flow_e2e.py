import pytest


@pytest.mark.integration
def test_search_redirects_to_champion(app_client):
    response = app_client.post(
        "/",
        data={"summoner_name": "", "summoner_tagline": "", "champion_name": "ahri"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/champion/ahri"


@pytest.mark.integration
def test_champion_html_and_ajax_version_filter(app_client, seed_champion_stats_data):
    page_response = app_client.get("/champion/ahri?version=14.5")

    assert page_response.status_code == 200
    assert "Champion Breakdown" in page_response.text
    assert "ahri" in page_response.text.lower()

    ajax_response = app_client.get("/champion/ahri?version=14.5&ajax=true")

    assert ajax_response.status_code == 200
    payload = ajax_response.json()

    assert payload["name"] == "ahri"
    assert len(payload["championStats"]) == 1
    assert payload["championStats"][0]["version"] == "14.5"
