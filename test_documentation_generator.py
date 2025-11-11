#!/usr/bin/env python3
"""
Test suite for Documentation Generator Skill

Tests the documentation generation capabilities including:
- Docstring generation (Google, NumPy, Sphinx styles)
- Function documentation
- Class documentation
- README generation
- API documentation
- Type hint handling
- Complex signatures (*args, **kwargs, defaults)
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from skills.documentation_generator import DocumentationGeneratorSkill
from skills.base import SkillValidationError, SkillExecutionError


def test_initialization():
    """Test Documentation Generator skill initialization."""
    print("\n" + "=" * 70)
    print("TEST: Skill Initialization")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    assert skill.name == "documentation_generator"
    assert skill.description == "Generates docstrings, README files, and API documentation"
    assert skill.version == "1.0.0"
    assert skill.enabled is True

    print("✓ Skill initialized successfully")
    print(f"  Name: {skill.name}")
    print(f"  Description: {skill.description}")
    print(f"  Version: {skill.version}")


def test_input_validation_missing_doc_type():
    """Test validation for missing doc_type."""
    print("\n" + "=" * 70)
    print("TEST: Input Validation - Missing doc_type")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    try:
        skill.validate_input({"code": "def foo(): pass"})
        assert False, "Should raise validation error"
    except SkillValidationError as e:
        print("✓ Correctly rejected missing doc_type")
        print(f"  Error: {str(e)}")


def test_input_validation_invalid_doc_type():
    """Test validation for invalid doc_type."""
    print("\n" + "=" * 70)
    print("TEST: Input Validation - Invalid doc_type")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    try:
        skill.validate_input({"doc_type": "invalid", "code": "def foo(): pass"})
        assert False, "Should raise validation error"
    except SkillValidationError as e:
        print("✓ Correctly rejected invalid doc_type")
        print(f"  Error: {str(e)}")


def test_input_validation_missing_code():
    """Test validation for missing code field."""
    print("\n" + "=" * 70)
    print("TEST: Input Validation - Missing Code")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    try:
        skill.validate_input({"doc_type": "docstring"})
        assert False, "Should raise validation error"
    except SkillValidationError as e:
        print("✓ Correctly rejected missing code")
        print(f"  Error: {str(e)}")


def test_input_validation_invalid_style():
    """Test validation for invalid docstring style."""
    print("\n" + "=" * 70)
    print("TEST: Input Validation - Invalid Style")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    try:
        skill.validate_input({
            "doc_type": "docstring",
            "code": "def foo(): pass",
            "style": "invalid"
        })
        assert False, "Should raise validation error"
    except SkillValidationError as e:
        print("✓ Correctly rejected invalid style")
        print(f"  Error: {str(e)}")


def test_input_validation_empty_code():
    """Test validation for empty code."""
    print("\n" + "=" * 70)
    print("TEST: Input Validation - Empty Code")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    try:
        skill.validate_input({"doc_type": "docstring", "code": "   "})
        assert False, "Should raise validation error"
    except SkillValidationError as e:
        print("✓ Correctly rejected empty code")
        print(f"  Error: {str(e)}")


def test_simple_function_google():
    """Test Google-style docstring for simple function."""
    print("\n" + "=" * 70)
    print("TEST: Simple Function - Google Style")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    code = """
def add(a, b):
    return a + b
"""

    result = skill.execute({
        "doc_type": "docstring",
        "code": code,
        "style": "google"
    })

    assert result["success"] is True
    assert result["doc_count"] == 1
    assert result["style"] == "google"
    assert "Args:" in result["documentation"]
    assert "Returns:" not in result["documentation"]  # No type hint

    print("✓ Generated Google-style docstring")
    print(f"  Doc count: {result['doc_count']}")
    print(f"\n{result['documentation']}")


def test_simple_function_numpy():
    """Test NumPy-style docstring for simple function."""
    print("\n" + "=" * 70)
    print("TEST: Simple Function - NumPy Style")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    code = """
def multiply(x, y):
    return x * y
"""

    result = skill.execute({
        "doc_type": "docstring",
        "code": code,
        "style": "numpy"
    })

    assert result["success"] is True
    assert result["doc_count"] == 1
    assert result["style"] == "numpy"
    assert "Parameters" in result["documentation"]
    assert "----------" in result["documentation"]

    print("✓ Generated NumPy-style docstring")
    print(f"  Doc count: {result['doc_count']}")
    print(f"\n{result['documentation']}")


def test_simple_function_sphinx():
    """Test Sphinx-style docstring for simple function."""
    print("\n" + "=" * 70)
    print("TEST: Simple Function - Sphinx Style")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    code = """
def divide(a, b):
    return a / b
"""

    result = skill.execute({
        "doc_type": "docstring",
        "code": code,
        "style": "sphinx"
    })

    assert result["success"] is True
    assert result["doc_count"] == 1
    assert result["style"] == "sphinx"
    assert ":param a:" in result["documentation"]
    assert ":type a:" in result["documentation"]

    print("✓ Generated Sphinx-style docstring")
    print(f"  Doc count: {result['doc_count']}")
    print(f"\n{result['documentation']}")


def test_function_with_type_hints():
    """Test docstring generation with type hints."""
    print("\n" + "=" * 70)
    print("TEST: Function with Type Hints")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    code = """
def greet(name: str, age: int) -> str:
    return f"Hello {name}, you are {age} years old"
"""

    result = skill.execute({
        "doc_type": "docstring",
        "code": code,
        "style": "google"
    })

    assert result["success"] is True
    assert "(str)" in result["documentation"]
    assert "(int)" in result["documentation"]
    assert "Returns:" in result["documentation"]
    assert "str:" in result["documentation"]

    print("✓ Generated docstring with type hints")
    print(f"\n{result['documentation']}")


def test_function_with_defaults():
    """Test docstring with default parameters."""
    print("\n" + "=" * 70)
    print("TEST: Function with Default Parameters")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    code = """
def create_user(name: str, age: int = 18, active: bool = True):
    pass
"""

    result = skill.execute({
        "doc_type": "docstring",
        "code": code,
        "style": "google"
    })

    assert result["success"] is True
    assert "optional" in result["documentation"]
    assert "Defaults to 18" in result["documentation"]
    assert "Defaults to True" in result["documentation"]

    print("✓ Generated docstring with defaults")
    print(f"\n{result['documentation']}")


def test_function_with_args_kwargs():
    """Test docstring with *args and **kwargs."""
    print("\n" + "=" * 70)
    print("TEST: Function with *args and **kwargs")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    code = """
def process_data(name, *args, **kwargs):
    pass
"""

    result = skill.execute({
        "doc_type": "docstring",
        "code": code,
        "style": "google"
    })

    assert result["success"] is True
    assert "*args" in result["documentation"]
    assert "**kwargs" in result["documentation"]

    print("✓ Generated docstring with *args/**kwargs")
    print(f"\n{result['documentation']}")


def test_async_function():
    """Test docstring for async function."""
    print("\n" + "=" * 70)
    print("TEST: Async Function")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    code = """
async def fetch_data(url: str) -> dict:
    return {}
"""

    result = skill.execute({
        "doc_type": "docstring",
        "code": code,
        "style": "google"
    })

    assert result["success"] is True
    assert "Async Function: fetch_data" in result["documentation"]
    assert "Asynchronously" in result["documentation"]

    print("✓ Generated docstring for async function")
    print(f"\n{result['documentation']}")


def test_function_with_raises():
    """Test docstring with exception raising."""
    print("\n" + "=" * 70)
    print("TEST: Function with Exceptions")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    code = """
def validate_age(age: int) -> bool:
    if age < 0:
        raise ValueError("Age cannot be negative")
    if age > 150:
        raise ValueError("Age too high")
    return True
"""

    result = skill.execute({
        "doc_type": "docstring",
        "code": code,
        "style": "google"
    })

    assert result["success"] is True
    assert "Raises:" in result["documentation"]
    assert "ValueError" in result["documentation"]

    print("✓ Generated docstring with exceptions")
    print(f"\n{result['documentation']}")


def test_class_docstring():
    """Test docstring generation for class."""
    print("\n" + "=" * 70)
    print("TEST: Class Documentation")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    code = """
class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b
"""

    result = skill.execute({
        "doc_type": "docstring",
        "code": code,
        "style": "google"
    })

    assert result["success"] is True
    assert result["doc_count"] == 3  # Class + 2 methods
    assert "Class: Calculator" in result["documentation"]
    assert "with 2 method(s)" in result["documentation"]

    print("✓ Generated class docstring")
    print(f"  Doc count: {result['doc_count']}")
    print(f"\n{result['documentation']}")


def test_class_with_inheritance():
    """Test docstring for class with inheritance."""
    print("\n" + "=" * 70)
    print("TEST: Class with Inheritance")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    code = """
class Animal:
    pass

class Dog(Animal):
    def bark(self):
        pass
"""

    result = skill.execute({
        "doc_type": "docstring",
        "code": code,
        "style": "google"
    })

    assert result["success"] is True
    assert "inherits from Animal" in result["documentation"]

    print("✓ Generated docstring with inheritance")
    print(f"\n{result['documentation']}")


def test_empty_function():
    """Test docstring for empty function."""
    print("\n" + "=" * 70)
    print("TEST: Empty Function")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    code = """
def empty():
    pass
"""

    result = skill.execute({
        "doc_type": "docstring",
        "code": code,
        "style": "google"
    })

    assert result["success"] is True
    assert "Empty" in result["documentation"]

    print("✓ Generated docstring for empty function")
    print(f"\n{result['documentation']}")


def test_function_no_params():
    """Test docstring for function with no parameters."""
    print("\n" + "=" * 70)
    print("TEST: Function with No Parameters")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    code = """
def get_timestamp() -> float:
    import time
    return time.time()
"""

    result = skill.execute({
        "doc_type": "docstring",
        "code": code,
        "style": "google"
    })

    assert result["success"] is True
    assert "Args:" not in result["documentation"]
    assert "Returns:" in result["documentation"]

    print("✓ Generated docstring for parameterless function")
    print(f"\n{result['documentation']}")


def test_syntax_error():
    """Test handling of syntax errors."""
    print("\n" + "=" * 70)
    print("TEST: Syntax Error Handling")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    code = """
def broken(
    missing closing parenthesis
"""

    result = skill.execute({
        "doc_type": "docstring",
        "code": code,
        "style": "google"
    })

    assert result["success"] is False
    assert "Syntax error" in result["error"]

    print("✓ Correctly handled syntax error")
    print(f"  Error: {result['error']}")


def test_no_functions_or_classes():
    """Test handling when no functions/classes found."""
    print("\n" + "=" * 70)
    print("TEST: No Functions or Classes")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    code = """
x = 5
y = 10
z = x + y
"""

    result = skill.execute({
        "doc_type": "docstring",
        "code": code,
        "style": "google"
    })

    assert result["success"] is False
    assert "No functions or classes found" in result["error"]

    print("✓ Correctly handled code with no functions/classes")
    print(f"  Error: {result['error']}")


def test_readme_generation():
    """Test README generation."""
    print("\n" + "=" * 70)
    print("TEST: README Generation")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    result = skill.execute({
        "doc_type": "readme",
        "project_name": "MyAwesomeProject"
    })

    assert result["success"] is True
    assert "# MyAwesomeProject" in result["documentation"]
    assert "## Overview" in result["documentation"]
    assert "## Installation" in result["documentation"]
    assert "## Usage" in result["documentation"]
    assert "## License" in result["documentation"]
    assert result["doc_count"] == 7
    assert "sections" in result

    print("✓ Generated README successfully")
    print(f"  Sections: {len(result['sections'])}")
    print(f"\nFirst 300 chars:\n{result['documentation'][:300]}...")


def test_api_docs_generation():
    """Test API documentation generation."""
    print("\n" + "=" * 70)
    print("TEST: API Documentation Generation")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    code = """
'''Module for mathematical operations.'''

def add(a: int, b: int) -> int:
    '''Add two numbers.'''
    return a + b

def subtract(a: int, b: int) -> int:
    '''Subtract b from a.'''
    return a - b

class Calculator:
    '''A simple calculator class.'''

    def multiply(self, a: int, b: int) -> int:
        '''Multiply two numbers.'''
        return a * b
"""

    result = skill.execute({
        "doc_type": "api_docs",
        "code": code
    })

    assert result["success"] is True
    assert "## Classes" in result["documentation"]
    assert "## Functions" in result["documentation"]
    assert "Calculator" in result["documentation"]
    assert "add" in result["documentation"]
    assert "subtract" in result["documentation"]
    assert result["classes"] == 1
    assert result["functions"] == 2

    print("✓ Generated API documentation successfully")
    print(f"  Classes documented: {result['classes']}")
    print(f"  Functions documented: {result['functions']}")
    print(f"\nFirst 400 chars:\n{result['documentation'][:400]}...")


def test_api_docs_with_private_methods():
    """Test API docs excludes private methods."""
    print("\n" + "=" * 70)
    print("TEST: API Docs - Private Methods Exclusion")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    code = """
def public_function():
    pass

def _private_function():
    pass

class MyClass:
    def public_method(self):
        pass

    def _private_method(self):
        pass
"""

    result = skill.execute({
        "doc_type": "api_docs",
        "code": code
    })

    assert result["success"] is True
    assert "public_function" in result["documentation"]
    assert "_private_function" not in result["documentation"]
    assert "public_method" in result["documentation"]
    assert "_private_method" not in result["documentation"]

    print("✓ Correctly excluded private methods from API docs")
    print(f"  Total items documented: {result['doc_count']}")


def test_multiple_functions():
    """Test docstring generation for multiple functions."""
    print("\n" + "=" * 70)
    print("TEST: Multiple Functions")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    code = """
def func_one(x):
    return x * 2

def func_two(y):
    return y + 5

def func_three(z):
    return z - 3
"""

    result = skill.execute({
        "doc_type": "docstring",
        "code": code,
        "style": "google"
    })

    assert result["success"] is True
    assert result["doc_count"] == 3
    assert "func_one" in result["documentation"]
    assert "func_two" in result["documentation"]
    assert "func_three" in result["documentation"]

    print("✓ Generated docstrings for multiple functions")
    print(f"  Functions documented: {result['doc_count']}")


def test_enable_disable():
    """Test skill enable/disable functionality."""
    print("\n" + "=" * 70)
    print("TEST: Enable/Disable Skill")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

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

    skill = DocumentationGeneratorSkill()
    info = skill.get_info()

    assert info["name"] == "documentation_generator"
    assert info["version"] == "1.0.0"
    assert "enabled" in info
    assert "description" in info

    print("✓ get_info() returns correct metadata")
    print(f"  {info}")


def test_complex_signature():
    """Test function with complex signature."""
    print("\n" + "=" * 70)
    print("TEST: Complex Function Signature")
    print("=" * 70)

    skill = DocumentationGeneratorSkill()

    code = """
def complex_func(
    required_arg: str,
    optional_arg: int = 10,
    *args,
    keyword_only: bool = False,
    **kwargs
) -> dict:
    return {}
"""

    result = skill.execute({
        "doc_type": "docstring",
        "code": code,
        "style": "google"
    })

    assert result["success"] is True
    assert "required_arg" in result["documentation"]
    assert "optional_arg" in result["documentation"]
    assert "Defaults to 10" in result["documentation"]
    assert "*args" in result["documentation"]
    assert "keyword_only" in result["documentation"]
    assert "**kwargs" in result["documentation"]

    print("✓ Generated docstring for complex signature")
    print(f"\n{result['documentation']}")


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 80)
    print(" " * 15 + "DOCUMENTATION GENERATOR SKILL TEST SUITE")
    print("=" * 80)

    tests = [
        # Initialization
        ("Initialization", test_initialization),

        # Input Validation (5 tests)
        ("Input Validation - Missing doc_type", test_input_validation_missing_doc_type),
        ("Input Validation - Invalid doc_type", test_input_validation_invalid_doc_type),
        ("Input Validation - Missing Code", test_input_validation_missing_code),
        ("Input Validation - Invalid Style", test_input_validation_invalid_style),
        ("Input Validation - Empty Code", test_input_validation_empty_code),

        # Docstring Styles (3 tests)
        ("Simple Function - Google", test_simple_function_google),
        ("Simple Function - NumPy", test_simple_function_numpy),
        ("Simple Function - Sphinx", test_simple_function_sphinx),

        # Function Features (7 tests)
        ("Function with Type Hints", test_function_with_type_hints),
        ("Function with Defaults", test_function_with_defaults),
        ("Function with *args/**kwargs", test_function_with_args_kwargs),
        ("Async Function", test_async_function),
        ("Function with Exceptions", test_function_with_raises),
        ("Empty Function", test_empty_function),
        ("Function No Parameters", test_function_no_params),

        # Class Features (2 tests)
        ("Class Documentation", test_class_docstring),
        ("Class with Inheritance", test_class_with_inheritance),

        # Error Handling (2 tests)
        ("Syntax Error Handling", test_syntax_error),
        ("No Functions/Classes", test_no_functions_or_classes),

        # README & API (3 tests)
        ("README Generation", test_readme_generation),
        ("API Docs Generation", test_api_docs_generation),
        ("API Docs Private Exclusion", test_api_docs_with_private_methods),

        # Additional Tests (3 tests)
        ("Multiple Functions", test_multiple_functions),
        ("Complex Signature", test_complex_signature),

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
        print("\n✅ All Documentation Generator Skill tests passed!")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
