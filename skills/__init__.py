"""Skill framework for Meton.

This module provides the skill registry and management system for Meton.
Skills are specialized capabilities that provide high-level assistance.

Example:
    >>> from skills import SkillRegistry
    >>> from skills.base import BaseSkill
    >>>
    >>> registry = SkillRegistry()
    >>> skill = MySkill()
    >>> registry.register(skill)
    >>> result = registry.execute_skill("my_skill", {"task": "do_something"})
"""

from typing import Dict, List, Any, Optional
import logging

from skills.base import (
    BaseSkill,
    SkillError,
    SkillValidationError,
    SkillExecutionError
)


class SkillRegistryError(SkillError):
    """Error in skill registry operations."""
    pass


class SkillRegistry:
    """Central registry for managing skills.

    The SkillRegistry maintains a collection of available skills and provides
    methods to register, unregister, retrieve, and execute skills.

    Example:
        >>> registry = SkillRegistry()
        >>> skill = CodeExplainerSkill()
        >>> registry.register(skill)
        >>> result = registry.execute_skill("code_explainer", {"code": "..."})
    """

    def __init__(self):
        """Initialize the skill registry."""
        self._skills: Dict[str, BaseSkill] = {}
        self.logger = logging.getLogger("meton.skills")

    def register(self, skill: BaseSkill) -> None:
        """Register a skill.

        Args:
            skill: BaseSkill instance to register

        Raises:
            SkillRegistryError: If skill is already registered or invalid

        Example:
            >>> registry = SkillRegistry()
            >>> skill = MySkill()
            >>> registry.register(skill)
        """
        if not isinstance(skill, BaseSkill):
            raise SkillRegistryError(
                f"Skill must be an instance of BaseSkill, got {type(skill).__name__}"
            )

        if not skill.name:
            raise SkillRegistryError("Skill must have a name")

        if skill.name in self._skills:
            raise SkillRegistryError(
                f"Skill '{skill.name}' is already registered"
            )

        self._skills[skill.name] = skill
        self.logger.info(f"Registered skill: {skill.name} v{skill.version}")

    def unregister(self, skill_name: str) -> None:
        """Unregister a skill.

        Args:
            skill_name: Name of skill to unregister

        Raises:
            SkillRegistryError: If skill is not found

        Example:
            >>> registry.unregister("my_skill")
        """
        if skill_name not in self._skills:
            raise SkillRegistryError(
                f"Skill '{skill_name}' is not registered"
            )

        del self._skills[skill_name]
        self.logger.info(f"Unregistered skill: {skill_name}")

    def get(self, skill_name: str) -> Optional[BaseSkill]:
        """Get skill by name.

        Args:
            skill_name: Name of skill to retrieve

        Returns:
            BaseSkill instance or None if not found

        Example:
            >>> skill = registry.get("code_explainer")
            >>> if skill:
            ...     result = skill.execute({"code": "..."})
        """
        return self._skills.get(skill_name)

    def list_all(self) -> List[Dict[str, Any]]:
        """List all registered skills.

        Returns:
            List of skill info dictionaries

        Example:
            >>> skills = registry.list_all()
            >>> for skill_info in skills:
            ...     print(f"{skill_info['name']}: {skill_info['description']}")
        """
        return [skill.get_info() for skill in self._skills.values()]

    def execute_skill(
        self, skill_name: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a skill by name.

        Args:
            skill_name: Name of skill to execute
            input_data: Input parameters for the skill

        Returns:
            Dictionary with execution results

        Raises:
            SkillRegistryError: If skill is not found or disabled
            SkillValidationError: If input validation fails
            SkillExecutionError: If skill execution fails

        Example:
            >>> result = registry.execute_skill(
            ...     "code_explainer",
            ...     {"code": "def hello(): print('hi')"}
            ... )
            >>> if result["success"]:
            ...     print(result["explanation"])
        """
        # Get skill
        skill = self.get(skill_name)
        if skill is None:
            raise SkillRegistryError(
                f"Skill '{skill_name}' is not registered"
            )

        # Check if enabled
        if not skill.enabled:
            raise SkillRegistryError(
                f"Skill '{skill_name}' is disabled"
            )

        # Validate input
        try:
            skill.validate_input(input_data)
        except SkillValidationError as e:
            self.logger.error(f"Validation failed for {skill_name}: {e}")
            raise

        # Execute skill
        try:
            self.logger.info(f"Executing skill: {skill_name}")
            result = skill.execute(input_data)
            self.logger.info(f"Skill {skill_name} completed successfully")
            return result
        except Exception as e:
            self.logger.error(f"Skill {skill_name} execution failed: {e}")
            raise SkillExecutionError(
                f"Skill '{skill_name}' execution failed: {str(e)}"
            ) from e

    def has_skill(self, skill_name: str) -> bool:
        """Check if a skill is registered.

        Args:
            skill_name: Name of skill to check

        Returns:
            True if skill is registered, False otherwise

        Example:
            >>> if registry.has_skill("code_explainer"):
            ...     result = registry.execute_skill("code_explainer", {...})
        """
        return skill_name in self._skills

    def enable_skill(self, skill_name: str) -> None:
        """Enable a skill.

        Args:
            skill_name: Name of skill to enable

        Raises:
            SkillRegistryError: If skill is not found

        Example:
            >>> registry.enable_skill("code_explainer")
        """
        skill = self.get(skill_name)
        if skill is None:
            raise SkillRegistryError(
                f"Skill '{skill_name}' is not registered"
            )
        skill.enable()
        self.logger.info(f"Enabled skill: {skill_name}")

    def disable_skill(self, skill_name: str) -> None:
        """Disable a skill.

        Args:
            skill_name: Name of skill to disable

        Raises:
            SkillRegistryError: If skill is not found

        Example:
            >>> registry.disable_skill("code_explainer")
        """
        skill = self.get(skill_name)
        if skill is None:
            raise SkillRegistryError(
                f"Skill '{skill_name}' is not registered"
            )
        skill.disable()
        self.logger.info(f"Disabled skill: {skill_name}")

    def clear(self) -> None:
        """Clear all registered skills.

        Example:
            >>> registry.clear()
            >>> assert len(registry.list_all()) == 0
        """
        count = len(self._skills)
        self._skills.clear()
        self.logger.info(f"Cleared {count} skills from registry")

    def __len__(self) -> int:
        """Return number of registered skills.

        Returns:
            Number of skills in registry
        """
        return len(self._skills)

    def __repr__(self) -> str:
        """String representation of registry.

        Returns:
            Registry info with skill count
        """
        return f"<SkillRegistry(skills={len(self._skills)})>"


# Export public API
__all__ = [
    "BaseSkill",
    "SkillError",
    "SkillValidationError",
    "SkillExecutionError",
    "SkillRegistry",
    "SkillRegistryError",
]
