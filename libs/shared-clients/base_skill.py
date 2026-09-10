#!/usr/bin/env python3
r"""
BaseSkill — ABC pour les skills TALEX (Phase 1)
4 méthodes abstraites/concrètes pour standardiser talex_narrate, talex_postmortem.

ERR_030: UTF-8 wrapper included.
"""
import io
import sys
from abc import ABC, abstractmethod
from typing import Optional

# ERR_030 FIX
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class BaseSkill(ABC):
    """Base abstrait pour tous les skills TALEX.
    
    4 méthodes:
    1. prepare(): prépare le contexte (abstract)
    2. analyze(): analyse les données (abstract)
    3. narrate(): génère le récit (concrete)
    4. complete(): finalise et journalise (concrete)
    
    Les skills héritent de BaseSkill et implémentent prepare() + analyze().
    """
    
    skill_id: str = "base-skill"
    skill_name: str = "Base Skill"
    version: str = "1.0.0"
    
    def __init__(self, context: dict = None):
        self.context = context or {}
        self.results: dict = {}
        self.started_at: str = ""
        self.completed_at: str = ""
    
    @abstractmethod
    def prepare(self) -> dict:
        """Prepare skill execution.
        
        Returns:
            dict with preparation context
        """
        pass
    
    @abstractmethod
    def analyze(self) -> dict:
        """Analyze data and produce results.
        
        Returns:
            dict with analysis results
        """
        pass
    
    def narrate(self, analysis: dict) -> str:
        """Generate narrative from analysis (concrete).
        
        Default implementation: simple template.
        Override for richer narrative.
        """
        lines = [
            f"# {self.skill_name} — Rapport",
            f"**Skill ID**: {self.skill_id}",
            f"**Version**: {self.version}",
            "",
            "## Résultats"
        ]
        
        for key, value in analysis.items():
            lines.append(f"- **{key}**: {value}")
        
        return "\n".join(lines)
    
    def complete(self) -> str:
        """Execute full skill pipeline and return narrative (concrete).
        
        Pipeline: prepare → analyze → narrate
        Records timestamps for traceability.
        """
        import time
        from datetime import datetime, timezone
        
        self.started_at = datetime.now(timezone.utc).isoformat()
        
        try:
            context = self.prepare()
            self.results = self.analyze()
            narrative = self.narrate(self.results)
            
            self.completed_at = datetime.now(timezone.utc).isoformat()
            print(f"[BaseSkill] {self.skill_name} completed in {self.started_at} → {self.completed_at}")
            
            return narrative
        except Exception as e:
            self.completed_at = datetime.now(timezone.utc).isoformat()
            print(f"[BaseSkill] {self.skill_name} FAILED: {e}")
            raise
