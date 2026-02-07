"""IMAP reply detection and automatic calendar link response."""
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
from typing import Set

from backend.config import config
from backend.database import SessionLocal, Lead, LeadStatus, Log
from backend.email_sender import EmailSender


class ReplyChecker:
    """Check for email replies using IMAP."""
    
    def __init__(self):
        self.imap_server = config.IMAP_SERVER
        self.imap_port = config.IMAP_PORT
        self.email_address = config.EMAIL_ADDRESS
        self.email_password = config.EMAIL_PASSWORD
        self.calendar_link = config.CALENDAR_LINK
        self.email_sender = EmailSender()
        self.processed_message_ids: Set[str] = set()
    
    def check_replies(self):
        """Check for new replies and handle them."""
        try:
            # Connect to IMAP
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.email_password)
            mail.select("INBOX")
            
            # Search for emails from the last 7 days
            date_since = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
            _, message_numbers = mail.search(None, f'SINCE {date_since}')
            
            if not message_numbers[0]:
                print("📭 No new messages to check")
                return
            
            for num in message_numbers[0].split():
                self._process_email(mail, num)
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            print(f"❌ Error checking replies: {str(e)}")
    
    def _process_email(self, mail, message_number):
        """Process a single email message."""
        try:
            # Fetch email
            _, msg_data = mail.fetch(message_number, "(RFC822)")
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # Get message ID to avoid duplicates
            message_id = email_message.get("Message-ID", "")
            if message_id in self.processed_message_ids:
                return
            
            # Get sender email
            from_header = email_message.get("From", "")
            sender_email = self._extract_email(from_header)
            
            if not sender_email or sender_email == self.email_address:
                return
            
            # Check if this is a reply from a lead
            session = SessionLocal()
            try:
                lead = session.query(Lead).filter(
                    Lead.email == sender_email,
                    Lead.status == LeadStatus.SENT
                ).first()
                
                if lead:
                    print(f"📧 Reply detected from: {sender_email}")
                    
                    # Mark as replied
                    lead.status = LeadStatus.REPLIED
                    session.commit()
                    
                    # Log event
                    log = Log(
                        email=sender_email,
                        event=f"Reply received from {sender_email}"
                    )
                    session.add(log)
                    session.commit()
                    
                    # Send automatic calendar link
                    self._send_calendar_response(sender_email)
                    
                    # Mark message as processed
                    self.processed_message_ids.add(message_id)
                
            finally:
                session.close()
                
        except Exception as e:
            print(f"❌ Error processing email: {str(e)}")
    
    def _extract_email(self, from_header: str) -> str:
        """Extract email address from From header."""
        if "<" in from_header and ">" in from_header:
            start = from_header.index("<") + 1
            end = from_header.index(">")
            return from_header[start:end].strip().lower()
        return from_header.strip().lower()
    
    def _send_calendar_response(self, to_email: str):
        """Send automatic calendar link response."""
        subject = "Let's schedule a call!"
        body = f"""Hi,

Thanks for your reply! I'd love to connect with you.

Please book a time that works best for you here:
{self.calendar_link}

Looking forward to our conversation!

Best regards,
Your Team"""
        
        success = self.email_sender.send_email(to_email, subject, body)
        
        if success:
            print(f"✅ Sent calendar link to {to_email}")
            
            # Log the calendar send
            session = SessionLocal()
            try:
                log = Log(
                    email=to_email,
                    event=f"Sent calendar link to {to_email}"
                )
                session.add(log)
                session.commit()
            finally:
                session.close()
        else:
            print(f"❌ Failed to send calendar link to {to_email}")
    
    def test_connection(self) -> bool:
        """Test IMAP connection."""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.email_password)
            mail.logout()
            print("✅ IMAP connection test successful")
            return True
        except Exception as e:
            print(f"❌ IMAP connection test failed: {str(e)}")
            return False
