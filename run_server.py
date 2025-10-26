"""Simple script to run the server with proper error handling."""
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Starting Academic FAQ Chatbot Server...")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    # Check if .env file exists
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        print(f"Found .env file at: {env_file}")
    else:
        print(f"Warning: .env file not found at: {env_file}")
    
    # Import and run the server
    from server import app
    
    print("\n" + "=" * 50)
    print("Server is starting...")
    print("="*50)
    print("\nAccess the application at:")
    print("  • Landing Page: http://localhost:5000")
    print("  • Chat Interface: http://localhost:5000/chat")
    print("\nPress CTRL+C to stop the server")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    
except ImportError as e:
    print(f"\nImport Error: {e}")
    print("\nPlease make sure you have installed all dependencies:")
    print("  pip install -r requirements.txt")
    sys.exit(1)
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
