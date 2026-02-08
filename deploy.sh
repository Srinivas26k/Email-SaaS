#!/bin/bash

# 🚀 Quick Deploy Script for Railway

echo "🚀 Email Outreach System - Quick Deploy"
echo "========================================"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Error: Not a git repository"
    echo "   Run: git init"
    exit 1
fi

# Check if files are committed
if [[ `git status --porcelain` ]]; then
    echo "📝 Uncommitted changes found. Committing..."
    git add .
    git commit -m "Production ready - Railway deployment"
    echo "✅ Changes committed"
else
    echo "✅ All changes already committed"
fi

# Check if remote exists
if ! git remote | grep -q "origin"; then
    echo ""
    echo "❌ No git remote found"
    echo ""
    echo "📋 Next steps:"
    echo "1. Create a GitHub repository"
    echo "2. Add remote: git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
    echo "3. Push: git push -u origin main"
    echo "4. Go to railway.app and deploy from GitHub"
    exit 1
fi

# Push to GitHub
echo ""
echo "📤 Pushing to GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Pushed to GitHub successfully"
else
    echo "❌ Failed to push to GitHub"
    exit 1
fi

echo ""
echo "🎉 Code is ready for deployment!"
echo ""
echo "📋 Next steps:"
echo "1. Go to https://railway.app"
echo "2. Click 'New Project' → 'Deploy from GitHub'"
echo "3. Select your repository"
echo "4. Click 'Deploy'"
echo "5. Add PostgreSQL database (+ New → PostgreSQL)"
echo "6. Set environment variables (see .env.example)"
echo ""
echo "📚 Full guide: DEPLOYMENT_GUIDE.md"
echo ""
echo "✨ Your app will be live in ~5 minutes!"
