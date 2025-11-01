#!/bin/bash

echo "🧠 Setting up Meton - Local Coding Assistant"
echo "=============================================="

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python $PYTHON_VERSION found"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check Ollama
echo "🔍 Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama not found. Please install: https://ollama.ai"
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "⚠️  Ollama is not running. Start it with: ollama serve"
    exit 1
fi

echo "✓ Ollama is running"

# Check for CodeLlama model
echo "🔍 Checking for CodeLlama 34B model..."
if ollama list | grep -q "codellama:34b"; then
    echo "✓ CodeLlama 34B found"
else
    echo "⚠️  CodeLlama 34B not found"
    echo "📥 Pulling CodeLlama 34B (this may take a while)..."
    ollama pull codellama:34b
fi

# Create conversations directory
mkdir -p conversations

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the environment:"
echo "  source venv/bin/activate"
echo ""
echo "To run Meton:"
echo "  python meton.py"
echo ""
