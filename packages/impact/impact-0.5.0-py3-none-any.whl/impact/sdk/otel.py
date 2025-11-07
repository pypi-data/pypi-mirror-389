from __future__ import annotations
from collections.abc import Mapping
from opentelemetry import trace, _events
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor, SpanExporter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, SimpleLogRecordProcessor
from opentelemetry.sdk._events import EventLoggerProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPSpanExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter as HTTPLogExporter
from opentelemetry._logs import set_logger_provider

def _create_trace_exporter(api_endpoint: str, headers: Mapping[str, str]) -> SpanExporter:
    """Create OTLP trace exporter.Appends /v1/traces to the endpoint."""
    endpoint = f"{api_endpoint.rstrip('/')}/v1/traces"
    return HTTPSpanExporter(endpoint=endpoint, headers=dict(headers))

def _create_log_exporter(api_endpoint: str, headers: Mapping[str, str]):
    """Create OTLP log exporter for EventLogger (message capture). Appends /v1/logs to the endpoint."""
    endpoint = f"{api_endpoint.rstrip('/')}/v1/logs"
    return HTTPLogExporter(endpoint=endpoint, headers=dict(headers))

def setup_tracing(
    *,
    service_name: str,
    service_version: str | None,
    environment: str | None,
    api_endpoint: str,
    headers: Mapping[str, str],
    disable_batch: bool = False,
    resource_attributes: Mapping[str, str] | None = None,
    disable_logs: bool = False,
):
    """Setup HTTP-only OTLP OpenTelemetry TracerProvider and EventLoggerProvider."""
    res_attrs = {
        "service.name": service_name,
        "service.version": service_version or "unknown",
        "deployment.environment": environment or "prod",
    }
    if resource_attributes:
        res_attrs.update(dict(resource_attributes))
    resource = Resource.create(res_attrs)

    # Setup traces - HTTP-only
    trace_exporter = _create_trace_exporter(api_endpoint, headers)
    tracer_provider = TracerProvider(resource=resource)
    span_processor = SimpleSpanProcessor(trace_exporter) if disable_batch else BatchSpanProcessor(trace_exporter)
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)

    # Setup EventLoggerProvider - required for GenAI message content capture
    if not disable_logs:
        log_exporter = _create_log_exporter(api_endpoint, headers)
        logger_provider = LoggerProvider(resource=resource)
        log_processor = SimpleLogRecordProcessor(log_exporter) if disable_batch else BatchLogRecordProcessor(log_exporter)
        logger_provider.add_log_record_processor(log_processor)
        # Register Logs provider globally so instrumentations use this pipeline.
        set_logger_provider(logger_provider)
        event_logger_provider = EventLoggerProvider(logger_provider=logger_provider)
        _events.set_event_logger_provider(event_logger_provider)
