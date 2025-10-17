#!/usr/bin/env bash
# Render build script

set -o errexit  # Exit on error

echo "🚀 Starting build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create models directory if it doesn't exist
echo "📁 Creating models directory..."
mkdir -p models

# Check if knowledge base exists
if [ -f "models/academic_faq.faiss" ] && [ -f "models/academic_faq_data.pkl" ]; then
    echo "✅ Knowledge base found!"
else
    echo "⚠️  Knowledge base not found. Building it now..."
    # Build knowledge base (only if PDFs are included in deployment)
    if [ -d "data/pdfs" ] && [ "$(ls -A data/pdfs)" ]; then
        echo "📚 Building knowledge base from PDFs..."
        python knowledge_base_builder.py --embedding-backend gemini --skip-urls
        echo "✅ Knowledge base built successfully!"
    else
        echo "⚠️  No PDFs found. Knowledge base will need to be uploaded manually."
    fi
fi

echo "✅ Build completed successfully!"
