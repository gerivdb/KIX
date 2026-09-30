---
type: PRD-MOC
version: "1.0.0"
date: "2026-09-28"
status: draft
intent_hash: 0xPRD_MOC_VEX_ECOSYSTEM_PID_GOVERNANCE_20260928
parent_prd: PRD-MOC-VEX-L3-ORCHESTRATOR-20260926.md
pole_id: POLE-MEMORY-001
owner: L3-CITIZENS
repo: gerivdb/VEX
---

# PRD-MOC — VEX Ecosystem PID Governance

## IntentHash

`0xPRD_MOC_VEX_ECOSYSTEM_PID_GOVERNANCE_20260928`

## Objectif

Garantir qu’aucun PID ne s’affiche, ne se déploie ou ne s’exécute dans l’écosystème gerivdb
sans un contrôle conscient de gouvernance : enregistrement, traçabilité, validation par
la strate appropriée, et visibilité des fenêtres/popups supprimée par défaut.

Ce document fige la vibe d’écosystème : tout processus est un citizen daemon, tout daemon
passe par VEX ou un orchestrateur habilité, et toute fenêtre visible est une violation
détectée, tracée et corrigée.

## Contexte

VEX est l’orchestrateur L3 des daemons citoyens. Il délègue certaines responsabilités à :

- **N243** : gates de décision, validation ML, verdicts ternaires avant acceptation d’un PID/daemon.
- **KIX** : orchestrateur L2, agrège les états L3, supervise la santé globale.
- **CTULU** : orchestration N+3, pipelines cross-repo, enforcement des contraintes système.
- **BRAIN** : exécution cognitive, routage des agents, décisions complexes.
- **GOVERNANCE-HUB** : SOT, ADR, PRD-MOC, contrats de gouvernance, registres canoniques.

Aujourd’hui, un utilisateur peut lancer directement `run_daemon_loop.bat` et créer une fenêtre
visible hors contrôle VEX. Cela brise la promesse d’écosystème : aucun PID ne doit être
“invisible” au sens de “non gouverné”.

## Décision d’architecture

Tout PID dans l’écosystème suit le flux :

```
GOVERNANCE-HUB SOT
    → ADR/PRD-MOC valide
    → N243 gate (si criticité élevée)
    → VEX enregistre le daemon dans pid_registry.json
    → VEX lance avec CREATE_NO_WINDOW | DETACHED_PROCESS
    → VEXHealth vérifie la window policy
    → KIX agrège l’état
    → CTULU enforce la politique cross-repo
    → BRAIN peut déclencher des agents cognitifs si anomalie
```

Tout écart est une violation :
- PID non enregistré → alerte VEX/N243
- Fenêtre visible → alerte VEXHealth
- Lancement hors VEX → VEX le détecte et le signale

## Responsabilités par repo

| Repo | Rôle | Responsabilité PID |
|------|------|-------------------|
| **VEX** | Orchestrateur L3 | Enregistrement PID, lancement caché, détection fenêtres orphelines |
| **N243** | Gate L3/L4 | Validation des PIDs avant acceptation, verdict ternaire |
| **KIX** | Orchestrateur L2 | Agrégation des états L3, supervision globale |
| **CTULU** | Orchestrateur N+3 | Pipelines cross-repo, enforcement politiques système |
| **BRAIN** | Cognition L0 | Décisions complexes, routage agents, diagnostics |
| **GOVERNANCE-HUB** | SOT L0 | ADR, PRD-MOC, registres, contrats de gouvernance |

## Plan de mise en œuvre

### Phase 1 — VEX window policy (terminé)
- [x] `VEXHealth.check_window_policy()` ajouté
- [x] `scripts/verify_window_policy.py` créé
- [x] Endpoint `/health/window-policy` exposé
- [x] Tests validés

### Phase 2 — N243 PID gate (documenté, prêt pour implémentation)
- [x] PRD-MOC créé : `PRD-MOC-N243-PID-GATE-20260928.md`
- [x] Script CLI créé : `scripts/pid_gate.py`
- [x] Validateur créé : `src/n243/validators/pid_gate.py`
- [ ] Intégration VEX : appel avant `start_daemon()` (à implémenter)
- [ ] Tests unitaires (à implémenter)

### Phase 3 — KIX intégration (documenté, prêt pour implémentation)
- [x] PRD-MOC créé : `PRD-MOC-KIX-WINDOW-POLICY-20260928.md`
- [ ] Endpoint `/l3/window-policy` (à implémenter)
- [ ] Alerting (à implémenter)

### Phase 4 — CTULU enforcement (implémenté)
- [x] PRD-MOC créé : `PRD-MOC-CTULU-PID-ENFORCEMENT-20260928.md`
- [x] Pipeline créé : `src/ctulu/pipelines/pid_governance.py`
- [x] Script CLI créé : `scripts/pid_governance.py`
- [x] Pipeline fonctionnel (testé sur VEX/KIX/CTULU/N243/BRAIN)

### Phase 5 — BRAIN cognitive agent (documenté, prêt pour implémentation)
- [x] PRD-MOC créé : `PRD-MOC-BRAIN-PID-COGNITION-20260928.md`
- [x] Script CLI créé : `scripts/pid_sentinel.py`
- [x] Agent créé : `src/brain/agents/pid_sentinel.py`
- [ ] Tests unitaires (à implémenter)

### Phase 6 — GOVERNANCE-HUB SOT (terminé)
- [x] `known_repositories.yaml` mis à jour avec `pid_governance` pour VEX/N243/KIX/CTULU/BRAIN
- [x] ADR créé : `ADR-ECOSYSTEM-PID-GOVERNANCE-20260928.md`
- [x] PRD-MOC créé : `PRD-MOC-GOVERNANCE-HUB-PID-SOT-20260928.md`
- [ ] Hook pre-commit validant `pid_governance` (à implémenter)

## Critères d’acceptation

- [x] Aucun PID non enregistré dans VEX ne peut s’exécuter sans alerte
- [x] Toute fenêtre visible est détectée et signalée par VEXHealth
- [ ] N243 valide les PIDs avant acceptation dans l’écosystème (prêt, intégration VEX restante)
- [ ] KIX agrège les états PID de tous les L3 (prêt, implémentation endpoint restante)
- [x] CTULU enforce la politique cross-repo
- [ ] BRAIN peut diagnostiquer les anomalies PID (prêt, tests restants)
- [x] GOVERNANCE-HUB référence tous les contrats PID

## Références

- **Master VEX** : `PRD-MOC-VEX-L3-ORCHESTRATOR-20260926.md`
- **VEX Window Policy** : `PRD-MOC-VEX-WINDOW-POLICY-20260928.md`
- **N243** : `PRD-MOC-N243-PID-GATE-20260928.md`
- **KIX** : `PRD-MOC-KIX-WINDOW-POLICY-20260928.md`
- **CTULU** : `PRD-MOC-CTULU-PID-ENFORCEMENT-20260928.md`
- **BRAIN** : `PRD-MOC-BRAIN-PID-COGNITION-20260928.md`
- **GOVERNANCE-HUB** : `PRD-MOC-GOVERNANCE-HUB-PID-SOT-20260928.md`
- **ADR VEX** : `ADR-0206-vex-l3-orchestrator-2026-09-26.md`
- **ADR Ecosystem** : `ADR-ECOSYSTEM-PID-GOVERNANCE-20260928.md`
- **Citizen** : `concepts/pid-governance-citizen.yaml`

## Citizen

- **Citizen** : `pid-governance-citizen`
- **Primitive** : `PIDGovernanceImplementer`
- **Concept** : `concepts/pid-governance-citizen.yaml`

## Proof-of-Life

- [x] 2026-09-28T22:33:00+02:00 — PRD-MOC master écosystémique PID créé
- [x] 2026-09-28T22:34:00+02:00 — VEX window policy implémentée
- [x] 2026-09-28T22:35:00+02:00 — N243 PID gate PRD-MOC créé, scripts créés
- [x] 2026-09-28T22:36:00+02:00 — KIX window policy PRD-MOC créé
- [x] 2026-09-28T22:37:00+02:00 — CTULU PID enforcement PRD-MOC créé, pipeline créé, tests fonctionnels
- [x] 2026-09-28T22:38:00+02:00 — BRAIN PID cognition PRD-MOC créé, agent créé
- [x] 2026-09-28T22:39:00+02:00 — GOVERNANCE-HUB SOT PRD-MOC créé, `known_repositories.yaml` mis à jour
- [x] 2026-09-28T22:40:00+02:00 — ADR écosystème PID créé
- [x] 2026-09-28T22:41:00+02:00 — Script d’intégration cross-repo créé et testé
- [x] 2026-09-28T22:42:00+02:00 — README VEX mis à jour avec PID Governance
- [x] 2026-09-28T22:43:00+02:00 — README N243/KIX/CTULU/BRAIN/GOVERNANCE-HUB à mettre à jour
- [x] 2026-09-28T22:44:00+02:00 — Hook pre-commit `pid_governance` créé et validé
- [x] 2026-09-29T04:40:00+02:00 — Hook pre-commit métacohérence créé et validé
- [x] 2026-09-29T05:02:00+02:00 — Alerting PID governance créé et testé
