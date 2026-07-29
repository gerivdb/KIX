"""
Cognitive Runners Registry — 4 couches cognitives
Definit tous les runners logiques (RLM, TLM, LLM, TEMPORAL)
pour l'orchestration souveraine via KIX.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CognitiveRunner:
    """Definition complete d'un runner cognitif."""
    name: str
    port: int
    layer: str           # "RLM" | "TLM" | "LLM" | "TEMPORAL"
    path_suffix: str     # Relative path from L2-PLATFORM root
    description: str = ""
    dependencies: tuple[str, ...] = ()  # Other runner names this depends on


# Architecture 4 couches — 17 runners cognitifs
COGNITIVE_RUNNERS: tuple[CognitiveRunner, ...] = (
    # === RLM (Décision) — 7 services ===
    CognitiveRunner("RLM-SECURE", 8797, "RLM", "RLM-SECURE",
                    "Security validation, pattern matching"),
    CognitiveRunner("RLM-DEPLOY", 8795, "RLM", "RLM-DEPLOY",
                    "Blue-green deployment orchestrator"),
    CognitiveRunner("RLM-GRAPH", 8794, "RLM", "RLM-GRAPH",
                    "Topology coherence, B243 validation"),
    CognitiveRunner("RLM-CONFIG", 8793, "RLM", "RLM-CONFIG",
                    "Syntax validation, ARGUS→NEXUS endpoint"),
    CognitiveRunner("RLM-INCIDENT", 8798, "RLM", "RLM-INCIDENT",
                    "Incident management, anomaly detection"),
    CognitiveRunner("RLM-RELEASE", 8799, "RLM", "RLM-RELEASE",
                    "Auto-migration TOPOS→ARGUS, release mgmt"),
    CognitiveRunner("RLM-METRICS", 8802, "RLM", "RLM-METRICS",
                    "Metrics collector, benchmarks, health"),

    # === TLM (Structure) — 4 services ===
    CognitiveRunner("TLM-LANG", 8801, "TLM", "TLM-LANG",
                    "Ternary Logic Machine language runner"),
    CognitiveRunner("TLM-CORE", 8789, "TLM", "TLM-CORE",
                    "TLM core logic engine"),
    CognitiveRunner("TLM-VALIDATE", 8790, "TLM", "TLM-VALIDATE",
                    "TLM validation engine"),
    CognitiveRunner("TLM-RELAX", 8791, "TLM", "TLM-RELAX",
                    "TLM relaxation/solver"),

    # === LLM (Génération) — 4 services ===
    CognitiveRunner("LLM-CORE", 8786, "LLM", "LLM-CORE",
                    "LLM core inference engine"),
    CognitiveRunner("LLM-EMBED", 8787, "LLM", "LLM-EMBED",
                    "Embedding generation"),
    CognitiveRunner("LLM-GENERATE", 8788, "LLM", "LLM-GENERATE",
                    "Text generation"),
    CognitiveRunner("LLM-CLASSIFY", 8806, "LLM", "LLM-CLASSIFY",
                    "Classification tasks"),

    # === TEMPORAL (Temps) — 2 services ===
    CognitiveRunner("TEMPORAL-ENGINE", 8804, "TEMPORAL", "TEMPORAL-ENGINE",
                    "Temporal logic engine"),
    CognitiveRunner("TIMX", 8805, "TEMPORAL", "TIMX",
                    "Time indexing service"),
)


# Helper functions

def get_all_runners() -> tuple[CognitiveRunner, ...]:
    """Retourne tous les runners cognitifs (17)."""
    return COGNITIVE_RUNNERS


def get_runners_by_layer(layer: str) -> tuple[CognitiveRunner, ...]:
    """Filtre les runners par couche cognitive."""
    return tuple(r for r in COGNITIVE_RUNNERS if r.layer == layer)


def get_runner_by_name(name: str) -> CognitiveRunner | None:
    """Retourne un runner par son nom exact."""
    for r in COGNITIVE_RUNNERS:
        if r.name == name:
            return r
    return None


def get_existing_runners(root_path: str) -> list[CognitiveRunner]:
    """Retourne seulement les runners dont le repertoire existe physiquement."""
    from pathlib import Path
    root = Path(root_path)
    existing = []
    for runner in COGNITIVE_RUNNERS:
        runner_path = root / runner.path_suffix
        if runner_path.exists() and runner_path.is_dir():
            existing.append(runner)
    return existing


def get_runners_by_layers(layers: list[str]) -> tuple[CognitiveRunner, ...]:
    """Filtre les runners par liste de couches."""
    layer_set = set(layers)
    return tuple(r for r in COGNITIVE_RUNNERS if r.layer in layer_set)


def get_layers() -> tuple[str, ...]:
    """Retourne la liste des couches disponibles."""
    return tuple(sorted({r.layer for r in COGNITIVE_RUNNERS}))


# Layer ordering for orchestration (dependency-aware)
LAYER_ORDER = ("RLM", "TLM", "LLM", "TEMPORAL")


def get_runners_ordered_by_layer() -> tuple[CognitiveRunner, ...]:
    """Retourne les runners ordonnes par couche (RLM → TLM → LLM → TEMPORAL)."""
    ordered = []
    for layer in LAYER_ORDER:
        ordered.extend(get_runners_by_layer(layer))
    return tuple(ordered)