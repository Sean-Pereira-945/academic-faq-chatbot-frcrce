@echo off
REM Production startup script for Windows testing

echo ========================================
echo  Academic FAQ Chatbot - Production Mode
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "chatbot_env\" (
    echo Error: Virtual environment not found!
    echo Please run: python -m venv chatbot_env
    pause
    exit /b 1
)

REM Activate virtual environment
call chatbot_env\Scripts\activate

REM Install/Update gunicorn if needed
echo Checking production dependencies...
pip install gunicorn gevent --quiet

REM Set production environment variable
set RENDER=true
set PORT=5000

echo.
echo Starting production server with Gunicorn...
echo Server will be available at: http://localhost:5000
echo.
echo Press CTRL+C to stop the server
echo.

REM Start with gunicorn
gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:5000 --timeout 120 wsgi:app

pause
