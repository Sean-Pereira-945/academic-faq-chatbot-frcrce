Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Academic FAQ Chatbot - Deploy to Google Cloud Run" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if gcloud is installed
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Google Cloud SDK not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[INFO] Checking Google Cloud authentication..." -ForegroundColor Yellow
$authList = gcloud auth list 2>&1 | Out-String
if ($authList -notmatch "ACTIVE") {
    Write-Host "[INFO] Please login to Google Cloud..." -ForegroundColor Yellow
    gcloud auth login
}

Write-Host ""
Write-Host "[INFO] Setting project configuration..." -ForegroundColor Yellow
gcloud config set project academic-chatbot-frcrce

Write-Host ""
Write-Host "[INFO] Deploying to Google Cloud Run..." -ForegroundColor Yellow
Write-Host "This may take 5-10 minutes..." -ForegroundColor Yellow
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

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your app is now live!" -ForegroundColor Green
    Write-Host "Check the URL above to access your chatbot." -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "[ERROR] Deployment failed!" -ForegroundColor Red
    Write-Host "Check the error messages above." -ForegroundColor Red
    Write-Host ""
}

Read-Host "Press Enter to exit"
