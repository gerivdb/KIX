#!/usr/bin/env python3
"""
Governance Dashboard CLI for Conversation Cognitive Runner.
Affiche les statistiques auto-gouvernance et les artefacts générés.

Usage:
    python scripts/governance_dashboard.py
    python scripts/governance_dashboard.py --type ADR
    python scripts/governance_dashboard.py --json
"""

import json
import sys
from pathlib import Path

# Ajouter le répertoire services au path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "services"))

from auto_governance import get_dashboard_stats, load_artifacts


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Governance Dashboard")
    parser.add_argument("--type", help="Filtrer par type d'artefact (ADR, PRD, INTENT, CONSTRAINT)")
    parser.add_argument("--json", action="store_true", help="Sortie JSON")
    parser.add_argument("--list", action="store_true", help="Lister les artefacts")
    args = parser.parse_args()

    if args.list:
        artifacts = load_artifacts(args.type)
        if args.json:
            print(json.dumps(artifacts, indent=2, ensure_ascii=False))
        else:
            print(f"Artefacts {'filtres par ' + args.type if args.type else 'tous'}:")
            print(f"Total: {len(artifacts)}")
            for artifact in artifacts:
                print(f"  [{artifact.get('type', '?')}] {artifact.get('intent_hash', '?')} - {artifact.get('title', '?')}")
        return 0

    stats = get_dashboard_stats()

    if args.json:
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    else:
        print("=" * 60)
        print("GOVERNANCE DASHBOARD — Auto-Gouvernance Phase 2")
        print("=" * 60)
        print(f"\nTotal artefacts generes: {stats['total_artifacts']}")
        print(f"Total decisions extraites: {stats['total_decisions']}")
        print(f"Derniere generation: {stats['last_generated']}")
        print("\nPar type:")
        for atype, count in stats.get("by_type", {}).items():
            print(f"  {atype}: {count}")
        print(f"\nPattern le plus detecte: {stats['top_pattern'][0]} ({stats['top_pattern'][1]} fois)")
        print("\nTous les patterns:")
        for pid, count in stats.get("pattern_counts", {}).items():
            print(f"  {pid}: {count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
