import argparse
import asyncio
import random
import time
from dataclasses import dataclass
from typing import Iterable

import httpx


DEFAULT_PATHS = [
    "/",
    "/",
    "/",
    "/champion/ahri?ajax=true",
    "/champion/lux?ajax=true",
]


@dataclass
class WorkerStats:
    requests: int = 0
    failures: int = 0
    total_latency: float = 0.0


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int((len(ordered) - 1) * p)
    return ordered[index]


async def worker(
    worker_id: int,
    client: httpx.AsyncClient,
    base_url: str,
    paths: list[str],
    deadline: float,
    timeout: float,
    cooldown: float,
) -> tuple[WorkerStats, list[float]]:
    stats = WorkerStats()
    latencies: list[float] = []

    while time.perf_counter() < deadline:
        path = random.choice(paths)
        start = time.perf_counter()
        try:
            response = await client.get(f"{base_url}{path}", timeout=timeout)
            elapsed = time.perf_counter() - start
            latencies.append(elapsed)
            stats.total_latency += elapsed
            stats.requests += 1

            if response.status_code >= 500:
                stats.failures += 1
        except Exception:
            elapsed = time.perf_counter() - start
            latencies.append(elapsed)
            stats.total_latency += elapsed
            stats.requests += 1
            stats.failures += 1

        if cooldown > 0:
            await asyncio.sleep(cooldown)

    print(f"worker={worker_id} done requests={stats.requests} failures={stats.failures}")
    return stats, latencies


def flatten(values: Iterable[list[float]]) -> list[float]:
    output: list[float] = []
    for chunk in values:
        output.extend(chunk)
    return output


async def run_load_test(
    base_url: str,
    duration_seconds: int,
    concurrency: int,
    timeout_seconds: float,
    cooldown_seconds: float,
    paths: list[str],
) -> int:
    deadline = time.perf_counter() + duration_seconds

    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [
            worker(
                worker_id=i,
                client=client,
                base_url=base_url,
                paths=paths,
                deadline=deadline,
                timeout=timeout_seconds,
                cooldown=cooldown_seconds,
            )
            for i in range(concurrency)
        ]

        results = await asyncio.gather(*tasks)

    stats_list = [item[0] for item in results]
    all_latencies = flatten([item[1] for item in results])

    total_requests = sum(item.requests for item in stats_list)
    total_failures = sum(item.failures for item in stats_list)
    total_latency = sum(item.total_latency for item in stats_list)

    avg_latency_ms = (total_latency / total_requests * 1000.0) if total_requests else 0.0
    p95_latency_ms = percentile(all_latencies, 0.95) * 1000.0
    p99_latency_ms = percentile(all_latencies, 0.99) * 1000.0
    rps = total_requests / duration_seconds if duration_seconds > 0 else 0.0
    success_rate = ((total_requests - total_failures) / total_requests * 100.0) if total_requests else 0.0

    print("\nLoad test summary")
    print("-----------------")
    print(f"base_url:         {base_url}")
    print(f"duration_seconds: {duration_seconds}")
    print(f"concurrency:      {concurrency}")
    print(f"requests:         {total_requests}")
    print(f"failures:         {total_failures}")
    print(f"success_rate:     {success_rate:.2f}%")
    print(f"throughput:       {rps:.2f} req/s")
    print(f"avg_latency:      {avg_latency_ms:.2f} ms")
    print(f"p95_latency:      {p95_latency_ms:.2f} ms")
    print(f"p99_latency:      {p99_latency_ms:.2f} ms")

    return 1 if total_failures > 0 else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simple async load test for PSI FastAPI app."
    )
    parser.add_argument("--base-url", default="http://localhost:8000", help="Target API base URL.")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds.")
    parser.add_argument("--concurrency", type=int, default=30, help="Number of concurrent workers.")
    parser.add_argument("--timeout", type=float, default=5.0, help="Per-request timeout in seconds.")
    parser.add_argument(
        "--cooldown",
        type=float,
        default=0.0,
        help="Optional pause between requests per worker.",
    )
    parser.add_argument(
        "--path",
        action="append",
        help="Request path to include in traffic mix. Repeatable. Defaults to safe built-in mix.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = args.path if args.path else DEFAULT_PATHS

    for path in paths:
        if not path.startswith("/"):
            raise ValueError(f"Invalid path '{path}'. Paths must start with '/'.")

    return asyncio.run(
        run_load_test(
            base_url=args.base_url.rstrip("/"),
            duration_seconds=args.duration,
            concurrency=args.concurrency,
            timeout_seconds=args.timeout,
            cooldown_seconds=args.cooldown,
            paths=paths,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
