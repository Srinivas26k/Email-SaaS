# 🔧 Troubleshooting Guide

## CSV Upload Issues

### Problem: "Unable to upload CSV"

#### Solution 1: Make sure the backend is running

The most common issue is that the backend server is not running.

**Check if backend is running:**
```bash
# You should see output like "Uvicorn running on http://0.0.0.0:8000"
ps aux | grep "backend.main"
```

**Start the backend:**
```bash
uv run python -m backend.main
```

You should see:
```
✅ License validated successfully
✅ Database initialized
✅ Background worker started
✅ Reply checker started
🎉 System ready!
```

#### Solution 2: Check browser console for errors

1. Open the dashboard at http://localhost:8000
2. Press F12 to open Developer Tools
3. Go to the "Console" tab
4. Try uploading a CSV
5. Look for any red error messages

Common errors:
- **"Failed to fetch"** → Backend is not running
- **"CORS error"** → Backend CORS configuration issue (already fixed)
- **"400 Bad Request"** → File format issue (must be .csv)
- **"500 Internal Server Error"** → Check backend logs

#### Solution 3: Verify CSV format

Your CSV must have an `email` column:

```csv
email,first_name,company,industry
john@example.com,John,Acme Corp,Tech
jane@example.com,Jane,Beta Inc,Finance
```

**Test with sample file:**
```bash
# Use the included sample file
curl -X POST "http://localhost:8000/api/upload-leads" \
  -F "file=@sample_leads.csv"
```

#### Solution 4: Check file size

FastAPI has default limits. For very large files (>10MB), you may need to increase limits.

#### Solution 5: Clear browser cache

Sometimes old JavaScript is cached:
1. Press Ctrl+Shift+R (hard refresh)
2. Or clear browser cache completely

---

## Other Common Issues

### Backend won't start

**Error: "Missing required configuration"**
```bash
# Make sure .env file exists and has required fields
cat .env | grep -E "LICENSE_KEY|EMAIL_ADDRESS|EMAIL_PASSWORD"
```

**Error: "License validation failed"**
- Check LICENSE_SHEET_URL is accessible
- Verify LICENSE_KEY exists in the Google Sheet
- Make sure Sheet is published/public

### No emails sending

1. **Check campaign status:**
   - Dashboard should show "RUNNING" (not "STOPPED" or "PAUSED")
   - Click "START" button if stopped

2. **Check daily limit:**
   - If you've sent 500 emails today, wait until tomorrow
   - Or increase DAILY_EMAIL_LIMIT in .env

3. **Check email credentials:**
   ```bash
   # Test SMTP connection
   uv run python -c "
   import smtplib
   from backend.config import config
   server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
   server.starttls()
   server.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
   print('✅ SMTP connection successful')
   "
   ```

### Dashboard not loading

1. **Check if backend is running:**
   ```bash
   curl http://localhost:8000/api/metrics
   ```

2. **Check port 8000 is not in use:**
   ```bash
   lsof -i :8000
   ```

3. **Try different browser or incognito mode**

---

## Debug Mode

### Enable verbose logging

Add to backend/main.py startup:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check database

```bash
# View database contents
sqlite3 email_system.db "SELECT * FROM leads LIMIT 5;"
sqlite3 email_system.db "SELECT * FROM campaign;"
```

### Monitor logs in real-time

```bash
# Watch backend output
uv run python -m backend.main 2>&1 | tee backend.log
```

---

## Quick Fixes

### Reset everything

```bash
# Stop backend (Ctrl+C)
# Delete database
rm email_system.db

# Restart
uv run python -m backend.main
```

### Test upload from command line

```bash
# This should work if backend is running
curl -X POST "http://localhost:8000/api/upload-leads" \
  -F "file=@sample_leads.csv" \
  -v
```

---

## Getting Help

If none of these solutions work:

1. **Check backend logs** - Look for error messages
2. **Check browser console** - Look for JavaScript errors
3. **Test API directly** - Use curl commands above
4. **Verify .env configuration** - All required fields present

**Still stuck?** Share:
- Backend startup output
- Browser console errors
- Output of: `curl http://localhost:8000/api/metrics`
