"""Production WSGI application entry point for Render deployment."""

import os
import sys
import logging

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

logger.info("Starting WSGI application")
logger.info("Current directory: %s", current_dir)
logger.info("Python version: %s", sys.version)
logger.info("Python path: %s", sys.path[:3])

try:
    from server import app
    logger.info("Successfully imported Flask app")
except Exception as e:
    logger.error("Failed to import Flask app: %s", e)
    import traceback
    traceback.print_exc()
    raise

# Get port from environment variable (Render provides this)
port = int(os.environ.get('PORT', 5000))
logger.info("Configured for port: %s", port)

if __name__ == "__main__":
    # Production configuration
    logger.info("Running Flask app directly (not recommended - use gunicorn)")
    app.run(host='0.0.0.0', port=port, debug=False)
