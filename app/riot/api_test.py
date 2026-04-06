import argparse
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Allow running the file directly with `python app/riot/api_test.py`.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.riot.riotApiClient import RiotApiClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch Riot account data and recent match details."
    )
    parser.add_argument("game_name", help="Riot game name, for example Faker")
    parser.add_argument("tagline", help="Riot tagline, for example KR1")
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Offset of the first match to fetch.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of match IDs to fetch.",
    )
    parser.add_argument(
        "--region",
        default="europe",
        help="Regional routing value such as europe, americas, or asia.",
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().with_name("matches.json")),
        help="Path to the JSON file that will be overwritten with fetched data.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("RIOT_API_KEY")

    if not api_key:
        print("RIOT_API_KEY is missing from the .env file.")
        return 1

    client = RiotApiClient(api_key=api_key, regional_routing=args.region)

    try:
        summoner = client.get_summoner_by_riot_id(args.game_name, args.tagline)
        match_ids = client.get_match_ids_by_puuid(
            summoner["puuid"],
            start=args.start,
            count=args.count,
        )
        matches = [
            client.get_match_info_by_match_id(match_id)
            for match_id in match_ids
        ]
    except httpx.HTTPStatusError as exc:
        print(f"Riot API returned {exc.response.status_code}: {exc.response.text}")
        return 1
    except httpx.RequestError as exc:
        print(f"Request failed: {exc}")
        return 1

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "summoner": summoner,
        "match_ids": match_ids,
        "matches": matches,
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("Summoner:")
    print(json.dumps(summoner, indent=2))
    print()
    print("Match IDs:")
    for match_id in match_ids:
        print(match_id)
    print()
    print(f"Wrote {len(matches)} matches to {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
