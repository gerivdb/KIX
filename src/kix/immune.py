"""KIX-IMMUNE V21.0 — Module d'immunité système pour KIX.

Composants :
- TINA/Blake3 heartbeat validation
- SOMA thermal/RAM regulation
- Bernstein G1 cycle detection
- TIMX JWT temps cognitif
- KORX-L1 state.kbin persistence (372 octets)
- Git Process Semaphore (max 4 git.exe)
- BOINC-LLM offloading (SOMA critical)

IntentHash: 0xKIX_IMMUNE_V210_20260804
"""

from __future__ import annotations

import hashlib
import json
import mmap
import os
import platform
import secrets
import struct
import time
from pathlib import Path
from typing import Dict, List, Optional


# ── Constants ─────────────────────────────────────────────────────────

STATE_KBIN_PATH = Path(__file__).resolve().parents[2] / "data" / "state.kbin"
STATE_KBIN_SIZE = 372

HEADER_MAGIC = b"KORX"
WAL_SEQ_OFFSET = 0x004
INTENT_HASH_OFFSET = 0x00C
RUNNER_BITMASK_OFFSET = 0x01C
PHI_CPS_OFFSET = 0x0DC
SOMA_METRICS_OFFSET = 0x0EC
GIT_COUNT_OFFSET = 0x150
GIT_PIDS_OFFSET = 0x154
GIT_LOCK_BITMASK_OFFSET = 0x164
SIGNATURE_OFFSET = 0x170

MAX_GIT_PROCESSES = 4


# ── TINA/Blake3 Heartbeat ─────────────────────────────────────────────

def compute_blake3(data: bytes) -> bytes:
    """Calcule le hash Blake3 (O(1) via pip blake3)."""
    try:
        import blake3
        h = blake3.blake3(data)
        return h.digest()[:16]
    except ImportError:
        return hashlib.sha256(data).digest()[:16]


def validate_heartbeat(registry_bytes: bytes, expected_hash: bytes, timeout_ms: int = 15) -> bool:
    """Valide le heartbeat TINA/Blake3 en < 15ms."""
    start = time.perf_counter()
    actual = compute_blake3(registry_bytes)
    elapsed_ms = (time.perf_counter() - start) * 1000

    if elapsed_ms > timeout_ms:
        return False
    return secrets.compare_digest(actual, expected_hash)


# ── SOMA Thermal/RAM Regulation ──────────────────────────────────────

class SOMA:
    """Régulation somatique et thermique."""

    def __init__(self) -> None:
        self.ram_warning_threshold = 0.80
        self.ram_critical_threshold = 0.90
        self.temp_warning_threshold = 75.0
        self.temp_critical_threshold = 85.0

    def get_ram_usage(self) -> float:
        """Retourne l'usage RAM en fraction (0.0 - 1.0)."""
        try:
            import psutil
            return psutil.virtual_memory().percent / 100.0
        except ImportError:
            return 0.0

    def get_temperature(self) -> Optional[float]:
        """Retourne la température CPU si disponible."""
        try:
            import psutil
            temps = psutil.sensors_temperatures()
            for name, entries in temps.items():
                for entry in entries:
                    if entry.current:
                        return float(entry.current)
        except (ImportError, AttributeError):
            pass
        return None

    def check_status(self) -> Dict[str, any]:
        """Vérifie les seuils SOMA et retourne le statut."""
        ram = self.get_ram_usage()
        temp = self.get_temperature()

        status = {
            "ram_usage": ram,
            "temperature_c": temp,
            "mode": "NORMAL",
        }

        if temp is not None and temp > self.temp_critical_threshold:
            status["mode"] = "CRITICAL"
        elif ram > self.ram_critical_threshold:
            status["mode"] = "CRITICAL"
        elif temp is not None and temp > self.temp_warning_threshold:
            status["mode"] = "LOW_FREQUENCY"
        elif ram > self.ram_warning_threshold:
            status["mode"] = "LOW_FREQUENCY"

        return status


# ── Bernstein G1 Cycle Detection ─────────────────────────────────────

class BernsteinG1:
    """Détection de cycles DAG par ordonnanceur Bernstein G1."""

    def __init__(self) -> None:
        self.phi_cps = 4.559
        self.rollback_threshold = 1.000

    def detect_cycle(self, dag_edges: list) -> bool:
        """Détecte un cycle dans le DAG d'exécution."""
        graph: Dict[str, list] = {}
        for src, dst in dag_edges:
            graph.setdefault(src, []).append(dst)
            graph.setdefault(dst, [])

        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.discard(node)
            return False

        for node in graph:
            if node not in visited:
                if dfs(node):
                    return True
        return False

    def update_phi_cps(self, has_cycle: bool) -> float:
        """Met à jour le score φ-CPS selon la présence de cycles."""
        if has_cycle:
            self.phi_cps = self.rollback_threshold
        else:
            self.phi_cps = min(4.559, self.phi_cps + 0.1)

        # P5-2: KG-L KIX bridge - emit korx-sem node after phi_cps calculation
        try:
            from kg_l_kix_bridge import emit_edge
            emit_edge(
                src="korx-sem",
                dst="kg-l:root",
                kind="causes",
                metadata={
                    "node_id": "korx-sem",
                    "node_kind": "guard",
                    "phi_cps": self.phi_cps,
                    "rollback_threshold": self.rollback_threshold,
                    "instance_type": "korx_sem",
                },
            )
        except Exception:
            pass  # Best effort

        return self.phi_cps


# ── KORX-L1 State Kernel ─────────────────────────────────────────────

class KORXStateKernel:
    """Persistance binaire KORX-L1 via mmap sur state.kbin (372 octets)."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or STATE_KBIN_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_file()

    def _ensure_file(self) -> None:
        """Crée le fichier state.kbin s'il n'existe pas."""
        if not self.path.exists():
            data = bytearray(STATE_KBIN_SIZE)
            # Header magique
            data[0:4] = HEADER_MAGIC
            # WAL Sequence ID = 0
            struct.pack_into("<Q", data, WAL_SEQ_OFFSET, 0)
            # IntentHash placeholder (128 bits)
            struct.pack_into("<16s", data, INTENT_HASH_OFFSET, b"\x00" * 16)
            # Runner bitmask 256 bytes (all zeros)
            # phi_cps float64 = 4.559
            struct.pack_into("<d", data, PHI_CPS_OFFSET, 4.559)
            # Timestamp cognitif
            struct.pack_into("<d", data, PHI_CPS_OFFSET + 8, 0.0)
            # System metrics 100 bytes (all zeros)
            # Git count = 0
            struct.pack_into("<I", data, GIT_COUNT_OFFSET, 0)
            # Git PIDs 4 x uint32 (all zeros)
            # Git lock bitmask 12 bytes (all zeros)
            # Signature placeholder 32 bytes
            struct.pack_into("<32s", data, SIGNATURE_OFFSET, b"\x00" * 32)
            self.path.write_bytes(data)

    def _mmap(self) -> mmap.mmap:
        """Mappe le fichier en mémoire (O(1) recovery)."""
        fd = open(self.path, "r+b")
        return mmap.mmap(fd.fileno(), STATE_KBIN_SIZE)

    # ── WAL Sequence ──────────────────────────────────────────────────

    def read_wal_seq(self) -> int:
        """Lit le WAL Sequence ID."""
        with self._mmap() as m:
            return struct.unpack_from("<Q", m, WAL_SEQ_OFFSET)[0]

    def write_wal_seq(self, seq: int) -> None:
        """Écrit le WAL Sequence ID."""
        with self._mmap() as m:
            struct.pack_into("<Q", m, WAL_SEQ_OFFSET, seq)

    # ── IntentHash ───────────────────────────────────────────────────

    def read_intent_hash(self) -> bytes:
        """Lit l'IntentHash d'Activation (128 bits)."""
        with self._mmap() as m:
            return bytes(m[INTENT_HASH_OFFSET:INTENT_HASH_OFFSET + 16])

    def write_intent_hash(self, hash_bytes: bytes) -> None:
        """Écrit l'IntentHash d'Activation."""
        with self._mmap() as m:
            m[INTENT_HASH_OFFSET:INTENT_HASH_OFFSET + 16] = hash_bytes[:16].ljust(16, b"\x00")

    # ── Runner Bitmask ───────────────────────────────────────────────

    def read_runner_bitmask(self) -> bytes:
        """Lit le bitmask des runners KIX (256 bytes)."""
        with self._mmap() as m:
            return bytes(m[RUNNER_BITMASK_OFFSET:RUNNER_BITMASK_OFFSET + 256])

    def write_runner_bitmask(self, bitmask: bytes) -> None:
        """Écrit le bitmask des runners."""
        with self._mmap() as m:
            m[RUNNER_BITMASK_OFFSET:RUNNER_BITMASK_OFFSET + 256] = bitmask[:256].ljust(256, b"\x00")

    # ── φ-CPS Score ──────────────────────────────────────────────────

    def read_phi_cps(self) -> float:
        """Lit le score φ-CPS."""
        with self._mmap() as m:
            return struct.unpack_from("<d", m, PHI_CPS_OFFSET)[0]

    def write_phi_cps(self, value: float) -> None:
        """Écrit le score φ-CPS."""
        with self._mmap() as m:
            struct.pack_into("<d", m, PHI_CPS_OFFSET, value)

    # ── SOMA Metrics ─────────────────────────────────────────────────

    def read_soma_metrics(self) -> bytes:
        """Lit les métriques SOMA (100 bytes)."""
        with self._mmap() as m:
            return bytes(m[SOMA_METRICS_OFFSET:SOMA_METRICS_OFFSET + 100])

    def write_soma_metrics(self, metrics: bytes) -> None:
        """Écrit les métriques SOMA."""
        with self._mmap() as m:
            m[SOMA_METRICS_OFFSET:SOMA_METRICS_OFFSET + 100] = metrics[:100].ljust(100, b"\x00")

    # ── Git Process Semaphore ────────────────────────────────────────

    def read_git_count(self) -> int:
        """Lit le nombre de processus git actifs."""
        with self._mmap() as m:
            return struct.unpack_from("<I", m, GIT_COUNT_OFFSET)[0]

    def write_git_count(self, count: int) -> None:
        """Écrit le nombre de processus git actifs (max 4)."""
        with self._mmap() as m:
            struct.pack_into("<I", m, GIT_COUNT_OFFSET, min(count, MAX_GIT_PROCESSES))

    def read_git_pids(self) -> List[int]:
        """Lit les PIDs git.exe autorisés (4 x uint32)."""
        with self._mmap() as m:
            return list(struct.unpack_from("<4I", m, GIT_PIDS_OFFSET))

    def write_git_pids(self, pids: List[int]) -> None:
        """Écrit les PIDs git.exe autorisés."""
        with self._mmap() as m:
            data = struct.pack("<4I", *([0] * 4))
            for i, pid in enumerate(pids[:4]):
                packed = struct.pack("<I", pid)
                m[GIT_PIDS_OFFSET + i * 4:GIT_PIDS_OFFSET + (i + 1) * 4] = packed

    def read_git_lock_bitmask(self) -> bytes:
        """Lit le bitmask des verrous .git/index.lock actifs (12 bytes)."""
        with self._mmap() as m:
            return bytes(m[GIT_LOCK_BITMASK_OFFSET:GIT_LOCK_BITMASK_OFFSET + 12])

    def write_git_lock_bitmask(self, bitmask: bytes) -> None:
        """Écrit le bitmask des verrous .git/index.lock."""
        with self._mmap() as m:
            m[GIT_LOCK_BITMASK_OFFSET:GIT_LOCK_BITMASK_OFFSET + 12] = bitmask[:12].ljust(12, b"\x00")

    def can_spawn_git(self) -> bool:
        """Vérifie si un nouveau processus git peut être lancé."""
        return self.read_git_count() < MAX_GIT_PROCESSES

    def register_git_process(self, pid: int) -> bool:
        """Enregistre un processus git. Retourne True si succès."""
        if not self.can_spawn_git():
            return False
        current_count = self.read_git_count()
        self.write_git_count(current_count + 1)
        pids = self.read_git_pids()
        pids[current_count % MAX_GIT_PROCESSES] = pid
        self.write_git_pids(pids)
        return True

    def unregister_git_process(self, pid: int) -> None:
        """Désenregistre un processus git."""
        current_count = self.read_git_count()
        if current_count > 0:
            self.write_git_count(current_count - 1)
        pids = self.read_git_pids()
        for i in range(len(pids)):
            if pids[i] == pid:
                pids[i] = 0
                break
        self.write_git_pids(pids)


# ── TIMX JWT Temps Cognitif ──────────────────────────────────────────

def validate_timx_token(token_wal_seq: int, current_wal_seq: int, delta_max: int = 1000) -> bool:
    """Valide un token JWT selon l'index WAL, pas l'horloge RTC."""
    return (current_wal_seq - token_wal_seq) <= delta_max


# ── CLI ──────────────────────────────────────────────────────────────

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="KIX-IMMUNE V21.0")
    parser.add_argument("command", choices=["status", "heartbeat", "reset", "phi_cps", "git"])
    args = parser.parse_args()

    if args.command == "status":
        soma = SOMA()
        status = soma.check_status()
        print(json.dumps(status, indent=2))

    elif args.command == "heartbeat":
        kernel = KORXStateKernel()
        seq = kernel.read_wal_seq()
        print(f"[KIX-IMMUNE] WAL seq: {seq}")

    elif args.command == "reset":
        kernel = KORXStateKernel()
        kernel.write_wal_seq(0)
        kernel.write_phi_cps(4.559)
        kernel.write_git_count(0)
        print("[KIX-IMMUNE] state.kbin reset")

    elif args.command == "phi_cps":
        bg = BernsteinG1()
        print(f"[KIX-IMMUNE] φ-CPS: {bg.phi_cps:.3f}")

    elif args.command == "git":
        kernel = KORXStateKernel()
        print(f"[KIX-IMMUNE] Git count: {kernel.read_git_count()}/{MAX_GIT_PROCESSES}")
        print(f"[KIX-IMMUNE] Can spawn: {kernel.can_spawn_git()}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
