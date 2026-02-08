#!/bin/bash

echo "🔍 Pre-Push Code Verification"
echo "=============================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# Check 1: Python syntax
echo "1️⃣  Checking Python syntax..."
for file in backend/*.py *.py; do
    if [ -f "$file" ]; then
        python3 -m py_compile "$file" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "   ${GREEN}✓${NC} $file"
        else
            echo -e "   ${RED}✗${NC} $file - Syntax error!"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done
echo ""

# Check 2: Required files exist
echo "2️⃣  Checking required files..."
REQUIRED_FILES=(
    "backend/main.py"
    "backend/config.py"
    "backend/database.py"
    "backend/email_sender.py"
    "backend/reply_checker.py"
    "backend/background_worker.py"
    "backend/template_renderer.py"
    "backend/templates.py"
    "backend/license_validator.py"
    "frontend/index.html"
    "frontend/app.js"
    "frontend/styles.css"
    ".env.example"
    "README.md"
    "QUICKSTART.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "   ${GREEN}✓${NC} $file"
    else
        echo -e "   ${RED}✗${NC} $file - Missing!"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# Check 3: .env file exists (but don't push it)
echo "3️⃣  Checking .env configuration..."
if [ -f ".env" ]; then
    echo -e "   ${GREEN}✓${NC} .env file exists"
    
    # Check if .env is in .gitignore
    if grep -q "^\.env$" .gitignore 2>/dev/null; then
        echo -e "   ${GREEN}✓${NC} .env is in .gitignore (won't be pushed)"
    else
        echo -e "   ${YELLOW}⚠${NC}  .env not in .gitignore - add it!"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "   ${YELLOW}⚠${NC}  .env file not found (needed for local testing)"
fi
echo ""

# Check 4: Database file (shouldn't be pushed)
echo "4️⃣  Checking database..."
if [ -f "email_system.db" ]; then
    echo -e "   ${GREEN}✓${NC} Database exists locally"
    
    if grep -q "email_system.db" .gitignore 2>/dev/null; then
        echo -e "   ${GREEN}✓${NC} Database is in .gitignore (w