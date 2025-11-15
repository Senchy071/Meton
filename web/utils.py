"""
Utility functions for Meton Web Interface.

Provides helper functions for:
- File validation
- Format conversion
- Session management
- Error handling
"""

import os
import mimetypes
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime


def validate_file(file_path: str, max_size_mb: int = 10) -> Tuple[bool, Optional[str]]:
    """
    Validate uploaded file.

    Args:
        file_path: Path to file
        max_size_mb: Maximum file size in MB

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check file exists
        if not os.path.exists(file_path):
            return False, "File does not exist"

        # Check file size
        file_size = os.path.getsize(file_path)
        max_size_bytes = max_size_mb * 1024 * 1024

        if file_size > max_size_bytes:
            return False, f"File size ({file_size / 1024 / 1024:.2f}MB) exceeds limit ({max_size_mb}MB)"

        # Check if file is readable
        try:
            with open(file_path, 'r') as f:
                f.read(1024)  # Try to read first 1KB
        except UnicodeDecodeError:
            # Binary file - check if it's an allowed type
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type and not mime_type.startswith('text'):
                return False, "Binary files are not supported"

        return True, None

    except Exception as e:
        return False, f"Validation error: {str(e)}"


def get_file_extension(file_path: str) -> str:
    """
    Get file extension.

    Args:
        file_path: Path to file

    Returns:
        File extension (without dot)
    """
    return Path(file_path).suffix[1:].lower() if Path(file_path).suffix else ""


def is_supported_file_type(file_path: str) -> bool:
    """
    Check if file type is supported.

    Args:
        file_path: Path to file

    Returns:
        True if supported, False otherwise
    """
    supported_extensions = {
        'py', 'pyw',  # Python
        'js', 'jsx', 'ts', 'tsx', 'mjs',  # JavaScript/TypeScript
        'java', 'kt', 'scala',  # JVM languages
        'c', 'h', 'cpp', 'hpp', 'cc', 'cxx',  # C/C++
        'rs',  # Rust
        'go',  # Go
        'rb',  # Ruby
        'php',  # PHP
        'swift',  # Swift
        'cs',  # C#
        'r',  # R
        'sql',  # SQL
        'sh', 'bash', 'zsh',  # Shell
        'json', 'yaml', 'yml', 'toml',  # Config
        'xml', 'html', 'css', 'scss', 'sass',  # Web
        'md', 'rst', 'txt',  # Documentation
        'env', 'ini', 'cfg'  # Config files
    }

    ext = get_file_extension(file_path)
    return ext in supported_extensions


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_file_info(file_path: str) -> dict:
    """
    Get file information.

    Args:
        file_path: Path to file

    Returns:
        Dictionary with file info
    """
    path = Path(file_path)

    if not path.exists():
        return {"error": "File does not exist"}

    stat = path.stat()

    return {
        "name": path.name,
        "size": format_file_size(stat.st_size),
        "size_bytes": stat.st_size,
        "extension": get_file_extension(file_path),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "is_supported": is_supported_file_type(file_path)
    }


def read_file_safely(file_path: str, max_lines: int = 1000) -> Tuple[bool, str]:
    """
    Read file content safely with size limits.

    Args:
        file_path: Path to file
        max_lines: Maximum lines to read

    Returns:
        Tuple of (success, content_or_error)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    lines.append(f"\n... (truncated after {max_lines} lines)")
                    break
                lines.append(line)

            return True, ''.join(lines)

    except UnicodeDecodeError:
        return False, "File contains binary data or unsupported encoding"
    except Exception as e:
        return False, f"Error reading file: {str(e)}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = Path(filename).name

    # Replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    # Ensure filename is not empty
    if not filename:
        filename = "unnamed_file"

    return filename


def create_session_id() -> str:
    """
    Create unique session ID.

    Returns:
        Session ID string
    """
    import uuid
    return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"


def format_timestamp(timestamp: Optional[str] = None) -> str:
    """
    Format timestamp for display.

    Args:
        timestamp: ISO format timestamp (None for current time)

    Returns:
        Formatted timestamp string
    """
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp)
        except ValueError:
            dt = datetime.now()
    else:
        dt = datetime.now()

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def extract_code_blocks(text: str) -> List[Tuple[str, str]]:
    """
    Extract code blocks from markdown text.

    Args:
        text: Markdown text

    Returns:
        List of (language, code) tuples
    """
    import re

    pattern = r'```(\w+)?\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)

    return [(lang or "text", code.strip()) for lang, code in matches]


def format_error_for_display(error: Exception) -> str:
    """
    Format exception for user-friendly display.

    Args:
        error: Exception object

    Returns:
        Formatted error message
    """
    error_type = type(error).__name__
    error_msg = str(error)

    # Common error messages with user-friendly explanations
    error_hints = {
        "FileNotFoundError": "The requested file was not found. Please check the file path.",
        "PermissionError": "Permission denied. Please check file permissions.",
        "MemoryError": "Out of memory. Try processing smaller files or reducing batch size.",
        "TimeoutError": "Operation timed out. The request took too long to complete.",
        "ConnectionError": "Network connection error. Please check your internet connection.",
    }

    hint = error_hints.get(error_type, "")

    if hint:
        return f"{error_type}: {error_msg}\n\nℹ️ {hint}"
    else:
        return f"{error_type}: {error_msg}"


def parse_user_command(message: str) -> Tuple[Optional[str], str]:
    """
    Parse user message for special commands.

    Args:
        message: User message

    Returns:
        Tuple of (command, content)
        command is None if no special command
    """
    message = message.strip()

    # Check for slash commands
    if message.startswith('/'):
        parts = message.split(None, 1)
        command = parts[0][1:].lower()  # Remove leading /
        content = parts[1] if len(parts) > 1 else ""
        return command, content

    return None, message


def estimate_tokens(text: str) -> int:
    """
    Rough estimation of token count.

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    # Rough approximation: 1 token ≈ 4 characters
    return len(text) // 4
