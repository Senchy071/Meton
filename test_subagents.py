#!/usr/bin/env python3
"""Tests for the Sub-Agent System.

Tests the SubAgent class, SubAgentLoader, and SubAgentSpawner.

Run: python test_subagents.py
"""

import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.subagent import (
    SubAgent,
    SubAgentLoader,
    SubAgentParseError,
    SubAgentValidationError
)


# ============================================================================
# SubAgent Tests
# ============================================================================

def test_subagent_from_string_basic():
    """Test parsing a basic sub-agent from string."""
    content = """---
name: test-agent
description: A test agent for testing purposes
---

You are a test agent.
"""
    agent = SubAgent.from_string(content)

    assert agent.name == "test-agent", f"Expected 'test-agent', got '{agent.name}'"
    assert agent.description == "A test agent for testing purposes"
    assert "You are a test agent" in agent.system_prompt
    assert agent.version == "1.0.0"
    assert agent.enabled is True
    assert agent.tools is None  # Inherit all
    assert agent.model == "inherit"


def test_subagent_from_string_full():
    """Test parsing an agent with all fields."""
    content = """---
name: full-agent
description: A fully specified agent
tools: Read, Grep, Glob
model: primary
version: 2.0.0
---

Full instructions here.
"""
    agent = SubAgent.from_string(content)

    assert agent.name == "full-agent"
    assert agent.description == "A fully specified agent"
    assert agent.tools == ["Read", "Grep", "Glob"]
    assert agent.model == "primary"
    assert agent.version == "2.0.0"


def test_subagent_tools_list():
    """Test tools as a YAML list."""
    content = """---
name: list-tools
description: Tools as list
tools:
  - Read
  - Write
  - Edit
---

Instructions.
"""
    agent = SubAgent.from_string(content)
    assert agent.tools == ["Read", "Write", "Edit"]


def test_subagent_missing_name():
    """Test error when name is missing."""
    content = """---
description: No name field
---

Instructions.
"""
    try:
        SubAgent.from_string(content)
        assert False, "Expected SubAgentParseError"
    except SubAgentParseError as e:
        assert "name" in str(e).lower()


def test_subagent_missing_description():
    """Test error when description is missing."""
    content = """---
name: no-desc
---

Instructions.
"""
    try:
        SubAgent.from_string(content)
        assert False, "Expected SubAgentParseError"
    except SubAgentParseError as e:
        assert "description" in str(e).lower()


def test_subagent_invalid_name():
    """Test error for invalid agent name."""
    content = """---
name: Invalid_Name
description: Invalid name with underscore
---

Instructions.
"""
    try:
        SubAgent.from_string(content)
        assert False, "Expected SubAgentValidationError"
    except SubAgentValidationError as e:
        assert "name" in str(e).lower()


def test_subagent_name_too_long():
    """Test error when name exceeds max length."""
    long_name = "a" * 65
    content = f"""---
name: {long_name}
description: Name too long
---

Instructions.
"""
    try:
        SubAgent.from_string(content)
        assert False, "Expected SubAgentValidationError"
    except SubAgentValidationError as e:
        assert "64" in str(e) or "name" in str(e).lower()


def test_subagent_no_frontmatter():
    """Test error when frontmatter is missing."""
    content = """# Just Markdown

No YAML frontmatter here.
"""
    try:
        SubAgent.from_string(content)
        assert False, "Expected SubAgentParseError"
    except SubAgentParseError as e:
        assert "frontmatter" in str(e).lower()


def test_subagent_invalid_yaml():
    """Test error for invalid YAML in frontmatter."""
    content = """---
name: test
description: test
invalid: [unclosed bracket
---

Instructions.
"""
    try:
        SubAgent.from_string(content)
        assert False, "Expected SubAgentParseError"
    except SubAgentParseError as e:
        assert "yaml" in str(e).lower()


def test_subagent_get_info():
    """Test get_info returns correct metadata."""
    content = """---
name: info-test
description: Test get_info
tools: Read
model: quick
---

Instructions.
"""
    agent = SubAgent.from_string(content)
    info = agent.get_info()

    assert info["name"] == "info-test"
    assert info["description"] == "Test get_info"
    assert info["tools"] == ["Read"]
    assert info["model"] == "quick"


def test_subagent_enable_disable():
    """Test enable/disable functionality."""
    content = """---
name: toggle-test
description: Test toggling
---

Instructions.
"""
    agent = SubAgent.from_string(content)

    assert agent.enabled is True
    agent.disable()
    assert agent.enabled is False
    agent.enable()
    assert agent.enabled is True


def test_subagent_valid_names():
    """Test various valid agent names."""
    valid_names = [
        "a",
        "ab",
        "test",
        "test-agent",
        "my-test-agent",
        "agent123",
        "a1b2c3",
    ]

    for name in valid_names:
        content = f"""---
name: {name}
description: Testing name {name}
---

Instructions.
"""
        agent = SubAgent.from_string(content)
        assert agent.name == name, f"Failed for name: {name}"


def test_subagent_invalid_names():
    """Test various invalid agent names."""
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
            SubAgent.from_string(content)
            assert False, f"Expected error for invalid name: {name}"
        except SubAgentValidationError:
            pass  # Expected


def test_subagent_valid_models():
    """Test valid model values."""
    valid_models = ["primary", "fallback", "quick", "inherit"]

    for model in valid_models:
        content = f"""---
name: model-test
description: Test model {model}
model: {model}
---

Instructions.
"""
        agent = SubAgent.from_string(content)
        assert agent.model == model


def test_subagent_invalid_model():
    """Test error for invalid model value."""
    content = """---
name: bad-model
description: Invalid model
model: invalid-model
---

Instructions.
"""
    try:
        SubAgent.from_string(content)
        assert False, "Expected SubAgentValidationError"
    except SubAgentValidationError as e:
        assert "model" in str(e).lower()


def test_subagent_get_effective_tools():
    """Test get_effective_tools filtering."""
    content = """---
name: tools-test
description: Test tools
tools: Read, Write, NonExistent
---

Instructions.
"""
    agent = SubAgent.from_string(content)

    available = ["Read", "Write", "Edit", "Glob"]
    effective = agent.get_effective_tools(available)

    assert "Read" in effective
    assert "Write" in effective
    assert "NonExistent" not in effective
    assert "Edit" not in effective  # Not in agent's allowed tools


def test_subagent_inherit_all_tools():
    """Test that None tools means inherit all."""
    content = """---
name: inherit-test
description: Inherit all tools
---

Instructions.
"""
    agent = SubAgent.from_string(content)

    available = ["Read", "Write", "Edit"]
    effective = agent.get_effective_tools(available)

    assert effective == available


# ============================================================================
# SubAgentLoader Tests
# ============================================================================

def test_loader_discover():
    """Test discovery of agents in directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create agent files
        (Path(tmpdir) / "agent-one.md").write_text("""---
name: agent-one
description: First agent
---

Instructions.
""")

        (Path(tmpdir) / "agent-two.md").write_text("""---
name: agent-two
description: Second agent
---

Instructions.
""")

        loader = SubAgentLoader(
            project_dir=Path(tmpdir),
            user_dir=Path("/nonexistent"),
            builtin_dir=Path("/nonexistent")
        )
        discovered = loader.discover()

        assert len(discovered) == 2
        assert "agent-one" in discovered
        assert "agent-two" in discovered


def test_loader_precedence():
    """Test that project agents override user agents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "project"
        user_dir = Path(tmpdir) / "user"
        project_dir.mkdir()
        user_dir.mkdir()

        # Same agent in both locations
        (project_dir / "my-agent.md").write_text("""---
name: my-agent
description: Project version
---

Project instructions.
""")

        (user_dir / "my-agent.md").write_text("""---
name: my-agent
description: User version
---

User instructions.
""")

        loader = SubAgentLoader(
            project_dir=project_dir,
            user_dir=user_dir,
            builtin_dir=Path("/nonexistent")
        )
        loader.discover()
        agent = loader.load_agent("my-agent")

        assert agent is not None
        assert agent.description == "Project version"


def test_loader_load_agent():
    """Test loading a specific agent."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "load-test.md").write_text("""---
name: load-test
description: Test loading
---

Instructions.
""")

        loader = SubAgentLoader(
            project_dir=Path(tmpdir),
            user_dir=Path("/nonexistent"),
            builtin_dir=Path("/nonexistent")
        )
        loader.discover()
        agent = loader.load_agent("load-test")

        assert agent is not None
        assert agent.name == "load-test"
        assert loader.get_agent("load-test") is agent


def test_loader_load_all():
    """Test loading all discovered agents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(3):
            (Path(tmpdir) / f"agent-{i}.md").write_text(f"""---
name: agent-{i}
description: Agent number {i}
---

Instructions.
""")

        loader = SubAgentLoader(
            project_dir=Path(tmpdir),
            user_dir=Path("/nonexistent"),
            builtin_dir=Path("/nonexistent")
        )
        agents = loader.load_all()

        assert len(agents) == 3
        assert len(loader.list_loaded()) == 3


def test_loader_unload_agent():
    """Test unloading an agent."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "unload-test.md").write_text("""---
name: unload-test
description: Test unloading
---

Instructions.
""")

        loader = SubAgentLoader(
            project_dir=Path(tmpdir),
            user_dir=Path("/nonexistent"),
            builtin_dir=Path("/nonexistent")
        )
        loader.discover()
        loader.load_agent("unload-test")

        assert loader.get_agent("unload-test") is not None
        loader.unload_agent("unload-test")
        assert loader.get_agent("unload-test") is None


def test_loader_get_descriptions():
    """Test getting agent descriptions for prompt injection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "desc-test.md").write_text("""---
name: desc-test
description: A descriptive agent
---

Instructions.
""")

        loader = SubAgentLoader(
            project_dir=Path(tmpdir),
            user_dir=Path("/nonexistent"),
            builtin_dir=Path("/nonexistent")
        )
        loader.load_all()
        descriptions = loader.get_agent_descriptions()

        assert "desc-test" in descriptions
        assert descriptions["desc-test"] == "A descriptive agent"


def test_loader_generate_prompt_section():
    """Test generating agents section for system prompt."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "prompt-agent.md").write_text("""---
name: prompt-agent
description: For prompt testing
tools: Read, Write
model: primary
---

Instructions.
""")

        loader = SubAgentLoader(
            project_dir=Path(tmpdir),
            user_dir=Path("/nonexistent"),
            builtin_dir=Path("/nonexistent")
        )
        loader.load_all()
        prompt = loader.generate_agents_prompt_section()

        assert "## Available Sub-Agents" in prompt
        assert "prompt-agent" in prompt
        assert "For prompt testing" in prompt
        assert "Read, Write" in prompt


# ============================================================================
# Built-in Agent Tests
# ============================================================================

def test_builtin_explorer_agent():
    """Test the built-in explorer agent loads correctly."""
    agent_path = Path("agents/builtin/explorer.md")

    if agent_path.exists():
        agent = SubAgent.from_file(agent_path)

        assert agent.name == "explorer"
        assert "explor" in agent.description.lower() or "search" in agent.description.lower()
        assert agent.model == "quick"
        assert agent.tools is not None


def test_builtin_planner_agent():
    """Test the built-in planner agent loads correctly."""
    agent_path = Path("agents/builtin/planner.md")

    if agent_path.exists():
        agent = SubAgent.from_file(agent_path)

        assert agent.name == "planner"
        assert "plan" in agent.description.lower()


def test_builtin_code_reviewer_agent():
    """Test the built-in code-reviewer agent loads correctly."""
    agent_path = Path("agents/builtin/code-reviewer.md")

    if agent_path.exists():
        agent = SubAgent.from_file(agent_path)

        assert agent.name == "code-reviewer"
        assert "review" in agent.description.lower()


def test_builtin_debugger_agent():
    """Test the built-in debugger agent loads correctly."""
    agent_path = Path("agents/builtin/debugger.md")

    if agent_path.exists():
        agent = SubAgent.from_file(agent_path)

        assert agent.name == "debugger"
        assert "debug" in agent.description.lower() or "error" in agent.description.lower()


# ============================================================================
# File Loading Tests
# ============================================================================

def test_subagent_from_file():
    """Test loading agent from file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        agent_file = Path(tmpdir) / "file-test.md"
        agent_file.write_text("""---
name: file-test
description: Test file loading
---

File loaded instructions.
""")

        agent = SubAgent.from_file(agent_file)

        assert agent.name == "file-test"
        assert agent.source_path == agent_file


def test_subagent_file_not_found():
    """Test error when agent file doesn't exist."""
    try:
        SubAgent.from_file("/nonexistent/path/agent.md")
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass


# ============================================================================
# SubAgentResult Tests
# ============================================================================

def test_subagent_result():
    """Test SubAgentResult creation and conversion."""
    from agents.subagent_spawner import SubAgentResult

    result = SubAgentResult(
        agent_id="abc123",
        agent_name="test-agent",
        task="Do something",
        output="Done!",
        success=True,
        iterations=3,
        duration_seconds=1.5,
        model_used="primary"
    )

    assert result.agent_id == "abc123"
    assert result.agent_name == "test-agent"
    assert result.success is True
    assert result.iterations == 3

    # Test to_dict
    d = result.to_dict()
    assert d["agent_id"] == "abc123"
    assert d["success"] is True
    assert "timestamp" in d


def test_subagent_result_failure():
    """Test SubAgentResult with failure."""
    from agents.subagent_spawner import SubAgentResult

    result = SubAgentResult(
        agent_id="def456",
        agent_name="failed-agent",
        task="Do something",
        success=False,
        error="Something went wrong"
    )

    assert result.success is False
    assert result.error == "Something went wrong"


# ============================================================================
# Run Tests
# ============================================================================

def run_all_tests():
    """Run all tests and report results."""
    tests = [
        # SubAgent tests
        test_subagent_from_string_basic,
        test_subagent_from_string_full,
        test_subagent_tools_list,
        test_subagent_missing_name,
        test_subagent_missing_description,
        test_subagent_invalid_name,
        test_subagent_name_too_long,
        test_subagent_no_frontmatter,
        test_subagent_invalid_yaml,
        test_subagent_get_info,
        test_subagent_enable_disable,
        test_subagent_valid_names,
        test_subagent_invalid_names,
        test_subagent_valid_models,
        test_subagent_invalid_model,
        test_subagent_get_effective_tools,
        test_subagent_inherit_all_tools,

        # SubAgentLoader tests
        test_loader_discover,
        test_loader_precedence,
        test_loader_load_agent,
        test_loader_load_all,
        test_loader_unload_agent,
        test_loader_get_descriptions,
        test_loader_generate_prompt_section,

        # Built-in agent tests
        test_builtin_explorer_agent,
        test_builtin_planner_agent,
        test_builtin_code_reviewer_agent,
        test_builtin_debugger_agent,

        # File loading tests
        test_subagent_from_file,
        test_subagent_file_not_found,

        # SubAgentResult tests
        test_subagent_result,
        test_subagent_result_failure,
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
    print("Sub-Agent System Tests")
    print("=" * 60)
    success = run_all_tests()
    sys.exit(0 if success else 1)
