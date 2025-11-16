#!/usr/bin/env python3
"""
Project Template Manager

Manages project templates for quick setup with variable substitution,
file generation, and configuration management.
"""

import os
import re
import yaml
import shutil
import stat
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class TemplateFile:
    """Represents a file in a project template."""
    path: str  # Relative path in project
    content: str  # File content (may contain {{variables}})
    is_executable: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Template:
    """Represents a project template."""
    id: str
    name: str
    description: str
    category: str  # web, api, cli, ml, data_science, general
    files: List[TemplateFile] = field(default_factory=list)
    configuration: Dict = field(default_factory=dict)  # Default Meton config
    dependencies: List[str] = field(default_factory=list)  # Python packages
    setup_commands: List[str] = field(default_factory=list)  # Post-creation commands
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0"

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert TemplateFile objects to dicts
        data['files'] = [f.to_dict() if isinstance(f, TemplateFile) else f for f in data['files']]
        return data


class TemplateManager:
    """Manages project templates for quick setup."""

    VALID_CATEGORIES = {'web', 'api', 'cli', 'ml', 'data_science', 'general'}
    VARIABLE_PATTERN = re.compile(r'\{\{(\w+)(?:\|([^}]+))?\}\}')

    def __init__(self, templates_dir: str = "templates/templates"):
        """Initialize template manager.

        Args:
            templates_dir: Directory containing template YAML files
        """
        # Handle both absolute and relative paths
        if not os.path.isabs(templates_dir):
            # Relative to project root
            project_root = Path(__file__).parent.parent
            self.templates_dir = project_root / templates_dir
        else:
            self.templates_dir = Path(templates_dir)

        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.available_templates: Dict[str, Template] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load all templates from templates directory."""
        self.available_templates.clear()

        # Load from main templates directory
        if self.templates_dir.exists():
            self._load_from_directory(self.templates_dir)

        # Load from user templates directory
        user_templates = Path.home() / ".meton" / "templates"
        if user_templates.exists():
            self._load_from_directory(user_templates)

        # Load from project-specific templates
        project_templates = Path.cwd() / ".meton" / "templates"
        if project_templates.exists():
            self._load_from_directory(project_templates)

    def _load_from_directory(self, directory: Path) -> None:
        """Load templates from a specific directory.

        Args:
            directory: Directory to load templates from
        """
        for template_file in directory.glob("*.yaml"):
            try:
                with open(template_file, 'r') as f:
                    data = yaml.safe_load(f)

                if not data:
                    continue

                # Convert file dictionaries to TemplateFile objects
                files = []
                for file_data in data.get('files', []):
                    if isinstance(file_data, dict):
                        files.append(TemplateFile(**file_data))
                    else:
                        files.append(file_data)

                template = Template(
                    id=data['id'],
                    name=data['name'],
                    description=data['description'],
                    category=data['category'],
                    files=files,
                    configuration=data.get('configuration', {}),
                    dependencies=data.get('dependencies', []),
                    setup_commands=data.get('setup_commands', []),
                    created_at=data.get('created_at', datetime.now().isoformat()),
                    version=data.get('version', '1.0')
                )

                self.available_templates[template.id] = template

            except Exception as e:
                print(f"Warning: Failed to load template {template_file}: {e}")
                continue

    def list_templates(self, category: Optional[str] = None) -> List[Template]:
        """List available templates.

        Args:
            category: Filter by category (optional)

        Returns:
            List of templates
        """
        templates = list(self.available_templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        return sorted(templates, key=lambda t: (t.category, t.name))

    def get_template(self, template_id: str) -> Template:
        """Get specific template.

        Args:
            template_id: Template identifier

        Returns:
            Template object

        Raises:
            ValueError: If template not found
        """
        if template_id not in self.available_templates:
            raise ValueError(f"Template '{template_id}' not found")

        return self.available_templates[template_id]

    def create_project(
        self,
        template_id: str,
        project_name: str,
        output_dir: str,
        variables: Optional[Dict] = None
    ) -> str:
        """Create new project from template.

        Args:
            template_id: Template to use
            project_name: Name of new project
            output_dir: Directory to create project in
            variables: Variables for substitution

        Returns:
            Path to created project

        Raises:
            ValueError: If template not found or project exists
        """
        template = self.get_template(template_id)

        # Create project directory
        project_path = Path(output_dir) / project_name
        if project_path.exists():
            raise ValueError(f"Project directory already exists: {project_path}")

        project_path.mkdir(parents=True, exist_ok=True)

        # Prepare variables for substitution
        sub_vars = {
            'project_name': project_name,
            'version': '0.1.0',
            'description': f"A {template.name} project",
            'author': os.getenv('USER', 'Unknown'),
            'email': '',
            'python_version': '3.11',
        }
        if variables:
            sub_vars.update(variables)

        # Create files
        for template_file in template.files:
            file_path = project_path / template_file.path

            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Render content with variables
            content = self.render_file(template_file.content, sub_vars)

            # Write file
            with open(file_path, 'w') as f:
                f.write(content)

            # Set executable if needed
            if template_file.is_executable:
                file_path.chmod(file_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        # Create Meton configuration if provided
        if template.configuration:
            config_path = project_path / ".meton" / "config.yaml"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                yaml.dump(template.configuration, f, default_flow_style=False)

        return str(project_path)

    def add_template(self, template: Template) -> None:
        """Add custom template.

        Args:
            template: Template to add

        Raises:
            ValueError: If template is invalid
        """
        # Validate template
        issues = self.validate_template(template)
        if issues:
            raise ValueError(f"Invalid template: {', '.join(issues)}")

        # Save to user templates directory
        user_templates = Path.home() / ".meton" / "templates"
        user_templates.mkdir(parents=True, exist_ok=True)

        template_file = user_templates / f"{template.id}.yaml"

        # Convert to dictionary for YAML
        template_dict = template.to_dict()

        with open(template_file, 'w') as f:
            yaml.dump(template_dict, f, default_flow_style=False, sort_keys=False)

        # Add to available templates
        self.available_templates[template.id] = template

    def delete_template(self, template_id: str) -> bool:
        """Remove template.

        Args:
            template_id: Template to remove

        Returns:
            True if deleted, False if not found
        """
        # Remove from available templates
        if template_id not in self.available_templates:
            return False

        del self.available_templates[template_id]

        # Try to delete from user templates
        user_templates = Path.home() / ".meton" / "templates"
        template_file = user_templates / f"{template_id}.yaml"

        if template_file.exists():
            template_file.unlink()

        return True

    def validate_template(self, template: Template) -> List[str]:
        """Check template validity.

        Args:
            template: Template to validate

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        # Check required fields
        if not template.id:
            issues.append("Template ID is required")

        if not template.name:
            issues.append("Template name is required")

        if not template.description:
            issues.append("Template description is required")

        # Check category
        if template.category not in self.VALID_CATEGORIES:
            issues.append(f"Invalid category '{template.category}'. Must be one of: {', '.join(self.VALID_CATEGORIES)}")

        # Check files
        if not template.files:
            issues.append("Template must have at least one file")

        # Validate file paths
        for file in template.files:
            # Check for directory traversal
            if '..' in file.path or file.path.startswith('/'):
                issues.append(f"Invalid file path '{file.path}': no '..' or absolute paths allowed")

        return issues

    def render_file(self, content: str, variables: Dict) -> str:
        """Replace {{variable}} placeholders.

        Supports default values: {{var|default}}

        Args:
            content: Content with {{variables}}
            variables: Variable values

        Returns:
            Rendered content
        """
        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ''

            return str(variables.get(var_name, default_value))

        return self.VARIABLE_PATTERN.sub(replace_var, content)

    def get_template_preview(self, template_id: str) -> str:
        """Show template structure.

        Args:
            template_id: Template to preview

        Returns:
            Formatted preview string

        Raises:
            ValueError: If template not found
        """
        template = self.get_template(template_id)

        lines = []
        lines.append(f"Template: {template.name}")
        lines.append(f"ID: {template.id}")
        lines.append(f"Category: {template.category}")
        lines.append(f"Description: {template.description}")
        lines.append(f"Version: {template.version}")
        lines.append("")

        lines.append("Files:")
        for file in template.files:
            executable = " [executable]" if file.is_executable else ""
            lines.append(f"  - {file.path}{executable}")
        lines.append("")

        if template.dependencies:
            lines.append("Dependencies:")
            for dep in template.dependencies:
                lines.append(f"  - {dep}")
            lines.append("")

        if template.setup_commands:
            lines.append("Setup Commands:")
            for cmd in template.setup_commands:
                lines.append(f"  - {cmd}")
            lines.append("")

        if template.configuration:
            lines.append("Meton Configuration:")
            config_yaml = yaml.dump(template.configuration, default_flow_style=False)
            for line in config_yaml.split('\n'):
                if line:
                    lines.append(f"  {line}")

        return '\n'.join(lines)

    def get_categories(self) -> List[str]:
        """Get list of all template categories.

        Returns:
            List of category names
        """
        categories = set()
        for template in self.available_templates.values():
            categories.add(template.category)

        return sorted(categories)

    def reload_templates(self) -> None:
        """Reload all templates from disk."""
        self._load_templates()
