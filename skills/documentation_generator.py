"""Documentation Generator Skill for Meton.

This skill generates documentation from Python code including:
- Docstrings in multiple formats (Google, NumPy, Sphinx)
- README files from project structure
- API documentation from modules

Example:
    >>> from skills.documentation_generator import DocumentationGeneratorSkill
    >>>
    >>> skill = DocumentationGeneratorSkill()
    >>> result = skill.execute({
    ...     "code": "def add(a, b):\\n    return a + b",
    ...     "doc_type": "docstring",
    ...     "style": "google"
    ... })
    >>> print(result["documentation"])
"""

import ast
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from skills.base import BaseSkill, SkillValidationError, SkillExecutionError


class DocumentationGeneratorSkill(BaseSkill):
    """Skill that generates documentation from code.

    Generates various types of documentation:
    - Docstrings in Google, NumPy, and Sphinx formats
    - README files from project structure
    - API documentation from modules

    Attributes:
        name: Skill identifier "documentation_generator"
        description: What the skill does
        version: Skill version
        enabled: Whether skill is enabled
    """

    name = "documentation_generator"
    description = "Generates docstrings, README files, and API documentation"
    version = "1.0.0"
    enabled = True

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data.

        Args:
            input_data: Must contain "doc_type" and appropriate fields

        Returns:
            True if validation passes

        Raises:
            SkillValidationError: If validation fails
        """
        super().validate_input(input_data)

        if "doc_type" not in input_data:
            raise SkillValidationError("Missing required field: 'doc_type'")

        doc_type = input_data["doc_type"]
        valid_types = ["docstring", "readme", "api_docs"]
        if doc_type not in valid_types:
            raise SkillValidationError(
                f"Invalid doc_type: {doc_type}. Must be one of {valid_types}"
            )

        # Validate based on doc_type
        if doc_type == "docstring":
            if "code" not in input_data:
                raise SkillValidationError("Missing required field: 'code'")
            if not isinstance(input_data["code"], str):
                raise SkillValidationError("Field 'code' must be a string")
            if not input_data["code"].strip():
                raise SkillValidationError("Field 'code' cannot be empty")

            # Validate style if provided
            if "style" in input_data:
                style = input_data["style"]
                valid_styles = ["google", "numpy", "sphinx"]
                if style not in valid_styles:
                    raise SkillValidationError(
                        f"Invalid style: {style}. Must be one of {valid_styles}"
                    )

        elif doc_type == "readme":
            # README can be generated with just project_name, or with project_path/code
            pass  # No strict requirements for README

        elif doc_type == "api_docs":
            if "code" not in input_data and "module_path" not in input_data:
                raise SkillValidationError(
                    "Missing required field: 'code' or 'module_path'"
                )

        return True

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute documentation generation.

        Args:
            input_data: Dictionary with:
                - doc_type: "docstring"|"readme"|"api_docs" (required)
                - code: Source code string (for docstring/api_docs)
                - style: "google"|"numpy"|"sphinx" (for docstring, default: "google")
                - project_path: Path to project (for readme)
                - module_path: Path to module (for api_docs)
                - project_name: Name of project (optional, for readme)

        Returns:
            Dictionary with:
                - success: bool
                - documentation: Generated documentation string
                - doc_count: Number of items documented
                - error: Error message (if success=False)

        Raises:
            SkillExecutionError: If execution fails
        """
        try:
            self.validate_input(input_data)

            doc_type = input_data["doc_type"]

            if doc_type == "docstring":
                return self._generate_docstring(
                    input_data["code"],
                    input_data.get("style", "google")
                )
            elif doc_type == "readme":
                return self._generate_readme(input_data)
            elif doc_type == "api_docs":
                return self._generate_api_docs(input_data)

        except SkillValidationError as e:
            return {
                "success": False,
                "documentation": "",
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "documentation": "",
                "error": f"Execution failed: {str(e)}"
            }

    def _generate_docstring(self, code: str, style: str) -> Dict[str, Any]:
        """Generate docstring for code.

        Args:
            code: Python source code
            style: Docstring style (google/numpy/sphinx)

        Returns:
            Dictionary with success, documentation, and doc_count
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "success": False,
                "documentation": "",
                "error": f"Syntax error in code: {str(e)}"
            }

        docstrings = []
        doc_count = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                docstring = self._create_function_docstring(node, style)
                docstrings.append(f"# Function: {node.name}\n{docstring}")
                doc_count += 1
            elif isinstance(node, ast.AsyncFunctionDef):
                docstring = self._create_function_docstring(node, style, is_async=True)
                docstrings.append(f"# Async Function: {node.name}\n{docstring}")
                doc_count += 1
            elif isinstance(node, ast.ClassDef):
                docstring = self._create_class_docstring(node, style)
                docstrings.append(f"# Class: {node.name}\n{docstring}")
                doc_count += 1

        if not docstrings:
            return {
                "success": False,
                "documentation": "",
                "error": "No functions or classes found in code"
            }

        return {
            "success": True,
            "documentation": "\n\n".join(docstrings),
            "doc_count": doc_count,
            "style": style
        }

    def _create_function_docstring(
        self,
        node: ast.FunctionDef,
        style: str,
        is_async: bool = False
    ) -> str:
        """Create docstring for a function.

        Args:
            node: AST FunctionDef node
            style: Docstring style
            is_async: Whether function is async

        Returns:
            Formatted docstring
        """
        # Extract function info
        func_name = node.name
        args = self._extract_arguments(node)
        returns = self._extract_return_type(node)
        raises = self._extract_raises(node)

        # Get brief description
        brief = self._generate_brief_description(func_name, is_async)

        # Generate based on style
        if style == "google":
            return self._format_google_style(brief, args, returns, raises)
        elif style == "numpy":
            return self._format_numpy_style(brief, args, returns, raises)
        elif style == "sphinx":
            return self._format_sphinx_style(brief, args, returns, raises)

    def _create_class_docstring(self, node: ast.ClassDef, style: str) -> str:
        """Create docstring for a class.

        Args:
            node: AST ClassDef node
            style: Docstring style

        Returns:
            Formatted docstring
        """
        class_name = node.name
        bases = [base.id for base in node.bases if isinstance(base, ast.Name)]

        # Count methods
        methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        method_count = len(methods)

        brief = f"Class {class_name}"
        if bases:
            brief += f" (inherits from {', '.join(bases)})"
        brief += f" with {method_count} method(s)."

        # For classes, we keep it simple across all styles
        if style == "google":
            docstring = f'"""{brief}\n\n'
            if bases:
                docstring += "Attributes:\n"
                docstring += "    # Add your attributes here\n\n"
            docstring += '"""'
        elif style == "numpy":
            docstring = f'"""{brief}\n\n'
            if bases:
                docstring += "Attributes\n"
                docstring += "----------\n"
                docstring += "# Add your attributes here\n\n"
            docstring += '"""'
        elif style == "sphinx":
            docstring = f'"""{brief}\n\n'
            if bases:
                docstring += ":ivar: Add your attributes here\n"
            docstring += '"""'

        return docstring

    def _extract_arguments(self, node: ast.FunctionDef) -> List[Dict[str, Any]]:
        """Extract function arguments with type hints.

        Args:
            node: AST FunctionDef node

        Returns:
            List of argument dictionaries with name, type, and default
        """
        args = []
        func_args = node.args

        # Regular args
        all_args = func_args.args
        defaults = func_args.defaults
        num_defaults = len(defaults)
        num_args = len(all_args)

        for i, arg in enumerate(all_args):
            # Skip 'self' and 'cls'
            if arg.arg in ['self', 'cls']:
                continue

            arg_info = {
                "name": arg.arg,
                "type": self._get_type_hint(arg),
                "default": None
            }

            # Check if this arg has a default value
            default_offset = i - (num_args - num_defaults)
            if default_offset >= 0:
                default_node = defaults[default_offset]
                arg_info["default"] = ast.unparse(default_node)

            args.append(arg_info)

        # *args
        if func_args.vararg:
            args.append({
                "name": f"*{func_args.vararg.arg}",
                "type": self._get_type_hint(func_args.vararg),
                "default": None
            })

        # Keyword-only arguments (come after *args)
        kwonlyargs = func_args.kwonlyargs
        kw_defaults = func_args.kw_defaults

        for i, arg in enumerate(kwonlyargs):
            arg_info = {
                "name": arg.arg,
                "type": self._get_type_hint(arg),
                "default": None
            }

            # Check if this kwonly arg has a default value
            if i < len(kw_defaults) and kw_defaults[i] is not None:
                arg_info["default"] = ast.unparse(kw_defaults[i])

            args.append(arg_info)

        # **kwargs
        if func_args.kwarg:
            args.append({
                "name": f"**{func_args.kwarg.arg}",
                "type": self._get_type_hint(func_args.kwarg),
                "default": None
            })

        return args

    def _get_type_hint(self, arg: ast.arg) -> str:
        """Extract type hint from argument.

        Args:
            arg: AST arg node

        Returns:
            Type hint string or "Any"
        """
        if arg.annotation:
            return ast.unparse(arg.annotation)
        return "Any"

    def _extract_return_type(self, node: ast.FunctionDef) -> Optional[str]:
        """Extract return type annotation.

        Args:
            node: AST FunctionDef node

        Returns:
            Return type string or None
        """
        if node.returns:
            return ast.unparse(node.returns)
        return None

    def _extract_raises(self, node: ast.FunctionDef) -> List[str]:
        """Extract exceptions that function might raise.

        Args:
            node: AST FunctionDef node

        Returns:
            List of exception names
        """
        raises = []
        for child in ast.walk(node):
            if isinstance(child, ast.Raise):
                if child.exc:
                    if isinstance(child.exc, ast.Call):
                        if isinstance(child.exc.func, ast.Name):
                            raises.append(child.exc.func.id)
                    elif isinstance(child.exc, ast.Name):
                        raises.append(child.exc.id)
        return list(set(raises))  # Remove duplicates

    def _generate_brief_description(self, func_name: str, is_async: bool = False) -> str:
        """Generate brief description from function name.

        Args:
            func_name: Function name
            is_async: Whether function is async

        Returns:
            Brief description
        """
        # Convert snake_case to words
        words = func_name.replace('_', ' ')

        prefix = "Asynchronously " if is_async else ""

        # Add verb based on common patterns
        if func_name.startswith('get_'):
            return f"{prefix}Get {words[4:]}"
        elif func_name.startswith('set_'):
            return f"{prefix}Set {words[4:]}"
        elif func_name.startswith('is_'):
            return f"{prefix}Check if {words[3:]}"
        elif func_name.startswith('has_'):
            return f"{prefix}Check if has {words[4:]}"
        elif func_name.startswith('create_'):
            return f"{prefix}Create {words[7:]}"
        elif func_name.startswith('delete_'):
            return f"{prefix}Delete {words[7:]}"
        elif func_name.startswith('update_'):
            return f"{prefix}Update {words[7:]}"
        elif func_name.startswith('calculate_'):
            return f"{prefix}Calculate {words[10:]}"
        elif func_name.startswith('compute_'):
            return f"{prefix}Compute {words[8:]}"
        elif func_name.startswith('process_'):
            return f"{prefix}Process {words[8:]}"
        else:
            return f"{prefix}{words.capitalize()}"

    def _format_google_style(
        self,
        brief: str,
        args: List[Dict[str, Any]],
        returns: Optional[str],
        raises: List[str]
    ) -> str:
        """Format docstring in Google style.

        Args:
            brief: Brief description
            args: List of arguments
            returns: Return type
            raises: List of exceptions

        Returns:
            Formatted docstring
        """
        lines = [f'"""{brief}.']

        if args:
            lines.append("")
            lines.append("Args:")
            for arg in args:
                arg_name = arg["name"]
                arg_type = arg["type"]
                default = arg["default"]

                if default:
                    lines.append(f"    {arg_name} ({arg_type}, optional): Description. Defaults to {default}.")
                else:
                    lines.append(f"    {arg_name} ({arg_type}): Description.")

        if returns:
            lines.append("")
            lines.append("Returns:")
            lines.append(f"    {returns}: Description.")

        if raises:
            lines.append("")
            lines.append("Raises:")
            for exc in raises:
                lines.append(f"    {exc}: Description.")

        lines.append('"""')
        return "\n".join(lines)

    def _format_numpy_style(
        self,
        brief: str,
        args: List[Dict[str, Any]],
        returns: Optional[str],
        raises: List[str]
    ) -> str:
        """Format docstring in NumPy style.

        Args:
            brief: Brief description
            args: List of arguments
            returns: Return type
            raises: List of exceptions

        Returns:
            Formatted docstring
        """
        lines = [f'"""{brief}.']

        if args:
            lines.append("")
            lines.append("Parameters")
            lines.append("----------")
            for arg in args:
                arg_name = arg["name"]
                arg_type = arg["type"]
                default = arg["default"]

                if default:
                    lines.append(f"{arg_name} : {arg_type}, optional")
                    lines.append(f"    Description. Defaults to {default}.")
                else:
                    lines.append(f"{arg_name} : {arg_type}")
                    lines.append("    Description.")

        if returns:
            lines.append("")
            lines.append("Returns")
            lines.append("-------")
            lines.append(f"{returns}")
            lines.append("    Description.")

        if raises:
            lines.append("")
            lines.append("Raises")
            lines.append("------")
            for exc in raises:
                lines.append(f"{exc}")
                lines.append("    Description.")

        lines.append('"""')
        return "\n".join(lines)

    def _format_sphinx_style(
        self,
        brief: str,
        args: List[Dict[str, Any]],
        returns: Optional[str],
        raises: List[str]
    ) -> str:
        """Format docstring in Sphinx style.

        Args:
            brief: Brief description
            args: List of arguments
            returns: Return type
            raises: List of exceptions

        Returns:
            Formatted docstring
        """
        lines = [f'"""{brief}.']

        if args or returns or raises:
            lines.append("")

        for arg in args:
            arg_name = arg["name"].lstrip('*')  # Remove * for *args/**kwargs
            arg_type = arg["type"]
            default = arg["default"]

            lines.append(f":param {arg_name}: Description.")
            lines.append(f":type {arg_name}: {arg_type}")
            if default:
                lines.append(f":default {arg_name}: {default}")

        if returns:
            lines.append(":return: Description.")
            lines.append(f":rtype: {returns}")

        for exc in raises:
            lines.append(f":raises {exc}: Description.")

        lines.append('"""')
        return "\n".join(lines)

    def _generate_readme(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate README from project structure.

        Args:
            input_data: Dictionary with project_path or code

        Returns:
            Dictionary with success, documentation
        """
        project_name = input_data.get("project_name", "Project")

        readme_sections = []

        # Title
        readme_sections.append(f"# {project_name}\n")

        # Overview
        readme_sections.append("## Overview\n")
        readme_sections.append("Brief description of what this project does.\n")

        # Installation
        readme_sections.append("## Installation\n")
        readme_sections.append("```bash")
        readme_sections.append("# Installation instructions")
        readme_sections.append("pip install -r requirements.txt")
        readme_sections.append("```\n")

        # Usage
        readme_sections.append("## Usage\n")
        readme_sections.append("```python")
        readme_sections.append("# Usage example")
        readme_sections.append("# Add your usage examples here")
        readme_sections.append("```\n")

        # Features
        if "project_path" in input_data:
            path = Path(input_data["project_path"])
            if path.exists() and path.is_dir():
                py_files = list(path.rglob("*.py"))
                if py_files:
                    readme_sections.append("## Features\n")
                    readme_sections.append(f"- {len(py_files)} Python modules")
                    readme_sections.append("- Add more features here\n")

        # API Reference
        readme_sections.append("## API Reference\n")
        readme_sections.append("See documentation for detailed API reference.\n")

        # Contributing
        readme_sections.append("## Contributing\n")
        readme_sections.append("Contributions are welcome! Please see CONTRIBUTING.md for guidelines.\n")

        # License
        readme_sections.append("## License\n")
        readme_sections.append("This project is licensed under the MIT License.\n")

        documentation = "\n".join(readme_sections)

        return {
            "success": True,
            "documentation": documentation,
            "doc_count": 7,  # Number of sections
            "sections": ["Overview", "Installation", "Usage", "Features", "API Reference", "Contributing", "License"]
        }

    def _generate_api_docs(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate API documentation from module.

        Args:
            input_data: Dictionary with code or module_path

        Returns:
            Dictionary with success, documentation
        """
        code = input_data.get("code")

        if not code and "module_path" in input_data:
            module_path = Path(input_data["module_path"])
            if module_path.exists():
                with open(module_path, 'r') as f:
                    code = f.read()

        if not code:
            return {
                "success": False,
                "documentation": "",
                "error": "No code provided and module_path not found"
            }

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "success": False,
                "documentation": "",
                "error": f"Syntax error in code: {str(e)}"
            }

        api_docs = []
        doc_count = 0

        # Extract module docstring
        module_doc = ast.get_docstring(tree)
        if module_doc:
            api_docs.append(f"# Module Documentation\n\n{module_doc}\n")

        # Extract classes
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
        if classes:
            api_docs.append("## Classes\n")
            for cls in classes:
                if not cls.name.startswith('_'):  # Only public classes
                    api_docs.append(f"### `{cls.name}`\n")

                    cls_doc = ast.get_docstring(cls)
                    if cls_doc:
                        api_docs.append(f"{cls_doc}\n")
                    else:
                        api_docs.append("No documentation available.\n")

                    # List methods
                    methods = [n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    public_methods = [m for m in methods if not m.name.startswith('_') or m.name == '__init__']

                    if public_methods:
                        api_docs.append("**Methods:**\n")
                        for method in public_methods:
                            sig = self._get_function_signature(method)
                            api_docs.append(f"- `{sig}`")

                    api_docs.append("")
                    doc_count += 1

        # Extract functions
        functions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        public_functions = [f for f in functions if not f.name.startswith('_')]

        if public_functions:
            api_docs.append("## Functions\n")
            for func in public_functions:
                sig = self._get_function_signature(func)
                api_docs.append(f"### `{sig}`\n")

                func_doc = ast.get_docstring(func)
                if func_doc:
                    api_docs.append(f"{func_doc}\n")
                else:
                    api_docs.append("No documentation available.\n")

                doc_count += 1

        if not api_docs:
            return {
                "success": False,
                "documentation": "",
                "error": "No public APIs found in code"
            }

        documentation = "\n".join(api_docs)

        return {
            "success": True,
            "documentation": documentation,
            "doc_count": doc_count,
            "classes": len(classes),
            "functions": len(public_functions)
        }

    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """Get function signature as string.

        Args:
            node: AST FunctionDef node

        Returns:
            Function signature string
        """
        args = self._extract_arguments(node)

        # Build argument list
        arg_strs = []
        for arg in args:
            arg_name = arg["name"]
            arg_type = arg["type"]
            default = arg["default"]

            if arg_type and arg_type != "Any":
                arg_str = f"{arg_name}: {arg_type}"
            else:
                arg_str = arg_name

            if default:
                arg_str += f"={default}"

            arg_strs.append(arg_str)

        # Add self/cls if method
        params = ", ".join(arg_strs)

        # Add return type
        returns = self._extract_return_type(node)
        if returns:
            return f"{node.name}({params}) -> {returns}"
        else:
            return f"{node.name}({params})"
