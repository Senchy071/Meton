#!/usr/bin/env python3
"""
Document Ingestion Script for Meton

Converts text documents (books, PDFs, markdown) into a format Meton can index.
Creates Python files with content in docstrings for semantic search.

Usage:
    python ingest_document.py book.txt
    python ingest_document.py book.pdf
    python ingest_document.py book.md
"""

import sys
import os
from pathlib import Path


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at sentence boundary
        if end < len(text):
            # Look for period followed by space/newline
            for i in range(end, max(start, end - 200), -1):
                if text[i] in '.!?\n' and i + 1 < len(text) and text[i + 1] in ' \n':
                    end = i + 1
                    break

        chunks.append(text[start:end].strip())
        start = end - overlap if end < len(text) else end

    return chunks


def text_to_python(text: str, output_file: str, title: str = "Document"):
    """Convert text content to Python file with docstrings."""

    # Split into chunks
    chunks = chunk_text(text, chunk_size=1500, overlap=200)

    # Create Python file
    with open(output_file, 'w', encoding='utf-8') as f:
        # Module docstring with full content
        f.write(f'"""\n')
        f.write(f'{title}\n')
        f.write('=' * len(title) + '\n\n')
        f.write('This module contains the full text of the document for semantic search.\n')
        f.write(f'Total chunks: {len(chunks)}\n')
        f.write('"""\n\n')

        # Create a function for each chunk
        for i, chunk in enumerate(chunks, 1):
            # Clean chunk for function name
            first_line = chunk.split('\n')[0][:50].strip()
            func_name = f"section_{i}"

            f.write(f'def {func_name}():\n')
            f.write(f'    """\n')
            f.write(f'    Section {i}: {first_line}...\n')
            f.write(f'    \n')

            # Write chunk content, properly indented
            for line in chunk.split('\n'):
                f.write(f'    {line}\n')

            f.write(f'    """\n')
            f.write(f'    pass\n\n')

    print(f"✓ Created {output_file}")
    print(f"  Chunks: {len(chunks)}")
    print(f"  Size: {len(text)} characters")


def read_text_file(file_path: str) -> str:
    """Read plain text file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def read_pdf_file(file_path: str) -> str:
    """Read PDF file (requires PyPDF2)."""
    try:
        import PyPDF2
    except ImportError:
        print("Error: PyPDF2 not installed. Install with: pip install PyPDF2")
        sys.exit(1)

    text = []
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text.append(page.extract_text())

    return '\n\n'.join(text)


def read_markdown_file(file_path: str) -> str:
    """Read Markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def main():
    if len(sys.argv) < 2:
        print("Usage: python ingest_document.py <file>")
        print()
        print("Supported formats:")
        print("  .txt  - Plain text")
        print("  .md   - Markdown")
        print("  .pdf  - PDF (requires PyPDF2)")
        print()
        print("Example:")
        print("  python ingest_document.py my_book.txt")
        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    # Determine file type
    ext = Path(input_file).suffix.lower()
    title = Path(input_file).stem.replace('_', ' ').title()

    print(f"📖 Ingesting: {input_file}")
    print(f"   Title: {title}")

    # Read content based on file type
    if ext == '.txt':
        content = read_text_file(input_file)
    elif ext == '.md':
        content = read_markdown_file(input_file)
    elif ext == '.pdf':
        content = read_pdf_file(input_file)
    else:
        print(f"Error: Unsupported file type: {ext}")
        print("Supported: .txt, .md, .pdf")
        sys.exit(1)

    # Create output directory
    output_dir = Path("documents")
    output_dir.mkdir(exist_ok=True)

    # Generate Python file
    output_file = output_dir / f"{Path(input_file).stem}.py"
    text_to_python(content, str(output_file), title)

    print()
    print("✅ Document ingested successfully!")
    print()
    print("Next steps:")
    print(f"  1. python meton.py")
    print(f"  2. > /index {output_dir}")
    print(f"  3. > Tell me about {title}")


if __name__ == '__main__':
    main()
