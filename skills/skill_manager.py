"""Skill Manager for Meton.

This module provides dynamic skill loading and management capabilities.
Supports both Python-based skills (BaseSkill) and Markdown-based skills
(MarkdownSkill) following the Claude Code skill format.

Skill Discovery Order:
1. Project markdown skills: .meton/skills/
2. User markdown skills: ~/.meton/skills/
3. Built-in markdown skills: skills/md_skills/
4. Python skills: skills/*.py

Example:
    >>> from skills.skill_manager import SkillManager
    >>>
    >>> manager = SkillManager()
    >>> manager.load_all_skills()
    >>> skill = manager.get_skill("code_explainer")
    >>> result = skill.execute({"code": "..."})
"""

import os
import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type, Union, Any
from skills.base import BaseSkill
from skills.markdown_skill import MarkdownSkill, MarkdownSkillLoader


class SkillManagerError(Exception):
    """Error in skill manager operations."""
    pass


class SkillManager:
    """Manages dynamic loading and unloading of skills.

    The SkillManager discovers available skills from multiple sources:
    - Markdown skills (.md files with YAML frontmatter) - Claude Code style
    - Python skills (Python classes inheriting BaseSkill)

    Markdown skills take precedence over Python skills with the same name.

    Attributes:
        skills_dir: Directory containing Python skill modules
        loaded_skills: Dictionary of currently loaded skill instances
        available_skills: Dictionary of discovered skill names to file paths
        markdown_loader: Loader for markdown-based skills

    Example:
        >>> manager = SkillManager()
        >>> manager.load_all_skills()
        >>> print(manager.list_loaded_skills())
        ['code-explainer', 'debugger', 'refactoring-engine']
    """

    def __init__(self, skills_dir: str = "skills"):
        """Initialize the skill manager.

        Args:
            skills_dir: Directory containing Python skill modules (default: "skills")
        """
        self.skills_dir = Path(skills_dir)
        self.loaded_skills: Dict[str, Union[BaseSkill, MarkdownSkill]] = {}
        self.available_skills: Dict[str, str] = {}  # Python skills only
        self.logger = logging.getLogger("meton.skill_manager")

        # Initialize markdown skill loader
        self.markdown_loader = MarkdownSkillLoader(
            project_dir=Path(".meton/skills"),
            user_dir=Path.home() / ".meton" / "skills",
            builtin_dir=self.skills_dir / "md_skills"
        )

        # Discover all skills
        self._discover_skills()

    def _discover_skills(self) -> None:
        """Discover all available skills (both markdown and Python).

        Scans for markdown skills first, then Python skills.
        """
        # Discover markdown skills first (higher precedence)
        self.markdown_loader.discover()

        # Discover Python skills
        self._discover_python_skills()

    def _discover_python_skills(self) -> None:
        """Discover Python skills in the skills directory.

        Scans the skills directory for Python files and identifies classes
        that inherit from BaseSkill. Populates the available_skills dictionary.
        """
        if not self.skills_dir.exists():
            self.logger.warning(f"Skills directory not found: {self.skills_dir}")
            return

        # Files to skip
        skip_files = {"__init__.py", "base.py", "skill_manager.py", "markdown_skill.py"}

        for file_path in self.skills_dir.glob("*.py"):
            filename = file_path.name

            # Skip excluded files
            if filename in skip_files:
                continue

            # Extract skill name from filename (remove .py extension)
            skill_name = file_path.stem

            # Store the file path
            self.available_skills[skill_name] = str(file_path)

        self.logger.info(
            f"Discovered {len(self.available_skills)} Python skills, "
            f"{len(self.markdown_loader.discovered)} markdown skills"
        )

    def load_skill(self, skill_name: str) -> bool:
        """Load a skill dynamically.

        First checks for markdown skills, then falls back to Python skills.

        Args:
            skill_name: Name of the skill to load

        Returns:
            True if skill loaded successfully, False otherwise

        Example:
            >>> manager = SkillManager()
            >>> success = manager.load_skill("code-explainer")
            >>> if success:
            ...     print("Skill loaded!")
        """
        # Check if already loaded
        if skill_name in self.loaded_skills:
            self.logger.debug(f"Skill '{skill_name}' is already loaded")
            return True

        # Try to load as markdown skill first
        if skill_name in self.markdown_loader.discovered:
            skill = self.markdown_loader.load_skill(skill_name)
            if skill:
                self.loaded_skills[skill_name] = skill
                self.logger.info(f"Loaded markdown skill: {skill_name}")
                return True
            return False

        # Fall back to Python skill
        return self._load_python_skill(skill_name)

    def _load_python_skill(self, skill_name: str) -> bool:
        """Load a Python-based skill.

        Args:
            skill_name: Name of the skill to load

        Returns:
            True if skill loaded successfully, False otherwise
        """
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

            self.logger.info(f"Loaded Python skill: {skill_name}")
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

        # Also unload from markdown loader if applicable
        self.markdown_loader.unload_skill(skill_name)

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
            ['code-explainer', 'debugger', 'refactoring-engine', ...]
        """
        # Combine markdown and Python skills (markdown takes precedence)
        all_skills = set(self.markdown_loader.discovered.keys())
        all_skills.update(self.available_skills.keys())
        return sorted(list(all_skills))

    def get_skill(self, skill_name: str) -> Optional[Union[BaseSkill, MarkdownSkill]]:
        """Get a loaded skill instance.

        Args:
            skill_name: Name of the skill

        Returns:
            BaseSkill or MarkdownSkill instance if loaded, None otherwise

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

        # Load markdown skills first
        for skill_name in self.markdown_loader.discovered.keys():
            if self.load_skill(skill_name):
                count += 1

        # Load Python skills (skip if already loaded as markdown)
        for skill_name in self.available_skills.keys():
            if skill_name not in self.loaded_skills:
                if self.load_skill(skill_name):
                    count += 1

        total_available = len(self.list_available_skills())
        self.logger.info(f"Loaded {count}/{total_available} skills")
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
        return (
            skill_name in self.markdown_loader.discovered or
            skill_name in self.available_skills
        )

    def rediscover_skills(self) -> int:
        """Rediscover skills in all skill directories.

        Useful when new skill files are added without restarting.

        Returns:
            Count of newly discovered skills

        Example:
            >>> new_count = manager.rediscover_skills()
            >>> print(f"Found {new_count} new skills")
        """
        old_count = len(self.list_available_skills())

        # Rediscover both markdown and Python skills
        self.markdown_loader.discover()
        self._discover_python_skills()

        new_count = len(self.list_available_skills()) - old_count

        self.logger.info(
            f"Rediscovered skills: {new_count} new, "
            f"{len(self.list_available_skills())} total"
        )
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
        return len(self.list_available_skills())

    def get_skill_type(self, skill_name: str) -> Optional[str]:
        """Get the type of a skill (markdown or python).

        Args:
            skill_name: Name of the skill

        Returns:
            "markdown", "python", or None if not found
        """
        if skill_name in self.markdown_loader.discovered:
            return "markdown"
        if skill_name in self.available_skills:
            return "python"
        return None

    def get_skills_by_type(self, skill_type: str) -> List[str]:
        """Get all skills of a specific type.

        Args:
            skill_type: "markdown" or "python"

        Returns:
            List of skill names of that type
        """
        if skill_type == "markdown":
            return list(self.markdown_loader.discovered.keys())
        elif skill_type == "python":
            return list(self.available_skills.keys())
        return []

    def generate_skills_prompt_section(self) -> str:
        """Generate a prompt section listing available skills.

        This is used for model-invoked skill discovery - the LLM can
        read skill descriptions and decide when to use them.

        Returns:
            Formatted string describing available skills
        """
        if not self.loaded_skills:
            return ""

        lines = ["## Available Skills", ""]

        for name, skill in sorted(self.loaded_skills.items()):
            info = skill.get_info()
            skill_type = info.get("type", "python")

            lines.append(f"### {name} ({skill_type})")
            lines.append(f"**Description:** {info.get('description', 'No description')}")

            if isinstance(skill, MarkdownSkill) and skill.allowed_tools:
                lines.append(f"**Allowed tools:** {', '.join(skill.allowed_tools)}")

            lines.append("")

        return "\n".join(lines)

    def execute_skill(
        self,
        skill_name: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a skill with the given input.

        Handles both Python skills (execute method) and Markdown skills
        (returns instructions for LLM to follow).

        Args:
            skill_name: Name of the skill to execute
            input_data: Input data for the skill

        Returns:
            Result dictionary with execution results

        Raises:
            SkillManagerError: If skill not found or execution fails
        """
        skill = self.get_skill(skill_name)

        if skill is None:
            # Try to load it first
            if not self.load_skill(skill_name):
                raise SkillManagerError(f"Skill '{skill_name}' not found")
            skill = self.get_skill(skill_name)

        if isinstance(skill, BaseSkill):
            # Python skill - direct execution
            return skill.execute(input_data)

        elif isinstance(skill, MarkdownSkill):
            # Markdown skill - return instructions for LLM
            return {
                "success": True,
                "type": "markdown_skill",
                "name": skill.name,
                "instructions": skill.get_system_prompt(),
                "allowed_tools": skill.allowed_tools,
                "model": skill.model,
                "input_data": input_data
            }

        raise SkillManagerError(f"Unknown skill type for '{skill_name}'")

    def __repr__(self) -> str:
        """String representation of SkillManager.

        Returns:
            Manager info with counts
        """
        md_count = len(self.markdown_loader.discovered)
        py_count = len(self.available_skills)
        loaded = len(self.loaded_skills)
        return f"<SkillManager(loaded={loaded}, markdown={md_count}, python={py_count})>"
