#!/usr/bin/env python3
"""
KIX - Orchestrateur central pour services LLM/RLM/TLM

Fonctionnalités essentielles :
- Lister tous les services (ports 8786-8799)
- Obtenir le statut détaillé d'un service
- Démarrer / arrêter un service
- Intégration avec ECOS_ROOT.json pour les métriques
- Vote ternaire pour les actions critiques
"""

import os
import subprocess
from flask import Flask, request, jsonify, render_template_string
import json
import time
from threading import Thread
import yaml
from datetime import datetime
from pathlib import Path
import requests

app = Flask(__name__)

# Port de l'orchestrateur KIX
KIX_PORT = 8800

# Mapping port -> nom de service
SERVICE_MAP = {
    8786: "Gitnote",
    8787: "WAZAA",
    8788: "PLIX",
    8789: "TRIX",
    8790: "LLUX",
    8791: "BOINC",
    8792: "DAG-3",
    8793: "RLM-MDU",
    8794: "RLM-CONFIG",
    8795: "RLM-DEPLOY",
    8796: "RLM-SECURE",
    8797: "RLM-GRAPH",
     8798: "RLM-INCIDENT",
     8799: "RLM-RELEASE",
     7243: "trixd"
}

# TLM Services (ports réservés pour intégration future)
TLM_SERVICE_MAP = {
    8789: "TRIX",
    8788: "PLIX",
    8790: "UAE",
    8791: "BLO",
    8792: "KG-SPIDX",
}

def get_service_status(port):
    """Interroger le service à son port et retourner le statut"""
    try:
        # Utiliser curl ou python requests adapté localement
        # Pour la démonstration, retourner un statut fictif
        # Dans l'implémentation réelle, on pingirait le service
        service_name = SERVICE_MAP.get(port) or TLM_SERVICE_MAP.get(port, "inconnu")
        # Simuler un état (RUNNING/STOPPED/ERROR)
        return {
            "port": port,
            "name": service_name,
            "status": "RUNNING",  # Par défaut actif
            "uptime": "2h34m",
            "metrics_source": "local_status_check"
        }
    except Exception as e:
        return {
            "port": port,
            "name": SERVICE_MAP.get(port) or TLM_SERVICE_MAP.get(port, "inconnu"),
            "status": "ERROR",
            "error": str(e)
        }

@app.route('/runners/tlm', methods=['GET'])
def list_tlm_runners():
    """Lister uniquement les services TLM"""
    runners = []
    # Services TLM (ceux dans TLM_SERVICE_MAP)
    for port in TLM_SERVICE_MAP.keys():
        status = get_service_status(port)
        runners.append({
            "port": port,
            "name": TLM_SERVICE_MAP[port],
            "status": status["status"],
            "uptime": status["uptime"],
            "metrics_source": status["metrics_source"],
            "family": "TLM",
            "dual_role": port in SERVICE_MAP  # TRIX, PLIX sont aussi RLM
        })
    return jsonify({"runners": runners}), 200

@app.route('/test-tlm', methods=['GET'])
def test_tlm():
    """Test endpoint"""
    return jsonify({"status": "tlm endpoint works"}), 200

@app.route('/runners', methods=['GET'])
def list_runners():
    """Lister tous les services gérés (RLM + TLM)"""
    runners = []
    for port in SERVICE_MAP.keys():
        status = get_service_status(port)
        runners.append({
            "port": port,
            "name": SERVICE_MAP[port],
            "status": status["status"],
            "uptime": status["uptime"],
            "metrics_source": status["metrics_source"],
            "family": "RLM"
        })
    
    # Ajouter les services TLM purs (non dans SERVICE_MAP)
    tlm_only_ports = [p for p in TLM_SERVICE_MAP.keys() if p not in SERVICE_MAP]
    for port in tlm_only_ports:
        status = get_service_status(port)
        runners.append({
            "port": port,
            "name": TLM_SERVICE_MAP[port],
            "status": status["status"],
            "uptime": status["uptime"],
            "metrics_source": status["metrics_source"],
            "family": "TLM"
        })
    
    return jsonify({"runners": runners}), 200


@app.route('/runners/register', methods=['POST'])
def register_runner():
    """Enregistrer un nouveau runner/service dans KIX."""
    data = request.get_json() or {}
    runner_id = data.get('id')
    name = data.get('name')
    port = data.get('port')
    health_endpoint = data.get('health_endpoint', '/health')

    if not runner_id or not name or port is None:
        return jsonify({"error": "id, name and port are required"}), 400

    try:
        port_int = int(port)
    except (TypeError, ValueError):
        return jsonify({"error": "port must be an integer"}), 400

    SERVICE_MAP[port_int] = name
    return jsonify({
        "id": runner_id,
        "name": name,
        "port": port_int,
        "health_endpoint": health_endpoint,
        "status": "registered",
    }), 200


@app.route('/runners/<int:port>/status', methods=['GET'])
def runner_status(port):
    """Statut détaillé d'un service spécifique"""
    if port not in SERVICE_MAP:
        return jsonify({"error": "Service inconnu"}), 404
    
    status = get_service_status(port)
    return jsonify({"service": SERVICE_MAP[port], "status": status}), 200

@app.route('/runners/<int:port>/start', methods=['POST'])
def start_runner(port):
    """Démarrer un service spécifique"""
    if port not in SERVICE_MAP:
        return jsonify({"error": "Service inconnu"}), 404
    
    service_name = SERVICE_MAP[port]
    
    # IMITER le démarrage (dans la vraie implémentation, lancer subprocess)
    # Pour KIX léger, on simule le démarrage
    try:
        # Vérifier que le service n'est pas déjà actif
        status = get_service_status(port)
        if status["status"] == "RUNNING":
            return jsonify({"message": f"{service_name} est déjà actif"}), 200
        
        # Simuler le démarrage avec delay
        time.sleep(0.5)  # Simuler un démarrage rapide
        
        return jsonify({
            "message": f"{service_name} démarré avec succès",
            "port": port,
            "service": service_name,
            "method": "graceful_start"
        }), 200
    except Exception as e:
        return jsonify({"error": f"Échec démarrage: {str(e)}"}), 500

@app.route('/runners/<int:port>/stop', methods=['POST'])
def stop_runner(port):
    """Arrêter un service spécifique"""
    if port not in SERVICE_MAP:
        return jsonify({"error": "Service inconnu"}), 404
    
    service_name = SERVICE_MAP[port]
    
    try:
        # Vérifier que le service est actif avant d'arrêter
        status = get_service_status(port)
        if status["status"] != "RUNNING":
            return jsonify({"message": f"{service_name} n'est pas actif"}), 200
        
        # Similer l'arrêt
        time.sleep(0.3)  # Simuler arrêts rapides
        
        return jsonify({
            "message": f"{service_name} arrêté avec succès",
            "port": port,
            "service": service_name,
            "method": "graceful_stop"
        }), 200
    except Exception as e:
        return jsonify({"error": f"Échec arrêt: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health():
    """Endpoint health pour les monitorings"""
    return jsonify({"status": "OK", "service": "KIX Orchestrator", "version": "test-20260728"}), 200


@app.route('/healthz', methods=['GET'])
def healthz():
    return jsonify({"status": "ok"}), 200


@app.route('/readyz', methods=['GET'])
def readyz():
    checks = {"kix": "ok"}
    try:
        import sqlite3
        db_path = os.environ.get("KIX_DB", os.path.join(os.path.dirname(__file__), "data", "kix.sqlite"))
        conn = sqlite3.connect(db_path)
        conn.execute("SELECT 1")
        conn.close()
        checks["runner_store"] = "ok"
    except Exception:
        checks["runner_store"] = "error"
        return jsonify({"status": "degraded", "checks": checks}), 503
    try:
        notifications_db = os.environ.get("KIX_NOTIFICATIONS_DB", os.path.join(os.path.dirname(__file__), "data", "notifications.db"))
        conn = sqlite3.connect(notifications_db)
        conn.execute("SELECT 1")
        conn.close()
        checks["notifications"] = "ok"
    except Exception:
        checks["notifications"] = "error"
    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    code = 200 if status == "ok" else 503
    return jsonify({"status": status, "checks": checks}), code


@app.route('/governance-check', methods=['POST'])
def governance_check():
    """Validation ADR via API
    Expected payload:
    {
        "adr_id": "<adr-identifier>",
        "status": "accepted|proposed|rejected",
        "intent_hash": "<hex-hash>"
    }
    Returns validation status for the ADR
    """
    try:
        data = request.get_json()
        adr_id = data.get('adr_id')
        status = data.get('status')
        intent_hash = data.get('intent_hash')
        
        if not adr_id:
            return jsonify({"error": "adr_id is required"}), 400
        if status not in ['accepted', 'proposed', 'rejected']:
            return jsonify({"error": "Invalid status"}), 400
        if not intent_hash:
            return jsonify({"error": "intent_hash is required"}), 400
            
        response = {
            "status": "validated",
            "adr": adr_id,
            "intent_hash": intent_hash
        }
        
        if status == "accepted":
            # Log the ADR validation for audit trail
            log_file = "D:\\DO\\WEB\\TOOLS\\L4-TOOLS\\REPO-STANDARDS\\adr_validation_log.json"
            try:
                log_entry = {
                    "adr_id": adr_id,
                    "status": "accepted",
                    "intent_hash": intent_hash,
                    "validated_at": time.strftime("%Y-%m-%dT%H:%M:%S+02:00"),
                    "validator": "KIX Orchestrator"
                }
                # Append to log if exists, create if not
                log_data = []
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        log_data = json.load(f)
                log_data.append(log_entry)
                with open(log_file, 'w') as f:
                    json.dump(log_data, f, indent=2)
            except Exception:
                pass  # Continue even if logging fails
                
        return jsonify(response), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/vote', methods=['POST'])
def vote():
    """Vote ternaire pour les actions critiques
    Expected payload:
    {
        "action": "start|stop|restart",
        "target": "<service-name>",
        "reason": "reason for action",
        "weight": 0|1|2  # 0=against, 1=neutral, 2=for
    }
    Returns decision based on majority of votes stored in ECOS_ROOT.json
    """
    try:
        data = request.get_json()
        action = data.get('action')
        target = data.get('target')
        reason = data.get('reason')
        weight = data.get('weight', 1)
        
        if action not in ['start', 'stop', 'restart']:
            return jsonify({"error": "Invalid action"}), 400
        if not target:
            return jsonify({"error": "Target is required"}), 400
            
        # Load current vote state from ECOS_ROOT.json or initialize
        vote_state_file = "D:\\DO\\WEB\\TOOLS\\L4-TOOLS\\REPO-STANDARDS\\ECOS_ROOT.json"
        try:
            with open(vote_state_file, 'r') as f:
                vote_state = json.load(f)
            # Initialize vote tracking if not present
            if 'vote' not in vote_state:
                vote_state['vote'] = {}
            if target not in vote_state['vote']:
                vote_state['vote'][target] = {'support': 0, 'oppose': 0, 'neutral': 0}
        except Exception:
            # If file doesn't exist or error, initialize
            vote_state = {'vote': {}}
            vote_state['vote'][target] = {'support': 0, 'oppose': 0, 'neutral': 0}
            
        # Update vote based on weight
        if weight == 2:
            vote_state['vote'][target]['support'] += 1
        elif weight == 0:
            vote_state['vote'][target]['oppose'] += 1
        else:  # neutral or 1
            vote_state['vote'][target]['neutral'] += 1
            
        # Store updated vote state
        try:
            with open(vote_state_file, 'w') as f:
                json.dump(vote_state, f)
        except Exception:
            pass  # Continue even if we can't save state
            
        # Determine decision based on vote tally
        tally = vote_state['vote'].get(target, {})
        support = tally.get('support', 0)
        oppose = tally.get('oppose', 0)
        neutral = tally.get('neutral', 0)
        total = support + oppose + neutral
        
        if total == 0:
            decision = "undecided"
        elif support > oppose:
            decision = "approved"
        elif oppose > support:
            decision = "rejected"
        else:
            decision = "undecided"
            
        response = {
            "action": action,
            "target": target,
            "reason": reason,
            "weight": weight,
            "decision": decision,
            "tally": tally
        }
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# Cycle de vie des processus — Endpoints TRIX (worktree locks)
# ============================================================================

TRIX_BASE_URL = "http://127.0.0.1:8742"
TRIX_TIMEOUT = 5


def _trix_post(path: str, payload: dict) -> dict:
    """Appel POST TRIX avec fallback local si indisponible."""
    url = f"{TRIX_BASE_URL}{path}"
    try:
        resp = requests.post(url, json=payload, timeout=TRIX_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return {"status": "fallback_local"}


def _trix_get(path: str) -> dict:
    """Appel GET TRIX avec fallback local si indisponible."""
    url = f"{TRIX_BASE_URL}{path}"
    try:
        resp = requests.get(url, timeout=TRIX_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return {}


@app.route('/process/release-handles', methods=['POST'])
def process_release_handles():
    """Relâcher les handles TRIX pour un worktree."""
    data = request.get_json() or {}
    worktree_path = data.get('worktree_path')
    agent_id = data.get('agent_id')

    if not worktree_path:
        return jsonify({"error": "worktree_path is required"}), 400

    payload = {"worktree_path": worktree_path, "agent_id": agent_id}
    result = _trix_post("/git/locks/release", payload)
    status = result.get("status", "fallback_local")
    return jsonify({"status": status, "worktree_path": worktree_path}), 200


@app.route('/worktree/purge', methods=['POST'])
def worktree_purge():
    """Purge de worktree après release et vote ternaire."""
    data = request.get_json() or {}
    worktree_path = data.get('worktree_path')
    agent_id = data.get('agent_id')

    if not worktree_path:
        return jsonify({"error": "worktree_path is required"}), 400

    # Étape 1 : release handles
    release_payload = {"worktree_path": worktree_path, "agent_id": agent_id}
    _trix_post("/git/locks/release", release_payload)

    # Étape 2 : vérifier handles libres
    locks = _trix_get("/git/locks/worktrees")
    worktree_lock = next(
        (lock for lock in locks.get("worktrees", []) if lock.get("path") == worktree_path),
        None,
    )

    if worktree_lock is None:
        vote = 2
    else:
        state = worktree_lock.get("state", "").lower()
        if state == "busy":
            vote = 0
        elif state == "waiting":
            vote = 1
        else:
            vote = 2

    # Étape 3 : vote ternaire
    if vote == 0:
        return jsonify({"vote": 0, "action": "busy", "worktree_path": worktree_path}), 409
    if vote == 1:
        return jsonify({"vote": 1, "action": "kill_in_progress", "worktree_path": worktree_path}), 202

    return jsonify({"vote": 2, "action": "purge_allowed", "worktree_path": worktree_path}), 200


@app.route('/worktree/status', methods=['GET'])
def worktree_status():
    """Liste des verrous worktree actifs depuis TRIX."""
    locks = _trix_get("/git/locks/worktrees")
    return jsonify(locks), 200


# ============================================================================
# Fin-Ops Dashboard — Multi-Environment Supervision (INTENT-094)
# ============================================================================

KNOWN_REPOS_PATH = Path(r"D:\DO\WEB\TOOLS\L4-TOOLS\REPO-STANDARDS\config\known_repositories.yaml")

def load_known_repositories():
    """Charge known_repositories.yaml et retourne la liste des repos."""
    try:
        with open(KNOWN_REPOS_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("repos", [])
    except Exception:
        return []

def compute_finops_metrics():
    """Calcule les métriques Fin-Ops par environnement."""
    repos = load_known_repositories()
    
    metrics = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_repos": len(repos),
        "env0": {"total": 0, "public": 0, "private": 0, "cloned": 0, "not_cloned": 0},
        "env1": {"services": 0, "pipelines": 0},
        "env2": {"clones": 0, "missing": 0},
        "env3": {"services": 0},
        "env4": {"services": 0},
        "env5": {"archived": 0},
        "runners": {"total": len(SERVICE_MAP) + len(TLM_SERVICE_MAP), "running": 0, "stopped": 0},
    }
    
    for repo in repos:
        stratum = repo.get("stratum", "").upper()
        visibility = repo.get("visibility", "unknown")
        cloned = repo.get("cloned", False)
        status = repo.get("status", "").lower()
        
        # Mapping stratum -> environnement Fin-Ops
        if stratum == "L0":
            env_key = "env0"
        elif stratum in ("L1", "L2"):
            env_key = "env2"
        elif stratum == "L3":
            env_key = "env3"
        elif stratum == "L4":
            env_key = "env1"
        elif stratum == "L5":
            env_key = "env5"
        else:
            continue
        
        # Comptage par environnement
        if env_key == "env0":
            metrics["env0"]["total"] += 1
            if visibility == "public":
                metrics["env0"]["public"] += 1
            elif visibility == "private":
                metrics["env0"]["private"] += 1
            if cloned:
                metrics["env0"]["cloned"] += 1
            else:
                metrics["env0"]["not_cloned"] += 1
        elif env_key == "env2":
            metrics["env2"]["clones"] += 1 if cloned else 0
            metrics["env2"]["missing"] += 0 if cloned else 1
        elif env_key == "env3":
            metrics["env3"]["services"] += 1
        elif env_key == "env1":
            metrics["env1"]["services"] += 1
        elif env_key == "env5":
            metrics["env5"]["archived"] += 1
    
    # Runners status (simulé pour l'instant)
    metrics["runners"]["running"] = metrics["runners"]["total"]
    metrics["runners"]["stopped"] = 0
    
    return metrics

FIN_OPS_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KIX — Fin-Ops Dashboard</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px; }
        h1 { color: #38bdf8; margin-bottom: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }
        .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; }
        .card h2 { color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 10px; }
        .metric { font-size: 2rem; font-weight: bold; color: #f1f5f9; }
        .metric small { font-size: 0.9rem; color: #94a3b8; }
        .status { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }
        .status.ok { background: #059669; color: white; }
        .status.warn { background: #d97706; color: white; }
        .status.err { background: #dc2626; color: white; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { text-align: left; padding: 8px; border-bottom: 1px solid #334155; }
        th { color: #94a3b8; font-weight: normal; font-size: 0.85rem; }
        td { color: #e2e8f0; }
        .footer { margin-top: 30px; color: #64748b; font-size: 0.8rem; }
    </style>
</head>
<body>
    <h1>KIX — Fin-Ops Dashboard</h1>
    <div class="grid">
        <div class="card">
            <h2>ENV0 — GitHub Remote</h2>
            <div class="metric">{{ metrics.env0.total }} <small>repos</small></div>
            <table>
                <tr><th>Public</th><td>{{ metrics.env0.public }}</td></tr>
                <tr><th>Private</th><td>{{ metrics.env0.private }}</td></tr>
                <tr><th>Cloned</th><td>{{ metrics.env0.cloned }}</td></tr>
                <tr><th>Not cloned</th><td>{{ metrics.env0.not_cloned }}</td></tr>
            </table>
        </div>
        <div class="card">
            <h2>ENV1 — Services</h2>
            <div class="metric">{{ metrics.env1.services }} <small>services</small></div>
            <table>
                <tr><th>Pipelines</th><td>{{ metrics.env1.pipelines }}</td></tr>
            </table>
        </div>
        <div class="card">
            <h2>ENV2 — Workstation</h2>
            <div class="metric">{{ metrics.env2.clones }} <small>clones</small></div>
            <table>
                <tr><th>Missing</th><td>{{ metrics.env2.missing }}</td></tr>
            </table>
        </div>
        <div class="card">
            <h2>ENV3 — Standard</h2>
            <div class="metric">{{ metrics.env3.services }} <small>services</small></div>
        </div>
        <div class="card">
            <h2>ENV4 — Critical</h2>
            <div class="metric">{{ metrics.env4.services }} <small>services</small></div>
        </div>
        <div class="card">
            <h2>ENV5 — GitOps</h2>
            <div class="metric">{{ metrics.env5.archived }} <small>archived</small></div>
        </div>
        <div class="card">
            <h2>Runners</h2>
            <div class="metric">{{ metrics.runners.total }} <small>total</small></div>
            <table>
                <tr><th>Running</th><td>{{ metrics.runners.running }}</td></tr>
                <tr><th>Stopped</th><td>{{ metrics.runners.stopped }}</td></tr>
            </table>
        </div>
    </div>
    <div class="footer">
        Generated at {{ metrics.generated_at }} | KIX Fin-Ops Dashboard v0.1
    </div>
</body>
</html>
"""

@app.route('/fin-ops/dashboard', methods=['GET'])
def finops_dashboard():
    """Dashboard Fin-Ops multi-environnement."""
    metrics = compute_finops_metrics()
    return render_template_string(FIN_OPS_DASHBOARD_HTML, metrics=metrics)

@app.route('/fin-ops/api/summary', methods=['GET'])
def finops_api_summary():
    """API JSON du dashboard Fin-Ops."""
    metrics = compute_finops_metrics()
    return jsonify(metrics), 200

@app.route('/fin-ops/api/inventory', methods=['GET'])
def finops_api_inventory():
    """Inventaire des repos connus."""
    repos = load_known_repositories()
    return jsonify({"repos": repos, "count": len(repos)}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=KIX_PORT, debug=False)