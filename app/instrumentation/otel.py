from __future__ import annotations

from typing import Callable

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.semconv.resource import ResourceAttributes

import logging
from app.api.config import settings
from app.database.database import engine

LOGGER = logging.getLogger(__name__)

_OTEL_IMPORT_ERROR: Exception | None = None


class _MissingFastAPIInstrumentor:
    @staticmethod
    def instrument_app(_app: FastAPI) -> None:
        return None


class _MissingHTTPXClientInstrumentor:
    def instrument(self) -> None:
        return None


class _MissingSQLAlchemyInstrumentor:
    def instrument(self, *, engine) -> None:
        return None


FastAPIInstrumentor = _MissingFastAPIInstrumentor
HTTPXClientInstrumentor = _MissingHTTPXClientInstrumentor
SQLAlchemyInstrumentor = _MissingSQLAlchemyInstrumentor
OTLPSpanExporter = None
OTLPMetricExporter = None
set_logger_provider = None
OTLPLogExporter = None
LoggerProvider = None
LoggingHandler = None
BatchLogRecordProcessor = None

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry._logs import set_logger_provider
    from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
except Exception as exc:  # pragma: no cover - exercised indirectly in test envs
    _OTEL_IMPORT_ERROR = exc


def setup_telemetry(app: FastAPI) -> Callable[[], None]:
    """Initialize tracing and auto-instrumentation for the app process."""
    if not settings.otel_enabled:
        LOGGER.info("Telemetry is disabled via configuration.")
        return lambda: None

    if (
        OTLPSpanExporter is None
        or OTLPMetricExporter is None
    ):
        LOGGER.warning(
            "Telemetry dependencies are unavailable; telemetry will be disabled for this process. Cause: %s",
            _OTEL_IMPORT_ERROR,
        )
        return lambda: None

    resource = Resource.create(
        {
            ResourceAttributes.SERVICE_NAME: settings.otel_service_name,
            ResourceAttributes.SERVICE_VERSION: settings.otel_service_version,
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: settings.otel_environment,
        }
    )

    provider = TracerProvider(
        resource=resource,
        sampler=TraceIdRatioBased(settings.otel_traces_sampler_arg),
    )

    span_exporter = OTLPSpanExporter(
        endpoint=settings.otel_exporter_otlp_endpoint,
        insecure=settings.otel_exporter_otlp_insecure,
    )
    provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(provider)

    metric_exporter = OTLPMetricExporter(
        endpoint=settings.otel_exporter_otlp_endpoint,
        insecure=settings.otel_exporter_otlp_insecure,
    )
    metric_reader = PeriodicExportingMetricReader(metric_exporter)
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument(engine=engine)

    app.state.tracer = trace.get_tracer(settings.otel_service_name)
    app.state.meter = metrics.get_meter(settings.otel_service_name)

    log_provider = None
    if (
        OTLPLogExporter is not None
        and set_logger_provider is not None
        and LoggerProvider is not None
        and LoggingHandler is not None
        and BatchLogRecordProcessor is not None
    ):
        log_provider = LoggerProvider(resource=resource)
        set_logger_provider(log_provider)

        log_exporter = OTLPLogExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            insecure=settings.otel_exporter_otlp_insecure,
        )
        log_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))

        otel_handler = LoggingHandler(level=logging.INFO, logger_provider=log_provider)
        logging.getLogger().addHandler(otel_handler)
        logging.getLogger("uvicorn").addHandler(otel_handler)
    elif _OTEL_IMPORT_ERROR is not None:
        LOGGER.warning(
            "Telemetry log exporting is unavailable; traces and metrics remain enabled. Cause: %s",
            _OTEL_IMPORT_ERROR,
        )

    LOGGER.info(
        "Telemetry initialized for service '%s' (environment=%s).",
        settings.otel_service_name,
        settings.otel_environment,
    )

    def _shutdown() -> None:
        meter_provider.shutdown()
        provider.shutdown()
        if log_provider is not None:
            log_provider.shutdown()

    return _shutdown
