"""Tests for skill framework (Task 21).

This test suite validates the skill framework implementation:
- BaseSkill class
- SkillRegistry
- Skill registration, execution, and management
"""

import pytest
from typing import Dict, Any

from skills import (
    BaseSkill,
    SkillRegistry,
    SkillError,
    SkillValidationError,
    SkillExecutionError,
    SkillRegistryError,
)


# Test skill implementations

class SimpleSkill(BaseSkill):
    """Simple test skill that returns success."""
    name = "simple_skill"
    description = "A simple test skill"
    version = "1.0.0"

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute simple skill."""
        return {
            "success": True,
            "result": "Task completed",
            "input_received": input_data
        }


class CalculatorSkill(BaseSkill):
    """Calculator skill for testing input validation."""
    name = "calculator"
    description = "Performs calculations"
    version = "1.0.0"

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input has required fields."""
        super().validate_input(input_data)

        if "operation" not in input_data:
            raise SkillValidationError("Missing required field: operation")

        if "numbers" not in input_data:
            raise SkillValidationError("Missing required field: numbers")

        if not isinstance(input_data["numbers"], list):
            raise SkillValidationError("Field 'numbers' must be a list")

        return True

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute calculation."""
        operation = input_data["operation"]
        numbers = input_data["numbers"]

        if operation == "sum":
            result = sum(numbers)
        elif operation == "multiply":
            result = 1
            for n in numbers:
                result *= n
        else:
            raise SkillExecutionError(f"Unknown operation: {operation}")

        return {
            "success": True,
            "result": result,
            "operation": operation
        }


class FailingSkill(BaseSkill):
    """Skill that always fails (for testing error handling)."""
    name = "failing_skill"
    description = "Always fails"
    version = "1.0.0"

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Always raises an error."""
        raise RuntimeError("This skill always fails")


# Tests for BaseSkill

class TestBaseSkill:
    """Tests for BaseSkill class."""

    def test_skill_creation(self):
        """Test creating a skill instance."""
        skill = SimpleSkill()
        assert skill.name == "simple_skill"
        assert skill.description == "A simple test skill"
        assert skill.version == "1.0.0"
        assert skill.enabled is True

    def test_skill_get_info(self):
        """Test getting skill metadata."""
        skill = SimpleSkill()
        info = skill.get_info()

        assert info["name"] == "simple_skill"
        assert info["description"] == "A simple test skill"
        assert info["version"] == "1.0.0"
        assert info["enabled"] is True

    def test_skill_enable_disable(self):
        """Test enabling and disabling skills."""
        skill = SimpleSkill()

        # Test disable
        skill.disable()
        assert skill.enabled is False

        # Test enable
        skill.enable()
        assert skill.enabled is True

    def test_skill_execute(self):
        """Test executing a skill."""
        skill = SimpleSkill()
        result = skill.execute({"task": "test"})

        assert result["success"] is True
        assert result["result"] == "Task completed"
        assert result["input_received"] == {"task": "test"}

    def test_skill_validate_input_dict_check(self):
        """Test that validate_input requires a dictionary."""
        skill = SimpleSkill()

        # Valid input (dict)
        assert skill.validate_input({"key": "value"}) is True

        # Invalid inputs (not dict)
        with pytest.raises(SkillValidationError, match="must be a dictionary"):
            skill.validate_input("not a dict")

        with pytest.raises(SkillValidationError, match="must be a dictionary"):
            skill.validate_input([1, 2, 3])

        with pytest.raises(SkillValidationError, match="must be a dictionary"):
            skill.validate_input(None)

    def test_skill_custom_validation(self):
        """Test custom input validation."""
        skill = CalculatorSkill()

        # Valid input
        valid_input = {"operation": "sum", "numbers": [1, 2, 3]}
        assert skill.validate_input(valid_input) is True

        # Missing operation
        with pytest.raises(SkillValidationError, match="Missing required field: operation"):
            skill.validate_input({"numbers": [1, 2, 3]})

        # Missing numbers
        with pytest.raises(SkillValidationError, match="Missing required field: numbers"):
            skill.validate_input({"operation": "sum"})

        # Invalid numbers type
        with pytest.raises(SkillValidationError, match="must be a list"):
            skill.validate_input({"operation": "sum", "numbers": "not a list"})

    def test_skill_repr(self):
        """Test skill string representation."""
        skill = SimpleSkill()
        repr_str = repr(skill)

        assert "SimpleSkill" in repr_str
        assert "simple_skill" in repr_str
        assert "1.0.0" in repr_str
        assert "enabled" in repr_str

        # Test disabled representation
        skill.disable()
        repr_str = repr(skill)
        assert "disabled" in repr_str


# Tests for SkillRegistry

class TestSkillRegistry:
    """Tests for SkillRegistry class."""

    def test_registry_creation(self):
        """Test creating a registry instance."""
        registry = SkillRegistry()
        assert len(registry) == 0
        assert len(registry.list_all()) == 0

    def test_register_skill(self):
        """Test registering a skill."""
        registry = SkillRegistry()
        skill = SimpleSkill()

        registry.register(skill)

        assert len(registry) == 1
        assert registry.has_skill("simple_skill")
        assert registry.get("simple_skill") is skill

    def test_register_multiple_skills(self):
        """Test registering multiple skills."""
        registry = SkillRegistry()
        skill1 = SimpleSkill()
        skill2 = CalculatorSkill()

        registry.register(skill1)
        registry.register(skill2)

        assert len(registry) == 2
        assert registry.has_skill("simple_skill")
        assert registry.has_skill("calculator")

    def test_register_duplicate_skill(self):
        """Test that registering duplicate skill raises error."""
        registry = SkillRegistry()
        skill1 = SimpleSkill()
        skill2 = SimpleSkill()

        registry.register(skill1)

        with pytest.raises(SkillRegistryError, match="already registered"):
            registry.register(skill2)

    def test_register_invalid_skill(self):
        """Test that registering non-skill raises error."""
        registry = SkillRegistry()

        with pytest.raises(SkillRegistryError, match="must be an instance of BaseSkill"):
            registry.register("not a skill")

        with pytest.raises(SkillRegistryError, match="must be an instance of BaseSkill"):
            registry.register({"name": "fake_skill"})

    def test_unregister_skill(self):
        """Test unregistering a skill."""
        registry = SkillRegistry()
        skill = SimpleSkill()

        registry.register(skill)
        assert registry.has_skill("simple_skill")

        registry.unregister("simple_skill")
        assert not registry.has_skill("simple_skill")
        assert len(registry) == 0

    def test_unregister_nonexistent_skill(self):
        """Test that unregistering non-existent skill raises error."""
        registry = SkillRegistry()

        with pytest.raises(SkillRegistryError, match="not registered"):
            registry.unregister("nonexistent_skill")

    def test_get_skill(self):
        """Test getting a skill by name."""
        registry = SkillRegistry()
        skill = SimpleSkill()
        registry.register(skill)

        retrieved = registry.get("simple_skill")
        assert retrieved is skill

        # Test getting non-existent skill
        assert registry.get("nonexistent") is None

    def test_list_all_skills(self):
        """Test listing all registered skills."""
        registry = SkillRegistry()
        skill1 = SimpleSkill()
        skill2 = CalculatorSkill()

        registry.register(skill1)
        registry.register(skill2)

        skills = registry.list_all()
        assert len(skills) == 2

        skill_names = {s["name"] for s in skills}
        assert skill_names == {"simple_skill", "calculator"}

        # Check that each has required fields
        for skill_info in skills:
            assert "name" in skill_info
            assert "description" in skill_info
            assert "version" in skill_info
            assert "enabled" in skill_info

    def test_execute_skill(self):
        """Test executing a skill through the registry."""
        registry = SkillRegistry()
        skill = CalculatorSkill()
        registry.register(skill)

        result = registry.execute_skill(
            "calculator",
            {"operation": "sum", "numbers": [1, 2, 3, 4, 5]}
        )

        assert result["success"] is True
        assert result["result"] == 15
        assert result["operation"] == "sum"

    def test_execute_nonexistent_skill(self):
        """Test executing non-existent skill raises error."""
        registry = SkillRegistry()

        with pytest.raises(SkillRegistryError, match="not registered"):
            registry.execute_skill("nonexistent", {"data": "test"})

    def test_execute_disabled_skill(self):
        """Test executing disabled skill raises error."""
        registry = SkillRegistry()
        skill = SimpleSkill()
        skill.disable()
        registry.register(skill)

        with pytest.raises(SkillRegistryError, match="disabled"):
            registry.execute_skill("simple_skill", {"data": "test"})

    def test_execute_skill_validation_failure(self):
        """Test that validation errors are propagated."""
        registry = SkillRegistry()
        skill = CalculatorSkill()
        registry.register(skill)

        # Missing required field
        with pytest.raises(SkillValidationError, match="Missing required field"):
            registry.execute_skill("calculator", {"operation": "sum"})

    def test_execute_skill_execution_failure(self):
        """Test that execution errors are wrapped in SkillExecutionError."""
        registry = SkillRegistry()
        skill = FailingSkill()
        registry.register(skill)

        with pytest.raises(SkillExecutionError, match="execution failed"):
            registry.execute_skill("failing_skill", {})

    def test_enable_disable_skill(self):
        """Test enabling and disabling skills through registry."""
        registry = SkillRegistry()
        skill = SimpleSkill()
        registry.register(skill)

        # Disable
        registry.disable_skill("simple_skill")
        assert skill.enabled is False

        # Enable
        registry.enable_skill("simple_skill")
        assert skill.enabled is True

    def test_enable_disable_nonexistent_skill(self):
        """Test enabling/disabling non-existent skill raises error."""
        registry = SkillRegistry()

        with pytest.raises(SkillRegistryError, match="not registered"):
            registry.enable_skill("nonexistent")

        with pytest.raises(SkillRegistryError, match="not registered"):
            registry.disable_skill("nonexistent")

    def test_has_skill(self):
        """Test checking if skill exists."""
        registry = SkillRegistry()
        skill = SimpleSkill()

        assert not registry.has_skill("simple_skill")

        registry.register(skill)
        assert registry.has_skill("simple_skill")

        registry.unregister("simple_skill")
        assert not registry.has_skill("simple_skill")

    def test_clear_registry(self):
        """Test clearing all skills from registry."""
        registry = SkillRegistry()
        registry.register(SimpleSkill())
        registry.register(CalculatorSkill())

        assert len(registry) == 2

        registry.clear()

        assert len(registry) == 0
        assert len(registry.list_all()) == 0
        assert not registry.has_skill("simple_skill")
        assert not registry.has_skill("calculator")

    def test_registry_len(self):
        """Test registry length."""
        registry = SkillRegistry()

        assert len(registry) == 0

        registry.register(SimpleSkill())
        assert len(registry) == 1

        registry.register(CalculatorSkill())
        assert len(registry) == 2

        registry.unregister("simple_skill")
        assert len(registry) == 1

        registry.clear()
        assert len(registry) == 0

    def test_registry_repr(self):
        """Test registry string representation."""
        registry = SkillRegistry()
        repr_str = repr(registry)

        assert "SkillRegistry" in repr_str
        assert "skills=0" in repr_str

        registry.register(SimpleSkill())
        repr_str = repr(registry)
        assert "skills=1" in repr_str


# Integration tests

class TestSkillIntegration:
    """Integration tests for skill framework."""

    def test_full_workflow(self):
        """Test complete skill workflow: register, execute, unregister."""
        # Create registry
        registry = SkillRegistry()

        # Register skills
        registry.register(SimpleSkill())
        registry.register(CalculatorSkill())

        # List skills
        skills = registry.list_all()
        assert len(skills) == 2

        # Execute simple skill
        result1 = registry.execute_skill("simple_skill", {"task": "test"})
        assert result1["success"] is True

        # Execute calculator skill
        result2 = registry.execute_skill(
            "calculator",
            {"operation": "multiply", "numbers": [2, 3, 4]}
        )
        assert result2["success"] is True
        assert result2["result"] == 24

        # Disable skill
        registry.disable_skill("simple_skill")
        with pytest.raises(SkillRegistryError, match="disabled"):
            registry.execute_skill("simple_skill", {"task": "test"})

        # Re-enable skill
        registry.enable_skill("simple_skill")
        result3 = registry.execute_skill("simple_skill", {"task": "test"})
        assert result3["success"] is True

        # Unregister skills
        registry.unregister("simple_skill")
        registry.unregister("calculator")
        assert len(registry) == 0

    def test_multiple_registries(self):
        """Test that multiple registries are independent."""
        registry1 = SkillRegistry()
        registry2 = SkillRegistry()

        registry1.register(SimpleSkill())

        assert registry1.has_skill("simple_skill")
        assert not registry2.has_skill("simple_skill")

        registry2.register(CalculatorSkill())

        assert registry1.has_skill("simple_skill")
        assert not registry1.has_skill("calculator")
        assert registry2.has_skill("calculator")
        assert not registry2.has_skill("simple_skill")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
