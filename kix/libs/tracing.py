#!/usr/bin/env python3
r"""
Tracing — Distributed Tracing for KIX runners (Phase 5)
OpenTelemetry + Jaeger export.

ERR_030 FIX: UTF-8 wrapper included.
"""
import io
import sys
import time
import os
from pathlib import Path
from typing import Optional, ContextManager
from contextlib import contextmanager

# ERR_030 FIX
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Tracing state
_tracing_enabled = False
_tracer = None
_trace_endpoint = os.environ.get("TRACE_ENDPOINT", "http://localhost:14268/api/traces")
_trace_service_name = os.environ.get("TRACE_SERVICE", "kix-runner")


def init_tracing(service_name: str = None, endpoint: str = None):
    """Initialize OpenTelemetry tracing.
    
    Args:
        service_name: Service name for traces
        endpoint: Jaeger/OTLP endpoint
    """
    global _tracing_enabled, _tracer, _trace_endpoint, _trace_service_name
    
    if service_name:
        _trace_service_name = service_name
    if endpoint:
        _trace_endpoint = endpoint
    
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        
        # Setup provider
        provider = TracerProvider()
        exporter = OTLPSpanExporter(endpoint=_trace_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        
        _tracer = trace.get_tracer(__name__)
        _tracing_enabled = True
        print(f"[Tracing] Initialized for service={_trace_service_name} endpoint={_trace_endpoint}")
        
    except ImportError:
        _tracing_enabled = False
        print("[Tracing] opentelemetry not installed — tracing disabled (fallback mode)")


@contextmanager
def trace_span(name: str, attributes: dict = None):
    """Context manager for tracing spans.
    
    Usage:
        with trace_span("query.hubs", {"topic": "graph.mutated"}) as span:
            result = engine.get_hubs()
            span.set_attribute("hubs.count", len(result))
    """
    start = time.perf_counter()
    span = None
    
    if _tracing_enabled and _tracer:
        with _tracer.start_as_current_span(name) as span:
            if attributes:
                for k, v in attributes.items():
                    span.set_attribute(k, str(v))
            try:
                yield span
            finally:
                span.set_attribute("duration_ms", (time.perf_counter() - start) * 1000)
    else:
        # Fallback: just yield None for compatibility
        yield None


class TracingMixin:
    """Mixin for adding tracing to runners."""
    
    def trace(self, name: str, attributes: dict = None):
        """Get a trace span context manager."""
        runner_attr = getattr(self, "runner_name", "unknown")
        attrs = {"runner": runner_attr}
        if attributes:
            attrs.update(attributes)
        return trace_span(name, attrs)


def get_tracing_status() -> dict:
    """Return tracing configuration status."""
    return {
        "enabled": _tracing_enabled,
        "endpoint": _trace_endpoint,
        "service_name": _trace_service_name,
        "tracer_available": _tracer is not None
    }


def record_duration(name: str, duration_ms: float, tags: dict = None):
    """Record a duration metric (fallback if no tracing)."""
    if _tracing_enabled:
        current_span = _tracer.start_span(name)
        current_span.set_attribute("duration_ms", duration_ms)
        for k, v in (tags or {}).items():
            current_span.set_attribute(k, str(v))
        current_span.end()
    else:
        print(f"[Tracing] {name}: {duration_ms:.2f}ms (tags={tags})")
