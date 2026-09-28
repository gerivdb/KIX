---
type: ADR
status: proposed
date: "2026-09-28"
intent_hash: 0xADR_KIX_WINDOW_POLICY_20260928
---

# ADR — KIX Window Policy Integration

## Contexte

KIX est l’orchestrateur L2. Il agrège les health checks de VEX et d’autres L3.
Dans le cadre de la gouvernance PID, KIX doit exposer une vue agrégée des violations
fenêtres dans l’écosystème.

## Décision

KIX ajoute un endpoint `/l3/window-policy` qui agrège les réponses de tous les VEX
de l’écosystème. Si une violation n’est pas corrigée depuis > 5 min → alerte.
Si violation sur un daemon critique → alerte immédiate.

## Conséquences

- KIX interroge périodiquement `/health/window-policy` de chaque VEX
- Les violations sont stockées dans un journal d’alertes
- KIX peut déclencher des actions correctives via BRAIN

## Références

- **Master** : `PRD-MOC-VEX-ECOSYSTEM-PID-GOVERNANCE-20260928.md`
- **VEX** : `PRD-MOC-VEX-WINDOW-POLICY-20260928.md`
- **GOVERNANCE-HUB** : `known_repositories.yaml`
