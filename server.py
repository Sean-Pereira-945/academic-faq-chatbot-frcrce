"""Flask server for the Academic FAQ Chatbot."""

from __future__ import annotations

import os
import sys
import logging

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Determine if running in production
IS_PRODUCTION = os.environ.get('RENDER', False) or os.environ.get('RAILWAY', False)

environment_label = 'Production' if IS_PRODUCTION else 'Development'
logger.info("Environment: %s", environment_label)
logger.info("Python version: %s", sys.version)
logger.info("Current directory: %s", os.getcwd())

app = Flask(__name__)

# Configure CORS based on environment
if IS_PRODUCTION:
    # In production, allow specific origins or use more restrictive settings
    CORS(app, resources={r"/api/*": {"origins": "*"}})
else:
    # In development, allow all origins
    CORS(app)

# Initialize chatbot with error handling
logger.info("Initializing chatbot in Flask app")
chatbot = None

try:
    from chatbot import AcademicFAQChatbot
    chatbot = AcademicFAQChatbot()
    logger.info("Chatbot initialized. Is trained: %s", chatbot.is_trained)
    if chatbot.is_trained:
        logger.info("Chatbot ready with %s documents", len(chatbot.search_engine.documents))
    else:
        logger.warning("Chatbot not trained - knowledge base not found")
except ImportError as e:
    logger.error("Failed to import chatbot module: %s", e)
    import traceback
    traceback.print_exc()
except Exception as e:
    logger.error("Error initializing chatbot: %s", e)
    import traceback
    traceback.print_exc()


@app.route('/')
def index():
    """Serve the landing page."""
    logger.info("Serving landing page")
    return render_template('index.html')


@app.route('/chat')
def chat_page():
    """Serve the chat interface."""
    logger.info("Serving chat page")
    return render_template('chat.html')


# Explicit static file routes for production
@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('static', filename)


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests."""
    try:
        data = request.get_json()
        if not data:
            logger.warning("No JSON data received")
            return jsonify({
                'error': 'No data provided'
            }), 400
            
        question = data.get('question', '').strip()
        logger.info("Received question: %s...", question[:100])
        
        if not question:
            return jsonify({
                'error': 'Please provide a question'
            }), 400
        
        if chatbot is None:
            logger.error("Chatbot is None - initialization failed")
            return jsonify({
                'error': 'Chatbot initialization failed. Please check server logs.',
                'details': 'The chatbot service could not be initialized. This may be due to missing dependencies or configuration.'
            }), 500
        
        if not chatbot.is_trained:
            logger.error("Chatbot is not trained")
            return jsonify({
                'error': 'Knowledge base not loaded. Please run knowledge_base_builder.py first.',
                'details': 'The chatbot needs a trained knowledge base to answer questions.'
            }), 500
        
        response = chatbot.generate_response(question)
        logger.info("Generated response: %s...", response[:100])
        
        return jsonify({
            'response': response,
            'success': True
        })
    
    except Exception as e:
        logger.error("Error in chat endpoint: %s", e)
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'An error occurred: {str(e)}',
            'success': False
        }), 500


@app.route('/health')
def health():
    """Health check endpoint for monitoring services."""
    return jsonify({
        'status': 'healthy',
        'service': 'Academic FAQ Chatbot',
        'version': '1.0.0'
    }), 200


@app.route('/api/status')
def status():
    """Get chatbot status."""
    try:
        import os
        faiss_exists = os.path.exists("models/academic_faq.faiss")
        pkl_exists = os.path.exists("models/academic_faq_data.pkl")
        
        logger.info(
            "Status check - FAISS exists: %s, PKL exists: %s",
            faiss_exists,
            pkl_exists,
        )
        logger.info("Status check - Chatbot is None: %s", chatbot is None)
        if chatbot is not None:
            logger.info("Status check - Chatbot is trained: %s", chatbot.is_trained)
        
        if chatbot is None:
            return jsonify({
                'is_trained': False,
                'stats': 'Chatbot initialization failed',
                'embedding_backend': 'N/A',
                'error': 'Chatbot failed to initialize. Check logs for details.',
                'debug_info': {
                    'faiss_file_exists': faiss_exists,
                    'pkl_file_exists': pkl_exists,
                    'working_directory': os.getcwd(),
                    'documents_count': 0,
                    'python_version': sys.version,
                    'is_production': IS_PRODUCTION
                }
            }), 500
        
        return jsonify({
            'is_trained': chatbot.is_trained,
            'stats': chatbot.get_stats() if chatbot.is_trained else 'Knowledge base not loaded',
            'embedding_backend': chatbot.search_engine.embedding_backend if chatbot.is_trained else 'N/A',
            'debug_info': {
                'faiss_file_exists': faiss_exists,
                'pkl_file_exists': pkl_exists,
                'working_directory': os.getcwd(),
                'documents_count': len(chatbot.search_engine.documents) if chatbot.is_trained else 0,
                'python_version': sys.version,
                'is_production': IS_PRODUCTION
            }
        })
    except Exception as e:
        logger.error("Error in status endpoint: %s", e)
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Status check failed: {str(e)}'
        }), 500



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = not IS_PRODUCTION
    
    if IS_PRODUCTION:
        # Production: Let gunicorn handle this
        logger.info("Production mode - using gunicorn")
    else:
        # Development: Run with Flask's built-in server
        logger.info("Development mode")
        logger.info("Starting server on http://0.0.0.0:%s", port)
        app.run(host='0.0.0.0', port=port, debug=debug_mode, use_reloader=False)
