"""
Code Chunker - Convert parsed code into indexable chunks.

Implements code-aware chunking strategy:
- Each function → 1 chunk
- Each class → 1 chunk (with all methods)
- Module docstring → 1 chunk
- Imports section → 1 chunk
"""

import uuid
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class CodeChunker:
    """
    Convert parsed code data into chunks suitable for embedding and indexing.

    Each chunk represents a logical unit of code (function, class, module doc,
    or imports) with complete metadata for retrieval and context.
    """

    def __init__(self):
        """Initialize the code chunker."""
        self.logger = logger

    def create_chunks(self, parsed_data: Dict[str, Any], filepath: str) -> List[Dict[str, Any]]:
        """
        Create chunks from parsed code data.

        Args:
            parsed_data: Dictionary from CodeParser.parse_file() containing:
                - functions: List of function metadata
                - classes: List of class metadata
                - module_doc: Module-level docstring
                - imports: List of import statements
            filepath: Absolute path to the source file

        Returns:
            List of chunk dictionaries, each containing:
            - chunk_id: Unique identifier (UUID)
            - file_path: Absolute path to source file
            - chunk_type: "function", "class", "module", or "imports"
            - name: Name of the code element
            - start_line: Starting line number
            - end_line: Ending line number
            - code: Source code of the chunk
            - docstring: Extracted docstring
            - imports: List of imports (for context)
        """
        chunks = []

        # Extract imports list for context
        imports = parsed_data.get("imports", [])

        # Create chunk for module docstring (if exists and non-empty)
        module_doc = parsed_data.get("module_doc", "")
        if module_doc.strip():
            chunk = self._create_module_chunk(filepath, module_doc, imports)
            chunks.append(chunk)

        # Create chunk for imports section (if imports exist)
        if imports:
            chunk = self._create_imports_chunk(filepath, imports)
            chunks.append(chunk)

        # Create chunks for functions
        for func_data in parsed_data.get("functions", []):
            chunk = self._create_function_chunk(filepath, func_data, imports)
            if chunk:
                chunks.append(chunk)

        # Create chunks for classes
        for class_data in parsed_data.get("classes", []):
            chunk = self._create_class_chunk(filepath, class_data, imports)
            if chunk:
                chunks.append(chunk)

        self.logger.debug(f"Created {len(chunks)} chunks from {filepath}")
        return chunks

    def _create_module_chunk(self, filepath: str, module_doc: str, imports: List[str]) -> Dict[str, Any]:
        """
        Create a chunk for the module-level docstring.

        Args:
            filepath: Absolute path to the source file
            module_doc: Module-level docstring
            imports: List of imports for context

        Returns:
            Module chunk dictionary
        """
        return {
            "chunk_id": str(uuid.uuid4()),
            "file_path": filepath,
            "chunk_type": "module",
            "name": self._get_module_name(filepath),
            "start_line": 1,
            "end_line": len(module_doc.splitlines()),
            "code": module_doc,
            "docstring": module_doc,
            "imports": imports
        }

    def _create_imports_chunk(self, filepath: str, imports: List[str]) -> Dict[str, Any]:
        """
        Create a chunk for the imports section.

        Args:
            filepath: Absolute path to the source file
            imports: List of imported module names

        Returns:
            Imports chunk dictionary
        """
        # Create a readable representation of imports
        imports_code = "\n".join(sorted(imports))

        return {
            "chunk_id": str(uuid.uuid4()),
            "file_path": filepath,
            "chunk_type": "imports",
            "name": f"{self._get_module_name(filepath)}_imports",
            "start_line": 1,
            "end_line": 1,
            "code": imports_code,
            "docstring": "",
            "imports": imports
        }

    def _create_function_chunk(self, filepath: str, func_data: Dict[str, Any], imports: List[str]) -> Dict[str, Any]:
        """
        Create a chunk for a function.

        Args:
            filepath: Absolute path to the source file
            func_data: Function metadata from CodeParser
            imports: List of imports for context

        Returns:
            Function chunk dictionary
        """
        try:
            return {
                "chunk_id": str(uuid.uuid4()),
                "file_path": filepath,
                "chunk_type": "function",
                "name": func_data["name"],
                "start_line": func_data["start_line"],
                "end_line": func_data["end_line"],
                "code": func_data["code"],
                "docstring": func_data.get("docstring", ""),
                "imports": imports,
                "signature": func_data.get("signature", "")
            }
        except KeyError as e:
            self.logger.warning(f"Missing required field in function data: {e}")
            return None

    def _create_class_chunk(self, filepath: str, class_data: Dict[str, Any], imports: List[str]) -> Dict[str, Any]:
        """
        Create a chunk for a class (including all methods).

        Args:
            filepath: Absolute path to the source file
            class_data: Class metadata from CodeParser
            imports: List of imports for context

        Returns:
            Class chunk dictionary
        """
        try:
            # Build a summary of methods for the chunk
            methods = class_data.get("methods", [])
            method_names = [m["name"] for m in methods]

            return {
                "chunk_id": str(uuid.uuid4()),
                "file_path": filepath,
                "chunk_type": "class",
                "name": class_data["name"],
                "start_line": class_data["start_line"],
                "end_line": class_data["end_line"],
                "code": class_data["code"],
                "docstring": class_data.get("docstring", ""),
                "imports": imports,
                "methods": method_names,
                "bases": class_data.get("bases", [])
            }
        except KeyError as e:
            self.logger.warning(f"Missing required field in class data: {e}")
            return None

    def _get_module_name(self, filepath: str) -> str:
        """
        Extract module name from file path.

        Args:
            filepath: Absolute path to the source file

        Returns:
            Module name (filename without .py extension)
        """
        from pathlib import Path
        return Path(filepath).stem

    def get_chunk_text(self, chunk: Dict[str, Any]) -> str:
        """
        Get the text representation of a chunk for embedding.

        Combines the chunk's name, docstring, and code into a single
        text string optimized for semantic search.

        Args:
            chunk: Chunk dictionary

        Returns:
            Text representation suitable for embedding
        """
        parts = []

        # Add chunk type and name
        chunk_type = chunk.get("chunk_type", "unknown")
        name = chunk.get("name", "unnamed")
        parts.append(f"{chunk_type}: {name}")

        # Add signature for functions
        if chunk_type == "function" and "signature" in chunk:
            parts.append(chunk["signature"])

        # Add bases for classes
        if chunk_type == "class" and chunk.get("bases"):
            bases = ", ".join(chunk["bases"])
            parts.append(f"inherits from: {bases}")

        # Add docstring
        docstring = chunk.get("docstring", "").strip()
        if docstring:
            parts.append(f"Documentation: {docstring}")

        # Add code
        code = chunk.get("code", "").strip()
        if code:
            parts.append(f"Code:\n{code}")

        return "\n\n".join(parts)

    def get_chunk_summary(self, chunk: Dict[str, Any]) -> str:
        """
        Get a brief summary of a chunk for display purposes.

        Args:
            chunk: Chunk dictionary

        Returns:
            Brief summary string
        """
        chunk_type = chunk.get("chunk_type", "unknown")
        name = chunk.get("name", "unnamed")
        file_path = chunk.get("file_path", "")
        start_line = chunk.get("start_line", 0)

        from pathlib import Path
        filename = Path(file_path).name if file_path else "unknown"

        return f"{chunk_type} '{name}' in {filename}:{start_line}"
