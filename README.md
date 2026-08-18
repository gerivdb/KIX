# KIX

Central orchestrator for the gerivdb RLM runners.
Port: **8800**

## Endpoints

- `GET /health`
- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `GET /status/cross-service`
- `GET /vote`
- `GET /runners`
- `GET /runners/<name>/status`
- `GET /runners/<name>/health` — Health-check d'un runner
- `GET /runners/<name>/logs` — Logs d'un runner (`?lines=100`)
- `POST /runners/<name>/start` — **Authentification requise** (`admin`, `operator`)
- `POST /runners/<name>/stop` — **Authentification requise** (`admin`, `operator`)
- `POST /runners/<name>/restart` — **Authentification requise** (`admin`, `operator`)
- `GET /doctor` — Vérifie tous les runners
- `POST /doctor/run` — **Authentification requise** (`admin`, `operator`) — Redémarre les runners en erreur
- `GET /swarm/status` — État agrégé pour Agent Manager / N+2/N+3
- `GET /alerts` — Alertes en temps réel (φ-CPS, services en erreur)
  - `?service=<name>` — filtrer les alertes par service
- `GET /notifications/history` — Historique des notifications envoyées
  - `?limit=<n>` — nombre d'entrées (défaut: 100)
  - `?service=<name>` — filtrer par service
- `GET /remediation/status` — **Authentification requise** (`admin`)
- `GET /metrics` — Métriques JSON (runners + notifications)
- `GET /metrics/prometheus` — Métriques Prometheus (format texte)
- `GET /dashboard` — Dashboard web (services + φ-CPS + alertes récentes + métriques notification)
- `GET /events` — Flux SSE pour mise à jour temps réel du dashboard
- `POST /login` — Obtenir un JWT token
- `GET /probe/audit` — Audit de santé publique (sans authentification)
- `GET /audit` — **Authentification requise** (`admin`) — Journal des actions critiques

## Industrialisation

### Endpoints de readiness/liveness

- `GET /healthz` — Liveness probe (KIX répond)
- `GET /readyz` — Readiness probe (dépendances : runner store, notifications, audit)

### Statut cross-service

- `GET /status/cross-service` — Agrégat temps réel :
  - `runners` : statut détaillé de tous les services
  - `remediation_policies` : politiques d’auto‑remédiation actives
  - `notification_metrics` : métriques de notification par canal

### Intégration continue (KIVA-CLI)

Conformément à l'ADR-024 (CI souveraine), la CI KIX est gérée par KIVA-CLI :

```powershell
kiva ci run --dry-run KIX
```

- Validation souveraine sans dépendance GitHub Actions
- Tests `pytest` sur Python 3.12
- Variables d'environnement isolées (`KIX_DB`, `KIX_NOTIFICATIONS_DB`, `KIX_METRICS_DB`, `KIX_AUDIT_DB`)

### Monitoring cross-service

La route `/status/cross-service` agrège :

- Les statuts runners
- Les politiques d’auto‑remédiation
- Les métriques de notification

Elle peut être consommée par :

- Un monitoring externe (Prometheus, Datadog)
- Un service de supervision cross‑service (CTULU, MIMIR)
- Un health-check Kubernetes (`/readyz`)

## Stack

- Python 3.12
- Flask
- SQLite
- PyJWT

## Architecture Generic Runner Wrapper

KIX est l'orchestrateur unique de tous les services applicatifs DevTools/ENV2.

### Principe

- KIX définit une interface `RunnerBase` (start/stop/status/health/logs/restart)
- Chaque runtime fournit son wrapper dans `runners/` :
  - `PythonRunner` — services Python (WAZAA, BUZZ-X)
  - `ZigBinaryRunner` — binaires Zig (TRIX, LLUX, TIMX, ROOTX, TLM-LANG)
  - `GatewayRunner` — CLI externes (GATEWAY-MANAGER)
- Le registry est déclaratif dans `config/runners.yaml` — zéro logique de démarrage en dur

### Nouveaux endpoints

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/runners/<name>/health` | GET | Health-check d'un runner |
| `/runners/<name>/logs` | GET | Logs d'un runner (`?lines=100`) |
| `/runners/<name>/restart` | POST | Redémarre un runner |
| `/doctor` | GET | Vérifie tous les runners, retourne erreurs |
| `/doctor/run` | POST | Redémarre les runners en erreur |
| `/swarm/status` | GET | État agrégé pour Agent Manager / N+2/N+3 |

### Validation

```powershell
# Validation statique (chemins, fichiers)
python scripts/validate_runners.py

# Démarrage + health-check
python scripts/validate_runners.py --start

# Arrêt des runners démarrés
python scripts/validate_runners.py --stop
```

### Runner types supportés

| Type | Usage | Exemple |
|------|-------|---------|
| `python` | Services Python | WAZAA, BUZZ-X, KIX lui-même |
| `zig-binary` | Binaires Zig compilés | TRIX (`trixd.exe`) |
| `gateway-exe` | CLIs externes | GATEWAY-MANAGER |

### Build automatique (Zig)

Pour les runners `zig-binary`, ajouter un bloc `build` dans `runners.yaml` :

```yaml
runners:
  - name: trixd
    runner_type: zig-binary
    binary: zig-out/bin/trixd.exe
    build:
      command: ["zig", "build", "trixd"]
      required: true
      pre_start: true
```

`pre_start: true` exécute le build avant chaque démarrage. `required: true` bloque le démarrage si le build échoue.

### Gouvernance

- **Gates** : P-108 (ADR accepted), P-109 (Phase 1 testée), P-110 (BUZZ-X fonctionnel)
- **BUZZ-X** : exclu de la portée initiale — intégration en Phase 4 seulement après réparation de `busrunner.py`
- **Documentation** : `PRD-MOC-KIX-GENERIC-RUNNER-WRAPPER-2026-08-18.md` (TRIX)

## Authentification et contrôle d'accès (RBAC)

KIX utilise **JWT** pour protéger les endpoints sensibles. Trois rôles sont disponibles :

| Rôle | Droits |
|------|--------|
| `admin` | Accès complet + consultation de l'audit log |
| `operator` | Démarrage/arrêt des runners |
| `viewer` | Consultation seule |

### Obtenir un token

```powershell
curl -X POST http://localhost:8800/login `
  -H "Content-Type: application/json" `
  -d '{"username":"admin","password":"admin123"}'
```

Réponse :
```json
{
  "access_token": "<JWT_TOKEN>",
  "role": "admin",
  "username": "admin"
}
```

### Utiliser le token

Inclure le token dans le header `Authorization` :

```powershell
curl -X POST http://localhost:8800/runners/RLM-GRAPH/start `
  -H "Authorization: Bearer <JWT_TOKEN>"
```

### Endpoints protégés

| Endpoint | Rôles autorisés |
|----------|-----------------|
| `POST /runners/<name>/start` | `admin`, `operator` |
| `POST /runners/<name>/stop` | `admin`, `operator` |
| `POST /runners/<name>/restart` | `admin`, `operator` |
| `POST /doctor/run` | `admin`, `operator` |
| `GET /remediation/status` | `admin` |
| `GET /audit` | `admin` |

### Variables d'environnement

- `KIX_JWT_SECRET` : secret JWT (défaut: `dev-secret-change-me`)
- `KIX_USERS` : JSON des utilisateurs personnalisés (optionnel)
- `KIX_AUDIT_DB` : chemin vers la base d'audit (défaut: `data/audit.db`)

## Dashboard

Ouvrir `http://localhost:8800/dashboard`.

Le dashboard affiche :

### Vue d'ensemble (cartes résumé)
- **Runners** : nombre total de services supervisés
- **Healthy / Unhealthy** : répartition des états
- **φ-CPS** : valeur actuelle du coefficient de santé

### φ-CPS History
- **Graphique** : évolution temporelle de φ-CPS (limites 20/50/100 points)
- **Sélection** : boutons pour changer la plage historique affichée
- **Mise à jour en temps réel** : le graphique et les cartes sont rafraîchis via SSE (`/events`)

### Runners
- Statut, PID, dernier check pour chaque service

### Recent Alerts
- 10 dernières alertes MIMIR avec services concernés
- Indicateur `triggered` / `skipped`

### Notification Metrics
- Taux de succès, latence moyenne et dernière notification par canal

Badges :
- `running` : vert
- `stopped` : rouge
- `starting` : jaune
- `unknown` : gris
- `YES` (alert triggered) : rouge
- `NO` (alert skipped) : gris

## Runbook — Bridge KIX/MIMIR

### Démarrer le bridge

```powershell
cd D:/DO/WEB/TOOLS/L2-PLATFORM/KIX
python scripts/kix_mimir_bridge.py --kix http://localhost:8800 --mimir "D:/DO/WEB/TOOLS/L3-CITIZENS/MIMIR/data/metrics.db" --interval 5
```

Le bridge :
- interroge KIX toutes les 5 secondes,
- écrit φ-CPS, health et alerts dans `metrics.db`,
- peut être lancé en arrière-plan.

### Arrêter le bridge

Arrêter le processus Python correspondant, ou fermer le terminal.

### Vérifier l'état du pipeline

```powershell
cd D:/DO/WEB/TOOLS/L2-PLATFORM/KIX
python scripts/check_pipeline_health.py
```

Sortie attendue :
- `KIX /health: OK`
- `MIMIR phi_cps rows : <nombre>`
- `MIMIR health rows  : <nombre>`
- `MIMIR alert rows   : <nombre>`
- `Pipeline: HEALTHY`

### Interprétation des métriques

| Métrique | Signification |
|----------|--------------|
| φ-CPS > 0.9 | Majorité des services RLM sont joignables et en bonne santé |
| φ-CPS < 0.9 | Au moins un service est en erreur ; vérifier les alertes |
| `alert.triggered = YES` | Seuil franchi ; inspecter les services listés |
| `alert.triggered = NO` | Seuil non franchi ; l'alerte est historique |

### Dépannage

- **KIX ne répond pas** : vérifier que le processus Flask est en écoute sur le port 8800.
- **RLM tous `unknown`** : vérifier que les services RLM sont démarrés et écoutent sur leurs ports respectifs.
- **Aucune alerte dans MIMIR** : vérifier que le bridge est en cours d'exécution et que `metrics.db` est accessible.

## Alerting proactif

### Script `alert_notifier.py`

Surveille φ-CPS et envoie une notification quand il reste sous le seuil pendant N cycles consécutifs.

```powershell
# Dry-run (affichage console)
cd D:/DO/WEB/TOOLS/L2-PLATFORM/KIX
python scripts/alert_notifier.py --dry-run --threshold 0.9 --cycles 3 --interval 5

# Avec webhook (ex: Discord/Teams)
python scripts/alert_notifier.py --webhook-url "https://example.com/webhook" --threshold 0.9 --cycles 3

# Filtrer par service
python scripts/alert_notifier.py --service RLM-GRAPH --dry-run
```

Paramètres :
- `--kix` : URL de KIX (défaut: `http://localhost:8800`)
- `--threshold` : seuil φ-CPS (défaut: `0.9`)
- `--cycles` : nombre de cycles consécutifs sous seuil avant alerte (défaut: `3`)
- `--interval` : intervalle en secondes entre les checks (défaut: `5`)
- `--dry-run` : affiche les notifications sans les envoyer
- `--webhook-url` : URL du webhook pour les notifications
- `--service` : filtrer les alertes par nom de service

Variables d'environnement :
- `KIX_URL`, `MIMIR_DB`, `ALERT_THRESHOLD`, `ALERT_CYCLES`, `ALERT_INTERVAL`, `ALERT_WEBHOOK_URL`

## Historique des notifications

### Endpoint `/notifications/history`

Consulter l'historique des notifications envoyées :

```powershell
# Dernières 50 notifications
curl "http://localhost:8800/notifications/history?limit=50" | jq .

# Filtrer par service
curl "http://localhost:8800/notifications/history?service=RLM-GRAPH" | jq .
```

Réponse :
```json
{
  "service": "kix",
  "port": 8800,
  "count": 10,
  "notifications": [
    {
      "id": 1,
      "event": "phi_cps_degraded",
      "timestamp": "2026-07-28T04:00:00+00:00",
      "phi_cps": 0.7,
      "threshold": 0.9,
      "consecutive_cycles": 3,
      "service": "RLM-GRAPH",
      "channel": "webhook",
      "payload": "{...}"
    }
  ]
}
```

### Canaux de notification

#### Webhook

```powershell
python scripts/alert_notifier.py --webhook-url "https://example.com/webhook" --threshold 0.9 --cycles 3
```

#### Teams

```powershell
python scripts/alert_notifier.py --teams-webhook "https://outlook.office.com/webhook/..." --threshold 0.9 --cycles 3
```

Format Teams : MessageCard adapté avec titre, sous-titre et texte.

#### Email (SMTP)

```powershell
python scripts/alert_notifier.py `
  --smtp-host "smtp.gmail.com" `
  --smtp-port 587 `
  --smtp-user "user@gmail.com" `
  --smtp-password "app-password" `
  --email-from "kix@gerivdb.io" `
  --email-to "team@gerivdb.io" `
  --threshold 0.9 --cycles 3
```

Variables d'environnement pour email :
- `ALERT_SMTP_HOST`, `ALERT_SMTP_PORT`, `ALERT_SMTP_USER`, `ALERT_SMTP_PASSWORD`, `ALERT_EMAIL_FROM`, `ALERT_EMAIL_TO`

### Combinaison de canaux

Plusieurs canaux peuvent être actifs simultanément :

```powershell
python scripts/alert_notifier.py `
  --webhook-url "https://example.com/webhook" `
  --teams-webhook "https://outlook.office.com/webhook/..." `
  --smtp-host "smtp.gmail.com" --smtp-port 587 --smtp-user "user@gmail.com" --smtp-password "pass" --email-from "kix@gerivdb.io" --email-to "team@gerivdb.io" `
  --threshold 0.9 --cycles 3
```

## Observabilité

### Endpoint `/metrics`

Métriques JSON incluant les runners et les notifications :

```powershell
curl http://localhost:8800/metrics | jq .
```

Réponse :
```json
{
  "service": "kix",
  "port": 8800,
  "runners_total": 10,
  "runners_running": 8,
  "runners_stopped": 2,
  "notifications": {
    "webhook": {
      "total_sent": 10,
      "total_success": 9,
      "total_failed": 1,
      "success_rate": 0.9,
      "avg_latency_ms": 120.5,
      "last_sent_at": "2026-07-28T04:00:00+00:00"
    }
  },
  "timestamp": "2026-07-28T04:00:00+00:00"
}
```

### Endpoint `/metrics/prometheus`

Métriques au format Prometheus texte :

```powershell
curl http://localhost:8800/metrics/prometheus
```

Sortie :
```
# HELP kix_notification_total_total Total notifications sent per channel
# TYPE kix_notification_total_total counter
kix_notification_total_total{channel="webhook"} 10
kix_notification_total_total{channel="teams"} 5
# HELP kix_notification_success_total Total successful notifications per channel
# TYPE kix_notification_success_total counter
kix_notification_success_total{channel="webhook"} 9
kix_notification_success_total{channel="teams"} 5
# HELP kix_notification_failed_total Total failed notifications per channel
# TYPE kix_notification_failed_total counter
kix_notification_failed_total{channel="webhook"} 1
# HELP kix_notification_latency_seconds Average notification latency per channel
# TYPE kix_notification_latency_seconds gauge
kix_notification_latency_seconds{channel="webhook"} 0.1205
```

### Dashboard — Section Notification Metrics

Le dashboard inclut maintenant une section **Notification Metrics** qui affiche :
- **Channel** : nom du canal (webhook, email, teams)
- **Total Sent** : nombre total de notifications envoyées
- **Success** : nombre de notifications réussies
- **Failed** : nombre de notifications échouées
- **Success Rate** : taux de succès (0.0 - 1.0)
- **Avg Latency (ms)** : latence moyenne d'envoi
- **Last Sent** : date du dernier envoi

### OpenTelemetry

Le script `alert_notifier.py` génère des traces OpenTelemetry pour chaque envoi de notification :

- Span name : `notification.send.<channel>`
- Attributs : `notification.channel`, `notification.service`, `notification.phi_cps`
- Status : `OK` ou `ERROR` selon le résultat

Pour activer la collecte OpenTelemetry, configurer les variables d'environnement OTLP standards (`OTEL_EXPORTER_OTLP_ENDPOINT`, etc.).

## Auto-remédiation

### Script `auto_remediation.py`

Le moteur d'auto-remédiation lit les politiques définies dans `config/automation.yaml` et exécute des actions automatiques quand les conditions sont remplies.

```powershell
# Dry-run (simulation)
cd D:/DO/WEB/TOOLS/L2-PLATFORM/KIX
python scripts/auto_remediation.py --dry-run

# Déclencher une remédiation manuelle pour un service
python scripts/auto_remediation.py --dry-run --service RLM-GRAPH

# Exécuter toutes les politiques
python scripts/auto_remediation.py
```

Paramètres :
- `--kix` : URL de KIX (défaut: `http://localhost:8800`)
- `--config` : chemin vers `automation.yaml` (défaut: `config/automation.yaml`)
- `--dry-run` : simulation sans exécution réelle
- `--service` : filtrer par nom de service
- `--action` : type d'action (`restart`, `notify`, `all`)
- `--interval` : intervalle en secondes entre les cycles (défaut: 10)

### Endpoint `/remediation/status`

Consulter l'historique des actions de remédiation :

```powershell
curl http://localhost:8800/remediation/status | jq .
```

Réponse :
```json
{
  "service": "kix",
  "port": 8800,
  "count": 5,
  "remediations": [
    {
      "policy_id": "restart-unreachable-runner",
      "service": "RLM-GRAPH",
      "action_type": "restart_runner",
      "success": 1,
      "detail": "restart triggered for RLM-GRAPH",
      "timestamp": "2026-07-28T05:00:00+00:00"
    }
  ]
}
```

### Politiques par défaut

Le fichier `config/automation.yaml` contient les politiques suivantes :

| Politique | Condition | Action |
|-----------|-----------|--------|
| `restart-unreachable-runner` | `runner.status == "unreachable"` | Redémarrer le runner |
| `restart-stopped-runner` | `runner.status == "stopped"` | Redémarrer le runner (délai 5s) |
| `alert-on-phi-cps-degraded` | `phi_cps < 0.9` | Notification webhook/Teams |
| `escalation-after-multiple-failures` | `consecutive_failures >= 3` | Notification email |

### Variables d'environnement

- `AUTOMATION_CONFIG` : chemin vers `automation.yaml`
- `KIX_REMEDIATION_DB` : chemin vers la base de remédiation (défaut: `data/remediation.db`)
- `REMEDIATION_INTERVAL` : intervalle de cycle en secondes

## Audit log

### Endpoint `/audit` (admin only)

Consulter l'historique des actions critiques :

```powershell
curl http://localhost:8800/audit `
  -H "Authorization: Bearer <admin_token>"
```

Réponse :
```json
{
  "service": "kix",
  "port": 8800,
  "count": 10,
  "audit": [
    {
      "id": 1,
      "action": "runner_start",
      "endpoint": "/runners/RLM-GRAPH/start",
      "method": "POST",
      "username": "admin",
      "timestamp": "2026-07-28T06:00:00+00:00",
      "details": "started RLM-GRAPH",
      "ip_address": "127.0.0.1"
    }
  ]
}
```

Paramètres :
- `?limit=<n>` : nombre d'entrées (défaut: 100)

### Actions tracées

- Démarrage/arrêt des runners (`runner_start`, `runner_stop`)
- Consultation de l'état de remédiation (`remediation_status_view`)


