class stubDAO:

    def get_summoner(self, name: str):
        if name == "test":
            return {"name": "test", "wins": 53, "losses": 47, "kills": 300, "deaths": 100, "assists": 500}
        return None

    def get_matches(self, name: str, offset: int, count: int):
        return [
            {"match_id": 1, "result": "win"},
            {"match_id": 2, "result": "loss"}
        ]