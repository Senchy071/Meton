"""Debugger Assistant Skill for Meton.

This skill analyzes Python errors, suggests fixes, and helps debug code including:
- Error parsing and traceback analysis
- Error type identification and location detection
- Root cause explanation
- Fix suggestions with confidence ranking
- Common pattern detection

Example:
    >>> from skills.debugger import DebuggerAssistantSkill
    >>>
    >>> skill = DebuggerAssistantSkill()
    >>> result = skill.execute({
    ...     "code": "def greet(name\\n    print(f'Hello {name}')",
    ...     "error": "SyntaxError: invalid syntax"
    ... })
    >>> print(result["error_analysis"])
"""

import ast
import re
import traceback as tb_module
from typing import Dict, Any, List, Optional, Tuple
from skills.base import BaseSkill, SkillValidationError, SkillExecutionError


class DebuggerAssistantSkill(BaseSkill):
    """Skill that analyzes errors, suggests fixes, and helps debug code.

    Analyzes Python code and errors to provide:
    - Error analysis and location
    - Root cause explanation
    - Fix suggestions with confidence ranking
    - Related issues detection

    Attributes:
        name: Skill identifier "debugger_assistant"
        description: What the skill does
        version: Skill version
        enabled: Whether skill is enabled
    """

    name = "debugger_assistant"
    description = "Analyzes errors, suggests fixes, and helps debug code"
    version = "1.0.0"
    enabled = True

    # Common error patterns for detection
    COMMON_PATTERNS = {
        "missing_colon": r"expected ':' at|SyntaxError.*:",
        "missing_parenthesis": r"unexpected EOF|unmatched '\)'",
        "undefined_variable": r"NameError.*not defined",
        "missing_import": r"NameError.*not defined|ImportError",
        "wrong_indentation": r"IndentationError|unexpected indent",
        "type_mismatch": r"TypeError.*unsupported operand|can't multiply",
        "attribute_error": r"AttributeError.*has no attribute",
        "index_error": r"IndexError.*out of range",
        "key_error": r"KeyError",
        "value_error": r"ValueError",
    }

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data.

        Args:
            input_data: Must contain "code" key with string value

        Returns:
            True if validation passes

        Raises:
            SkillValidationError: If validation fails
        """
        super().validate_input(input_data)

        if "code" not in input_data:
            raise SkillValidationError("Missing required field: 'code'")

        if not isinstance(input_data["code"], str):
            raise SkillValidationError("Field 'code' must be a string")

        if not input_data["code"].strip():
            raise SkillValidationError("Field 'code' cannot be empty")

        # Validate optional fields
        if "error" in input_data and not isinstance(input_data["error"], str):
            raise SkillValidationError("Field 'error' must be a string")

        if "error_type" in input_data:
            error_type = input_data["error_type"]
            if error_type not in ["syntax", "runtime", "logic"]:
                raise SkillValidationError(
                    f"Invalid error_type: {error_type}. Must be 'syntax', 'runtime', or 'logic'."
                )

        return True

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute error analysis and debugging assistance.

        Args:
            input_data: Dictionary with:
                - code: Source code string (required)
                - error: Error message or traceback (optional)
                - error_type: "syntax"|"runtime"|"logic" (optional)

        Returns:
            Dictionary with:
                - success: bool
                - error_analysis: What went wrong
                - error_location: {"line": int, "column": int} (if detectable)
                - cause: Root cause explanation
                - fix_suggestions: List of fix suggestions with confidence
                - related_issues: List of common related problems
                - error: Error message (if success=False)

        Raises:
            SkillExecutionError: If execution fails
        """
        try:
            # Validate input
            self.validate_input(input_data)

            code = input_data["code"]
            error_msg = input_data.get("error", "")
            error_type = input_data.get("error_type", "")

            # Analyze the error
            result = self._analyze_error(code, error_msg, error_type)

            return {
                "success": True,
                **result
            }

        except SkillValidationError as e:
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            raise SkillExecutionError(f"Debugger execution failed: {str(e)}")

    def _analyze_error(
        self,
        code: str,
        error_msg: str,
        error_type: str
    ) -> Dict[str, Any]:
        """Analyze error and generate debugging assistance.

        Args:
            code: Source code
            error_msg: Error message or traceback
            error_type: Type of error (syntax/runtime/logic)

        Returns:
            Dictionary with analysis results
        """
        # Try to parse the code to detect syntax errors
        syntax_error = self._check_syntax(code)

        # If we have a syntax error from parsing or error message
        if syntax_error or (error_msg and "SyntaxError" in error_msg):
            return self._analyze_syntax_error(code, error_msg, syntax_error)

        # If explicit error message provided
        if error_msg:
            return self._analyze_runtime_error(code, error_msg)

        # No error detected - perform logic analysis
        return self._analyze_logic(code)

    def _check_syntax(self, code: str) -> Optional[SyntaxError]:
        """Check code for syntax errors.

        Args:
            code: Source code to check

        Returns:
            SyntaxError if found, None otherwise
        """
        try:
            ast.parse(code)
            return None
        except SyntaxError as e:
            return e

    def _analyze_syntax_error(
        self,
        code: str,
        error_msg: str,
        syntax_error: Optional[SyntaxError]
    ) -> Dict[str, Any]:
        """Analyze syntax errors.

        Args:
            code: Source code
            error_msg: Error message
            syntax_error: SyntaxError object if available

        Returns:
            Analysis results
        """
        # Extract error location
        error_location = {}
        if syntax_error:
            if syntax_error.lineno:
                error_location["line"] = syntax_error.lineno
            if syntax_error.offset:
                error_location["column"] = syntax_error.offset
            error_text = syntax_error.msg
        else:
            # Try to parse location from error message
            error_location = self._extract_location_from_message(error_msg)
            error_text = error_msg

        # Determine specific error type
        error_analysis = self._classify_syntax_error(code, error_text, error_location)

        # Generate fix suggestions
        fix_suggestions = self._generate_syntax_fixes(
            code, error_text, error_location, error_analysis
        )

        # Find related issues
        related_issues = self._find_related_issues(error_analysis)

        return {
            "error_analysis": error_analysis,
            "error_location": error_location,
            "cause": self._explain_syntax_cause(error_analysis, error_location),
            "fix_suggestions": fix_suggestions,
            "related_issues": related_issues
        }

    def _analyze_runtime_error(
        self,
        code: str,
        error_msg: str
    ) -> Dict[str, Any]:
        """Analyze runtime errors.

        Args:
            code: Source code
            error_msg: Error message or traceback

        Returns:
            Analysis results
        """
        # Parse error type
        error_type = self._extract_error_type(error_msg)

        # Extract location from traceback
        error_location = self._extract_location_from_message(error_msg)

        # Classify the runtime error
        error_analysis = self._classify_runtime_error(error_type, error_msg)

        # Generate fix suggestions
        fix_suggestions = self._generate_runtime_fixes(
            code, error_type, error_msg, error_location
        )

        # Find related issues
        related_issues = self._find_related_issues(error_analysis)

        return {
            "error_analysis": error_analysis,
            "error_location": error_location,
            "cause": self._explain_runtime_cause(error_type, error_msg),
            "fix_suggestions": fix_suggestions,
            "related_issues": related_issues
        }

    def _analyze_logic(self, code: str) -> Dict[str, Any]:
        """Analyze code for potential logic issues.

        Args:
            code: Source code

        Returns:
            Analysis results
        """
        issues = []
        suggestions = []

        try:
            tree = ast.parse(code)

            # Check for common logic issues
            # 1. Unreachable code
            unreachable = self._find_unreachable_code(tree)
            if unreachable:
                issues.append("Potentially unreachable code detected")

            # 2. Unused variables
            unused = self._find_unused_variables(tree)
            if unused:
                issues.append(f"Unused variables: {', '.join(unused)}")

            # 3. Missing return statements
            missing_returns = self._find_missing_returns(tree)
            if missing_returns:
                issues.append("Functions may be missing return statements")

            # Generate suggestions
            if unreachable:
                suggestions.append({
                    "description": "Remove or fix unreachable code",
                    "fixed_code": "# Check control flow (return, break, continue statements)",
                    "confidence": "medium"
                })

            if unused:
                suggestions.append({
                    "description": f"Remove unused variables: {', '.join(unused[:3])}",
                    "fixed_code": "# Remove or use these variables",
                    "confidence": "medium"
                })

            if not issues:
                issues.append("No obvious logic errors detected")
                suggestions.append({
                    "description": "Code appears structurally sound - check business logic",
                    "fixed_code": code,
                    "confidence": "low"
                })

        except Exception:
            issues.append("Unable to parse code for logic analysis")

        error_analysis = "Logic analysis: " + "; ".join(issues)

        return {
            "error_analysis": error_analysis,
            "error_location": {},
            "cause": "Performing static analysis for potential logic issues",
            "fix_suggestions": suggestions,
            "related_issues": ["Logic errors require understanding expected behavior"]
        }

    def _classify_syntax_error(
        self,
        code: str,
        error_text: str,
        location: Dict[str, int]
    ) -> str:
        """Classify the type of syntax error.

        Args:
            code: Source code
            error_text: Error message
            location: Error location

        Returns:
            Classification description
        """
        error_lower = error_text.lower()

        if ":" in error_lower or "expected ':'" in error_lower:
            return "Missing colon (likely after if, for, while, def, or class)"
        elif "parenthesis" in error_lower or "parentheses" in error_lower or "was never closed" in error_lower or "'(' " in error_text or "')'" in error_text:
            return "Mismatched or missing parentheses"
        elif "bracket" in error_lower:
            return "Mismatched or missing brackets"
        elif "indent" in error_lower:
            return "Incorrect indentation"
        elif "eof" in error_lower:
            return "Unexpected end of file (missing closing bracket/parenthesis/quote)"
        elif "invalid syntax" in error_lower:
            # Try to detect specific case
            if location.get("line"):
                line_num = location["line"]
                lines = code.split("\n")
                if line_num <= len(lines):
                    line = lines[line_num - 1]
                    if "if " in line or "for " in line or "while " in line or "def " in line:
                        return "Missing colon at end of statement"
            return "Invalid syntax"
        else:
            return f"Syntax error: {error_text}"

    def _classify_runtime_error(self, error_type: str, error_msg: str) -> str:
        """Classify runtime error.

        Args:
            error_type: Type of error (NameError, TypeError, etc.)
            error_msg: Error message

        Returns:
            Classification description
        """
        if error_type == "NameError":
            # Extract variable name
            match = re.search(r"name '(\w+)' is not defined", error_msg)
            if match:
                var_name = match.group(1)
                return f"Variable '{var_name}' is not defined"
            return "Variable is not defined"

        elif error_type == "TypeError":
            if "unsupported operand" in error_msg:
                return "Operation not supported between these types"
            elif "argument" in error_msg:
                return "Incorrect number or type of arguments"
            return "Type error - incompatible types"

        elif error_type == "AttributeError":
            match = re.search(r"'(\w+)' object has no attribute '(\w+)'", error_msg)
            if match:
                obj_type, attr = match.group(1), match.group(2)
                return f"Object of type '{obj_type}' has no attribute '{attr}'"
            return "Attribute not found on object"

        elif error_type == "IndexError":
            return "List index out of range"

        elif error_type == "KeyError":
            return "Dictionary key not found"

        elif error_type == "ValueError":
            return "Invalid value for the operation"

        elif error_type == "ImportError" or error_type == "ModuleNotFoundError":
            return "Module or package not found"

        return f"{error_type} occurred"

    def _generate_syntax_fixes(
        self,
        code: str,
        error_text: str,
        location: Dict[str, int],
        analysis: str
    ) -> List[Dict[str, Any]]:
        """Generate fix suggestions for syntax errors.

        Args:
            code: Source code
            error_text: Error message
            location: Error location
            analysis: Error analysis

        Returns:
            List of fix suggestions
        """
        fixes = []
        lines = code.split("\n")

        # Missing colon
        if "colon" in analysis.lower():
            line_num = location.get("line", 1)
            if line_num <= len(lines):
                line = lines[line_num - 1]
                fixed_line = line.rstrip() + ":"
                fixed_code = "\n".join(
                    lines[:line_num-1] + [fixed_line] + lines[line_num:]
                )
                fixes.append({
                    "description": f"Add missing colon at end of line {line_num}",
                    "fixed_code": fixed_code,
                    "confidence": "high"
                })

        # Missing parenthesis
        elif "parenthes" in analysis.lower():
            # Count parentheses
            open_count = code.count("(")
            close_count = code.count(")")
            if open_count > close_count:
                fixes.append({
                    "description": f"Add {open_count - close_count} closing parenthesis/parentheses",
                    "fixed_code": code + ")" * (open_count - close_count),
                    "confidence": "medium"
                })
            elif close_count > open_count:
                fixes.append({
                    "description": f"Remove {close_count - open_count} extra closing parenthesis/parentheses",
                    "fixed_code": "# Check for extra ')' in your code",
                    "confidence": "medium"
                })

        # Indentation error
        elif "indent" in analysis.lower():
            fixes.append({
                "description": "Fix indentation (use 4 spaces per level)",
                "fixed_code": "# Ensure consistent indentation throughout",
                "confidence": "medium"
            })

        # Generic syntax error
        if not fixes:
            fixes.append({
                "description": "Review syntax near the error location",
                "fixed_code": "# Check the code structure around the reported line",
                "confidence": "low"
            })

        return fixes

    def _generate_runtime_fixes(
        self,
        code: str,
        error_type: str,
        error_msg: str,
        location: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """Generate fix suggestions for runtime errors.

        Args:
            code: Source code
            error_type: Error type
            error_msg: Error message
            location: Error location

        Returns:
            List of fix suggestions
        """
        fixes = []

        if error_type == "NameError":
            # Extract variable name
            match = re.search(r"name '(\w+)' is not defined", error_msg)
            if match:
                var_name = match.group(1)

                # Suggest common fixes
                fixes.append({
                    "description": f"Define variable '{var_name}' before using it",
                    "fixed_code": f"{var_name} = None  # or appropriate value",
                    "confidence": "high"
                })

                # Check if it might be a typo of existing variable
                fixes.append({
                    "description": f"Check if '{var_name}' is a typo of another variable",
                    "fixed_code": f"# Check spelling of '{var_name}'",
                    "confidence": "medium"
                })

                # Check if it needs to be imported
                if var_name[0].isupper() or var_name in ["pd", "np", "plt", "os", "sys"]:
                    fixes.append({
                        "description": f"Import missing module/class '{var_name}'",
                        "fixed_code": f"import {var_name}",
                        "confidence": "medium"
                    })

        elif error_type == "TypeError":
            if "unsupported operand" in error_msg or "concatenate" in error_msg:
                fixes.append({
                    "description": "Convert operands to compatible types",
                    "fixed_code": "# e.g., str(number) or int(string)",
                    "confidence": "high"
                })
                # Add specific example for common case
                if "str" in error_msg and "int" in error_msg:
                    fixes.append({
                        "description": "Convert string to int or int to string",
                        "fixed_code": "result = int(string_var) + number  # or str(number) + string_var",
                        "confidence": "high"
                    })
            elif "argument" in error_msg:
                fixes.append({
                    "description": "Check function signature and arguments",
                    "fixed_code": "# Verify number and type of arguments",
                    "confidence": "high"
                })

        elif error_type == "AttributeError":
            match = re.search(r"'(\w+)' object has no attribute '(\w+)'", error_msg)
            if match:
                obj_type, attr = match.group(1), match.group(2)
                fixes.append({
                    "description": f"Check if attribute '{attr}' exists on {obj_type} object",
                    "fixed_code": f"# Use dir(obj) to see available attributes",
                    "confidence": "medium"
                })
                fixes.append({
                    "description": f"Check for typos in attribute name '{attr}'",
                    "fixed_code": f"# Common: {attr} vs {attr.lower()}",
                    "confidence": "medium"
                })

        elif error_type == "IndexError":
            fixes.append({
                "description": "Check list bounds before accessing",
                "fixed_code": "if index < len(my_list):\n    value = my_list[index]",
                "confidence": "high"
            })

        elif error_type == "KeyError":
            fixes.append({
                "description": "Check if key exists before accessing",
                "fixed_code": "value = my_dict.get('key', default_value)",
                "confidence": "high"
            })

        elif error_type == "ImportError" or error_type == "ModuleNotFoundError":
            match = re.search(r"No module named '(\w+)'", error_msg)
            if match:
                module_name = match.group(1)
                fixes.append({
                    "description": f"Install missing module '{module_name}'",
                    "fixed_code": f"pip install {module_name}",
                    "confidence": "high"
                })

        if not fixes:
            fixes.append({
                "description": "Review the error message and traceback",
                "fixed_code": "# Check the line indicated in the traceback",
                "confidence": "low"
            })

        return fixes

    def _explain_syntax_cause(self, analysis: str, location: Dict[str, int]) -> str:
        """Explain the root cause of syntax error.

        Args:
            analysis: Error analysis
            location: Error location

        Returns:
            Cause explanation
        """
        location_str = ""
        if location.get("line"):
            location_str = f" at line {location['line']}"
            if location.get("column"):
                location_str += f", column {location['column']}"

        if "colon" in analysis.lower():
            return f"Python requires a colon ':' at the end of if, for, while, def, and class statements{location_str}"
        elif "parenthes" in analysis.lower():
            return f"Every opening parenthesis '(' must have a matching closing parenthesis ')'{location_str}"
        elif "bracket" in analysis.lower():
            return f"Every opening bracket '[' or '{{' must have a matching closing bracket{location_str}"
        elif "indent" in analysis.lower():
            return f"Python uses indentation to define code blocks. Use consistent spaces (typically 4){location_str}"
        else:
            return f"Syntax error detected{location_str}. {analysis}"

    def _explain_runtime_cause(self, error_type: str, error_msg: str) -> str:
        """Explain the root cause of runtime error.

        Args:
            error_type: Error type
            error_msg: Error message

        Returns:
            Cause explanation
        """
        if error_type == "NameError":
            return "The variable or name is used before it's defined or imported"
        elif error_type == "TypeError":
            return "An operation is performed on incompatible types or with wrong arguments"
        elif error_type == "AttributeError":
            return "Attempting to access an attribute/method that doesn't exist on the object"
        elif error_type == "IndexError":
            return "Attempting to access a list index that doesn't exist"
        elif error_type == "KeyError":
            return "Attempting to access a dictionary key that doesn't exist"
        elif error_type == "ValueError":
            return "A function received an argument of correct type but inappropriate value"
        elif error_type in ["ImportError", "ModuleNotFoundError"]:
            return "The module or package is not installed or cannot be found"
        else:
            return f"{error_type}: {error_msg}"

    def _find_related_issues(self, analysis: str) -> List[str]:
        """Find related common issues.

        Args:
            analysis: Error analysis

        Returns:
            List of related issues
        """
        related = []

        if "colon" in analysis.lower():
            related.extend([
                "Missing colons after if/for/while/def/class",
                "Incorrect statement syntax"
            ])
        elif "parenthes" in analysis.lower():
            related.extend([
                "Mismatched brackets or quotes",
                "Unclosed function calls or expressions"
            ])
        elif "indent" in analysis.lower():
            related.extend([
                "Mixing tabs and spaces",
                "Inconsistent indentation levels"
            ])
        elif "NameError" in analysis or "not defined" in analysis:
            related.extend([
                "Variable typos",
                "Missing imports",
                "Scope issues (variable not in current scope)"
            ])
        elif "TypeError" in analysis:
            related.extend([
                "Type conversion needed",
                "Wrong number of function arguments",
                "Operating on None value"
            ])
        elif "AttributeError" in analysis:
            related.extend([
                "Typo in attribute/method name",
                "Wrong object type",
                "Using None where object expected"
            ])

        if not related:
            related.append("Consult Python documentation for more details")

        return related

    def _extract_error_type(self, error_msg: str) -> str:
        """Extract error type from error message.

        Args:
            error_msg: Error message or traceback

        Returns:
            Error type (e.g., "NameError", "TypeError")
        """
        # Common Python error types
        error_types = [
            "SyntaxError", "NameError", "TypeError", "AttributeError",
            "IndexError", "KeyError", "ValueError", "ImportError",
            "ModuleNotFoundError", "ZeroDivisionError", "FileNotFoundError"
        ]

        for error_type in error_types:
            if error_type in error_msg:
                return error_type

        return "UnknownError"

    def _extract_location_from_message(self, error_msg: str) -> Dict[str, int]:
        """Extract line and column from error message.

        Args:
            error_msg: Error message or traceback

        Returns:
            Dictionary with line and column if found
        """
        location = {}

        # Try to find line number in traceback format
        line_match = re.search(r'line (\d+)', error_msg)
        if line_match:
            location["line"] = int(line_match.group(1))

        # Try to find column in error message
        col_match = re.search(r'column (\d+)', error_msg)
        if col_match:
            location["column"] = int(col_match.group(1))

        return location

    def _find_unreachable_code(self, tree: ast.AST) -> bool:
        """Find potentially unreachable code.

        Args:
            tree: AST tree

        Returns:
            True if unreachable code found
        """
        class UnreachableVisitor(ast.NodeVisitor):
            def __init__(self):
                self.has_unreachable = False

            def check_block(self, stmts):
                """Check a block of statements for unreachable code."""
                for i, stmt in enumerate(stmts):
                    if isinstance(stmt, ast.Return) and i < len(stmts) - 1:
                        self.has_unreachable = True
                    elif isinstance(stmt, (ast.If, ast.For, ast.While, ast.With)):
                        # Recursively check nested blocks
                        if hasattr(stmt, 'body'):
                            self.check_block(stmt.body)
                        if hasattr(stmt, 'orelse'):
                            self.check_block(stmt.orelse)

            def visit_FunctionDef(self, node):
                self.check_block(node.body)
                # Don't visit nested functions
                # self.generic_visit(node)

        visitor = UnreachableVisitor()
        visitor.visit(tree)
        return visitor.has_unreachable

    def _find_unused_variables(self, tree: ast.AST) -> List[str]:
        """Find potentially unused variables.

        Args:
            tree: AST tree

        Returns:
            List of unused variable names
        """
        class VariableVisitor(ast.NodeVisitor):
            def __init__(self):
                self.assigned = set()
                self.used = set()

            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Store):
                    self.assigned.add(node.id)
                elif isinstance(node.ctx, ast.Load):
                    self.used.add(node.id)
                self.generic_visit(node)

        visitor = VariableVisitor()
        visitor.visit(tree)
        unused = visitor.assigned - visitor.used
        return sorted(list(unused))[:5]  # Return max 5

    def _find_missing_returns(self, tree: ast.AST) -> bool:
        """Check if functions are missing return statements.

        Args:
            tree: AST tree

        Returns:
            True if functions missing returns found
        """
        class ReturnVisitor(ast.NodeVisitor):
            def __init__(self):
                self.has_missing = False

            def visit_FunctionDef(self, node):
                # Check if function has no return and more than just pass
                has_return = any(isinstance(stmt, ast.Return) for stmt in ast.walk(node))
                has_real_body = len(node.body) > 1 or (
                    len(node.body) == 1 and not isinstance(node.body[0], ast.Pass)
                )
                if has_real_body and not has_return and node.name != "__init__":
                    self.has_missing = True
                # Don't visit nested functions
                # self.generic_visit(node)

        visitor = ReturnVisitor()
        visitor.visit(tree)
        return visitor.has_missing
