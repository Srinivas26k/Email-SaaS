# ✅ Reply Detection & Auto-Calendar - FIXED!

## What I Fixed

### Problem 1: Replies Not Detected
**Issue:** You received replies but they weren't showing in the system.

**Root Cause:** Reply checker was only looking for leads with "SENT" status, but some leads might have different statuses.

**Fix:** Updated reply checker to check ALL leads in database, regardless of status.

### Problem 2: No Custom Reply Template
**Issue:** You wanted to customize the auto-reply message with placeholders.

**Solution:** Added a full template system with placeholder support.

---

## 🚀 What's New

### 1. Custom Reply Template UI
- New "Auto-Reply" section in Templates page
- Customize subject and body
- Use placeholders: `{{first_name}}`, `{{company}}`, `{{calendar_link}}`, etc.

### 2. Improved Reply Detection
- Checks ALL leads, not just "SENT" ones
- Better logging
- More robust error handling

### 3. Manual Reply Checker Tool
- Run on-demand to check for replies immediately
- Shows detailed information
- Updates database and sends calendar links

---

## 🎯 How to Use Right Now

### Step 1: Check for Existing Replies

Run this command to manually check your inbox and update the database:

```bash
uv run python manual_reply_check.py
```

This will:
- ✅ Show all leads in your database
- ✅ Scan your inbox for replies
- ✅ Update lead statuses to "REPLIED"
- ✅ Send calendar links automatically

### Step 2: Customize Your Reply Template

1. Start backend: `uv run python -m backend.main`
2. Open: http://localhost:8000
3. Click "Templates" in sidebar
4. Scroll to "Auto-Reply (when they respond)" section
5. Customize your message:

**Example:**
```
Subject: Let's schedule a call, {{first_name}}!

Body:
Hi {{first_name}},

Thanks for getting back to me! I'd love to discuss how we can help {{company}}.

Please book a time that works best for you:
{{calendar_link}}

Looking forward to our conversation!

Best regards
```

6. Click "SAVE TEMPLATES"

### Step 3: Verify It's Working

```bash
# Run manual check
uv run python manual_reply_check.py

# You should see:
# ✉️  From: email@example.com
# 🔄 Updating to REPLIED...
# ✅ Updated to REPLIED
# ✅ Sent calendar link to email@example.com
```

---

## 📊 Available Placeholders

### Always Available:
- `{{email}}` - Lead's email
- `{{calendar_link}}` - Your Calendly link

### From Your CSV:
- `{{first_name}}` - First name
- `{{company}}` - Company name
- `{{industry}}` - Industry
- Any other columns from your CSV

---

## 🔍 Why Replies Weren't Detected Before

Looking at your screenshot, I see replies from emails like:
- `rajee**@vjpra..`

These emails need to be in your leads database for the system to detect them.

**To check if they're in your database:**

```bash
uv run python manual_reply_check.py
```

Look at the "Current Leads in Database" section. If the email isn't there, the system won't detect it.

**Solution:** Make sure you uploaded a CSV with those email addresses.

---

## 🔧 Automatic vs Manual Checking

### Automatic (Background)
When backend is running, reply checker runs every 5 minutes automatically.

### Manual (On-Demand)
Run this anytime to check immediately:
```bash
uv run python manual_reply_check.py
```

Use manual checking when:
- You just received a reply and want immediate action
- Testing the system
- Troubleshooting

---

## ✅ Quick Test

1. **Check current leads:**
   ```bash
   uv run python manual_reply_check.py
   ```

2. **Start backend:**
   ```bash
   uv run python -m backend.main
   ```

3. **Open dashboard:**
   http://localhost:8000

4. **Go to Leads page:**
   - Click "Leads" in sidebar
   - Filter by "Replied"
   - You should see updated statuses

5. **Check logs:**
   - Go to Dashboard
   - Scroll to "Recent Activity"
   - Look for "Reply received from..." entries

---

## 🆘 If Replies Still Not Detected

### Check 1: Are emails in database?
```bash
uv run python manual_reply_check.py
```
Look at the leads list. If the email isn't there, upload a CSV with it.

### Check 2: IMAP credentials correct?
Check `.env` file:
```env
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password  # NOT regular password!
```

### Check 3: Test IMAP connection
```bash
uv run python -c "from backend.reply_checker import ReplyChecker; ReplyChecker().test_connection()"
```

Should show: `✅ IMAP connection test successful`

---

## 📁 New Files

- `manual_reply_check.py` - Manual reply checker tool
- `REPLY_TEMPLATE_GUIDE.md` - Complete documentation
- `QUICK_REPLY_FIX.md` - This file

---

## 🎉 Summary

✅ **Reply detection improved** - Now checks all leads
✅ **Custom template added** - Personalize your auto-reply
✅ **Manual checker created** - Check replies on-demand
✅ **Better logging** - See what's happening
✅ **Placeholder system** - Use {{variables}} in templates

**Next Step:** Run `uv run python manual_reply_check.py` to check for your existing replies!
