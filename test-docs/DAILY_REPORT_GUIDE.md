# 📊 Daily Analytics Report - Complete Guide

## ✅ What's New

I've added a **professional daily analytics report** system that automatically emails you a comprehensive summary every night at 1 AM.

---

## 🎯 Features

### 1. **Automatic Daily Email Report**
- Sent every night at 1 AM automatically
- Beautiful HTML email with professional design
- Comprehensive analytics and metrics
- 7-day trend analysis
- Recent activity log

### 2. **Manual Report Generation**
- Send report anytime on-demand
- Test the report before midnight
- Preview report data via API

### 3. **Professional Analytics**
- Today's performance metrics
- Overall campaign statistics
- Reply rates and failure rates
- Daily progress tracking
- 7-day trend visualization

---

## 📊 What's Included in the Report

### Today's Metrics
- **Emails Sent Today** - How many emails sent today
- **Replies Today** - How many people replied
- **Failed Today** - How many emails failed
- **Daily Usage** - Percentage of daily limit used

### Overall Statistics
- **Total Leads** - All leads in database
- **Total Sent** - All emails sent
- **Total Replied** - All replies received
- **Reply Rate** - Percentage of emails that got replies
- **Total Failed** - All failed emails
- **Failure Rate** - Percentage of failed emails
- **Pending** - Leads waiting to be sent
- **Campaign Status** - Current campaign state

### 7-Day Trend
- Table showing last 7 days
- Emails sent per day
- Replies received per day
- Easy to spot trends

### Recent Activity
- Last 5 important events
- Timestamps for each event
- Quick glance at what happened

---

## 🚀 How It Works

### Automatic (Every Night at 1 AM)

The system automatically:
1. Generates analytics report at 1 AM
2. Creates beautiful HTML email
3. Sends to your configured email address
4. Logs the event

**No action needed!** Just check your inbox every morning.

### Manual (On Demand)

Send a report anytime:

**Option 1: Command Line**
```bash
uv run python send_test_report.py
```

**Option 2: API Call**
```bash
curl -X POST "http://localhost:8000/api/report/send"
```

**Option 3: Custom Email**
```bash
curl -X POST "http://localhost:8000/api/report/send?email=custom@example.com"
```

---

## 🎨 Report Design

The email report features:
- **Professional gradient header** with date and status
- **Color-coded metrics** (green for success, red for failures, etc.)
- **Progress bar** showing daily limit usage
- **Clean table** for 7-day trend
- **Activity timeline** with recent events
- **Responsive design** that works on mobile and desktop

---

## 🔧 Configuration

### Change Report Time

Edit `backend/scheduler.py`, line ~60:

```python
# Current: 1 AM
self.scheduler.add_job(
    func=self.send_daily_report,
    trigger='cron',
    hour=1,  # Change this (0-23)
    minute=0,
    id='daily_report',
    name='Send daily analytics report',
    replace_existing=True
)
```

Examples:
- `hour=0` - Midnight
- `hour=12` - Noon
- `hour=23` - 11 PM

### Change Report Recipient

By default, reports go to your configured email (`EMAIL_ADDRESS` in `.env`).

To send to a different email:
```bash
curl -X POST "http://localhost:8000/api/report/send?email=boss@company.com"
```

### Customize Report Content

Edit `backend/daily_report.py`:
- `generate_report()` - Modify data collection
- `generate_html_report()` - Modify email design

---

## 📋 Testing the Report

### Test 1: Generate Report Data

```bash
curl http://localhost:8000/api/report/preview | python3 -m json.tool
```

This shows the raw data without sending an email.

### Test 2: Send Test Report

```bash
uv run python send_test_report.py
```

This will:
1. Show you a preview of the report data
2. Ask for confirmation
3. Send the email if you confirm

### Test 3: Check Email

1. Run the test script
2. Check your inbox (EMAIL_ADDRESS from .env)
3. Look for subject: "📊 Daily Outreach Report - YYYY-MM-DD"

---

## 🎯 What You'll See in Your Inbox

**Subject:** 📊 Daily Outreach Report - 2026-02-08

**Email Content:**
```
┌─────────────────────────────────────┐
│   📊 Daily Outreach Report          │
│   2026-02-08 • Campaign: RUNNING    │
└─────────────────────────────────────┘

┌──────────┬──────────┬──────────┬──────────┐
│ Sent     │ Replies  │ Failed   │ Usage    │
│ Today    │ Today    │ Today    │          │
├──────────┼──────────┼──────────┼──────────┤
│   15     │    3     │    0     │   3%     │
│ of 500   │          │          │          │
└──────────┴──────────┴──────────┴──────────┘

Daily Progress
[████████░░░░░░░░░░░░░░░░░░░░] 15 / 500

Overall Statistics
├─ Total Leads: 100
├─ Total Sent: 50
├─ Total Replied: 10
├─ Reply Rate: 20%
├─ Total Failed: 2
├─ Failure Rate: 2%
├─ Pending: 48
└─ Campaign Status: RUNNING

Last 7 Days Trend
Date       | Sent | Replied
2026-02-02 |  12  |    2
2026-02-03 |  15  |    3
2026-02-04 |  18  |    4
...

Recent Activity
• Sent initial email to john@example.com
  2026-02-08 14:30:15
• Reply received from jane@example.com
  2026-02-08 13:45:22
...
```

---

## 🆘 Troubleshooting

### "Report not received"

**Check 1: Is scheduler running?**
```bash
curl http://localhost:8000/health
```

Should show: `"scheduler_running": true`

**Check 2: Check backend logs**

Look for:
```
📊 Generating and sending daily report...
✅ Daily report sent to your-email@gmail.com
```

**Check 3: Test SMTP**
```bash
uv run python -c "from backend.email_sender import EmailSender; EmailSender().test_connection()"
```

**Check 4: Check spam folder**

The report might be in spam. Add your email to contacts.

### "Report looks broken"

**Issue:** HTML not rendering properly

**Solution:** Some email clients block HTML. Try:
- Gmail (web) - Best support
- Outlook (web) - Good support
- Apple Mail - Good support

### "Want to customize report"

Edit `backend/daily_report.py`:

**Change colors:**
```python
# Line ~150
.metric.success .metric-value {{ color: #4CAF50; }}  # Green
.metric.danger .metric-value {{ color: #F44336; }}   # Red
```

**Add more metrics:**
```python
# In generate_report() method
# Add your custom queries
custom_metric = session.query(Lead).filter(...).count()
```

---

## 📁 Files Created

- `backend/daily_report.py` - Report generator
- `send_test_report.py` - Manual test script
- `DAILY_REPORT_GUIDE.md` - This guide

## 📁 Files Modified

- `backend/scheduler.py` - Added daily report task
- `backend/email_sender.py` - Added HTML email support
- `backend/main.py` - Added report API endpoints

---

## ✅ Quick Start Checklist

- [ ] Backend is running with scheduler
- [ ] Test report generation: `uv run python send_test_report.py`
- [ ] Check email inbox for test report
- [ ] Verify report looks good
- [ ] Wait for automatic report at 1 AM tomorrow
- [ ] Check inbox next morning

---

## 🎉 Summary

**Automatic Reports:** ✅ Sent every night at 1 AM  
**Manual Reports:** ✅ Send anytime with test script  
**Professional Design:** ✅ Beautiful HTML email  
**Comprehensive Analytics:** ✅ All metrics included  
**7-Day Trends:** ✅ Easy to spot patterns  
**Recent Activity:** ✅ Quick glance at events  

**Test it now:** `uv run python send_test_report.py`

You'll receive a professional analytics report in your inbox every morning! 📊
