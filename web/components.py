"""
Reusable UI components for Meton Web Interface.

Provides pre-built components for:
- Status indicators
- File displays
- Settings panels
- Export dialogs
"""

import gradio as gr
from typing import Dict, List, Any


def create_status_indicator(status: str, details: Dict[str, Any] = None) -> str:
    """
    Create formatted status indicator.

    Args:
        status: Status text
        details: Optional additional details

    Returns:
        Formatted status string
    """
    status_map = {
        "ready": "✅ Ready",
        "processing": "⏳ Processing...",
        "error": "❌ Error",
        "not_initialized": "⚠️ Not Initialized"
    }

    status_lower = status.lower().replace(" ", "_")
    formatted_status = status_map.get(status_lower, status)

    if details:
        details_str = "\n".join([f"{k}: {v}" for k, v in details.items()])
        return f"{formatted_status}\n\n{details_str}"

    return formatted_status


def create_file_list_display(files: List[str]) -> str:
    """
    Create formatted file list display.

    Args:
        files: List of file names

    Returns:
        Formatted file list
    """
    if not files:
        return "📂 No files uploaded"

    file_lines = []
    for i, file in enumerate(files, 1):
        # Determine icon based on extension
        ext = file.split('.')[-1].lower() if '.' in file else ''

        icon_map = {
            'py': '🐍',
            'js': '📜',
            'ts': '📘',
            'json': '📋',
            'yaml': '⚙️',
            'yml': '⚙️',
            'md': '📄',
            'txt': '📝'
        }

        icon = icon_map.get(ext, '📄')
        file_lines.append(f"{icon} {file}")

    return "\n".join(file_lines)


def create_tool_status(tools: Dict[str, bool]) -> str:
    """
    Create formatted tool status display.

    Args:
        tools: Dictionary of tool name -> enabled status

    Returns:
        Formatted tool status
    """
    if not tools:
        return "No tools configured"

    status_lines = []
    for tool_name, enabled in tools.items():
        status = "🟢 Enabled" if enabled else "⚪ Disabled"
        display_name = tool_name.replace('_', ' ').title()
        status_lines.append(f"{display_name}: {status}")

    return "\n".join(status_lines)


def create_metrics_display(metrics: Dict[str, Any]) -> str:
    """
    Create formatted metrics display.

    Args:
        metrics: Dictionary of metric name -> value

    Returns:
        Formatted metrics
    """
    if not metrics:
        return "No metrics available"

    metric_lines = []
    for key, value in metrics.items():
        display_key = key.replace('_', ' ').title()

        # Format value based on type
        if isinstance(value, float):
            if 'time' in key.lower():
                formatted_value = f"{value:.2f}s"
            elif 'rate' in key.lower():
                formatted_value = f"{value*100:.1f}%"
            else:
                formatted_value = f"{value:.2f}"
        else:
            formatted_value = str(value)

        metric_lines.append(f"**{display_key}:** {formatted_value}")

    return "\n".join(metric_lines)


def create_error_message(error: str, details: str = None) -> str:
    """
    Create formatted error message.

    Args:
        error: Error message
        details: Optional error details

    Returns:
        Formatted error message
    """
    message = f"❌ **Error:** {error}"

    if details:
        message += f"\n\n**Details:**\n```\n{details}\n```"

    return message


def create_success_message(message: str, details: str = None) -> str:
    """
    Create formatted success message.

    Args:
        message: Success message
        details: Optional additional details

    Returns:
        Formatted success message
    """
    result = f"✅ **Success:** {message}"

    if details:
        result += f"\n\n{details}"

    return result


def create_warning_message(message: str, action: str = None) -> str:
    """
    Create formatted warning message.

    Args:
        message: Warning message
        action: Optional recommended action

    Returns:
        Formatted warning message
    """
    result = f"⚠️ **Warning:** {message}"

    if action:
        result += f"\n\n**Recommended Action:** {action}"

    return result


def create_code_block(code: str, language: str = "python") -> str:
    """
    Create formatted code block.

    Args:
        code: Code content
        language: Programming language for syntax highlighting

    Returns:
        Formatted code block
    """
    return f"```{language}\n{code}\n```"


def create_help_panel() -> str:
    """
    Create help panel content.

    Returns:
        Formatted help content
    """
    return """
## 🚀 Getting Started

### Chat Interface
- Type your question or request in the text box
- Press **Send** or hit **Enter** to submit
- View the conversation history above

### File Upload
- Click **Upload Files** or drag & drop files
- Supported formats: Python, JavaScript, JSON, YAML, Markdown, Text
- Maximum file size: 10MB per file
- Files are available to the agent for analysis

### Tools & Settings
- **Web Search**: Enable internet search capabilities
- **Self-Reflection**: Agent reviews its own responses for quality
- **Chain-of-Thought**: Shows reasoning steps
- **Parallel Execution**: Run multiple tools simultaneously

- **Model**: Select the AI model to use
  - `qwen2.5:32b` - Best for coding (default)
  - `llama3.1:8b` - Faster, less resource-intensive
  - `mistral:latest` - Quick responses

### Export Conversation
- **Export MD**: Download conversation as Markdown
- **Export JSON**: Download as structured JSON

### Tips
- Be specific in your questions
- Upload relevant files for better context
- Use the **Clear** button to start fresh
- Enable tools as needed for your task
"""


def create_welcome_message() -> str:
    """
    Create welcome message for first-time users.

    Returns:
        Welcome message
    """
    return """
👋 **Welcome to Meton!**

I'm your local AI coding assistant, powered by state-of-the-art language models running entirely on your machine.

**I can help you with:**
- 🐛 Debugging code
- ♻️ Refactoring and improving code quality
- ✅ Writing tests
- 📝 Generating documentation
- 🔍 Searching and analyzing codebases
- 💡 Explaining complex code
- 🚀 And much more!

**To get started:**
1. Upload any code files you want to work with (optional)
2. Enable tools like Web Search if needed
3. Ask me anything!

Try asking: *"Help me understand how async/await works in Python"*
"""
