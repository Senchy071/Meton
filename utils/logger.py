"""Logging setup for Meton with Rich integration."""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
from rich.console import Console
from rich.logging import RichHandler


class MetonLogger:
    """Custom logger for Meton with Rich-enhanced console output."""

    def __init__(
        self,
        name: str = "meton",
        log_dir: str = "./logs",
        level: int = logging.INFO,
        console_output: bool = True,
        use_rich: bool = True
    ):
        """Initialize Meton logger with Rich integration.

        Args:
            name: Logger name
            log_dir: Directory for log files
            level: Logging level
            console_output: Enable console output
            use_rich: Use Rich for colored console output

        Example:
            >>> logger = MetonLogger()
            >>> logger.info("Application started")
            >>> logger.debug("Debug information")
            >>> logger.warning("Warning message")
            >>> logger.error("Error occurred")
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.use_rich = use_rich
        self.console = Console() if use_rich else None

        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False

        # Clear existing handlers
        self.logger.handlers.clear()

        # Add handlers
        if console_output:
            if use_rich:
                self._add_rich_console_handler()
            else:
                self._add_console_handler()

        self._add_file_handler()

    def _add_rich_console_handler(self) -> None:
        """Add Rich console handler with beautiful formatting."""
        rich_handler = RichHandler(
            console=self.console,
            show_time=False,  # We'll handle time in the format
            show_path=False,  # Don't show file paths in console
            markup=True,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            log_time_format="[%X]"
        )
        rich_handler.setLevel(logging.INFO)

        # Simple format for Rich console
        console_format = logging.Formatter(
            '%(message)s',
            datefmt='[%X]'
        )
        rich_handler.setFormatter(console_format)

        self.logger.addHandler(rich_handler)

    def _add_console_handler(self) -> None:
        """Add standard console handler with color formatting."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Color codes for different log levels
        # Using ANSI escape codes for colors
        console_format = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_format)

        self.logger.addHandler(console_handler)

    def _add_file_handler(self) -> None:
        """Add file handler with detailed formatting."""
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = self.log_dir / f"{self.name}_{timestamp}.log"

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        # Detailed format for file
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)

        self.logger.addHandler(file_handler)

    def debug(self, message: str) -> None:
        """Log debug message (blue color).

        Args:
            message: Debug message to log
        """
        if self.use_rich:
            self.logger.debug(f"[blue]{message}[/blue]")
        else:
            self.logger.debug(message)

    def info(self, message: str) -> None:
        """Log info message (green color).

        Args:
            message: Info message to log
        """
        if self.use_rich:
            self.logger.info(f"[green]{message}[/green]")
        else:
            self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log warning message (yellow color).

        Args:
            message: Warning message to log
        """
        if self.use_rich:
            self.logger.warning(f"[yellow]{message}[/yellow]")
        else:
            self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log error message (red color).

        Args:
            message: Error message to log
        """
        if self.use_rich:
            self.logger.error(f"[red bold]{message}[/red bold]")
        else:
            self.logger.error(message)

    def critical(self, message: str) -> None:
        """Log critical message (red bold color).

        Args:
            message: Critical message to log
        """
        if self.use_rich:
            self.logger.critical(f"[red bold underline]{message}[/red bold underline]")
        else:
            self.logger.critical(message)

    def exception(self, message: str) -> None:
        """Log exception with traceback (red color).

        Args:
            message: Exception message to log
        """
        if self.use_rich:
            self.logger.exception(f"[red bold]{message}[/red bold]")
        else:
            self.logger.exception(message)


def setup_logger(
    name: str = "meton",
    log_dir: str = "./logs",
    level: int = logging.INFO,
    console_output: bool = True,
    use_rich: bool = True
) -> MetonLogger:
    """Set up and return a Meton logger with Rich integration.

    Args:
        name: Logger name
        log_dir: Directory for log files
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Enable console output
        use_rich: Use Rich for colored console output

    Returns:
        Configured MetonLogger instance

    Example:
        >>> logger = setup_logger()
        >>> logger.info("Starting Meton...")
        >>> logger.debug("Loading configuration...")
        >>> logger.warning("Model not found, using fallback")
        >>> logger.error("Failed to connect to Ollama")
    """
    return MetonLogger(
        name=name,
        log_dir=log_dir,
        level=level,
        console_output=console_output,
        use_rich=use_rich
    )


def suppress_library_loggers() -> None:
    """Suppress verbose logging from third-party libraries.

    This function sets all common third-party library loggers to WARNING level
    to reduce console noise.

    Example:
        >>> suppress_library_loggers()
        >>> # Now httpx, urllib3, etc. will only show warnings and errors
    """
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("langgraph").setLevel(logging.WARNING)
    logging.getLogger("ollama").setLevel(logging.WARNING)
