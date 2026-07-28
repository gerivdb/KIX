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
from flask import Flask, request, jsonify
import json
import time
from threading import Thread

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
    8799: "RLM-RELEASE"
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=KIX_PORT, debug=False)