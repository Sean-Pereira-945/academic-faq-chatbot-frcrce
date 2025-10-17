# 🔥 Deploy Academic FAQ Chatbot to Firebase (Static + Functions)

## 📋 Overview

We'll deploy your chatbot to Firebase using:
- **Firebase Hosting**: Serve HTML, CSS, JS (frontend)
- **Firebase Functions**: Handle API requests (backend)

However, there's an important limitation:
- Firebase Functions has a **540 second timeout**
- Your AI model loading might take longer
- **Recommended: Use Firebase Hosting + Google Cloud Run** (see below)

---

## ⚠️ IMPORTANT: Choose Your Deployment Strategy

### **Option A: Firebase Hosting Only (Simple Static Site)** 
- Convert to a **client-side only** app
- Call Gemini API directly from browser
- ✅ **EASIEST** - No backend needed
- ⚠️ API key exposed to users

### **Option B: Firebase Hosting + Google Cloud Run** ⭐ RECOMMENDED
- Frontend on Firebase Hosting
- Backend (Flask) on Cloud Run
- ✅ **BEST** - Keep API key secure
- ✅ Use existing Dockerfile

### **Option C: Firebase Hosting + Firebase Functions**
- Frontend on Firebase Hosting
- Backend on Firebase Functions
- ⚠️ May timeout with large models
- ⚠️ Requires code restructuring

---

## 🚀 **RECOMMENDED: Option B - Firebase Hosting + Cloud Run**

This gives you the best of both worlds!

### **Step 1: Install Firebase CLI**

```bash
npm install -g firebase-tools
```

### **Step 2: Initialize Firebase**

```bash
cd "C:\Users\SEAN\OneDrive\Desktop\Classwork\TE\NLP lab\mini-project\academic-chatbot"
firebase login
firebase init hosting
```

When prompted:
- **Project**: Create new or select existing
- **Public directory**: Enter `static`
- **Single-page app**: `No`
- **Automatic builds**: `No`
- **Overwrite index.html**: `No`

### **Step 3: Deploy Backend to Cloud Run**

```bash
gcloud run deploy academic-chatbot-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --env-vars-file .env.yaml
```

You'll get a URL like: `https://academic-chatbot-api-xxxxx-uc.a.run.app`

### **Step 4: Update firebase.json**

Create/update `firebase.json`:
```json
{
  "hosting": {
    "public": "static",
    "rewrites": [
      {
        "source": "/api/**",
        "run": {
          "serviceId": "academic-chatbot-api",
          "region": "us-central1"
        }
      },
      {
        "source": "/",
        "function": "serveIndex"
      },
      {
        "source": "/chat",
        "function": "serveChat"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(jpg|jpeg|gif|png|svg|webp|js|css)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "max-age=7200"
          }
        ]
      }
    ]
  }
}
```

### **Step 5: Deploy to Firebase**

```bash
firebase deploy --only hosting
```

### **Step 6: Get Your URL**

Your app will be at: `https://your-project-id.web.app`

---

## 🎯 **Option A: Pure Client-Side (Simplest)**

If you want Firebase Hosting only (no backend), I can convert your app to:
- Call Gemini API directly from browser JavaScript
- Store knowledge base in IndexedDB or fetch from Cloud Storage
- No server needed!

⚠️ **Trade-off**: API key will be visible in browser

Would you like me to create this version?

---

## 📦 **Files I'll Create**

1. **firebase.json** - Firebase configuration
2. **firebase-deploy.bat** - Automated deployment
3. **functions/index.js** - Serve HTML pages
4. **Static site version** (optional)

---

## 🔥 **Quick Firebase-Only Deployment (No Backend)**

If you want the simplest solution:

### I'll create:
1. **Client-side JavaScript** that calls Gemini API
2. **Static knowledge base** in JSON format
3. **Pure HTML/CSS/JS** - no Python needed
4. **Single command deployment**: `firebase deploy`

This will:
- ✅ Deploy in 30 seconds
- ✅ Work on Firebase Hosting
- ✅ Be completely free (under Firebase limits)
- ⚠️ Expose your API key (but can use Firebase App Check)

---

## 💡 **My Recommendation**

**For your chatbot, I recommend:**

**Firebase Hosting + Cloud Run** because:
1. ✅ Frontend hosted on Firebase (fast, global CDN)
2. ✅ Backend on Cloud Run (keeps API key secure)
3. ✅ Uses your existing Python code
4. ✅ Best performance
5. ✅ Professional setup

**Total setup time: 15 minutes**

---

## 🎮 **What Would You Like?**

**Option 1**: Create Firebase + Cloud Run setup (RECOMMENDED)
- I'll create the `firebase.json` and deployment scripts
- Frontend on Firebase, backend on Cloud Run

**Option 2**: Convert to pure client-side static site
- I'll rewrite the JavaScript to call Gemini directly
- Everything on Firebase Hosting
- Simpler but exposes API key

**Option 3**: Create Firebase Functions version
- I'll convert your Python code to Node.js
- Everything on Firebase
- May have timeout issues with large models

Which option do you prefer? Let me know and I'll set it up for you! 🚀
