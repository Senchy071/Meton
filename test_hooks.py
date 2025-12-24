#!/usr/bin/env python3
"""Tests for Phase 4: Hooks System.

This module tests the hooks system including:
- Hook base classes and types
- HookManager registration and execution
- HookLoader discovery and loading
- Tool and agent integration
"""

import sys
import json
import tempfile
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from hooks.base import Hook, HookType, HookContext, HookResult
from hooks.hook_manager import HookManager, create_logging_hook
from hooks.hook_loader import HookLoader

# Track test results
passed = 0
failed = 0


def test(name):
    """Decorator to track test results."""
    def decorator(func):
        def wrapper():
            global passed, failed
            try:
                func()
                print(f"  PASS: {name}")
                passed += 1
            except AssertionError as e:
                print(f"  FAIL: {name}")
                print(f"        {str(e)}")
                failed += 1
            except Exception as e:
                print(f"  ERROR: {name}")
                print(f"         {type(e).__name__}: {str(e)}")
                failed += 1
        return wrapper
    return decorator


# =============================================================================
# HookType Tests
# =============================================================================

print("\n" + "=" * 60)
print("HookType Tests")
print("=" * 60)


@test("hook_type_enum_values")
def test_hook_type_enum_values():
    """Test HookType enum has expected values."""
    assert HookType.PRE_QUERY.value == "pre_query"
    assert HookType.POST_QUERY.value == "post_query"
    assert HookType.PRE_TOOL.value == "pre_tool"
    assert HookType.POST_TOOL.value == "post_tool"
    assert HookType.PRE_SKILL.value == "pre_skill"
    assert HookType.POST_SKILL.value == "post_skill"
    assert HookType.PRE_AGENT.value == "pre_agent"
    assert HookType.POST_AGENT.value == "post_agent"


@test("hook_type_from_string")
def test_hook_type_from_string():
    """Test creating HookType from string."""
    assert HookType("pre_tool") == HookType.PRE_TOOL
    assert HookType("post_query") == HookType.POST_QUERY


test_hook_type_enum_values()
test_hook_type_from_string()


# =============================================================================
# HookContext Tests
# =============================================================================

print("\n" + "=" * 60)
print("HookContext Tests")
print("=" * 60)


@test("hook_context_creation")
def test_hook_context_creation():
    """Test creating a HookContext."""
    context = HookContext(
        hook_type=HookType.POST_TOOL,
        name="file_operations",
        input_data='{"action": "read"}',
        output_data="file contents",
        success=True,
        duration_seconds=0.5,
    )

    assert context.hook_type == HookType.POST_TOOL
    assert context.name == "file_operations"
    assert context.success == True
    assert context.duration_seconds == 0.5


@test("hook_context_to_dict")
def test_hook_context_to_dict():
    """Test converting HookContext to dictionary."""
    context = HookContext(
        hook_type=HookType.POST_TOOL,
        name="test_tool",
        success=True,
    )

    d = context.to_dict()
    assert d["hook_type"] == "post_tool"
    assert d["name"] == "test_tool"
    assert d["success"] == True


@test("hook_context_format_template")
def test_hook_context_format_template():
    """Test template formatting with context values."""
    context = HookContext(
        hook_type=HookType.POST_TOOL,
        name="my_tool",
        success=True,
        duration_seconds=1.5,
    )

    template = "Tool {name} completed: {success} in {duration}s"
    result = context.format_template(template)

    assert "my_tool" in result
    assert "True" in result
    assert "1.5" in result


test_hook_context_creation()
test_hook_context_to_dict()
test_hook_context_format_template()


# =============================================================================
# Hook Tests
# =============================================================================

print("\n" + "=" * 60)
print("Hook Tests")
print("=" * 60)


@test("hook_creation_with_command")
def test_hook_creation_with_command():
    """Test creating a Hook with a shell command."""
    hook = Hook(
        name="test-hook",
        hook_type=HookType.POST_TOOL,
        command="echo 'hello'",
        description="Test hook",
    )

    assert hook.name == "test-hook"
    assert hook.hook_type == HookType.POST_TOOL
    assert hook.command == "echo 'hello'"
    assert hook.enabled == True


@test("hook_creation_with_function")
def test_hook_creation_with_function():
    """Test creating a Hook with a Python function."""
    def my_hook(context: HookContext) -> HookResult:
        return HookResult(success=True)

    hook = Hook(
        name="func-hook",
        hook_type=HookType.PRE_QUERY,
        func=my_hook,
    )

    assert hook.name == "func-hook"
    assert hook.func is not None
    assert hook.command is None


@test("hook_validation_requires_command_or_func")
def test_hook_validation_requires_command_or_func():
    """Test that Hook requires either command or func."""
    try:
        hook = Hook(
            name="invalid",
            hook_type=HookType.POST_TOOL,
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "must have either" in str(e)


@test("hook_validation_not_both_command_and_func")
def test_hook_validation_not_both_command_and_func():
    """Test that Hook cannot have both command and func."""
    def my_func(ctx):
        return HookResult()

    try:
        hook = Hook(
            name="invalid",
            hook_type=HookType.POST_TOOL,
            command="echo hello",
            func=my_func,
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "cannot have both" in str(e)


@test("hook_matches_target")
def test_hook_matches_target():
    """Test target matching for hooks."""
    hook = Hook(
        name="filtered",
        hook_type=HookType.POST_TOOL,
        command="echo",
        target_names=["file_operations", "code_executor"],
    )

    assert hook.matches_target("file_operations") == True
    assert hook.matches_target("code_executor") == True
    assert hook.matches_target("web_search") == False


@test("hook_matches_all_when_no_filter")
def test_hook_matches_all_when_no_filter():
    """Test that hook matches all targets when no filter set."""
    hook = Hook(
        name="unfiltered",
        hook_type=HookType.POST_TOOL,
        command="echo",
    )

    assert hook.matches_target("any_tool") == True
    assert hook.matches_target("another_tool") == True


@test("hook_evaluate_condition_equals")
def test_hook_evaluate_condition_equals():
    """Test condition evaluation with equals."""
    hook = Hook(
        name="conditional",
        hook_type=HookType.POST_TOOL,
        command="echo",
        condition="{success} == true",
    )

    context_success = HookContext(hook_type=HookType.POST_TOOL, success=True)
    context_fail = HookContext(hook_type=HookType.POST_TOOL, success=False)

    assert hook.evaluate_condition(context_success) == True
    assert hook.evaluate_condition(context_fail) == False


@test("hook_evaluate_condition_not_equals")
def test_hook_evaluate_condition_not_equals():
    """Test condition evaluation with not equals."""
    hook = Hook(
        name="conditional",
        hook_type=HookType.POST_TOOL,
        command="echo",
        condition="{success} != true",
    )

    context_fail = HookContext(hook_type=HookType.POST_TOOL, success=False)
    assert hook.evaluate_condition(context_fail) == True


@test("hook_to_dict_and_from_dict")
def test_hook_to_dict_and_from_dict():
    """Test serialization and deserialization of Hook."""
    original = Hook(
        name="serialize-test",
        hook_type=HookType.POST_QUERY,
        command="echo done",
        condition="{success} == true",
        timeout=10.0,
        enabled=True,
        description="Test serialization",
    )

    d = original.to_dict()
    restored = Hook.from_dict(d)

    assert restored.name == original.name
    assert restored.hook_type == original.hook_type
    assert restored.command == original.command
    assert restored.timeout == original.timeout


test_hook_creation_with_command()
test_hook_creation_with_function()
test_hook_validation_requires_command_or_func()
test_hook_validation_not_both_command_and_func()
test_hook_matches_target()
test_hook_matches_all_when_no_filter()
test_hook_evaluate_condition_equals()
test_hook_evaluate_condition_not_equals()
test_hook_to_dict_and_from_dict()


# =============================================================================
# HookManager Tests
# =============================================================================

print("\n" + "=" * 60)
print("HookManager Tests")
print("=" * 60)


@test("hook_manager_creation")
def test_hook_manager_creation():
    """Test creating a HookManager."""
    manager = HookManager()
    assert manager.enabled == True
    assert len(manager.list_hooks()) == 0


@test("hook_manager_register")
def test_hook_manager_register():
    """Test registering hooks."""
    manager = HookManager()
    hook = Hook(
        name="test",
        hook_type=HookType.POST_TOOL,
        command="echo",
    )

    result = manager.register(hook)
    assert result == True
    assert len(manager.list_hooks()) == 1


@test("hook_manager_unregister")
def test_hook_manager_unregister():
    """Test unregistering hooks."""
    manager = HookManager()
    hook = Hook(name="test", hook_type=HookType.POST_TOOL, command="echo")
    manager.register(hook)

    result = manager.unregister("test")
    assert result == True
    assert len(manager.list_hooks()) == 0


@test("hook_manager_get_hook")
def test_hook_manager_get_hook():
    """Test getting a hook by name."""
    manager = HookManager()
    hook = Hook(name="findme", hook_type=HookType.POST_TOOL, command="echo")
    manager.register(hook)

    found = manager.get_hook("findme")
    assert found is not None
    assert found.name == "findme"

    not_found = manager.get_hook("nonexistent")
    assert not_found is None


@test("hook_manager_list_by_type")
def test_hook_manager_list_by_type():
    """Test listing hooks by type."""
    manager = HookManager()
    manager.register(Hook(name="h1", hook_type=HookType.POST_TOOL, command="echo"))
    manager.register(Hook(name="h2", hook_type=HookType.POST_TOOL, command="echo"))
    manager.register(Hook(name="h3", hook_type=HookType.PRE_QUERY, command="echo"))

    post_tool = manager.list_hooks(HookType.POST_TOOL)
    assert len(post_tool) == 2

    pre_query = manager.list_hooks(HookType.PRE_QUERY)
    assert len(pre_query) == 1


@test("hook_manager_execute_shell_hook")
def test_hook_manager_execute_shell_hook():
    """Test executing a shell command hook."""
    manager = HookManager()
    hook = Hook(
        name="echo-test",
        hook_type=HookType.POST_TOOL,
        command="echo 'success'",
    )
    manager.register(hook)

    context = HookContext(
        hook_type=HookType.POST_TOOL,
        name="test_tool",
        success=True,
    )

    results = manager.execute(context, "test_tool")
    assert len(results) == 1
    assert results[0].success == True
    assert "success" in results[0].output


@test("hook_manager_execute_function_hook")
def test_hook_manager_execute_function_hook():
    """Test executing a Python function hook."""
    call_count = [0]

    def my_hook(context: HookContext) -> HookResult:
        call_count[0] += 1
        return HookResult(success=True, output="function called")

    manager = HookManager()
    hook = Hook(
        name="func-test",
        hook_type=HookType.POST_TOOL,
        func=my_hook,
    )
    manager.register(hook)

    context = HookContext(hook_type=HookType.POST_TOOL)
    results = manager.execute(context)

    assert call_count[0] == 1
    assert results[0].success == True


@test("hook_manager_respects_enabled_flag")
def test_hook_manager_respects_enabled_flag():
    """Test that disabled hooks are not executed."""
    manager = HookManager()
    hook = Hook(
        name="disabled",
        hook_type=HookType.POST_TOOL,
        command="echo 'should not run'",
        enabled=False,
    )
    manager.register(hook)

    context = HookContext(hook_type=HookType.POST_TOOL)
    results = manager.execute(context)

    assert len(results) == 0


@test("hook_manager_global_disable")
def test_hook_manager_global_disable():
    """Test globally disabling hooks."""
    manager = HookManager()
    hook = Hook(name="test", hook_type=HookType.POST_TOOL, command="echo")
    manager.register(hook)

    manager.disable_all()
    context = HookContext(hook_type=HookType.POST_TOOL)
    results = manager.execute(context)

    assert len(results) == 0


@test("hook_manager_stats")
def test_hook_manager_stats():
    """Test getting hook statistics."""
    manager = HookManager()
    manager.register(Hook(name="h1", hook_type=HookType.POST_TOOL, command="echo", enabled=True))
    manager.register(Hook(name="h2", hook_type=HookType.POST_TOOL, command="echo", enabled=False))

    stats = manager.get_stats()
    assert stats["total_hooks"] == 2
    assert stats["enabled_hooks"] == 1
    assert stats["disabled_hooks"] == 1


@test("hook_manager_history")
def test_hook_manager_history():
    """Test hook execution history."""
    manager = HookManager()
    hook = Hook(name="tracked", hook_type=HookType.POST_TOOL, command="echo test")
    manager.register(hook)

    context = HookContext(hook_type=HookType.POST_TOOL, name="tool1")
    manager.execute(context, "tool1")

    history = manager.get_history()
    assert len(history) == 1
    assert history[0]["hook_name"] == "tracked"


@test("hook_manager_enable_disable_hook")
def test_hook_manager_enable_disable_hook():
    """Test enabling and disabling individual hooks."""
    manager = HookManager()
    hook = Hook(name="toggle", hook_type=HookType.POST_TOOL, command="echo")
    manager.register(hook)

    manager.disable_hook("toggle")
    assert manager.get_hook("toggle").enabled == False

    manager.enable_hook("toggle")
    assert manager.get_hook("toggle").enabled == True


test_hook_manager_creation()
test_hook_manager_register()
test_hook_manager_unregister()
test_hook_manager_get_hook()
test_hook_manager_list_by_type()
test_hook_manager_execute_shell_hook()
test_hook_manager_execute_function_hook()
test_hook_manager_respects_enabled_flag()
test_hook_manager_global_disable()
test_hook_manager_stats()
test_hook_manager_history()
test_hook_manager_enable_disable_hook()


# =============================================================================
# HookLoader Tests
# =============================================================================

print("\n" + "=" * 60)
print("HookLoader Tests")
print("=" * 60)


@test("hook_loader_creation")
def test_hook_loader_creation():
    """Test creating a HookLoader."""
    loader = HookLoader()
    assert loader.base_dir.exists()


@test("hook_loader_parse_frontmatter")
def test_hook_loader_parse_frontmatter():
    """Test parsing YAML frontmatter."""
    loader = HookLoader()

    content = """---
name: test-hook
hook_type: post_tool
command: echo hello
---

# Test Hook

This is a test hook.
"""

    frontmatter, body = loader._parse_frontmatter(content)
    assert frontmatter["name"] == "test-hook"
    assert frontmatter["hook_type"] == "post_tool"
    assert "Test Hook" in body


@test("hook_loader_load_from_markdown")
def test_hook_loader_load_from_markdown():
    """Test loading a hook from markdown file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        hook_dir = Path(tmpdir) / "test-hook"
        hook_dir.mkdir()
        hook_file = hook_dir / "HOOK.md"
        hook_file.write_text("""---
name: markdown-test
hook_type: post_tool
command: echo 'from markdown'
description: A test hook from markdown
---

# Markdown Test Hook
""")

        loader = HookLoader(builtin_hooks_dir=Path(tmpdir))
        hook = loader.load_from_markdown(hook_file, "test")

        assert hook is not None
        assert hook.name == "markdown-test"
        assert hook.hook_type == HookType.POST_TOOL


@test("hook_loader_load_from_config")
def test_hook_loader_load_from_config():
    """Test loading hooks from config dictionary."""
    loader = HookLoader()
    config = {
        "hooks": {
            "enabled": True,
            "items": [
                {
                    "name": "config-hook",
                    "hook_type": "pre_query",
                    "command": "echo 'from config'",
                    "description": "A hook from config",
                }
            ]
        }
    }

    hooks = loader.load_from_config(config)
    assert len(hooks) == 1
    assert hooks[0].name == "config-hook"
    assert hooks[0].source == "config"


@test("hook_loader_discover")
def test_hook_loader_discover():
    """Test discovering hooks in directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a hook directory
        hook_dir = Path(tmpdir) / "my-hook"
        hook_dir.mkdir()
        (hook_dir / "HOOK.md").write_text("""---
name: discovered
hook_type: post_tool
command: echo
---
""")

        loader = HookLoader(
            builtin_hooks_dir=Path(tmpdir),
            user_hooks_dir=Path("/nonexistent"),
            project_hooks_dir=Path("/nonexistent"),
        )

        discovered = loader.discover()
        assert "my-hook" in discovered["builtin"]


@test("hook_loader_load_all")
def test_hook_loader_load_all():
    """Test loading all hooks from all sources."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a hook directory
        hook_dir = Path(tmpdir) / "test-hook"
        hook_dir.mkdir()
        (hook_dir / "HOOK.md").write_text("""---
name: loaded-hook
hook_type: post_tool
command: echo loaded
---
""")

        loader = HookLoader(
            builtin_hooks_dir=Path(tmpdir),
            user_hooks_dir=Path("/nonexistent"),
            project_hooks_dir=Path("/nonexistent"),
        )

        hooks = loader.load_all()
        assert len(hooks) == 1
        assert hooks[0].name == "loaded-hook"


@test("hook_loader_create_hook_directory")
def test_hook_loader_create_hook_directory():
    """Test creating a new hook directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = HookLoader(project_hooks_dir=Path(tmpdir))

        hook_file = loader.create_hook_directory(
            name="new-hook",
            hook_type=HookType.POST_TOOL,
            command="echo 'new'",
            description="A newly created hook",
        )

        assert hook_file.exists()
        content = hook_file.read_text()
        assert "new-hook" in content
        assert "post_tool" in content


test_hook_loader_creation()
test_hook_loader_parse_frontmatter()
test_hook_loader_load_from_markdown()
test_hook_loader_load_from_config()
test_hook_loader_discover()
test_hook_loader_load_all()
test_hook_loader_create_hook_directory()


# =============================================================================
# Integration Tests
# =============================================================================

print("\n" + "=" * 60)
print("Integration Tests")
print("=" * 60)


@test("tool_hook_integration")
def test_tool_hook_integration():
    """Test hooks integration with MetonBaseTool."""
    from tools.base import MetonBaseTool

    # Create a simple test tool
    class TestTool(MetonBaseTool):
        name: str = "test_tool"
        description: str = "A test tool"

        def _run(self, input_str: str) -> str:
            return f"processed: {input_str}"

    # Create hook manager with a tracking hook
    call_log = []

    def tracking_hook(context: HookContext) -> HookResult:
        call_log.append({
            "type": context.hook_type.value,
            "name": context.name,
            "success": context.success,
        })
        return HookResult(success=True)

    manager = HookManager()
    manager.register(Hook(
        name="pre-tracker",
        hook_type=HookType.PRE_TOOL,
        func=tracking_hook,
    ))
    manager.register(Hook(
        name="post-tracker",
        hook_type=HookType.POST_TOOL,
        func=tracking_hook,
    ))

    # Create tool with hook manager
    tool = TestTool()
    tool.set_hook_manager(manager)

    # Execute tool
    result = tool.run("hello")

    assert "processed: hello" in result
    assert len(call_log) == 2
    assert call_log[0]["type"] == "pre_tool"
    assert call_log[1]["type"] == "post_tool"
    assert call_log[1]["success"] == True


@test("pre_hook_can_modify_input")
def test_pre_hook_can_modify_input():
    """Test that pre-hooks can modify tool input."""
    from tools.base import MetonBaseTool

    class EchoTool(MetonBaseTool):
        name: str = "echo"
        description: str = "Echoes input"

        def _run(self, input_str: str) -> str:
            return input_str

    def modifier_hook(context: HookContext) -> HookResult:
        return HookResult(
            success=True,
            modified_input=context.input_data.upper()
        )

    manager = HookManager()
    manager.register(Hook(
        name="modifier",
        hook_type=HookType.PRE_TOOL,
        func=modifier_hook,
    ))

    tool = EchoTool()
    tool.set_hook_manager(manager)

    result = tool.run("hello")
    assert result == "HELLO"


@test("pre_hook_can_skip_execution")
def test_pre_hook_can_skip_execution():
    """Test that pre-hooks can skip tool execution."""
    from tools.base import MetonBaseTool

    class FailTool(MetonBaseTool):
        name: str = "fail"
        description: str = "Would fail"

        def _run(self, input_str: str) -> str:
            raise Exception("Should not be called")

    def skipper_hook(context: HookContext) -> HookResult:
        return HookResult(
            success=True,
            should_skip=True,
            output="Skipped by hook"
        )

    manager = HookManager()
    manager.register(Hook(
        name="skipper",
        hook_type=HookType.PRE_TOOL,
        func=skipper_hook,
    ))

    tool = FailTool()
    tool.set_hook_manager(manager)

    result = tool.run("test")
    assert result == "Skipped by hook"


@test("create_logging_hook_helper")
def test_create_logging_hook_helper():
    """Test the create_logging_hook helper function."""
    hook = create_logging_hook(
        name="logger",
        hook_type=HookType.POST_TOOL,
        log_message="Tool {name} completed",
    )

    assert hook.name == "logger"
    assert hook.hook_type == HookType.POST_TOOL
    assert hook.func is not None

    # Test execution
    context = HookContext(
        hook_type=HookType.POST_TOOL,
        name="test_tool",
    )
    result = hook.func(context)
    assert result.success == True


test_tool_hook_integration()
test_pre_hook_can_modify_input()
test_pre_hook_can_skip_execution()
test_create_logging_hook_helper()


# =============================================================================
# CLI Integration Tests
# =============================================================================

print("\n" + "=" * 60)
print("CLI Integration Tests")
print("=" * 60)


@test("cli_imports_hooks")
def test_cli_imports_hooks():
    """Test that CLI imports hook components."""
    from cli import HookManager, HookLoader, Hook, HookType
    assert HookManager is not None
    assert HookLoader is not None
    assert Hook is not None
    assert HookType is not None


@test("cli_has_hook_attributes")
def test_cli_has_hook_attributes():
    """Test that MetonCLI has hook attributes."""
    from cli import MetonCLI
    cli = MetonCLI()

    assert hasattr(cli, 'hook_manager')
    assert hasattr(cli, 'hook_loader')


test_cli_imports_hooks()
test_cli_has_hook_attributes()


# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 60)
print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
print("=" * 60)

if failed > 0:
    sys.exit(1)
