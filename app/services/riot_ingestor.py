import asyncio
import logging
import random
from types import SimpleNamespace

from apscheduler.schedulers.background import BackgroundScheduler

from app.database.DAO import DAO
from app.services import summonerServices

LOGGER = logging.getLogger(__name__)


QUEUES = ["RANKED_SOLO_5x5", "RANKED_FLEX_SR"]
TIERS = [
    "CHALLENGER",
    "GRANDMASTER",
    "MASTER",
    "DIAMOND",
    "EMERALD",
    "PLATINUM",
    "GOLD",
    "SILVER",
    "BRONZE",
    "IRON",
]
DIVISIONS = ["I", "II", "III", "IV"]


class RiotIngestor:
    def __init__(self, app, *, interval_seconds: int = 30):
        self.app = app
        self.interval_seconds = interval_seconds
        self.scheduler = BackgroundScheduler()
        self._job = None

    def start(self) -> None:
        LOGGER.info("Starting Riot ingestor scheduler; interval=%ss", self.interval_seconds)
        self.scheduler.add_job(self._iteration_sync, "interval", seconds=self.interval_seconds, max_instances=1)
        self.scheduler.start()

    def stop(self) -> None:
        LOGGER.info("Stopping Riot ingestor scheduler")
        try:
            self.scheduler.shutdown(wait=False)
        except Exception:
            LOGGER.exception("Error shutting down scheduler")

    def _sample_tier_by_gaussian(self) -> str:
        mean = (len(TIERS) - 1) / 2.0
        sigma = max(1.0, len(TIERS) / 3.0)
        idx = int(random.gauss(mean, sigma))
        idx = max(0, min(len(TIERS) - 1, idx))
        return TIERS[idx]

    def _iteration_sync(self) -> None:
        """Synchronous wrapper that runs the async iteration in a new event loop."""
        try:
            asyncio.run(self._iteration_async())
        except Exception:
            LOGGER.exception("Error in ingestor iteration wrapper")

    async def _iteration_async(self) -> None:
        try:
            api_client = self.app.state.api_client
            dao = DAO.get_dao()
            queue = random.choice(QUEUES)
            tier = self._sample_tier_by_gaussian()
            division = random.choice(DIVISIONS)

            LOGGER.info("Ingestor iteration: queue=%s tier=%s division=%s", queue, tier, division)

            # Call the league entries endpoint to get summoners
            try:
                entries = api_client.get_league_entries(queue, tier, division)
            except Exception as exc:
                LOGGER.warning("Failed to fetch league entries for %s/%s/%s: %s", queue, tier, division, exc)
                return

            if not entries:
                LOGGER.info("No league entries returned for %s/%s/%s", queue, tier, division)
                return

            # Process a small sample of entries to keep API usage controlled
            sample_size = min(5, max(1, len(entries) // 10))
            sample = random.sample(entries, sample_size)

            for e in sample:
                # League entries endpoint already provides puuid directly
                puuid = e.get("puuid")
                if not puuid:
                    LOGGER.warning("League entry missing puuid; skipping entry with keys: %s", list(e.keys()))
                    continue

                # Use a minimal request-like object that holds the app
                fake_request = SimpleNamespace(app=self.app)
                try:
                    result = summonerServices.ingest_matches_from_puuid_service(fake_request, puuid, dao)
                    LOGGER.info("Ingested summoner puuid=%s: inserted=%s failed=%s", puuid, result.inserted_count, result.failed_count)
                except Exception:
                    LOGGER.exception("Failed to refresh matches for puuid=%s", puuid)

        except Exception:
            LOGGER.exception("Unhandled error during ingest iteration")
        finally:
            try:
                dao.close()
            except Exception:
                pass


_INGESTOR_KEY = "riot_ingestor"


def start_ingestor(app, interval_seconds: int = 30):
    ingestor: RiotIngestor | None = getattr(app.state, _INGESTOR_KEY, None)
    if ingestor is None:
        ingestor = RiotIngestor(app, interval_seconds=interval_seconds)
        setattr(app.state, _INGESTOR_KEY, ingestor)
        ingestor.start()


def stop_ingestor(app):
    ingestor: RiotIngestor | None = getattr(app.state, _INGESTOR_KEY, None)
    if ingestor is not None:
        ingestor.stop()
        delattr(app.state, _INGESTOR_KEY)
