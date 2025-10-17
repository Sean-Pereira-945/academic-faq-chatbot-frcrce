# 🚀 Pre-Deployment Checklist

## ✅ Files Ready for Production

- [x] `requirements.txt` - Updated with gunicorn & gevent
- [x] `Procfile` - Gunicorn configuration
- [x] `runtime.txt` - Python 3.11.9
- [x] `build.sh` - Build script
- [x] `wsgi.py` - Production entry point
- [x] `render.yaml` - Render configuration
- [x] `server.py` - Production-ready Flask app
- [x] `.gitignore` - Updated to include knowledge base files
- [x] `RENDER_DEPLOYMENT.md` - Complete deployment guide

## 📋 Before You Deploy

### 1. Test Locally with Production Server
```bash
# Install production dependencies
pip install gunicorn gevent

# Test production mode
gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:5000 --timeout 120 wsgi:app
```

Visit: http://localhost:5000

### 2. Ensure Knowledge Base Files Are Ready
```bash
# Check if files exist
dir models\academic_faq.faiss
dir models\academic_faq_data.pkl

# If missing, rebuild:
python knowledge_base_builder.py --embedding-backend gemini --skip-urls
```

### 3. Commit Everything to Git
```bash
cd "c:\Users\SEAN\OneDrive\Desktop\Classwork\TE\NLP lab\mini-project\academic-chatbot"

# Add all files
git add .

# Commit
git commit -m "Production ready: Added Render deployment files"

# Push to GitHub
git push origin main
```

### 4. Verify GitHub Repository
- [ ] Visit: https://github.com/Sean-Pereira-945/academic-faq-chatbot-frcrce
- [ ] Confirm all files are present
- [ ] Check models/ directory has .faiss and .pkl files
- [ ] Verify PDFs are in data/pdfs/

## 🎯 Deployment Steps

### Step 1: Create Render Account
1. Go to https://render.com
2. Sign up with GitHub
3. Authorize Render to access your repositories

### Step 2: Create New Web Service
1. Click "New +" → "Web Service"
2. Select your repository: `academic-faq-chatbot-frcrce`
3. Configure:
   - **Name**: `academic-faq-chatbot`
   - **Root Directory**: `academic-chatbot`
   - **Environment**: Python 3
   - **Build Command**: `chmod +x build.sh && ./build.sh`
   - **Start Command**: (leave empty, uses Procfile)

### Step 3: Add Environment Variable
1. Scroll to "Environment Variables"
2. Add:
   - Key: `GEMINI_API_KEY`
   - Value: `AIzaSyB2vnP2zLpLe-Jh3Cqpwkm_E_koPJ2iy0E`

### Step 4: Deploy
1. Click "Create Web Service"
2. Wait 5-10 minutes for deployment
3. Monitor logs for success messages

### Step 5: Test Deployment
Visit your app:
- Landing: `https://your-app.onrender.com/`
- Chat: `https://your-app.onrender.com/chat`
- Status: `https://your-app.onrender.com/api/status`
- Health: `https://your-app.onrender.com/health`

## 🔍 Post-Deployment Verification

### Test These Endpoints:

**Health Check:**
```bash
curl https://your-app.onrender.com/health
```
Expected: `{"status":"healthy"}`

**Status Check:**
```bash
curl https://your-app.onrender.com/api/status
```
Expected: `{"is_trained":true,"stats":"Knowledge base contains 259 text chunks"}`

**Chat API:**
```bash
curl -X POST https://your-app.onrender.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What are the library rules?"}'
```
Expected: JSON response with answer

### Test Questions:
- "What are the library rules?"
- "Tell me about internship requirements"
- "What is the academic calendar?"
- "Explain the credit system"

## 📊 Expected Deployment Output

```
==> Building...
📦 Installing Python dependencies...
✅ Knowledge base found!
✅ Build completed successfully!

==> Starting service...
🔄 Initializing chatbot in Flask app...
✅ Knowledge base loaded from models/academic_faq
📊 Chatbot initialized. Is trained: True
✅ Chatbot ready with 259 documents
🚀 Production mode - using gunicorn

==> Your service is live at https://academic-faq-chatbot.onrender.com
```

## ⚠️ Common Issues & Solutions

### Issue: "Knowledge base not loaded"
**Solution**: 
- Check if models/ files are in Git
- Or let build.sh rebuild from PDFs

### Issue: "GEMINI_API_KEY not found"
**Solution**:
- Add environment variable in Render dashboard
- Click "Save Changes" to redeploy

### Issue: App is slow on first request
**Solution**:
- Normal on free tier (30-60s cold start)
- Upgrade to paid plan for no sleep
- Use UptimeRobot to keep awake

## 🎉 Success Criteria

- [ ] App is accessible at Render URL
- [ ] Landing page loads with animations
- [ ] Chat interface is responsive
- [ ] Questions get accurate answers
- [ ] No citation/source references in responses
- [ ] Responses are concise (80-120 words)
- [ ] Health check returns 200 OK
- [ ] Status API shows 259 documents loaded
- [ ] No errors in Render logs

## 📝 Next Steps After Deployment

1. **Update README** with production URL
2. **Share with users** and get feedback
3. **Monitor logs** for errors
4. **Set up UptimeRobot** (free tier)
5. **Consider paid plan** ($7/month for better performance)
6. **Add analytics** (optional)
7. **Implement feedback form** (optional)

## 🔗 Important Links

- **Render Dashboard**: https://dashboard.render.com/
- **GitHub Repo**: https://github.com/Sean-Pereira-945/academic-faq-chatbot-frcrce
- **Deployment Guide**: See RENDER_DEPLOYMENT.md
- **RAG Architecture**: See RAG_ARCHITECTURE.md

---

**Ready to deploy?** Follow RENDER_DEPLOYMENT.md for detailed instructions!
