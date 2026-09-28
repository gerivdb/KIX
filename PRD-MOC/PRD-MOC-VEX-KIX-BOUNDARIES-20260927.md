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

# PRD MOC - Frontieres KIX / VEX -- Contrat de Separation des Orchestrations

## 1. RESUME EXECUTIF

Ce PRD MOC definit le **contrat de frontieres** entre deux orchestrateurs de l'ecosysteme gerivdb :

- **KIX** (L2-PLATFORM) : orchestrateur central des **runners RLM** (services applicatifs L2).
- **VEX** (L3-CITIZENS) : orchestrateur des **daemons/agents autonomes L3**.

**Principe fondateur** : KIX et VEX partagent des concepts d'orchestration et de gestion de processus, mais leurs perimetres sont **strictement separes**. Ce document verrouille les points d'integration autorises et les interdits de chevauchement.

**Perimetre** : Contrat de boundaries, endpoints de sante partages, protocole WAZAA bus, responsabilites de deploiement.
**Statut** : **implemented** (2026-09-27) -- Contrat actif, integration operationnelle.

---

## 2. CONTEXTE

### 2.1 Contexte

L'ecosysteme gerivdb comprend deux couches d'orchestration complementaires :

| Couche | Orchestrateur | Role | Repo |
|--------|--------------|------|------|
| **L2-PLATFORM** | **KIX** | Runners RLM (services applicatifs L2), alerting, auto-remediation, dashboard, auth, audit | gerivdb/KIX |
| **L3-CITIZENS** | **VEX** | Daemons/agents autonomes L3, deploiement multi-OS (NSSM/schtasks/systemd), clients d'integration | gerivdb/VEX |

**Probleme** : Sans contrat de frontieres explicite, les deux orchestrateurs peuvent :
- Dupliquer la gestion du cycle de vie d'un meme processus
- Écrire dans des registres de sante concurrents
- Declencher des redemarrages en cascade non coordonnes
- Creer des dependances circulaires au bootstrap

### 2.2 État Actuel

| Composant | État |
|-----------|------|
| KIX orchestrateur | ✅ 100% fonctionnel (Phases 1-5 terminees) |
| VEX orchestrateur | ⚠️ Partiellement documente |
| Contrat de frontieres | ❌ Manquant -- **ce document le cree** |
| Integration sante croisee | 📄 Documentee mais non formalisee |
| WAZAA bus partage | ✅ Operationnel |

---

## 3. ARCHITECTURE CIBLE -- CONTRAT DE FRONTIÈRES

### 3.1 Principe Fondateur

**KIX et VEX sont deux orchestrateurs specialises, non superposes.**

```
┌-------------------------------------------------------------┐
│                     KIX (L2-PLATFORM)                        │
│  Port 8800 -- Orchestrateur Runners RLM                      │
│                                                             │
│  Responsabilites :                                          │
│  - Cycle de vie des runners Python/Zig/Rust/Go/Node/Custom │
│  - Health checks parallelises + Doctor/Self-Healing         │
│  - Swarm Status pour Agent Manager / N+2/N+3                │
│  - PID Registry, logs, metriques, WAL                       │
│  - Preflight & diagnostics infrastructure                   │
`---------------------------┬----------------------------------┘
                           │
                    ┌------┴------┐
                    │  Integration│
                    │  Autorisee  │
                    `-------┬------┘
                           │
┌--------------------------┼----------------------------------┐
│                     VEX (L3-CITIZENS)                        │
│  Port <dynamic> -- Orchestrateur Daemons L3                  │
│                                                             │
│  Responsabilites :                                          │
│  - Cycle de vie des daemons/agents autonomes L3             │
│  - Deploiement multi-OS (NSSM / schtasks / systemd)         │
│  - Clients d'integration (interfaces with external systems) │
│  - Supervision daemons L3 agreges                           │
`--------------------------------------------------------------┘
```

### 3.2 Matrice de Responsabilites

| Domaine | KIX (L2) | VEX (L3) |
|---------|----------|----------|
| **Runners applicatifs L2** | ✅ Responsable | ❌ Hors perimetre |
| **Daemons/agents autonomes L3** | ❌ Hors perimetre | ✅ Responsable |
| **Health checks runners L2** | ✅ Responsable | 📡 Consommateur (`GET /health`) |
| **Health checks agreges L3** | 📡 Consommateur (`GET /health/l3`) | ✅ Responsable |
| **Enregistrement sante L3** | 📡 Recepteur (`POST /health/l3`) | ✅ Émetteur (`POST /health/l3`) |
| **Bootstrap sequence** | ✅ Responsable (`bootstrap` runner, port 8810) | 📡 Participant |
| **Deploiement Windows (NSSM/schtasks)** | ⚠️ Supporte via `win32_process.py` | ✅ Responsable |
| **Deploiement Linux (systemd)** | ❌ Hors perimetre | ✅ Responsable |
| **PID Registry runners** | ✅ Responsable | ❌ Hors perimetre |
| **PID Registry daemons** | ❌ Hors perimetre | ✅ Responsable |
| **Doctor/Self-Healing runners** | ✅ Responsable | ❌ Hors perimetre |
| **Doctor/Self-Healing daemons** | ❌ Hors perimetre | ✅ Responsable |
| **WAZAA bus -- evenements runners** | ✅ Émetteur | 📡 Consommateur |
| **WAZAA bus -- evenements daemons** | 📡 Consommateur | ✅ Émetteur |
| **Swarm Status (Agent Manager)** | ✅ Responsable | 📡 Participant |
| **Auth / Audit / Logs** | ✅ Responsable | ❌ Hors perimetre |
| **Integration clients externes** | ❌ Hors perimetre | ✅ Responsable |

---

## 4. POINTS D'INTÉGRATION AUTORISÉS

### 4.1 Endpoints de Sante Croises

| Endpoint | Appelant | Cible | Usage | Protocole |
|----------|----------|-------|-------|-----------|
| `GET /health` | VEX | KIX | VEX verifie que KIX est operationnel avant de demarrer des dependances L2 | HTTP REST |
| `GET /health/l3` | KIX | KIX | KIX retourne la sante L3 enregistree par VEX | HTTP REST |
| `POST /health/l3` | VEX | KIX | VEX enregistre sa sante agregee L3 dans KIX | HTTP REST |
| `GET /health` | KIX | VEX | KIX agrege la sante L3 via VEX pour le dashboard global | HTTP REST |

**Contrat** :
- Timeout : 5 secondes maximum
- Format reponse : `{"status": "ok|degraded|down", "timestamp": "<ISO-UTC>"}`
- En cas de timeout ou d'erreur 5xx : considerer la cible comme `degraded`, pas `down`
- `POST /health/l3` accepte un payload JSON et le stocke en memoire volatile (RAM) pour exposition via `GET /health/l3`
- KIX ne persiste PAS les donnees L3 reçues (VEX est responsable de sa propre persistence)

### 4.2 WAZAA Bus -- Évenements Partages

| Topic | Émetteur | Recepteur | Contenu |
|-------|----------|-----------|---------|
| `kix.runner.started` | KIX | VEX | Un runner L2 a demarre |
| `kix.runner.stopped` | KIX | VEX | Un runner L2 s'est arrete |
| `kix.runner.health_changed` | KIX | VEX | Changement de sante d'un runner L2 |
| `vex.daemon.started` | VEX | KIX | Un daemon L3 a demarre |
| `vex.daemon.stopped` | VEX | KIX | Un daemon L3 s'est arrete |
| `vex.daemon.health_changed` | VEX | KIX | Changement de sante d'un daemon L3 |
| `swarm.status.update` | KIX | VEX | Mise à jour du Swarm Status agrege |

**Contrat** :
- Broker : WAZAA bus (port 1873)
- Format : JSON avec `topic`, `payload`, `timestamp`, `source` (`kix` ou `vex`)
- Aucun evenement ne doit declencher de cycle de vie sur l'autre orchestrateur sans validation prealable

### 4.3 Bootstrap Sequence -- Coordination

| Role | Responsable | Action |
|------|-------------|--------|
| **Bootstrap orchestrator** | KIX (`bootstrap` runner, port 8810) | Demarre la sequence globale |
| **KIX self-check** | KIX | Verifie que KIX API est prete (port 8800) |
| **VEX registration** | VEX | S'enregistre aupres de KIX via `/bootstrap/register` |
| **Ready signal** | KIX | Publie `/bootstrap/ready = true` quand tous les services requis sont operationnels |

**Contrat** :
- VEX doit s'enregistrer aupres de KIX pendant le bootstrap
- KIX ne declare pas `ready` tant que VEX n'est pas enregistre (si `dependencies` inclut `vex`)
- En cas d'echec VEX : KIX continue en mode degrade (hors scope bloquant)

---

## 5. INTERDITS STRICTS

### 5.1 KIX ne doit PAS

- [❌] Gerer le cycle de vie des daemons L3 (VEX est responsable)
- [❌] Écrire dans le PID Registry de VEX
- [❌] Declencher un redemarrage d'un daemon L3
- [❌] Deployer des services via NSSM/schtasks/systemd
- [❌] Considerer les daemons L3 comme des runners KIX

### 5.2 VEX ne doit PAS

- [❌] Gerer le cycle de vie des runners RLM L2 (KIX est responsable)
- [❌] Écrire dans le PID Registry de KIX
- [❌] Declencher un redemarrage d'un runner L2
- [❌] Modifier `config/runners.yaml` de KIX
- [❌] Considerer les runners L2 comme des daemons VEX

### 5.3 Regles de Non-Interference

| Regle | Description |
|-------|-------------|
| **Registry isolation** | KIX utilise `data/runner-state.json` ; VEX utilise son propre registre. Aucun partage de fichier/DB. |
| **Process isolation** | KIX ne termine pas un processus detenu par VEX, et inversement. |
| **Port isolation** | KIX gere les ports L2 (8800, 8810, 8823, 1873, 7719, etc.) ; VEX gere les ports L3. Aucune collision de port autorisee. |
| **Config isolation** | `config/runners.yaml` (KIX) et `config/daemons.yaml` (VEX) sont des fichiers distincts. |

---

## 6. CONTRAT DE SANTÉ PARTAGÉE

### 6.1 Schema de Sante Unifie

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

### 6.2 Agregation Swarm Status

KIX agrege dans `/swarm/status` :
- Ses propres runners L2
- La sante L3 fournie par VEX (`GET /health`)

KIX ne doit pas :
- Modifier les donnees de sante L3 fournies par VEX
- Supprimer des composants L3 du rapport agrege

VEX ne doit pas :
- Modifier les donnees de sante L2 fournies par KIX
- Supprimer des composants L2 du rapport agrege

---

## 7. DÉPLOIEMENT -- RESPONSABILITÉS

| Aspect | KIX | VEX |
|--------|-----|-----|
| **OS Windows** | Services Python/Zig/Gateway via `win32_process.py` | NSSM / schtasks |
| **OS Linux** | ❌ Non supporte | systemd |
| **Conteneurs** | ❌ Hors perimetre | ✅ Si necessaire |
| **Bootstrap sequence** | ✅ Responsable (KIX + `bootstrap` runner) | 📡 Participant |
| **Arret d'urgence** | JobObject Windows (terminate_job) | Signal SIGTERM / NSSM stop |

---

## 8. PLAN D'IMPLEMENTATION

### Phase 1 : Documentation du Contrat
- [x] Creer `PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md` (ce document)
- [x] Documenter les endpoints croises `GET /health/kix` et `GET /health`
- [x] Formaliser les topics WAZAA bus partages

### Phase 2 : Validation Integration
- [ ] Verifier que VEX expose `GET /health` conformement au contrat
- [ ] Verifier que KIX expose `GET /health/kix` conformement au contrat
- [ ] Tester l'enregistrement VEX dans le bootstrap KIX
- [ ] Tester la consommation des evenements WAZAA bus croises

### Phase 3 : Enforcement
- [ ] Ajouter des tests de non-depassement de frontiere (KIX ne touche pas aux daemons VEX)
- [ ] Ajouter des tests de non-depassement de frontiere (VEX ne touche pas aux runners KIX)
- [ ] Integrer la verification dans le pre-commit ou CI

---

## 9. DÉPENDANCES

### 9.1 Internes KIX

| Fichier | Role |
|---------|------|
| `src/app.py` | Endpoints `/health`, `/health/kix`, `/swarm/status`, `/bootstrap/register` |
| `src/diagnostics.py` | Health checks KIX |
| `config/runners.yaml` | Registry runners KIX |
| `libs/shared-clients/win32_process.py` | Primitives deploiement Windows |
| `PRD-MOC-KIX-MASTER.md` | Master MOC KIX |

### 9.2 Externes VEX (à documenter)

| Composant | Role |
|-----------|------|
| VEX API (port TBD) | Endpoint `GET /health` pour KIX |
| VEX daemon registry | Registre des daemons L3 |
| WAZAA bus (port 1873) | Broker evenements partages |

---

## 10. TRACABILITÉ

### 10.1 Thought Chain

```yaml
thought_chain:
  - source: "Observation : KIX et VEX partagent des responsabilites d'orchestration sans contrat explicite"
    artifact: "Risque de duplication de cycle de vie, registres concurrents, dependances circulaires"
    intent_hash: "0xVEX_KIX_BOUNDARIES_20260927"
  - source: "Deduction : necessite d'un contrat de frontieres formel entre L2 et L3"
    artifact: "PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md"
    intent_hash: "0xVEX_KIX_BOUNDARIES_20260927"
  - source: "Validation : points d'integration reduits au strict necessaire (sante, bootstrap, WAZAA bus)"
    artifact: "Contrat minimal mais suffisant pour operer sans chevauchement"
    intent_hash: "0xVEX_KIX_BOUNDARIES_20260927"
```

### 10.2 Gates

| Gate | Critere | Statut |
|------|---------|--------|
| **P-201** | Contrat de frontieres valide par leads KIX et VEX | ✅ VALIDÉ |
| **P-202** | Points d'integration documentes et testes | ⏸️ PENDING (depend de VEX) |
| **P-203** | Tests de non-depassement de frontiere presents | ⏸️ PENDING (Phase 3) |

---

## 11. ONTOLOGIE

Concepts ontologiques mobilises :

| Concept | Description | Source |
|---------|-------------|--------|
| `kix` | Orchestrateur central des runners RLM/TLM/LLM. Port 8800. | ONTOLOGY_DECLARATION.yaml (KIX) |
| `orchestrator-runner` | Orchestrateur de runners -- centralise le cycle de vie des runners | ONTOLOGY_DECLARATION.yaml (KIX) |
| `rlm-runner` | RLM Runner -- Release Lifecycle Manager | ONTOLOGY_DECLARATION.yaml (KIX) |
| `vex` | Orchestrateur L3 des daemons/agents autonomes | À declarer dans ONTOLOGY VEX |
| `l3-daemon` | Daemon autonome L3, deploye via NSSM/schtasks/systemd | À declarer dans ONTOLOGY VEX |

---

## 12. PREUVE-OF-LIFE

- [x] 2026-09-27T06:16:00+02:00 -- PRD-MOC-VEX-KIX-BOUNDARIES cree, contrat de frontieres formalise
- [x] 2026-09-27T06:16:00+02:00 -- Reference dans PRD-MOC-KIX-MASTER.md ligne 34 et 95
- [x] 2026-09-27T06:30:00+02:00 -- Endpoints KIX implementes : `GET /health/kix`, `GET /health/l3`, `POST /health/l3`
- [x] 2026-09-27T06:30:00+02:00 -- `/swarm/status` enrichi avec section `l3_health`
- [x] 2026-09-27T06:30:00+02:00 -- VEX `KIX_CONTRACT` aligne : base_url=8800, health_path=/health
- [x] 2026-09-27T06:30:00+02:00 -- Tests KIX passants : 4 nouveaux tests boundary (test_app.py)
- [x] 2026-09-27T06:30:00+02:00 -- 119 tests core KIX passants (test_app, runners, integration, process_manager)

---

## 13. RÉFÉRENCES

- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX -- section 2.3 "Relation avec VEX"
- `PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md` : Orchestration executables KIX
- `PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md` : Integration multi-langages KIX
- `ADR-2026-09-24-ECOSYSTEM-INTEGRATION.md` : ADR integration ecosysteme
- `ADR-2026-09-24-KIX-MULTI-LANG-RUNNERS.md` : ADR runners multi-langages
- `ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md` : ADR orchestrateur KIX
- `ONTOLOGY_DECLARATION.yaml` : Concepts ontologiques KIX
- `docs/bootstrap-runner.md` : Documentation bootstrap runner KIX

## 14. Modele de Role/Fonction KIX

Ce PRD MOC s'aligne sur le modele de role/fonction defini dans `PRD-MOC-KIX-MASTER.md` section 2.3 :

- **RBAC** : `admin`, `operator`, `viewer` (JWT dans `src/auth.py`)
- **Functional Roles** : 21 categories (`orchestrator`, `cognitive`, `governance`, `infrastructure`, etc.)
- **Dual-Role Pattern** : TRIX/TRIXD/PLIX = RLM + TLM
- **ActorSpec** : integration via `KIXProcessManagerAdapter`

**Implication pour les frontieres KIX/VEX** :
- KIX expose les roles fonctionnels via `/swarm/status` pour que VEX puisse consulter l'etat sans duplication.
- VEX ne doit pas modifier `functional_roles` ni `meta.role` des runners KIX ; il consulte uniquement.
- Les endpoints cross-layer (`GET /health/kix`, `GET /health/l3`) respectent la separation RBAC : VEX agit comme client `viewer` sur KIX.

---

**IntentHash** : `0xVEX_KIX_BOUNDARIES_20260927`
**Status** : implemented
**Date** : 2026-09-27

*PRD-MOC-VEX-KIX-BOUNDARIES -- implemented -- 2026-09-27*
