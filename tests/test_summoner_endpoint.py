from fastapi.testclient import TestClient

from app.api.config import settings
from app.endpoints import endpoints
from app.main import app

from app.models.summonerModels import Match, MatchPage, Summoner, SummonerChampion, MatchParticipant, SummonerDivision
from app.services.summonerServices import SummonerPageServiceResult, SummonerRefreshServiceResult


client = TestClient(app)


def make_summoner() -> Summoner:
    return Summoner(
        puuid="player-puuid",
        name="test",
        tagline="euw",
        wins=5,
        gamesPlayed=10,
        kills=10,
        deaths=5,
        assists=5,
        divisions=[
            SummonerDivision(
                queueId=420,
                queueDescription="Ranked Solo",
                tier="DIAMOND",
                rank="IV",
                leaguePoints=10,
                wins=21,
                losses=20,
            )
        ],
    )


def make_match_page() -> MatchPage:
    matches = [
        Match(
            match_id=i,
            start=__import__("datetime").datetime.now(),
            end=__import__("datetime").datetime.now(),
            version="14.5",
            queueId=420,
            queueDescription="Ranked Solo",
            participants=[],
        )
        for i in range(settings.matches_per_page)
    ]
    return MatchPage(matches=matches, hasMore=True, nextOffset=settings.matches_per_page)

def make_SummonerChampion() -> list[SummonerChampion]:
    return [SummonerChampion(champion_id="fake_id",champion_name="fake_name",games_played=3,wins=1)]


def make_page_data() -> SummonerPageServiceResult:
    return SummonerPageServiceResult(
        summoner=make_summoner(),
        match_page=make_match_page(),
    )


def test_summoner_page_found(monkeypatch):
    monkeypatch.setattr(endpoints, "load_summoner_page", lambda request, name, tagline, offset, count, dao, queue_filter: make_page_data())
    # Provide a fake DAO so load_favorite_champions can call dao.get_summoner_champions
    class FakeDAO:
        def get_summoner_champions(self, summoner_id, count, queue_filter="all", offset=0):
            return make_SummonerChampion()

    fake_dao = FakeDAO()
    app.dependency_overrides[endpoints.get_dao] = lambda: fake_dao


    response = client.get("/summoner/test/euw")
    app.dependency_overrides.pop(endpoints.get_dao, None)

    assert response.status_code == 200
    assert "test#euw" in response.text
    assert "Recent Matches" in response.text
    assert "Games Shown" in response.text
    assert "Ranked Solo" in response.text


def test_summoner_page_links_match_participants(monkeypatch):
    page_data = make_page_data()
    page_data.match_page.matches[0].participants = [
        MatchParticipant(
            puuid="participant-puuid",
            name="Other Player",
            tagline="EUW",
            kills=1,
            deaths=2,
            assists=3,
            gold=1000,
            team=100,
            position="TOP",
            champion="Ahri",
            items=[],
            won=True,
        )
    ]
    class FakeDAO:
        def get_summoner_champions(self, summoner_id, count, queue_filter="all", offset=0):
            return make_SummonerChampion()

    fake_dao = FakeDAO()
    monkeypatch.setattr(endpoints, "load_summoner_page", lambda request, name, tagline, offset, count, dao, queue_filter: page_data)
    app.dependency_overrides[endpoints.get_dao] = lambda: fake_dao

    response = client.get("/summoner/test/euw")

    assert response.status_code == 200
    assert 'href="/summoner/Other%20Player/EUW"' in response.text


def test_summoner_page_renders_item_icons_in_match_details(monkeypatch):
    page_data = make_page_data()
    page_data.match_page.matches[0].participants = [
        MatchParticipant(
            puuid="participant-puuid",
            name="Other Player",
            tagline="EUW",
            kills=1,
            deaths=2,
            assists=3,
            gold=1000,
            team=100,
            position="TOP",
            champion="Ahri",
            items=[
                {
                    "id": 1055,
                    "name": "Doran's Blade",
                    "description": "Starter item",
                    "slot": "item0",
                    "isRoleBound": False,
                }
            ],
            won=True,
        )
    ]

    class FakeDAO:
        def get_summoner_champions(self, summoner_id, count, queue_filter="all", offset=0):
            return make_SummonerChampion()

    fake_dao = FakeDAO()
    monkeypatch.setattr(endpoints, "load_summoner_page", lambda request, name, tagline, offset, count, dao, queue_filter: page_data)
    app.dependency_overrides[endpoints.get_dao] = lambda: fake_dao

    response = client.get("/summoner/test/euw")

    assert response.status_code == 200
    assert '/static/img/items/1055.png' in response.text


def test_summoner_page_not_found_redirects(monkeypatch):
    monkeypatch.setattr(
        endpoints,
        "load_summoner_page",
        lambda request, name, tagline, offset, count, dao, queue_filter: SummonerPageServiceResult(summoner=None, match_page=None),
    )
    class FakeDAO:
        def get_summoner_champions(self, summoner_id, count, queue_filter="all", offset=0):
            return make_SummonerChampion()

    fake_dao = FakeDAO()
    app.dependency_overrides[endpoints.get_dao] = lambda: fake_dao
    app.dependency_overrides.pop(endpoints.get_dao, None)

    response = client.get("/summoner/nonexistent/euw", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/summoner/not-found?name=nonexistent&tagline=euw"


def test_summoner_matches_ajax_response(monkeypatch):
    monkeypatch.setattr(endpoints, "load_summoner_page", lambda request, name, tagline, offset, count, dao, queue_filter: make_page_data())

    class FakeDAO:
        def get_summoner_champions(self, summoner_id, count, queue_filter="all", offset=0):
            return make_SummonerChampion()

    fake_dao = FakeDAO()
    from app.main import app as _app
    _app.dependency_overrides[endpoints.get_dao] = lambda: fake_dao

    response = client.get("/summoner/test/euw?offset=0&ajax=true")
    assert response.status_code == 200

    data = response.json()
    assert len(data["matches"]) == settings.matches_per_page
    assert data["nextOffset"] == settings.matches_per_page
    assert data["matches"][0]["queueDescription"] == "Ranked Solo"
    assert "queueId" not in data["matches"][0]


def test_summoner_queue_filters_are_forwarded_independently(monkeypatch):
    captured = {}

    def fake_load_summoner_page(request, name, tagline, offset, count, dao, queue_filter):
        captured["match_queue_filter"] = queue_filter
        return make_page_data()

    monkeypatch.setattr(endpoints, "load_summoner_page", fake_load_summoner_page)

    class FakeDAO:
        def get_summoner_champions(self, summoner_id, count, queue_filter="all", offset=0):
            captured["favorite_queue_filter"] = queue_filter
            return make_SummonerChampion()

    app.dependency_overrides[endpoints.get_dao] = lambda: FakeDAO()

    response = client.get("/summoner/test/euw?match_queue_filter=aram&favorite_queue_filter=ranked_flex")
    app.dependency_overrides.pop(endpoints.get_dao, None)

    assert response.status_code == 200
    assert captured["match_queue_filter"] == "aram"
    assert captured["favorite_queue_filter"] == "ranked_flex"
    assert 'id="favorite-queue-filter"' in response.text
    assert 'id="match-queue-filter"' in response.text
    assert response.text.count('<option value="all"') == 1
    assert response.text.count('<option value="other"') == 1


def test_summoner_favorite_champions_ajax_response(monkeypatch):
    captured = {}

    class FakeDAO:
        def get_summoner(self, summoner_name):
            return make_summoner()

        def get_summoner_champions(self, summoner_id, count, queue_filter="all", offset=0):
            captured["summoner_id"] = summoner_id
            captured["count"] = count
            captured["queue_filter"] = queue_filter
            captured["offset"] = offset
            return [
                SummonerChampion(
                    champion_id=f"champion-{index}",
                    champion_name=f"Champion {index}",
                    queueDescription="Ranked Solo",
                    games_played=10 - index,
                    wins=5,
                    kills=20,
                    deaths=5,
                    assists=10,
                )
                for index in range(count)
            ]

    app.dependency_overrides[endpoints.get_dao] = lambda: FakeDAO()

    response = client.get("/summoner/test/euw/favorite-champions?offset=5&favorite_queue_filter=ranked_solo")
    app.dependency_overrides.pop(endpoints.get_dao, None)

    assert response.status_code == 200
    data = response.json()
    assert len(data["champions"]) == settings.favorite_champion_page_size
    assert data["hasMore"] is True
    assert data["nextOffset"] == 10
    assert data["champions"][0]["queueDescription"] == "Ranked Solo"
    assert "queueId" not in data["champions"][0]
    assert captured == {
        "summoner_id": "player-puuid",
        "count": settings.favorite_champion_page_size + 1,
        "queue_filter": "ranked_solo",
        "offset": 5,
    }


def test_not_found_page_displays_searched_summoner():
    response = client.get("/summoner/not-found?name=missing&tagline=euw")
    assert response.status_code == 200
    assert "Summoner Not Found" in response.text
    assert "missing#euw" in response.text


def test_summoner_refresh_returns_json(monkeypatch):
    monkeypatch.setattr(
        endpoints,
        "refresh_summoner_matches_service",
        lambda request, name, tagline, dao: SummonerRefreshServiceResult(
            summoner=make_summoner(),
            inserted_count=2,
            failed_count=1,
        ),
    )

    response = client.post("/summoner/test/euw/refresh")
    assert response.status_code == 200
    assert response.json() == {
        "insertedCount": 2,
        "failedCount": 1,
        "summonerName": "test",
        "summonerTagline": "euw",
    }
