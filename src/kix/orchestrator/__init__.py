"""KIX orchestrator package — base_orchestrator adoption.

Provides:
- L2RunnerOrchestrator: KIX L2 orchestrator adopting base_orchestrator primitive
- KIXProcessManagerAdapter: adapter from KIX ProcessManager to ProcessManagerInterface
- KIXRegistryAdapter: adapter from KIX runner registry to RegistryInterface
- KIXHealthAdapter: adapter from KIX health to HealthCheckerInterface
"""

from kix.orchestrator.l2_runner_orchestrator import (
    KIXHealthAdapter,
    KIXProcessManagerAdapter,
    KIXRegistryAdapter,
    L2RunnerOrchestrator,
)

__all__ = [
    "L2RunnerOrchestrator",
    "KIXProcessManagerAdapter",
    "KIXRegistryAdapter",
    "KIXHealthAdapter",
]
