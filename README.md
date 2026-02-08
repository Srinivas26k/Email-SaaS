# Email Outreach System - Production Ready

## 🚀 Quick Start - Cloud Deployment

This system is **production-ready** for 24/7 cloud operation with:
- ✅ **Parallel background processing** (email sending + reply checking)
- ✅ **Crash recovery** (auto-restarts on failures)
- ✅ **PostgreSQL** support for cloud databases
- ✅ **Horizontal scaling** ready
- ✅ **Health monitoring** endpoints

---

## 📋 What's New - Production Enhancements

### 1. **APScheduler Integration** (`backend/scheduler.py`)
Replaced threading with production-grade scheduler:

```python
# 3 Independent Background Tasks:
1. Email Queue Processing    → Every 30 seconds
2. Reply Checking            → Every 5 minutes  
3. Daily Counter Reset       → Midnight (cron)
```

**Why This Matters:**
- ✅ Tasks run in parallel (non-blocking)
- ✅ Survives server restarts
- ✅ Configurable intervals
- ✅ Automatic error recovery

### 2. **PostgreSQL Support** (Cloud-Ready)
- SQLite → PostgreSQL migration
- Auto-detects `DATABASE_URL` from Railway/Render
- Connection pooling for performance
- ACID compliance for reliability

### 3. **Health Monitoring**
```bash
GET /health
```
Returns:
```json
{
  "status": "healthy",
  "scheduler_running": true,
  "timestamp": "2024-02-08T10:30:00Z"
}
```

Use with UptimeRobot for 24/7 monitoring.

---

## 🔄 How Parallel Processing Works

### Architecture Overview

```
┌─────────────────────────────────────────┐
│         FastAPI Web Server              │
│   (Handles API requests + Dashboard)    │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         APScheduler Background          │
│                                         │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Email Queue  │  │Reply Checker │   │
│  │ (30s loop)   │  │ (5min loop)  │   │
│  └──────────────┘  └──────────────┘   │
│         │                  │           │
│         └──────┬───────────┘           │
│                ▼                       │
│       ┌─────────────────┐             │
│       │ Database (Leads)│             │
│       └─────────────────┘             │
└─────────────────────────────────────────┘
```

### Task Flow

**1. Email Sending (Every 30 seconds)**
```
Check Campaign Status → Get Next Lead → Send Email → Update DB → Apply Rate Limit
```

**2. Reply Checking (Every 5 minutes)**
```
Connect IMAP → Fetch New Emails → Match with Leads → Mark as Replied → Send Calendar Link
```

**3. Daily Reset (Midnight)**
```
Reset sent_today counter → Update last_reset_date
```

### Key Features

**Non-Blocking:** All tasks run independently
```python
# Email sending doesn't block reply checking
# Reply checking doesn't block daily reset
# Dashboard API remains responsive
```

**Crash Recovery:**
```python
# If email sending fails → Logs error, continues with next lead
# If reply check fails → Logs error, retries in 5 minutes
# Database errors → Automatic retry with backoff
```

**Rate Limiting:**
```python
# Between emails: 60-120 seconds random delay
# After 20 emails: 5-8 minute pause
# Daily limit: Stops at 500/day (configurable)
```

---

## 📁 File Structure

```
email-outreach-system/
├── backend/
│   ├── main.py              # FastAPI app with scheduler integration
│   ├── scheduler.py         # ⭐ NEW: APScheduler background tasks
│   ├── config.py            # ⭐ UPDATED: PostgreSQL support
│   ├── database.py          # ORM models
│   ├── email_sender.py      # SMTP sending logic
│   ├── reply_checker.py     # IMAP reply detection
│   ├── templates.py         # Email templates
│   └── license_validator.py # License checking
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── requirements.txt         # ⭐ UPDATED: Added APScheduler + psycopg2
├── Procfile                 # ⭐ NEW: Railway/Render deployment
├── railway.json             # ⭐ NEW: Railway config
├── render.yaml              # ⭐ NEW: Render config
├── DEPLOYMENT_GUIDE.md      # ⭐ NEW: Step-by-step deployment
└── .env.example
```

---

## 🚀 Deployment Options

### Option 1: Railway.app (Recommended - $5/month)
```bash
1. Push code to GitHub
2. Connect Railway to your repo
3. Add PostgreSQL database
4. Set environment variables
5. Deploy! ✅
```

### Option 2: Render.com (Free tier available)
```bash
1. Push code to GitHub
2. Import repository to Render
3. render.yaml auto-configures everything
4. Deploy! ✅
```

### Option 3: DigitalOcean App Platform ($5/month)
```bash
1. Create App Platform app
2. Connect GitHub
3. Configure buildpack (Python)
4. Add managed PostgreSQL
5. Deploy! ✅
```

**Full deployment instructions:** See `DEPLOYMENT_GUIDE.md`

---

## ⚙️ Environment Variables

**Required:**
```env
LICENSE_SHEET_URL=https://docs.google.com/spreadsheets/d/.../export?format=csv
LICENSE_KEY=your-license-key
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password  # Gmail App Password, not regular password!
```

**Optional (with defaults):**
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
DAILY_EMAIL_LIMIT=500
MIN_DELAY_SECONDS=60
MAX_DELAY_SECONDS=120
PAUSE_EVERY_N_EMAILS=20
PAUSE_MIN_MINUTES=5
PAUSE_MAX_MINUTES=8
CALENDAR_LINK=https://calendly.com/your-link
```

**Auto-configured by platform:**
```env
DATABASE_URL=postgresql://...  # Railway/Render sets this automatically
PORT=8000                      # Railway/Render sets this automatically
```

---

## 🔧 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your credentials

# Run migrations (creates SQLite DB locally)
python -c "from backend.database import init_db; init_db()"

# Start server
uvicorn backend.main:app --reload

# Access dashboard
open http://localhost:8000
```

**Note:** Local uses SQLite, cloud uses PostgreSQL

---

## 📊 Monitoring

### Health Check
```bash
curl https://your-app.railway.app/health
```

### View Logs
**Railway:**
```bash
railway logs
```

**Render:**
```bash
# View in dashboard → Logs tab
```

### What to Monitor

✅ **Scheduler Status:** `scheduler_running: true`
✅ **Email Sending:** `✅ Sent initial to user@example.com`
✅ **Reply Checking:** `📬 Checking for replies...`
✅ **Errors:** `❌ Error sending to...` (should be rare)

---

## 🎯 Key Metrics

### Dashboard Shows:
- **Sent Today:** Current / Daily Limit
- **Replies:** Total reply count
- **Failed:** Failed email count
- **Campaign Status:** Running / Paused / Stopped

### Database Tracks:
- Lead status (PENDING → SENT → REPLIED)
- Follow-up count (0, 1, 2)
- Last sent timestamp
- All activity logs

---

## 🐛 Troubleshooting

### Scheduler Not Running
**Check logs for:**
```
✅ Email scheduler started
```

**If missing:**
1. Verify `backend/scheduler.py` exists
2. Check `main.py` imports `email_scheduler`
3. Restart service

### Emails Not Sending
**Check:**
1. ✅ Campaign status = RUNNING
2. ✅ Gmail App Password (not regular password)
3. ✅ Daily limit not reached
4. ✅ Leads exist with PENDING status

### Replies Not Detected
**Check:**
1. ✅ IMAP credentials correct
2. ✅ Reply checker running (logs show `📬 Checking...`)
3. ✅ Emails are actually replies (not new emails)

---

## 📈 Scaling

### Current Capacity
- **500 emails/day** (configurable)
- **Single worker** handles ~1 email/minute
- **PostgreSQL** supports millions of leads

### To Scale Up

**Increase Daily Limit:**
```env
DAILY_EMAIL_LIMIT=1000
```

**Faster Processing:**
```python
# In scheduler.py, line 27:
IntervalTrigger(seconds=15)  # Was 30 seconds
```

**Multiple Workers:**
```yaml
# railway.json
"replicas": 2
```

**Note:** Multiple replicas need Redis for coordination (advanced)

---

## 🔐 Security

✅ **Credentials:** Never commit `.env` file
✅ **License:** Validated on startup (blocks unauthorized use)
✅ **HTTPS:** Automatic with Railway/Render
✅ **Environment Variables:** Encrypted in platform

---

## 📞 Support

**Issues?**
1. Check `DEPLOYMENT_GUIDE.md`
2. Review logs in hosting dashboard
3. Test `/health` endpoint
4. Verify environment variables

**Performance Questions?**
- Current setup handles **500 emails/day**
- Can scale to **5,000+ emails/day** with Redis + multiple workers
- PostgreSQL supports **unlimited leads**

---

## 🎉 You're Ready!

Your email outreach system is now:
- ✅ Running 24/7 in the cloud
- ✅ Processing emails in parallel
- ✅ Automatically checking replies
- ✅ Sending calendar links on reply
- ✅ Crash-resistant with auto-recovery
- ✅ Fully monitored and logged

**Next Steps:**
1. Deploy to Railway/Render (15 minutes)
2. Upload your lead list
3. Start campaign
4. Monitor for 24 hours
5. Scale as needed

Happy outreaching! 🚀