# 📅 Auto-Reply Template System - Complete Guide

## ✅ What's New

I've added a **customizable auto-reply template** system that automatically sends your calendar link when someone replies to your outreach emails.

---

## 🎯 Features Added

### 1. **Custom Reply Template**
- New template field in the Templates page
- Customize subject and body
- Use placeholders for personalization

### 2. **Automatic Placeholder Replacement**
- `{{first_name}}` - Lead's first name
- `{{company}}` - Lead's company
- `{{email}}` - Lead's email address
- `{{calendar_link}}` - Your calendar link
- Any other CSV columns you uploaded

### 3. **Improved Reply Detection**
- Now checks ALL leads, not just those with "SENT" status
- Better logging and error handling
- Manual check tool included

---

## 🚀 How to Use

### Step 1: Set Up Your Reply Template

1. **Open Dashboard:** http://localhost:8000
2. **Go to Templates page** (click Templates in sidebar)
3. **Scroll to "Auto-Reply" section** (4th template box)
4. **Customize your message:**

**Example Template:**

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

5. **Click "SAVE TEMPLATES"**

### Step 2: Verify Reply Detection is Working

Run the manual reply checker:

```bash
uv run python manual_reply_check.py
```

This will:
- Show all leads in your database
- Check your inbox for replies
- Update lead statuses to "REPLIED"
- Send calendar links automatically

---

## 🔍 Troubleshooting Replies Not Detected

### Issue: "I got replies but they're not showing in the system"

**Solution 1: Run Manual Reply Check**

```bash
uv run python manual_reply_check.py
```

This will scan your inbox and update the database immediately.

**Solution 2: Check if Emails are in Database**

The reply checker only works for emails that are in your leads database. If you sent emails manually (not through the system), they won't be detected.

To check:
```bash
uv run python manual_reply_check.py
```

Look at the "Current Leads in Database" section.

**Solution 3: Verify IMAP Settings**

Make sure your `.env` file has correct IMAP settings:

```env
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

**For Gmail:** You MUST use an App Password, not your regular password.

**Solution 4: Check Reply Checker Logs**

When the backend is running, you should see:
```
✅ Reply checker started
```

Every 5 minutes, it checks for new replies.

---

## 📊 How Reply Detection Works

### Automatic (Every 5 Minutes)

When the backend is running:
1. Reply checker scans inbox every 5 minutes
2. Looks for emails from leads in database
3. Updates status to "REPLIED"
4. Sends calendar link automatically
5. Logs the event

### Manual (On Demand)

Run the manual checker:
```bash
uv run python manual_reply_check.py
```

This gives you detailed output:
- Lists all leads in database
- Shows which emails were found
- Updates statuses
- Sends calendar links

---

## 🎨 Template Placeholders

### Always Available:
- `{{email}}` - Lead's email address
- `{{calendar_link}}` - Your calendar link (from .env)

### From CSV Upload:
- `{{first_name}}` - If your CSV has first_name column
- `{{company}}` - If your CSV has company column
- `{{industry}}` - If your CSV has industry column
- Any other columns from your CSV

### Example:

If your CSV has these columns:
```csv
email,first_name,company,industry,phone
```

You can use:
```
Hi {{first_name}},

I noticed {{company}} is in the {{industry}} space.

Let's connect: {{calendar_link}}

Feel free to call me at {{phone}} if you prefer.
```

---

## 🔧 Configuration

### Update Calendar Link

Edit `.env` file:
```env
CALENDAR_LINK=https://calendly.com/your-link
```

Restart backend:
```bash
uv run python -m backend.main
```

### Change Reply Check Frequency

Edit `backend/main.py`, line ~60:
```python
time.sleep(300)  # Check every 5 minutes (300 seconds)
```

Change to:
```python
time.sleep(60)  # Check every 1 minute
```

---

## 📋 Testing Your Setup

### Test 1: Check IMAP Connection

```bash
uv run python -c "from backend.reply_checker import ReplyChecker; ReplyChecker().test_connection()"
```

Should show: `✅ IMAP connection test successful`

### Test 2: Manual Reply Check

```bash
uv run python manual_reply_check.py
```

Should show:
- List of leads
- Any replies found
- Status updates

### Test 3: Send Test Reply

1. Send an email to yourself from one of your lead's email addresses
2. Run manual check: `uv run python manual_reply_check.py`
3. Check if status updated to "REPLIED"
4. Check if calendar email was sent

---

## 📁 Files Modified/Created

### Modified:
- `backend/reply_checker.py` - Improved reply detection
- `backend/database.py` - Added reply template support
- `backend/main.py` - Added reply template API
- `frontend/index.html` - Added reply template UI
- `frontend/app.js` - Added reply template handling
- `frontend/styles.css` - Updated template grid layout

### Created:
- `manual_reply_check.py` - Manual reply checker tool
- `REPLY_TEMPLATE_GUIDE.md` - This guide

---

## 🆘 Common Issues

### "No replies detected"

**Cause:** Reply checker only checks emails in your database.

**Fix:** Make sure you uploaded the CSV with those email addresses.

### "Calendar link not sent"

**Cause:** SMTP settings might be wrong.

**Fix:** Check `.env` file has correct EMAIL_ADDRESS and EMAIL_PASSWORD.

### "Template not saving"

**Cause:** Backend not running or JavaScript error.

**Fix:** 
1. Check backend is running
2. Press Ctrl+Shift+R to refresh browser
3. Check browser console for errors

---

## ✅ Quick Start Checklist

- [ ] Backend is running: `uv run python -m backend.main`
- [ ] Open dashboard: http://localhost:8000
- [ ] Go to Templates page
- [ ] Customize "Auto-Reply" template
- [ ] Click "SAVE TEMPLATES"
- [ ] Run manual check: `uv run python manual_reply_check.py`
- [ ] Verify replies are detected and calendar links sent

---

## 🎉 You're All Set!

Your auto-reply system is now configured. When someone replies to your outreach:

1. ✅ System detects the reply (every 5 minutes)
2. ✅ Updates lead status to "REPLIED"
3. ✅ Sends personalized calendar link automatically
4. ✅ Logs the event in dashboard

**Need immediate check?** Run: `uv run python manual_reply_check.py`
