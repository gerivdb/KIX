---
type: PRD-MOC
version: "1.0.0"
date: "2026-09-28"
status: draft
intent_hash: 0xPRD_MOC_KIX_WINDOW_POLICY_20260928
parent_prd: PRD-MOC-VEX-ECOSYSTEM-PID-GOVERNANCE-20260928.md
pole_id: POLE-MEMORY-001
owner: L2-PLATFORM
repo: gerivdb/KIX
---

# PRD-MOC -- KIX Window Policy Integration

## Objectif

Agreger les etats de window policy de tous les L3 geres par KIX, et exposer une vue
globale des violations fenetres dans l’ecosysteme.

## Contexte

KIX est l’orchestrateur L2. Il agrege les health checks de VEX et d’autres L3.
Dans le cadre de la gouvernance PID, KIX doit :

- Consommer `/health/window-policy` de chaque VEX
- Detecter les violations cross-repo
- Alerter si une violation n’est pas corrigee dans un delai donne

## Decision d’architecture

KIX ajoute un endpoint `/l3/window-policy` qui agrege les reponses de tous les VEX
de l’ecosysteme.

## Plan de mise en œuvre

### Phase 1 -- Consommation VEX
- [ ] Appeler `/health/window-policy` pour chaque VEX connu
- [ ] Agreger les violations dans un etat global
- [ ] Exposer `/l3/window-policy`

### Phase 2 -- Alerting
- [ ] Si violation non corrigee depuis > 5 min -> alerte
- [ ] Si violation sur un daemon critique -> alerte immediate

## Criteres d’acceptation

- [ ] `/l3/window-policy` retourne l’etat agrege
- [ ] Alertes fonctionnelles
- [ ] Tests passent

## References

- **Master** : `PRD-MOC-VEX-ECOSYSTEM-PID-GOVERNANCE-20260928.md`
- **VEX** : `PRD-MOC-VEX-WINDOW-POLICY-20260928.md`
- **VEX L3 Orchestrator** : `PRD-MOC-VEX-L3-ORCHESTRATOR-20260926.md`
- **ADR** : `ADR-KIX-WINDOW-POLICY-20260928.md`
- **ADR Ecosystem** : `ADR-ECOSYSTEM-PID-GOVERNANCE-20260928.md`

## Proof-of-Life

- [ ] 2026-09-28T22:36:00+02:00 -- PRD-MOC cree
- [ ] 2026-09-28T22:37:00+02:00 -- Endpoint `/l3/window-policy` cree
- [ ] 2026-09-28T22:38:00+02:00 -- Tests passent
