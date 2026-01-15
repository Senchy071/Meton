#!/usr/bin/env python3
"""Meton - Local AI Coding Assistant.

Wisdom in Action (Metis + Ergon)

A fully local coding assistant powered by LangChain, LangGraph, and CodeLlama.
Everything runs on your hardware - no external API calls, no data leaving your machine.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load config and set up logging early (before other imports)
from core.config import Config
from utils.logger import setup_logger

config = Config()
logging_config = config.config.logging


def configure_logging() -> None:
    """Configure logging based on config.yaml settings."""
    # Suppress noisy library logs if configured
    if logging_config.suppress_library_logs:
        noisy_loggers = [
            "httpx",
            "httpcore",
            "urllib3",
            "langchain",
            "langchain_core",
            "langchain_community",
            "langgraph",
            "ollama",
            "sentence_transformers",
            "faiss",
            "chromadb",
            "transformers",
            "torch",
        ]
        for logger_name in noisy_loggers:
            logging.getLogger(logger_name).setLevel(logging.WARNING)

    # Set up main logger with config
    logger = setup_logger(
        name="meton",
        config=logging_config.model_dump()
    )
    return logger


# Configure logging before importing CLI
logger = configure_logging()

from cli import main


if __name__ == "__main__":
    try:
        logger.info("Starting Meton")
        main()
    except KeyboardInterrupt:
        logger.info("User interrupted - shutting down")
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n\n❌ Fatal error: {e}")
        sys.exit(1)
