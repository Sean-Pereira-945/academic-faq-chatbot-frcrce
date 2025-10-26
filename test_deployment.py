#!/usr/bin/env python
"""Test script to verify deployment readiness."""

import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported."""
    logger.info("Testing imports")
    
    try:
        import flask
        logger.info("Flask %s", flask.__version__)
    except ImportError as e:
        logger.error("Flask import failed: %s", e)
        return False
    
    try:
        import flask_cors
        logger.info("Flask-CORS imported")
    except ImportError as e:
        logger.error("Flask-CORS import failed: %s", e)
        return False
    
    try:
        import sentence_transformers
        logger.info("sentence-transformers %s", sentence_transformers.__version__)
    except ImportError as e:
        logger.error("sentence-transformers import failed: %s", e)
        return False
    
    try:
        import faiss
        logger.info("FAISS imported")
    except ImportError as e:
        logger.error("FAISS import failed: %s", e)
        return False
    
    try:
        import google.generativeai
        logger.info("Google Generative AI imported")
    except ImportError as e:
        logger.error("Google Generative AI import failed: %s", e)
        return False
    
    try:
        import numpy as np
        logger.info("NumPy %s", np.__version__)
    except ImportError as e:
        logger.error("NumPy import failed: %s", e)
        return False
    
    try:
        import pandas as pd
        logger.info("Pandas %s", pd.__version__)
    except ImportError as e:
        logger.error("Pandas import failed: %s", e)
        return False
    
    try:
        import gunicorn  # type: ignore[import-not-found]
        logger.info("Gunicorn imported")
    except ImportError as e:
        logger.error("Gunicorn import failed: %s", e)
        return False
    
    return True

def test_knowledge_base():
    """Test that knowledge base files exist."""
    logger.info("Testing knowledge base files")
    
    faiss_path = "models/academic_faq.faiss"
    pkl_path = "models/academic_faq_data.pkl"
    
    if os.path.exists(faiss_path):
        size = os.path.getsize(faiss_path)
        logger.info("FAISS file exists (%s bytes)", f"{size:,}")
    else:
        logger.warning("FAISS file not found at %s", faiss_path)
        return False
    
    if os.path.exists(pkl_path):
        size = os.path.getsize(pkl_path)
        logger.info("PKL file exists (%s bytes)", f"{size:,}")
    else:
        logger.warning("PKL file not found at %s", pkl_path)
        return False
    
    return True

def test_api_key():
    """Test that API key is available."""
    logger.info("Testing API key")
    
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        logger.info("GEMINI_API_KEY is set (length: %s)", len(api_key))
        return True
    else:
        logger.warning("GEMINI_API_KEY environment variable not set")
        return False

def test_chatbot_init():
    """Test chatbot initialization."""
    logger.info("Testing chatbot initialization")
    
    try:
        from chatbot import AcademicFAQChatbot
        logger.info("Chatbot module imported")
        
        chatbot = AcademicFAQChatbot()
        logger.info("Chatbot initialized (is_trained: %s)", chatbot.is_trained)
        
        if chatbot.is_trained:
            stats = chatbot.get_stats()
            logger.info("Chatbot stats: %s", stats)
            return True
        else:
            logger.warning("Chatbot not trained")
            return False
            
    except Exception as e:
        logger.error("Chatbot initialization failed: %s", e)
        import traceback
        traceback.print_exc()
        return False

def test_server_import():
    """Test server module import."""
    logger.info("Testing server import")
    
    try:
        from server import app
        logger.info("Server module imported")
        logger.info("Flask app created: %s", app.name)
        return True
    except Exception as e:
        logger.error("Server import failed: %s", e)
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    logger.info("Starting deployment tests")
    logger.info("Python version: %s", sys.version)
    logger.info("Current directory: %s", os.getcwd())
    
    results = {
        "Imports": test_imports(),
        "Knowledge Base": test_knowledge_base(),
        "API Key": test_api_key(),
        "Chatbot Init": test_chatbot_init(),
        "Server Import": test_server_import()
    }
    
    logger.info("\n" + "=" * 60)
    logger.info("Test Results:")
    logger.info("=" * 60)
    
    all_passed = True
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    logger.info("=" * 60)
    
    if all_passed:
        logger.info("All tests passed! Ready for deployment.")
        return 0
    else:
        logger.error("Some tests failed. Please fix issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
