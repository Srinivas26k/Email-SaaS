#!/usr/bin/env python3
"""
Test script to verify all system components are working correctly.
Run this before starting the full application.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from backend import config
        print("  ✅ config module")
        
        from backend import database
        print("  ✅ database module")
        
        from backend import license_validator
        print("  ✅ license_validator module")
        
        from backend import templates
        print("  ✅ templates module")
        
        from backend import email_sender
        print("  ✅ email_sender module")
        
        from backend import reply_checker
        print("  ✅ reply_checker module")
        
        from backend import background_worker
        print("  ✅ background_worker module")
        
        from backend import main
        print("  ✅ main module")
        
        print("\n✅ All imports successful!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {str(e)}\n")
        return False


def test_database_schema():
    """Test database schema creation."""
    print("🔍 Testing database schema...")
    
    try:
        from backend.database import init_db, Lead, Campaign, Log, LeadStatus, CampaignStatus
        
        # Initialize database
        init_db()
        print("  ✅ Database initialized")
        
        # Check that tables exist
        from backend.database import engine
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = ['leads', 'campaign', 'logs']
        for table in expected_tables:
            if table in tables:
                print(f"  ✅ Table '{table}' exists")
            else:
                print(f"  ❌ Table '{table}' missing")
                return False
        
        print("\n✅ Database schema valid!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Database test failed: {str(e)}\n")
        return False


def test_templates():
    """Test template rendering."""
    print("🔍 Testing template rendering...")
    
    try:
        from backend.templates import render_template
        
        # Test healthcare template
        result = render_template('healthcare', 'initial', {
            'first_name': 'John',
            'company': 'Acme Corp',
            'industry': 'healthcare'
        })
        
        if result['subject'] and result['body']:
            print("  ✅ Healthcare template renders correctly")
        else:
            print("  ❌ Healthcare template incomplete")
            return False
        
        # Test fintech template
        result = render_template('fintech', 'followup1', {
            'first_name': 'Jane',
            'company': 'FinTech Inc',
            'industry': 'fintech'
        })
        
        if result['subject'] and result['body']:
            print("  ✅ Fintech template renders correctly")
        else:
            print("  ❌ Fintech template incomplete")
            return False
        
        print("\n✅ Template system working!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Template test failed: {str(e)}\n")
        return False


def test_config():
    """Test configuration loading."""
    print("🔍 Testing configuration...")
    
    try:
        from backend.config import config
        
        # Check that config loads (even if values are defaults)
        print(f"  ℹ️  API Host: {config.API_HOST}")
        print(f"  ℹ️  API Port: {config.API_PORT}")
        print(f"  ℹ️  Daily Limit: {config.DAILY_EMAIL_LIMIT}")
        print(f"  ℹ️  SMTP Server: {config.SMTP_SERVER}")
        
        # Check if .env exists
        env_file = project_root / '.env'
        if env_file.exists():
            print("  ✅ .env file exists")
        else:
            print("  ⚠️  .env file not found - using defaults")
            print("  ℹ️  Copy .env.example to .env and configure")
        
        print("\n✅ Configuration loaded!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Config test failed: {str(e)}\n")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  EMAIL OUTREACH SYSTEM - VERIFICATION TEST")
    print("="*60 + "\n")
    
    all_passed = True
    
    # Run tests
    all_passed &= test_imports()
    all_passed &= test_config()
    all_passed &= test_database_schema()
    all_passed &= test_templates()
    
    # Summary
    print("="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\nSystem is ready to run.")
        print("\nNext steps:")
        print("1. Configure .env file with your credentials")
        print("2. Run: uv run python -m backend.main")
        print("3. Open: http://localhost:8000")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease fix the errors above before running the system.")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
