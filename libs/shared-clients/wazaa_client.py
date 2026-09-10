#!/usr/bin/env python3
r"""
WAZAA_Client — Client unifié pour le bus WAZAA (Phase 1)
Fournit publish(), subscribe(), wait_for_completion().

ERR_030: UTF-8 wrapper included.
"""
import io
import sys
import time
import random
import json
import threading
import queue
from pathlib import Path
from typing import Optional, Callable

# ERR_030 FIX
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def retry_with_backoff(max_retries=3, base_delay=0.1, max_delay=2.0):
    """Retry decorator with exponential backoff + jitter (Phase 5)."""
    import functools
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_err = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        delay += random.uniform(0, 0.1)
                        print(f"[Retry] {func.__name__} attempt {attempt + 1} failed: {e}, retry in {delay:.3f}s")
                        time.sleep(delay)
            raise last_err
        return wrapper
    return decorator


class WAZAA_Client:
    """Client unifié pour le bus WAZAA.
    
    Mode local: utilise une queue en mémoire pour le dispatch synchrone.
    Mode remote: HTTP calls vers WAZAA (port 1874).
    
    Config injectée via settings.yaml.
    """
    
    def __init__(self, host: str = "local", config: dict = None):
        self.host = host
        self.config = config or {}
        self._subscriptions: dict[str, list[Callable]] = {}
        self._event_queue: queue.Queue = queue.Queue(maxsize=10000)
        self._running = False
        self._worker_thread = None
        self._processed_events = 0
        
        if host == "local" or "localhost" in str(host):
            self._mode = "local"
        else:
            self._mode = "remote"
    
    def subscribe(self, topic: str, handler: Callable):
        """Subscribe to a WAZAA topic."""
        if topic not in self._subscriptions:
            self._subscriptions[topic] = []
        self._subscriptions[topic].append(handler)
        print(f"[WAZAA_Client] Subscribed to {topic}")
    
    @retry_with_backoff(max_retries=3, base_delay=0.1, max_delay=2.0)
    def publish(self, topic: str, payload: dict) -> bool:
        """Publish event to WAZAA topic."""
        if self._mode == "local":
            event = {
                "topic": topic,
                "payload": payload,
                "timestamp": time.time(),
                "id": f"evt-{self._processed_events}"
            }
            try:
                self._event_queue.put_nowait(event)
                self._processed_events += 1
                return True
            except queue.Full:
                print(f"[WAZAA_Client] Queue full, dropping event for {topic}")
                return False
        else:
            # Remote HTTP stub
            return True
    
    def start(self):
        """Start the subscriber worker thread."""
        if self._mode == "local":
            self._running = True
            self._worker_thread = threading.Thread(target=self._process_events, daemon=True)
            self._worker_thread.start()
            print("[WAZAA_Client] Worker thread started")
    
    def stop(self):
        """Stop the subscriber."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=2)
        print("[WAZAA_Client] Stopped")
    
    def _process_events(self):
        """Process events from queue."""
        while self._running:
            try:
                event = self._event_queue.get(timeout=1)
                topic = event["topic"]
                
                if topic in self._subscriptions:
                    for handler in self._subscriptions[topic]:
                        try:
                            handler(event)
                        except Exception as e:
                            print(f"[WAZAA_Client] Handler error: {e}")
            except queue.Empty:
                continue
    
    def wait_for_completion(self, timeout: float = 30.0) -> dict:
        """Wait for all queued events to be processed."""
        start = time.time()
        while time.time() - start < timeout:
            if self._event_queue.empty():
                return {"status": "completed", "processed": self._processed_events}
            time.sleep(0.1)
        return {"status": "timeout", "processed": self._processed_events}
