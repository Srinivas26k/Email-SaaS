# 📤 CSV Upload - Quick Reference

## ✅ Working Now!

The CSV upload feature is fully functional. Here's what you need to know:

---

## 🚀 How to Upload CSV

### Step 1: Start the Backend
```bash
uv run python -m backend.main
```

Wait for:
```
🎉 System ready!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Open Dashboard
Open browser: **http://localhost:8000**

### Step 3: Upload CSV
1. Scroll to "Upload Leads" section
2. Click "Browse..." or drag & drop your CSV file
3. Click "UPLOAD CSV" button
4. You'll see a notification: "Added X leads, skipped Y duplicates"

---

## 📋 CSV Format Requirements

### Required Column
- **email** - Must be present

### Optional Columns
- Any other columns you want (first_name, company, industry, etc.)
- All columns become available as template variables

### Example CSV
```csv
email,first_name,company,industry
john@example.com,John,Acme Corp,Tech
jane@example.com,Jane,Beta Inc,Finance
bob@example.com,Bob,Gamma LLC,Healthcare
```

---

## 🎯 What Happens After Upload

1. **Deduplication** - Duplicate emails are automatically skipped
2. **Column Detection** - All CSV columns become template variables
3. **Status Update** - Dashboard metrics update immediately
4. **Template Variables** - Go to Templates page to use {{column_name}}

---

## 🔍 Verify Upload Worked

### Check Dashboard Metrics
- "SENT TODAY" should show lead count
- Total leads counter updates

### Check Leads Page
1. Click "Leads" in sidebar
2. See all uploaded leads
3. Filter by status: Pending, Sent, Replied, Failed

### Check Templates Page
1. Click "Templates" in sidebar
2. See "Available Variables" section
3. Your CSV columns appear as clickable tags

---

## 💡 Tips

### Multiple Uploads
- You can upload multiple CSV files
- Duplicates are automatically skipped
- New columns are added to available variables

### Large Files
- System handles thousands of leads
- Upload may take a few seconds for large files
- Watch for success notification

### Testing
Use the included `sample_leads.csv`:
```bash
# Test from command line
curl -X POST "http://localhost:8000/api/upload-leads" \
  -F "file=@sample_leads.csv"
```

---

## 🐛 If Upload Fails

### Quick Checklist
- [ ] Backend is running (check terminal)
- [ ] Browser is at http://localhost:8000
- [ ] CSV file has 'email' column
- [ ] File extension is .csv

### See Detailed Help
Check `TROUBLESHOOTING.md` for complete debugging guide.

### Test Backend
```bash
# Should return metrics JSON
curl http://localhost:8000/api/metrics
```

---

## 📊 Current Status

**Backend:** ✅ Running  
**Upload Endpoint:** ✅ Working  
**Leads in Database:** 10  
**Campaign Status:** COMPLETED  

You're all set! The CSV upload is working perfectly.
