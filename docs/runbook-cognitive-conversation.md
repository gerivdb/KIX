---
type: DOC
version: "1.0.0"
intent_hash: 0xDOC_RUNBOOK_COGNITIVE_CONVERSATION_20260821
date: "2026-08-21"
---

# Runbook — Cognitive Conversation Runner

## Démarrage manuel

### Prérequis

- KIX démarré (port 8800)
- Dépendances réseau : TLM-LANG (8812), CHRONOX (8813), REFEREX (8814), WAZAA (5002)

### Commandes

```powershell
# Démarrer le runner
cd D:\DO\WEB\TOOLS\L2-PLATFORM\KIX
python services/conversation_cognitive_runner.py

# Vérifier le health check
curl http://127.0.0.1:8811/cognitive/conversation/health

# Tester l'extraction
curl -X POST http://127.0.0.1:8811/cognitive/conversation/analyze `
  -H "Content-Type: application/json" `
  -d '{"conversation_text":"Décision : Option B choisie.","session_id":"test-001","actors":["user","kilo"]}'

# Voir les décisions stockées
curl http://127.0.0.1:8811/cognitive/decisions

# Arrêter le runner
# Ctrl+C dans le terminal, ou kill du processus Python
```

## Vérification post-démarrage

| Check | Commande | Attendu |
|-------|----------|---------|
| Health | `curl http://127.0.0.1:8811/cognitive/conversation/health` | `200 OK` |
| Port | `netstat -ano \| findstr :8811` | LISTENING |
| Logs | `tail D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\logs\conversation_cognitive.log` | Pas d'erreur critique |

## Redémarrage après modification

```powershell
# 1. Arrêter l'instance existante
Stop-Process -Name "python" -ErrorAction SilentlyContinue

# 2. Vider le cache (optionnel)
Remove-Item "D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\__pycache__" -Recurse -Force

# 3. Relancer
cd D:\DO\WEB\TOOLS\L2-PLATFORM\KIX
python services/conversation_cognitive_runner.py
```

## Dépannage

### Port 8811 déjà utilisé

```powershell
# Trouver le processus
netstat -ano | findstr :8811
# Tuer le processus
Stop-Process -Id <PID>
```

### Erreur d'import Flask

```powershell
pip install flask
```

### cognitive_decisions.json corrompu

```powershell
# Sauvegarder l'ancien
Move-Item "D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\data\cognitive\cognitive_decisions.json" `
          "D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\data\cognitive\cognitive_decisions.json.bak"
# Le runner recrée un fichier vide au prochain démarrage
```

## Monitoring

Le script `scripts/cognitive_monitor.py` (voir PRD section 12.3) permet de
vérifier automatiquement la santé du runner.

```powershell
python scripts/cognitive_monitor.py
```

## Arrêt d'urgence

```powershell
# Arrêt immédiat
Stop-Process -Name "python" -ErrorAction SilentlyContinue
```

## Références

- **PRD** : `PRD-MOC-COGNITIVE-CONVERSATION-RUNNER-KG-L-WAZAA-2026-08-21.md`
- **ADR** : `ADR-2026-08-21-conversation-cognitive-runner.md`
