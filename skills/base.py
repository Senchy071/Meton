"""Base skill class for Meton skills.

This module provides the base interface that all Meton skills must implement.
Skills are specialized capabilities that provide high-level assistance like
code explanation, debugging, refactoring, etc.

Example:
    >>> from skills.base import BaseSkill
    >>>
    >>> class MySkill(BaseSkill):
    ...     name = "my_skill"
    ...     description = "Does something useful"
    ...     version = "1.0.0"
    ...
    ...     def execute(self, input_data):
    ...         return {"success": True, "result": "Done!"}
    >>>
    >>> skill = MySkill()
    >>> result = skill.execute({"task": "do_something"})
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class SkillError(Exception):
    """Base exception for skill errors."""
    pass


class SkillValidationError(SkillError):
    """Input validation failed."""
    pass


class SkillExecutionError(SkillError):
    """Skill execution failed."""
    pass


class BaseSkill(ABC):
    """Base class for all Meton skills.

    All skills must inherit from this class and implement the execute() method.
    Skills provide high-level intelligent assistance (code explanation, debugging,
    refactoring, etc.) and can use tools and RAG for context.

    Attributes:
        name: Unique skill identifier (e.g., "code_explainer")
        description: What the skill does
        version: Skill version (semantic versioning)
        enabled: Whether skill is currently enabled

    Example:
        >>> class ExplainerSkill(BaseSkill):
        ...     name = "code_explainer"
        ...     description = "Explains how code works"
        ...     version = "1.0.0"
        ...
        ...     def execute(self, input_data):
        ...         code = input_data.get("code")
        ...         explanation = self._explain(code)
        ...         return {"success": True, "explanation": explanation}
    """

    # Must be overridden by subclasses
    name: str = "base_skill"
    description: str = "Base skill (override this)"
    version: str = "0.0.0"
    enabled: bool = True

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the skill.

        This is the main entry point for skill execution. Subclasses must
        implement this method to provide the skill's functionality.

        Args:
            input_data: Dictionary with input parameters specific to the skill

        Returns:
            Dictionary with execution results. Should include at minimum:
            - success: bool - Whether execution succeeded
            - result/error: Any - The result or error message

        Raises:
            SkillExecutionError: If execution fails

        Example:
            >>> skill = MySkill()
            >>> result = skill.execute({"query": "explain this code", "code": "..."})
            >>> if result["success"]:
            ...     print(result["explanation"])
        """
        pass

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input before execution.

        Override this method to add custom validation logic for your skill.
        Raise SkillValidationError if validation fails.

        Args:
            input_data: Dictionary with input parameters

        Returns:
            True if validation passes

        Raises:
            SkillValidationError: If validation fails

        Example:
            >>> def validate_input(self, input_data):
            ...     if "code" not in input_data:
            ...         raise SkillValidationError("Missing required field: code")
            ...     return True
        """
        if not isinstance(input_data, dict):
            raise SkillValidationError(
                f"input_data must be a dictionary, got {type(input_data).__name__}"
            )
        return True

    def get_info(self) -> Dict[str, Any]:
        """Return skill metadata.

        Returns:
            Dictionary with skill information:
            - name: Skill name
            - description: What the skill does
            - version: Skill version
            - enabled: Whether skill is enabled

        Example:
            >>> skill = MySkill()
            >>> info = skill.get_info()
            >>> print(f"{info['name']} v{info['version']}: {info['description']}")
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled
        }

    def enable(self) -> None:
        """Enable the skill.

        Example:
            >>> skill = MySkill()
            >>> skill.disable()
            >>> skill.enable()
            >>> assert skill.enabled is True
        """
        self.enabled = True

    def disable(self) -> None:
        """Disable the skill.

        Example:
            >>> skill = MySkill()
            >>> skill.disable()
            >>> assert skill.enabled is False
        """
        self.enabled = False

    def __repr__(self) -> str:
        """String representation of skill.

        Returns:
            Skill name and version
        """
        status = "enabled" if self.enabled else "disabled"
        return f"<{self.__class__.__name__}(name='{self.name}', version='{self.version}', {status})>"
