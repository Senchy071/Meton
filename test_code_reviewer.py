#!/usr/bin/env python3
"""
Test suite for Code Reviewer Skill

Tests the automated code review capabilities including:
- Best practices checks (complexity, length, parameters, naming, nesting, docstrings)
- Security checks (dangerous functions, SQL injection, secrets, shell commands)
- Style checks (naming conventions, imports, type hints)
- Score calculation
- Severity levels
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from skills.code_reviewer import CodeReviewerSkill, ReviewIssue
from skills.base import SkillValidationError


def test_initialization():
    """Test Code Reviewer skill initialization."""
    print("\n" + "=" * 70)
    print("TEST: Skill Initialization")
    print("=" * 70)

    skill = CodeReviewerSkill()

    assert skill.name == "code_reviewer"
    assert skill.description == "Reviews code for best practices, security, and style compliance"
    assert skill.version == "1.0.0"
    assert skill.enabled is True

    print("✓ Skill initialized successfully")
    print(f"  Name: {skill.name}")
    print(f"  Description: {skill.description}")
    print(f"  Version: {skill.version}")


def test_clean_code():
    """Test that clean code returns score 100."""
    print("\n" + "=" * 70)
    print("TEST: Clean Code (No Issues)")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
def calculate_sum(numbers: list) -> int:
    '''Calculate sum of numbers.'''
    return sum(numbers)
"""

    result = skill.execute({"code": code})

    assert result["success"] is True
    assert result["score"] == 100
    assert result["summary"]["total_issues"] == 0

    print("✓ Clean code returns score 100")
    print(f"  Score: {result['score']}")
    print(f"  Issues: {result['summary']['total_issues']}")


def test_high_complexity():
    """Test cyclomatic complexity check."""
    print("\n" + "=" * 70)
    print("TEST: Best Practices - High Complexity")
    print("=" * 70)

    skill = CodeReviewerSkill()

    # Function with 11 decision points (> threshold of 10)
    code = """
def complex_function(x, y, z):
    if x > 0:
        return 1
    elif x < 0:
        return -1

    if y > 0:
        return 2
    elif y < 0:
        return -2

    if z > 0:
        return 3
    elif z < 0:
        return -3

    if x and y:
        return 4
    elif x or z:
        return 5

    return 0
"""

    result = skill.execute({"code": code, "checks": ["best_practices"]})

    assert result["success"] is True
    assert any("complexity" in issue["message"].lower() for issue in result["issues"])
    assert any(issue["severity"] == "MEDIUM" for issue in result["issues"])

    print("✓ Detected high complexity")
    print(f"  Issues found: {result['summary']['total_issues']}")
    print(f"  Score: {result['score']}")


def test_long_function():
    """Test function length check."""
    print("\n" + "=" * 70)
    print("TEST: Best Practices - Long Function")
    print("=" * 70)

    skill = CodeReviewerSkill()

    # Create a function with 60 lines
    lines = ["def long_function():", "    '''Long function.'''"]
    lines.extend([f"    x = {i}" for i in range(60)])
    code = "\n".join(lines)

    result = skill.execute({"code": code, "checks": ["best_practices"]})

    assert result["success"] is True
    assert any("too long" in issue["message"].lower() for issue in result["issues"])
    assert any(issue["severity"] == "LOW" for issue in result["issues"])

    print("✓ Detected long function")
    print(f"  Issues found: {result['summary']['total_issues']}")


def test_too_many_parameters():
    """Test too many parameters check."""
    print("\n" + "=" * 70)
    print("TEST: Best Practices - Too Many Parameters")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
def process_data(a, b, c, d, e, f, g):
    return a + b + c + d + e + f + g
"""

    result = skill.execute({"code": code, "checks": ["best_practices"]})

    assert result["success"] is True
    assert any("too many parameters" in issue["message"].lower() for issue in result["issues"])

    print("✓ Detected too many parameters")
    print(f"  Issues found: {result['summary']['total_issues']}")


def test_non_descriptive_names():
    """Test non-descriptive naming check."""
    print("\n" + "=" * 70)
    print("TEST: Best Practices - Non-Descriptive Names")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
def foo():
    tmp = 5
    x = 10
    return tmp + x
"""

    result = skill.execute({"code": code, "checks": ["best_practices"]})

    assert result["success"] is True
    assert any("non-descriptive" in issue["message"].lower() for issue in result["issues"])

    print("✓ Detected non-descriptive names")
    print(f"  Issues found: {result['summary']['total_issues']}")


def test_excessive_nesting():
    """Test excessive nesting check."""
    print("\n" + "=" * 70)
    print("TEST: Best Practices - Excessive Nesting")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
def nested_function():
    if True:
        if True:
            if True:
                if True:
                    if True:
                        return "deep"
"""

    result = skill.execute({"code": code, "checks": ["best_practices"]})

    assert result["success"] is True
    assert any("nesting" in issue["message"].lower() for issue in result["issues"])
    assert any(issue["severity"] == "MEDIUM" for issue in result["issues"])

    print("✓ Detected excessive nesting")
    print(f"  Issues found: {result['summary']['total_issues']}")


def test_missing_docstring():
    """Test missing docstring check."""
    print("\n" + "=" * 70)
    print("TEST: Best Practices - Missing Docstring")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
def public_function():
    return 42
"""

    result = skill.execute({"code": code, "checks": ["best_practices"]})

    assert result["success"] is True
    assert any("docstring" in issue["message"].lower() for issue in result["issues"])
    assert any(issue["severity"] == "INFO" for issue in result["issues"])

    print("✓ Detected missing docstring")
    print(f"  Issues found: {result['summary']['total_issues']}")


def test_dangerous_eval():
    """Test detection of eval()."""
    print("\n" + "=" * 70)
    print("TEST: Security - Dangerous eval()")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
def execute_code(user_input):
    return eval(user_input)
"""

    result = skill.execute({"code": code, "checks": ["security"]})

    assert result["success"] is True
    assert any("eval" in issue["message"].lower() for issue in result["issues"])
    assert any(issue["severity"] == "CRITICAL" for issue in result["issues"])

    print("✓ Detected eval() usage")
    print(f"  Severity: CRITICAL")


def test_dangerous_exec():
    """Test detection of exec()."""
    print("\n" + "=" * 70)
    print("TEST: Security - Dangerous exec()")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
def run_code(code_str):
    exec(code_str)
"""

    result = skill.execute({"code": code, "checks": ["security"]})

    assert result["success"] is True
    assert any("exec" in issue["message"].lower() for issue in result["issues"])
    assert any(issue["severity"] == "CRITICAL" for issue in result["issues"])

    print("✓ Detected exec() usage")


def test_sql_injection():
    """Test SQL injection detection."""
    print("\n" + "=" * 70)
    print("TEST: Security - SQL Injection")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return execute_query(query)
"""

    result = skill.execute({"code": code, "checks": ["security"]})

    assert result["success"] is True
    assert any("sql injection" in issue["message"].lower() for issue in result["issues"])
    assert any(issue["severity"] == "HIGH" for issue in result["issues"])

    print("✓ Detected SQL injection pattern")


def test_hardcoded_password():
    """Test hardcoded password detection."""
    print("\n" + "=" * 70)
    print("TEST: Security - Hardcoded Password")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
def connect_db():
    password = "secret123"
    api_key = "abc123xyz"
    return connect(password, api_key)
"""

    result = skill.execute({"code": code, "checks": ["security"]})

    assert result["success"] is True
    assert any("hardcoded secret" in issue["message"].lower() for issue in result["issues"])
    assert any(issue["severity"] == "HIGH" for issue in result["issues"])
    assert result["summary"]["by_severity"]["HIGH"] >= 2  # password and api_key

    print("✓ Detected hardcoded secrets")
    print(f"  Secrets found: {result['summary']['by_severity']['HIGH']}")


def test_shell_command():
    """Test shell command detection."""
    print("\n" + "=" * 70)
    print("TEST: Security - Shell Command")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
import os

def cleanup():
    os.system("rm -rf /tmp/*")
"""

    result = skill.execute({"code": code, "checks": ["security"]})

    assert result["success"] is True
    assert any("shell" in issue["message"].lower() for issue in result["issues"])
    assert any(issue["severity"] == "HIGH" for issue in result["issues"])

    print("✓ Detected shell command execution")


def test_subprocess_shell_true():
    """Test subprocess with shell=True."""
    print("\n" + "=" * 70)
    print("TEST: Security - subprocess with shell=True")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
import subprocess

def run_command(cmd):
    subprocess.call(cmd, shell=True)
"""

    result = skill.execute({"code": code, "checks": ["security"]})

    assert result["success"] is True
    assert any("shell" in issue["message"].lower() and "true" in issue["message"].lower() for issue in result["issues"])
    assert any(issue["severity"] == "HIGH" for issue in result["issues"])

    print("✓ Detected shell=True in subprocess")


def test_pickle_loads():
    """Test pickle.loads detection."""
    print("\n" + "=" * 70)
    print("TEST: Security - pickle.loads()")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
import pickle

def load_data(data):
    return pickle.loads(data)
"""

    result = skill.execute({"code": code, "checks": ["security"]})

    assert result["success"] is True
    assert any("pickle.loads" in issue["message"].lower() for issue in result["issues"])
    assert any(issue["severity"] == "MEDIUM" for issue in result["issues"])

    print("✓ Detected pickle.loads() usage")


def test_file_path_from_variable():
    """Test file path from variable detection."""
    print("\n" + "=" * 70)
    print("TEST: Security - File Path from Variable")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
def read_file(filename):
    with open(filename) as f:
        return f.read()
"""

    result = skill.execute({"code": code, "checks": ["security"]})

    assert result["success"] is True
    assert any("path" in issue["message"].lower() for issue in result["issues"])
    assert any(issue["severity"] == "MEDIUM" for issue in result["issues"])

    print("✓ Detected file path from variable")


def test_snake_case_function():
    """Test snake_case function naming."""
    print("\n" + "=" * 70)
    print("TEST: Style - Function snake_case")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
def CalculateSum():
    return 42
"""

    result = skill.execute({"code": code, "checks": ["style"]})

    assert result["success"] is True
    assert any("snake_case" in issue["message"].lower() for issue in result["issues"])
    assert any(issue["severity"] == "LOW" for issue in result["issues"])

    print("✓ Detected non-snake_case function name")


def test_pascal_case_class():
    """Test PascalCase class naming."""
    print("\n" + "=" * 70)
    print("TEST: Style - Class PascalCase")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
class my_class:
    pass
"""

    result = skill.execute({"code": code, "checks": ["style"]})

    assert result["success"] is True
    assert any("PascalCase" in issue["message"] for issue in result["issues"])
    assert any(issue["severity"] == "LOW" for issue in result["issues"])

    print("✓ Detected non-PascalCase class name")


def test_missing_type_hints():
    """Test missing type hints detection."""
    print("\n" + "=" * 70)
    print("TEST: Style - Missing Type Hints")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
def calculate(a, b):
    return a + b
"""

    result = skill.execute({"code": code, "checks": ["style"]})

    assert result["success"] is True
    assert any("type hint" in issue["message"].lower() for issue in result["issues"])
    assert any(issue["severity"] == "INFO" for issue in result["issues"])

    print("✓ Detected missing type hints")


def test_wildcard_import():
    """Test wildcard import detection."""
    print("\n" + "=" * 70)
    print("TEST: Style - Wildcard Import")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
from os import *

def test():
    pass
"""

    result = skill.execute({"code": code, "checks": ["style"]})

    assert result["success"] is True
    assert any("wildcard" in issue["message"].lower() for issue in result["issues"])
    assert any(issue["severity"] == "MEDIUM" for issue in result["issues"])

    print("✓ Detected wildcard import")


def test_unused_import():
    """Test unused import detection."""
    print("\n" + "=" * 70)
    print("TEST: Style - Unused Import")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
import os
import sys

def test():
    print("hello")
"""

    result = skill.execute({"code": code, "checks": ["style"]})

    assert result["success"] is True
    assert any("unused import" in issue["message"].lower() for issue in result["issues"])

    print("✓ Detected unused imports")
    print(f"  Issues: {result['summary']['total_issues']}")


def test_multiple_statements_one_line():
    """Test multiple statements on one line."""
    print("\n" + "=" * 70)
    print("TEST: Style - Multiple Statements One Line")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
def test():
    x = 5; y = 10; return x + y
"""

    result = skill.execute({"code": code, "checks": ["style"]})

    assert result["success"] is True
    assert any("multiple statements" in issue["message"].lower() for issue in result["issues"])
    assert any(issue["severity"] == "LOW" for issue in result["issues"])

    print("✓ Detected multiple statements on one line")


def test_selective_checks_security_only():
    """Test running only security checks."""
    print("\n" + "=" * 70)
    print("TEST: Selective Checks - Security Only")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
def CalculateSum():  # Style issue
    password = "secret"  # Security issue
    return eval("1+1")  # Security issue
"""

    result = skill.execute({"code": code, "checks": ["security"]})

    assert result["success"] is True
    assert result["summary"]["by_category"]["security"] >= 2
    assert result["summary"]["by_category"]["style"] == 0

    print("✓ Correctly ran only security checks")
    print(f"  Security issues: {result['summary']['by_category']['security']}")


def test_selective_checks_style_only():
    """Test running only style checks."""
    print("\n" + "=" * 70)
    print("TEST: Selective Checks - Style Only")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
def BadFunctionName():  # Style issue
    eval("x")  # Security issue
    return 42
"""

    result = skill.execute({"code": code, "checks": ["style"]})

    assert result["success"] is True
    assert result["summary"]["by_category"]["style"] >= 1
    assert result["summary"]["by_category"]["security"] == 0

    print("✓ Correctly ran only style checks")
    print(f"  Style issues: {result['summary']['by_category']['style']}")


def test_line_number_accuracy():
    """Test that line numbers are accurate."""
    print("\n" + "=" * 70)
    print("TEST: Line Number Accuracy")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """# Line 1
def test():  # Line 2
    x = eval("42")  # Line 3 - should be flagged
    return x
"""

    result = skill.execute({"code": code, "checks": ["security"]})

    assert result["success"] is True
    eval_issues = [i for i in result["issues"] if "eval" in i["message"].lower()]
    assert len(eval_issues) > 0
    assert eval_issues[0]["line_number"] == 3

    print("✓ Line numbers are accurate")
    print(f"  eval() found at line: {eval_issues[0]['line_number']}")


def test_score_calculation():
    """Test score calculation."""
    print("\n" + "=" * 70)
    print("TEST: Score Calculation")
    print("=" * 70)

    skill = CodeReviewerSkill()

    # Code with 1 CRITICAL (eval), 1 HIGH (password), 1 LOW (naming)
    code = """
def foo():  # LOW (non-descriptive name)
    password = "secret123"  # HIGH (hardcoded secret)
    return eval("1+1")  # CRITICAL (eval)
"""

    result = skill.execute({"code": code})

    # Score = 100 - (1*20 + 1*10 + 1*2) = 100 - 32 = 68
    # But there might be more issues (missing docstring, type hints, etc.)
    assert result["success"] is True
    assert result["score"] < 100
    assert result["score"] >= 0

    print("✓ Score calculation works")
    print(f"  Score: {result['score']}")
    print(f"  CRITICAL: {result['summary']['by_severity']['CRITICAL']}")
    print(f"  HIGH: {result['summary']['by_severity']['HIGH']}")
    print(f"  LOW: {result['summary']['by_severity']['LOW']}")


def test_severity_levels():
    """Test all severity levels are assigned correctly."""
    print("\n" + "=" * 70)
    print("TEST: Severity Levels")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
def foo():  # LOW + INFO issues
    eval("x")  # CRITICAL
    password = "secret"  # HIGH
    if True:
        if True:
            if True:
                if True:
                    if True:
                        pass  # MEDIUM (nesting)
"""

    result = skill.execute({"code": code})

    assert result["success"] is True
    assert result["summary"]["by_severity"]["CRITICAL"] >= 1
    assert result["summary"]["by_severity"]["HIGH"] >= 1
    assert result["summary"]["by_severity"]["MEDIUM"] >= 1
    assert result["summary"]["by_severity"]["LOW"] >= 1

    print("✓ All severity levels present")
    for severity, count in result["summary"]["by_severity"].items():
        if count > 0:
            print(f"  {severity}: {count}")


def test_syntax_error():
    """Test handling of syntax errors."""
    print("\n" + "=" * 70)
    print("TEST: Syntax Error Handling")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
def broken(
    missing closing parenthesis
"""

    result = skill.execute({"code": code})

    assert result["success"] is True
    assert len(result["issues"]) == 1
    assert result["issues"][0]["severity"] == "CRITICAL"
    assert "syntax error" in result["issues"][0]["message"].lower()

    print("✓ Syntax errors handled correctly")
    print(f"  Error: {result['issues'][0]['message']}")


def test_input_validation():
    """Test input validation."""
    print("\n" + "=" * 70)
    print("TEST: Input Validation")
    print("=" * 70)

    skill = CodeReviewerSkill()

    # Missing code
    result = skill.execute({})
    assert result["success"] is False
    assert "missing" in result["error"].lower()
    print("✓ Rejected missing code")

    # Empty code
    result = skill.execute({"code": "   "})
    assert result["success"] is False
    print("✓ Rejected empty code")

    # Invalid checks
    result = skill.execute({"code": "x = 1", "checks": ["invalid"]})
    assert result["success"] is False
    print("✓ Rejected invalid checks")

    # Non-list checks
    result = skill.execute({"code": "x = 1", "checks": "security"})
    assert result["success"] is False
    print("✓ Rejected non-list checks")


def test_issue_aggregation():
    """Test that issues are properly aggregated."""
    print("\n" + "=" * 70)
    print("TEST: Issue Aggregation")
    print("=" * 70)

    skill = CodeReviewerSkill()

    code = """
def test():
    x = 1  # Non-descriptive name
    y = 2  # Non-descriptive name
    tmp = 3  # Non-descriptive name
    return x + y + tmp
"""

    result = skill.execute({"code": code, "checks": ["best_practices"]})

    assert result["success"] is True
    # Should have multiple issues for non-descriptive names
    assert result["summary"]["total_issues"] >= 3

    print("✓ Issues properly aggregated")
    print(f"  Total issues: {result['summary']['total_issues']}")


def test_enable_disable():
    """Test skill enable/disable functionality."""
    print("\n" + "=" * 70)
    print("TEST: Enable/Disable Skill")
    print("=" * 70)

    skill = CodeReviewerSkill()

    assert skill.enabled is True

    skill.disable()
    assert skill.enabled is False

    skill.enable()
    assert skill.enabled is True

    print("✓ Enable/disable functionality works")


def test_get_info():
    """Test get_info method."""
    print("\n" + "=" * 70)
    print("TEST: Get Info")
    print("=" * 70)

    skill = CodeReviewerSkill()
    info = skill.get_info()

    assert info["name"] == "code_reviewer"
    assert info["version"] == "1.0.0"
    assert "enabled" in info
    assert "description" in info

    print("✓ get_info() returns correct metadata")
    print(f"  {info}")


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 80)
    print(" " * 20 + "CODE REVIEWER SKILL TEST SUITE")
    print("=" * 80)

    tests = [
        # Initialization
        ("Initialization", test_initialization),

        # Clean code
        ("Clean Code (Score 100)", test_clean_code),

        # Best Practices (7 tests)
        ("Best Practices - High Complexity", test_high_complexity),
        ("Best Practices - Long Function", test_long_function),
        ("Best Practices - Too Many Parameters", test_too_many_parameters),
        ("Best Practices - Non-Descriptive Names", test_non_descriptive_names),
        ("Best Practices - Excessive Nesting", test_excessive_nesting),
        ("Best Practices - Missing Docstring", test_missing_docstring),

        # Security (8 tests)
        ("Security - eval()", test_dangerous_eval),
        ("Security - exec()", test_dangerous_exec),
        ("Security - SQL Injection", test_sql_injection),
        ("Security - Hardcoded Password", test_hardcoded_password),
        ("Security - Shell Command", test_shell_command),
        ("Security - subprocess shell=True", test_subprocess_shell_true),
        ("Security - pickle.loads()", test_pickle_loads),
        ("Security - File Path Variable", test_file_path_from_variable),

        # Style (7 tests)
        ("Style - Function snake_case", test_snake_case_function),
        ("Style - Class PascalCase", test_pascal_case_class),
        ("Style - Missing Type Hints", test_missing_type_hints),
        ("Style - Wildcard Import", test_wildcard_import),
        ("Style - Unused Import", test_unused_import),
        ("Style - Multiple Statements", test_multiple_statements_one_line),

        # Selective Checks (2 tests)
        ("Selective - Security Only", test_selective_checks_security_only),
        ("Selective - Style Only", test_selective_checks_style_only),

        # Additional Tests (6 tests)
        ("Line Number Accuracy", test_line_number_accuracy),
        ("Score Calculation", test_score_calculation),
        ("Severity Levels", test_severity_levels),
        ("Syntax Error Handling", test_syntax_error),
        ("Input Validation", test_input_validation),
        ("Issue Aggregation", test_issue_aggregation),

        # Meta Tests (2 tests)
        ("Enable/Disable", test_enable_disable),
        ("Get Info", test_get_info),
    ]

    passed = 0
    failed = 0
    errors = []

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            errors.append((test_name, str(e)))
            print(f"\n✗ FAILED: {test_name}")
            print(f"  {str(e)}")
        except Exception as e:
            failed += 1
            errors.append((test_name, str(e)))
            print(f"\n✗ ERROR: {test_name}")
            print(f"  {str(e)}")

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if errors:
        print("\nFailed tests:")
        for test_name, error in errors:
            print(f"  - {test_name}: {error}")
    else:
        print("\n✅ All Code Reviewer Skill tests passed!")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
