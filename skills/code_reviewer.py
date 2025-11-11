"""Code Reviewer Skill for Meton.

This skill performs automated code reviews for:
- Best practices (complexity, function length, naming)
- Security issues (dangerous functions, SQL injection, hardcoded secrets)
- Style compliance (naming conventions, imports, type hints)

Example:
    >>> from skills.code_reviewer import CodeReviewerSkill
    >>>
    >>> skill = CodeReviewerSkill()
    >>> result = skill.execute({
    ...     "code": "password = 'secret123'",
    ...     "checks": ["security"]
    ... })
    >>> print(result["score"])
"""

import ast
import re
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from skills.base import BaseSkill, SkillValidationError, SkillExecutionError


@dataclass
class ReviewIssue:
    """Represents a code review issue.

    Attributes:
        severity: Issue severity (CRITICAL, HIGH, MEDIUM, LOW, INFO)
        category: Issue category (best_practices, security, style)
        message: Description of the issue
        line_number: Line number where issue occurs (optional)
        suggestion: Suggestion for fixing the issue (optional)
    """
    severity: str
    category: str
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class CodeReviewerSkill(BaseSkill):
    """Skill that performs automated code reviews.

    Reviews Python code for:
    - Best practices (complexity, length, parameters, naming, nesting, docstrings)
    - Security issues (dangerous functions, SQL injection, secrets, shell commands)
    - Style compliance (naming conventions, imports, type hints)

    Attributes:
        name: Skill identifier "code_reviewer"
        description: What the skill does
        version: Skill version
        enabled: Whether skill is enabled
    """

    name = "code_reviewer"
    description = "Reviews code for best practices, security, and style compliance"
    version = "1.0.0"
    enabled = True

    # Thresholds
    COMPLEXITY_THRESHOLD = 10
    FUNCTION_LENGTH_THRESHOLD = 50
    MAX_PARAMETERS = 5
    MAX_NESTED_DEPTH = 4

    # Severity scores for score calculation
    SEVERITY_SCORES = {
        "CRITICAL": 20,
        "HIGH": 10,
        "MEDIUM": 5,
        "LOW": 2,
        "INFO": 1
    }

    # Dangerous functions for security checks
    DANGEROUS_FUNCS = ["eval", "exec", "compile", "__import__"]
    SHELL_FUNCS = ["system", "popen", "popen2", "popen3", "popen4"]

    # Secret patterns
    SECRET_KEYWORDS = ["password", "passwd", "pwd", "secret", "api_key", "apikey",
                       "token", "auth", "credential", "private_key", "access_key"]

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

        # Validate optional checks field
        if "checks" in input_data:
            checks = input_data["checks"]
            if not isinstance(checks, list):
                raise SkillValidationError("Field 'checks' must be a list")

            valid_checks = ["best_practices", "security", "style"]
            for check in checks:
                if check not in valid_checks:
                    raise SkillValidationError(
                        f"Invalid check: {check}. Must be one of {valid_checks}"
                    )

        return True

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code review.

        Args:
            input_data: Dictionary with:
                - code: Source code string (required)
                - checks: List of check categories (optional, default: all)
                  Valid values: ["best_practices", "security", "style"]

        Returns:
            Dictionary with:
                - success: bool
                - issues: List of ReviewIssue dictionaries
                - summary: Summary statistics
                - score: Quality score (0-100)
                - error: Error message (if success=False)

        Raises:
            SkillExecutionError: If execution fails
        """
        try:
            self.validate_input(input_data)

            code = input_data["code"]
            checks = input_data.get("checks", ["best_practices", "security", "style"])

            # Perform review
            issues = self._review_code(code, checks)

            # Calculate summary
            summary = self._calculate_summary(issues)

            # Calculate score
            score = self._calculate_score(issues)

            return {
                "success": True,
                "issues": [issue.to_dict() for issue in issues],
                "summary": summary,
                "score": score
            }

        except SkillValidationError as e:
            return {
                "success": False,
                "issues": [],
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "issues": [],
                "error": f"Code review failed: {str(e)}"
            }

    def _review_code(self, code: str, checks: List[str]) -> List[ReviewIssue]:
        """Perform code review.

        Args:
            code: Source code to review
            checks: List of check categories to run

        Returns:
            List of ReviewIssue objects
        """
        issues = []

        # Parse code
        try:
            tree = ast.parse(code)
            lines = code.split('\n')
        except SyntaxError as e:
            return [ReviewIssue(
                severity="CRITICAL",
                category="syntax",
                message=f"Syntax error: {str(e)}",
                line_number=e.lineno if hasattr(e, 'lineno') else None
            )]

        # Run requested checks
        if "best_practices" in checks:
            issues.extend(self._check_best_practices(tree, code, lines))

        if "security" in checks:
            issues.extend(self._check_security(tree, code, lines))

        if "style" in checks:
            issues.extend(self._check_style(tree, code, lines))

        return issues

    def _check_best_practices(
        self,
        tree: ast.AST,
        code: str,
        lines: List[str]
    ) -> List[ReviewIssue]:
        """Check for best practice violations.

        Args:
            tree: AST tree
            code: Source code
            lines: Code lines

        Returns:
            List of issues found
        """
        issues = []

        # Check function-specific issues
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Function complexity
                func_complexity = self._calculate_function_complexity(node)
                if func_complexity > self.COMPLEXITY_THRESHOLD:
                    issues.append(ReviewIssue(
                        severity="MEDIUM",
                        category="best_practices",
                        message=f"Function '{node.name}' has high cyclomatic complexity: {func_complexity} (threshold: {self.COMPLEXITY_THRESHOLD})",
                        line_number=node.lineno,
                        suggestion="Consider breaking this function into smaller functions"
                    ))

                # Function length
                if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                    func_length = node.end_lineno - node.lineno + 1
                    if func_length > self.FUNCTION_LENGTH_THRESHOLD:
                        issues.append(ReviewIssue(
                            severity="LOW",
                            category="best_practices",
                            message=f"Function '{node.name}' is too long: {func_length} lines (threshold: {self.FUNCTION_LENGTH_THRESHOLD})",
                            line_number=node.lineno,
                            suggestion="Break this function into smaller, focused functions"
                        ))

                # Too many parameters
                args = node.args
                total_args = len(args.args) + len(args.kwonlyargs)
                if args.vararg:
                    total_args += 1
                if args.kwarg:
                    total_args += 1

                if total_args > self.MAX_PARAMETERS:
                    issues.append(ReviewIssue(
                        severity="LOW",
                        category="best_practices",
                        message=f"Function '{node.name}' has too many parameters: {total_args} (max: {self.MAX_PARAMETERS})",
                        line_number=node.lineno,
                        suggestion="Consider using a configuration object or reducing parameters"
                    ))

                # Non-descriptive names
                if self._is_non_descriptive_name(node.name):
                    issues.append(ReviewIssue(
                        severity="LOW",
                        category="best_practices",
                        message=f"Function '{node.name}' has non-descriptive name",
                        line_number=node.lineno,
                        suggestion="Use descriptive names that explain the function's purpose"
                    ))

                # Missing docstrings on public functions
                if not node.name.startswith('_'):
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        issues.append(ReviewIssue(
                            severity="INFO",
                            category="best_practices",
                            message=f"Public function '{node.name}' missing docstring",
                            line_number=node.lineno,
                            suggestion="Add a docstring explaining what the function does"
                        ))

        # Check nesting depth
        nesting_issues = self._check_nesting_depth(tree)
        issues.extend(nesting_issues)

        # Check for non-descriptive variable names
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if self._is_non_descriptive_name(node.id):
                    issues.append(ReviewIssue(
                        severity="LOW",
                        category="best_practices",
                        message=f"Variable '{node.id}' has non-descriptive name",
                        line_number=node.lineno if hasattr(node, 'lineno') else None,
                        suggestion="Use descriptive variable names"
                    ))

        return issues

    def _check_security(
        self,
        tree: ast.AST,
        code: str,
        lines: List[str]
    ) -> List[ReviewIssue]:
        """Check for security issues.

        Args:
            tree: AST tree
            code: Source code
            lines: Code lines

        Returns:
            List of issues found
        """
        issues = []

        for node in ast.walk(tree):
            # Check for dangerous functions (eval, exec, compile)
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id

                    if func_name in self.DANGEROUS_FUNCS:
                        issues.append(ReviewIssue(
                            severity="CRITICAL",
                            category="security",
                            message=f"Dangerous function '{func_name}()' detected",
                            line_number=node.lineno if hasattr(node, 'lineno') else None,
                            suggestion=f"Avoid using {func_name}() as it can execute arbitrary code"
                        ))

                # Check for os.system() or subprocess with shell=True
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in self.SHELL_FUNCS:
                        issues.append(ReviewIssue(
                            severity="HIGH",
                            category="security",
                            message=f"Shell command execution detected: {node.func.attr}()",
                            line_number=node.lineno if hasattr(node, 'lineno') else None,
                            suggestion="Use subprocess with shell=False and proper argument passing"
                        ))

                    # Check for subprocess.call/run with shell=True
                    if node.func.attr in ["call", "run", "Popen"]:
                        for keyword in node.keywords:
                            if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant):
                                if keyword.value.value is True:
                                    issues.append(ReviewIssue(
                                        severity="HIGH",
                                        category="security",
                                        message="subprocess called with shell=True",
                                        line_number=node.lineno if hasattr(node, 'lineno') else None,
                                        suggestion="Use shell=False and pass arguments as a list"
                                    ))

                    # Check for pickle.loads
                    if node.func.attr == "loads":
                        if isinstance(node.func.value, ast.Name) and node.func.value.id == "pickle":
                            issues.append(ReviewIssue(
                                severity="MEDIUM",
                                category="security",
                                message="pickle.loads() can execute arbitrary code",
                                line_number=node.lineno if hasattr(node, 'lineno') else None,
                                suggestion="Only unpickle data from trusted sources or use safer formats like JSON"
                            ))

            # Check for SQL injection patterns (string concatenation with SQL keywords)
            if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
                if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                    sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE"]
                    if any(keyword in node.left.value.upper() for keyword in sql_keywords):
                        issues.append(ReviewIssue(
                            severity="HIGH",
                            category="security",
                            message="Potential SQL injection: string concatenation with SQL query",
                            line_number=node.lineno if hasattr(node, 'lineno') else None,
                            suggestion="Use parameterized queries or ORM instead of string concatenation"
                        ))

        # Check for hardcoded secrets
        secret_issues = self._check_hardcoded_secrets(tree)
        issues.extend(secret_issues)

        # Check for open() with user input (potential path traversal)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "open":
                    # Check if first argument is a variable or user input
                    if node.args and isinstance(node.args[0], ast.Name):
                        issues.append(ReviewIssue(
                            severity="MEDIUM",
                            category="security",
                            message="File path from variable: validate to prevent path traversal",
                            line_number=node.lineno if hasattr(node, 'lineno') else None,
                            suggestion="Validate and sanitize file paths before use"
                        ))

        return issues

    def _check_style(
        self,
        tree: ast.AST,
        code: str,
        lines: List[str]
    ) -> List[ReviewIssue]:
        """Check for style violations.

        Args:
            tree: AST tree
            code: Source code
            lines: Code lines

        Returns:
            List of issues found
        """
        issues = []

        # Check naming conventions
        for node in ast.walk(tree):
            # Function/method names should be snake_case
            if isinstance(node, ast.FunctionDef):
                if not self._is_snake_case(node.name) and not node.name.startswith('__'):
                    issues.append(ReviewIssue(
                        severity="LOW",
                        category="style",
                        message=f"Function '{node.name}' should use snake_case",
                        line_number=node.lineno,
                        suggestion=f"Rename to '{self._to_snake_case(node.name)}'"
                    ))

                # Check for missing type hints on public functions
                if not node.name.startswith('_'):
                    has_type_hints = any(
                        arg.annotation for arg in node.args.args
                    ) or node.returns

                    if not has_type_hints:
                        issues.append(ReviewIssue(
                            severity="INFO",
                            category="style",
                            message=f"Function '{node.name}' missing type hints",
                            line_number=node.lineno,
                            suggestion="Add type hints to parameters and return value"
                        ))

            # Class names should be PascalCase
            if isinstance(node, ast.ClassDef):
                if not self._is_pascal_case(node.name):
                    issues.append(ReviewIssue(
                        severity="LOW",
                        category="style",
                        message=f"Class '{node.name}' should use PascalCase",
                        line_number=node.lineno,
                        suggestion=f"Rename to '{self._to_pascal_case(node.name)}'"
                    ))

            # Constants should be UPPER_CASE
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Check if it looks like a constant (module-level, immutable value)
                        if isinstance(node.value, ast.Constant):
                            if not self._is_upper_case(target.id) and not target.id.startswith('_'):
                                # Only flag if it's likely a constant (all caps or has numbers)
                                if target.id.isupper() or any(c.isdigit() for c in target.id):
                                    continue
                                if len(target.id) > 2 and target.id == target.id.upper():
                                    continue

                                issues.append(ReviewIssue(
                                    severity="INFO",
                                    category="style",
                                    message=f"Constant '{target.id}' should use UPPER_CASE",
                                    line_number=node.lineno if hasattr(node, 'lineno') else None,
                                    suggestion=f"Consider renaming to '{target.id.upper()}' if this is a constant"
                                ))

        # Check imports
        import_issues = self._check_imports(tree)
        issues.extend(import_issues)

        # Check for multiple statements on one line
        for i, line in enumerate(lines, 1):
            # Count semicolons (indicator of multiple statements)
            if ';' in line and not line.strip().startswith('#'):
                issues.append(ReviewIssue(
                    severity="LOW",
                    category="style",
                    message="Multiple statements on one line",
                    line_number=i,
                    suggestion="Put each statement on its own line"
                ))

        return issues

    def _check_hardcoded_secrets(self, tree: ast.AST) -> List[ReviewIssue]:
        """Check for hardcoded secrets and passwords.

        Args:
            tree: AST tree

        Returns:
            List of issues found
        """
        issues = []

        for node in ast.walk(tree):
            # Check assignments like: password = "secret123"
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id.lower()

                        # Check if variable name suggests a secret
                        if any(keyword in var_name for keyword in self.SECRET_KEYWORDS):
                            # Check if assigned a string literal
                            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                                # Ignore empty strings or placeholder values
                                if node.value.value and node.value.value not in ["", "TODO", "FIXME"]:
                                    issues.append(ReviewIssue(
                                        severity="HIGH",
                                        category="security",
                                        message=f"Hardcoded secret in variable '{target.id}'",
                                        line_number=node.lineno if hasattr(node, 'lineno') else None,
                                        suggestion="Use environment variables or a secrets management system"
                                    ))

        return issues

    def _check_imports(self, tree: ast.AST) -> List[ReviewIssue]:
        """Check import statements for issues.

        Args:
            tree: AST tree

        Returns:
            List of issues found
        """
        issues = []
        imported_names = set()
        used_names = set()

        for node in ast.walk(tree):
            # Check for wildcard imports
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == '*':
                        issues.append(ReviewIssue(
                            severity="MEDIUM",
                            category="style",
                            message=f"Wildcard import: from {node.module} import *",
                            line_number=node.lineno if hasattr(node, 'lineno') else None,
                            suggestion="Import specific names instead of using wildcard"
                        ))
                    else:
                        imported_names.add(alias.asname if alias.asname else alias.name)

            # Track imported names from regular imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.asname if alias.asname else alias.name)

            # Track used names
            if isinstance(node, ast.Name):
                used_names.add(node.id)

        # Check for unused imports (simple heuristic)
        unused = imported_names - used_names
        for name in unused:
            # Skip common exceptions
            if name not in ['__version__', '__all__']:
                issues.append(ReviewIssue(
                    severity="LOW",
                    category="style",
                    message=f"Unused import: {name}",
                    suggestion=f"Remove unused import '{name}'"
                ))

        return issues

    def _check_nesting_depth(self, tree: ast.AST) -> List[ReviewIssue]:
        """Check for excessive nesting depth.

        Args:
            tree: AST tree

        Returns:
            List of issues found
        """
        issues = []

        def get_depth(node, current_depth=0):
            """Recursively calculate nesting depth."""
            max_depth = current_depth

            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                    child_depth = get_depth(child, current_depth + 1)
                    max_depth = max(max_depth, child_depth)
                else:
                    child_depth = get_depth(child, current_depth)
                    max_depth = max(max_depth, child_depth)

            return max_depth

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                depth = get_depth(node)
                if depth > self.MAX_NESTED_DEPTH:
                    issues.append(ReviewIssue(
                        severity="MEDIUM",
                        category="best_practices",
                        message=f"Function '{node.name}' has excessive nesting: {depth} levels (max: {self.MAX_NESTED_DEPTH})",
                        line_number=node.lineno,
                        suggestion="Reduce nesting using early returns or extracting functions"
                    ))

        return issues

    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity.

        Args:
            tree: AST tree

        Returns:
            Complexity score
        """
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            # Decision points increase complexity
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity

    def _calculate_function_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a specific function.

        Args:
            func_node: Function AST node

        Returns:
            Complexity score
        """
        complexity = 1  # Base complexity

        for node in ast.walk(func_node):
            # Decision points increase complexity
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity

    def _is_non_descriptive_name(self, name: str) -> bool:
        """Check if a name is non-descriptive.

        Args:
            name: Variable or function name

        Returns:
            True if non-descriptive
        """
        # Skip magic methods and private names
        if name.startswith('_'):
            return False

        # Common non-descriptive names
        non_descriptive = ['x', 'y', 'z', 'i', 'j', 'k', 'foo', 'bar', 'baz', 'tmp', 'temp', 'data', 'item']
        return name in non_descriptive

    def _is_snake_case(self, name: str) -> bool:
        """Check if name follows snake_case convention."""
        return name.islower() or '_' in name and name.replace('_', '').islower()

    def _is_pascal_case(self, name: str) -> bool:
        """Check if name follows PascalCase convention."""
        return name[0].isupper() and '_' not in name

    def _is_upper_case(self, name: str) -> bool:
        """Check if name is UPPER_CASE."""
        return name.isupper()

    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase."""
        return ''.join(word.capitalize() for word in name.split('_'))

    def _calculate_summary(self, issues: List[ReviewIssue]) -> Dict[str, Any]:
        """Calculate summary statistics.

        Args:
            issues: List of issues

        Returns:
            Summary dictionary
        """
        by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        by_category = {"best_practices": 0, "security": 0, "style": 0, "syntax": 0}

        for issue in issues:
            by_severity[issue.severity] += 1
            by_category[issue.category] += 1

        return {
            "total_issues": len(issues),
            "by_severity": by_severity,
            "by_category": by_category
        }

    def _calculate_score(self, issues: List[ReviewIssue]) -> int:
        """Calculate quality score (0-100).

        Args:
            issues: List of issues

        Returns:
            Score from 0 to 100
        """
        score = 100

        for issue in issues:
            score -= self.SEVERITY_SCORES.get(issue.severity, 0)

        return max(0, score)  # Ensure non-negative
