"""Production WSGI application entry point for Render deployment."""

import os
import sys

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import app

# Get port from environment variable (Render provides this)
port = int(os.environ.get('PORT', 5000))

if __name__ == "__main__":
    # Production configuration
    app.run(host='0.0.0.0', port=port, debug=False)
