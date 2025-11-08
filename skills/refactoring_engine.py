"""Refactoring Engine Skill for Meton.

This skill analyzes Python code and suggests improvements for:
- Readability (naming, structure, clarity)
- Performance (optimization opportunities)
- Best practices (Pythonic idioms, patterns)

Example:
    >>> from skills.refactoring_engine import RefactoringEngineSkill
    >>>
    >>> skill = RefactoringEngineSkill()
    >>> result = skill.execute({
    ...     "code": "for i in range(len(items)):\\n    result.append(items[i] * 2)",
    ...     "focus": "readability"
    ... })
    >>> print(result["refactoring_suggestions"][0]["type"])
    "simplify"
"""

import ast
import re
from typing import Dict, Any, List, Set, Optional, Tuple
from skills.base import BaseSkill, SkillValidationError, SkillExecutionError


class RefactoringEngineSkill(BaseSkill):
    """Skill that analyzes code and suggests refactoring improvements.

    Analyzes Python code to identify opportunities for:
    - Extract function (code duplication, long functions)
    - Simplify conditionals (nested ifs, complex boolean logic)
    - Remove dead code (unreachable, unused variables)
    - Improve naming (single letters, unclear names)
    - Use list comprehensions (simple loops)
    - Remove magic numbers (hardcoded values)
    - Use context managers (file operations)
    - Add type hints (missing annotations)

    Attributes:
        name: Skill identifier "refactoring_engine"
        description: What the skill does
        version: Skill version
        enabled: Whether skill is enabled
    """

    name = "refactoring_engine"
    description = "Analyzes code and suggests improvements for readability, performance, and best practices"
    version = "1.0.0"
    enabled = True

    # Thresholds for detection
    LONG_FUNCTION_LINES = 20
    COMPLEX_FUNCTION_COMPLEXITY = 10
    MAX_NESTED_DEPTH = 3
    MIN_DUPLICATION_LINES = 3

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
        if "focus" in input_data:
            focus = input_data["focus"]
            if focus not in ["readability", "performance", "best_practices", "all"]:
                raise SkillValidationError(
                    f"Invalid focus: {focus}. Must be 'readability', 'performance', 'best_practices', or 'all'."
                )

        if "aggressive" in input_data:
            if not isinstance(input_data["aggressive"], bool):
                raise SkillValidationError("Field 'aggressive' must be a boolean")

        return True

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute refactoring analysis.

        Args:
            input_data: Dictionary with:
                - code: Source code string (required)
                - focus: "readability"|"performance"|"best_practices"|"all" (optional, default: "all")
                - aggressive: bool (optional, default: False)

        Returns:
            Dictionary with:
                - success: bool
                - refactoring_suggestions: List of refactoring opportunities
                - metrics: Before/after metrics
                - summary: Overall assessment
                - error: Error message (if success=False)

        Raises:
            SkillExecutionError: If execution fails
        """
        try:
            # Validate input
            self.validate_input(input_data)

            code = input_data["code"]
            focus = input_data.get("focus", "all")
            aggressive = input_data.get("aggressive", False)

            # Analyze the code
            suggestions = self._analyze_code(code, focus, aggressive)

            # Calculate metrics
            metrics = self._calculate_metrics(code, suggestions)

            # Generate summary
            summary = self._generate_summary(suggestions, metrics)

            return {
                "success": True,
                "refactoring_suggestions": suggestions,
                "metrics": metrics,
                "summary": summary
            }

        except SkillValidationError as e:
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            raise SkillExecutionError(f"Refactoring analysis failed: {str(e)}")

    def _analyze_code(
        self,
        code: str,
        focus: str,
        aggressive: bool
    ) -> List[Dict[str, Any]]:
        """Analyze code and identify refactoring opportunities.

        Args:
            code: Source code
            focus: What to focus on
            aggressive: Whether to be aggressive with suggestions

        Returns:
            List of refactoring suggestions
        """
        suggestions = []

        try:
            tree = ast.parse(code)
            lines = code.split('\n')

            # Different analysis based on focus
            if focus in ["all", "readability"]:
                suggestions.extend(self._detect_long_functions(tree, lines))
                suggestions.extend(self._detect_naming_issues(tree))
                suggestions.extend(self._detect_nested_conditionals(tree, code))
                suggestions.extend(self._detect_list_comprehension_opportunities(tree, code))

            if focus in ["all", "performance"]:
                suggestions.extend(self._detect_inefficient_loops(tree, code))

            if focus in ["all", "best_practices"]:
                suggestions.extend(self._detect_magic_numbers(tree, code))
                suggestions.extend(self._detect_missing_context_managers(tree, code))
                suggestions.extend(self._detect_dead_code(tree))
                suggestions.extend(self._detect_missing_type_hints(tree, code))

            # Sort by severity
            severity_order = {"major": 0, "moderate": 1, "minor": 2}
            suggestions.sort(key=lambda x: severity_order.get(x["severity"], 3))

        except SyntaxError:
            # Can't analyze code with syntax errors
            suggestions.append({
                "type": "fix_syntax",
                "severity": "major",
                "description": "Fix syntax errors before refactoring",
                "original_code": code[:100] + "..." if len(code) > 100 else code,
                "refactored_code": "# Fix syntax errors first",
                "reason": "Code must be syntactically valid for refactoring",
                "impact": "readability"
            })

        return suggestions

    def _detect_long_functions(
        self,
        tree: ast.AST,
        lines: List[str]
    ) -> List[Dict[str, Any]]:
        """Detect functions that are too long.

        Args:
            tree: AST tree
            lines: Source code lines

        Returns:
            List of suggestions
        """
        suggestions = []

        class FunctionVisitor(ast.NodeVisitor):
            def __init__(self, outer_self):
                self.outer_self = outer_self
                self.suggestions = []

            def visit_FunctionDef(self, node):
                # Calculate function length
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    func_length = node.end_lineno - node.lineno + 1

                    if func_length > self.outer_self.LONG_FUNCTION_LINES:
                        # Get function code
                        func_lines = lines[node.lineno - 1:node.end_lineno]
                        original = '\n'.join(func_lines)

                        self.suggestions.append({
                            "type": "extract_function",
                            "severity": "moderate",
                            "description": f"Function '{node.name}' is {func_length} lines long (>{self.outer_self.LONG_FUNCTION_LINES})",
                            "original_code": original,
                            "refactored_code": f"# Consider breaking '{node.name}' into smaller functions",
                            "reason": "Long functions are harder to understand and maintain",
                            "impact": "readability"
                        })

                self.generic_visit(node)

        visitor = FunctionVisitor(self)
        visitor.visit(tree)
        return visitor.suggestions

    def _detect_naming_issues(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Detect poor variable/function names.

        Args:
            tree: AST tree

        Returns:
            List of suggestions
        """
        suggestions = []
        poor_names = set()

        class NameVisitor(ast.NodeVisitor):
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Store):
                    name = node.id
                    # Check for single letter names (except common ones)
                    if len(name) == 1 and name not in ['i', 'j', 'k', 'x', 'y', 'z', '_']:
                        poor_names.add(name)
                    # Check for unclear abbreviations
                    elif len(name) <= 3 and name not in ['df', 'np', 'pd', 'os', 'sys']:
                        if not name.isupper():  # Allow constants
                            poor_names.add(name)
                self.generic_visit(node)

            def visit_FunctionDef(self, node):
                name = node.name
                # Check for single letter function names
                if len(name) == 1:
                    poor_names.add(f"function '{name}'")
                self.generic_visit(node)

        visitor = NameVisitor()
        visitor.visit(tree)

        for name in list(poor_names)[:5]:  # Limit to 5 suggestions
            suggestions.append({
                "type": "rename",
                "severity": "minor",
                "description": f"Variable/function name '{name}' is unclear",
                "original_code": f"{name} = ...",
                "refactored_code": f"descriptive_name = ...  # Use a more descriptive name",
                "reason": "Clear names improve code readability",
                "impact": "readability"
            })

        return suggestions

    def _detect_nested_conditionals(
        self,
        tree: ast.AST,
        code: str
    ) -> List[Dict[str, Any]]:
        """Detect deeply nested if statements.

        Args:
            tree: AST tree
            code: Source code

        Returns:
            List of suggestions
        """
        suggestions = []

        class NestedIfVisitor(ast.NodeVisitor):
            def __init__(self):
                self.depth = 0
                self.max_depth = 0
                self.deep_ifs = []

            def visit_If(self, node):
                self.depth += 1
                if self.depth > MAX_NESTED_DEPTH:
                    self.deep_ifs.append(node)
                self.max_depth = max(self.max_depth, self.depth)
                self.generic_visit(node)
                self.depth -= 1

        MAX_NESTED_DEPTH = self.MAX_NESTED_DEPTH
        visitor = NestedIfVisitor()
        visitor.visit(tree)

        if visitor.deep_ifs:
            suggestions.append({
                "type": "simplify",
                "severity": "moderate",
                "description": f"Found {len(visitor.deep_ifs)} deeply nested if statement(s) (depth > {MAX_NESTED_DEPTH})",
                "original_code": "if cond1:\n    if cond2:\n        if cond3:\n            ...",
                "refactored_code": "# Use early returns or combine conditions:\nif not cond1:\n    return\nif not cond2:\n    return\nif cond3:\n    ...",
                "reason": "Deep nesting makes code harder to follow",
                "impact": "readability"
            })

        return suggestions

    def _detect_list_comprehension_opportunities(
        self,
        tree: ast.AST,
        code: str
    ) -> List[Dict[str, Any]]:
        """Detect loops that could be list comprehensions.

        Args:
            tree: AST tree
            code: Source code

        Returns:
            List of suggestions
        """
        suggestions = []

        class LoopVisitor(ast.NodeVisitor):
            def __init__(self):
                self.opportunities = []

            def visit_For(self, node):
                # Check if it's a simple append loop
                if len(node.body) == 1 and isinstance(node.body[0], ast.Expr):
                    expr = node.body[0].value
                    if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Attribute):
                        if expr.func.attr == 'append':
                            self.opportunities.append(node)

                self.generic_visit(node)

        visitor = LoopVisitor()
        visitor.visit(tree)

        for opportunity in visitor.opportunities[:3]:  # Limit to 3
            suggestions.append({
                "type": "simplify",
                "severity": "minor",
                "description": "Loop can be simplified to list comprehension",
                "original_code": "for item in items:\n    result.append(item * 2)",
                "refactored_code": "result = [item * 2 for item in items]",
                "reason": "List comprehensions are more Pythonic and often faster",
                "impact": "readability"
            })

        return suggestions

    def _detect_inefficient_loops(
        self,
        tree: ast.AST,
        code: str
    ) -> List[Dict[str, Any]]:
        """Detect inefficient loop patterns.

        Args:
            tree: AST tree
            code: Source code

        Returns:
            List of suggestions
        """
        suggestions = []

        class LoopVisitor(ast.NodeVisitor):
            def __init__(self):
                self.range_len_loops = []

            def visit_For(self, node):
                # Check for range(len(x)) pattern
                if isinstance(node.iter, ast.Call):
                    if isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
                        if len(node.iter.args) == 1 and isinstance(node.iter.args[0], ast.Call):
                            inner = node.iter.args[0]
                            if isinstance(inner.func, ast.Name) and inner.func.id == 'len':
                                self.range_len_loops.append(node)

                self.generic_visit(node)

        visitor = LoopVisitor()
        visitor.visit(tree)

        for loop in visitor.range_len_loops[:3]:  # Limit to 3
            suggestions.append({
                "type": "optimize",
                "severity": "minor",
                "description": "Use enumerate() instead of range(len())",
                "original_code": "for i in range(len(items)):\n    print(items[i])",
                "refactored_code": "for i, item in enumerate(items):\n    print(item)",
                "reason": "enumerate() is more Pythonic and clearer",
                "impact": "readability"
            })

        return suggestions

    def _detect_magic_numbers(
        self,
        tree: ast.AST,
        code: str
    ) -> List[Dict[str, Any]]:
        """Detect magic numbers that should be constants.

        Args:
            tree: AST tree
            code: Source code

        Returns:
            List of suggestions
        """
        suggestions = []
        magic_numbers = []

        class NumberVisitor(ast.NodeVisitor):
            def visit_Num(self, node):
                # Python 3.7 and earlier
                if hasattr(node, 'n'):
                    value = node.n
                    # Ignore common values
                    if value not in [0, 1, -1, 2, 10, 100]:
                        magic_numbers.append(value)
                self.generic_visit(node)

            def visit_Constant(self, node):
                # Python 3.8+
                if isinstance(node.value, (int, float)):
                    value = node.value
                    # Ignore common values
                    if value not in [0, 1, -1, 2, 10, 100]:
                        magic_numbers.append(value)
                self.generic_visit(node)

        visitor = NumberVisitor()
        visitor.visit(tree)

        if magic_numbers:
            unique_numbers = list(set(magic_numbers))[:3]  # Limit to 3
            for num in unique_numbers:
                suggestions.append({
                    "type": "extract_constant",
                    "severity": "minor",
                    "description": f"Magic number '{num}' should be a named constant",
                    "original_code": f"if value > {num}:",
                    "refactored_code": f"MAX_VALUE = {num}\nif value > MAX_VALUE:",
                    "reason": "Named constants are more maintainable and self-documenting",
                    "impact": "maintainability"
                })

        return suggestions

    def _detect_missing_context_managers(
        self,
        tree: ast.AST,
        code: str
    ) -> List[Dict[str, Any]]:
        """Detect file operations without context managers.

        Args:
            tree: AST tree
            code: Source code

        Returns:
            List of suggestions
        """
        suggestions = []

        class FileVisitor(ast.NodeVisitor):
            def __init__(self):
                self.open_calls = []
                self.in_with = False

            def visit_With(self, node):
                old_in_with = self.in_with
                self.in_with = True
                self.generic_visit(node)
                self.in_with = old_in_with

            def visit_Call(self, node):
                if isinstance(node.func, ast.Name) and node.func.id == 'open':
                    if not self.in_with:
                        self.open_calls.append(node)
                self.generic_visit(node)

        visitor = FileVisitor()
        visitor.visit(tree)

        if visitor.open_calls:
            suggestions.append({
                "type": "use_context_manager",
                "severity": "moderate",
                "description": f"Found {len(visitor.open_calls)} file open() call(s) without context manager",
                "original_code": "f = open('file.txt')\ndata = f.read()\nf.close()",
                "refactored_code": "with open('file.txt') as f:\n    data = f.read()",
                "reason": "Context managers ensure files are properly closed",
                "impact": "best_practices"
            })

        return suggestions

    def _detect_dead_code(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Detect dead/unreachable code.

        Args:
            tree: AST tree

        Returns:
            List of suggestions
        """
        suggestions = []

        class DeadCodeVisitor(ast.NodeVisitor):
            def __init__(self):
                self.unreachable = []
                self.unused_vars = []

            def check_block(self, stmts, context=""):
                """Check a block of statements for unreachable code."""
                for i, stmt in enumerate(stmts):
                    if isinstance(stmt, ast.Return) and i < len(stmts) - 1:
                        self.unreachable.append(context)
                        break
                    # Recurse into nested blocks
                    if isinstance(stmt, ast.If):
                        self.check_block(stmt.body, context)
                        self.check_block(stmt.orelse, context)
                    elif isinstance(stmt, (ast.For, ast.While)):
                        self.check_block(stmt.body, context)
                        self.check_block(stmt.orelse, context)

            def visit_FunctionDef(self, node):
                self.check_block(node.body, node.name)
                # Don't visit nested functions with generic_visit

        visitor = DeadCodeVisitor()
        visitor.visit(tree)

        if visitor.unreachable:
            for func_name in list(set(visitor.unreachable))[:3]:  # Limit to 3, unique
                suggestions.append({
                    "type": "remove_dead_code",
                    "severity": "minor",
                    "description": f"Function '{func_name}' has unreachable code after return",
                    "original_code": "def foo():\n    return x\n    print('unreachable')",
                    "refactored_code": "def foo():\n    return x",
                    "reason": "Dead code confuses readers and should be removed",
                    "impact": "readability"
                })

        return suggestions

    def _detect_missing_type_hints(
        self,
        tree: ast.AST,
        code: str
    ) -> List[Dict[str, Any]]:
        """Detect functions missing type hints.

        Args:
            tree: AST tree
            code: Source code

        Returns:
            List of suggestions
        """
        suggestions = []
        functions_without_hints = []

        class TypeHintVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                # Check if function has type hints
                has_hints = False
                if node.returns is not None:
                    has_hints = True
                for arg in node.args.args:
                    if arg.annotation is not None:
                        has_hints = True
                        break

                if not has_hints and not node.name.startswith('_'):
                    functions_without_hints.append(node.name)

                self.generic_visit(node)

        visitor = TypeHintVisitor()
        visitor.visit(tree)

        if functions_without_hints:
            count = len(functions_without_hints)
            suggestions.append({
                "type": "add_type_hints",
                "severity": "minor",
                "description": f"Found {count} function(s) without type hints",
                "original_code": "def calculate(x, y):\n    return x + y",
                "refactored_code": "def calculate(x: int, y: int) -> int:\n    return x + y",
                "reason": "Type hints improve code clarity and enable static type checking",
                "impact": "maintainability"
            })

        return suggestions

    def _calculate_metrics(
        self,
        code: str,
        suggestions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate code metrics.

        Args:
            code: Source code
            suggestions: Refactoring suggestions

        Returns:
            Metrics dictionary
        """
        lines_before = len([l for l in code.split('\n') if l.strip()])
        complexity_before = self._calculate_complexity(code)

        # Estimate improvements (simplified - would need actual refactored code for precision)
        lines_after = lines_before
        complexity_after = complexity_before

        # Estimate based on suggestion types
        for suggestion in suggestions:
            if suggestion["type"] == "extract_function":
                complexity_after = max(1, complexity_after - 2)
            elif suggestion["type"] == "simplify":
                complexity_after = max(1, complexity_after - 1)
                lines_after = max(1, lines_after - 2)
            elif suggestion["type"] == "remove_dead_code":
                lines_after = max(1, lines_after - 1)

        return {
            "complexity_before": complexity_before,
            "complexity_after": complexity_after,
            "lines_before": lines_before,
            "lines_after": lines_after,
            "improvement_score": self._calculate_improvement_score(
                complexity_before, complexity_after, lines_before, lines_after
            )
        }

    def _calculate_complexity(self, code: str) -> int:
        """Calculate cyclomatic complexity.

        Args:
            code: Source code

        Returns:
            Complexity score
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return 0

        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            # Decision points increase complexity
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity

    def _calculate_improvement_score(
        self,
        complexity_before: int,
        complexity_after: int,
        lines_before: int,
        lines_after: int
    ) -> float:
        """Calculate overall improvement score (0-100).

        Args:
            complexity_before: Complexity before refactoring
            complexity_after: Complexity after refactoring
            lines_before: Lines before refactoring
            lines_after: Lines after refactoring

        Returns:
            Improvement score
        """
        if complexity_before == 0 or lines_before == 0:
            return 0.0

        complexity_improvement = (complexity_before - complexity_after) / complexity_before
        lines_improvement = (lines_before - lines_after) / lines_before

        # Weighted average (complexity is more important)
        score = (complexity_improvement * 0.7 + lines_improvement * 0.3) * 100
        return max(0.0, min(100.0, score))

    def _generate_summary(
        self,
        suggestions: List[Dict[str, Any]],
        metrics: Dict[str, Any]
    ) -> str:
        """Generate overall assessment summary.

        Args:
            suggestions: Refactoring suggestions
            metrics: Code metrics

        Returns:
            Summary string
        """
        if not suggestions:
            return "Code is well-structured with no major refactoring opportunities detected."

        major = sum(1 for s in suggestions if s["severity"] == "major")
        moderate = sum(1 for s in suggestions if s["severity"] == "moderate")
        minor = sum(1 for s in suggestions if s["severity"] == "minor")

        summary_parts = [
            f"Found {len(suggestions)} refactoring opportunity/opportunities:"
        ]

        if major:
            summary_parts.append(f"{major} major")
        if moderate:
            summary_parts.append(f"{moderate} moderate")
        if minor:
            summary_parts.append(f"{minor} minor")

        complexity_reduction = metrics["complexity_before"] - metrics["complexity_after"]
        if complexity_reduction > 0:
            summary_parts.append(
                f"Estimated complexity reduction: {metrics['complexity_before']} → {metrics['complexity_after']}"
            )

        improvement_score = metrics.get("improvement_score", 0)
        if improvement_score > 10:
            summary_parts.append(f"Improvement score: {improvement_score:.1f}/100")

        return ". ".join(summary_parts) + "."
