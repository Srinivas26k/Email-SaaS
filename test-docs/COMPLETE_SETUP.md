# ✅ Complete Setup - Reply Detection & Auto-Calendar

## 🎉 Everything is Ready!

I've completed the full implementation of:
1. ✅ Custom reply template system
2. ✅ Improved reply detection
3. ✅ Manual reply checker tool
4. ✅ Placeholder support for personalization
5. ✅ Backend fixed and running

---

## 🚀 Quick Start (3 Steps)

### Step 1: Start the Backend

```bash
uv run python -m backend.main
```

Wait for:
```
✅ Database initialized
✅ Background worker started
✅ Reply checker started
🎉 System ready!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Check for Existing Replies

```bash
uv run python manual_reply_check.py
```

This will:
- Show all your leads
- Scan inbox for replies
- Update statuses to "REPLIED"
- Send calendar links automatically

### Step 3: Customize Your Reply Template

1. Open: http://localhost:8000
2. Click "Templates" in sidebar
3. Scroll to "Auto-Reply (when they respond)"
4. Customize your message
5. Click "SAVE TEMPLATES"

---

## 📋 Your Current Leads

From the manual checker, I can see you have 5 leads:
- rajeshviprala31+a@gmail.com - SENT
- rajeshviprala31+b@gmail.com - SENT
- rajeshviprala31+c@gmail.com - SENT
- rajeshviprala31+d@gmail.com - SENT
- rajeshviprala31+r@gmail.com - SENT

The system will detect replies from these emails automatically.

---

## 🎨 Template Example

Here's a good template to start with:

**Subject:**
```
Let's schedule a call, {{first_name}}!
```

**Body:**
```
Hi {{first_name}},

Thanks for getting back to me! I'd love to discuss how we can help {{company}}.

Please book a time that works best for you:
{{calendar_link}}

Looking forward to our conversation!

Best regards
```

### Available Placeholders:
- `{{first_name}}` - From your CSV
- `{{company}}` - From your CSV
- `{{industry}}` - From your CSV
- `{{email}}` - Lead's email
- `{{calendar_link}}` - Your Calendly link
- Any other CSV columns

---

## 🔍 How Reply Detection Works

### Automatic (Every 5 Minutes)
When backend is running, the reply checker automatically:
1. Scans your inbox
2. Looks for emails from leads in database
3. Updates status to "REPLIED"
4. Sends personalized calendar link
5. Logs the event

### Manual (On Demand)
Run anytime:
```bash
uv run python manual_reply_check.py
```

Use this when:
- You just received a reply
- Testing the system
- Want immediate action

---

## 📊 Monitoring Replies

### Dashboard
1. Open http://localhost:8000
2. Check "REPLIES" metric on dashboard
3. Go to "Leads" page → Filter by "Replied"
4. Check "Recent Activity" for reply logs

### Logs
Backend terminal shows:
```
📧 Reply detected from: email@example.com (was SENT)
✅ Sent calendar link to email@example.com
```

---

## 🔧 Configuration

### Update Calendar Link
Edit `.env`:
```env
CALENDAR_LINK=https://calendly.com/your-link
```

Restart backend.

### Change Reply Check Frequency
Edit `backend/main.py`, line ~60:
```python
time.sleep(300)  # 5 minutes
```

Change to:
```python
time.sleep(60)  # 1 minute
```

---

## 🆘 Troubleshooting

### "No replies detected"

**Check 1:** Are the emails in your database?
```bash
uv run python manual_reply_check.py
```

Look at "Current Leads in Database" section.

**Check 2:** IMAP credentials correct?
```bash
uv run python -c "from backend.reply_checker import ReplyChecker; ReplyChecker().test_connection()"
```

Should show: `✅ IMAP connection test successful`

**Check 3:** Gmail App Password
Make sure you're using an App Password, not your regular password.

### "Calendar link not sent"

**Check SMTP settings in `.env`:**
```env
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### "Template not saving"

1. Check backend is running
2. Hard refresh browser (Ctrl+Shift+R)
3. Check browser console for errors (F12)

---

## 📁 Files Created/Modified

### New Files:
- `manual_reply_check.py` - Manual reply checker
- `REPLY_TEMPLATE_GUIDE.md` - Complete documentation
- `QUICK_REPLY_FIX.md` - Quick reference
- `COMPLETE_SETUP.md` - This file

### Modified Files:
- `backend/reply_checker.py` - Improved detection
- `backend/database.py` - Added reply template
- `backend/main.py` - Fixed imports, added reply template API
- `frontend/index.html` - Added reply template UI
- `frontend/app.js` - Added reply template handling
- `frontend/styles.css` - Updated layout

---

## ✅ Testing Checklist

- [ ] Backend starts without errors
- [ ] Manual reply checker runs successfully
- [ ] Dashboard loads at http://localhost:8000
- [ ] Templates page shows 4 template boxes
- [ ] Reply template can be edited and saved
- [ ] Leads page shows current leads
- [ ] IMAP connection test passes

---

## 🎯 What Happens When Someone Replies

1. **Reply arrives** in your inbox
2. **Reply checker detects** it (every 5 minutes, or run manual checker)
3. **Status updates** to "REPLIED" in database
4. **Calendar email sent** automatically with your custom template
5. **Event logged** in dashboard
6. **Metrics updated** - "REPLIES" counter increases

---

## 📞 Next Steps

1. **Run manual checker** to process existing replies:
   ```bash
   uv run python manual_reply_check.py
   ```

2. **Customize your template** at http://localhost:8000/templates

3. **Monitor the dashboard** to see replies coming in

4. **Check your sent emails** to verify calendar links are being sent

---

## 🎉 You're All Set!

The system is fully configured and ready to:
- ✅ Detect replies automatically
- ✅ Send personalized calendar links
- ✅ Track everything in the dashboard
- ✅ Use your custom templates

**Start now:** `uv run python -m backend.main`
