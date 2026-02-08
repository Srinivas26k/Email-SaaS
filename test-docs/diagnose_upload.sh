#!/bin/bash

echo "🔍 CSV Upload Diagnostics"
echo "=========================="
echo ""

# Check if backend is running
echo "1. Checking if backend is running..."
if curl -s http://localhost:8000/api/metrics > /dev/null 2>&1; then
    echo "   ✅ Backend is running on port 8000"
else
    echo "   ❌ Backend is NOT running!"
    echo "   → Start it with: uv run python -m backend.main"
    exit 1
fi

echo ""

# Check metrics
echo "2. Current metrics:"
curl -s http://localhost:8000/api/metrics | python3 -m json.tool | head -10

echo ""

# Test upload with sample file
echo "3. Testing CSV upload with sample_leads.csv..."
if [ -f "sample_leads.csv" ]; then
    RESPONSE=$(curl -s -X POST "http://localhost:8000/api/upload-leads" -F "file=@sample_leads.csv")
    echo "   Response: $RESPONSE"
    
    if echo "$RESPONSE" | grep -q "success.*true"; then
        echo "   ✅ Upload test SUCCESSFUL!"
    else
        echo "   ❌ Upload test FAILED!"
    fi
else
    echo "   ⚠️  sample_leads.csv not found"
fi

echo ""

# Check frontend files
echo "4. Checking frontend files..."
if [ -f "frontend/index.html" ]; then
    echo "   ✅ frontend/index.html exists"
else
    echo "   ❌ frontend/index.html missing"
fi

if [ -f "frontend/app.js" ]; then
    echo "   ✅ frontend/app.js exists"
else
    echo "   ❌ frontend/app.js missing"
fi

echo ""

# Check browser access
echo "5. Testing browser access..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)
if [ "$STATUS" = "200" ]; then
    echo "   ✅ Dashboard accessible at http://localhost:8000"
else
    echo "   ❌ Dashboard returned status: $STATUS"
fi

echo ""
echo "=========================="
echo "📋 Next Steps:"
echo ""
echo "1. Open your browser to: http://localhost:8000"
echo "2. Press F12 to open Developer Tools"
echo "3. Go to Console tab"
echo "4. Try uploading a CSV file"
echo "5. Check console for any error messages"
echo ""
echo "Alternative test page:"
echo "   file://$(pwd)/test_upload.html"
echo ""
