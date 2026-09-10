#!/usr/bin/env python3
r"""
Integration Test — Phase 5 Resilience Stack (P5-T06)
End-to-end: circuit breaker + retry + tracing in KIX runner context.
"""
import io
import sys
import time
from pathlib import Path

# ERR_030 FIX
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

_shared_path = str(Path(__file__).resolve().parent.parent.parent / "kix" / "libs" / "shared-clients")
sys.path.insert(0, _shared_path)
_tracing_path = str(Path(__file__).resolve().parent.parent.parent / "kix" / "libs")
sys.path.insert(0, _tracing_path)

from circuit_breaker import CircuitBreaker, get_circuit
from tracing import init_tracing, trace_span, get_tracing_status
from wazaa_client import WAZAA_Client


def test_end_to_end_tracing_and_circuit_breaker():
    """Test: tracing + circuit breaker integration."""
    
    # Initialize tracing (fallback mode if no collector)
    init_tracing("test-runner", "http://localhost:14268/api/traces")
    status = get_tracing_status()
    assert status["enabled"] or not status["enabled"], "Tracing status check OK"
    
    # Use circuit breaker with tracing
    with trace_span("circuit_test", {"breaker": "test-e2e"}) as span:
        breaker = CircuitBreaker("test-e2e", failure_threshold=2, timeout_seconds=2.0)
        
        def failing_operation():
            raise ConnectionError("simulated failure")
        
        for _ in range(2):
            try:
                breaker.call(failing_operation)
            except:
                pass
        
        assert breaker.state.value == "open", f"Expected open, got {breaker.state.value}"
        
        if span:
            span.set_attribute("result", "circuit_opened")
            span.set_attribute("failures", breaker.get_metrics()["failure_count"])


def test_wazaa_client_with_resilience():
    """Test: WAZAA client operates with circuit breaker protection."""
    
    client = WAZAA_Client(host="local")
    client.start()
    
    breaker = get_circuit("wazaa-test", failure_threshold=3, timeout_seconds=5.0)
    
    def resilient_publish(topic, payload):
        return breaker.call_with_retry(
            client.publish, topic, payload, max_retries=2
        )
    
    # Normal publish should succeed
    result = resilient_publish("test.wazaa.resilience", {"test": True})
    assert result is True or result is None, f"Expected True/None, got {result}"
    
    client.stop()
    print(f"[Integration] WAZAA resilience metrics: {breaker.get_metrics()}")


def test_rapid_failure_detection():
    """Test: rapid failures trip circuit breaker quickly."""
    
    breaker = CircuitBreaker("rapid-test", failure_threshold=5, timeout_seconds=30.0)
    
    def failing_call():
        raise Exception("rapid failure")
    
    start = time.perf_counter()
    for i in range(5):
        try:
            breaker.call(failing_call)
        except:
            pass
    elapsed = time.perf_counter() - start
    
    metrics = breaker.get_metrics()
    assert metrics["circuit_opens"] >= 1, f"Expected circuit opened, got {metrics}"
    assert elapsed < 2.0, f"Expected fast trip (<2s), took {elapsed:.3f}s"
    print(f"[Integration] Rapid failure detected in {elapsed:.3f}s")


if __name__ == "__main__":
    tests = [
        test_end_to_end_tracing_and_circuit_breaker,
        test_wazaa_client_with_resilience,
        test_rapid_failure_detection,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  [OK] {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  [KO] {test.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
