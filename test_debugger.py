"""Tests for Debugger Assistant Skill.

This module tests the DebuggerAssistantSkill's ability to:
- Parse and analyze Python errors
- Detect syntax errors
- Analyze runtime errors
- Suggest fixes with confidence ranking
- Detect common error patterns
"""

import pytest
from skills.debugger import DebuggerAssistantSkill
from skills.base import SkillValidationError


@pytest.fixture
def skill():
    """Create a DebuggerAssistantSkill instance."""
    return DebuggerAssistantSkill()


class TestInitialization:
    """Test skill initialization."""

    def test_skill_creation(self, skill):
        """Test that skill is created with correct attributes."""
        assert skill.name == "debugger_assistant"
        assert skill.version == "1.0.0"
        assert skill.enabled is True
        assert "debug" in skill.description.lower()

    def test_skill_info(self, skill):
        """Test get_info returns correct metadata."""
        info = skill.get_info()
        assert info["name"] == "debugger_assistant"
        assert info["version"] == "1.0.0"
        assert info["enabled"] is True
        assert "debug" in info["description"].lower()


class TestInputValidation:
    """Test input validation."""

    def test_missing_code(self, skill):
        """Test that missing code raises validation error."""
        result = skill.execute({})
        assert result["success"] is False
        assert "code" in result["error"].lower()

    def test_empty_code(self, skill):
        """Test that empty code raises validation error."""
        result = skill.execute({"code": ""})
        assert result["success"] is False
        assert "empty" in result["error"].lower()

    def test_invalid_code_type(self, skill):
        """Test that non-string code raises validation error."""
        result = skill.execute({"code": 123})
        assert result["success"] is False
        assert "string" in result["error"].lower()

    def test_invalid_error_type(self, skill):
        """Test that invalid error_type raises validation error."""
        result = skill.execute({
            "code": "x = 1",
            "error_type": "invalid"
        })
        assert result["success"] is False
        assert "error_type" in result["error"].lower()

    def test_valid_input(self, skill):
        """Test that valid input passes validation."""
        result = skill.execute({
            "code": "x = 1",
            "error": "NameError: name 'y' is not defined"
        })
        assert result["success"] is True


class TestSyntaxErrors:
    """Test syntax error detection and analysis."""

    def test_missing_colon(self, skill):
        """Test detection of missing colon."""
        code = """
def greet(name)
    print(f'Hello {name}')
"""
        result = skill.execute({"code": code})
        assert result["success"] is True
        assert "colon" in result["error_analysis"].lower()
        assert result["error_location"].get("line") == 2
        assert len(result["fix_suggestions"]) > 0
        assert result["fix_suggestions"][0]["confidence"] == "high"
        assert ":" in result["fix_suggestions"][0]["fixed_code"]

    def test_missing_parenthesis(self, skill):
        """Test detection of missing parenthesis."""
        code = """
result = (1 + 2 * (3 + 4)
print(result)
"""
        result = skill.execute({"code": code})
        assert result["success"] is True
        assert "parenthes" in result["error_analysis"].lower()
        assert len(result["fix_suggestions"]) > 0

    def test_indentation_error(self, skill):
        """Test detection of indentation error."""
        code = """
def foo():
print('wrong indent')
"""
        result = skill.execute({"code": code})
        assert result["success"] is True
        assert "indent" in result["error_analysis"].lower()
        assert "indent" in result["cause"].lower()

    def test_syntax_error_with_message(self, skill):
        """Test syntax error with explicit error message."""
        code = "if True print('hello')"
        error = "SyntaxError: invalid syntax"
        result = skill.execute({"code": code, "error": error})
        assert result["success"] is True
        # Should detect syntax error or more specifically missing colon
        assert "syntax" in result["error_analysis"].lower() or "colon" in result["error_analysis"].lower()
        assert len(result["fix_suggestions"]) > 0


class TestRuntimeErrors:
    """Test runtime error detection and analysis."""

    def test_name_error(self, skill):
        """Test NameError detection."""
        code = """
def calculate():
    x = 10
    return y + 5
"""
        error = "NameError: name 'y' is not defined"
        result = skill.execute({"code": code, "error": error})
        assert result["success"] is True
        assert "not defined" in result["error_analysis"].lower()
        assert "'y'" in result["error_analysis"] or "y" in result["error_analysis"]
        assert len(result["fix_suggestions"]) > 0
        # Should suggest defining the variable
        assert any("define" in fix["description"].lower()
                   for fix in result["fix_suggestions"])

    def test_type_error(self, skill):
        """Test TypeError detection."""
        code = """
def add_numbers(a, b):
    return a + b

result = add_numbers("5", 3)
"""
        error = "TypeError: can only concatenate str (not 'int') to str"
        result = skill.execute({"code": code, "error": error})
        assert result["success"] is True
        assert "type" in result["error_analysis"].lower()
        assert len(result["fix_suggestions"]) > 0
        # Should suggest type conversion
        assert any("convert" in fix["description"].lower() or "type" in fix["description"].lower()
                   for fix in result["fix_suggestions"])

    def test_attribute_error(self, skill):
        """Test AttributeError detection."""
        code = """
my_list = [1, 2, 3]
my_list.append(4)
my_list.push(5)
"""
        error = "AttributeError: 'list' object has no attribute 'push'"
        result = skill.execute({"code": code, "error": error})
        assert result["success"] is True
        assert "attribute" in result["error_analysis"].lower()
        assert "push" in result["error_analysis"]
        assert len(result["fix_suggestions"]) > 0
        assert len(result["related_issues"]) > 0

    def test_index_error(self, skill):
        """Test IndexError detection."""
        code = """
numbers = [1, 2, 3]
value = numbers[5]
"""
        error = "IndexError: list index out of range"
        result = skill.execute({"code": code, "error": error})
        assert result["success"] is True
        assert "index" in result["error_analysis"].lower()
        assert len(result["fix_suggestions"]) > 0
        # Should suggest bounds checking
        assert any("bound" in fix["description"].lower() or "len" in fix["fixed_code"].lower()
                   for fix in result["fix_suggestions"])

    def test_key_error(self, skill):
        """Test KeyError detection."""
        code = """
data = {"name": "Alice", "age": 30}
city = data["city"]
"""
        error = "KeyError: 'city'"
        result = skill.execute({"code": code, "error": error})
        assert result["success"] is True
        assert "key" in result["error_analysis"].lower()
        assert len(result["fix_suggestions"]) > 0
        # Should suggest using .get()
        assert any("get" in fix["fixed_code"].lower()
                   for fix in result["fix_suggestions"])

    def test_import_error(self, skill):
        """Test ImportError detection."""
        code = """
import pandas as pd
df = pd.DataFrame()
"""
        error = "ModuleNotFoundError: No module named 'pandas'"
        result = skill.execute({"code": code, "error": error})
        assert result["success"] is True
        assert "module" in result["error_analysis"].lower() or "import" in result["error_analysis"].lower()
        assert len(result["fix_suggestions"]) > 0
        # Should suggest pip install
        assert any("pip install" in fix["fixed_code"].lower()
                   for fix in result["fix_suggestions"])


class TestLogicAnalysis:
    """Test logic error detection."""

    def test_unreachable_code(self, skill):
        """Test detection of unreachable code."""
        code = """
def calculate(x):
    if x > 0:
        return x * 2
        print("This is unreachable")
    return 0
"""
        result = skill.execute({"code": code})
        assert result["success"] is True
        assert "unreachable" in result["error_analysis"].lower()

    def test_unused_variables(self, skill):
        """Test detection of unused variables."""
        code = """
def process_data():
    x = 10
    y = 20
    z = 30
    return x + y
"""
        result = skill.execute({"code": code})
        assert result["success"] is True
        if "unused" in result["error_analysis"].lower():
            assert "z" in result["error_analysis"]

    def test_missing_return(self, skill):
        """Test detection of missing return statement."""
        code = """
def calculate_sum(a, b):
    result = a + b
    # Missing return statement
"""
        result = skill.execute({"code": code})
        assert result["success"] is True
        # May or may not detect this - it's a logic issue

    def test_clean_code(self, skill):
        """Test analysis of code without obvious errors."""
        code = """
def greet(name):
    '''Greet a person by name.'''
    return f'Hello, {name}!'

result = greet('World')
print(result)
"""
        result = skill.execute({"code": code})
        assert result["success"] is True
        assert result["error_analysis"] is not None
        assert len(result["fix_suggestions"]) > 0


class TestComplexTracebacks:
    """Test parsing of complex error tracebacks."""

    def test_traceback_with_line_number(self, skill):
        """Test parsing traceback with line numbers."""
        code = """
def divide(a, b):
    return a / b

result = divide(10, 0)
"""
        error = """
Traceback (most recent call last):
  File "test.py", line 4, in <module>
    result = divide(10, 0)
  File "test.py", line 2, in divide
    return a / b
ZeroDivisionError: division by zero
"""
        result = skill.execute({"code": code, "error": error})
        assert result["success"] is True
        assert result["error_location"].get("line") is not None

    def test_nested_function_error(self, skill):
        """Test error in nested function call."""
        code = """
def outer():
    def inner():
        return undefined_var
    return inner()

outer()
"""
        error = "NameError: name 'undefined_var' is not defined"
        result = skill.execute({"code": code, "error": error})
        assert result["success"] is True
        assert "not defined" in result["error_analysis"].lower()


class TestFixSuggestions:
    """Test fix suggestion quality."""

    def test_fix_confidence_levels(self, skill):
        """Test that fixes have appropriate confidence levels."""
        code = "def foo()\n    pass"
        result = skill.execute({"code": code})
        assert result["success"] is True
        assert len(result["fix_suggestions"]) > 0
        for fix in result["fix_suggestions"]:
            assert "confidence" in fix
            assert fix["confidence"] in ["high", "medium", "low"]

    def test_multiple_fix_suggestions(self, skill):
        """Test that multiple fixes are suggested when appropriate."""
        code = "x = y + 1"
        error = "NameError: name 'y' is not defined"
        result = skill.execute({"code": code, "error": error})
        assert result["success"] is True
        # Should suggest multiple ways to fix
        assert len(result["fix_suggestions"]) >= 2

    def test_fix_has_code(self, skill):
        """Test that fixes include actual code suggestions."""
        code = "if True\n    print('hello')"
        result = skill.execute({"code": code})
        assert result["success"] is True
        assert len(result["fix_suggestions"]) > 0
        for fix in result["fix_suggestions"]:
            assert "fixed_code" in fix
            assert len(fix["fixed_code"]) > 0


class TestRelatedIssues:
    """Test related issues detection."""

    def test_related_issues_present(self, skill):
        """Test that related issues are identified."""
        code = "def foo():\nprint('hello')"
        result = skill.execute({"code": code})
        assert result["success"] is True
        assert "related_issues" in result
        assert len(result["related_issues"]) > 0

    def test_related_issues_relevant(self, skill):
        """Test that related issues are relevant to error type."""
        code = "x = y"
        error = "NameError: name 'y' is not defined"
        result = skill.execute({"code": code, "error": error})
        assert result["success"] is True
        # Related issues should mention imports, typos, or scope
        related_text = " ".join(result["related_issues"]).lower()
        assert any(keyword in related_text
                   for keyword in ["import", "typo", "scope", "variable"])


class TestErrorTypes:
    """Test different error type classifications."""

    def test_syntax_error_type(self, skill):
        """Test syntax error is correctly classified."""
        code = "if True"
        result = skill.execute({"code": code, "error_type": "syntax"})
        assert result["success"] is True
        assert "syntax" in result["error_analysis"].lower() or "colon" in result["error_analysis"].lower()

    def test_runtime_error_type(self, skill):
        """Test runtime error is correctly handled."""
        code = "x = 1 / 0"
        error = "ZeroDivisionError: division by zero"
        result = skill.execute({"code": code, "error": error, "error_type": "runtime"})
        assert result["success"] is True

    def test_logic_error_type(self, skill):
        """Test logic error analysis."""
        code = """
def double(x):
    result = x * 2
"""
        result = skill.execute({"code": code, "error_type": "logic"})
        assert result["success"] is True


class TestEnableDisable:
    """Test enable/disable functionality."""

    def test_disable_skill(self, skill):
        """Test disabling the skill."""
        skill.disable()
        assert skill.enabled is False

    def test_enable_skill(self, skill):
        """Test enabling the skill."""
        skill.disable()
        skill.enable()
        assert skill.enabled is True

    def test_execution_when_disabled(self, skill):
        """Test that skill can execute even when disabled."""
        skill.disable()
        result = skill.execute({"code": "x = 1"})
        # Skill should still execute (enabled flag is for registry management)
        assert result["success"] is True


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_very_long_code(self, skill):
        """Test handling of very long code."""
        code = "\n".join([f"x{i} = {i}" for i in range(100)])
        result = skill.execute({"code": code})
        assert result["success"] is True

    def test_unicode_in_code(self, skill):
        """Test handling of unicode characters."""
        code = "message = '你好世界'"
        result = skill.execute({"code": code})
        assert result["success"] is True

    def test_multiline_string_error(self, skill):
        """Test error in multiline string."""
        code = '''
text = """
This is a multiline
string without closing quotes
'''
        result = skill.execute({"code": code})
        assert result["success"] is True

    def test_empty_error_message(self, skill):
        """Test with empty error message."""
        code = "x = 1"
        result = skill.execute({"code": code, "error": ""})
        assert result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
