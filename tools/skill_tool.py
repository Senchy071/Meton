"""Skill Invocation Tool for Meton.

This tool allows the agent to invoke skills by name, enabling high-level
task execution through specialized skill capabilities.

Example:
    >>> from tools.skill_tool import SkillInvocationTool
    >>> from skills.skill_manager import SkillManager
    >>>
    >>> manager = SkillManager()
    >>> tool = SkillInvocationTool(manager)
    >>> result = tool._run('{"skill": "code-reviewer", "input": {"code": "..."}}')
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union

from pydantic import Field

from tools.base import MetonBaseTool, ToolConfig
from skills.skill_manager import SkillManager
from skills.base import BaseSkill
from skills.markdown_skill import MarkdownSkill


class SkillToolConfig(ToolConfig):
    """Configuration for skill invocation tool."""
    enabled: bool = True
    verbose: bool = False


class SkillInvocationTool(MetonBaseTool):
    """Tool for invoking Meton skills.

    This tool allows the agent to invoke skills by name. Skills are high-level
    capabilities that perform specialized tasks like code review, explanation,
    debugging, and refactoring.

    The agent can use this tool when:
    - A task requires specialized analysis (code review, debugging)
    - A high-level operation is needed (explanation, documentation)
    - The task matches a skill's description

    Input Format:
        {"skill": "skill-name", "input": {"key": "value", ...}}

    Example:
        >>> tool = SkillInvocationTool(skill_manager)
        >>> result = tool._run('{"skill": "code-explainer", "input": {"code": "def foo(): pass"}}')
    """

    name: str = "invoke_skill"
    description: str = (
        "Invoke a Meton skill for high-level tasks. "
        "Skills are specialized capabilities for code review, explanation, debugging, etc. "
        "Input: {\"skill\": \"skill-name\", \"input\": {\"key\": \"value\", ...}}. "
        "Use /skill list to see available skills."
    )

    skill_manager: SkillManager = Field(...)
    config: SkillToolConfig = Field(default_factory=SkillToolConfig)
    logger: Optional[logging.Logger] = Field(default=None)

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True

    def __init__(self, skill_manager: SkillManager, **kwargs):
        """Initialize the skill invocation tool.

        Args:
            skill_manager: SkillManager instance with loaded skills
            **kwargs: Additional configuration options
        """
        super().__init__(skill_manager=skill_manager, **kwargs)
        self.logger = logging.getLogger("meton.skill_tool")

    def _run(self, input_str: str) -> str:
        """Invoke a skill by name.

        Args:
            input_str: JSON string with skill name and input data
                      Format: {"skill": "skill-name", "input": {...}}

        Returns:
            JSON string with skill execution result
        """
        # Check if enabled
        if not self.config.enabled:
            return json.dumps({
                "success": False,
                "error": "Skill invocation is disabled.",
                "result": None
            })

        # Parse input
        success, data = self._parse_json_input(input_str, ["skill"])
        if not success:
            return json.dumps({
                "success": False,
                "error": data,  # data is error message
                "result": None
            })

        skill_name = data.get("skill", "").strip()
        skill_input = data.get("input", {})

        if not skill_name:
            return json.dumps({
                "success": False,
                "error": "Skill name is required",
                "result": None
            })

        # Get the skill
        skill = self.skill_manager.get_skill(skill_name)
        if skill is None:
            available = self.skill_manager.list_loaded_skills()
            return json.dumps({
                "success": False,
                "error": f"Skill '{skill_name}' not found. Available: {', '.join(available)}",
                "result": None
            })

        # Execute the skill
        try:
            if isinstance(skill, BaseSkill):
                # Python skill
                result = skill.execute(skill_input)
            elif isinstance(skill, MarkdownSkill):
                # Markdown skill - return instructions for agent to follow
                result = {
                    "type": "markdown_skill",
                    "name": skill.name,
                    "instructions": skill.instructions,
                    "allowed_tools": skill.allowed_tools,
                    "model": skill.model,
                    "note": "Follow these instructions to complete the task"
                }
            else:
                result = {"error": f"Unknown skill type: {type(skill)}"}

            self._log_execution("invoke_skill", f"skill={skill_name}")

            return json.dumps({
                "success": True,
                "skill": skill_name,
                "result": result
            }, indent=2, default=str)

        except Exception as e:
            self.logger.error(f"Skill execution error: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "result": None
            })

    def get_available_skills(self) -> List[Dict[str, str]]:
        """Get list of available skills with descriptions.

        Returns:
            List of skill info dicts with name, type, and description
        """
        skills = []
        for name in self.skill_manager.list_loaded_skills():
            skill = self.skill_manager.get_skill(name)
            if skill:
                skill_type = self.skill_manager.get_skill_type(name)
                if isinstance(skill, BaseSkill):
                    description = skill.description
                elif isinstance(skill, MarkdownSkill):
                    description = skill.description
                else:
                    description = "Unknown skill type"

                skills.append({
                    "name": name,
                    "type": skill_type,
                    "description": description
                })

        return skills

    def generate_prompt_section(self) -> str:
        """Generate a system prompt section describing available skills.

        Returns:
            Formatted string for inclusion in agent system prompt
        """
        skills = self.get_available_skills()
        if not skills:
            return ""

        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "AVAILABLE SKILLS (invoke with invoke_skill tool):",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            ""
        ]

        for skill in skills:
            lines.append(f"- {skill['name']} ({skill['type']}): {skill['description']}")

        lines.append("")
        lines.append("To invoke a skill:")
        lines.append('ACTION: invoke_skill')
        lines.append('ACTION_INPUT: {"skill": "skill-name", "input": {"key": "value"}}')
        lines.append("")

        return "\n".join(lines)
