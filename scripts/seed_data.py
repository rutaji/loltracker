from datetime import datetime

from app.database.database import SessionLocal
from app.database.models import Champion, Match, MatchParticipant, Summoner, ChampionStats, MatchesAnalyzed


def add_if_missing(session, model, identity, instance):
    if session.get(model, identity) is None:
        session.add(instance)


def main():
    session = SessionLocal()

    try:
        summoners = [
            Summoner.create_default(id="s1", name="Faker#korea"),
            Summoner.create_default(id="s2", name="Doublelift#12345"),
            Summoner.create_default(id="s3", name="Uzi#eune"),
        ]

        champions = [
            Champion.create_default(id="Ahri", name="Ahri"),
            Champion.create_default(id="Yasuo", name="Yasuo"),
            Champion.create_default(id="Lux", name="Lux"),
        ]

        now = int(datetime.now().timestamp())
        matches = [
            Match(id="m1", created=now, ended=now + 1200, gametype="Ranked", patch="14.4"),
            Match(id="m2", created=now + 3600, ended=now + 4800, gametype="Normal", patch="14.5"),
        ]

        participants = [
            MatchParticipant(summoner_id="s1", match_id="m1", kill=10, assist=5, death=2, gold=15000, team=100, won=True, champion="Ahri"),
            MatchParticipant(summoner_id="s2", match_id="m1", kill=8, assist=7, death=4, gold=14000, team=100, won=True, champion="Yasuo"),
            MatchParticipant(summoner_id="s3", match_id="m1", kill=5, assist=10, death=6, gold=13000, team=200, won=False, champion="Lux"),
            MatchParticipant(summoner_id="s1", match_id="m2", kill=7, assist=8, death=3, gold=14500, team=200, won=False, champion="Yasuo"),
            MatchParticipant(summoner_id="s2", match_id="m2", kill=12, assist=4, death=5, gold=15500, team=100, won=True, champion="Lux"),
            MatchParticipant(summoner_id="s3", match_id="m2", kill=3, assist=6, death=7, gold=12000, team=200, won=False, champion="Ahri"),
        ]

        champion_stats = [
            ChampionStats(champion_id="Ahri", patch="14.4", gametype="CLASSIC", games_played=20, games_won=10, games_banned=5, kill=15, death=8, assist=12),
            ChampionStats(champion_id="Ahri", patch="14.5", gametype="CLASSIC", games_played=20, games_won=15, games_banned=2, kill=20, death=10, assist=15),
            ChampionStats(champion_id="Lux", patch="14.5", gametype="CLASSIC", games_played=20, games_won=5, games_banned=3, kill=25, death=12, assist=18),
        ]

        matches_analyzed = [
            MatchesAnalyzed(patch="14.4", gametype="CLASSIC", count=200),
            MatchesAnalyzed(patch="14.5", gametype="CLASSIC", count=260),
        ]

        for summoner in summoners:
            add_if_missing(session, Summoner, summoner.id, summoner)
        session.commit()

        for champion in champions:
            add_if_missing(session, Champion, champion.id, champion)
        session.commit()

        for match in matches:
            add_if_missing(session, Match, match.id, match)
        session.commit()

        for stats in champion_stats:
            stats_key = {"champion_id": stats.champion_id, "patch": stats.patch, "gametype": stats.gametype}
            add_if_missing(session, ChampionStats, stats_key, stats)
        session.commit()

        for analyzed in matches_analyzed:
            analyzed_key = {"patch": analyzed.patch, "gametype": analyzed.gametype}
            add_if_missing(session, MatchesAnalyzed, analyzed_key, analyzed)
        session.commit()

        for participant in participants:
            participant_key = {
                "summoner_id": participant.summoner_id,
                "match_id": participant.match_id,
            }
            add_if_missing(session, MatchParticipant, participant_key, participant)
        session.commit()
        print("Seed data inserted")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
