from typing import Optional
from app.models.championModels import Champion
from app.services.stubDAO import stubDAO

def get_champion_service(name: str, version: list[str], dao: stubDAO) -> Optional[Champion]:
    champion = dao.get_champion(name, version)

    if champion is None:
        return None
    
    return champion
