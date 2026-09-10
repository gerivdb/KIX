#!/usr/bin/env python3
r"""
Circuit Breaker — Phase 5 Observability & Resilience
Implements circuit breaker pattern with configurable thresholds.

States: CLOSED → OPEN → HALF_OPEN → CLOSED
Config injectée via settings.yaml.

ERR_030 FIX: UTF-8 wrapper included.
"""
import io
import sys
import time
import threading
import enum
from pathlib import Path
from typing import Optional, Callable, Any
from functools import wraps

# ERR_030 FIX
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class CircuitState(enum.Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """Circuit breaker pour protection fail-fast.
    
    States:
    - CLOSED: allow requests, count failures
    - OPEN: block requests, timeout before HALF_OPEN
    - HALF_OPEN: allow test request, CLOSED if OK
    
    Config:
    - failure_threshold: nbr d'échecs avant OPEN
    - timeout_seconds: durée OPEN avant HALF_OPEN
    - retry_count: nb tentatives en HALF_OPEN
    """
    
    def __init__(self, name: str, failure_threshold: int = 5,
                 timeout_seconds: float = 30.0, retry_count: int = 2):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.retry_count = retry_count
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = threading.Lock()
        
        # Metrics
        self._total_requests = 0
        self._total_failures = 0
        self._total_successes = 0
        self._circuit_opens = 0
        self._circuit_closes = 0
    
    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        return self._state
    
    def _before_request_hook(self) -> Any:
        """Called before each request."""
        self._total_requests += 1
    
    def _record_success(self):
        """Record successful request."""
        with self._lock:
            self._total_successes += 1
            self._failure_count = 0
            
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
                self._circuit_closes += 1
                print(f"[CircuitBreaker] {self.name}: HALF_OPEN → CLOSED (success)")
    
    def _record_failure(self, error: Exception = None):
        """Record failed request."""
        with self._lock:
            self._total_failures += 1
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                # Failed in HALF_OPEN → back to OPEN
                self._state = CircuitState.OPEN
                self._circuit_opens += 1
                print(f"[CircuitBreaker] {self.name}: HALF_OPEN → OPEN (failure)")
            
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    self._circuit_opens += 1
                    print(f"[CircuitBreaker] {self.name}: CLOSED → OPEN (failures={self._failure_count})")
    
    def can_execute(self) -> bool:
        """Check if request can be executed (circuit check)."""
        with self._lock:
            now = time.time()
            
            if self._state == CircuitState.CLOSED:
                return True
            
            if self._state == CircuitState.OPEN:
                # Check timeout
                if self._last_failure_time and (now - self._last_failure_time) >= self.timeout_seconds:
                    self._state = CircuitState.HALF_OPEN
                    print(f"[CircuitBreaker] {self.name}: OPEN → HALF_OPEN (timeout expired)")
                    return True
                return False
            
            if self._state == CircuitState.HALF_OPEN:
                return True
            
            return False
    
    def call(self, func: Callable, *args, fallback: Callable = None, **kwargs) -> Any:
        """Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            fallback: Fallback function if circuit open
            *args, **kwargs: Arguments to func
            
        Returns:
            Result of func or fallback
            
        Raises:
            CircuitBreakerOpenError: If circuit is open and no fallback
        """
        if not self.can_execute():
            if fallback:
                print(f"[CircuitBreaker] {self.name}: OPEN, calling fallback")
                return fallback(*args, **kwargs)
            raise CircuitBreakerOpenError(f"Circuit {self.name} is OPEN")
        
        try:
            self._before_request_hook()
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure(e)
            if fallback:
                return fallback(*args, **kwargs)
            raise
    
    def call_with_retry(self, func: Callable, *args, fallback: Callable = None,
                        max_retries: int = 3, **kwargs) -> Any:
        """Execute with retry on failures (before circuit tracking).
        
        Args:
            func: Function to execute
            fallback: Fallback if all retries fail
            max_retries: Number of retry attempts
        """
        import random
        
        last_error = None
        for attempt in range(max_retries + 1):
            if self.can_execute():
                try:
                    self._before_request_hook()
                    result = func(*args, **kwargs)
                    self._record_success()
                    return result
                except Exception as e:
                    last_error = e
                    self._record_failure(e)
                    if attempt < max_retries:
                        delay = min(0.1 * (2 ** attempt), 2.0) + random.uniform(0, 0.1)
                        print(f"[Retry] {self.name} attempt {attempt + 1} failed: {e}, retry in {delay:.3f}s")
                        time.sleep(delay)
            else:
                break  # Circuit is open, stop retrying
        
        if fallback:
            return fallback(*args, **kwargs)
        raise last_error
    
    def decorate(self, fallback: Callable = None):
        """Decorator for circuit breaker pattern.
        
        Usage:
            breaker = CircuitBreaker("my-service")
            
            @breaker.decorate(fallback=my_fallback)
            def call_service(x):
                return requests.get(x)
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self.call(func, *args, fallback=fallback, **kwargs)
            return wrapper
        return decorator
    
    def get_metrics(self) -> dict:
        """Return circuit breaker metrics."""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "total_requests": self._total_requests,
            "total_successes": self._total_successes,
            "total_failures": self._total_failures,
            "circuit_opens": self._circuit_opens,
            "circuit_closes": self._circuit_closes,
            "failure_threshold": self.failure_threshold,
            "timeout_seconds": self.timeout_seconds
        }
    
    def reset(self):
        """Reset circuit to CLOSED state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None
            print(f"[CircuitBreaker] {self.name}: reset to CLOSED")


class CircuitBreakerRegistry:
    """Registry for circuit breakers (singleton)."""
    
    _instance = None
    _breakers: dict[str, CircuitBreaker] = {}
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_or_create(self, name: str, **kwargs) -> CircuitBreaker:
        """Get existing breaker or create new."""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, **kwargs)
        return self._breakers[name]
    
    def get_all_metrics(self) -> dict:
        """Get metrics from all breakers."""
        return {name: b.get_metrics() for name, b in self._breakers.items()}


# Convenience function
_circuit_registry = CircuitBreakerRegistry()

def get_circuit(name: str, **kwargs) -> CircuitBreaker:
    """Get or create a circuit breaker."""
    return _circuit_registry.get_or_create(name, **kwargs)
