#!/usr/bin/env bash
# Render build script

set -o errexit  # Exit on error

echo "🚀 Starting build process..."
echo "🐍 Python version: $(python --version)"
echo "📁 Current directory: $(pwd)"
echo "📂 Directory contents:"
ls -la

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Verify critical dependencies
echo "🔍 Verifying installations..."
python -c "import flask; print(f'✅ Flask: {flask.__version__}')"
python -c "import sentence_transformers; print(f'✅ sentence-transformers: {sentence_transformers.__version__}')"
python -c "import faiss; print('✅ FAISS installed')"
python -c "import google.generativeai; print('✅ Google Generative AI installed')"

export HF_HOME="${PWD}/.cache/huggingface"
mkdir -p "$HF_HOME"
python - <<'PY'
from sentence_transformers import SentenceTransformer, CrossEncoder
SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
try:
    CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
except Exception as exc:  # pragma: no cover - informational logging only
    print(f"⚠️  Cross-encoder preload skipped: {exc}")
PY

# Create models directory if it doesn't exist
echo "📁 Creating models directory..."
mkdir -p models

# List models directory
echo "📂 Models directory contents:"
ls -la models/ || echo "Models directory is empty"

# Check if knowledge base exists
if [ -f "models/academic_faq.faiss" ] && [ -f "models/academic_faq_data.pkl" ]; then
    echo "✅ Knowledge base found!"
    echo "📊 FAISS file size: $(du -h models/academic_faq.faiss)"
    echo "📊 PKL file size: $(du -h models/academic_faq_data.pkl)"
else
    echo "⚠️  Knowledge base not found. Building it now..."
    # Build knowledge base (only if PDFs are included in deployment)
    if [ -d "data/pdfs" ] && [ "$(ls -A data/pdfs)" ]; then
        echo "📚 Building knowledge base from PDFs..."
        python knowledge_base_builder.py --embedding-backend gemini --skip-urls
        echo "✅ Knowledge base built successfully!"
    else
        echo "⚠️  No PDFs found. Knowledge base will need to be uploaded manually."
        echo "📂 Data directory contents:"
        ls -la data/ || echo "Data directory not found"
    fi
fi

echo "📂 Final models directory check:"
ls -la models/

echo "✅ Build completed successfully!"
