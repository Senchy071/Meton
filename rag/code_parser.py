"""
Code Parser - AST-based Python file parser for code intelligence.

Extracts functions, classes, module docstrings, and imports from Python files
using the ast module. Provides structured data for chunking and indexing.
"""

import ast
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class CodeParser:
    """
    Parse Python files using AST to extract code elements.

    Extracts:
    - Functions with signatures, docstrings, and source code
    - Classes with methods, docstrings, and source code
    - Module-level docstrings
    - Import statements
    """

    def __init__(self):
        """Initialize the code parser."""
        self.logger = logger

    def parse_file(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Parse a Python file and extract all code elements.

        Args:
            filepath: Path to the Python file to parse

        Returns:
            Dictionary containing:
            - functions: List of function metadata dicts
            - classes: List of class metadata dicts
            - module_doc: Module-level docstring (or empty string)
            - imports: List of import statements
            - file_path: Absolute path to the file

            Returns None if parsing fails.
        """
        try:
            # Read the file content
            source_code = self._read_file(filepath)
            if source_code is None:
                return None

            # Parse the AST
            try:
                tree = ast.parse(source_code)
            except SyntaxError as e:
                self.logger.warning(f"Syntax error in {filepath}: {e}")
                return None

            # Extract module docstring
            module_doc = ast.get_docstring(tree) or ""

            # Split source into lines for code extraction
            source_lines = source_code.splitlines()

            # Extract all elements
            functions = self._extract_functions(tree, source_lines, filepath)
            classes = self._extract_classes(tree, source_lines, filepath)
            imports = self._extract_imports(tree)

            return {
                "functions": functions,
                "classes": classes,
                "module_doc": module_doc,
                "imports": imports,
                "file_path": str(Path(filepath).resolve())
            }

        except Exception as e:
            self.logger.error(f"Error parsing {filepath}: {e}")
            return None

    def _read_file(self, filepath: str) -> Optional[str]:
        """
        Read file content with encoding fallback.

        Args:
            filepath: Path to the file

        Returns:
            File content as string, or None if read fails
        """
        try:
            # Try UTF-8 first
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                # Fallback to latin-1
                with open(filepath, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                self.logger.error(f"Error reading {filepath}: {e}")
                return None
        except Exception as e:
            self.logger.error(f"Error reading {filepath}: {e}")
            return None

    def _extract_functions(self, tree: ast.AST, source_lines: List[str], filepath: str) -> List[Dict[str, Any]]:
        """
        Extract all top-level functions from the AST.

        Args:
            tree: Parsed AST tree
            source_lines: Source code split into lines
            filepath: Path to the file (for logging)

        Returns:
            List of function metadata dictionaries
        """
        functions = []

        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                func_data = self._extract_function_data(node, source_lines, filepath)
                if func_data:
                    functions.append(func_data)

        return functions

    def _extract_function_data(self, node: ast.FunctionDef, source_lines: List[str], filepath: str) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from a function node.

        Args:
            node: AST FunctionDef node
            source_lines: Source code split into lines
            filepath: Path to the file (for logging)

        Returns:
            Function metadata dictionary or None if extraction fails
        """
        try:
            # Extract basic info
            name = node.name
            start_line = node.lineno
            end_line = node.end_lineno if node.end_lineno else start_line

            # Extract docstring
            docstring = ast.get_docstring(node) or ""

            # Extract source code
            code = self._get_source_segment(source_lines, start_line, end_line)

            # Extract function signature
            signature = self._get_function_signature(node)

            return {
                "name": name,
                "type": "function",
                "start_line": start_line,
                "end_line": end_line,
                "docstring": docstring,
                "code": code,
                "signature": signature
            }

        except Exception as e:
            self.logger.warning(f"Error extracting function {node.name if hasattr(node, 'name') else '?'} from {filepath}: {e}")
            return None

    def _extract_classes(self, tree: ast.AST, source_lines: List[str], filepath: str) -> List[Dict[str, Any]]:
        """
        Extract all top-level classes from the AST.

        Args:
            tree: Parsed AST tree
            source_lines: Source code split into lines
            filepath: Path to the file (for logging)

        Returns:
            List of class metadata dictionaries
        """
        classes = []

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_data = self._extract_class_data(node, source_lines, filepath)
                if class_data:
                    classes.append(class_data)

        return classes

    def _extract_class_data(self, node: ast.ClassDef, source_lines: List[str], filepath: str) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from a class node.

        Args:
            node: AST ClassDef node
            source_lines: Source code split into lines
            filepath: Path to the file (for logging)

        Returns:
            Class metadata dictionary or None if extraction fails
        """
        try:
            # Extract basic info
            name = node.name
            start_line = node.lineno
            end_line = node.end_lineno if node.end_lineno else start_line

            # Extract docstring
            docstring = ast.get_docstring(node) or ""

            # Extract source code
            code = self._get_source_segment(source_lines, start_line, end_line)

            # Extract methods
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_data = {
                        "name": item.name,
                        "start_line": item.lineno,
                        "end_line": item.end_lineno if item.end_lineno else item.lineno,
                        "docstring": ast.get_docstring(item) or "",
                        "signature": self._get_function_signature(item)
                    }
                    methods.append(method_data)

            # Extract base classes
            bases = [self._get_node_name(base) for base in node.bases]

            return {
                "name": name,
                "type": "class",
                "start_line": start_line,
                "end_line": end_line,
                "docstring": docstring,
                "code": code,
                "methods": methods,
                "bases": bases
            }

        except Exception as e:
            self.logger.warning(f"Error extracting class {node.name if hasattr(node, 'name') else '?'} from {filepath}: {e}")
            return None

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """
        Extract all import statements from the AST.

        Args:
            tree: Parsed AST tree

        Returns:
            List of imported module names
        """
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return list(set(imports))  # Remove duplicates

    def _get_source_segment(self, source_lines: List[str], start_line: int, end_line: int) -> str:
        """
        Extract source code segment from lines.

        Args:
            source_lines: Source code split into lines
            start_line: Starting line number (1-indexed)
            end_line: Ending line number (1-indexed)

        Returns:
            Source code segment as string
        """
        # Convert to 0-indexed
        start_idx = start_line - 1
        end_idx = end_line

        # Extract lines
        lines = source_lines[start_idx:end_idx]

        return "\n".join(lines)

    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """
        Extract function signature from FunctionDef node.

        Args:
            node: AST FunctionDef node

        Returns:
            Function signature as string (e.g., "def foo(x, y=1) -> int:")
        """
        # Build argument list
        args = []

        # Regular arguments
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {self._get_node_name(arg.annotation)}"
            args.append(arg_str)

        # Default values
        defaults = node.args.defaults
        num_defaults = len(defaults)
        num_args = len(args)

        if num_defaults > 0:
            # Add defaults to the last N arguments
            for i, default in enumerate(defaults):
                arg_idx = num_args - num_defaults + i
                default_val = self._get_node_name(default)
                args[arg_idx] += f"={default_val}"

        # Keyword-only arguments
        for arg in node.args.kwonlyargs:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {self._get_node_name(arg.annotation)}"
            args.append(arg_str)

        # *args and **kwargs
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")

        # Build signature
        sig = f"def {node.name}({', '.join(args)})"

        # Add return annotation
        if node.returns:
            sig += f" -> {self._get_node_name(node.returns)}"

        sig += ":"

        return sig

    def _get_node_name(self, node: ast.AST) -> str:
        """
        Get a string representation of an AST node.

        Args:
            node: AST node

        Returns:
            String representation of the node
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Attribute):
            return f"{self._get_node_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._get_node_name(node.value)}[{self._get_node_name(node.slice)}]"
        elif isinstance(node, ast.List):
            elements = [self._get_node_name(el) for el in node.elts]
            return f"[{', '.join(elements)}]"
        elif isinstance(node, ast.Tuple):
            elements = [self._get_node_name(el) for el in node.elts]
            return f"({', '.join(elements)})"
        else:
            return "?"
