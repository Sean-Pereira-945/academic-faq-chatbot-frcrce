@echo off
echo ========================================
echo   Firebase Setup for Academic Chatbot
echo ========================================
echo.

REM Check if npm is installed
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js/npm not installed!
    echo Please install Node.js from: https://nodejs.org/
    pause
    exit /b 1
)

echo [STEP 1/3] Installing Firebase CLI...
npm install -g firebase-tools

echo.
echo [STEP 2/3] Logging in to Firebase...
firebase login

echo.
echo [STEP 3/3] Initializing Firebase project...
firebase init hosting

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit firebase.json if needed
echo 2. Run: firebase-deploy.bat
echo.
pause
