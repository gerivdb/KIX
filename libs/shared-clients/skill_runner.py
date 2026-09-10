#!/usr/bin/env python3
r"""
SkillRunner — Runner générique pour charger et executer des skills (Phase 1)

Charge un skill via entrypoint ou nom de module, injecte config, execute.

ERR_030: UTF-8 wrapper included.
"""
import io
import sys
import json
import importlib
import importlib.util
from pathlib import Path
from typing import Optional

# ERR_030 FIX
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', effects='replace')

sys.path.insert(0, str(Path(__file__).resolve().parent))

from base_runner import BaseRunner
from base_skill import BaseSkill


class SkillRunner(BaseRunner):
    """Runner générique pour executer des skills TALEX.
    
    Charge un skill via:
    1. Entry point (setup.cfg / pyproject.toml)
    2. Module path (ex: "talex.talex_narrate")
    3. File path (.py)
    
    Injecte shared clients (KG_L_Client, WAZAA_Client, VaultWriter) via config.
    """
    
    runner_name = "skill-runner"
    runner_version = "1.0.0"
    port = 8795
    
    def __init__(self, skill_path: str, config: dict = None):
        super().__init__(config)
        self.skill_path = skill_path
        self.skill: Optional[BaseSkill] = self._load_skill()
    
    def _load_skill(self) -> Optional[BaseSkill]:
        """Load skill from path, entrypoint, or module name."""
        # Try as module name first
        try:
            module = importlib.import_module(self.skill_path)
            if hasattr(module, 'SKILL'):
                return module.SKILL
            # Look for class that inherits BaseSkill
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and issubclass(obj, BaseSkill) and obj != BaseSkill:
                    return obj(context=self.config)
        except ImportError:
            pass
        
        # Try as file path
        skill_file = Path(self.skill_path)
        if skill_file.exists() and skill_file.suffix == ".py":
            spec = importlib.util.spec_from_file_location(
                skill_file.stem, str(skill_file)
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, 'SKILL'):
                return module.SKILL
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and issubclass(obj, BaseSkill) and obj != BaseSkill:
                    return obj(context=self.config)
        
        print(f"[SkillRunner] Could not load skill: {self.skill_path}")
        return None
    
    def run(self):
        """Execute the loaded skill."""
        if not self.skill:
            print(f"[SkillRunner] No skill loaded from {self.skill_path}")
            self._error_count += 1
            return
        
        try:
            narrative = self.skill.complete()
            print(f"[SkillRunner] Narrative generated: {len(narrative)} chars")
        except Exception as e:
            self._error_count += 1
            print(f"[SkillRunner] Skill execution failed: {e}")
    
    def execute_skill(self, skill_class: type, context: dict = None) -> str:
        """Execute a specific skill class with context."""
        skill = skill_class(context=context or self.config)
        return skill.complete()
