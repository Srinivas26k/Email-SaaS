#!/usr/bin/env python3
"""Send a test daily report immediately."""

from backend.daily_report import DailyReportGenerator
from backend.config import config

def main():
    print("📊 Generating Daily Report...")
    print("=" * 60)
    
    generator = DailyReportGenerator()
    
    # Generate report data
    report = generator.generate_report()
    
    print(f"\n📋 Report Summary for {report['date']}:")
    print(f"   Today's Sent: {report['today']['sent']}")
    print(f"   Today's Replies: {report['today']['replied']}")
    print(f"   Today's Failed: {report['today']['failed']}")
    print(f"   Daily Usage: {round(report['today']['usage_percent'])}%")
    print()
    print(f"   Total Leads: {report['overall']['total_leads']}")
    print(f"   Total Sent: {report['overall']['total_sent']}")
    print(f"   Total Replied: {report['overall']['total_replied']}")
    print(f"   Reply Rate: {report['overall']['reply_rate']}%")
    print()
    
    # Ask for confirmation
    email = input(f"\n📧 Send report to {config.EMAIL_ADDRESS}? (y/n): ")
    
    if email.lower() == 'y':
        print("\n📤 Sending report...")
        success = generator.send_daily_report()
        
        if success:
            print("✅ Report sent successfully!")
            print(f"📬 Check your inbox: {config.EMAIL_ADDRESS}")
        else:
            print("❌ Failed to send report")
    else:
        print("❌ Report not sent")

if __name__ == "__main__":
    main()
