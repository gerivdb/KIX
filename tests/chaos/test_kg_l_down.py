#!/usr/bin/env python3
r"""
Chaos Test — KG-L Service Down (P5-T04)
Verifies circuit breaker + retry kick in when KG-L is unavailable.
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

from circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, get_circuit


def test_circuit_breaker_opens_on_failures():
    """Test: KG-L unavailable → circuit opens after threshold."""
    
    breaker = CircuitBreaker(
        "kg-l-service",
        failure_threshold=3,
        timeout_seconds=5.0,
        retry_count=2
    )
    
    # Simulate KG-L being down
    def failing_call():
        raise ConnectionError("KG-L unavailable")
    
    # First 3 failures should be attempted
    for i in range(3):
        try:
            breaker.call(failing_call)
        except ConnectionError:
            pass  # Expected
    
    # After 3 failures, circuit should be OPEN
    assert breaker.state.value == "open", f"Expected OPEN, got {breaker.state.value}"
    
    # Now calls should fail fast with CircuitBreakerOpenError
    try:
        breaker.call(failing_call)
        assert False, "Should have raised CircuitBreakerOpenError"
    except CircuitBreakerOpenError:
        pass  # Expected
    
    print(f"[Chaos] Circuit breaker correctly opened after 3 failures")
    print(f"[Chaos] Metrics: {breaker.get_metrics()}")


def test_circuit_breaker_allows_after_timeout():
    """Test: After timeout, circuit goes HALF_OPEN."""
    
    breaker = CircuitBreaker(
        "wazaa-bus",
        failure_threshold=2,
        timeout_seconds=1.0,  # Short timeout for testing
        retry_count=1
    )
    
    def failing_call():
        raise ConnectionError("WAZAA unavailable")
    
    # Trigger failures
    for _ in range(2):
        try:
            breaker.call(failing_call)
        except:
            pass
    
    assert breaker.state.value == "open"
    
    # Wait for timeout
    time.sleep(1.2)
    
    # Now circuit should allow (HALF_OPEN)
    try:
        breaker.call(failing_call)
    except ConnectionError:
        pass  # Still failing, but should attempt
    
    # Circuit should be OPEN again after failed HALF_OPEN attempt
    assert breaker.state.value == "open", f"Expected OPEN after timeout, got {breaker.state.value}"


def test_retry_with_backoff_success_after_retry():
    """Test: retry succeeds after transient failure."""
    
    breaker = CircuitBreaker(
        "vault-service",
        failure_threshold=5,
        timeout_seconds=30.0,
        retry_count=3
    )
    
    call_count = 0
    
    def flaky_call():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError(f"Transient failure #{call_count}")
        return "success"
    
    # Use call_with_retry for retry integration
    result = breaker.call_with_retry(flaky_call, max_retries=3)
    assert result == "success", f"Expected success, got {result}"
    assert call_count >= 3, f"Expected >= 3 attempts, got {call_count}"
    
    # Circuit should remain CLOSED (success after retries)
    assert breaker.state.value == "closed", f"Expected CLOSED after success, got {breaker.state.value}"


def test_fallback_invoked_on_open_circuit():
    """Test: fallback function invoked when circuit is open."""
    
    breaker = CircuitBreaker(
        "external-api",
        failure_threshold=1,
        timeout_seconds=30.0,
        retry_count=1
    )
    
    def failing_call():
        raise ConnectionError("API down")
    
    def fallback_call():
        return "fallback_result"
    
    # Trip the circuit
    try:
        breaker.call(failing_call)
    except ConnectionError:
        pass
    
    assert breaker.state.value == "open"
    
    # With fallback, should return fallback result instead of raising
    result = breaker.call(failing_call, fallback=fallback_call)
    assert result == "fallback_result", f"Expected fallback_result, got {result}"


if __name__ == "__main__":
    tests = [
        test_circuit_breaker_opens_on_failures,
        test_circuit_breaker_allows_after_timeout,
        test_retry_with_backoff_success_after_retry,
        test_fallback_invoked_on_open_circuit,
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
