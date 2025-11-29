#!/bin/bash
# Run Meton in completely offline mode

# Disable HuggingFace telemetry and force offline mode
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1

# Disable LangChain telemetry
export LANGCHAIN_TRACING_V2=false
export LANGCHAIN_ENDPOINT=""

# Disable Gradio analytics (for web UI)
export GRADIO_ANALYTICS_ENABLED=False
export GRADIO_SERVER_NAME="127.0.0.1"

# Disable pip version check
export PIP_DISABLE_PIP_VERSION_CHECK=1

# Disable Python update checks
export PYTHONDONTWRITEBYTECODE=1

echo "🔒 Starting Meton in OFFLINE mode..."
echo ""
echo "Environment:"
echo "  HF_HUB_OFFLINE=1 (HuggingFace offline)"
echo "  TRANSFORMERS_OFFLINE=1 (Transformers offline)"
echo "  LANGCHAIN_TRACING_V2=false (No LangChain telemetry)"
echo "  GRADIO_ANALYTICS_ENABLED=False (No Gradio analytics)"
echo ""

# Activate virtual environment
source venv/bin/activate

# Run Meton
python meton.py "$@"
