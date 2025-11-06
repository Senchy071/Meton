"""Code Explainer Skill for Meton.

This skill analyzes Python code and provides detailed explanations including:
- Summary and detailed explanation
- Key concepts and patterns
- Complexity assessment
- Improvement suggestions

Example:
    >>> from skills.code_explainer import CodeExplainerSkill
    >>>
    >>> skill = CodeExplainerSkill()
    >>> result = skill.execute({
    ...     "code": "def factorial(n):\\n    return 1 if n <= 1 else n * factorial(n-1)",
    ...     "language": "python"
    ... })
    >>> print(result["summary"])
"""

import ast
from typing import Dict, Any, List, Set, Optional
from skills.base import BaseSkill, SkillValidationError, SkillExecutionError


class CodeExplainerSkill(BaseSkill):
    """Skill that analyzes and explains code in detail.

    Analyzes Python code using AST parsing to provide:
    - Brief summary
    - Detailed explanation
    - Key concepts
    - Complexity assessment
    - Improvement suggestions

    Attributes:
        name: Skill identifier "code_explainer"
        description: What the skill does
        version: Skill version
        enabled: Whether skill is enabled
    """

    name = "code_explainer"
    description = "Analyzes and explains code with context-aware understanding"
    version = "1.0.0"
    enabled = True

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
        if "language" in input_data:
            language = input_data["language"]
            if language not in ["python", "py"]:
                raise SkillValidationError(
                    f"Unsupported language: {language}. Only 'python' is supported."
                )

        return True

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code explanation.

        Args:
            input_data: Dictionary with:
                - code: Source code string (required)
                - language: Programming language (optional, default: "python")
                - context: Additional context (optional)

        Returns:
            Dictionary with:
                - success: bool
                - summary: Brief 1-2 sentence overview
                - detailed_explanation: Comprehensive explanation
                - key_concepts: List of concepts
                - complexity: "simple"|"moderate"|"complex"
                - suggestions: List of improvement suggestions
                - error: Error message (if success=False)

        Raises:
            SkillExecutionError: If execution fails
        """
        try:
            # Validate input
            self.validate_input(input_data)

            code = input_data["code"]
            context = input_data.get("context", "")

            # Parse code with AST
            try:
                tree = ast.parse(code)
            except SyntaxError as e:
                return {
                    "success": False,
                    "error": f"Syntax error in code: {str(e)}",
                    "summary": "Invalid Python syntax",
                    "detailed_explanation": f"The code contains a syntax error: {str(e)}",
                    "key_concepts": [],
                    "complexity": "unknown",
                    "suggestions": ["Fix syntax errors before analyzing"]
                }

            # Analyze code
            analysis = self._analyze_code(tree, code, context)

            return {
                "success": True,
                **analysis
            }

        except SkillValidationError as e:
            return {
                "success": False,
                "error": str(e),
                "summary": "",
                "detailed_explanation": "",
                "key_concepts": [],
                "complexity": "unknown",
                "suggestions": []
            }
        except Exception as e:
            raise SkillExecutionError(f"Code explanation failed: {str(e)}")

    def _analyze_code(self, tree: ast.AST, code: str, context: str) -> Dict[str, Any]:
        """Analyze parsed AST and generate explanation.

        Args:
            tree: Parsed AST
            code: Original source code
            context: Additional context

        Returns:
            Dictionary with analysis results
        """
        # Extract code elements
        functions = self._extract_functions(tree)
        classes = self._extract_classes(tree)
        imports = self._extract_imports(tree)
        patterns = self._detect_patterns(tree)

        # Calculate complexity
        complexity_score = self._calculate_complexity(tree)
        complexity_level = self._assess_complexity(complexity_score)

        # Generate explanations
        summary = self._generate_summary(functions, classes, imports, patterns)
        detailed_explanation = self._generate_detailed_explanation(
            functions, classes, imports, patterns, code, context
        )
        key_concepts = self._extract_key_concepts(functions, classes, patterns)
        suggestions = self._generate_suggestions(
            functions, classes, patterns, complexity_score
        )

        return {
            "summary": summary,
            "detailed_explanation": detailed_explanation,
            "key_concepts": key_concepts,
            "complexity": complexity_level,
            "suggestions": suggestions
        }

    def _extract_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract function definitions from AST.

        Args:
            tree: Parsed AST

        Returns:
            List of function information dictionaries
        """
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "is_async": False,
                    "has_decorators": len(node.decorator_list) > 0,
                    "decorators": [self._get_decorator_name(dec) for dec in node.decorator_list],
                    "returns": self._get_return_annotation(node),
                    "docstring": ast.get_docstring(node)
                }
                functions.append(func_info)
            elif isinstance(node, ast.AsyncFunctionDef):
                func_info = {
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "is_async": True,
                    "has_decorators": len(node.decorator_list) > 0,
                    "decorators": [self._get_decorator_name(dec) for dec in node.decorator_list],
                    "returns": self._get_return_annotation(node),
                    "docstring": ast.get_docstring(node)
                }
                functions.append(func_info)
        return functions

    def _extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract class definitions from AST.

        Args:
            tree: Parsed AST

        Returns:
            List of class information dictionaries
        """
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append({
                            "name": item.name,
                            "is_async": isinstance(item, ast.AsyncFunctionDef)
                        })

                class_info = {
                    "name": node.name,
                    "bases": [self._get_name(base) for base in node.bases],
                    "methods": methods,
                    "has_decorators": len(node.decorator_list) > 0,
                    "docstring": ast.get_docstring(node)
                }
                classes.append(class_info)
        return classes

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements from AST.

        Args:
            tree: Parsed AST

        Returns:
            List of imported module names
        """
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
        return imports

    def _detect_patterns(self, tree: ast.AST) -> Dict[str, bool]:
        """Detect common code patterns.

        Args:
            tree: Parsed AST

        Returns:
            Dictionary of detected patterns
        """
        patterns = {
            "has_loops": False,
            "has_recursion": False,
            "has_async": False,
            "has_list_comprehension": False,
            "has_generator": False,
            "has_context_manager": False,
            "has_exception_handling": False,
            "has_lambda": False
        }

        function_names = set()

        for node in ast.walk(tree):
            # Detect loops
            if isinstance(node, (ast.For, ast.While)):
                patterns["has_loops"] = True

            # Collect function names for recursion detection
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_names.add(node.name)

            # Detect async
            if isinstance(node, (ast.AsyncFunctionDef, ast.AsyncFor, ast.AsyncWith)):
                patterns["has_async"] = True

            # Detect comprehensions
            if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp)):
                patterns["has_list_comprehension"] = True

            # Detect generators
            if isinstance(node, ast.GeneratorExp) or \
               (isinstance(node, ast.FunctionDef) and any(isinstance(n, ast.Yield) for n in ast.walk(node))):
                patterns["has_generator"] = True

            # Detect context managers
            if isinstance(node, (ast.With, ast.AsyncWith)):
                patterns["has_context_manager"] = True

            # Detect exception handling
            if isinstance(node, (ast.Try, ast.ExceptHandler, ast.Raise)):
                patterns["has_exception_handling"] = True

            # Detect lambdas
            if isinstance(node, ast.Lambda):
                patterns["has_lambda"] = True

        # Detect recursion by checking if function calls itself
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in function_names:
                    patterns["has_recursion"] = True
                    break

        return patterns

    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity.

        Cyclomatic complexity = number of decision points + 1
        Decision points: if, for, while, except, and, or, etc.

        Args:
            tree: Parsed AST

        Returns:
            Complexity score
        """
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            # Decision points
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                # and/or operators
                complexity += len(node.values) - 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Each function adds 1 to complexity
                complexity += 1

        return complexity

    def _assess_complexity(self, score: int) -> str:
        """Assess complexity level based on score.

        Args:
            score: Complexity score

        Returns:
            Complexity level: "simple", "moderate", or "complex"
        """
        if score <= 5:
            return "simple"
        elif score <= 10:
            return "moderate"
        else:
            return "complex"

    def _generate_summary(
        self,
        functions: List[Dict[str, Any]],
        classes: List[Dict[str, Any]],
        imports: List[str],
        patterns: Dict[str, bool]
    ) -> str:
        """Generate brief summary of code.

        Args:
            functions: List of function definitions
            classes: List of class definitions
            imports: List of imports
            patterns: Detected patterns

        Returns:
            Brief 1-2 sentence summary
        """
        parts = []

        # Count elements
        func_count = len(functions)
        class_count = len(classes)

        if class_count > 0:
            parts.append(f"{class_count} class{'es' if class_count > 1 else ''}")
        if func_count > 0:
            parts.append(f"{func_count} function{'s' if func_count > 1 else ''}")

        # Special patterns
        special = []
        if patterns.get("has_async"):
            special.append("async operations")
        if patterns.get("has_recursion"):
            special.append("recursion")

        summary = "This code defines "
        if parts:
            summary += ", ".join(parts)
        else:
            summary += "a script"

        if special:
            summary += f" with {', '.join(special)}"

        summary += "."

        # Add import info
        if imports:
            summary += f" It uses {len(imports)} import{'s' if len(imports) > 1 else ''}."

        return summary

    def _generate_detailed_explanation(
        self,
        functions: List[Dict[str, Any]],
        classes: List[Dict[str, Any]],
        imports: List[str],
        patterns: Dict[str, bool],
        code: str,
        context: str
    ) -> str:
        """Generate detailed code explanation.

        Args:
            functions: List of function definitions
            classes: List of class definitions
            imports: List of imports
            patterns: Detected patterns
            code: Original source code
            context: Additional context

        Returns:
            Comprehensive explanation
        """
        explanation = []

        # Context
        if context:
            explanation.append(f"Context: {context}")
            explanation.append("")

        # Imports
        if imports:
            explanation.append("Dependencies:")
            explanation.append(f"- The code imports {len(imports)} module(s): {', '.join(imports[:5])}")
            if len(imports) > 5:
                explanation.append(f"  and {len(imports) - 5} more...")
            explanation.append("")

        # Classes
        if classes:
            explanation.append("Classes:")
            for cls in classes:
                base_info = f" (inherits from {', '.join(cls['bases'])})" if cls['bases'] else ""
                explanation.append(f"- {cls['name']}{base_info}")
                if cls['methods']:
                    method_names = [m['name'] for m in cls['methods']]
                    explanation.append(f"  Methods: {', '.join(method_names)}")
                if cls['docstring']:
                    explanation.append(f"  Purpose: {cls['docstring'].split('.')[0]}.")
            explanation.append("")

        # Functions
        if functions:
            explanation.append("Functions:")
            for func in functions:
                async_prefix = "async " if func['is_async'] else ""
                args_str = f"({', '.join(func['args'])})" if func['args'] else "()"
                explanation.append(f"- {async_prefix}{func['name']}{args_str}")
                if func['decorators']:
                    explanation.append(f"  Decorators: {', '.join(func['decorators'])}")
                if func['docstring']:
                    explanation.append(f"  Purpose: {func['docstring'].split('.')[0]}.")
            explanation.append("")

        # Patterns
        active_patterns = [k.replace("has_", "").replace("_", " ")
                          for k, v in patterns.items() if v]
        if active_patterns:
            explanation.append("Code Patterns:")
            explanation.append(f"- This code uses: {', '.join(active_patterns)}")
            explanation.append("")

        # Logic flow
        explanation.append("Logic Flow:")
        if patterns.get("has_recursion"):
            explanation.append("- Uses recursive approach (function calls itself)")
        if patterns.get("has_loops"):
            explanation.append("- Contains iteration logic (loops)")
        if patterns.get("has_async"):
            explanation.append("- Implements asynchronous operations")
        if patterns.get("has_exception_handling"):
            explanation.append("- Includes error handling with try/except")
        if patterns.get("has_context_manager"):
            explanation.append("- Uses context managers (with statements) for resource management")

        if not any(patterns.values()):
            explanation.append("- Straightforward sequential execution")

        return "\n".join(explanation)

    def _extract_key_concepts(
        self,
        functions: List[Dict[str, Any]],
        classes: List[Dict[str, Any]],
        patterns: Dict[str, bool]
    ) -> List[str]:
        """Extract key programming concepts from code.

        Args:
            functions: List of function definitions
            classes: List of class definitions
            patterns: Detected patterns

        Returns:
            List of key concepts
        """
        concepts = set()

        # Basic concepts
        if functions:
            concepts.add("functions")
        if classes:
            concepts.add("object-oriented programming")
            concepts.add("classes")

        # Pattern-based concepts
        if patterns.get("has_recursion"):
            concepts.add("recursion")
        if patterns.get("has_async"):
            concepts.add("async/await")
            concepts.add("asynchronous programming")
        if patterns.get("has_loops"):
            concepts.add("loops")
            concepts.add("iteration")
        if patterns.get("has_list_comprehension"):
            concepts.add("list comprehensions")
        if patterns.get("has_generator"):
            concepts.add("generators")
        if patterns.get("has_context_manager"):
            concepts.add("context managers")
        if patterns.get("has_exception_handling"):
            concepts.add("exception handling")
        if patterns.get("has_lambda"):
            concepts.add("lambda functions")

        # Decorator concepts
        for func in functions:
            if func['has_decorators']:
                concepts.add("decorators")
                break

        # Inheritance
        for cls in classes:
            if cls['bases']:
                concepts.add("inheritance")
                break

        return sorted(list(concepts))

    def _generate_suggestions(
        self,
        functions: List[Dict[str, Any]],
        classes: List[Dict[str, Any]],
        patterns: Dict[str, bool],
        complexity_score: int
    ) -> List[str]:
        """Generate improvement suggestions.

        Args:
            functions: List of function definitions
            classes: List of class definitions
            patterns: Detected patterns
            complexity_score: Complexity score

        Returns:
            List of suggestions
        """
        suggestions = []

        # Complexity suggestions
        if complexity_score > 10:
            suggestions.append(
                "Consider breaking down complex functions into smaller, more manageable pieces"
            )

        # Documentation suggestions
        missing_docs = []
        for func in functions:
            if not func['docstring']:
                missing_docs.append(func['name'])

        for cls in classes:
            if not cls['docstring']:
                missing_docs.append(f"class {cls['name']}")

        if missing_docs:
            if len(missing_docs) <= 3:
                suggestions.append(
                    f"Add docstrings to: {', '.join(missing_docs)}"
                )
            else:
                suggestions.append(
                    f"Add docstrings to {len(missing_docs)} functions/classes for better documentation"
                )

        # Type hints suggestion
        missing_types = []
        for func in functions:
            if not func['returns']:
                missing_types.append(func['name'])

        if missing_types and len(missing_types) <= 3:
            suggestions.append(
                f"Consider adding type hints to: {', '.join(missing_types)}"
            )
        elif len(missing_types) > 3:
            suggestions.append(
                "Consider adding type hints for better code clarity"
            )

        # Pattern-specific suggestions
        if patterns.get("has_recursion") and not patterns.get("has_exception_handling"):
            suggestions.append(
                "Add base case validation to prevent stack overflow in recursive functions"
            )

        if patterns.get("has_async") and not patterns.get("has_exception_handling"):
            suggestions.append(
                "Add error handling for async operations to handle network/timeout issues"
            )

        # If no suggestions, add positive feedback
        if not suggestions:
            suggestions.append("Code looks well-structured with no immediate improvements needed")

        return suggestions

    # Helper methods

    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Get decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            return self._get_name(decorator.func)
        else:
            return "decorator"

    def _get_return_annotation(self, node: ast.FunctionDef) -> Optional[str]:
        """Get return type annotation from function."""
        if node.returns:
            return self._get_name(node.returns)
        return None

    def _get_name(self, node: ast.expr) -> str:
        """Get name from AST expression node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name(node.value)}[...]"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        else:
            return "unknown"
