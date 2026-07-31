from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def setup_prometheus(app: FastAPI) -> None:
    """Configure Prometheus metrics instrumentation."""
    if not settings.PROMETHEUS_ENABLED:
        return
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        instrumentator = Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            should_instrument_requests_inprogress=True,
            excluded_handlers=["/metrics", "/api/v1/health/live"],
            inprogress_name="autodocops_inprogress_requests",
            inprogress_labels=True,
        )
        instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
        logger.info("Prometheus metrics enabled at /metrics")
    except ImportError:
        logger.warning("prometheus-fastapi-instrumentator not installed, skipping metrics")


def setup_tracing(app: FastAPI) -> None:
    """Configure OpenTelemetry distributed tracing."""
    if not settings.OTEL_ENABLED:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        resource = Resource.create({
            "service.name": settings.APP_NAME,
            "service.version": settings.APP_VERSION,
            "deployment.environment": settings.ENVIRONMENT,
        })
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_ENDPOINT, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
        logger.info(f"OpenTelemetry tracing enabled, exporting to {settings.OTEL_EXPORTER_ENDPOINT}")
    except ImportError:
        logger.warning("OpenTelemetry packages not installed, skipping tracing")
    except Exception as e:
        logger.warning(f"OpenTelemetry setup failed: {e}")
