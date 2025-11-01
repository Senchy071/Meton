#!/usr/bin/env python3
"""Meton - Local AI Coding Assistant.

Wisdom in Action (Metis + Ergon)

A fully local coding assistant powered by LangChain, LangGraph, and CodeLlama.
Everything runs on your hardware - no external API calls, no data leaving your machine.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cli import main


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        sys.exit(1)
