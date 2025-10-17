Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Firebase + Cloud Run Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Firebase CLI is installed
if (-not (Get-Command firebase -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Firebase CLI not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install with: npm install -g firebase-tools" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if gcloud is installed
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Google Cloud SDK not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[STEP 1/4] Deploying backend to Cloud Run..." -ForegroundColor Yellow
Write-Host ""

gcloud run deploy academic-chatbot `
  --source . `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --env-vars-file .env.yaml `
  --memory 2Gi `
  --timeout 300 `
  --max-instances 10

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Cloud Run deployment failed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[STEP 2/4] Checking Firebase login..." -ForegroundColor Yellow
$loginList = firebase login:list 2>&1 | Out-String
if ($loginList -notmatch "@") {
    Write-Host "Please login to Firebase..." -ForegroundColor Yellow
    firebase login
}

Write-Host ""
Write-Host "[STEP 3/4] Initializing Firebase (if needed)..." -ForegroundColor Yellow
if (-not (Test-Path ".firebaserc")) {
    Write-Host "Please select or create your Firebase project:" -ForegroundColor Yellow
    firebase use --add
}

Write-Host ""
Write-Host "[STEP 4/4] Deploying to Firebase Hosting..." -ForegroundColor Yellow
firebase deploy --only hosting

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your chatbot is now live on Firebase!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Frontend: https://YOUR-PROJECT-ID.web.app" -ForegroundColor Cyan
    Write-Host "Backend: https://academic-chatbot-xxxxx-uc.a.run.app" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "[ERROR] Firebase deployment failed!" -ForegroundColor Red
    Write-Host ""
}

Read-Host "Press Enter to exit"
