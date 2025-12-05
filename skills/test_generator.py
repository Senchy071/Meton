#!/usr/bin/env python3
"""
Test Generator Skill

Automatically generates unit tests for Python code with support for:
- pytest and unittest frameworks
- Happy path, edge cases, and error cases
- Mocking for external dependencies
- Async functions
- Parametrized tests
- Multiple coverage levels
"""

import ast
import re
from typing import Dict, List, Any, Optional, Tuple
from skills.base import BaseSkill, SkillValidationError, SkillExecutionError


class TestGeneratorSkill(BaseSkill):
    """
    Skill for automatically generating unit tests for Python code.

    Analyzes code structure and generates appropriate test cases covering:
    - Happy path (normal operation)
    - Edge cases (boundaries, empty, None)
    - Error cases (exceptions, invalid inputs)
    - Mocking for external dependencies

    Supports pytest and unittest frameworks with configurable coverage levels.
    """

    name = "test_generator"
    description = "Automatically generate unit tests for Python code"
    version = "1.0.0"

    def __init__(self):
        """Initialize the Test Generator skill."""
        super().__init__()
        self._test_cases: List[Dict[str, str]] = []
        self._imports_needed: set = set()
        self._test_code_lines: List[str] = []

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data for test generation.

        Args:
            input_data: Dictionary containing code and optional parameters

        Returns:
            True if validation passes

        Raises:
            SkillValidationError: If input is invalid
        """
        if not isinstance(input_data, dict):
            raise SkillValidationError("Input must be a dictionary")

        if "code" not in input_data:
            raise SkillValidationError("Missing required field: 'code'")

        if not isinstance(input_data["code"], str):
            raise SkillValidationError("Field 'code' must be a string")

        if not input_data["code"].strip():
            raise SkillValidationError("Field 'code' cannot be empty")

        # Validate framework if provided
        if "framework" in input_data:
            if input_data["framework"] not in ["pytest", "unittest"]:
                raise SkillValidationError("Field 'framework' must be 'pytest' or 'unittest'")

        # Validate coverage_level if provided
        if "coverage_level" in input_data:
            if input_data["coverage_level"] not in ["basic", "standard", "comprehensive"]:
                raise SkillValidationError(
                    "Field 'coverage_level' must be 'basic', 'standard', or 'comprehensive'"
                )

        return True

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate unit tests for the provided code.

        Args:
            input_data: Dictionary containing:
                - code: Source code to test
                - framework: "pytest" or "unittest" (default: "pytest")
                - coverage_level: "basic", "standard", or "comprehensive" (default: "standard")

        Returns:
            Dictionary containing:
                - success: bool
                - test_code: Generated test code
                - test_count: Number of tests generated
                - test_cases: List of test case metadata
                - imports_needed: List of required imports
                - coverage_estimate: Estimated coverage percentage
                - notes: Additional testing recommendations
                - error: Error message if success is False
        """
        if not self.enabled:
            raise SkillExecutionError("Test Generator skill is disabled")

        # Validate input
        self.validate_input(input_data)

        # Extract parameters
        code = input_data["code"]
        framework = input_data.get("framework", "pytest")
        coverage_level = input_data.get("coverage_level", "standard")

        # Reset state
        self._test_cases = []
        self._imports_needed = set()
        self._test_code_lines = []

        try:
            # Parse the code
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "success": False,
                "error": f"Syntax error in code: {str(e)}"
            }

        # Analyze code structure
        functions = self._extract_functions(tree)
        classes = self._extract_classes(tree)
        imports = self._extract_imports(tree)

        # Add framework-specific imports
        if framework == "pytest":
            self._imports_needed.add("pytest")
        else:
            self._imports_needed.add("unittest")

        # Generate tests based on coverage level
        if functions:
            self._generate_function_tests(functions, framework, coverage_level, imports)

        if classes:
            self._generate_class_tests(classes, framework, coverage_level, imports)

        # Build final test code
        test_code = self._build_test_code(framework)

        # Calculate coverage estimate
        coverage_estimate = self._estimate_coverage(coverage_level, len(functions), len(classes))

        # Generate notes
        notes = self._generate_notes(functions, classes, coverage_level)

        return {
            "success": True,
            "test_code": test_code,
            "test_count": len(self._test_cases),
            "test_cases": self._test_cases,
            "imports_needed": sorted(list(self._imports_needed)),
            "coverage_estimate": coverage_estimate,
            "notes": notes
        }

    def _extract_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract function information from AST."""
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Skip nested functions (methods will be handled in classes)
                if not any(isinstance(parent, ast.ClassDef)
                          for parent in ast.walk(tree)
                          if hasattr(parent, 'body') and node in parent.body):

                    func_info = {
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "defaults": len(node.args.defaults),
                        "returns": ast.unparse(node.returns) if node.returns else None,
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                        "docstring": ast.get_docstring(node),
                        "decorators": [ast.unparse(d) for d in node.decorator_list],
                        "raises": self._extract_exceptions(node),
                        "calls": self._extract_calls(node)
                    }
                    functions.append(func_info)

        return functions

    def _extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract class information from AST."""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_info = {
                            "name": item.name,
                            "args": [arg.arg for arg in item.args.args],
                            "is_async": isinstance(item, ast.AsyncFunctionDef),
                            "decorators": [ast.unparse(d) for d in item.decorator_list],
                            "raises": self._extract_exceptions(item)
                        }
                        methods.append(method_info)

                class_info = {
                    "name": node.name,
                    "bases": [ast.unparse(base) for base in node.bases],
                    "methods": methods,
                    "docstring": ast.get_docstring(node)
                }
                classes.append(class_info)

        return classes

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements from AST."""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return imports

    def _extract_exceptions(self, node: ast.FunctionDef) -> List[str]:
        """Extract exceptions that might be raised in a function."""
        exceptions = []

        for child in ast.walk(node):
            if isinstance(child, ast.Raise):
                if child.exc:
                    if isinstance(child.exc, ast.Call):
                        if isinstance(child.exc.func, ast.Name):
                            exceptions.append(child.exc.func.id)
                    elif isinstance(child.exc, ast.Name):
                        exceptions.append(child.exc.id)

        return exceptions

    def _extract_calls(self, node: ast.FunctionDef) -> List[str]:
        """Extract function calls to detect dependencies."""
        calls = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(ast.unparse(child.func))

        return calls

    def _generate_function_tests(
        self,
        functions: List[Dict[str, Any]],
        framework: str,
        coverage_level: str,
        imports: List[str]
    ) -> None:
        """Generate tests for functions."""
        for func in functions:
            func_name = func["name"]

            # Generate happy path test
            self._generate_happy_path_test(func, framework)

            # Generate edge case tests based on coverage level
            if coverage_level in ["standard", "comprehensive"]:
                self._generate_edge_case_tests(func, framework)

            # Generate error case tests
            if func["raises"] and coverage_level in ["standard", "comprehensive"]:
                self._generate_error_case_tests(func, framework)

            # Generate mock tests if external calls detected
            if coverage_level == "comprehensive" and func["calls"]:
                needs_mocking = self._needs_mocking(func["calls"], imports)
                if needs_mocking:
                    self._generate_mock_tests(func, framework, needs_mocking)

            # Generate async tests
            if func["is_async"]:
                if framework == "pytest":
                    self._imports_needed.add("pytest-asyncio")

    def _generate_class_tests(
        self,
        classes: List[Dict[str, Any]],
        framework: str,
        coverage_level: str,
        imports: List[str]
    ) -> None:
        """Generate tests for classes."""
        for cls in classes:
            # Test initialization
            self._generate_class_init_test(cls, framework)

            # Test methods
            for method in cls["methods"]:
                if method["name"] not in ["__init__", "__str__", "__repr__"]:
                    self._generate_method_test(cls, method, framework, coverage_level)

    def _generate_happy_path_test(self, func: Dict[str, Any], framework: str) -> None:
        """Generate a happy path test."""
        func_name = func["name"]
        test_name = f"test_{func_name}_happy_path"

        self._test_cases.append({
            "name": test_name,
            "description": f"Test {func_name} with valid inputs",
            "type": "happy_path"
        })

        if framework == "pytest":
            self._test_code_lines.append(f"def {test_name}():")
            self._test_code_lines.append(f"    \"\"\"Test {func_name} with valid inputs.\"\"\"")

            # Generate sample call
            if func["args"]:
                # Create sample arguments
                args_str = ", ".join(self._generate_sample_arg(arg) for arg in func["args"])
                self._test_code_lines.append(f"    result = {func_name}({args_str})")
                self._test_code_lines.append(f"    assert result is not None")
            else:
                self._test_code_lines.append(f"    result = {func_name}()")
                self._test_code_lines.append(f"    assert result is not None")

            self._test_code_lines.append("")
        else:  # unittest
            # Will be added to a test class later
            pass

    def _generate_edge_case_tests(self, func: Dict[str, Any], framework: str) -> None:
        """Generate edge case tests."""
        func_name = func["name"]

        if not func["args"]:
            return

        # Test with None values
        test_name = f"test_{func_name}_with_none"
        self._test_cases.append({
            "name": test_name,
            "description": f"Test {func_name} with None values",
            "type": "edge_case"
        })

        if framework == "pytest":
            self._test_code_lines.append(f"def {test_name}():")
            self._test_code_lines.append(f"    \"\"\"Test {func_name} with None values.\"\"\"")
            self._test_code_lines.append(f"    # Test behavior with None")
            args_str = ", ".join("None" for _ in func["args"])
            self._test_code_lines.append(f"    result = {func_name}({args_str})")
            self._test_code_lines.append(f"    # Add assertions based on expected behavior")
            self._test_code_lines.append("")

        # Test with empty values
        test_name = f"test_{func_name}_with_empty"
        self._test_cases.append({
            "name": test_name,
            "description": f"Test {func_name} with empty values",
            "type": "edge_case"
        })

        if framework == "pytest":
            self._test_code_lines.append(f"def {test_name}():")
            self._test_code_lines.append(f"    \"\"\"Test {func_name} with empty values.\"\"\"")
            self._test_code_lines.append(f"    # Test behavior with empty values")
            args_str = ", ".join(self._generate_empty_value(arg) for arg in func["args"])
            self._test_code_lines.append(f"    result = {func_name}({args_str})")
            self._test_code_lines.append(f"    # Add assertions based on expected behavior")
            self._test_code_lines.append("")

    def _generate_error_case_tests(self, func: Dict[str, Any], framework: str) -> None:
        """Generate error case tests for functions that raise exceptions."""
        func_name = func["name"]

        for exception in func["raises"]:
            test_name = f"test_{func_name}_raises_{exception.lower()}"
            self._test_cases.append({
                "name": test_name,
                "description": f"Test {func_name} raises {exception}",
                "type": "error_case"
            })

            if framework == "pytest":
                self._test_code_lines.append(f"def {test_name}():")
                self._test_code_lines.append(f"    \"\"\"Test {func_name} raises {exception}.\"\"\"")
                self._test_code_lines.append(f"    with pytest.raises({exception}):")

                # Generate invalid arguments
                args_str = ", ".join(self._generate_invalid_arg(arg) for arg in func["args"])
                self._test_code_lines.append(f"        {func_name}({args_str})")
                self._test_code_lines.append("")

    def _generate_mock_tests(
        self,
        func: Dict[str, Any],
        framework: str,
        dependencies: List[str]
    ) -> None:
        """Generate tests with mocked dependencies."""
        func_name = func["name"]
        test_name = f"test_{func_name}_with_mocks"

        self._test_cases.append({
            "name": test_name,
            "description": f"Test {func_name} with mocked dependencies",
            "type": "integration"
        })

        if framework == "pytest":
            self._imports_needed.add("unittest.mock")
            self._test_code_lines.append(f"def {test_name}(mocker):")
            self._test_code_lines.append(f"    \"\"\"Test {func_name} with mocked dependencies.\"\"\"")

            # Mock dependencies
            for dep in dependencies:
                mock_name = f"mock_{dep.replace('.', '_')}"
                self._test_code_lines.append(f"    {mock_name} = mocker.patch('{dep}')")

            # Call function
            if func["args"]:
                args_str = ", ".join(self._generate_sample_arg(arg) for arg in func["args"])
                self._test_code_lines.append(f"    result = {func_name}({args_str})")
            else:
                self._test_code_lines.append(f"    result = {func_name}()")

            self._test_code_lines.append(f"    assert result is not None")
            self._test_code_lines.append("")

    def _generate_class_init_test(self, cls: Dict[str, Any], framework: str) -> None:
        """Generate test for class initialization."""
        class_name = cls["name"]
        test_name = f"test_{class_name.lower()}_initialization"

        self._test_cases.append({
            "name": test_name,
            "description": f"Test {class_name} initialization",
            "type": "happy_path"
        })

        if framework == "pytest":
            self._test_code_lines.append(f"def {test_name}():")
            self._test_code_lines.append(f"    \"\"\"Test {class_name} initialization.\"\"\"")

            # Find __init__ method
            init_method = None
            for method in cls["methods"]:
                if method["name"] == "__init__":
                    init_method = method
                    break

            if init_method and len(init_method["args"]) > 1:  # Exclude 'self'
                args = init_method["args"][1:]  # Skip 'self'
                args_str = ", ".join(self._generate_sample_arg(arg) for arg in args)
                self._test_code_lines.append(f"    obj = {class_name}({args_str})")
            else:
                self._test_code_lines.append(f"    obj = {class_name}()")

            self._test_code_lines.append(f"    assert obj is not None")
            self._test_code_lines.append(f"    assert isinstance(obj, {class_name})")
            self._test_code_lines.append("")

    def _generate_method_test(
        self,
        cls: Dict[str, Any],
        method: Dict[str, Any],
        framework: str,
        coverage_level: str
    ) -> None:
        """Generate test for a class method."""
        class_name = cls["name"]
        method_name = method["name"]
        test_name = f"test_{class_name.lower()}_{method_name}"

        self._test_cases.append({
            "name": test_name,
            "description": f"Test {class_name}.{method_name}",
            "type": "happy_path"
        })

        if framework == "pytest":
            self._test_code_lines.append(f"def {test_name}():")
            self._test_code_lines.append(f"    \"\"\"Test {class_name}.{method_name}.\"\"\"")

            # Create instance
            self._test_code_lines.append(f"    obj = {class_name}()")

            # Call method
            if len(method["args"]) > 1:  # Exclude 'self'
                args = method["args"][1:]
                args_str = ", ".join(self._generate_sample_arg(arg) for arg in args)
                self._test_code_lines.append(f"    result = obj.{method_name}({args_str})")
            else:
                self._test_code_lines.append(f"    result = obj.{method_name}()")

            self._test_code_lines.append(f"    # Add assertions based on expected behavior")
            self._test_code_lines.append("")

    def _needs_mocking(self, calls: List[str], imports: List[str]) -> List[str]:
        """Determine which calls need mocking."""
        needs_mock = []

        # Common external dependencies that should be mocked
        mock_candidates = ["requests", "urllib", "http", "socket", "open", "os."]

        for call in calls:
            # Check if it's an external call
            for candidate in mock_candidates:
                if candidate in call.lower():
                    needs_mock.append(call)
                    break

            # Check if it's from an imported module
            for imp in imports:
                if call.startswith(imp + "."):
                    needs_mock.append(call)
                    break

        return needs_mock

    def _generate_sample_arg(self, arg_name: str) -> str:
        """Generate a sample argument value based on name."""
        arg_lower = arg_name.lower()

        # Common naming patterns
        if "name" in arg_lower or "str" in arg_lower or "text" in arg_lower:
            return '"test"'
        elif "num" in arg_lower or "count" in arg_lower or "size" in arg_lower:
            return "1"
        elif "list" in arg_lower or "items" in arg_lower:
            return "[1, 2, 3]"
        elif "dict" in arg_lower or "map" in arg_lower:
            return '{"key": "value"}'
        elif "bool" in arg_lower or "flag" in arg_lower:
            return "True"
        elif "float" in arg_lower or "rate" in arg_lower:
            return "1.0"
        else:
            return '"test_value"'

    def _generate_empty_value(self, arg_name: str) -> str:
        """Generate an empty value based on argument name."""
        arg_lower = arg_name.lower()

        if "list" in arg_lower or "items" in arg_lower:
            return "[]"
        elif "dict" in arg_lower or "map" in arg_lower:
            return "{}"
        elif "str" in arg_lower or "text" in arg_lower or "name" in arg_lower:
            return '""'
        elif "num" in arg_lower or "count" in arg_lower:
            return "0"
        else:
            return '""'

    def _generate_invalid_arg(self, arg_name: str) -> str:
        """Generate an invalid argument value."""
        arg_lower = arg_name.lower()

        # Return type mismatches
        if "num" in arg_lower or "count" in arg_lower:
            return '"not_a_number"'
        elif "list" in arg_lower:
            return '"not_a_list"'
        elif "dict" in arg_lower:
            return '"not_a_dict"'
        else:
            return "None"

    def _build_test_code(self, framework: str) -> str:
        """Build the final test code."""
        lines = []

        # Add imports
        if framework == "pytest":
            lines.append("import pytest")
            if "pytest-asyncio" in self._imports_needed:
                lines.append("import pytest_asyncio")
            if "unittest.mock" in self._imports_needed:
                lines.append("from unittest.mock import Mock, patch")
        else:
            lines.append("import unittest")
            if "unittest.mock" in self._imports_needed:
                lines.append("from unittest.mock import Mock, patch")

        lines.append("")
        lines.append("# Import the code to test")
        lines.append("# from your_module import *")
        lines.append("")
        lines.append("")

        # Add test code
        if framework == "pytest":
            lines.extend(self._test_code_lines)
        else:
            # For unittest, wrap in a TestCase class
            lines.append("class TestGeneratedTests(unittest.TestCase):")
            lines.append("    \"\"\"Generated test cases.\"\"\"")
            lines.append("")

            # Convert pytest-style to unittest-style
            for line in self._test_code_lines:
                if line.startswith("def test_"):
                    lines.append("    " + line)
                elif line.strip():
                    lines.append("    " + line)
                else:
                    lines.append("")

            lines.append("")
            lines.append("")
            lines.append("if __name__ == '__main__':")
            lines.append("    unittest.main()")

        return "\n".join(lines)

    def _estimate_coverage(
        self,
        coverage_level: str,
        num_functions: int,
        num_classes: int
    ) -> str:
        """Estimate test coverage percentage."""
        base_coverage = {
            "basic": 40,
            "standard": 65,
            "comprehensive": 85
        }

        base = base_coverage.get(coverage_level, 65)

        # Adjust based on complexity
        total_items = num_functions + num_classes
        if total_items == 0:
            return "0%"

        # More items might reduce coverage slightly
        adjustment = min(10, total_items * 2)
        estimated = max(30, base - adjustment)

        return f"{estimated}%"

    def _generate_notes(
        self,
        functions: List[Dict[str, Any]],
        classes: List[Dict[str, Any]],
        coverage_level: str
    ) -> str:
        """Generate additional testing notes and recommendations."""
        notes = []

        # Check for async functions
        async_funcs = [f for f in functions if f["is_async"]]
        if async_funcs:
            notes.append("⚠ Async functions detected - ensure pytest-asyncio is installed")

        # Check for complex functions
        complex_funcs = [f for f in functions if len(f["args"]) > 5]
        if complex_funcs:
            notes.append(
                f"⚠ {len(complex_funcs)} function(s) with many parameters - "
                "consider parametrized tests"
            )

        # Check for functions with no docstring
        undocumented = [f for f in functions if not f["docstring"]]
        if undocumented:
            notes.append(
                f"💡 {len(undocumented)} function(s) without docstrings - "
                "add documentation for better tests"
            )

        # Coverage level recommendations
        if coverage_level == "basic":
            notes.append("💡 Consider 'standard' or 'comprehensive' coverage for better test quality")

        # Mocking recommendations
        external_calls = any(f["calls"] for f in functions)
        if external_calls and coverage_level != "comprehensive":
            notes.append("💡 External dependencies detected - use 'comprehensive' level for mocking")

        # Class testing recommendations
        if classes:
            notes.append("💡 Remember to test class inheritance and polymorphism if applicable")

        if not notes:
            notes.append("✅ Code structure looks good for testing")

        return " | ".join(notes)
