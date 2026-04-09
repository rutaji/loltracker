import os
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi import Request
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from app.router import router
from fastapi.staticfiles import StaticFiles
from app.riot.riotApiClient import RiotApiClient
from app.instrumentation import setup_telemetry


logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Load environment variables early
project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")

# Placeholder for telemetry shutdown function
telemetry_shutdown = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        raise RuntimeError("RIOT_API_KEY is missing from the .env file.")

    app.state.api_client = RiotApiClient(api_key=api_key, regional_routing="europe")
    try:
        yield
    finally:
        if telemetry_shutdown is not None:
            telemetry_shutdown()


# Create app with lifespan
app = FastAPI(lifespan=lifespan)

# Initialize telemetry immediately after app creation (before startup)
telemetry_shutdown = setup_telemetry(app)

request_counter = None
request_latency = None


@app.middleware("http")
async def record_request_metrics(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)

    global request_counter
    global request_latency

    if request_counter is None or request_latency is None:
        meter = getattr(request.app.state, "meter", None)
        if meter is not None:
            request_counter = meter.create_counter(
                "psi_http_server_requests_total",
                description="Total number of HTTP requests handled by the API.",
                unit="1",
            )
            request_latency = meter.create_histogram(
                "psi_http_server_request_duration_seconds",
                description="Duration of HTTP requests handled by the API.",
                unit="s",
            )

    route = request.scope.get("route")
    route_path = getattr(route, "path", request.url.path)

    attributes = {
        "http.method": request.method,
        "http.status_code": response.status_code,
        "http.route": route_path,
    }

    if request_counter is not None:
        request_counter.add(1, attributes=attributes)
    if request_latency is not None:
        request_latency.record(time.perf_counter() - start_time, attributes=attributes)

    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    span = trace.get_current_span()
    span.record_exception(exc)
    span.set_status(Status(StatusCode.ERROR))
    LOGGER.exception("Unhandled exception while processing %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    span = trace.get_current_span()
    span.set_attribute("http.status_code", exc.status_code)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

