from fastapi import FastAPI


def get_riot_ingestion_status(app: FastAPI) -> dict:
    rate_limiter = getattr(app.state, "rate_limiter", None)
    ingestor = getattr(app.state, "riot_ingestor", None)

    if rate_limiter is not None:
        limiter_state = rate_limiter.get_state()
    else:
        limiter_state = {"tokens": None, "capacity": None, "reserved": None}

    return {
        "ingestorRunning": ingestor is not None,
        "rateLimiter": limiter_state,
    }
