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
