---
type: "PRD_MOC"
citizen: "L2-PLATFORM"
layer: "L2"
author: gerivdb
source_repo: gerivdb/KIX
source_path: PRD-MOC/PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md
parent_doc: PRD-MOC-KIX-MASTER.md
related_adr: ADR-2026-09-24-ECOSYSTEM-INTEGRATION.md, ADR-2026-09-24-KIX-MULTI-LANG-RUNNERS.md, ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md
related_moc: PRD-MOC-KIX-MASTER.md, PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md, PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md, PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md
version: "1.0.0"
date: "2026-09-27"
status: "implemented"
intent_hash: "0xVEX_KIX_BOUNDARIES_20260927"
mox_gates:
  - P-201
  - P-202
  - P-203
---

# PRD MOC - Frontières KIX / VEX — Contrat de Séparation des Orchestrations

## 1. RESUME EXECUTIF

Ce PRD MOC définit le **contrat de frontières** entre deux orchestrateurs de l'écosystème gerivdb :

- **KIX** (L2-PLATFORM) : orchestrateur central des **runners RLM** (services applicatifs L2).
- **VEX** (L3-CITIZENS) : orchestrateur des **daemons/agents autonomes L3**.

**Principe fondateur** : KIX et VEX partagent des concepts d'orchestration et de gestion de processus, mais leurs périmètres sont **strictement séparés**. Ce document verrouille les points d'intégration autorisés et les interdits de chevauchement.

**Périmètre** : Contrat de boundaries, endpoints de santé partagés, protocole WAZAA bus, responsabilités de déploiement.
**Statut** : **implemented** (2026-09-27) — Contrat actif, intégration opérationnelle.

---

## 2. CONTEXTE

### 2.1 Contexte

L'écosystème gerivdb comprend deux couches d'orchestration complémentaires :

| Couche | Orchestrateur | Rôle | Repo |
|--------|--------------|------|------|
| **L2-PLATFORM** | **KIX** | Runners RLM (services applicatifs L2), alerting, auto-remediation, dashboard, auth, audit | gerivdb/KIX |
| **L3-CITIZENS** | **VEX** | Daemons/agents autonomes L3, déploiement multi-OS (NSSM/schtasks/systemd), clients d'intégration | gerivdb/VEX |

**Problème** : Sans contrat de frontières explicite, les deux orchestrateurs peuvent :
- Dupliquer la gestion du cycle de vie d'un même processus
- Écrire dans des registres de santé concurrents
- Déclencher des redémarrages en cascade non coordonnés
- Créer des dépendances circulaires au bootstrap

### 2.2 État Actuel

| Composant | État |
|-----------|------|
| KIX orchestrateur | ✅ 100% fonctionnel (Phases 1-5 terminées) |
| VEX orchestrateur | ⚠️ Partiellement documenté |
| Contrat de frontières | ❌ Manquant — **ce document le crée** |
| Intégration santé croisée | 📄 Documentée mais non formalisée |
| WAZAA bus partagé | ✅ Opérationnel |

---

## 3. ARCHITECTURE CIBLE — CONTRAT DE FRONTIÈRES

### 3.1 Principe Fondateur

**KIX et VEX sont deux orchestrateurs spécialisés, non superposés.**

```
┌─────────────────────────────────────────────────────────────┐
│                     KIX (L2-PLATFORM)                        │
│  Port 8800 — Orchestrateur Runners RLM                      │
│                                                             │
│  Responsabilités :                                          │
│  • Cycle de vie des runners Python/Zig/Rust/Go/Node/Custom │
│  • Health checks parallélisés + Doctor/Self-Healing         │
│  • Swarm Status pour Agent Manager / N+2/N+3                │
│  • PID Registry, logs, métriques, WAL                       │
│  • Preflight & diagnostics infrastructure                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    ┌──────┴──────┐
                    │  Intégration│
                    │  Autorisée  │
                    └──────┬──────┘
                           │
┌──────────────────────────┼──────────────────────────────────┐
│                     VEX (L3-CITIZENS)                        │
│  Port <dynamic> — Orchestrateur Daemons L3                  │
│                                                             │
│  Responsabilités :                                          │
│  • Cycle de vie des daemons/agents autonomes L3             │
│  • Déploiement multi-OS (NSSM / schtasks / systemd)         │
│  • Clients d'intégration (interfaces with external systems) │
│  • Supervision daemons L3 agrégés                           │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Matrice de Responsabilités

| Domaine | KIX (L2) | VEX (L3) |
|---------|----------|----------|
| **Runners applicatifs L2** | ✅ Responsable | ❌ Hors périmètre |
| **Daemons/agents autonomes L3** | ❌ Hors périmètre | ✅ Responsable |
| **Health checks runners L2** | ✅ Responsable | 📡 Consommateur (`GET /health`) |
| **Health checks agrégés L3** | 📡 Consommateur (`GET /health/l3`) | ✅ Responsable |
| **Enregistrement santé L3** | 📡 Récepteur (`POST /health/l3`) | ✅ Émetteur (`POST /health/l3`) |
| **Bootstrap sequence** | ✅ Responsable (`bootstrap` runner, port 8810) | 📡 Participant |
| **Déploiement Windows (NSSM/schtasks)** | ⚠️ Supporté via `win32_process.py` | ✅ Responsable |
| **Déploiement Linux (systemd)** | ❌ Hors périmètre | ✅ Responsable |
| **PID Registry runners** | ✅ Responsable | ❌ Hors périmètre |
| **PID Registry daemons** | ❌ Hors périmètre | ✅ Responsable |
| **Doctor/Self-Healing runners** | ✅ Responsable | ❌ Hors périmètre |
| **Doctor/Self-Healing daemons** | ❌ Hors périmètre | ✅ Responsable |
| **WAZAA bus — événements runners** | ✅ Émetteur | 📡 Consommateur |
| **WAZAA bus — événements daemons** | 📡 Consommateur | ✅ Émetteur |
| **Swarm Status (Agent Manager)** | ✅ Responsable | 📡 Participant |
| **Auth / Audit / Logs** | ✅ Responsable | ❌ Hors périmètre |
| **Intégration clients externes** | ❌ Hors périmètre | ✅ Responsable |

---

## 4. POINTS D'INTÉGRATION AUTORISÉS

### 4.1 Endpoints de Santé Croisés

| Endpoint | Appelant | Cible | Usage | Protocole |
|----------|----------|-------|-------|-----------|
| `GET /health` | VEX | KIX | VEX vérifie que KIX est opérationnel avant de démarrer des dépendances L2 | HTTP REST |
| `GET /health/l3` | KIX | KIX | KIX retourne la santé L3 enregistrée par VEX | HTTP REST |
| `POST /health/l3` | VEX | KIX | VEX enregistre sa santé agrégée L3 dans KIX | HTTP REST |
| `GET /health` | KIX | VEX | KIX agrège la santé L3 via VEX pour le dashboard global | HTTP REST |

**Contrat** :
- Timeout : 5 secondes maximum
- Format réponse : `{"status": "ok|degraded|down", "timestamp": "<ISO-UTC>"}`
- En cas de timeout ou d'erreur 5xx : considérer la cible comme `degraded`, pas `down`
- `POST /health/l3` accepte un payload JSON et le stocke en mémoire volatile (RAM) pour exposition via `GET /health/l3`
- KIX ne persiste PAS les données L3 reçues (VEX est responsable de sa propre persistence)

### 4.2 WAZAA Bus — Événements Partagés

| Topic | Émetteur | Récepteur | Contenu |
|-------|----------|-----------|---------|
| `kix.runner.started` | KIX | VEX | Un runner L2 a démarré |
| `kix.runner.stopped` | KIX | VEX | Un runner L2 s'est arrêté |
| `kix.runner.health_changed` | KIX | VEX | Changement de santé d'un runner L2 |
| `vex.daemon.started` | VEX | KIX | Un daemon L3 a démarré |
| `vex.daemon.stopped` | VEX | KIX | Un daemon L3 s'est arrêté |
| `vex.daemon.health_changed` | VEX | KIX | Changement de santé d'un daemon L3 |
| `swarm.status.update` | KIX | VEX | Mise à jour du Swarm Status agrégé |

**Contrat** :
- Broker : WAZAA bus (port 1873)
- Format : JSON avec `topic`, `payload`, `timestamp`, `source` (`kix` ou `vex`)
- Aucun événement ne doit déclencher de cycle de vie sur l'autre orchestrateur sans validation préalable

### 4.3 Bootstrap Sequence — Coordination

| Rôle | Responsable | Action |
|------|-------------|--------|
| **Bootstrap orchestrator** | KIX (`bootstrap` runner, port 8810) | Démarre la séquence globale |
| **KIX self-check** | KIX | Vérifie que KIX API est prête (port 8800) |
| **VEX registration** | VEX | S'enregistre auprès de KIX via `/bootstrap/register` |
| **Ready signal** | KIX | Publie `/bootstrap/ready = true` quand tous les services requis sont opérationnels |

**Contrat** :
- VEX doit s'enregistrer auprès de KIX pendant le bootstrap
- KIX ne déclare pas `ready` tant que VEX n'est pas enregistré (si `dependencies` inclut `vex`)
- En cas d'échec VEX : KIX continue en mode dégradé (hors scope bloquant)

---

## 5. INTERDITS STRICTS

### 5.1 KIX ne doit PAS

- [❌] Gérer le cycle de vie des daemons L3 (VEX est responsable)
- [❌] Écrire dans le PID Registry de VEX
- [❌] Déclencher un redémarrage d'un daemon L3
- [❌] Déployer des services via NSSM/schtasks/systemd
- [❌] Considérer les daemons L3 comme des runners KIX

### 5.2 VEX ne doit PAS

- [❌] Gérer le cycle de vie des runners RLM L2 (KIX est responsable)
- [❌] Écrire dans le PID Registry de KIX
- [❌] Déclencher un redémarrage d'un runner L2
- [❌] Modifier `config/runners.yaml` de KIX
- [❌] Considérer les runners L2 comme des daemons VEX

### 5.3 Règles de Non-Interférence

| Règle | Description |
|-------|-------------|
| **Registry isolation** | KIX utilise `data/runner-state.json` ; VEX utilise son propre registre. Aucun partage de fichier/DB. |
| **Process isolation** | KIX ne termine pas un processus détenu par VEX, et inversement. |
| **Port isolation** | KIX gère les ports L2 (8800, 8810, 8823, 1873, 7719, etc.) ; VEX gère les ports L3. Aucune collision de port autorisée. |
| **Config isolation** | `config/runners.yaml` (KIX) et `config/daemons.yaml` (VEX) sont des fichiers distincts. |

---

## 6. CONTRAT DE SANTÉ PARTAGÉE

### 6.1 Schéma de Santé Unifié

```json
{
  "source": "kix|vex",
  "status": "ok|degraded|down",
  "timestamp": "2026-09-27T06:00:00Z",
  "components": [
    {
      "name": "trixd",
      "type": "runner|daemon",
      "status": "ok|degraded|down",
      "port": 8823,
      "uptime_seconds": 3600
    }
  ],
  "alerts": []
}
```

### 6.2 Agrégation Swarm Status

KIX agrège dans `/swarm/status` :
- Ses propres runners L2
- La santé L3 fournie par VEX (`GET /health`)

KIX ne doit pas :
- Modifier les données de santé L3 fournies par VEX
- Supprimer des composants L3 du rapport agrégé

VEX ne doit pas :
- Modifier les données de santé L2 fournies par KIX
- Supprimer des composants L2 du rapport agrégé

---

## 7. DÉPLOIEMENT — RESPONSABILITÉS

| Aspect | KIX | VEX |
|--------|-----|-----|
| **OS Windows** | Services Python/Zig/Gateway via `win32_process.py` | NSSM / schtasks |
| **OS Linux** | ❌ Non supporté | systemd |
| **Conteneurs** | ❌ Hors périmètre | ✅ Si nécessaire |
| **Bootstrap sequence** | ✅ Responsable (KIX + `bootstrap` runner) | 📡 Participant |
| **Arrêt d'urgence** | JobObject Windows (terminate_job) | Signal SIGTERM / NSSM stop |

---

## 8. PLAN D'IMPLEMENTATION

### Phase 1 : Documentation du Contrat
- [x] Créer `PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md` (ce document)
- [x] Documenter les endpoints croisés `GET /health/kix` et `GET /health`
- [x] Formaliser les topics WAZAA bus partagés

### Phase 2 : Validation Intégration
- [ ] Vérifier que VEX expose `GET /health` conformément au contrat
- [ ] Vérifier que KIX expose `GET /health/kix` conformément au contrat
- [ ] Tester l'enregistrement VEX dans le bootstrap KIX
- [ ] Tester la consommation des événements WAZAA bus croisés

### Phase 3 : Enforcement
- [ ] Ajouter des tests de non-dépassement de frontière (KIX ne touche pas aux daemons VEX)
- [ ] Ajouter des tests de non-dépassement de frontière (VEX ne touche pas aux runners KIX)
- [ ] Intégrer la vérification dans le pre-commit ou CI

---

## 9. DÉPENDANCES

### 9.1 Internes KIX

| Fichier | Rôle |
|---------|------|
| `src/app.py` | Endpoints `/health`, `/health/kix`, `/swarm/status`, `/bootstrap/register` |
| `src/diagnostics.py` | Health checks KIX |
| `config/runners.yaml` | Registry runners KIX |
| `libs/shared-clients/win32_process.py` | Primitives déploiement Windows |
| `PRD-MOC-KIX-MASTER.md` | Master MOC KIX |

### 9.2 Externes VEX (à documenter)

| Composant | Rôle |
|-----------|------|
| VEX API (port TBD) | Endpoint `GET /health` pour KIX |
| VEX daemon registry | Registre des daemons L3 |
| WAZAA bus (port 1873) | Broker événements partagés |

---

## 10. TRACABILITÉ

### 10.1 Thought Chain

```yaml
thought_chain:
  - source: "Observation : KIX et VEX partagent des responsabilités d'orchestration sans contrat explicite"
    artifact: "Risque de duplication de cycle de vie, registres concurrents, dépendances circulaires"
    intent_hash: "0xVEX_KIX_BOUNDARIES_20260927"
  - source: "Déduction : nécessité d'un contrat de frontières formel entre L2 et L3"
    artifact: "PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md"
    intent_hash: "0xVEX_KIX_BOUNDARIES_20260927"
  - source: "Validation : points d'intégration réduits au strict nécessaire (santé, bootstrap, WAZAA bus)"
    artifact: "Contrat minimal mais suffisant pour opérer sans chevauchement"
    intent_hash: "0xVEX_KIX_BOUNDARIES_20260927"
```

### 10.2 Gates

| Gate | Critère | Statut |
|------|---------|--------|
| **P-201** | Contrat de frontières validé par leads KIX et VEX | ✅ VALIDÉ |
| **P-202** | Points d'intégration documentés et testés | ⏸️ PENDING (dépend de VEX) |
| **P-203** | Tests de non-dépassement de frontière présents | ⏸️ PENDING (Phase 3) |

---

## 11. ONTOLOGIE

Concepts ontologiques mobilisés :

| Concept | Description | Source |
|---------|-------------|--------|
| `kix` | Orchestrateur central des runners RLM/TLM/LLM. Port 8800. | ONTOLOGY_DECLARATION.yaml (KIX) |
| `orchestrator-runner` | Orchestrateur de runners — centralise le cycle de vie des runners | ONTOLOGY_DECLARATION.yaml (KIX) |
| `rlm-runner` | RLM Runner — Release Lifecycle Manager | ONTOLOGY_DECLARATION.yaml (KIX) |
| `vex` | Orchestrateur L3 des daemons/agents autonomes | À déclarer dans ONTOLOGY VEX |
| `l3-daemon` | Daemon autonome L3, déployé via NSSM/schtasks/systemd | À déclarer dans ONTOLOGY VEX |

---

## 12. PREUVE-OF-LIFE

- [x] 2026-09-27T06:16:00+02:00 — PRD-MOC-VEX-KIX-BOUNDARIES créé, contrat de frontières formalisé
- [x] 2026-09-27T06:16:00+02:00 — Référencé dans PRD-MOC-KIX-MASTER.md ligne 34 et 95
- [x] 2026-09-27T06:30:00+02:00 — Endpoints KIX implémentés : `GET /health/kix`, `GET /health/l3`, `POST /health/l3`
- [x] 2026-09-27T06:30:00+02:00 — `/swarm/status` enrichi avec section `l3_health`
- [x] 2026-09-27T06:30:00+02:00 — VEX `KIX_CONTRACT` aligné : base_url=8800, health_path=/health
- [x] 2026-09-27T06:30:00+02:00 — Tests KIX passants : 4 nouveaux tests boundary (test_app.py)
- [x] 2026-09-27T06:30:00+02:00 — 119 tests core KIX passants (test_app, runners, integration, process_manager)

---

## 13. RÉFÉRENCES

- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX — section 2.3 "Relation avec VEX"
- `PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md` : Orchestration exécutables KIX
- `PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md` : Intégration multi-langages KIX
- `ADR-2026-09-24-ECOSYSTEM-INTEGRATION.md` : ADR intégration écosystème
- `ADR-2026-09-24-KIX-MULTI-LANG-RUNNERS.md` : ADR runners multi-langages
- `ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md` : ADR orchestrateur KIX
- `ONTOLOGY_DECLARATION.yaml` : Concepts ontologiques KIX
- `docs/bootstrap-runner.md` : Documentation bootstrap runner KIX

## 14. Modèle de Rôle/Fonction KIX

Ce PRD MOC s'aligne sur le modèle de rôle/fonction défini dans `PRD-MOC-KIX-MASTER.md` section 2.3 :

- **RBAC** : `admin`, `operator`, `viewer` (JWT dans `src/auth.py`)
- **Functional Roles** : 21 catégories (`orchestrator`, `cognitive`, `governance`, `infrastructure`, etc.)
- **Dual-Role Pattern** : TRIX/TRIXD/PLIX = RLM + TLM
- **ActorSpec** : intégration via `KIXProcessManagerAdapter`

**Implication pour les frontières KIX/VEX** :
- KIX expose les rôles fonctionnels via `/swarm/status` pour que VEX puisse consulter l'état sans duplication.
- VEX ne doit pas modifier `functional_roles` ni `meta.role` des runners KIX ; il consulte uniquement.
- Les endpoints cross-layer (`GET /health/kix`, `GET /health/l3`) respectent la séparation RBAC : VEX agit comme client `viewer` sur KIX.

---

**IntentHash** : `0xVEX_KIX_BOUNDARIES_20260927`
**Status** : implemented
**Date** : 2026-09-27

*PRD-MOC-VEX-KIX-BOUNDARIES — implemented — 2026-09-27*
