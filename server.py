"""Flask server for the Academic FAQ Chatbot."""

from __future__ import annotations

import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from chatbot import AcademicFAQChatbot

# Determine if running in production
IS_PRODUCTION = os.environ.get('RENDER', False)

app = Flask(__name__)

# Configure CORS based on environment
if IS_PRODUCTION:
    # In production, allow specific origins or use more restrictive settings
    CORS(app, resources={r"/api/*": {"origins": "*"}})
else:
    # In development, allow all origins
    CORS(app)

# Initialize chatbot with error handling
print("🔄 Initializing chatbot in Flask app...")
try:
    chatbot = AcademicFAQChatbot()
    print(f"📊 Chatbot initialized. Is trained: {chatbot.is_trained}")
    if chatbot.is_trained:
        print(f"✅ Chatbot ready with {len(chatbot.search_engine.documents)} documents")
    else:
        print("⚠️  Chatbot not trained - knowledge base not found!")
except Exception as e:
    print(f"❌ Error initializing chatbot: {e}")
    import traceback
    traceback.print_exc()
    # Create a dummy chatbot that will return errors
    chatbot = None


@app.route('/')
def index():
    """Serve the landing page."""
    return render_template('index.html')


@app.route('/chat')
def chat_page():
    """Serve the chat interface."""
    return render_template('chat.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests."""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({
                'error': 'Please provide a question'
            }), 400
        
        if chatbot is None:
            return jsonify({
                'error': 'Chatbot initialization failed. Please check server logs.'
            }), 500
        
        if not chatbot.is_trained:
            return jsonify({
                'error': 'Knowledge base not loaded. Please run knowledge_base_builder.py first.'
            }), 500
        
        response = chatbot.generate_response(question)
        
        return jsonify({
            'response': response,
            'success': True
        })
    
    except Exception as e:
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
    import os
    faiss_exists = os.path.exists("models/academic_faq.faiss")
    pkl_exists = os.path.exists("models/academic_faq_data.pkl")
    
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
                'documents_count': 0
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
            'documents_count': len(chatbot.search_engine.documents) if chatbot.is_trained else 0
        }
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = not IS_PRODUCTION
    
    if IS_PRODUCTION:
        # Production: Let gunicorn handle this
        print("🚀 Production mode - using gunicorn")
    else:
        # Development: Run with Flask's built-in server
        print("🔧 Development mode")
        app.run(host='0.0.0.0', port=port, debug=debug_mode, use_reloader=False)
