"""Tests for Refactoring Engine Skill.

This module tests the RefactoringEngineSkill's ability to:
- Detect refactoring opportunities
- Suggest improvements for readability, performance, and best practices
- Calculate code metrics
- Provide valid refactored code suggestions
"""

import pytest
from skills.refactoring_engine import RefactoringEngineSkill
from skills.base import SkillValidationError


@pytest.fixture
def skill():
    """Create a RefactoringEngineSkill instance."""
    return RefactoringEngineSkill()


class TestInitialization:
    """Test skill initialization."""

    def test_skill_creation(self, skill):
        """Test that skill is created with correct attributes."""
        assert skill.name == "refactoring_engine"
        assert skill.version == "1.0.0"
        assert skill.enabled is True
        assert "improv" in skill.description.lower() or "refactor" in skill.description.lower()

    def test_skill_info(self, skill):
        """Test get_info returns correct metadata."""
        info = skill.get_info()
        assert info["name"] == "refactoring_engine"
        assert info["version"] == "1.0.0"
        assert info["enabled"] is True


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

    def test_invalid_focus(self, skill):
        """Test that invalid focus raises validation error."""
        result = skill.execute({
            "code": "x = 1",
            "focus": "invalid"
        })
        assert result["success"] is False
        assert "focus" in result["error"].lower()

    def test_invalid_aggressive_type(self, skill):
        """Test that invalid aggressive type raises validation error."""
        result = skill.execute({
            "code": "x = 1",
            "aggressive": "yes"
        })
        assert result["success"] is False
        assert "aggressive" in result["error"].lower()


class TestLongFunctions:
    """Test long function detection."""

    def test_detect_long_function(self, skill):
        """Test detection of long functions."""
        code = """
def very_long_function():
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    d = 7
    e = 8
    f = 9
    g = 10
    h = 11
    i = 12
    j = 13
    k = 14
    l = 15
    m = 16
    n = 17
    o = 18
    p = 19
    q = 20
    r = 21
    return r
"""
        result = skill.execute({"code": code, "focus": "readability"})
        assert result["success"] is True
        assert len(result["refactoring_suggestions"]) > 0
        assert any(s["type"] == "extract_function" for s in result["refactoring_suggestions"])

    def test_short_function_no_suggestion(self, skill):
        """Test that short functions don't trigger suggestions."""
        code = """
def short_function():
    return 42
"""
        result = skill.execute({"code": code, "focus": "readability"})
        assert result["success"] is True
        # Should not suggest extract_function for short functions
        extract_suggestions = [s for s in result["refactoring_suggestions"] if s["type"] == "extract_function"]
        assert len(extract_suggestions) == 0


class TestNamingIssues:
    """Test naming improvement detection."""

    def test_detect_poor_variable_names(self, skill):
        """Test detection of poor variable names."""
        code = """
def calculate():
    a = 10
    b = 20
    c = a + b
    return c
"""
        result = skill.execute({"code": code, "focus": "readability"})
        assert result["success"] is True
        # Should suggest renaming
        rename_suggestions = [s for s in result["refactoring_suggestions"] if s["type"] == "rename"]
        assert len(rename_suggestions) > 0

    def test_good_names_no_suggestion(self, skill):
        """Test that good names don't trigger suggestions."""
        code = """
def calculate_total():
    subtotal = 100
    tax_rate = 0.08
    total = subtotal * (1 + tax_rate)
    return total
"""
        result = skill.execute({"code": code, "focus": "readability"})
        assert result["success"] is True
        # Good names should not trigger rename suggestions
        rename_suggestions = [s for s in result["refactoring_suggestions"] if s["type"] == "rename"]
        # Might be empty or have very few minor suggestions
        assert len(rename_suggestions) <= 1


class TestNestedConditionals:
    """Test nested conditional detection."""

    def test_detect_deeply_nested_ifs(self, skill):
        """Test detection of deeply nested if statements."""
        code = """
def process(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                if x + y + z > 10:
                    return True
    return False
"""
        result = skill.execute({"code": code, "focus": "readability"})
        assert result["success"] is True
        simplify_suggestions = [s for s in result["refactoring_suggestions"] if s["type"] == "simplify"]
        assert len(simplify_suggestions) > 0
        assert any("nested" in s["description"].lower() for s in simplify_suggestions)

    def test_shallow_nesting_ok(self, skill):
        """Test that shallow nesting doesn't trigger suggestions."""
        code = """
def check(x, y):
    if x > 0:
        if y > 0:
            return True
    return False
"""
        result = skill.execute({"code": code, "focus": "readability"})
        assert result["success"] is True
        # Shallow nesting (depth 2) should be OK
        nested_suggestions = [s for s in result["refactoring_suggestions"]
                              if "nested" in s.get("description", "").lower()]
        assert len(nested_suggestions) == 0


class TestListComprehensions:
    """Test list comprehension detection."""

    def test_detect_simple_append_loop(self, skill):
        """Test detection of simple append loops."""
        code = """
result = []
for item in items:
    result.append(item * 2)
"""
        result = skill.execute({"code": code, "focus": "readability"})
        assert result["success"] is True
        # Should suggest list comprehension
        suggestions = result["refactoring_suggestions"]
        assert len(suggestions) > 0
        # One of the suggestions should mention comprehension or simplify
        assert any("comprehension" in s["description"].lower() or
                   s["type"] == "simplify" for s in suggestions)


class TestInefficientLoops:
    """Test inefficient loop pattern detection."""

    def test_detect_range_len_pattern(self, skill):
        """Test detection of range(len()) pattern."""
        code = """
for i in range(len(items)):
    print(items[i])
"""
        result = skill.execute({"code": code, "focus": "performance"})
        assert result["success"] is True
        # Should suggest enumerate
        optimize_suggestions = [s for s in result["refactoring_suggestions"] if s["type"] == "optimize"]
        assert len(optimize_suggestions) > 0
        assert any("enumerate" in s["refactored_code"].lower() for s in optimize_suggestions)

    def test_enumerate_ok(self, skill):
        """Test that enumerate usage doesn't trigger suggestions."""
        code = """
for i, item in enumerate(items):
    print(i, item)
"""
        result = skill.execute({"code": code, "focus": "performance"})
        assert result["success"] is True
        # Should not suggest changing enumerate
        optimize_suggestions = [s for s in result["refactoring_suggestions"]
                               if "enumerate" in s.get("description", "").lower()]
        assert len(optimize_suggestions) == 0


class TestMagicNumbers:
    """Test magic number detection."""

    def test_detect_magic_numbers(self, skill):
        """Test detection of magic numbers."""
        code = """
def calculate_discount(price):
    if price > 500:
        return price * 0.15
    return price * 0.05
"""
        result = skill.execute({"code": code, "focus": "best_practices"})
        assert result["success"] is True
        # Should detect magic numbers (500, 0.15, 0.05)
        magic_suggestions = [s for s in result["refactoring_suggestions"]
                            if s["type"] == "extract_constant"]
        assert len(magic_suggestions) > 0

    def test_common_numbers_ok(self, skill):
        """Test that common numbers don't trigger suggestions."""
        code = """
def increment(x):
    return x + 1
"""
        result = skill.execute({"code": code, "focus": "best_practices"})
        assert result["success"] is True
        # Common numbers like 0, 1, 2 should not trigger suggestions
        magic_suggestions = [s for s in result["refactoring_suggestions"]
                            if s["type"] == "extract_constant"]
        assert len(magic_suggestions) == 0


class TestContextManagers:
    """Test context manager detection."""

    def test_detect_missing_context_manager(self, skill):
        """Test detection of open() without context manager."""
        code = """
def read_file():
    f = open('data.txt')
    data = f.read()
    f.close()
    return data
"""
        result = skill.execute({"code": code, "focus": "best_practices"})
        assert result["success"] is True
        # Should suggest using with statement
        cm_suggestions = [s for s in result["refactoring_suggestions"]
                         if s["type"] == "use_context_manager"]
        assert len(cm_suggestions) > 0

    def test_context_manager_ok(self, skill):
        """Test that proper context manager usage doesn't trigger suggestions."""
        code = """
def read_file():
    with open('data.txt') as f:
        data = f.read()
    return data
"""
        result = skill.execute({"code": code, "focus": "best_practices"})
        assert result["success"] is True
        # Should not suggest context manager
        cm_suggestions = [s for s in result["refactoring_suggestions"]
                         if s["type"] == "use_context_manager"]
        assert len(cm_suggestions) == 0


class TestDeadCode:
    """Test dead code detection."""

    def test_detect_unreachable_code(self, skill):
        """Test detection of unreachable code after return."""
        code = """
def calculate(x):
    if x > 0:
        return x * 2
        print("This is unreachable")
    return 0
"""
        result = skill.execute({"code": code, "focus": "best_practices"})
        assert result["success"] is True
        # Should detect unreachable code
        dead_code_suggestions = [s for s in result["refactoring_suggestions"]
                                if s["type"] == "remove_dead_code"]
        assert len(dead_code_suggestions) > 0


class TestTypeHints:
    """Test type hint detection."""

    def test_detect_missing_type_hints(self, skill):
        """Test detection of missing type hints."""
        code = """
def add_numbers(a, b):
    return a + b
"""
        result = skill.execute({"code": code, "focus": "best_practices"})
        assert result["success"] is True
        # Should suggest adding type hints
        type_hint_suggestions = [s for s in result["refactoring_suggestions"]
                                if s["type"] == "add_type_hints"]
        assert len(type_hint_suggestions) > 0

    def test_type_hints_present_ok(self, skill):
        """Test that functions with type hints don't trigger suggestions."""
        code = """
def add_numbers(a: int, b: int) -> int:
    return a + b
"""
        result = skill.execute({"code": code, "focus": "best_practices"})
        assert result["success"] is True
        # Should not suggest type hints
        type_hint_suggestions = [s for s in result["refactoring_suggestions"]
                                if s["type"] == "add_type_hints"]
        assert len(type_hint_suggestions) == 0


class TestMetrics:
    """Test metrics calculation."""

    def test_metrics_present(self, skill):
        """Test that metrics are calculated."""
        code = """
def calculate():
    if True:
        if True:
            return 1
    return 0
"""
        result = skill.execute({"code": code})
        assert result["success"] is True
        assert "metrics" in result
        metrics = result["metrics"]
        assert "complexity_before" in metrics
        assert "complexity_after" in metrics
        assert "lines_before" in metrics
        assert "lines_after" in metrics
        assert metrics["complexity_before"] > 0
        assert metrics["lines_before"] > 0

    def test_complexity_calculation(self, skill):
        """Test complexity is calculated correctly."""
        simple_code = "x = 1"
        complex_code = """
def foo():
    if True:
        if True:
            if True:
                pass
"""
        simple_result = skill.execute({"code": simple_code})
        complex_result = skill.execute({"code": complex_code})

        assert simple_result["metrics"]["complexity_before"] < complex_result["metrics"]["complexity_before"]


class TestFocusParameter:
    """Test focus parameter filtering."""

    def test_focus_readability(self, skill):
        """Test focus=readability filters suggestions."""
        code = """
def f():
    a = 10
    if a > 500:
        pass
"""
        result = skill.execute({"code": code, "focus": "readability"})
        assert result["success"] is True
        # Should focus on readability issues (naming, structure)

    def test_focus_performance(self, skill):
        """Test focus=performance filters suggestions."""
        code = """
for i in range(len(items)):
    print(items[i])
"""
        result = skill.execute({"code": code, "focus": "performance"})
        assert result["success"] is True
        # Should focus on performance issues
        assert any(s["impact"] in ["readability", "performance"]
                  for s in result["refactoring_suggestions"])

    def test_focus_best_practices(self, skill):
        """Test focus=best_practices filters suggestions."""
        code = """
f = open('file.txt')
data = f.read()
f.close()
"""
        result = skill.execute({"code": code, "focus": "best_practices"})
        assert result["success"] is True
        # Should focus on best practices
        assert len(result["refactoring_suggestions"]) > 0

    def test_focus_all(self, skill):
        """Test focus=all includes all types."""
        code = """
def f():
    a = 10
    b = 500
    if a > b:
        for i in range(len(items)):
            print(items[i])
"""
        result = skill.execute({"code": code, "focus": "all"})
        assert result["success"] is True
        # Should include various types of suggestions


class TestSummary:
    """Test summary generation."""

    def test_summary_generated(self, skill):
        """Test that summary is generated."""
        code = """
def calculate():
    a = 10
    if a > 500:
        return True
    return False
"""
        result = skill.execute({"code": code})
        assert result["success"] is True
        assert "summary" in result
        assert len(result["summary"]) > 0
        assert "refactoring" in result["summary"].lower() or "opportunity" in result["summary"].lower()

    def test_clean_code_summary(self, skill):
        """Test summary for clean code."""
        code = """
def calculate_total(subtotal: float, tax_rate: float) -> float:
    '''Calculate total with tax.'''
    return subtotal * (1 + tax_rate)
"""
        result = skill.execute({"code": code})
        assert result["success"] is True
        # Should indicate code is clean
        if not result["refactoring_suggestions"]:
            assert "well-structured" in result["summary"].lower() or "no major" in result["summary"].lower()


class TestSyntaxErrors:
    """Test handling of syntax errors."""

    def test_syntax_error_handling(self, skill):
        """Test that syntax errors are handled gracefully."""
        code = """
def broken(
    return x
"""
        result = skill.execute({"code": code})
        assert result["success"] is True
        # Should suggest fixing syntax first
        assert len(result["refactoring_suggestions"]) > 0
        assert any(s["type"] == "fix_syntax" for s in result["refactoring_suggestions"])


class TestSeverityLevels:
    """Test severity classification."""

    def test_severity_levels_assigned(self, skill):
        """Test that suggestions have severity levels."""
        code = """
def f():
    a = 10
    if a > 500:
        f = open('file.txt')
        data = f.read()
        f.close()
"""
        result = skill.execute({"code": code})
        assert result["success"] is True
        if result["refactoring_suggestions"]:
            for suggestion in result["refactoring_suggestions"]:
                assert "severity" in suggestion
                assert suggestion["severity"] in ["minor", "moderate", "major"]

    def test_suggestions_sorted_by_severity(self, skill):
        """Test that suggestions are sorted by severity."""
        code = """
def f():
    a = 10
    b = 500
    if a > b:
        if a > 100:
            if a > 50:
                f = open('file.txt')
"""
        result = skill.execute({"code": code})
        assert result["success"] is True
        if len(result["refactoring_suggestions"]) > 1:
            severities = [s["severity"] for s in result["refactoring_suggestions"]]
            severity_order = {"major": 0, "moderate": 1, "minor": 2}
            severity_values = [severity_order[s] for s in severities]
            # Should be sorted (non-decreasing)
            assert severity_values == sorted(severity_values)


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


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_function(self, skill):
        """Test handling of empty function."""
        code = """
def empty():
    pass
"""
        result = skill.execute({"code": code})
        assert result["success"] is True

    def test_very_simple_code(self, skill):
        """Test handling of very simple code."""
        code = "x = 1"
        result = skill.execute({"code": code})
        assert result["success"] is True

    def test_multiple_functions(self, skill):
        """Test handling of multiple functions."""
        code = """
def foo():
    a = 10
    return a

def bar():
    b = 20
    return b
"""
        result = skill.execute({"code": code})
        assert result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
