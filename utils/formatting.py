"""Rich formatting helpers for Meton CLI.

This module provides consistent, beautiful CLI output using the Rich library.
All formatting functions use a unified color scheme and style.

Example usage:
    >>> from utils.formatting import *
    >>> print_banner()
    >>> print_section("Agent Initialization")
    >>> print_thinking("Analyzing the problem...")
    >>> print_tool_use("file_ops", "read config.yaml")
    >>> print_success("Configuration loaded!")
    >>> print_code("def hello(): pass", "python")
"""

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.box import DOUBLE, ROUNDED, HEAVY
from rich.text import Text


# Global console instance for consistent output
console = Console()


def print_banner() -> None:
    """Display Meton welcome banner with logo.

    Example:
        >>> print_banner()
        ╔════════════════════════════════════════════╗
        ║  🧠 METON - Local Coding Assistant        ║
        ║  Wisdom in Action                         ║
        ╚════════════════════════════════════════════╝
    """
    banner_text = Text()
    banner_text.append("🧠 METON", style="bold cyan")
    banner_text.append(" - Local Coding Assistant\n", style="cyan")
    banner_text.append("Wisdom in Action", style="italic dim")

    panel = Panel(
        banner_text,
        box=DOUBLE,
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(panel)


def print_section(title: str) -> None:
    """Print section header with formatting.

    Args:
        title: Section title text

    Example:
        >>> print_section("Configuration")
        ═══ Configuration ═══
    """
    console.print(f"\n[bold cyan]{'═' * 3} {title} {'═' * 3}[/bold cyan]\n")


def print_thinking(text: str) -> None:
    """Show agent thinking/reasoning.

    Args:
        text: Thinking text to display

    Example:
        >>> print_thinking("Analyzing the code structure...")
        💭 Analyzing the code structure...
    """
    console.print(f"[yellow italic]💭 {text}[/yellow italic]")


def print_tool_use(tool_name: str, action: str) -> None:
    """Show tool execution.

    Args:
        tool_name: Name of the tool being used
        action: Description of the action

    Example:
        >>> print_tool_use("file_ops", "read config.yaml")
        🔧 [file_ops] read config.yaml
    """
    console.print(f"[cyan]🔧 [{tool_name}][/cyan] {action}")


def print_success(text: str) -> None:
    """Display success message.

    Args:
        text: Success message text

    Example:
        >>> print_success("Operation completed successfully!")
        ✓ Operation completed successfully!
    """
    console.print(f"[bold green]✓ {text}[/bold green]")


def print_error(text: str) -> None:
    """Display error message.

    Args:
        text: Error message text

    Example:
        >>> print_error("Failed to connect to Ollama")
        ✗ Failed to connect to Ollama
    """
    console.print(f"[bold red]✗ {text}[/bold red]")


def print_warning(text: str) -> None:
    """Display warning message.

    Args:
        text: Warning message text

    Example:
        >>> print_warning("Model not found, using fallback")
        ⚠ Model not found, using fallback
    """
    console.print(f"[bold yellow]⚠ {text}[/bold yellow]")


def print_code(code: str, language: str = "python", line_numbers: bool = False, theme: str = "monokai") -> None:
    """Display syntax highlighted code block.

    Args:
        code: Code to display
        language: Programming language for syntax highlighting
        line_numbers: Show line numbers
        theme: Syntax theme (default: monokai)

    Example:
        >>> print_code("def hello():\\n    print('world')", "python")
        def hello():
            print('world')
    """
    syntax = Syntax(
        code,
        language,
        theme=theme,
        line_numbers=line_numbers,
        word_wrap=True,
        background_color="default"
    )
    console.print(syntax)


def print_assistant(text: str) -> None:
    """Display assistant response with formatting.

    Args:
        text: Assistant response text (supports Markdown)

    Example:
        >>> print_assistant("Here's the solution:\\n\\n```python\\nprint('hello')\\n```")
        🧠 Assistant:
        Here's the solution:
        ...
    """
    console.print("[bold green]🧠 Assistant:[/bold green]")

    # Check if text contains code blocks or markdown
    if "```" in text or "#" in text or "*" in text:
        md = Markdown(text)
        console.print(md)
    else:
        console.print(text)


def print_user(text: str) -> None:
    """Display user input with formatting.

    Args:
        text: User input text

    Example:
        >>> print_user("What is property redistribution?")
        👤 You: What is property redistribution?
    """
    console.print(f"[bold cyan]👤 You:[/bold cyan] {text}")


def format_status(status: str, details: str) -> str:
    """Format status line with details.

    Args:
        status: Status text (e.g., "Loading", "Ready", "Error")
        details: Additional details

    Returns:
        Formatted status string

    Example:
        >>> formatted = format_status("Ready", "CodeLlama 34B loaded")
        >>> print(formatted)
        [Ready] CodeLlama 34B loaded
    """
    return f"[bold cyan][{status}][/bold cyan] {details}"


def print_status(status: str, details: str) -> None:
    """Print status line.

    Args:
        status: Status text
        details: Additional details

    Example:
        >>> print_status("Ready", "CodeLlama 34B loaded")
        [Ready] CodeLlama 34B loaded
    """
    console.print(format_status(status, details))


def print_info(text: str) -> None:
    """Display info message.

    Args:
        text: Info message text

    Example:
        >>> print_info("Initializing agent...")
        ℹ Initializing agent...
    """
    console.print(f"[bold blue]ℹ {text}[/bold blue]")


def print_panel(content: str, title: Optional[str] = None, style: str = "cyan") -> None:
    """Display content in a bordered panel.

    Args:
        content: Panel content
        title: Optional panel title
        style: Border style color

    Example:
        >>> print_panel("Important message", "Notice", "yellow")
        ╭─ Notice ─────────╮
        │ Important message│
        ╰──────────────────╯
    """
    panel = Panel(
        content,
        title=title,
        border_style=style,
        box=ROUNDED
    )
    console.print(panel)


def print_separator(char: str = "─", style: str = "dim") -> None:
    """Print a horizontal separator line.

    Args:
        char: Character to use for separator
        style: Rich style string

    Example:
        >>> print_separator()
        ─────────────────────────────────
    """
    width = console.width
    console.print(f"[{style}]{char * width}[/{style}]")


def clear_screen() -> None:
    """Clear the console screen.

    Example:
        >>> clear_screen()
    """
    console.clear()


def print_header(text: str, style: str = "bold cyan") -> None:
    """Print a prominent header with underline.

    Args:
        text: Header text
        style: Rich style string

    Example:
        >>> print_header("Configuration Settings")
        Configuration Settings
        ══════════════════════
    """
    console.print(f"\n[{style}]{text}[/{style}]")
    console.print(f"[{style}]{'═' * len(text)}[/{style}]")


def print_table_row(label: str, value: str, label_width: int = 20) -> None:
    """Print a formatted table row (label: value).

    Args:
        label: Row label
        value: Row value
        label_width: Width for label column

    Example:
        >>> print_table_row("Model", "CodeLlama 34B")
        Model               : CodeLlama 34B
    """
    console.print(f"[cyan]{label:<{label_width}}[/cyan]: {value}")


def print_step(step_num: int, total_steps: int, description: str) -> None:
    """Print a step in a multi-step process.

    Args:
        step_num: Current step number
        total_steps: Total number of steps
        description: Step description

    Example:
        >>> print_step(1, 5, "Loading configuration")
        [1/5] Loading configuration
    """
    console.print(f"[bold cyan][{step_num}/{total_steps}][/bold cyan] {description}")


def print_debug(text: str) -> None:
    """Print debug message (only if debugging is enabled).

    Args:
        text: Debug message text

    Example:
        >>> print_debug("Variable x = 42")
        🐛 Variable x = 42
    """
    console.print(f"[dim blue]🐛 {text}[/dim blue]")


# Convenience function to print with markdown
def print_md(text: str) -> None:
    """Print markdown-formatted text.

    Args:
        text: Markdown text

    Example:
        >>> print_md("# Header\\n\\n**Bold** text")
    """
    md = Markdown(text)
    console.print(md)
