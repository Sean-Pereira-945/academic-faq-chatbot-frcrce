# 🚀 Render Deployment Guide

## Prerequisites

1. **GitHub Account** - Your code should be in a GitHub repository
2. **Render Account** - Sign up at https://render.com (free tier available)
3. **Gemini API Key** - Get from https://ai.google.dev/

---

## 📦 Files Required for Deployment

Your project now includes all necessary files:

- ✅ `requirements.txt` - Python dependencies with gunicorn
- ✅ `Procfile` - Tells Render how to start your app
- ✅ `runtime.txt` - Specifies Python version (3.11.9)
- ✅ `build.sh` - Build script for Render
- ✅ `wsgi.py` - Production WSGI entry point
- ✅ `.gitignore` - Excludes unnecessary files from Git
- ✅ Production-ready `server.py`

---

## 🔧 Step-by-Step Deployment

### Step 1: Prepare Your Repository

1. **Commit all changes to Git:**
   ```bash
   cd "c:\Users\SEAN\OneDrive\Desktop\Classwork\TE\NLP lab\mini-project\academic-chatbot"
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Ensure knowledge base files are committed:**
   ```bash
   git add models/academic_faq.faiss
   git add models/academic_faq_data.pkl
   git push origin main
   ```

   > **Note**: These files are large (~10-50MB). If Git rejects them:
   > - Use Git LFS: `git lfs track "*.faiss" "*.pkl"`
   > - Or rebuild on Render (slower but works)

---

### Step 2: Create a New Web Service on Render

1. **Go to Render Dashboard:**
   - Visit https://dashboard.render.com/
   - Click **"New +"** → **"Web Service"**

2. **Connect Your Repository:**
   - Choose **"Build and deploy from a Git repository"**
   - Connect your GitHub account if not already connected
   - Select your repository: `academic-faq-chatbot-frcrce`
   - Click **"Connect"**

3. **Configure Your Web Service:**

   | Field | Value |
   |-------|-------|
   | **Name** | `academic-faq-chatbot` (or your choice) |
   | **Region** | Choose closest to your users |
   | **Branch** | `main` |
   | **Root Directory** | `academic-chatbot` |
   | **Runtime** | `Python 3` |
   | **Build Command** | `chmod +x build.sh && ./build.sh` |
   | **Start Command** | Leave empty (uses Procfile) |
   | **Plan** | Free (or paid for better performance) |

---

### Step 3: Add Environment Variables

In the Render dashboard, scroll to **"Environment Variables"** section:

| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | Your Gemini API key from Google AI Studio |
| `PYTHON_VERSION` | `3.11.9` |
| `PORT` | `10000` (Render provides this automatically) |

**How to add:**
1. Click **"Add Environment Variable"**
2. Enter key: `GEMINI_API_KEY`
3. Enter value: `AIzaSyB2vnP2zLpLe-Jh3Cqpwkm_E_koPJ2iy0E` (your actual key)
4. Click **"Add"**

---

### Step 4: Deploy

1. Click **"Create Web Service"** at the bottom
2. Render will:
   - Clone your repository
   - Install dependencies from `requirements.txt`
   - Run `build.sh` script
   - Start the app using the `Procfile`

3. **Monitor the deployment:**
   - Watch the logs in real-time
   - Initial build takes 5-10 minutes (downloads ML models)
   - Look for: `✅ Chatbot ready with 259 documents`

---

### Step 5: Access Your App

Once deployed successfully:

1. **Your app URL:** `https://academic-faq-chatbot.onrender.com` (or your chosen name)
2. **Test endpoints:**
   - Landing page: `https://your-app.onrender.com/`
   - Chat interface: `https://your-app.onrender.com/chat`
   - Status API: `https://your-app.onrender.com/api/status`

---

## 🔍 Troubleshooting

### Issue: Build Fails - "Knowledge base not found"

**Solution 1 - Commit knowledge base files:**
```bash
# Make sure .gitignore doesn't exclude these
git add -f models/academic_faq.faiss
git add -f models/academic_faq_data.pkl
git commit -m "Add knowledge base files"
git push
```

**Solution 2 - Rebuild on Render:**
- Ensure PDFs are in `data/pdfs/` directory
- The `build.sh` script will automatically build the knowledge base
- This takes longer but works if files are too large for Git

---

### Issue: "GEMINI_API_KEY not found"

**Solution:**
1. Go to Render Dashboard → Your Service → Environment
2. Add environment variable: `GEMINI_API_KEY` = your key
3. Click **"Save Changes"**
4. Render will automatically redeploy

---

### Issue: "Out of Memory" or Slow Performance

**Solutions:**
1. **Upgrade to paid plan** ($7/month for better resources)
2. **Optimize knowledge base:**
   ```bash
   # Reduce chunks if needed
   python knowledge_base_builder.py --embedding-backend gemini --skip-urls
   ```
3. **Use lighter models** (already using `gemini-2.5-flash` - optimal choice)

---

### Issue: App Sleeps on Free Tier

**Problem:** Free tier apps sleep after 15 min of inactivity

**Solutions:**
1. **Upgrade to paid plan** (no sleep)
2. **Use a ping service:**
   - UptimeRobot: https://uptimerobot.com/
   - Ping your app every 10 minutes to keep it awake
   - Configure: Check `https://your-app.onrender.com/api/status`

---

### Issue: Slow First Response

**Cause:** App spins down on free tier, takes 30-60s to wake up

**Solutions:**
1. Upgrade to paid plan
2. Use a keep-alive service (UptimeRobot)
3. Display loading message in frontend

---

## ⚙️ Configuration Options

### Adjust Workers (for better performance on paid plan)

Edit `Procfile`:
```
web: gunicorn --worker-class gevent --workers 2 --bind 0.0.0.0:$PORT --timeout 120 --preload wsgi:app
```

### Increase Timeout (for slow API responses)

Edit `Procfile`:
```
web: gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:$PORT --timeout 300 --preload wsgi:app
```

---

## 📊 Monitoring & Logs

### View Logs:
1. Go to Render Dashboard → Your Service
2. Click **"Logs"** tab
3. View real-time logs and errors

### Check Status:
Visit: `https://your-app.onrender.com/api/status`

Expected response:
```json
{
  "is_trained": true,
  "stats": "Knowledge base contains 259 text chunks",
  "embedding_backend": "GEMINI",
  "debug_info": {
    "faiss_file_exists": true,
    "pkl_file_exists": true,
    "documents_count": 259
  }
}
```

---

## 🔒 Security Best Practices

### 1. Keep API Keys Secret
- ✅ Use Render's environment variables
- ❌ Never commit API keys to Git
- ❌ Never hardcode sensitive data

### 2. Update CORS Settings (Production)

Edit `server.py` to restrict origins:
```python
if IS_PRODUCTION:
    CORS(app, resources={
        r"/api/*": {
            "origins": ["https://your-frontend-domain.com"]
        }
    })
```

### 3. Rate Limiting (Optional)

Install Flask-Limiter:
```bash
pip install Flask-Limiter
```

Add to `server.py`:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)
```

---

## 🚀 Performance Optimization

### 1. Enable Caching
Add response caching for common queries (optional future enhancement)

### 2. Database for Conversation History
Consider adding PostgreSQL for storing chat history (Render provides free tier)

### 3. CDN for Static Assets
Use Render's built-in CDN for CSS/JS files (automatic)

---

## 📈 Scaling

### Free Tier Limits:
- 512 MB RAM
- 0.1 CPU
- Sleeps after 15 min inactivity
- 750 hours/month

### Starter Plan ($7/month):
- 2 GB RAM
- 1 CPU
- No sleep
- Unlimited hours
- **Recommended for production**

---

## 🎯 Post-Deployment Checklist

- [ ] App is accessible at your Render URL
- [ ] Landing page loads correctly
- [ ] Chat interface works
- [ ] API endpoint `/api/status` returns correct info
- [ ] Knowledge base is loaded (259 documents)
- [ ] Gemini API is responding
- [ ] Test multiple questions
- [ ] Monitor logs for errors
- [ ] Set up UptimeRobot (if using free tier)
- [ ] Update README with production URL

---

## 🔗 Useful Links

- **Render Dashboard:** https://dashboard.render.com/
- **Render Docs:** https://render.com/docs
- **Gemini API:** https://ai.google.dev/
- **Your GitHub Repo:** https://github.com/Sean-Pereira-945/academic-faq-chatbot-frcrce

---

## 🆘 Getting Help

If you encounter issues:

1. **Check Render logs** for error messages
2. **Test locally first:** `python run_server.py`
3. **Verify environment variables** are set correctly
4. **Check knowledge base files** are present
5. **Contact Render support** (excellent free tier support)

---

## 🎉 Success!

Your Academic FAQ Chatbot is now live in production! 🚀

**Next Steps:**
- Share your app URL with users
- Monitor usage and performance
- Gather feedback for improvements
- Consider upgrading to paid tier for better performance

---

**Deployed URL Example:**
`https://academic-faq-chatbot.onrender.com`

**Test it with questions like:**
- "What are the library rules?"
- "Tell me about internship requirements"
- "What is the academic calendar?"

Enjoy your production-ready RAG-powered chatbot! 🎓✨
