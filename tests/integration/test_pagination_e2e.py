import pytest

from app.api.config import settings


@pytest.mark.integration
def test_partial_match_page_sets_has_more_false(app_client, seed_partial_matches_data):
    response = app_client.get("/summoner/partial/euw?offset=0&ajax=true")

    assert response.status_code == 200
    payload = response.json()

    assert len(payload["matches"]) == 2
    assert payload["hasMore"] is False
    assert payload["nextOffset"] == settings.matches_per_page
