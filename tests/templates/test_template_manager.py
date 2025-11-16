#!/usr/bin/env python3
"""
Comprehensive tests for Template Manager

Tests all aspects of template management including:
- Template loading and listing
- Project creation
- Variable substitution
- Validation
- Custom template management
- Edge cases and error handling
"""

import pytest
import tempfile
import shutil
import yaml
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)  # Ensure we're in the right directory

from templates.template_manager import TemplateManager, Template, TemplateFile


@pytest.fixture
def temp_templates_dir():
    """Create temporary templates directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def template_manager(temp_templates_dir):
    """Create template manager with temporary directory."""
    return TemplateManager(templates_dir=temp_templates_dir)


@pytest.fixture
def sample_template():
    """Create sample template for testing."""
    return Template(
        id="test-template",
        name="Test Template",
        description="A test template",
        category="general",
        files=[
            TemplateFile(
                path="README.md",
                content="# {{project_name}}\n\n{{description|A test project}}"
            ),
            TemplateFile(
                path="src/main.py",
                content="print('Hello from {{project_name}}')"
            ),
            TemplateFile(
                path="run.sh",
                content="#!/bin/bash\necho 'Running {{project_name}}'",
                is_executable=True
            )
        ],
        dependencies=["pytest"],
        setup_commands=["pip install -r requirements.txt"],
        version="1.0"
    )


# ========== Template Loading Tests ==========

def test_template_manager_initialization(template_manager):
    """Test template manager initializes correctly."""
    assert template_manager is not None
    assert isinstance(template_manager.available_templates, dict)
    assert template_manager.templates_dir.exists()


def test_list_all_templates(template_manager, sample_template):
    """Test listing all templates."""
    template_manager.add_template(sample_template)
    templates = template_manager.list_templates()
    assert len(templates) >= 1
    assert any(t.id == sample_template.id for t in templates)


def test_list_templates_by_category():
    """Test filtering templates by category."""
    # Use built-in templates
    manager = TemplateManager()
    api_templates = manager.list_templates(category="api")
    cli_templates = manager.list_templates(category="cli")

    # Built-in templates should include at least one API and one CLI template
    assert len(api_templates) >= 1
    assert len(cli_templates) >= 1
    assert all(t.category == "api" for t in api_templates)
    assert all(t.category == "cli" for t in cli_templates)


def test_get_existing_template():
    """Test retrieving existing template."""
    manager = TemplateManager()
    templates = manager.list_templates()

    if templates:
        template = manager.get_template(templates[0].id)
        assert template is not None
        assert template.id == templates[0].id


def test_get_nonexistent_template(template_manager):
    """Test getting non-existent template raises error."""
    with pytest.raises(ValueError, match="not found"):
        template_manager.get_template("nonexistent-template")


# ========== Project Creation Tests ==========

def test_create_project_basic(template_manager, sample_template, temp_output_dir):
    """Test basic project creation."""
    template_manager.add_template(sample_template)

    project_path = template_manager.create_project(
        template_id="test-template",
        project_name="my-project",
        output_dir=temp_output_dir
    )

    project_dir = Path(project_path)
    assert project_dir.exists()
    assert (project_dir / "README.md").exists()
    assert (project_dir / "src" / "main.py").exists()


def test_create_project_with_variables(template_manager, sample_template, temp_output_dir):
    """Test project creation with custom variables."""
    template_manager.add_template(sample_template)

    project_path = template_manager.create_project(
        template_id="test-template",
        project_name="my-project",
        output_dir=temp_output_dir,
        variables={"description": "My custom description"}
    )

    readme = Path(project_path) / "README.md"
    content = readme.read_text()

    assert "my-project" in content
    assert "My custom description" in content


def test_create_project_existing_directory(template_manager, sample_template, temp_output_dir):
    """Test creating project in existing directory fails."""
    template_manager.add_template(sample_template)

    # Create project once
    template_manager.create_project(
        template_id="test-template",
        project_name="my-project",
        output_dir=temp_output_dir
    )

    # Try to create again - should fail
    with pytest.raises(ValueError, match="already exists"):
        template_manager.create_project(
            template_id="test-template",
            project_name="my-project",
            output_dir=temp_output_dir
        )


def test_create_project_executable_permissions(template_manager, sample_template, temp_output_dir):
    """Test executable files get correct permissions."""
    template_manager.add_template(sample_template)

    project_path = template_manager.create_project(
        template_id="test-template",
        project_name="my-project",
        output_dir=temp_output_dir
    )

    run_script = Path(project_path) / "run.sh"
    assert run_script.exists()

    # Check if file is executable
    import os
    assert os.access(run_script, os.X_OK)


# ========== Variable Substitution Tests ==========

def test_render_file_basic(template_manager):
    """Test basic variable substitution."""
    content = "Hello {{name}}!"
    result = template_manager.render_file(content, {"name": "World"})
    assert result == "Hello World!"


def test_render_file_with_default(template_manager):
    """Test variable substitution with default value."""
    content = "Hello {{name|World}}!"
    result = template_manager.render_file(content, {})
    assert result == "Hello World!"


def test_render_file_missing_variable(template_manager):
    """Test missing variable without default."""
    content = "Hello {{name}}!"
    result = template_manager.render_file(content, {})
    assert result == "Hello !"


def test_render_file_multiple_variables(template_manager):
    """Test multiple variable substitution."""
    content = "{{greeting}} {{name}}, version {{version|1.0}}"
    result = template_manager.render_file(content, {
        "greeting": "Hello",
        "name": "Alice"
    })
    assert result == "Hello Alice, version 1.0"


# ========== Template Validation Tests ==========

def test_validate_valid_template(template_manager, sample_template):
    """Test validation of valid template."""
    issues = template_manager.validate_template(sample_template)
    assert len(issues) == 0


def test_validate_missing_id(template_manager):
    """Test validation fails without ID."""
    template = Template(
        id="",
        name="Test",
        description="Test",
        category="general",
        files=[TemplateFile(path="test.txt", content="test")]
    )
    issues = template_manager.validate_template(template)
    assert any("ID is required" in issue for issue in issues)


def test_validate_missing_name(template_manager):
    """Test validation fails without name."""
    template = Template(
        id="test",
        name="",
        description="Test",
        category="general",
        files=[TemplateFile(path="test.txt", content="test")]
    )
    issues = template_manager.validate_template(template)
    assert any("name is required" in issue for issue in issues)


def test_validate_invalid_category(template_manager):
    """Test validation fails with invalid category."""
    template = Template(
        id="test",
        name="Test",
        description="Test",
        category="invalid",
        files=[TemplateFile(path="test.txt", content="test")]
    )
    issues = template_manager.validate_template(template)
    assert any("Invalid category" in issue for issue in issues)


def test_validate_no_files(template_manager):
    """Test validation fails without files."""
    template = Template(
        id="test",
        name="Test",
        description="Test",
        category="general",
        files=[]
    )
    issues = template_manager.validate_template(template)
    assert any("at least one file" in issue for issue in issues)


def test_validate_invalid_file_path(template_manager):
    """Test validation fails with invalid file paths."""
    template = Template(
        id="test",
        name="Test",
        description="Test",
        category="general",
        files=[
            TemplateFile(path="../etc/passwd", content="bad"),
            TemplateFile(path="/etc/hosts", content="bad")
        ]
    )
    issues = template_manager.validate_template(template)
    assert len(issues) >= 2
    assert any(".." in issue or "absolute" in issue for issue in issues)


# ========== Custom Template Management Tests ==========

def test_add_template(template_manager, sample_template):
    """Test adding custom template."""
    template_manager.add_template(sample_template)
    assert sample_template.id in template_manager.available_templates


def test_add_invalid_template(template_manager):
    """Test adding invalid template fails."""
    invalid_template = Template(
        id="",  # Invalid: empty ID
        name="Test",
        description="Test",
        category="general",
        files=[]  # Invalid: no files
    )

    with pytest.raises(ValueError, match="Invalid template"):
        template_manager.add_template(invalid_template)


def test_delete_template(template_manager, sample_template):
    """Test deleting template."""
    template_manager.add_template(sample_template)
    assert sample_template.id in template_manager.available_templates

    result = template_manager.delete_template(sample_template.id)
    assert result is True
    assert sample_template.id not in template_manager.available_templates


def test_delete_nonexistent_template(template_manager):
    """Test deleting non-existent template."""
    result = template_manager.delete_template("nonexistent")
    assert result is False


# ========== Template Preview Tests ==========

def test_get_template_preview(template_manager, sample_template):
    """Test generating template preview."""
    template_manager.add_template(sample_template)
    preview = template_manager.get_template_preview(sample_template.id)

    assert sample_template.name in preview
    assert sample_template.description in preview
    assert "README.md" in preview
    assert "src/main.py" in preview


def test_get_preview_nonexistent(template_manager):
    """Test preview of non-existent template fails."""
    with pytest.raises(ValueError, match="not found"):
        template_manager.get_template_preview("nonexistent")


# ========== Utility Tests ==========

def test_get_categories():
    """Test getting list of categories."""
    manager = TemplateManager()
    categories = manager.get_categories()
    assert isinstance(categories, list)
    assert len(categories) > 0


def test_reload_templates(template_manager):
    """Test reloading templates."""
    initial_count = len(template_manager.available_templates)
    template_manager.reload_templates()
    # Count should be the same after reload
    assert len(template_manager.available_templates) == initial_count


# ========== Built-in Templates Tests ==========

def test_fastapi_template_exists():
    """Test FastAPI template is available."""
    manager = TemplateManager()
    templates = manager.list_templates()
    fastapi = [t for t in templates if t.id == "fastapi-api"]
    assert len(fastapi) == 1
    assert fastapi[0].category == "api"


def test_cli_template_exists():
    """Test CLI template is available."""
    manager = TemplateManager()
    templates = manager.list_templates()
    cli = [t for t in templates if t.id == "cli-tool"]
    assert len(cli) == 1
    assert cli[0].category == "cli"


def test_data_science_template_exists():
    """Test data science template is available."""
    manager = TemplateManager()
    templates = manager.list_templates()
    ds = [t for t in templates if t.id == "data-science"]
    assert len(ds) == 1
    assert ds[0].category == "data_science"


def test_flask_template_exists():
    """Test Flask template is available."""
    manager = TemplateManager()
    templates = manager.list_templates()
    flask = [t for t in templates if t.id == "flask-web"]
    assert len(flask) == 1
    assert flask[0].category == "web"


def test_general_template_exists():
    """Test general Python template is available."""
    manager = TemplateManager()
    templates = manager.list_templates()
    general = [t for t in templates if t.id == "python-general"]
    assert len(general) == 1
    assert general[0].category == "general"


# ========== Integration Tests ==========

def test_full_workflow(temp_output_dir):
    """Test complete workflow: load, create, verify."""
    manager = TemplateManager()

    # List templates
    templates = manager.list_templates()
    assert len(templates) >= 5  # Our 5 built-in templates

    # Get a template
    template = manager.get_template("python-general")
    assert template is not None

    # Create project
    project_path = manager.create_project(
        template_id="python-general",
        project_name="test-project",
        output_dir=temp_output_dir,
        variables={
            "author": "Test Author",
            "description": "Test project"
        }
    )

    # Verify structure
    project_dir = Path(project_path)
    assert (project_dir / "README.md").exists()
    assert (project_dir / "requirements.txt").exists()
    assert (project_dir / "setup.py").exists()

    # Verify variable substitution
    readme = (project_dir / "README.md").read_text()
    assert "test-project" in readme
    assert "Test Author" in readme
    assert "Test project" in readme


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
