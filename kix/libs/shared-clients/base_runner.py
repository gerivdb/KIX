#!/usr/bin/env python3
r"""
BaseRunner — Classe mère abstraite pour tous les runners KIX (Phase 1)
Élimine la duplication de health/metrics/WAZAA setup.

ERR_030: UTF-8 wrapper included.
"""
import io
import sys
import os
import signal
import threading
import time
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional

# ERR_030 FIX
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', effects='replace')

# Shared clients — support both package and direct import
try:
    from shared_clients.kg_l_client import KG_L_Client
    from shared_clients.wazaa_client import WAZAA_Client
    from shared_clients.vault_writer import VaultWriter
except ImportError:
    try:
        from kg_l_client import KG_L_Client
        from wazaa_client import WAZAA_Client
        from vault_writer import VaultWriter
    except ImportError:
        # Stubs for environments where dependencies are missing
        class KG_L_Client:
            def __init__(self, *a, **kw): pass
        class WAZAA_Client:
            def __init__(self, *a, **kw): pass
            def start(self): pass
            def stop(self): pass
            def subscribe(self, *a, **kw): pass
        class VaultWriter:
            def __init__(self, *a, **kw): pass
            def write_auto_index(self, *a, **kw): pass


class BaseRunner(ABC):
    """Base abstrait pour tous les runners KIX.
    
    Fournit:
    - Health endpoint (/health)
    - Metrics endpoint (/metrics)
    - WAZAA subscription setup
    - Signal handlers (SIGTERM/SIGINT)
    - DI container for shared clients
    
    DI container injecte: KG_L_Client, WAZAA_Client, VaultWriter
    via config.yaml (settings.yaml).
    """
    
    # Override in subclass
    runner_name: str = "base-runner"
    runner_version: str = "1.0.0"
    port: int = 8000
    config_path: str = "config.yaml"
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self._running = False
        self._start_time = None
        self._event_count = 0
        self._error_count = 0
        
        # DI Container — inject shared clients from config
        self._setup_di()
        
        # Setup signal handlers
        self._setup_signals()
        
        # Setup WAZAA subscriptions
        self._setup_wazaa()
    
    def _setup_di(self):
        """Setup dependency injection for shared clients."""
        di_config = self.config.get("di", {})
        
        self.kgl = KG_L_Client(
            host=self.config.get("kgl_host", "local"),
            data_path=self.config.get("kgl_data_path")
        )
        
        self.wazaa = WAZAA_Client(
            host=self.config.get("wazaa_host", "local")
        )
        
        self.vault = VaultWriter(
            vault_path=self.config.get("vault_path", "D:/DO/WEB/TOOLS/L0-CANON/VOLTX")
        )
        
        print(f"[BaseRunner] DI initialized for {self.runner_name}")
    
    def _setup_signals(self):
        """Setup signal handlers for graceful shutdown."""
        def handler(signum, frame):
            sig_name = signal.Signals(signum).name
            print(f"[BaseRunner] Received {sig_name}, shutting down...")
            self.stop()
        
        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)
    
    def _setup_wazaa(self):
        """Subscribe to WAZAA topics from config."""
        topics = self.config.get("wazaa_subscriptions", [])
        
        for topic_config in topics:
            topic = topic_config.get("topic")
            handler = topic_config.get("handler")
            if topic and handler:
                self.wazaa.subscribe(topic, getattr(self, handler, self._default_handler))
        
        if self.config.get("wazaa_host", "local") == "local":
            self.wazaa.start()
    
    def _default_handler(self, event):
        """Default event handler."""
        self._event_count += 1
        print(f"[BaseRunner] Unhandled event: {event.get('topic', 'unknown')}")
    
    def health(self) -> dict:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": self.runner_name,
            "version": self.runner_version,
            "build": self._get_build_timestamp(),
            "uptime_seconds": time.time() - self._start_time if self._start_time else 0,
            "events_processed": self._event_count,
            "errors": self._error_count
        }
    
    def metrics(self) -> dict:
        """Prometheus-style metrics."""
        return {
            f"{self.runner_name}_events_total": self._event_count,
            f"{self.runner_name}_errors_total": self._error_count,
            f"{self.runner_name}_uptime_seconds": time.time() - self._start_time if self._start_time else 0
        }
    
    def _get_build_timestamp(self) -> str:
        """Get build timestamp for fingerprinting."""
        return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(os.path.getctime(__file__)))
    
    def start(self):
        """Start the runner."""
        self._running = True
        self._start_time = time.time()
        print(f"[BaseRunner] {self.runner_name} started on port {self.port}")
    
    def stop(self):
        """Stop the runner."""
        self._running = False
        self.wazaa.stop()
        print(f"[BaseRunner] {self.runner_name} stopped")
    
    @abstractmethod
    def run(self):
        """Main runner loop — implement in subclass."""
        pass
    
    def run_with_server(self):
        """Start runner with HTTP server for /health and /metrics."""
        try:
            from flask import Flask, jsonify
            
            app = Flask(__name__)
            
            @app.route("/health")
            def health_endpoint():
                return jsonify(self.health())
            
            @app.route("/metrics")
            def metrics_endpoint():
                return jsonify(self.metrics())
            
            # Start runner in background thread
            runner_thread = threading.Thread(target=self.run, daemon=True)
            runner_thread.start()
            
            # Start HTTP server
            app.run(host="0.0.0.0", port=self.port, threaded=True)
            
        except ImportError:
            # No Flask — run without HTTP
            self.start()
            self.run()
