from __future__ import annotations

import importlib

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.instrumentation import otel


def test_setup_telemetry_disabled(monkeypatch):
    monkeypatch.setattr(otel.settings, "otel_enabled", False)

    shutdown_func = otel.setup_telemetry(FastAPI())

    assert callable(shutdown_func)
    shutdown_func()


def test_setup_telemetry_enabled_configures_providers_and_instrumentation(monkeypatch):
    app = FastAPI()

    monkeypatch.setattr(otel.settings, "otel_enabled", True)
    monkeypatch.setattr(otel.settings, "otel_service_name", "psi-api")
    monkeypatch.setattr(otel.settings, "otel_service_version", "1.2.3")
    monkeypatch.setattr(otel.settings, "otel_environment", "test")
    monkeypatch.setattr(otel.settings, "otel_exporter_otlp_endpoint", "http://collector:4317")
    monkeypatch.setattr(otel.settings, "otel_exporter_otlp_insecure", True)
    monkeypatch.setattr(otel.settings, "otel_traces_sampler_arg", 0.25)

    resource_calls = {}
    tracer_provider_calls = {}
    meter_provider_calls = {}
    span_processor_calls = {}
    tracer_provider_shutdown = {"called": False}
    meter_provider_shutdown = {"called": False}
    fastapi_instrumented = {"app": None}
    httpx_instrumented = {"called": False}
    sqlalchemy_instrumented = {"engine": None}

    class FakeTracerProvider:
        def __init__(self, *, resource, sampler):
            tracer_provider_calls["resource"] = resource
            tracer_provider_calls["sampler"] = sampler

        def add_span_processor(self, processor):
            span_processor_calls["processor"] = processor

        def shutdown(self):
            tracer_provider_shutdown["called"] = True

    class FakeMeterProvider:
        def __init__(self, *, resource, metric_readers):
            meter_provider_calls["resource"] = resource
            meter_provider_calls["metric_readers"] = metric_readers

        def shutdown(self):
            meter_provider_shutdown["called"] = True

    class FakeHTTPXInstrumentor:
        def instrument(self):
            httpx_instrumented["called"] = True

    class FakeSQLAlchemyInstrumentor:
        def instrument(self, *, engine):
            sqlalchemy_instrumented["engine"] = engine

    class FakeSpanProcessor:
        def __init__(self, exporter):
            span_processor_calls["exporter"] = exporter

    class FakeMetricReader:
        def __init__(self, exporter):
            meter_provider_calls["metric_exporter"] = exporter

    monkeypatch.setattr(
        otel.Resource,
        "create",
        lambda attributes: resource_calls.update({"attributes": attributes}) or attributes,
    )
    monkeypatch.setattr(otel, "TracerProvider", FakeTracerProvider)
    monkeypatch.setattr(otel, "MeterProvider", FakeMeterProvider)
    monkeypatch.setattr(otel, "BatchSpanProcessor", FakeSpanProcessor)
    monkeypatch.setattr(otel, "PeriodicExportingMetricReader", FakeMetricReader)
    monkeypatch.setattr(otel, "OTLPSpanExporter", lambda **kwargs: {"type": "span_exporter", "kwargs": kwargs})
    monkeypatch.setattr(otel, "OTLPMetricExporter", lambda **kwargs: {"type": "metric_exporter", "kwargs": kwargs})
    monkeypatch.setattr(otel, "TraceIdRatioBased", lambda ratio: ("sampler", ratio))
    monkeypatch.setattr(otel.trace, "set_tracer_provider", lambda provider: tracer_provider_calls.update({"set_provider": provider}))
    monkeypatch.setattr(otel.metrics, "set_meter_provider", lambda provider: meter_provider_calls.update({"set_provider": provider}))
    monkeypatch.setattr(otel.FastAPIInstrumentor, "instrument_app", lambda instrumented_app: fastapi_instrumented.update({"app": instrumented_app}))
    monkeypatch.setattr(otel, "HTTPXClientInstrumentor", FakeHTTPXInstrumentor)
    monkeypatch.setattr(otel, "SQLAlchemyInstrumentor", FakeSQLAlchemyInstrumentor)
    monkeypatch.setattr(otel.trace, "get_tracer", lambda service_name: {"tracer": service_name})
    monkeypatch.setattr(otel.metrics, "get_meter", lambda service_name: {"meter": service_name})

    shutdown_func = otel.setup_telemetry(app)

    assert resource_calls["attributes"] == {
        otel.ResourceAttributes.SERVICE_NAME: "psi-api",
        otel.ResourceAttributes.SERVICE_VERSION: "1.2.3",
        otel.ResourceAttributes.DEPLOYMENT_ENVIRONMENT: "test",
    }
    assert tracer_provider_calls["resource"] == resource_calls["attributes"]
    assert tracer_provider_calls["sampler"] == ("sampler", 0.25)
    assert tracer_provider_calls["set_provider"] is not None
    assert meter_provider_calls["resource"] == resource_calls["attributes"]
    assert len(meter_provider_calls["metric_readers"]) == 1
    assert meter_provider_calls["set_provider"] is not None
    assert span_processor_calls["exporter"] == {
        "type": "span_exporter",
        "kwargs": {
            "endpoint": "http://collector:4317",
            "insecure": True,
        },
    }
    assert meter_provider_calls["metric_exporter"] == {
        "type": "metric_exporter",
        "kwargs": {
            "endpoint": "http://collector:4317",
            "insecure": True,
        },
    }
    assert fastapi_instrumented["app"] is app
    assert httpx_instrumented["called"] is True
    assert sqlalchemy_instrumented["engine"] is otel.engine
    assert app.state.tracer == {"tracer": "psi-api"}
    assert app.state.meter == {"meter": "psi-api"}

    shutdown_func()

    assert tracer_provider_shutdown["called"] is True
    assert meter_provider_shutdown["called"] is True


def test_setup_telemetry_shutdown_hook_calls_both_providers(monkeypatch):
    app = FastAPI()

    monkeypatch.setattr(otel.settings, "otel_enabled", True)
    monkeypatch.setattr(otel.settings, "otel_service_name", "psi-api")
    monkeypatch.setattr(otel.settings, "otel_service_version", "0.1.0")
    monkeypatch.setattr(otel.settings, "otel_environment", "dev")
    monkeypatch.setattr(otel.settings, "otel_exporter_otlp_endpoint", "http://collector:4317")
    monkeypatch.setattr(otel.settings, "otel_exporter_otlp_insecure", True)
    monkeypatch.setattr(otel.settings, "otel_traces_sampler_arg", 1.0)

    tracer_shutdown = {"called": False}
    meter_shutdown = {"called": False}

    class FakeTracerProvider:
        def __init__(self, *, resource, sampler):
            self.resource = resource
            self.sampler = sampler

        def add_span_processor(self, processor):
            self.processor = processor

        def shutdown(self):
            tracer_shutdown["called"] = True

    class FakeMeterProvider:
        def __init__(self, *, resource, metric_readers):
            self.resource = resource
            self.metric_readers = metric_readers

        def shutdown(self):
            meter_shutdown["called"] = True

    class FakeHTTPXInstrumentor:
        def instrument(self):
            return None

    class FakeSQLAlchemyInstrumentor:
        def instrument(self, *, engine):
            return None

    monkeypatch.setattr(otel, "TracerProvider", FakeTracerProvider)
    monkeypatch.setattr(otel, "MeterProvider", FakeMeterProvider)
    monkeypatch.setattr(otel, "BatchSpanProcessor", lambda exporter: exporter)
    monkeypatch.setattr(otel, "PeriodicExportingMetricReader", lambda exporter: exporter)
    monkeypatch.setattr(otel, "OTLPSpanExporter", lambda **kwargs: kwargs)
    monkeypatch.setattr(otel, "OTLPMetricExporter", lambda **kwargs: kwargs)
    monkeypatch.setattr(otel.trace, "set_tracer_provider", lambda provider: None)
    monkeypatch.setattr(otel.metrics, "set_meter_provider", lambda provider: None)
    monkeypatch.setattr(otel.FastAPIInstrumentor, "instrument_app", lambda instrumented_app: None)
    monkeypatch.setattr(otel, "HTTPXClientInstrumentor", FakeHTTPXInstrumentor)
    monkeypatch.setattr(otel, "SQLAlchemyInstrumentor", FakeSQLAlchemyInstrumentor)
    monkeypatch.setattr(otel.trace, "get_tracer", lambda service_name: None)
    monkeypatch.setattr(otel.metrics, "get_meter", lambda service_name: None)

    shutdown_func = otel.setup_telemetry(app)
    shutdown_func()

    assert tracer_shutdown["called"] is True
    assert meter_shutdown["called"] is True


def test_app_creation_smoke(monkeypatch):
    import app.instrumentation as instrumentation

    monkeypatch.setattr(instrumentation, "setup_telemetry", lambda app: (lambda: None))

    import app.main as main_module

    reloaded_module = importlib.reload(main_module)
    client = TestClient(reloaded_module.app)

    response = client.get("/")

    assert response.status_code == 200
    assert "LoL Tracker" in response.text
