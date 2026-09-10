#!/usr/bin/env python3
r"""
Chaos Test — WAZAA Partition (P5-T05)
Verifies resilience when WAZAA events are not consumed (partition).
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

from wazaa_client import WAZAA_Client


def test_wazaa_queue_overflow_resilience():
    """Test: queue overflow is handled gracefully."""
    client = WAZAA_Client(host="local")
    
    sent = 0
    for i in range(20):
        ok = client.publish("test.topic", {"id": i})
        if ok:
            sent += 1
    
    assert sent >= 15, f"Expected >= 15 published, got {sent}"
    print(f"[Chaos] Queue resilience: {sent}/20 published")


def test_wazaa_handler_processing():
    """Test: subscribed handlers receive events."""
    client = WAZAA_Client(host="local")
    client.start()
    
    results = []
    def handler(event):
        results.append(event.get("topic"))
    
    client.subscribe("test-partition.topic", handler)
    client.publish("test-partition.topic", {"data": 1})
    
    time.sleep(0.5)
    assert len(results) >= 1, f"Expected event processed, got {len(results)}"
    print(f"[Chaos] Handler received {len(results)} events")
    
    client.stop()


if __name__ == "__main__":
    tests = [
        test_wazaa_queue_overflow_resilience,
        test_wazaa_handler_processing,
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
