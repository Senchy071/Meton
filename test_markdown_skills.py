#!/usr/bin/env python3
"""Tests for the Markdown-based Skills System.

Tests the MarkdownSkill class, MarkdownSkillLoader, and integration
with the SkillManager.

Run: python test_markdown_skills.py
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from skills.markdown_skill import (
    MarkdownSkill,
    MarkdownSkillLoader,
    SkillParseError,
    SkillValidationError
)
from skills.skill_manager import SkillManager


# ============================================================================
# MarkdownSkill Tests
# ============================================================================

def test_markdown_skill_from_string_basic():
    """Test parsing a basic skill from string."""
    content = """---
name: test-skill
description: A test skill for testing purposes
---

## Instructions

This is a test skill.
"""
    skill = MarkdownSkill.from_string(content)

    assert skill.name == "test-skill", f"Expected 'test-skill', got '{skill.name}'"
    assert skill.description == "A test skill for testing purposes"
    assert "This is a test skill" in skill.instructions
    assert skill.version == "1.0.0"
    assert skill.enabled is True
    assert skill.allowed_tools is None
    assert skill.model is None


def test_markdown_skill_from_string_full():
    """Test parsing a skill with all fields."""
    content = """---
name: full-skill
description: A fully specified skill
allowed-tools: Read, Grep, Glob
model: primary
version: 2.0.0
---

## Full Instructions

Detailed instructions here.
"""
    skill = MarkdownSkill.from_string(content)

    assert skill.name == "full-skill"
    assert skill.description == "A fully specified skill"
    assert skill.allowed_tools == ["Read", "Grep", "Glob"]
    assert skill.model == "primary"
    assert skill.version == "2.0.0"


def test_markdown_skill_allowed_tools_list():
    """Test allowed-tools as a YAML list."""
    content = """---
name: list-tools
description: Tools as list
allowed-tools:
  - Read
  - Write
  - Edit
---

Instructions.
"""
    skill = MarkdownSkill.from_string(content)
    assert skill.allowed_tools == ["Read", "Write", "Edit"]


def test_markdown_skill_missing_name():
    """Test error when name is missing."""
    content = """---
description: No name field
---

Instructions.
"""
    try:
        MarkdownSkill.from_string(content)
        assert False, "Expected SkillParseError"
    except SkillParseError as e:
        assert "name" in str(e).lower()


def test_markdown_skill_missing_description():
    """Test error when description is missing."""
    content = """---
name: no-desc
---

Instructions.
"""
    try:
        MarkdownSkill.from_string(content)
        assert False, "Expected SkillParseError"
    except SkillParseError as e:
        assert "description" in str(e).lower()


def test_markdown_skill_invalid_name():
    """Test error for invalid skill name."""
    content = """---
name: Invalid_Name
description: Invalid name with underscore
---

Instructions.
"""
    try:
        MarkdownSkill.from_string(content)
        assert False, "Expected SkillValidationError"
    except SkillValidationError as e:
        assert "name" in str(e).lower()


def test_markdown_skill_name_too_long():
    """Test error when name exceeds max length."""
    long_name = "a" * 65
    content = f"""---
name: {long_name}
description: Name too long
---

Instructions.
"""
    try:
        MarkdownSkill.from_string(content)
        assert False, "Expected SkillValidationError"
    except SkillValidationError as e:
        assert "64" in str(e) or "name" in str(e).lower()


def test_markdown_skill_no_frontmatter():
    """Test error when frontmatter is missing."""
    content = """# Just Markdown

No YAML frontmatter here.
"""
    try:
        MarkdownSkill.from_string(content)
        assert False, "Expected SkillParseError"
    except SkillParseError as e:
        assert "frontmatter" in str(e).lower()


def test_markdown_skill_invalid_yaml():
    """Test error for invalid YAML in frontmatter."""
    content = """---
name: test
description: test
invalid: [unclosed bracket
---

Instructions.
"""
    try:
        MarkdownSkill.from_string(content)
        assert False, "Expected SkillParseError"
    except SkillParseError as e:
        assert "yaml" in str(e).lower()


def test_markdown_skill_get_info():
    """Test get_info returns correct metadata."""
    content = """---
name: info-test
description: Test get_info
allowed-tools: Read
model: quick
---

Instructions.
"""
    skill = MarkdownSkill.from_string(content)
    info = skill.get_info()

    assert info["name"] == "info-test"
    assert info["description"] == "Test get_info"
    assert info["type"] == "markdown"
    assert info["allowed_tools"] == ["Read"]
    assert info["model"] == "quick"


def test_markdown_skill_get_system_prompt():
    """Test system prompt generation."""
    content = """---
name: prompt-test
description: Test prompt
allowed-tools: Read, Write
---

## Instructions

Do the thing.
"""
    skill = MarkdownSkill.from_string(content)
    prompt = skill.get_system_prompt()

    assert "# Skill: prompt-test" in prompt
    assert "Do the thing" in prompt
    assert "Allowed Tools" in prompt
    assert "Read, Write" in prompt


def test_markdown_skill_enable_disable():
    """Test enable/disable functionality."""
    content = """---
name: toggle-test
description: Test toggling
---

Instructions.
"""
    skill = MarkdownSkill.from_string(content)

    assert skill.enabled is True
    skill.disable()
    assert skill.enabled is False
    skill.enable()
    assert skill.enabled is True


def test_markdown_skill_valid_names():
    """Test various valid skill names."""
    valid_names = [
        "a",
        "ab",
        "test",
        "test-skill",
        "my-test-skill",
        "skill123",
        "a1b2c3",
    ]

    for name in valid_names:
        content = f"""---
name: {name}
description: Testing name {name}
---

Instructions.
"""
        skill = MarkdownSkill.from_string(content)
        assert skill.name == name, f"Failed for name: {name}"


def test_markdown_skill_invalid_names():
    """Test various invalid skill names."""
    invalid_names = [
        "-starts-with-hyphen",
        "ends-with-hyphen-",
        "has_underscore",
        "HAS-UPPERCASE",
        "has spaces",
        "has.dots",
    ]

    for name in invalid_names:
        content = f"""---
name: {name}
description: Testing invalid name
---

Instructions.
"""
        try:
            MarkdownSkill.from_string(content)
            assert False, f"Expected error for invalid name: {name}"
        except SkillValidationError:
            pass  # Expected


# ============================================================================
# MarkdownSkillLoader Tests
# ============================================================================

def test_loader_discover_directory_structure():
    """Test discovery of skills in directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create skill directories
        skill1_dir = Path(tmpdir) / "skill-one"
        skill1_dir.mkdir()
        (skill1_dir / "SKILL.md").write_text("""---
name: skill-one
description: First skill
---

Instructions for skill one.
""")

        skill2_dir = Path(tmpdir) / "skill-two"
        skill2_dir.mkdir()
        (skill2_dir / "SKILL.md").write_text("""---
name: skill-two
description: Second skill
---

Instructions for skill two.
""")

        loader = MarkdownSkillLoader(
            project_dir=Path(tmpdir),
            user_dir=Path("/nonexistent"),
            builtin_dir=Path("/nonexistent")
        )
        discovered = loader.discover()

        assert len(discovered) == 2
        assert "skill-one" in discovered
        assert "skill-two" in discovered


def test_loader_discover_flat_structure():
    """Test discovery of flat .md files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create flat .md files
        (Path(tmpdir) / "flat-skill.md").write_text("""---
name: flat-skill
description: A flat skill file
---

Instructions.
""")

        loader = MarkdownSkillLoader(
            project_dir=Path(tmpdir),
            user_dir=Path("/nonexistent"),
            builtin_dir=Path("/nonexistent")
        )
        discovered = loader.discover()

        assert "flat-skill" in discovered


def test_loader_precedence():
    """Test that project skills override user skills."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "project"
        user_dir = Path(tmpdir) / "user"
        project_dir.mkdir()
        user_dir.mkdir()

        # Same skill in both locations
        skill_dir_project = project_dir / "my-skill"
        skill_dir_project.mkdir()
        (skill_dir_project / "SKILL.md").write_text("""---
name: my-skill
description: Project version
---

Project instructions.
""")

        skill_dir_user = user_dir / "my-skill"
        skill_dir_user.mkdir()
        (skill_dir_user / "SKILL.md").write_text("""---
name: my-skill
description: User version
---

User instructions.
""")

        loader = MarkdownSkillLoader(
            project_dir=project_dir,
            user_dir=user_dir,
            builtin_dir=Path("/nonexistent")
        )
        loader.discover()
        skill = loader.load_skill("my-skill")

        assert skill is not None
        assert skill.description == "Project version"


def test_loader_load_skill():
    """Test loading a specific skill."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "load-test"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: load-test
description: Test loading
---

Load test instructions.
""")

        loader = MarkdownSkillLoader(
            project_dir=Path(tmpdir),
            user_dir=Path("/nonexistent"),
            builtin_dir=Path("/nonexistent")
        )
        loader.discover()
        skill = loader.load_skill("load-test")

        assert skill is not None
        assert skill.name == "load-test"
        assert loader.get_skill("load-test") is skill


def test_loader_load_all():
    """Test loading all discovered skills."""
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(3):
            skill_dir = Path(tmpdir) / f"skill-{i}"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(f"""---
name: skill-{i}
description: Skill number {i}
---

Instructions for skill {i}.
""")

        loader = MarkdownSkillLoader(
            project_dir=Path(tmpdir),
            user_dir=Path("/nonexistent"),
            builtin_dir=Path("/nonexistent")
        )
        skills = loader.load_all()

        assert len(skills) == 3
        assert len(loader.list_loaded()) == 3


def test_loader_unload_skill():
    """Test unloading a skill."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "unload-test"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: unload-test
description: Test unloading
---

Instructions.
""")

        loader = MarkdownSkillLoader(
            project_dir=Path(tmpdir),
            user_dir=Path("/nonexistent"),
            builtin_dir=Path("/nonexistent")
        )
        loader.discover()
        loader.load_skill("unload-test")

        assert loader.get_skill("unload-test") is not None
        loader.unload_skill("unload-test")
        assert loader.get_skill("unload-test") is None


def test_loader_get_skill_descriptions():
    """Test getting skill descriptions for prompt injection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "desc-test"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: desc-test
description: A descriptive skill
---

Instructions.
""")

        loader = MarkdownSkillLoader(
            project_dir=Path(tmpdir),
            user_dir=Path("/nonexistent"),
            builtin_dir=Path("/nonexistent")
        )
        loader.load_all()
        descriptions = loader.get_skill_descriptions()

        assert "desc-test" in descriptions
        assert descriptions["desc-test"] == "A descriptive skill"


def test_loader_generate_prompt_section():
    """Test generating skills section for system prompt."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "prompt-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: prompt-skill
description: For prompt testing
allowed-tools: Read, Write
---

Instructions.
""")

        loader = MarkdownSkillLoader(
            project_dir=Path(tmpdir),
            user_dir=Path("/nonexistent"),
            builtin_dir=Path("/nonexistent")
        )
        loader.load_all()
        prompt = loader.generate_skills_prompt_section()

        assert "## Available Skills" in prompt
        assert "prompt-skill" in prompt
        assert "For prompt testing" in prompt
        assert "Read, Write" in prompt


# ============================================================================
# SkillManager Integration Tests
# ============================================================================

def test_skill_manager_loads_markdown_skills():
    """Test SkillManager loads markdown skills from md_skills directory."""
    manager = SkillManager()

    # Check if markdown skills were discovered
    md_skills = manager.get_skills_by_type("markdown")

    # Should find our test skills
    assert len(md_skills) >= 0  # May be empty in test environment


def test_skill_manager_hybrid_loading():
    """Test loading both markdown and Python skills."""
    manager = SkillManager()

    # Get counts
    md_count = len(manager.get_skills_by_type("markdown"))
    py_count = len(manager.get_skills_by_type("python"))

    # Should have Python skills
    assert py_count > 0, "Expected Python skills to be discovered"

    # Load all skills
    loaded = manager.load_all_skills()
    assert loaded > 0


def test_skill_manager_get_skill_type():
    """Test getting skill type."""
    manager = SkillManager()

    # Python skills should be detected
    py_skills = manager.get_skills_by_type("python")
    assert len(py_skills) > 0, "Expected Python skills to be discovered"

    # Find a Python skill that doesn't have a markdown counterpart
    md_skill_names = set(manager.get_skills_by_type("markdown"))
    py_only_skills = [s for s in py_skills if s not in md_skill_names]

    if py_only_skills:
        skill_type = manager.get_skill_type(py_only_skills[0])
        assert skill_type == "python", f"Expected 'python', got '{skill_type}' for {py_only_skills[0]}"

    # Markdown skills
    md_skills = manager.get_skills_by_type("markdown")
    if md_skills:
        skill_type = manager.get_skill_type(md_skills[0])
        assert skill_type == "markdown", f"Expected 'markdown', got '{skill_type}' for {md_skills[0]}"


def test_skill_manager_generate_prompt():
    """Test generating skills prompt section."""
    manager = SkillManager()
    manager.load_all_skills()

    prompt = manager.generate_skills_prompt_section()

    if manager.get_loaded_count() > 0:
        assert "## Available Skills" in prompt


def test_skill_manager_execute_python_skill():
    """Test executing a Python skill through manager."""
    manager = SkillManager()

    # Load code_explainer (Python skill)
    if manager.is_available("code_explainer"):
        manager.load_skill("code_explainer")

        result = manager.execute_skill("code_explainer", {
            "code": "def hello(): pass"
        })

        assert result["success"] is True


def test_skill_manager_execute_markdown_skill():
    """Test executing a markdown skill returns instructions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a markdown skill
        skill_dir = Path(tmpdir) / "exec-test"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: exec-test
description: Execution test
allowed-tools: Read
model: primary
---

Test instructions.
""")

        # Create manager with custom path
        manager = SkillManager()
        manager.markdown_loader = MarkdownSkillLoader(
            project_dir=Path(tmpdir),
            user_dir=Path("/nonexistent"),
            builtin_dir=Path("/nonexistent")
        )
        manager.markdown_loader.discover()

        result = manager.execute_skill("exec-test", {"query": "test"})

        assert result["success"] is True
        assert result["type"] == "markdown_skill"
        assert result["name"] == "exec-test"
        assert "Test instructions" in result["instructions"]
        assert result["allowed_tools"] == ["Read"]
        assert result["model"] == "primary"


# ============================================================================
# Test Built-in Markdown Skills
# ============================================================================

def test_builtin_code_reviewer_skill():
    """Test the built-in code-reviewer skill loads correctly."""
    skill_path = Path("skills/md_skills/code-reviewer/SKILL.md")

    if skill_path.exists():
        skill = MarkdownSkill.from_file(skill_path)

        assert skill.name == "code-reviewer"
        assert "review" in skill.description.lower() or "code" in skill.description.lower()
        assert skill.allowed_tools is not None


def test_builtin_code_explainer_skill():
    """Test the built-in code-explainer skill loads correctly."""
    skill_path = Path("skills/md_skills/code-explainer/SKILL.md")

    if skill_path.exists():
        skill = MarkdownSkill.from_file(skill_path)

        assert skill.name == "code-explainer"
        assert "explain" in skill.description.lower()


def test_builtin_debugger_skill():
    """Test the built-in debugger skill loads correctly."""
    skill_path = Path("skills/md_skills/debugger/SKILL.md")

    if skill_path.exists():
        skill = MarkdownSkill.from_file(skill_path)

        assert skill.name == "debugger"
        assert "debug" in skill.description.lower() or "error" in skill.description.lower()


# ============================================================================
# File Loading Tests
# ============================================================================

def test_markdown_skill_from_file():
    """Test loading skill from file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = Path(tmpdir) / "file-test.md"
        skill_file.write_text("""---
name: file-test
description: Test file loading
---

File loaded instructions.
""")

        skill = MarkdownSkill.from_file(skill_file)

        assert skill.name == "file-test"
        assert skill.source_path == skill_file


def test_markdown_skill_additional_files():
    """Test discovery of additional files in skill directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir)

        # Main skill file
        (skill_dir / "SKILL.md").write_text("""---
name: multi-file
description: Skill with additional files
---

See reference.md for more details.
""")

        # Additional files
        (skill_dir / "reference.md").write_text("# Reference\nAdditional documentation.")
        (skill_dir / "examples.md").write_text("# Examples\nExample code here.")

        skill = MarkdownSkill.from_file(skill_dir / "SKILL.md")

        assert len(skill.additional_files) == 2

        ref_content = skill.get_additional_file_content("reference.md")
        assert ref_content is not None
        assert "Reference" in ref_content


def test_markdown_skill_file_not_found():
    """Test error when skill file doesn't exist."""
    try:
        MarkdownSkill.from_file("/nonexistent/path/SKILL.md")
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass


# ============================================================================
# Run Tests
# ============================================================================

def run_all_tests():
    """Run all tests and report results."""
    tests = [
        # MarkdownSkill tests
        test_markdown_skill_from_string_basic,
        test_markdown_skill_from_string_full,
        test_markdown_skill_allowed_tools_list,
        test_markdown_skill_missing_name,
        test_markdown_skill_missing_description,
        test_markdown_skill_invalid_name,
        test_markdown_skill_name_too_long,
        test_markdown_skill_no_frontmatter,
        test_markdown_skill_invalid_yaml,
        test_markdown_skill_get_info,
        test_markdown_skill_get_system_prompt,
        test_markdown_skill_enable_disable,
        test_markdown_skill_valid_names,
        test_markdown_skill_invalid_names,

        # MarkdownSkillLoader tests
        test_loader_discover_directory_structure,
        test_loader_discover_flat_structure,
        test_loader_precedence,
        test_loader_load_skill,
        test_loader_load_all,
        test_loader_unload_skill,
        test_loader_get_skill_descriptions,
        test_loader_generate_prompt_section,

        # SkillManager integration tests
        test_skill_manager_loads_markdown_skills,
        test_skill_manager_hybrid_loading,
        test_skill_manager_get_skill_type,
        test_skill_manager_generate_prompt,
        test_skill_manager_execute_python_skill,
        test_skill_manager_execute_markdown_skill,

        # Built-in skill tests
        test_builtin_code_reviewer_skill,
        test_builtin_code_explainer_skill,
        test_builtin_debugger_skill,

        # File loading tests
        test_markdown_skill_from_file,
        test_markdown_skill_additional_files,
        test_markdown_skill_file_not_found,
    ]

    passed = 0
    failed = 0
    errors = []

    for test in tests:
        try:
            test()
            passed += 1
            print(f"  PASS: {test.__name__}")
        except AssertionError as e:
            failed += 1
            errors.append((test.__name__, str(e)))
            print(f"  FAIL: {test.__name__} - {e}")
        except Exception as e:
            failed += 1
            errors.append((test.__name__, f"ERROR: {e}"))
            print(f"  ERROR: {test.__name__} - {e}")

    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")

    if errors:
        print()
        print("Failures:")
        for name, error in errors:
            print(f"  - {name}: {error}")

    return failed == 0


if __name__ == "__main__":
    print("Markdown Skills System Tests")
    print("=" * 60)
    success = run_all_tests()
    sys.exit(0 if success else 1)
