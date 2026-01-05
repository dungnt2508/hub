"""
OpenTelemetry Tracing Setup
"""
import os
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as OTLPHTTPSpanExporter

from .logger import logger
from .config import config


def setup_tracing(
    service_name: Optional[str] = None,
    jaeger_endpoint: Optional[str] = None,
    console_export: bool = True
) -> trace.Tracer:
    """
    Setup OpenTelemetry tracing.
    
    Args:
        service_name: Service name for traces (defaults to APP_NAME)
        jaeger_endpoint: Jaeger OTLP endpoint (optional, e.g., http://localhost:4317)
        console_export: Whether to export traces to console (default: True)
        
    Returns:
        Tracer instance
    """
    service_name = service_name or config.APP_NAME
    
    # Create resource with service name
    resource = Resource.create({
        "service.name": service_name,
        "service.version": config.APP_VERSION,
        "deployment.environment": config.ENVIRONMENT,
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Add console exporter (for development)
    if console_export:
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))
        logger.info("OpenTelemetry: Console exporter enabled")
    
    # Add Jaeger/OTLP exporter if endpoint provided
    if jaeger_endpoint:
        try:
            if jaeger_endpoint.startswith("http://") or jaeger_endpoint.startswith("https://"):
                # HTTP endpoint
                otlp_exporter = OTLPHTTPSpanExporter(endpoint=jaeger_endpoint)
            else:
                # gRPC endpoint (default)
                otlp_exporter = OTLPSpanExporter(endpoint=jaeger_endpoint, insecure=True)
            
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info(f"OpenTelemetry: OTLP exporter enabled (endpoint: {jaeger_endpoint})")
        except Exception as e:
            logger.warning(f"Failed to setup OTLP exporter: {e}")
    
    # Set global tracer provider
    trace.set_tracer_provider(provider)
    
    # Get tracer
    tracer = trace.get_tracer(service_name)
    
    logger.info(f"OpenTelemetry tracing initialized for service: {service_name}")
    
    return tracer


def get_tracer(name: Optional[str] = None) -> trace.Tracer:
    """
    Get tracer instance.
    
    Args:
        name: Tracer name (defaults to service name)
        
    Returns:
        Tracer instance
    """
    name = name or config.APP_NAME
    return trace.get_tracer(name)


def get_current_span() -> Optional[trace.Span]:
    """
    Get current active span.
    
    Returns:
        Current span or None if no active span
    """
    return trace.get_current_span()


# Initialize tracing on module import
_tracer: Optional[trace.Tracer] = None

def init_tracing():
    """Initialize tracing (call this at application startup)"""
    global _tracer
    
    if _tracer is None:
        jaeger_endpoint = os.getenv("JAEGER_ENDPOINT")
        console_export = os.getenv("OTEL_CONSOLE_EXPORT", "true").lower() == "true"
        
        _tracer = setup_tracing(
            service_name=config.APP_NAME,
            jaeger_endpoint=jaeger_endpoint,
            console_export=console_export
        )
    
    return _tracer


# Auto-initialize if enabled
if os.getenv("ENABLE_TRACING", "true").lower() == "true":
    try:
        _tracer = init_tracing()
    except Exception as e:
        logger.warning(f"Failed to initialize tracing: {e}")
        _tracer = None

