# 🔥 Deploy Academic FAQ Chatbot to Firebase/Google Cloud

## 📋 Overview

Since your app is a **Flask application** (backend + frontend), you have several options:

### **Option 1: Google Cloud Run (Recommended)** ⭐
- Uses your existing Dockerfile
- Automatic scaling
- Integrates with Firebase
- **EASIEST** for your Flask app

### **Option 2: Firebase Cloud Functions**
- Serverless deployment
- Requires restructuring code
- Good for smaller apps

### **Option 3: Firebase Hosting + Cloud Run**
- Frontend on Firebase Hosting
- Backend on Cloud Run
- Best performance

---

## 🚀 **RECOMMENDED: Deploy to Google Cloud Run**

Cloud Run is perfect for your Dockerized Flask app and works seamlessly with Firebase!

### **Prerequisites:**

1. **Google Cloud Account** (uses same credentials as Firebase)
2. **Google Cloud SDK** installed
3. **Docker** (already have Dockerfile ✅)

---

## 📦 **Step-by-Step: Google Cloud Run Deployment**

### **Step 1: Install Google Cloud SDK**

**Windows:**
Download from: https://cloud.google.com/sdk/docs/install

Or use PowerShell:
```powershell
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
& $env:Temp\GoogleCloudSDKInstaller.exe
```

**After installation:**
```bash
gcloud --version
```

### **Step 2: Initialize Google Cloud**

```bash
# Login to your Google account
gcloud auth login

# Create a new project or use existing
gcloud projects create academic-chatbot-frcrce --name="Academic FAQ Chatbot"

# Set the project
gcloud config set project academic-chatbot-frcrce

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### **Step 3: Configure Your Project**

Set your region (choose closest to your users):
```bash
gcloud config set run/region us-central1
```

### **Step 4: Set Environment Variables**

Create a `.env.yaml` file:
```yaml
GEMINI_API_KEY: "AIzaSyB2vnP2zLpLe-Jh3Cqpwkm_E_koPJ2iy0E"
```

**Important**: Add `.env.yaml` to `.gitignore`:
```bash
echo ".env.yaml" >> .gitignore
```

### **Step 5: Deploy to Cloud Run**

```bash
# Navigate to your project directory
cd "C:\Users\SEAN\OneDrive\Desktop\Classwork\TE\NLP lab\mini-project\academic-chatbot"

# Deploy (Cloud Run will build from Dockerfile automatically)
gcloud run deploy academic-chatbot \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --env-vars-file .env.yaml \
  --memory 2Gi \
  --timeout 300 \
  --max-instances 10
```

**Windows PowerShell version:**
```powershell
gcloud run deploy academic-chatbot `
  --source . `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --env-vars-file .env.yaml `
  --memory 2Gi `
  --timeout 300 `
  --max-instances 10
```

### **Step 6: Get Your URL**

After deployment completes, you'll get a URL like:
```
https://academic-chatbot-xxxxxxxxxx-uc.a.run.app
```

Your app is now live! 🎉

---

## 🔧 **Alternative: Quick Deploy Script**

Let me create an automated deployment script for you:

### **For Windows (deploy.bat):**
```batch
@echo off
echo 🚀 Deploying Academic FAQ Chatbot to Google Cloud Run...

REM Check if gcloud is installed
gcloud --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Google Cloud SDK not installed!
    echo Please install from: https://cloud.google.com/sdk/docs/install
    exit /b 1
)

REM Set project
gcloud config set project academic-chatbot-frcrce

REM Deploy
gcloud run deploy academic-chatbot ^
  --source . ^
  --platform managed ^
  --region us-central1 ^
  --allow-unauthenticated ^
  --env-vars-file .env.yaml ^
  --memory 2Gi ^
  --timeout 300 ^
  --max-instances 10

echo ✅ Deployment complete!
pause
```

### **For PowerShell (deploy.ps1):**
```powershell
Write-Host "🚀 Deploying Academic FAQ Chatbot to Google Cloud Run..." -ForegroundColor Cyan

# Check if gcloud is installed
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Google Cloud SDK not installed!" -ForegroundColor Red
    Write-Host "Please install from: https://cloud.google.com/sdk/docs/install"
    exit 1
}

# Set project
gcloud config set project academic-chatbot-frcrce

# Deploy
gcloud run deploy academic-chatbot `
  --source . `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --env-vars-file .env.yaml `
  --memory 2Gi `
  --timeout 300 `
  --max-instances 10

Write-Host "✅ Deployment complete!" -ForegroundColor Green
```

---

## 🔥 **Option 2: Firebase Hosting + Cloud Run**

For better performance, serve static files from Firebase Hosting and API from Cloud Run:

### **Step 1: Install Firebase CLI**

```bash
npm install -g firebase-tools
```

### **Step 2: Initialize Firebase**

```bash
firebase login
firebase init hosting
```

When prompted:
- **Public directory**: `static`
- **Configure as single-page app**: No
- **Setup automatic builds**: No

### **Step 3: Update `firebase.json`**

```json
{
  "hosting": {
    "public": "static",
    "rewrites": [
      {
        "source": "/api/**",
        "run": {
          "serviceId": "academic-chatbot",
          "region": "us-central1"
        }
      },
      {
        "source": "**",
        "run": {
          "serviceId": "academic-chatbot",
          "region": "us-central1"
        }
      }
    ],
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ]
  }
}
```

### **Step 4: Deploy Both**

```bash
# Deploy Cloud Run first
gcloud run deploy academic-chatbot --source .

# Deploy Firebase Hosting
firebase deploy --only hosting
```

---

## 💰 **Pricing Comparison**

### **Google Cloud Run:**
- **Free Tier**: 2 million requests/month
- **Memory**: 2GB = ~$0.0000025/second
- **Cost**: Usually free for moderate traffic
- **Better than Render's free tier!**

### **Firebase Hosting:**
- **Free Tier**: 10GB storage, 360MB/day transfer
- **Cost**: Very affordable for static files

---

## 🎯 **Recommended Setup**

**For your use case, I recommend:**

1. **Deploy to Google Cloud Run** (using your Dockerfile)
   - Free tier is generous
   - Auto-scales
   - Easy deployment
   - Works with your existing code

2. **Use Firebase Hosting for custom domain** (optional)
   - Faster static file delivery
   - Free SSL certificate
   - Custom domain support

---

## 📋 **Comparison: Render vs Google Cloud Run**

| Feature | Render (Current) | Google Cloud Run |
|---------|-----------------|------------------|
| Free Tier | 750 hours/month | 2M requests/month |
| Cold Start | ~30s | ~10s |
| Memory | 512MB free | Up to 8GB |
| Timeout | 120s | 3600s |
| Scaling | Manual | Automatic |
| Custom Domain | Yes | Yes (with Firebase) |
| SSL | Automatic | Automatic |

---

## 🚀 **Quick Start Commands**

```bash
# 1. Install Google Cloud SDK
# Download from: https://cloud.google.com/sdk/docs/install

# 2. Login and setup
gcloud auth login
gcloud config set project academic-chatbot-frcrce

# 3. Create .env.yaml
echo "GEMINI_API_KEY: 'AIzaSyB2vnP2zLpLe-Jh3Cqpwkm_E_koPJ2iy0E'" > .env.yaml

# 4. Deploy!
gcloud run deploy academic-chatbot \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --env-vars-file .env.yaml
```

---

## ✅ **What Files You Already Have**

Good news! Your project is already ready for Cloud Run:
- ✅ `Dockerfile` - Cloud Run will use this
- ✅ `requirements.txt` - Dependencies defined
- ✅ `wsgi.py` - Entry point
- ✅ All code structured properly

**No changes needed to your code!** Just deploy with gcloud CLI.

---

## 🐛 **Troubleshooting**

### **If deployment fails:**

1. **Check quotas:**
   ```bash
   gcloud compute project-info describe --project=academic-chatbot-frcrce
   ```

2. **View logs:**
   ```bash
   gcloud run services logs read academic-chatbot --limit=50
   ```

3. **Test locally with Docker:**
   ```bash
   docker build -t academic-chatbot .
   docker run -p 8080:8080 -e PORT=8080 academic-chatbot
   ```

---

## 📝 **Summary**

**Easiest Path:**
1. Install Google Cloud SDK
2. Run `gcloud auth login`
3. Create `.env.yaml` with your API key
4. Run `gcloud run deploy academic-chatbot --source .`
5. Get your URL and test!

**Your app is already Docker-ready, so deployment is simple!** ✨

---

## 🎉 **Next Steps**

Would you like me to:
1. Create the `.env.yaml` file?
2. Create the deployment scripts (deploy.bat, deploy.ps1)?
3. Create a `firebase.json` for Firebase Hosting integration?
4. Help you set up custom domain?

Let me know and I'll help you deploy! 🚀
