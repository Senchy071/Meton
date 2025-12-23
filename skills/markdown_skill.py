"""Markdown-based Skill Definition for Meton.

This module provides support for Claude Code-style markdown skill definitions.
Skills are defined in .md files with YAML frontmatter containing metadata
and markdown content containing instructions.

File Format:
    ---
    name: skill-name
    description: When to use this skill
    allowed-tools: Read, Grep, Glob  # optional
    model: primary  # optional
    ---

    ## Instructions
    Your skill instructions here...

Example:
    >>> from skills.markdown_skill import MarkdownSkill
    >>>
    >>> skill = MarkdownSkill.from_file(".meton/skills/code-reviewer/SKILL.md")
    >>> print(skill.name)
    'code-reviewer'
    >>> print(skill.description)
    'Review code for best practices...'
"""

import re
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field


class SkillParseError(Exception):
    """Error parsing a markdown skill definition."""
    pass


class SkillValidationError(Exception):
    """Error validating skill metadata."""
    pass


@dataclass
class MarkdownSkill:
    """Represents a markdown-based skill definition.

    This class mirrors Claude Code's skill format where skills are defined
    in markdown files with YAML frontmatter for metadata.

    Attributes:
        name: Unique skill identifier (lowercase, hyphens, max 64 chars)
        description: What the skill does AND when to use it (max 1024 chars)
        instructions: Full markdown content with instructions
        allowed_tools: Optional list of allowed tool names
        model: Optional model to use (primary, fallback, quick, or specific)
        version: Skill version (default: 1.0.0)
        enabled: Whether the skill is enabled
        source_path: Path to the source .md file
        additional_files: Paths to additional referenced files
    """

    name: str
    description: str
    instructions: str
    allowed_tools: Optional[List[str]] = None
    model: Optional[str] = None
    version: str = "1.0.0"
    enabled: bool = True
    source_path: Optional[Path] = None
    additional_files: List[Path] = field(default_factory=list)

    # Class-level constants
    MAX_NAME_LENGTH = 64
    MAX_DESCRIPTION_LENGTH = 1024
    NAME_PATTERN = re.compile(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$')

    def __post_init__(self):
        """Validate skill after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate skill metadata.

        Raises:
            SkillValidationError: If validation fails
        """
        # Validate name
        if not self.name:
            raise SkillValidationError("Skill name is required")

        if len(self.name) > self.MAX_NAME_LENGTH:
            raise SkillValidationError(
                f"Skill name exceeds {self.MAX_NAME_LENGTH} characters"
            )

        if not self.NAME_PATTERN.match(self.name):
            raise SkillValidationError(
                f"Invalid skill name '{self.name}'. Must be lowercase with "
                "hyphens only, cannot start or end with hyphen"
            )

        # Validate description
        if not self.description:
            raise SkillValidationError("Skill description is required")

        if len(self.description) > self.MAX_DESCRIPTION_LENGTH:
            raise SkillValidationError(
                f"Skill description exceeds {self.MAX_DESCRIPTION_LENGTH} characters"
            )

        # Validate instructions
        if not self.instructions or not self.instructions.strip():
            raise SkillValidationError("Skill instructions are required")

    @classmethod
    def from_file(cls, file_path: str | Path) -> "MarkdownSkill":
        """Load a skill from a markdown file.

        Args:
            file_path: Path to the SKILL.md file

        Returns:
            MarkdownSkill instance

        Raises:
            SkillParseError: If file cannot be parsed
            SkillValidationError: If skill metadata is invalid
            FileNotFoundError: If file doesn't exist

        Example:
            >>> skill = MarkdownSkill.from_file(".meton/skills/reviewer/SKILL.md")
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Skill file not found: {path}")

        content = path.read_text(encoding='utf-8')
        skill = cls.from_string(content)
        skill.source_path = path

        # Discover additional files in the same directory
        skill.additional_files = cls._discover_additional_files(path.parent)

        return skill

    @classmethod
    def from_string(cls, content: str) -> "MarkdownSkill":
        """Parse a skill from markdown string content.

        Args:
            content: Markdown content with YAML frontmatter

        Returns:
            MarkdownSkill instance

        Raises:
            SkillParseError: If content cannot be parsed
            SkillValidationError: If skill metadata is invalid

        Example:
            >>> content = '''---
            ... name: my-skill
            ... description: Does something useful
            ... ---
            ... ## Instructions
            ... Do the thing.
            ... '''
            >>> skill = MarkdownSkill.from_string(content)
        """
        # Parse YAML frontmatter
        frontmatter, instructions = cls._parse_frontmatter(content)

        # Extract required fields
        name = frontmatter.get('name')
        description = frontmatter.get('description')

        if not name:
            raise SkillParseError("Missing required field 'name' in frontmatter")
        if not description:
            raise SkillParseError("Missing required field 'description' in frontmatter")

        # Extract optional fields
        allowed_tools = cls._parse_tools(frontmatter.get('allowed-tools'))
        model = frontmatter.get('model')
        version = frontmatter.get('version', '1.0.0')

        return cls(
            name=name,
            description=description,
            instructions=instructions,
            allowed_tools=allowed_tools,
            model=model,
            version=str(version),
        )

    @staticmethod
    def _parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from markdown content.

        Args:
            content: Full markdown content

        Returns:
            Tuple of (frontmatter dict, remaining content)

        Raises:
            SkillParseError: If frontmatter is missing or invalid
        """
        # Match YAML frontmatter between --- delimiters
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(pattern, content, re.DOTALL)

        if not match:
            raise SkillParseError(
                "Invalid skill format. Expected YAML frontmatter between --- delimiters"
            )

        yaml_content = match.group(1)
        markdown_content = match.group(2).strip()

        try:
            frontmatter = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise SkillParseError(f"Invalid YAML in frontmatter: {e}")

        if not isinstance(frontmatter, dict):
            raise SkillParseError("Frontmatter must be a YAML mapping")

        return frontmatter, markdown_content

    @staticmethod
    def _parse_tools(tools_value: Optional[str | List[str]]) -> Optional[List[str]]:
        """Parse allowed-tools field.

        Args:
            tools_value: String (comma-separated) or list of tool names

        Returns:
            List of tool names or None
        """
        if tools_value is None:
            return None

        if isinstance(tools_value, list):
            return [t.strip() for t in tools_value if t.strip()]

        if isinstance(tools_value, str):
            return [t.strip() for t in tools_value.split(',') if t.strip()]

        return None

    @staticmethod
    def _discover_additional_files(skill_dir: Path) -> List[Path]:
        """Discover additional files in a skill directory.

        Args:
            skill_dir: Directory containing the SKILL.md

        Returns:
            List of additional file paths (excluding SKILL.md)
        """
        additional = []

        if not skill_dir.exists() or not skill_dir.is_dir():
            return additional

        for item in skill_dir.rglob('*'):
            if item.is_file() and item.name != 'SKILL.md':
                additional.append(item)

        return additional

    def get_info(self) -> Dict[str, Any]:
        """Return skill metadata.

        Returns:
            Dictionary with skill information

        Example:
            >>> info = skill.get_info()
            >>> print(info['name'], info['description'])
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "type": "markdown",
            "allowed_tools": self.allowed_tools,
            "model": self.model,
            "source_path": str(self.source_path) if self.source_path else None,
        }

    def get_system_prompt(self) -> str:
        """Generate system prompt for LLM from skill instructions.

        Returns:
            Formatted system prompt string
        """
        prompt_parts = [
            f"# Skill: {self.name}",
            "",
            self.instructions,
        ]

        if self.allowed_tools:
            prompt_parts.extend([
                "",
                "## Allowed Tools",
                f"You may only use these tools: {', '.join(self.allowed_tools)}",
            ])

        return "\n".join(prompt_parts)

    def get_additional_file_content(self, filename: str) -> Optional[str]:
        """Get content of an additional file.

        Args:
            filename: Name of the file to read

        Returns:
            File content or None if not found
        """
        for file_path in self.additional_files:
            if file_path.name == filename or str(file_path).endswith(filename):
                try:
                    return file_path.read_text(encoding='utf-8')
                except Exception:
                    return None
        return None

    def enable(self) -> None:
        """Enable the skill."""
        self.enabled = True

    def disable(self) -> None:
        """Disable the skill."""
        self.enabled = False

    def __repr__(self) -> str:
        """String representation."""
        status = "enabled" if self.enabled else "disabled"
        tools = f", tools={self.allowed_tools}" if self.allowed_tools else ""
        return f"<MarkdownSkill(name='{self.name}', version='{self.version}', {status}{tools})>"


class MarkdownSkillLoader:
    """Discovers and loads markdown-based skills from multiple directories.

    Skill Discovery Order (highest to lowest precedence):
    1. Project skills: .meton/skills/
    2. User skills: ~/.meton/skills/
    3. Built-in skills: skills/md_skills/

    Each skill should be in its own directory with a SKILL.md file:
        .meton/skills/code-reviewer/SKILL.md
        .meton/skills/debugger/SKILL.md

    Example:
        >>> loader = MarkdownSkillLoader()
        >>> loader.discover()
        >>> skills = loader.load_all()
        >>> print([s.name for s in skills])
        ['code-reviewer', 'debugger', 'doc-generator']
    """

    def __init__(
        self,
        project_dir: Optional[Path] = None,
        user_dir: Optional[Path] = None,
        builtin_dir: Optional[Path] = None
    ):
        """Initialize the skill loader.

        Args:
            project_dir: Project skills directory (default: .meton/skills/)
            user_dir: User skills directory (default: ~/.meton/skills/)
            builtin_dir: Built-in skills directory (default: skills/md_skills/)
        """
        self.project_dir = project_dir or Path(".meton/skills")
        self.user_dir = user_dir or Path.home() / ".meton" / "skills"
        self.builtin_dir = builtin_dir or Path("skills/md_skills")

        self.logger = logging.getLogger("meton.markdown_skill_loader")

        # Discovered skill paths (name -> path)
        self.discovered: Dict[str, Path] = {}

        # Loaded skills (name -> MarkdownSkill)
        self.loaded: Dict[str, MarkdownSkill] = {}

    def discover(self) -> Dict[str, Path]:
        """Discover all available markdown skills.

        Scans all skill directories in precedence order.
        Higher precedence directories override lower ones.

        Returns:
            Dictionary mapping skill names to their SKILL.md paths
        """
        self.discovered.clear()

        # Scan in reverse precedence order (builtin first, project last)
        # so that project skills override user skills which override builtins
        for skill_dir in [self.builtin_dir, self.user_dir, self.project_dir]:
            self._scan_directory(skill_dir)

        self.logger.info(f"Discovered {len(self.discovered)} markdown skills")
        return self.discovered.copy()

    def _scan_directory(self, base_dir: Path) -> None:
        """Scan a directory for skill definitions.

        Args:
            base_dir: Directory to scan
        """
        if not base_dir.exists() or not base_dir.is_dir():
            self.logger.debug(f"Skill directory not found: {base_dir}")
            return

        # Look for SKILL.md files in subdirectories
        for item in base_dir.iterdir():
            if item.is_dir():
                skill_file = item / "SKILL.md"
                if skill_file.exists():
                    # Use directory name as skill identifier
                    skill_name = item.name
                    self.discovered[skill_name] = skill_file
                    self.logger.debug(f"Found skill: {skill_name} at {skill_file}")

        # Also check for .md files directly in the directory (flat structure)
        for item in base_dir.glob("*.md"):
            if item.name != "SKILL.md" and item.name != "README.md":
                skill_name = item.stem
                self.discovered[skill_name] = item
                self.logger.debug(f"Found flat skill: {skill_name} at {item}")

    def load_skill(self, name: str) -> Optional[MarkdownSkill]:
        """Load a specific skill by name.

        Args:
            name: Skill name to load

        Returns:
            MarkdownSkill instance or None if not found/failed
        """
        if name in self.loaded:
            return self.loaded[name]

        if name not in self.discovered:
            self.logger.warning(f"Skill '{name}' not discovered")
            return None

        try:
            skill = MarkdownSkill.from_file(self.discovered[name])
            self.loaded[name] = skill
            self.logger.info(f"Loaded markdown skill: {name}")
            return skill
        except (SkillParseError, SkillValidationError, FileNotFoundError) as e:
            self.logger.error(f"Failed to load skill '{name}': {e}")
            return None

    def load_all(self) -> List[MarkdownSkill]:
        """Load all discovered skills.

        Returns:
            List of successfully loaded MarkdownSkill instances
        """
        if not self.discovered:
            self.discover()

        skills = []
        for name in self.discovered:
            skill = self.load_skill(name)
            if skill:
                skills.append(skill)

        self.logger.info(f"Loaded {len(skills)}/{len(self.discovered)} markdown skills")
        return skills

    def unload_skill(self, name: str) -> bool:
        """Unload a skill.

        Args:
            name: Skill name to unload

        Returns:
            True if unloaded, False if wasn't loaded
        """
        if name in self.loaded:
            del self.loaded[name]
            self.logger.info(f"Unloaded skill: {name}")
            return True
        return False

    def reload_skill(self, name: str) -> Optional[MarkdownSkill]:
        """Reload a skill from disk.

        Args:
            name: Skill name to reload

        Returns:
            Reloaded skill or None if failed
        """
        self.unload_skill(name)
        return self.load_skill(name)

    def get_skill(self, name: str) -> Optional[MarkdownSkill]:
        """Get a loaded skill by name.

        Args:
            name: Skill name

        Returns:
            MarkdownSkill instance or None
        """
        return self.loaded.get(name)

    def list_discovered(self) -> List[str]:
        """List all discovered skill names.

        Returns:
            List of skill names
        """
        return list(self.discovered.keys())

    def list_loaded(self) -> List[str]:
        """List all loaded skill names.

        Returns:
            List of loaded skill names
        """
        return list(self.loaded.keys())

    def get_skill_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all loaded skills.

        Useful for injecting into system prompts for model-invoked discovery.

        Returns:
            Dictionary mapping skill names to descriptions
        """
        return {
            name: skill.description
            for name, skill in self.loaded.items()
        }

    def generate_skills_prompt_section(self) -> str:
        """Generate a prompt section listing available skills.

        This is injected into the agent's system prompt for model-invoked
        skill discovery.

        Returns:
            Formatted string describing available skills
        """
        if not self.loaded:
            return ""

        lines = ["## Available Skills", ""]

        for name, skill in sorted(self.loaded.items()):
            lines.append(f"### {name}")
            lines.append(f"**Description:** {skill.description}")
            if skill.allowed_tools:
                lines.append(f"**Allowed tools:** {', '.join(skill.allowed_tools)}")
            lines.append("")

        return "\n".join(lines)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<MarkdownSkillLoader("
            f"discovered={len(self.discovered)}, "
            f"loaded={len(self.loaded)})>"
        )
