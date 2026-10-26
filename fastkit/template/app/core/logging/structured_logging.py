import json
import logging
import uuid
from datetime import UTC, datetime

from fastapi.encoders import jsonable_encoder
from opentelemetry import trace

from app.core.context_var import span_id_var, trace_id_var


def _trace_and_span_from_otel() -> tuple[str, str]:
    span = trace.get_current_span()
    if not span:
        return "", ""

    span_context = span.get_span_context()
    if not span_context or not span_context.is_valid:
        return "", ""

    trace_id = format(span_context.trace_id, "032x")
    span_id = format(span_context.span_id, "016x")
    return trace_id, span_id


def get_current_trace_and_span_ids() -> tuple[str, str]:
    otel_trace_id, otel_span_id = _trace_and_span_from_otel()
    if otel_trace_id:
        return otel_trace_id, otel_span_id

    trace_id = trace_id_var.get("")
    span_id = span_id_var.get("")
    return trace_id, span_id


def generate_trace_id() -> str:
    return uuid.uuid4().hex


def get_or_create_trace_id() -> str:
    trace_id, _ = get_current_trace_and_span_ids()
    if trace_id:
        return trace_id
    return generate_trace_id()


class StructuredContextFilter(logging.Filter):
    def __init__(self, service_name: str):
        super().__init__()
        self._service_name = service_name

    def filter(self, record: logging.LogRecord) -> bool:
        trace_id, span_id = get_current_trace_and_span_ids()
        record.service = getattr(record, "service", self._service_name)
        record.trace_id = getattr(record, "trace_id", trace_id)
        record.span_id = getattr(record, "span_id", span_id)
        return True


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service", ""),
            "trace_id": getattr(record, "trace_id", ""),
            "span_id": getattr(record, "span_id", ""),
            "message": record.getMessage(),
        }

        event_data = getattr(record, "event_data", None)
        if isinstance(event_data, dict):
            payload["event_data"] = event_data

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(jsonable_encoder(payload), ensure_ascii=True)
