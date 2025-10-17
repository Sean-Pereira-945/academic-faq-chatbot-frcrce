@echo off
echo ========================================
echo   Firebase + Cloud Run Deployment
echo ========================================
echo.

REM Check if Firebase CLI is installed
firebase --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Firebase CLI not installed!
    echo.
    echo Please install with: npm install -g firebase-tools
    echo.
    pause
    exit /b 1
)

REM Check if gcloud is installed
gcloud --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Google Cloud SDK not installed!
    echo.
    echo Please install from: https://cloud.google.com/sdk/docs/install
    echo.
    pause
    exit /b 1
)

echo [STEP 1/4] Deploying backend to Cloud Run...
echo.

gcloud run deploy academic-chatbot ^
  --source . ^
  --platform managed ^
  --region us-central1 ^
  --allow-unauthenticated ^
  --env-vars-file .env.yaml ^
  --memory 2Gi ^
  --timeout 300 ^
  --max-instances 10

if %errorlevel% neq 0 (
    echo [ERROR] Cloud Run deployment failed!
    pause
    exit /b 1
)

echo.
echo [STEP 2/4] Checking Firebase login...
firebase login:list 2>nul | find "@" >nul
if %errorlevel% neq 0 (
    echo Please login to Firebase...
    firebase login
)

echo.
echo [STEP 3/4] Initializing Firebase (if needed)...
if not exist ".firebaserc" (
    echo Please select or create your Firebase project:
    firebase use --add
)

echo.
echo [STEP 4/4] Deploying to Firebase Hosting...
firebase deploy --only hosting

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   DEPLOYMENT SUCCESSFUL!
    echo ========================================
    echo.
    echo Your chatbot is now live on Firebase!
    echo.
    echo Frontend: https://YOUR-PROJECT-ID.web.app
    echo Backend: https://academic-chatbot-xxxxx-uc.a.run.app
    echo.
) else (
    echo.
    echo [ERROR] Firebase deployment failed!
    echo.
)

pause
