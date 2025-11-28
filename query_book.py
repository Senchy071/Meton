#!/usr/bin/env python3
"""
Query Ingested Books - Helper Script

Makes it easier to query books ingested with ingest_document.py
Automatically uses semantic search on indexed documents.

Usage:
    python query_book.py "What are the main prompting techniques?"
    python query_book.py "Explain chain-of-thought prompting"
    python query_book.py "List all prompt patterns mentioned"
"""

import sys
import subprocess
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Usage: python query_book.py \"Your question here\"")
        print()
        print("Examples:")
        print('  python query_book.py "What are the main prompting rules?"')
        print('  python query_book.py "Explain few-shot learning"')
        print('  python query_book.py "List all techniques in chapter 3"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    # Check if documents directory exists
    docs_dir = Path("documents")
    if not docs_dir.exists() or not list(docs_dir.glob("*.py")):
        print("❌ No documents found!")
        print()
        print("First ingest your book:")
        print("  python ingest_document.py ~/path/to/book.pdf")
        print()
        print("Then index it in Meton:")
        print("  python meton.py")
        print("  > /index documents/")
        sys.exit(1)

    print(f"📚 Querying indexed books...")
    print(f"❓ Question: {query}")
    print()

    # Create a prompt that explicitly uses semantic search
    prompt = f"""Based on the indexed documents in the documents/ directory, please answer this question:

{query}

Important: Use the codebase_search tool to find relevant information from the indexed book content. Do not list files or directories - search the actual content of the indexed documents.

Provide a comprehensive answer based on what you find in the indexed content."""

    # Write prompt to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    print("🤖 Starting Meton with your query...")
    print("=" * 60)
    print()

    # Run Meton with the prompt
    # Note: This creates an interactive session, user will see the response
    try:
        subprocess.run([
            sys.executable, "meton.py",
            "--query", prompt
        ])
    except FileNotFoundError:
        # Fallback: print instructions
        print("💡 Run this in Meton:")
        print()
        print(prompt)
        print()
        print("=" * 60)
        print()
        print("To use:")
        print("  1. python meton.py")
        print(f"  2. Copy the above question and paste it")


if __name__ == '__main__':
    main()
