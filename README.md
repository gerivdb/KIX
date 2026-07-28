# KIX

Central orchestrator for the gerivdb RLM runners.
Port: **8800**

## Endpoints

- `GET /health`
- `GET /metrics`
- `GET /vote`
- `GET /runners`
- `GET /runners/<name>/status`
- `POST /runners/<name>/start`
- `POST /runners/<name>/stop`
- `GET /alerts` — Alertes en temps réel (φ-CPS, services en erreur)
  - `?service=<name>` — filtrer les alertes par service
- `GET /notifications/history` — Historique des notifications envoyées
  - `?limit=<n>` — nombre d'entrées (défaut: 100)
  - `?service=<name>` — filtrer par service
- `GET /dashboard` — Dashboard web (services + φ-CPS + alertes récentes)
- `GET /events` — Flux SSE pour mise à jour temps réel du dashboard

## Stack

- Python 3.12
- Flask
- SQLite

## Dashboard

Ouvrir `http://localhost:8800/dashboard`.

Le dashboard affiche :
- **RLM services** : statut, PID, dernier check
- **φ-CPS History** : historique du coefficient de santé
- **Recent Alerts** : 10 dernières alertes MIMIR avec services concernés

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
