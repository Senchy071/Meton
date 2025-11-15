#!/usr/bin/env python3
"""Test suite for Code Explainer Skill.

This module tests the CodeExplainerSkill functionality including:
- Simple function explanation
- Complex class analysis
- Async code detection
- Recursion detection
- Import handling
- Syntax error handling
- Pattern detection
- Complexity assessment
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from skills.code_explainer import CodeExplainerSkill
from skills.base import SkillValidationError, SkillExecutionError


def test_initialization():
    """Test skill initialization."""
    print("\n1. Testing Skill Initialization...")

    skill = CodeExplainerSkill()

    assert skill.name == "code_explainer"
    assert skill.version == "1.0.0"
    assert skill.enabled is True
    assert "code" in skill.description.lower()

    info = skill.get_info()
    assert info["name"] == "code_explainer"
    assert info["enabled"] is True

    print("✓ Skill initialized correctly")


def test_simple_function():
    """Test explanation of simple function."""
    print("\n2. Testing Simple Function Explanation...")

    skill = CodeExplainerSkill()

    code = """
def add_numbers(a, b):
    '''Add two numbers together.'''
    return a + b
"""

    result = skill.execute({"code": code})

    assert result["success"] is True
    assert "summary" in result
    assert "detailed_explanation" in result
    assert "key_concepts" in result
    assert "complexity" in result
    assert "suggestions" in result

    # Check summary
    assert "function" in result["summary"].lower()

    # Check complexity
    assert result["complexity"] in ["simple", "moderate", "complex"]
    assert result["complexity"] == "simple"  # Simple function should be "simple"

    # Check key concepts
    assert "functions" in result["key_concepts"]

    print(f"✓ Simple function explained successfully")
    print(f"  Summary: {result['summary']}")
    print(f"  Complexity: {result['complexity']}")
    print(f"  Key concepts: {', '.join(result['key_concepts'])}")


def test_complex_class():
    """Test explanation of complex class with methods."""
    print("\n3. Testing Complex Class Analysis...")

    skill = CodeExplainerSkill()

    code = """
class Calculator:
    '''A simple calculator class.'''

    def __init__(self):
        self.result = 0

    def add(self, x, y):
        '''Add two numbers.'''
        self.result = x + y
        return self.result

    def subtract(self, x, y):
        '''Subtract y from x.'''
        self.result = x - y
        return self.result

    def multiply(self, x, y):
        '''Multiply two numbers.'''
        self.result = x * y
        return self.result
"""

    result = skill.execute({"code": code})

    assert result["success"] is True
    assert "class" in result["summary"].lower()

    # Check key concepts include OOP concepts
    concepts = result["key_concepts"]
    assert "classes" in concepts or "object-oriented programming" in concepts

    # Check detailed explanation mentions methods
    assert "method" in result["detailed_explanation"].lower()

    print(f"✓ Complex class analyzed successfully")
    print(f"  Summary: {result['summary']}")
    print(f"  Key concepts: {', '.join(result['key_concepts'])}")


def test_async_code():
    """Test detection of async code."""
    print("\n4. Testing Async Code Detection...")

    skill = CodeExplainerSkill()

    code = """
import asyncio

async def fetch_data(url):
    '''Fetch data from URL asynchronously.'''
    await asyncio.sleep(1)
    return f"Data from {url}"

async def main():
    result = await fetch_data("https://example.com")
    return result
"""

    result = skill.execute({"code": code})

    assert result["success"] is True

    # Check async is detected
    assert "async" in result["summary"].lower() or "async" in result["detailed_explanation"].lower()

    # Check key concepts include async
    concepts_str = " ".join(result["key_concepts"])
    assert "async" in concepts_str.lower()

    print(f"✓ Async code detected successfully")
    print(f"  Summary: {result['summary']}")
    print(f"  Async concepts: {[c for c in result['key_concepts'] if 'async' in c.lower()]}")


def test_recursive_function():
    """Test detection of recursive functions."""
    print("\n5. Testing Recursive Function Detection...")

    skill = CodeExplainerSkill()

    code = """
def factorial(n):
    '''Calculate factorial recursively.'''
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""

    result = skill.execute({"code": code})

    assert result["success"] is True

    # Check recursion is detected
    summary_and_explanation = result["summary"] + " " + result["detailed_explanation"]
    assert "recurs" in summary_and_explanation.lower()

    # Check key concepts include recursion
    assert "recursion" in result["key_concepts"]

    print(f"✓ Recursive function detected successfully")
    print(f"  Summary: {result['summary']}")


def test_code_with_imports():
    """Test handling of code with imports."""
    print("\n6. Testing Code with Imports...")

    skill = CodeExplainerSkill()

    code = """
import os
import sys
from pathlib import Path
from typing import List, Dict

def get_files(directory: str) -> List[str]:
    '''Get all files in directory.'''
    path = Path(directory)
    return [str(f) for f in path.glob("*")]
"""

    result = skill.execute({"code": code})

    assert result["success"] is True

    # Check imports are mentioned
    assert "import" in result["summary"].lower() or "import" in result["detailed_explanation"].lower()

    # Check detailed explanation mentions dependencies
    assert "import" in result["detailed_explanation"].lower() or "dependencies" in result["detailed_explanation"].lower()

    print(f"✓ Code with imports analyzed successfully")
    print(f"  Summary: {result['summary']}")


def test_invalid_syntax():
    """Test handling of invalid syntax."""
    print("\n7. Testing Invalid Syntax Handling...")

    skill = CodeExplainerSkill()

    code = """
def broken_function(
    print("This is invalid syntax"
"""

    result = skill.execute({"code": code})

    # Should still return a result, but with success=False
    assert result["success"] is False
    assert "error" in result
    assert "syntax" in result["error"].lower()
    assert result["complexity"] == "unknown"

    print(f"✓ Invalid syntax handled gracefully")
    print(f"  Error message: {result['error']}")


def test_input_validation():
    """Test input validation."""
    print("\n8. Testing Input Validation...")

    skill = CodeExplainerSkill()

    # Test missing code field
    result = skill.execute({"language": "python"})
    assert result["success"] is False
    assert "code" in result["error"].lower()

    # Test empty code
    result = skill.execute({"code": ""})
    assert result["success"] is False
    assert "empty" in result["error"].lower()

    # Test non-string code
    result = skill.execute({"code": 123})
    assert result["success"] is False
    assert "string" in result["error"].lower()

    # Test unsupported language
    result = skill.execute({"code": "print('hello')", "language": "java"})
    assert result["success"] is False
    assert "unsupported" in result["error"].lower()

    print("✓ Input validation works correctly")


def test_pattern_detection():
    """Test detection of various code patterns."""
    print("\n9. Testing Pattern Detection...")

    skill = CodeExplainerSkill()

    # Code with multiple patterns
    code = """
def process_data(items):
    '''Process items with various patterns.'''
    # List comprehension
    filtered = [x for x in items if x > 0]

    # Loop
    for item in filtered:
        print(item)

    # Exception handling
    try:
        result = sum(filtered)
    except Exception as e:
        print(f"Error: {e}")
        result = 0

    # Lambda
    double = lambda x: x * 2

    # Context manager
    with open("output.txt", "w") as f:
        f.write(str(result))

    return result
"""

    result = skill.execute({"code": code})

    assert result["success"] is True

    # Check various patterns are detected
    concepts = result["key_concepts"]
    assert "loops" in concepts or "iteration" in concepts
    assert "exception handling" in concepts
    assert "lambda functions" in concepts
    assert "context managers" in concepts
    assert "list comprehensions" in concepts

    print(f"✓ Multiple patterns detected successfully")
    print(f"  Patterns found: {', '.join(concepts)}")


def test_complexity_assessment():
    """Test complexity assessment."""
    print("\n10. Testing Complexity Assessment...")

    skill = CodeExplainerSkill()

    # Simple code
    simple_code = "x = 1 + 2"
    result = skill.execute({"code": simple_code})
    assert result["complexity"] == "simple"

    # Moderate complexity code
    moderate_code = """
def calculate(x, y, operation):
    if operation == 'add':
        return x + y
    elif operation == 'subtract':
        return x - y
    elif operation == 'multiply':
        return x * y
    else:
        return x / y
"""
    result = skill.execute({"code": moderate_code})
    assert result["complexity"] in ["simple", "moderate"]

    # Complex code
    complex_code = """
def complex_function(data):
    result = []
    for item in data:
        if item > 0:
            for i in range(item):
                if i % 2 == 0:
                    result.append(i)
                elif i % 3 == 0:
                    result.append(i * 2)
                else:
                    result.append(i * 3)
        elif item < 0:
            for i in range(abs(item)):
                if i % 2 == 0:
                    result.append(-i)
    return result
"""
    result = skill.execute({"code": complex_code})
    assert result["complexity"] in ["moderate", "complex"]

    print(f"✓ Complexity assessment works correctly")
    print(f"  Simple: simple")
    print(f"  Moderate: {result['complexity']}")


def test_suggestions_generation():
    """Test generation of improvement suggestions."""
    print("\n11. Testing Suggestions Generation...")

    skill = CodeExplainerSkill()

    # Code without docstrings
    code_no_docs = """
def calculate(x, y):
    return x + y
"""

    result = skill.execute({"code": code_no_docs})
    assert result["success"] is True
    assert len(result["suggestions"]) > 0

    # Should suggest adding docstrings
    suggestions_text = " ".join(result["suggestions"]).lower()
    assert "docstring" in suggestions_text or "documentation" in suggestions_text or "no immediate" in suggestions_text

    print(f"✓ Suggestions generated successfully")
    print(f"  Suggestions: {result['suggestions']}")


def test_with_context():
    """Test explanation with additional context."""
    print("\n12. Testing Explanation with Context...")

    skill = CodeExplainerSkill()

    code = """
def validate_user(user_id):
    return user_id > 0
"""

    context = "This function is part of an authentication system"

    result = skill.execute({
        "code": code,
        "context": context
    })

    assert result["success"] is True
    assert context in result["detailed_explanation"]

    print(f"✓ Context included in explanation")


def test_enable_disable():
    """Test enable/disable functionality."""
    print("\n13. Testing Enable/Disable...")

    skill = CodeExplainerSkill()

    assert skill.enabled is True

    skill.disable()
    assert skill.enabled is False

    skill.enable()
    assert skill.enabled is True

    print("✓ Enable/disable works correctly")


def test_generator_detection():
    """Test detection of generator functions."""
    print("\n14. Testing Generator Detection...")

    skill = CodeExplainerSkill()

    code = """
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b
"""

    result = skill.execute({"code": code})

    assert result["success"] is True
    assert "generators" in result["key_concepts"]

    print(f"✓ Generator detected successfully")


def test_decorator_detection():
    """Test detection of decorators."""
    print("\n15. Testing Decorator Detection...")

    skill = CodeExplainerSkill()

    code = """
@property
def name(self):
    return self._name

@staticmethod
def helper():
    return 42
"""

    result = skill.execute({"code": code})

    assert result["success"] is True
    assert "decorators" in result["key_concepts"]

    print(f"✓ Decorators detected successfully")


def run_all_tests():
    """Run all test cases."""
    print("=" * 60)
    print("CODE EXPLAINER SKILL TEST SUITE")
    print("=" * 60)

    tests = [
        test_initialization,
        test_simple_function,
        test_complex_class,
        test_async_code,
        test_recursive_function,
        test_code_with_imports,
        test_invalid_syntax,
        test_input_validation,
        test_pattern_detection,
        test_complexity_assessment,
        test_suggestions_generation,
        test_with_context,
        test_enable_disable,
        test_generator_detection,
        test_decorator_detection
    ]

    passed = 0
    failed = 0
    errors = []

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            failed += 1
            errors.append(f"{test.__name__}: {str(e)}")
            print(f"✗ {test.__name__} FAILED: {str(e)}")
        except Exception as e:
            failed += 1
            errors.append(f"{test.__name__}: {str(e)}")
            print(f"✗ {test.__name__} ERROR: {str(e)}")

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")

    print("=" * 60)

    if failed == 0:
        print("✅ All Code Explainer Skill tests passed!")
        return True
    else:
        print(f"❌ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
