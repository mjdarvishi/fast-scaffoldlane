"""Prometheus metrics exposure for monitoring."""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY,
)


def initialize_prometheus():
    """Initialize Prometheus metrics. Called at application startup."""
    pass  # Metrics are defined at module load time with the default registry


# HTTP Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

# Application metrics
active_connections = Gauge(
    "active_connections",
    "Number of active connections",
)

# Database metrics
database_queries_total = Counter(
    "database_queries_total",
    "Total database queries",
    ["operation", "table"],
)

database_query_duration_seconds = Histogram(
    "database_query_duration_seconds",
    "Database query latency in seconds",
    ["operation", "table"],
)

database_errors_total = Counter(
    "database_errors_total",
    "Total database errors",
    ["operation", "table", "error_type"],
)

# Cache metrics
cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_name"],
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_name"],
)

# Job/Worker metrics
job_executions_total = Counter(
    "job_executions_total",
    "Total job executions",
    ["job_name", "status"],
)

job_execution_duration_seconds = Histogram(
    "job_execution_duration_seconds",
    "Job execution duration in seconds",
    ["job_name"],
)

# Custom business metrics
chat_messages_total = Counter(
    "chat_messages_total",
    "Total chat messages processed",
    ["status"],
)

alarms_triggered_total = Counter(
    "alarms_triggered_total",
    "Total alarms triggered",
    ["alarm_type"],
)


def get_metrics() -> bytes:
    """Get all metrics in Prometheus exposition format."""
    return generate_latest(REGISTRY)


def get_metrics_content_type() -> str:
    """Get the content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST
