"""Hook Loader for Meton.

This module handles discovery and loading of hooks from:
1. config.yaml - hooks section
2. Markdown files with YAML frontmatter in .meton/hooks/ directories
3. User hooks in ~/.meton/hooks/
4. Built-in hooks in hooks/builtin/

Example markdown hook file (.meton/hooks/notify-on-error/HOOK.md):
    ---
    name: notify-on-error
    hook_type: post_tool
    command: notify-send 'Tool Error' '{error}'
    condition: "{success} == false"
    timeout: 5
    ---

    # Notify on Error

    This hook sends a desktop notification when a tool fails.
"""

import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

import yaml

from hooks.base import Hook, HookType


class HookLoader:
    """Loads hooks from various sources.

    Discovery order (later overrides earlier):
    1. Built-in hooks from hooks/builtin/
    2. User hooks from ~/.meton/hooks/
    3. Project hooks from .meton/hooks/
    4. Config hooks from config.yaml hooks section

    Attributes:
        base_dir: Base directory for the project
        user_hooks_dir: User-level hooks directory
        project_hooks_dir: Project-level hooks directory
        builtin_hooks_dir: Built-in hooks directory
        logger: Logger instance
    """

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        user_hooks_dir: Optional[Path] = None,
        project_hooks_dir: Optional[Path] = None,
        builtin_hooks_dir: Optional[Path] = None,
    ):
        """Initialize the hook loader.

        Args:
            base_dir: Base project directory (defaults to cwd)
            user_hooks_dir: User hooks directory (defaults to ~/.meton/hooks)
            project_hooks_dir: Project hooks directory (defaults to .meton/hooks)
            builtin_hooks_dir: Built-in hooks directory (defaults to hooks/builtin)
        """
        self.base_dir = base_dir or Path.cwd()
        self.user_hooks_dir = user_hooks_dir or Path.home() / ".meton" / "hooks"
        self.project_hooks_dir = project_hooks_dir or self.base_dir / ".meton" / "hooks"
        self.builtin_hooks_dir = builtin_hooks_dir or self.base_dir / "hooks" / "builtin"
        self.logger = logging.getLogger("meton.hooks.loader")

    def load_all(self, config: Optional[Dict[str, Any]] = None) -> List[Hook]:
        """Load all hooks from all sources.

        Args:
            config: Optional config dict with hooks section

        Returns:
            List of all loaded hooks
        """
        hooks = []

        # 1. Built-in hooks
        builtin = self.load_from_directory(self.builtin_hooks_dir, "builtin")
        hooks.extend(builtin)
        self.logger.debug(f"Loaded {len(builtin)} built-in hooks")

        # 2. User hooks
        user = self.load_from_directory(self.user_hooks_dir, "user")
        hooks.extend(user)
        self.logger.debug(f"Loaded {len(user)} user hooks")

        # 3. Project hooks
        project = self.load_from_directory(self.project_hooks_dir, "project")
        hooks.extend(project)
        self.logger.debug(f"Loaded {len(project)} project hooks")

        # 4. Config hooks
        if config:
            config_hooks = self.load_from_config(config)
            hooks.extend(config_hooks)
            self.logger.debug(f"Loaded {len(config_hooks)} config hooks")

        self.logger.info(f"Total hooks loaded: {len(hooks)}")
        return hooks

    def load_from_directory(self, directory: Path, source_type: str) -> List[Hook]:
        """Load hooks from a directory.

        Each hook should be in its own subdirectory with a HOOK.md file.

        Args:
            directory: Directory to scan
            source_type: Source identifier (builtin/user/project)

        Returns:
            List of loaded hooks
        """
        hooks = []

        if not directory.exists():
            return hooks

        # Look for subdirectories with HOOK.md files
        for item in directory.iterdir():
            if item.is_dir():
                hook_file = item / "HOOK.md"
                if hook_file.exists():
                    try:
                        hook = self.load_from_markdown(hook_file, source_type)
                        if hook:
                            hooks.append(hook)
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to load hook from {hook_file}: {e}"
                        )

        return hooks

    def load_from_markdown(self, file_path: Path, source_type: str) -> Optional[Hook]:
        """Load a hook from a markdown file with YAML frontmatter.

        Args:
            file_path: Path to HOOK.md file
            source_type: Source identifier

        Returns:
            Hook instance or None if invalid
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            self.logger.error(f"Failed to read {file_path}: {e}")
            return None

        # Parse frontmatter
        frontmatter, _ = self._parse_frontmatter(content)
        if not frontmatter:
            self.logger.warning(f"No frontmatter in {file_path}")
            return None

        # Validate required fields
        if "name" not in frontmatter:
            self.logger.warning(f"Missing 'name' in {file_path}")
            return None

        if "hook_type" not in frontmatter:
            self.logger.warning(f"Missing 'hook_type' in {file_path}")
            return None

        if "command" not in frontmatter:
            self.logger.warning(f"Missing 'command' in {file_path}")
            return None

        # Parse hook type
        try:
            hook_type = HookType(frontmatter["hook_type"])
        except ValueError:
            self.logger.warning(
                f"Invalid hook_type '{frontmatter['hook_type']}' in {file_path}"
            )
            return None

        # Parse target_names if present
        target_names = frontmatter.get("target_names", [])
        if isinstance(target_names, str):
            target_names = [t.strip() for t in target_names.split(",")]

        # Create hook
        hook = Hook(
            name=frontmatter["name"],
            hook_type=hook_type,
            command=frontmatter["command"],
            condition=frontmatter.get("condition"),
            timeout=float(frontmatter.get("timeout", 30.0)),
            enabled=frontmatter.get("enabled", True),
            blocking=frontmatter.get("blocking", True),
            target_names=target_names,
            description=frontmatter.get("description", ""),
            source=f"{source_type}:{file_path}",
        )

        self.logger.debug(f"Loaded hook '{hook.name}' from {file_path}")
        return hook

    def load_from_config(self, config: Dict[str, Any]) -> List[Hook]:
        """Load hooks from config dictionary.

        Expected format:
            hooks:
              enabled: true
              items:
                - name: my-hook
                  hook_type: post_tool
                  command: echo "hello"

        Args:
            config: Configuration dictionary

        Returns:
            List of hooks from config
        """
        hooks = []
        hooks_config = config.get("hooks", {})

        if not hooks_config.get("enabled", True):
            return hooks

        items = hooks_config.get("items", [])
        for item in items:
            try:
                hook = self._parse_config_hook(item)
                if hook:
                    hooks.append(hook)
            except Exception as e:
                self.logger.warning(f"Failed to parse config hook: {e}")

        return hooks

    def _parse_config_hook(self, item: Dict[str, Any]) -> Optional[Hook]:
        """Parse a hook from config item.

        Args:
            item: Hook configuration dict

        Returns:
            Hook instance or None if invalid
        """
        if "name" not in item:
            return None
        if "hook_type" not in item:
            return None
        if "command" not in item:
            return None

        try:
            hook_type = HookType(item["hook_type"])
        except ValueError:
            return None

        target_names = item.get("target_names", [])
        if isinstance(target_names, str):
            target_names = [t.strip() for t in target_names.split(",")]

        return Hook(
            name=item["name"],
            hook_type=hook_type,
            command=item["command"],
            condition=item.get("condition"),
            timeout=float(item.get("timeout", 30.0)),
            enabled=item.get("enabled", True),
            blocking=item.get("blocking", True),
            target_names=target_names,
            description=item.get("description", ""),
            source="config",
        )

    def _parse_frontmatter(self, content: str) -> tuple:
        """Parse YAML frontmatter from markdown content.

        Args:
            content: Markdown content with optional frontmatter

        Returns:
            Tuple of (frontmatter_dict, body_content)
        """
        # Match frontmatter between --- delimiters
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, content, re.DOTALL)

        if not match:
            return {}, content

        try:
            frontmatter = yaml.safe_load(match.group(1))
            body = match.group(2)
            return frontmatter or {}, body
        except yaml.YAMLError as e:
            self.logger.warning(f"Failed to parse frontmatter: {e}")
            return {}, content

    def discover(self) -> Dict[str, List[str]]:
        """Discover available hooks without loading them.

        Returns:
            Dictionary mapping source type to list of hook names
        """
        discovered = {
            "builtin": [],
            "user": [],
            "project": [],
        }

        for source_type, directory in [
            ("builtin", self.builtin_hooks_dir),
            ("user", self.user_hooks_dir),
            ("project", self.project_hooks_dir),
        ]:
            if directory.exists():
                for item in directory.iterdir():
                    if item.is_dir() and (item / "HOOK.md").exists():
                        discovered[source_type].append(item.name)

        return discovered

    def create_hook_directory(
        self,
        name: str,
        hook_type: HookType,
        command: str,
        location: str = "project",
        description: str = "",
        **kwargs
    ) -> Path:
        """Create a new hook directory with HOOK.md file.

        Args:
            name: Hook name
            hook_type: Type of hook
            command: Shell command to execute
            location: Where to create (project/user)
            description: Hook description
            **kwargs: Additional hook parameters

        Returns:
            Path to created HOOK.md file
        """
        base_dir = (
            self.project_hooks_dir if location == "project"
            else self.user_hooks_dir
        )

        hook_dir = base_dir / name
        hook_dir.mkdir(parents=True, exist_ok=True)

        # Build frontmatter
        frontmatter = {
            "name": name,
            "hook_type": hook_type.value,
            "command": command,
            "description": description,
        }
        frontmatter.update(kwargs)

        # Build content
        yaml_content = yaml.dump(frontmatter, default_flow_style=False)
        content = f"""---
{yaml_content}---

# {name}

{description or 'A custom hook.'}

## Command

```bash
{command}
```

## Usage

This hook runs on `{hook_type.value}` events.
"""

        hook_file = hook_dir / "HOOK.md"
        hook_file.write_text(content, encoding="utf-8")

        self.logger.info(f"Created hook at {hook_file}")
        return hook_file
