"""Skill Manager for Meton.

This module provides dynamic skill loading and management capabilities.
Skills can be loaded, unloaded, and reloaded at runtime without restarting the application.

Example:
    >>> from skills.skill_manager import SkillManager
    >>>
    >>> manager = SkillManager()
    >>> manager.load_skill("code_explainer")
    >>> skill = manager.get_skill("code_explainer")
    >>> result = skill.execute({"code": "..."})
"""

import os
import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type
from skills.base import BaseSkill


class SkillManagerError(Exception):
    """Error in skill manager operations."""
    pass


class SkillManager:
    """Manages dynamic loading and unloading of skills.

    The SkillManager discovers available skills in the skills directory,
    loads them dynamically, and provides methods to manage their lifecycle.

    Attributes:
        skills_dir: Directory containing skill modules
        loaded_skills: Dictionary of currently loaded skill instances
        available_skills: Dictionary of discovered skill names to file paths

    Example:
        >>> manager = SkillManager()
        >>> manager.load_all_skills()
        >>> print(manager.list_loaded_skills())
        ['code_explainer', 'debugger', 'refactoring_engine']
    """

    def __init__(self, skills_dir: str = "skills"):
        """Initialize the skill manager.

        Args:
            skills_dir: Directory containing skill modules (default: "skills")
        """
        self.skills_dir = Path(skills_dir)
        self.loaded_skills: Dict[str, BaseSkill] = {}
        self.available_skills: Dict[str, str] = {}
        self.logger = logging.getLogger("meton.skill_manager")

        # Discover available skills
        self._discover_skills()

    def _discover_skills(self) -> None:
        """Discover available skills in the skills directory.

        Scans the skills directory for Python files and identifies classes
        that inherit from BaseSkill. Populates the available_skills dictionary.
        """
        if not self.skills_dir.exists():
            self.logger.warning(f"Skills directory not found: {self.skills_dir}")
            return

        # Files to skip
        skip_files = {"__init__.py", "base.py", "skill_manager.py"}

        for file_path in self.skills_dir.glob("*.py"):
            filename = file_path.name

            # Skip excluded files
            if filename in skip_files:
                continue

            # Extract skill name from filename (remove .py extension)
            skill_name = file_path.stem

            # Store the file path
            self.available_skills[skill_name] = str(file_path)

        self.logger.info(f"Discovered {len(self.available_skills)} skills")

    def load_skill(self, skill_name: str) -> bool:
        """Load a skill dynamically.

        Args:
            skill_name: Name of the skill to load

        Returns:
            True if skill loaded successfully, False otherwise

        Example:
            >>> manager = SkillManager()
            >>> success = manager.load_skill("code_explainer")
            >>> if success:
            ...     print("Skill loaded!")
        """
        # Check if already loaded
        if skill_name in self.loaded_skills:
            self.logger.warning(f"Skill '{skill_name}' is already loaded")
            return True

        # Check if skill exists
        if skill_name not in self.available_skills:
            self.logger.error(f"Skill '{skill_name}' not found in available skills")
            return False

        try:
            file_path = self.available_skills[skill_name]

            # Dynamic import
            spec = importlib.util.spec_from_file_location(skill_name, file_path)
            if spec is None or spec.loader is None:
                self.logger.error(f"Failed to create spec for {skill_name}")
                return False

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find BaseSkill subclass
            skill_class = None
            for item_name in dir(module):
                item = getattr(module, item_name)
                if (isinstance(item, type) and
                    issubclass(item, BaseSkill) and
                    item is not BaseSkill):
                    skill_class = item
                    break

            if skill_class is None:
                self.logger.error(f"No BaseSkill subclass found in {skill_name}")
                return False

            # Instantiate skill
            skill_instance = skill_class()
            self.loaded_skills[skill_name] = skill_instance

            self.logger.info(f"Loaded skill: {skill_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load skill '{skill_name}': {e}")
            return False

    def unload_skill(self, skill_name: str) -> bool:
        """Unload a skill.

        Args:
            skill_name: Name of the skill to unload

        Returns:
            True if skill was unloaded, False if it wasn't loaded

        Example:
            >>> manager.unload_skill("code_explainer")
            True
        """
        if skill_name not in self.loaded_skills:
            self.logger.warning(f"Skill '{skill_name}' is not loaded")
            return False

        del self.loaded_skills[skill_name]
        self.logger.info(f"Unloaded skill: {skill_name}")
        return True

    def reload_skill(self, skill_name: str) -> bool:
        """Reload a skill (unload then load).

        Useful for development when skill code has been modified.

        Args:
            skill_name: Name of the skill to reload

        Returns:
            True if skill reloaded successfully, False otherwise

        Example:
            >>> manager.reload_skill("code_explainer")
            True
        """
        # Unload if loaded (ignore result)
        if skill_name in self.loaded_skills:
            self.unload_skill(skill_name)

        # Load the skill
        success = self.load_skill(skill_name)

        if success:
            self.logger.info(f"Reloaded skill: {skill_name}")
        else:
            self.logger.error(f"Failed to reload skill: {skill_name}")

        return success

    def list_loaded_skills(self) -> List[str]:
        """List currently loaded skill names.

        Returns:
            List of loaded skill names

        Example:
            >>> manager.list_loaded_skills()
            ['code_explainer', 'debugger']
        """
        return list(self.loaded_skills.keys())

    def list_available_skills(self) -> List[str]:
        """List all discoverable skill names.

        Returns:
            List of available skill names (loaded and unloaded)

        Example:
            >>> manager.list_available_skills()
            ['code_explainer', 'debugger', 'refactoring_engine', ...]
        """
        return list(self.available_skills.keys())

    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """Get a loaded skill instance.

        Args:
            skill_name: Name of the skill

        Returns:
            BaseSkill instance if loaded, None otherwise

        Example:
            >>> skill = manager.get_skill("code_explainer")
            >>> if skill:
            ...     result = skill.execute({"code": "..."})
        """
        return self.loaded_skills.get(skill_name)

    def load_all_skills(self) -> int:
        """Load all available skills.

        Returns:
            Count of successfully loaded skills

        Example:
            >>> count = manager.load_all_skills()
            >>> print(f"Loaded {count} skills")
        """
        count = 0
        for skill_name in self.available_skills.keys():
            if self.load_skill(skill_name):
                count += 1

        self.logger.info(f"Loaded {count}/{len(self.available_skills)} skills")
        return count

    def unload_all_skills(self) -> int:
        """Unload all loaded skills.

        Returns:
            Count of unloaded skills

        Example:
            >>> count = manager.unload_all_skills()
            >>> print(f"Unloaded {count} skills")
        """
        skill_names = list(self.loaded_skills.keys())
        count = 0

        for skill_name in skill_names:
            if self.unload_skill(skill_name):
                count += 1

        self.logger.info(f"Unloaded {count} skills")
        return count

    def get_skill_info(self, skill_name: str) -> Optional[Dict]:
        """Get information about a skill.

        Args:
            skill_name: Name of the skill

        Returns:
            Dictionary with skill information if loaded, None otherwise

        Example:
            >>> info = manager.get_skill_info("code_explainer")
            >>> print(info["description"])
        """
        skill = self.get_skill(skill_name)
        if skill:
            return skill.get_info()
        return None

    def is_loaded(self, skill_name: str) -> bool:
        """Check if a skill is loaded.

        Args:
            skill_name: Name of the skill

        Returns:
            True if skill is loaded, False otherwise

        Example:
            >>> if manager.is_loaded("code_explainer"):
            ...     print("Code explainer is ready")
        """
        return skill_name in self.loaded_skills

    def is_available(self, skill_name: str) -> bool:
        """Check if a skill is available (discoverable).

        Args:
            skill_name: Name of the skill

        Returns:
            True if skill is available, False otherwise

        Example:
            >>> if manager.is_available("code_explainer"):
            ...     manager.load_skill("code_explainer")
        """
        return skill_name in self.available_skills

    def rediscover_skills(self) -> int:
        """Rediscover skills in the skills directory.

        Useful when new skill files are added without restarting.

        Returns:
            Count of newly discovered skills

        Example:
            >>> new_count = manager.rediscover_skills()
            >>> print(f"Found {new_count} new skills")
        """
        old_count = len(self.available_skills)
        self._discover_skills()
        new_count = len(self.available_skills) - old_count

        self.logger.info(f"Rediscovered skills: {new_count} new, {len(self.available_skills)} total")
        return new_count

    def get_loaded_count(self) -> int:
        """Get count of loaded skills.

        Returns:
            Number of loaded skills
        """
        return len(self.loaded_skills)

    def get_available_count(self) -> int:
        """Get count of available skills.

        Returns:
            Number of available skills
        """
        return len(self.available_skills)

    def __repr__(self) -> str:
        """String representation of SkillManager.

        Returns:
            Manager info with counts
        """
        return f"<SkillManager(loaded={len(self.loaded_skills)}, available={len(self.available_skills)})>"
