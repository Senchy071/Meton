#!/usr/bin/env python3
"""Tests for Phase 3: Agent Integration with Skills and Sub-Agents.

This module tests the integration of skills and sub-agents with the main
Meton agent, including the SkillInvocationTool and SubAgentTool.
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.skill_tool import SkillInvocationTool, SkillToolConfig
from tools.subagent_tool import SubAgentTool, SubAgentToolConfig
from skills.skill_manager import SkillManager
from skills.markdown_skill import MarkdownSkill

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
# SkillInvocationTool Tests
# =============================================================================

print("\n" + "=" * 60)
print("SkillInvocationTool Tests")
print("=" * 60)


@test("skill_tool_creation")
def test_skill_tool_creation():
    """Test creating a SkillInvocationTool."""
    manager = SkillManager()
    manager.load_all_skills()
    tool = SkillInvocationTool(manager)

    assert tool.name == "invoke_skill"
    assert "skill" in tool.description.lower()
    assert tool.skill_manager is manager


@test("skill_tool_get_available_skills")
def test_skill_tool_get_available_skills():
    """Test getting available skills."""
    manager = SkillManager()
    manager.load_all_skills()
    tool = SkillInvocationTool(manager)

    skills = tool.get_available_skills()
    assert len(skills) > 0

    # Check skill structure
    for skill in skills:
        assert "name" in skill
        assert "type" in skill
        assert "description" in skill


@test("skill_tool_generate_prompt_section")
def test_skill_tool_generate_prompt_section():
    """Test generating prompt section for skills."""
    manager = SkillManager()
    manager.load_all_skills()
    tool = SkillInvocationTool(manager)

    prompt = tool.generate_prompt_section()
    assert "AVAILABLE SKILLS" in prompt
    assert "invoke_skill" in prompt


@test("skill_tool_invoke_valid_skill")
def test_skill_tool_invoke_valid_skill():
    """Test invoking a valid skill."""
    manager = SkillManager()
    manager.load_all_skills()
    tool = SkillInvocationTool(manager)

    # Get first available skill
    skills = manager.list_loaded_skills()
    if skills:
        skill_name = skills[0]
        result = tool._run(json.dumps({
            "skill": skill_name,
            "input": {}
        }))

        result_data = json.loads(result)
        assert result_data["success"] == True
        assert result_data["skill"] == skill_name


@test("skill_tool_invoke_missing_skill")
def test_skill_tool_invoke_missing_skill():
    """Test invoking a non-existent skill."""
    manager = SkillManager()
    tool = SkillInvocationTool(manager)

    result = tool._run(json.dumps({
        "skill": "nonexistent-skill",
        "input": {}
    }))

    result_data = json.loads(result)
    assert result_data["success"] == False
    assert "not found" in result_data["error"].lower()


@test("skill_tool_invalid_json")
def test_skill_tool_invalid_json():
    """Test handling invalid JSON input."""
    manager = SkillManager()
    tool = SkillInvocationTool(manager)

    result = tool._run("not valid json")
    result_data = json.loads(result)

    assert result_data["success"] == False
    assert "json" in result_data["error"].lower()


@test("skill_tool_missing_skill_field")
def test_skill_tool_missing_skill_field():
    """Test handling missing skill field."""
    manager = SkillManager()
    tool = SkillInvocationTool(manager)

    result = tool._run(json.dumps({"input": {}}))
    result_data = json.loads(result)

    assert result_data["success"] == False
    assert "missing" in result_data["error"].lower() or "required" in result_data["error"].lower()


@test("skill_tool_disabled")
def test_skill_tool_disabled():
    """Test skill tool when disabled."""
    manager = SkillManager()
    tool = SkillInvocationTool(manager)
    tool.config.enabled = False

    result = tool._run(json.dumps({"skill": "test", "input": {}}))
    result_data = json.loads(result)

    assert result_data["success"] == False
    assert "disabled" in result_data["error"].lower()


test_skill_tool_creation()
test_skill_tool_get_available_skills()
test_skill_tool_generate_prompt_section()
test_skill_tool_invoke_valid_skill()
test_skill_tool_invoke_missing_skill()
test_skill_tool_invalid_json()
test_skill_tool_missing_skill_field()
test_skill_tool_disabled()


# =============================================================================
# SubAgentTool Tests (without actual agent execution)
# =============================================================================

print("\n" + "=" * 60)
print("SubAgentTool Tests")
print("=" * 60)


class MockSubAgentManager:
    """Mock SubAgentManager for testing without actual agent execution."""

    def __init__(self):
        self.agents = {
            "explorer": MockAgent("explorer", "quick", "Fast exploration"),
            "planner": MockAgent("planner", "primary", "Implementation planning"),
        }

    def list_agents(self):
        return list(self.agents.keys())

    def get_agent(self, name):
        return self.agents.get(name)

    def run_agent(self, agent_name, task, context=None):
        if agent_name not in self.agents:
            return MockResult(success=False, error=f"Agent {agent_name} not found")
        return MockResult(
            success=True,
            output=f"Completed task: {task}",
            agent_id="test-123",
            iterations=2,
            duration_seconds=1.5,
            model_used="test-model"
        )


class MockAgent:
    """Mock agent for testing."""
    def __init__(self, name, model, description):
        self.name = name
        self.model = model
        self.description = description
        self.tools = ["file_operations", "codebase_search"]


class MockResult:
    """Mock result for testing."""
    def __init__(self, success=True, output="", error=None, agent_id="", iterations=0, duration_seconds=0.0, model_used=""):
        self.success = success
        self.output = output
        self.error = error
        self.agent_id = agent_id
        self.iterations = iterations
        self.duration_seconds = duration_seconds
        self.model_used = model_used


@test("subagent_tool_creation")
def test_subagent_tool_creation():
    """Test creating a SubAgentTool."""
    manager = MockSubAgentManager()
    tool = SubAgentTool(manager)

    assert tool.name == "spawn_agent"
    assert "agent" in tool.description.lower()
    assert tool.agent_manager is manager


@test("subagent_tool_get_available_agents")
def test_subagent_tool_get_available_agents():
    """Test getting available agents."""
    manager = MockSubAgentManager()
    tool = SubAgentTool(manager)

    agents = tool.get_available_agents()
    assert len(agents) == 2

    # Check agent structure
    for agent in agents:
        assert "name" in agent
        assert "model" in agent
        assert "description" in agent


@test("subagent_tool_generate_prompt_section")
def test_subagent_tool_generate_prompt_section():
    """Test generating prompt section for agents."""
    manager = MockSubAgentManager()
    tool = SubAgentTool(manager)

    prompt = tool.generate_prompt_section()
    assert "AVAILABLE SUB-AGENTS" in prompt
    assert "spawn_agent" in prompt
    assert "explorer" in prompt


@test("subagent_tool_spawn_valid_agent")
def test_subagent_tool_spawn_valid_agent():
    """Test spawning a valid agent."""
    manager = MockSubAgentManager()
    tool = SubAgentTool(manager)

    result = tool._run(json.dumps({
        "agent": "explorer",
        "task": "Find all Python files"
    }))

    result_data = json.loads(result)
    assert result_data["success"] == True
    assert result_data["agent"] == "explorer"
    assert "output" in result_data


@test("subagent_tool_spawn_missing_agent")
def test_subagent_tool_spawn_missing_agent():
    """Test spawning a non-existent agent."""
    manager = MockSubAgentManager()
    tool = SubAgentTool(manager)

    result = tool._run(json.dumps({
        "agent": "nonexistent",
        "task": "Do something"
    }))

    result_data = json.loads(result)
    assert result_data["success"] == False
    assert "not found" in result_data["error"].lower()


@test("subagent_tool_invalid_json")
def test_subagent_tool_invalid_json():
    """Test handling invalid JSON input."""
    manager = MockSubAgentManager()
    tool = SubAgentTool(manager)

    result = tool._run("not valid json")
    result_data = json.loads(result)

    assert result_data["success"] == False
    assert "json" in result_data["error"].lower()


@test("subagent_tool_missing_fields")
def test_subagent_tool_missing_fields():
    """Test handling missing required fields."""
    manager = MockSubAgentManager()
    tool = SubAgentTool(manager)

    # Missing task
    result = tool._run(json.dumps({"agent": "explorer"}))
    result_data = json.loads(result)
    assert result_data["success"] == False

    # Missing agent
    result = tool._run(json.dumps({"task": "Do something"}))
    result_data = json.loads(result)
    assert result_data["success"] == False


@test("subagent_tool_disabled")
def test_subagent_tool_disabled():
    """Test subagent tool when disabled."""
    manager = MockSubAgentManager()
    tool = SubAgentTool(manager)
    tool.config.enabled = False

    result = tool._run(json.dumps({"agent": "explorer", "task": "test"}))
    result_data = json.loads(result)

    assert result_data["success"] == False
    assert "disabled" in result_data["error"].lower()


@test("subagent_tool_with_context")
def test_subagent_tool_with_context():
    """Test spawning agent with optional context."""
    manager = MockSubAgentManager()
    tool = SubAgentTool(manager)

    result = tool._run(json.dumps({
        "agent": "explorer",
        "task": "Find authentication code",
        "context": "We are working on a security audit"
    }))

    result_data = json.loads(result)
    assert result_data["success"] == True


test_subagent_tool_creation()
test_subagent_tool_get_available_agents()
test_subagent_tool_generate_prompt_section()
test_subagent_tool_spawn_valid_agent()
test_subagent_tool_spawn_missing_agent()
test_subagent_tool_invalid_json()
test_subagent_tool_missing_fields()
test_subagent_tool_disabled()
test_subagent_tool_with_context()


# =============================================================================
# Agent Integration Tests
# =============================================================================

print("\n" + "=" * 60)
print("Agent Integration Tests")
print("=" * 60)


@test("agent_accepts_skill_tool")
def test_agent_accepts_skill_tool():
    """Test that MetonAgent accepts skill_tool parameter."""
    from core.agent import MetonAgent
    from core.config import Config
    from core.models import ModelManager
    from core.conversation import ConversationManager

    config = Config()
    model_manager = ModelManager(config)
    conversation = ConversationManager(config)

    manager = SkillManager()
    manager.load_all_skills()
    skill_tool = SkillInvocationTool(manager)

    agent = MetonAgent(
        config=config,
        model_manager=model_manager,
        conversation=conversation,
        tools=[skill_tool],
        skill_tool=skill_tool
    )

    assert agent.skill_tool is skill_tool


@test("agent_accepts_subagent_tool")
def test_agent_accepts_subagent_tool():
    """Test that MetonAgent accepts subagent_tool parameter."""
    from core.agent import MetonAgent
    from core.config import Config
    from core.models import ModelManager
    from core.conversation import ConversationManager

    config = Config()
    model_manager = ModelManager(config)
    conversation = ConversationManager(config)

    mock_manager = MockSubAgentManager()
    subagent_tool = SubAgentTool(mock_manager)

    agent = MetonAgent(
        config=config,
        model_manager=model_manager,
        conversation=conversation,
        tools=[subagent_tool],
        subagent_tool=subagent_tool
    )

    assert agent.subagent_tool is subagent_tool


@test("agent_system_prompt_includes_skills")
def test_agent_system_prompt_includes_skills():
    """Test that agent system prompt includes skill section."""
    from core.agent import MetonAgent
    from core.config import Config
    from core.models import ModelManager
    from core.conversation import ConversationManager

    config = Config()
    model_manager = ModelManager(config)
    conversation = ConversationManager(config)

    manager = SkillManager()
    manager.load_all_skills()
    skill_tool = SkillInvocationTool(manager)

    agent = MetonAgent(
        config=config,
        model_manager=model_manager,
        conversation=conversation,
        tools=[skill_tool],
        skill_tool=skill_tool
    )

    prompt = agent._get_system_prompt()
    assert "AVAILABLE SKILLS" in prompt


@test("agent_system_prompt_includes_subagents")
def test_agent_system_prompt_includes_subagents():
    """Test that agent system prompt includes sub-agent section."""
    from core.agent import MetonAgent
    from core.config import Config
    from core.models import ModelManager
    from core.conversation import ConversationManager

    config = Config()
    model_manager = ModelManager(config)
    conversation = ConversationManager(config)

    mock_manager = MockSubAgentManager()
    subagent_tool = SubAgentTool(mock_manager)

    agent = MetonAgent(
        config=config,
        model_manager=model_manager,
        conversation=conversation,
        tools=[subagent_tool],
        subagent_tool=subagent_tool
    )

    prompt = agent._get_system_prompt()
    assert "AVAILABLE SUB-AGENTS" in prompt


@test("agent_prompt_without_integration_tools")
def test_agent_prompt_without_integration_tools():
    """Test that agent works without skill/subagent tools."""
    from core.agent import MetonAgent
    from core.config import Config
    from core.models import ModelManager
    from core.conversation import ConversationManager

    config = Config()
    model_manager = ModelManager(config)
    conversation = ConversationManager(config)

    agent = MetonAgent(
        config=config,
        model_manager=model_manager,
        conversation=conversation,
        tools=[]
    )

    # Should not raise error
    prompt = agent._get_system_prompt()
    assert "AVAILABLE TOOLS" in prompt


test_agent_accepts_skill_tool()
test_agent_accepts_subagent_tool()
test_agent_system_prompt_includes_skills()
test_agent_system_prompt_includes_subagents()
test_agent_prompt_without_integration_tools()


# =============================================================================
# CLI Integration Tests
# =============================================================================

print("\n" + "=" * 60)
print("CLI Integration Tests")
print("=" * 60)


@test("cli_imports_integration_tools")
def test_cli_imports_integration_tools():
    """Test that CLI imports skill and subagent tools."""
    from cli import SkillInvocationTool, SubAgentTool, SkillManager, SubAgentManager
    assert SkillInvocationTool is not None
    assert SubAgentTool is not None
    assert SkillManager is not None
    assert SubAgentManager is not None


@test("cli_has_integration_attributes")
def test_cli_has_integration_attributes():
    """Test that CLI has skill and subagent attributes."""
    from cli import MetonCLI
    cli = MetonCLI()

    assert hasattr(cli, 'skill_tool')
    assert hasattr(cli, 'subagent_tool')
    assert hasattr(cli, 'skill_manager')
    assert hasattr(cli, 'subagent_manager')


test_cli_imports_integration_tools()
test_cli_has_integration_attributes()


# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 60)
print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
print("=" * 60)

if failed > 0:
    sys.exit(1)
