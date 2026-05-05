from app.utils.champion_kit import resolve_champion_kit


def test_resolve_champion_kit_loads_passive_and_spells():
    kit = resolve_champion_kit("Aatrox")

    assert kit is not None
    assert kit["championName"] == "Aatrox"
    assert kit["passive"] is not None
    assert kit["passive"]["name"]
    assert kit["passive"]["icon"].startswith("/static/img/passives/")
    assert len(kit["spells"]) == 4
    assert kit["spells"][0]["slot"] == "Q"
    assert kit["spells"][0]["icon"].startswith("/static/img/spells/")
