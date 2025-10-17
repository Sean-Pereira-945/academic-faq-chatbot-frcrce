# 🔥 Complete Firebase Deployment Guide - Step by Step

## 📋 What We're Building

**Firebase Hosting** (Frontend) + **Google Cloud Run** (Backend API)

- ✅ Frontend served from Firebase's global CDN
- ✅ Backend Flask app on Cloud Run
- ✅ Secure API key handling
- ✅ Custom domain support
- ✅ Free tier available

---

## ⚡ Quick Start (3 Commands)

```bash
# 1. Setup Firebase
firebase-setup.bat

# 2. Deploy everything
firebase-deploy.bat

# 3. Done! 🎉
```

---

## 📦 Prerequisites

### **1. Node.js (for Firebase CLI)**
- Download: https://nodejs.org/
- Install LTS version
- Verify: `node --version`

### **2. Google Cloud SDK (already installed ✅)**
- You have this from previous steps
- Verify: `gcloud --version`

### **3. Firebase CLI**
```bash
npm install -g firebase-tools
```

---

## 🚀 Step-by-Step Deployment

### **STEP 1: Install Firebase CLI**

```bash
npm install -g firebase-tools
```

Wait for installation to complete (1-2 minutes).

### **STEP 2: Login to Firebase**

```bash
firebase login
```

This will open your browser. Login with your Google account.

### **STEP 3: Initialize Firebase**

```bash
firebase init hosting
```

Answer these questions:
```
? Please select an option: (Use existing project or create new)
? Select a project: <YOUR-PROJECT-NAME>
? What do you want to use as your public directory? public
? Configure as a single-page app? No
? Set up automatic builds and deploys with GitHub? No
```

### **STEP 4: Create public directory**

The firebase.json is configured to use Cloud Run, so we need to create a minimal public directory:

```bash
mkdir public
echo "Redirecting to Cloud Run..." > public/index.html
```

### **STEP 5: Deploy Backend to Cloud Run**

```bash
gcloud run deploy academic-chatbot ^
  --source . ^
  --region us-central1 ^
  --allow-unauthenticated ^
  --env-vars-file .env.yaml ^
  --memory 2Gi ^
  --timeout 300
```

**Save the Cloud Run URL** you get (looks like: `https://academic-chatbot-xxxxx-uc.a.run.app`)

### **STEP 6: Update firebase.json**

The `firebase.json` is already configured to route all requests to Cloud Run!

It will:
- Route `/api/**` to your Cloud Run backend
- Route `/**` to your Cloud Run backend (for HTML pages)
- Serve static files from `public/` if they exist

### **STEP 7: Deploy to Firebase**

```bash
firebase deploy --only hosting
```

You'll get a URL like: `https://your-project-id.web.app`

### **STEP 8: Test Your Deployment**

Visit: `https://your-project-id.web.app`

Your chatbot should load! 🎉

---

## 🎯 **How It Works**

```
User Request
    ↓
Firebase Hosting (CDN)
    ↓
Check: Is it a static file? (CSS, JS, images)
    ↓ Yes: Serve from Firebase
    ↓ No: Forward to Cloud Run
    ↓
Cloud Run (Your Flask App)
    ↓
Return Response
    ↓
User sees the page
```

---

## 📁 **File Structure**

```
academic-chatbot/
├── firebase.json          ← Firebase config (routes traffic)
├── .firebaserc            ← Firebase project config (created during init)
├── public/                ← Static files served by Firebase
│   └── index.html         ← Placeholder (Cloud Run serves actual pages)
├── Dockerfile             ← Cloud Run uses this
├── server.py              ← Your Flask app
├── templates/             ← HTML templates
├── static/                ← CSS/JS (served by Flask OR Firebase)
└── ...rest of your code
```

---

## 🔧 **Automated Deployment Scripts**

I've created scripts for you:

### **firebase-setup.bat**
- Installs Firebase CLI
- Logs you in
- Initializes Firebase
Run ONCE to setup

### **firebase-deploy.bat** / **firebase-deploy.ps1**
- Deploys backend to Cloud Run
- Deploys frontend to Firebase
- One command deployment!
Run EVERY TIME you want to deploy

---

## 💰 **Cost Breakdown**

### **Firebase Hosting (Frontend):**
- **Free Tier**: 10GB storage, 360MB/day transfer
- **Cost**: $0 for most small apps
- **Overage**: $0.026/GB

### **Cloud Run (Backend):**
- **Free Tier**: 2M requests/month, 360,000 GB-seconds
- **Cost**: Usually $0 for moderate traffic
- **Overage**: $0.00002400 per request

**Total: FREE for most use cases!** 🎉

---

## 🎨 **Custom Domain (Optional)**

### **Step 1: Go to Firebase Console**
https://console.firebase.google.com

### **Step 2: Navigate to Hosting**
- Click your project
- Go to "Hosting" section
- Click "Add custom domain"

### **Step 3: Enter Your Domain**
- Enter: `chatbot.yourdomain.com`
- Follow DNS setup instructions

### **Step 4: Wait for SSL**
- Firebase automatically provisions SSL
- Takes 5-30 minutes

---

## ✅ **Verification Checklist**

After deployment, test these URLs:

### **Firebase URL**: `https://your-project-id.web.app`
- [ ] Homepage loads
- [ ] CSS loads properly
- [ ] Can navigate to /chat

### **API Endpoints**: `https://your-project-id.web.app/api/status`
- [ ] Returns JSON with chatbot status
- [ ] Shows `is_trained: true`

### **Health Check**: `https://your-project-id.web.app/health`
- [ ] Returns `{"status": "healthy"}`

### **Chat Functionality**:
- [ ] Can send messages
- [ ] Receives AI responses
- [ ] No 502 errors

---

## 🐛 **Troubleshooting**

### **"Command 'firebase' not found"**
```bash
npm install -g firebase-tools
```

### **"Cloud Run service not found"**
Make sure you deployed to Cloud Run first:
```bash
gcloud run deploy academic-chatbot --source .
```

### **"403 Forbidden"**
Update `firebase.json` to allow unauthenticated access to Cloud Run.

### **CSS not loading**
Check if static files are in correct location. Firebase will serve from `public/` if available, otherwise Cloud Run serves them.

---

## 📊 **Firebase vs Render Comparison**

| Feature | Render | Firebase + Cloud Run |
|---------|--------|---------------------|
| Setup Time | 10 min | 15 min |
| Free Tier | 750 hours | 2M requests |
| Cold Start | ~30s | ~10s |
| CDN | Basic | Google's global CDN |
| Custom Domain | Free | Free |
| SSL | Auto | Auto |
| Cost (paid) | $7/mo | Pay-per-use |

---

## 🎉 **Success!**

Your chatbot is now deployed on Firebase + Cloud Run!

**URLs:**
- **Frontend (Firebase)**: `https://your-project-id.web.app`
- **Backend (Cloud Run)**: `https://academic-chatbot-xxxxx-uc.a.run.app`
- **Custom Domain**: `https://chatbot.yourdomain.com` (if configured)

---

## 📞 **Need Help?**

Common commands:
```bash
# View Firebase projects
firebase projects:list

# Check deployment status
firebase hosting:channel:list

# View logs
gcloud run services logs read academic-chatbot --limit=50

# Redeploy
firebase-deploy.bat
```

---

## 🔄 **Updates & Redeployment**

Whenever you make changes:

1. **Commit to Git**: `git push`
2. **Redeploy**: Run `firebase-deploy.bat`
3. **Wait**: 3-5 minutes
4. **Test**: Visit your Firebase URL

That's it! 🚀

---

## 📝 **Summary**

✅ **Frontend**: Firebase Hosting (global CDN)
✅ **Backend**: Google Cloud Run (Python/Flask)
✅ **Database**: FAISS (embedded in container)
✅ **API**: Gemini (secure server-side)
✅ **Cost**: FREE (under limits)
✅ **Performance**: Fast (CDN + auto-scaling)
✅ **Security**: API key protected

**Your chatbot is production-ready on Firebase!** 🎊
