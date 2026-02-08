"""Email sending functionality with SMTP."""
import smtplib
import time
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict

from backend.config import config


class EmailSender:
    """Email sender with rate limiting."""
    
    def __init__(self):
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
        self.email_address = config.EMAIL_ADDRESS
        self.email_password = config.EMAIL_PASSWORD
        self.emails_sent_in_session = 0
    
    def send_email(self, to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """
        Send email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text or HTML)
            is_html: If True, send as HTML email
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach body as plain text or HTML
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Connect and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
            
            self.emails_sent_in_session += 1
            
            # Apply delay based on rate limiting rules (skip for reports)
            if not is_html:  # Don't delay for HTML reports
                self._apply_rate_limit()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False
    
    def _apply_rate_limit(self):
        """Apply rate limiting delays."""
        # Random delay between emails
        delay = random.randint(config.MIN_DELAY_SECONDS, config.MAX_DELAY_SECONDS)
        print(f"⏱️  Waiting {delay} seconds before next email...")
        time.sleep(delay)
        
        # Longer pause every N emails
        if self.emails_sent_in_session % config.PAUSE_EVERY_N_EMAILS == 0:
            pause_minutes = random.randint(
                config.PAUSE_MIN_MINUTES, 
                config.PAUSE_MAX_MINUTES
            )
            pause_seconds = pause_minutes * 60
            print(f"⏸️  Pausing for {pause_minutes} minutes after {self.emails_sent_in_session} emails...")
            time.sleep(pause_seconds)
    
    def test_connection(self) -> bool:
        """Test SMTP connection."""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
            print("✅ SMTP connection test successful")
            return True
        except Exception as e:
            print(f"❌ SMTP connection test failed: {str(e)}")
            return False
