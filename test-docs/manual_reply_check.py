#!/usr/bin/env python3
"""Manual reply checker - Run this to manually check for replies and update the database."""

import imaplib
import email
from datetime import datetime, timedelta
from backend.config import config
from backend.database import SessionLocal, Lead, LeadStatus, Log
from backend.reply_checker import ReplyChecker

def extract_email(from_header: str) -> str:
    """Extract email address from From header."""
    if "<" in from_header and ">" in from_header:
        start = from_header.index("<") + 1
        end = from_header.index(">")
        return from_header[start:end].strip().lower()
    return from_header.strip().lower()

def check_all_replies():
    """Check for replies and show detailed information."""
    print("🔍 Checking for replies...")
    print("=" * 60)
    
    try:
        # Connect to IMAP
        mail = imaplib.IMAP4_SSL(config.IMAP_SERVER, config.IMAP_PORT)
        mail.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
        mail.select("INBOX")
        
        # Search for emails from the last 7 days
        date_since = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
        _, message_numbers = mail.search(None, f'SINCE {date_since}')
        
        if not message_numbers[0]:
            print("📭 No messages found in the last 7 days")
            return
        
        messages = message_numbers[0].split()
        print(f"📬 Found {len(messages)} messages in the last 7 days\n")
        
        session = SessionLocal()
        replies_found = 0
        emails_checked = []
        
        for num in messages:
            try:
                # Fetch email
                _, msg_data = mail.fetch(num, "(RFC822)")
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Get sender email
                from_header = email_message.get("From", "")
                sender_email = extract_email(from_header)
                subject = email_message.get("Subject", "")
                date = email_message.get("Date", "")
                
                # Skip if it's from us
                if sender_email == config.EMAIL_ADDRESS.lower():
                    continue
                
                # Track all unique emails we've seen
                if sender_email not in emails_checked:
                    emails_checked.append(sender_email)
                
                # Check if this email is in our leads
                lead = session.query(Lead).filter(Lead.email == sender_email).first()
                
                if lead:
                    print(f"✉️  From: {sender_email}")
                    print(f"   Subject: {subject}")
                    print(f"   Date: {date}")
                    print(f"   Current Status: {lead.status.value}")
                    
                    if lead.status != LeadStatus.REPLIED:
                        print(f"   🔄 Updating to REPLIED...")
                        lead.status = LeadStatus.REPLIED
                        session.commit()
                        
                        # Log event
                        log = Log(
                            email=sender_email,
                            event=f"Reply received from {sender_email}"
                        )
                        session.add(log)
                        session.commit()
                        
                        replies_found += 1
                        print(f"   ✅ Updated to REPLIED")
                    else:
                        print(f"   ℹ️  Already marked as REPLIED")
                    
                    print()
                
            except Exception as e:
                print(f"❌ Error processing message: {str(e)}")
        
        # Show emails that were NOT in database
        print("\n" + "=" * 60)
        print("📧 Emails found in inbox (not from you):")
        print("=" * 60)
        
        all_lead_emails = [lead.email for lead in session.query(Lead).all()]
        
        for email_addr in emails_checked:
            if email_addr in all_lead_emails:
                print(f"✅ {email_addr} - IN DATABASE")
            else:
                print(f"❌ {email_addr} - NOT IN DATABASE (won't be tracked)")
        
        session.close()
        mail.close()
        mail.logout()
        
        print("\n" + "=" * 60)
        print(f"✅ Check complete! Found {replies_found} new replies")
        
        if replies_found > 0:
            print("\n📅 Now sending calendar links to new replies...")
            reply_checker = ReplyChecker()
            reply_checker.check_replies()
        else:
            print("\n💡 TIP: If you expected replies but found 0:")
            print("   - Check the list above for emails NOT IN DATABASE")
            print("   - Those emails need to be uploaded via CSV first")
            print("   - Or they might be from different email addresses")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def list_all_leads():
    """List all leads in the database."""
    print("\n📋 Current Leads in Database:")
    print("=" * 60)
    
    session = SessionLocal()
    leads = session.query(Lead).all()
    
    if not leads:
        print("No leads found in database")
        return
    
    for lead in leads:
        print(f"Email: {lead.email}")
        print(f"Status: {lead.status.value}")
        print(f"Last Sent: {lead.last_sent_at}")
        print(f"Follow-ups: {lead.followup_count}")
        print("-" * 60)
    
    session.close()
    
    print(f"\nTotal: {len(leads)} leads")

if __name__ == "__main__":
    print("🚀 Manual Reply Checker")
    print()
    
    # List current leads
    list_all_leads()
    
    print()
    
    # Check for replies
    check_all_replies()
