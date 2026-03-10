class stubDAO:

    def __init__(self):
        self.matches = [
            {
                "match_id": i,
                "start": f"2026-03-0{i}T18:00:00",
                "end": f"2026-03-0{i}T18:35:00",
                "version": "14.5",
                "mode": "Ranked Solo",
                "participants": [
                    {
                        "name": "test",
                        "kills": 10+i,
                        "deaths": 2,
                        "assists": 5,
                        "gold": 12000+i*100,
                        "team": "blue",
                        "champion": "Ahri",
                        "won": True
                    },
                    {
                        "name": "enemy",
                        "kills": 3,
                        "deaths": 8,
                        "assists": 4,
                        "gold": 9000,
                        "team": "red",
                        "champion": "Zed",
                        "won": False
                    }
                ]
            }
            for i in range(1, 11)
        ]

    def get_summoner(self, name: str):
        if name == "test":
            return {
                "name": "test",
                "wins": 53,
                "losses": 47,
                "kills": 300,
                "deaths": 100,
                "assists": 500
            }
        return None

    def get_matches(self, name: str, offset: int, count: int):
        return self.matches[offset:offset+count]