import logging
from typing import Optional
from opentelemetry import trace
from app.models.championModels import Champion
from app.database.DAO import DAO

logger = logging.getLogger(__name__)

def get_champion_service(name: str, version: list[str], dao: DAO) -> Optional[Champion]:
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("service.champion.get") as span:
        span.set_attribute("champion.request.name_length", len(name))
        span.set_attribute("champion.request.versions", len(version))
        champion = dao.get_champion(name, version)

        if champion is None:
            span.set_attribute("champion.found", False)
            logger.debug("ChampionService: champion %s not found", name)
            return None

        span.set_attribute("champion.found", True)
        logger.debug("ChampionService: champion %s found", name)
        return champion
