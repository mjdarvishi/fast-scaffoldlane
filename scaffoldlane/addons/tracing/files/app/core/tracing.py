"""OpenTelemetry tracing bootstrap."""

import logging

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import Settings

tracer = trace.get_tracer("app")


def setup_tracing(
    settings: Settings,
    logger: logging.Logger,
    app: FastAPI | None = None,
) -> None:
    if not settings.tracing.enabled:
        logger.info("Tracing disabled")
        return

    resource = Resource.create(
        {
            SERVICE_NAME: settings.tracing.service_name,
        }
    )

    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(
        endpoint=settings.tracing.otlp_traces_endpoint,
    )

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    HTTPXClientInstrumentor().instrument()

    if app is not None:
        FastAPIInstrumentor.instrument_app(app, exclude_spans=["receive", "send"])

    logger.info(
        "Tracing enabled | service=%s",
        settings.tracing.service_name,
    )
