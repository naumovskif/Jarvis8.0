# JARVIS Multi-UI Setup Guide (A+B)
## Web Dashboard + Terminal UI Implementation

**Complete guide to set up both UIs running simultaneously**

---

## 🎯 Overview

You now have **3 components** that work together:

```
┌──────────────────────────────────────────────────────────┐
│           JARVIS Multi-UI Architecture                   │
└──────────────────────────────────────────────────────────┘

┌─────────────────────────────┬──────────────────────────┐
│  Web Dashboard (Next.js)    │  Terminal UI (Textual)   │
│  http://localhost:3000      │  Terminal                │
│  Beautiful, responsive      │  Accessible, fast        │
│  Mobile-friendly            │  SSH-able                │
└─────────────────────────────┴──────────────────────────┘
                    ↓
            ┌───────────────────┐
            │  FastAPI Backend  │
            │  http://0.0.0.0:8000
            │  REST + WebSocket │
            └───────────────────┘
                    ↓
            ┌───────────────────┐
            │ JARVIS Core       │
            │ • Upgrades        │
            │ • Models          │
            │ • Metrics         │
            │ • Security        │
            └───────────────────┘
```

---

## 📋 Prerequisites

### Required
```bash
# Python 3.8+
python --version

# Node.js 16+
node --version
npm --version
```

### Installation
```bash
# Backend dependencies
pip install fastapi uvicorn textual rich httpx

# Frontend dependencies (later)
npm install -g create-next-app
```

---

## 🚀 Setup Step-by-Step

### Step 1: Prepare Backend (5 minutes)

The backend file `jarvis_backend.py` is already created. Install dependencies:

```bash
cd /path/to/JARVIS/Mark-XXXIX-OR-main

# Install backend dependencies
pip install fastapi uvicorn pydantic python-multipart

# Verify JARVIS core is importable
python -c "from jarvis_smart_upgrade import upgrade_jarvis; print('✅ JARVIS core ready')"
python -c "from metrics import MetricsCollector; print('✅ Metrics ready')"
python -c "from or_client_v2 import OpenRouterClientV2; print('✅ Models ready')"
```

### Step 2: Start Backend (Terminal 1)

```bash
cd /path/to/JARVIS/Mark-XXXIX-OR-main

# Run backend
python jarvis_backend.py

# You should see:
# ======================================================================
# JARVIS Dashboard Backend
# ======================================================================
# Starting server at http://0.0.0.0:8000
# API Docs: http://localhost:8000/docs
# ======================================================================
```

✅ **Backend is now running!**

Test it:
```bash
# In another terminal
curl http://localhost:8000/api/health

# Should return JSON with health data
```

### Step 3: Setup Web Dashboard (Terminal 2)

```bash
# Create Next.js project (run this once)
npx create-next-app@latest jarvis-dashboard \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --no-git

cd jarvis-dashboard

# Install dependencies
npm install axios recharts lucide-react

# Copy component files (create these)
# Create components directory if not exists
mkdir -p app/components
```

**Copy the component files** from `WEB_DASHBOARD_SETUP.md`:

- `app/page.tsx` - Main dashboard
- `components/Layout.tsx`
- `components/HealthCard.tsx`
- `components/UpgradeForm.tsx`
- `components/DeploymentHistory.tsx`

### Step 4: Start Web Dashboard

```bash
cd jarvis-dashboard

# Run development server
npm run dev

# You should see:
# ▲ Next.js 14.0
# ✓ Ready in 1234ms
# ▲ Local:        http://localhost:3000
# ▲ Environments: .env.local
```

✅ **Web dashboard is running at http://localhost:3000**

### Step 5: Install Terminal UI Dependencies

```bash
cd /path/to/JARVIS/Mark-XXXIX-OR-main

# Install Textual for terminal UI
pip install textual rich
```

### Step 6: Start Terminal UI (Terminal 3)

```bash
cd /path/to/JARVIS/Mark-XXXIX-OR-main

# Run terminal dashboard
python jarvis_terminal_ui.py

# You should see a beautiful terminal interface!
```

✅ **Terminal UI is running in your terminal!**

---

## 🎯 Three Things Running Simultaneously

### Terminal 1: Backend
```
$ python jarvis_backend.py
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Terminal 2: Web Dashboard
```
$ npm run dev
▲ Next.js 14.0
✓ Ready in 1234ms
▲ Local: http://localhost:3000
```

### Terminal 3: Terminal UI
```
$ python jarvis_terminal_ui.py

╔═══════════════════════════════════════════════════════════╗
║        🤖 JARVIS AI Assistant - Enterprise Dashboard v3.0 ║
╚═══════════════════════════════════════════════════════════╝
```

---

## 🧪 Testing Everything Works

### Test 1: Backend API
```bash
# Check health
curl http://localhost:8000/api/health

# Get deployments
curl http://localhost:8000/api/deployments

# Get models
curl http://localhost:8000/api/models

# API Docs (interactive!)
open http://localhost:8000/docs
```

### Test 2: Web Dashboard
```bash
# Open in browser
open http://localhost:3000

# Should show:
# ✓ JARVIS logo and hero
# ✓ System health gauge
# ✓ Metrics display
# ✓ Upgrade form
# ✓ Deployment history
```

### Test 3: Terminal UI
```bash
# In Terminal 3
# Should see:
# ✓ Beautiful formatted output
# ✓ Interactive buttons
# ✓ Real-time metrics
# ✓ Status indicators
```

### Test 4: Make a Real Request

**Via Web Dashboard:**
```
1. Open http://localhost:3000
2. Type in the textarea: "Add request logging"
3. Click Deploy
4. Should see status update
5. Check deployment history
```

**Via Terminal UI:**
```
1. In Terminal 3, press 'd' or click Deploy
2. Type: "Implement caching"
3. Press Enter
4. See real-time update
```

**Via API directly:**
```bash
curl -X POST http://localhost:8000/api/upgrade \
  -H "Content-Type: application/json" \
  -d '{"description": "Add webhook support"}'
```

---

## 🌐 Access Points

### Web Dashboard
```
URL: http://localhost:3000
Features:
  ✓ Beautiful modern UI
  ✓ Real-time metrics
  ✓ System health gauge
  ✓ Upgrade form
  ✓ Deployment timeline
  ✓ Mobile responsive
  ✓ Dark theme
```

### Terminal UI
```
Command: python jarvis_terminal_ui.py
Features:
  ✓ Beautiful TUI
  ✓ Keyboard navigation
  ✓ Real-time updates
  ✓ Status indicators
  ✓ Accessible
  ✓ Works over SSH
```

### API
```
Base URL: http://localhost:8000

Endpoints:
  GET  /api/health            - System health
  GET  /api/models            - Model status
  GET  /api/metrics           - Performance metrics
  GET  /api/deployments       - Deployment history
  POST /api/upgrade           - Request upgrade
  WS   /ws/metrics            - Real-time metrics
  WS   /ws/deployments        - Real-time deployments

Interactive Docs: http://localhost:8000/docs
```

---

## 🔧 Customization

### Change Backend Port
```python
# In jarvis_backend.py, change:
uvicorn.run(app, host="0.0.0.0", port=9000)  # Change to 9000
```

### Change Web Dashboard Port
```bash
npm run dev -- -p 3001  # Run on 3001 instead
```

### Change Terminal UI Theme
```python
# In jarvis_terminal_ui.py, add:
app = DashboardApp(theme="nord")  # Available: "nord", "dracula", "solarized", etc.
```

---

## 🚀 Deployment

### Deploy Backend to Cloud

**Option 1: Heroku**
```bash
cd /path/to/JARVIS
heroku create jarvis-api
git push heroku main
# Now at https://jarvis-api.herokuapp.com
```

**Option 2: Railway**
```bash
railway up jarvis_backend.py
# Now at https://jarvis-api.railway.app
```

**Option 3: PythonAnywhere**
```
1. Create account at pythonanywhere.com
2. Upload jarvis_backend.py
3. Configure web app
```

### Deploy Web Dashboard to Cloud

**Option 1: Vercel (RECOMMENDED)**
```bash
cd jarvis-dashboard
npm install -g vercel
vercel deploy
# Now at https://jarvis-dashboard.vercel.app
```

**Option 2: Netlify**
```bash
cd jarvis-dashboard
npm run build
netlify deploy --prod --dir=.next
```

**Option 3: GitHub Pages**
```bash
cd jarvis-dashboard
npm run build
npm run export
# Deploy .next to GitHub Pages
```

### Update Frontend to Use Remote Backend

In `jarvis-dashboard/components/HealthCard.tsx`:
```tsx
// Change this:
const response = await axios.get('http://localhost:8000/api/health');

// To this:
const response = await axios.get('https://jarvis-api.herokuapp.com/api/health');
```

---

## 📊 Architecture Diagram

```
User
  ├─→ Web Dashboard (Browser)
  │   ├─ http://localhost:3000
  │   └─ Beautiful responsive UI
  │
  ├─→ Terminal UI (CLI)
  │   ├─ Terminal
  │   └─ Fancy text interface
  │
  └─→ API (Programmatic)
      ├─ http://localhost:8000
      └─ REST endpoints

All three → FastAPI Backend
         ↓
      JARVIS Core
         ↓
    Multi-Model System
```

---

## 🐛 Troubleshooting

### Backend not starting
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process
kill -9 <PID>

# Try different port
python jarvis_backend.py --port 9000
```

### Web dashboard not connecting to backend
```bash
# 1. Verify backend is running
curl http://localhost:8000/api/health

# 2. Check CORS headers
curl -i http://localhost:8000/api/health

# 3. Check browser console for errors
# F12 → Console → Check for CORS errors

# 4. If using remote backend, update URL in components
```

### Terminal UI not displaying
```bash
# Ensure terminal supports colors
export TERM=xterm-256color

# Try different terminal
# iTerm2, Windows Terminal, or modern Linux terminal recommended

# Check textual is installed
python -m pip install --upgrade textual
```

### Deployments not showing in UI
```bash
# Check JARVIS core is working
python -c "from jarvis_smart_upgrade import get_deployment_history; print(get_deployment_history())"

# Restart backend to reload
```

---

## 📈 Next Steps

### Phase 1: Get Everything Running ✅
1. ✅ Backend running
2. ✅ Web dashboard running
3. ✅ Terminal UI running

### Phase 2: Make Requests
1. Open web dashboard or terminal UI
2. Request some upgrades
3. Watch them deploy in real-time
4. See updates in both interfaces simultaneously

### Phase 3: Deployment
1. Deploy backend to cloud
2. Deploy web dashboard to Vercel
3. Access from anywhere

### Phase 4: Add More Features
1. Email notifications
2. Slack integration
3. Custom themes
4. Advanced analytics
5. User authentication

---

## 🎓 Learning Resources

### FastAPI
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [WebSocket Guide](https://fastapi.tiangolo.com/advanced/websockets/)

### Next.js
- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/)

### Textual
- [Textual Documentation](https://textual.textualize.io/)
- [Rich Library](https://rich.readthedocs.io/)

---

## 🎉 You Now Have

✅ **FastAPI Backend** - REST API + WebSocket with real-time updates  
✅ **Web Dashboard** - Beautiful Next.js interface, mobile-responsive  
✅ **Terminal UI** - Fancy CLI, accessible, keyboard-friendly  
✅ **Real-Time Sync** - All three interfaces show same data  
✅ **Production Ready** - Deployable to cloud  

---

## 🚀 Quick Command Reference

```bash
# Terminal 1: Start Backend
cd /path/to/JARVIS && python jarvis_backend.py

# Terminal 2: Start Web Dashboard
cd jarvis-dashboard && npm run dev

# Terminal 3: Start Terminal UI
cd /path/to/JARVIS && python jarvis_terminal_ui.py

# Test Backend
curl http://localhost:8000/api/health

# Open Web Dashboard
open http://localhost:3000

# API Documentation
open http://localhost:8000/docs
```

---

**Everything is ready! Start the three terminals and watch the magic happen! 🪄**

Questions? Check the individual setup guides:
- `WEB_DASHBOARD_SETUP.md` - Detailed web dashboard
- `UI_SUGGESTIONS.md` - Full UI recommendations
- `SMART_UPGRADE_GUIDE.md` - How upgrades work
