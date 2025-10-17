@echo off
echo ========================================
echo   Academic FAQ Chatbot - Deploy to Google Cloud Run
echo ========================================
echo.

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

echo [INFO] Checking Google Cloud authentication...
gcloud auth list 2>nul | find "ACTIVE" >nul
if %errorlevel% neq 0 (
    echo [INFO] Please login to Google Cloud...
    gcloud auth login
)

echo.
echo [INFO] Setting project configuration...
gcloud config set project academic-chatbot-frcrce

echo.
echo [INFO] Deploying to Google Cloud Run...
echo This may take 5-10 minutes...
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

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   DEPLOYMENT SUCCESSFUL!
    echo ========================================
    echo.
    echo Your app is now live!
    echo Check the URL above to access your chatbot.
    echo.
) else (
    echo.
    echo [ERROR] Deployment failed!
    echo Check the error messages above.
    echo.
)

pause
