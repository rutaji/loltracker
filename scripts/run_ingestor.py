import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from app.main import create_app
from app.riot.rotating_client import RotatingRiotApiClient
from app.services.riot_ingestor import start_ingestor, stop_ingestor

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)

# Load environment variables
load_dotenv(project_root / ".env")


def run_ingestor():
    """Create app, configure ingestor with rotating keys, and run indefinitely."""
    LOGGER.info("Starting Riot ingestor worker...")
    
    # Create the application
    app = create_app()
    
    # Initialize app state with rate limiter (since lifespan won't be entered)
    reserved_calls = int(os.getenv("RIOT_RESERVED_CALLS", "0"))
    riot_capacity = int(os.getenv("RIOT_RATE_LIMIT_TOTAL", "100"))
    riot_refill_interval = int(os.getenv("RIOT_RATE_LIMIT_WINDOW_SECONDS", "120"))
    
    from app.services.rate_limiter import TokenBucket
    app.state.rate_limiter = TokenBucket(
        capacity=riot_capacity,
        refill_interval_seconds=riot_refill_interval,
        reserved=reserved_calls,
    )
    
    LOGGER.info(
        "Initialized app state: rate_limiter with capacity=%d refill_interval=%ds reserved=%d",
        riot_capacity,
        riot_refill_interval,
        reserved_calls,
    )
    
    # Read ingestor API keys from environment
    ingestor_key_1 = os.getenv("RIOT_INGESTOR_KEY_1")
    ingestor_key_2 = os.getenv("RIOT_INGESTOR_KEY_2")
    fallback_key = os.getenv("RIOT_API_KEY")
    
    # Build list of available keys
    ingestor_keys = []
    if ingestor_key_1:
        ingestor_keys.append(ingestor_key_1)
        LOGGER.info("Using RIOT_INGESTOR_KEY_1")
    if ingestor_key_2:
        ingestor_keys.append(ingestor_key_2)
        LOGGER.info("Using RIOT_INGESTOR_KEY_2")
    
    if not ingestor_keys and fallback_key:
        ingestor_keys.append(fallback_key)
        LOGGER.warning("No ingestor keys found; falling back to RIOT_API_KEY")
    
    if not ingestor_keys:
        raise RuntimeError(
            "No API keys available for ingestor. "
            "Set RIOT_INGESTOR_KEY_1, RIOT_INGESTOR_KEY_2, or RIOT_API_KEY."
        )
    
    # Create rotating client with ingestor keys
    rate_limit_total = int(os.getenv("RIOT_RATE_LIMIT_TOTAL", "100"))
    rate_limit_window = int(os.getenv("RIOT_RATE_LIMIT_WINDOW_SECONDS", "120"))
    reserved_calls = int(os.getenv("RIOT_RESERVED_CALLS", "0"))
    regional_routing = os.getenv("RIOT_REGIONAL_ROUTING", "europe")
    platform_routing = os.getenv("RIOT_PLATFORM_ROUTING", "euw1")
    
    rotating_client = RotatingRiotApiClient(
        api_keys=ingestor_keys,
        regional_routing=regional_routing,
        platform_routing=platform_routing,
        rate_limit_total=rate_limit_total,
        rate_limit_window_seconds=rate_limit_window,
        reserved_calls=reserved_calls,
    )
    
    # Replace the api_client in app.state with the rotating client
    # Note: The app's lifespan will have already created a standard RiotApiClient,
    # but we override it here for the ingestor's exclusive use.
    app.state.api_client = rotating_client
    
    LOGGER.info(
        "Configured rotating client with %d keys; "
        "rate limit: %d requests per %d seconds per key",
        len(ingestor_keys),
        rate_limit_total,
        rate_limit_window,
    )
    
    # Start the ingestor
    ingest_enabled = os.getenv("RIOT_INGEST_ENABLED", "true").lower() in ("1", "true", "yes")
    if not ingest_enabled:
        LOGGER.warning("RIOT_INGEST_ENABLED is false; enabling for this worker")
        ingest_enabled = True
    
    interval_seconds = int(os.getenv("RIOT_INGEST_INTERVAL_SECONDS", "30"))
    start_ingestor(app, interval_seconds=interval_seconds)
    LOGGER.info("Ingestor started with interval: %d seconds", interval_seconds)
    
    # Keep the process alive
    try:
        asyncio.run(asyncio.sleep(float('inf')))
    except KeyboardInterrupt:
        LOGGER.info("Received interrupt signal; stopping ingestor...")
        stop_ingestor(app)
        LOGGER.info("Ingestor stopped")


if __name__ == "__main__":
    run_ingestor()
