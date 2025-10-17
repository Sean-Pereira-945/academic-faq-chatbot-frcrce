@echo off
echo Starting Academic FAQ Chatbot Web Server...
echo.
echo Make sure GEMINI_API_KEY is set in your .env file
echo.
cd /d "%~dp0"
call chatbot_env\Scripts\activate
python server.py
pause
