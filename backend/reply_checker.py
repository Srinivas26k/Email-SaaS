"""IMAP reply detection and automatic calendar link response for all accounts."""
import imaplib
import email
import logging
from datetime import datetime, timedelta
from typing import Set

from sqlalchemy import func
from backend.database import SessionLocal, Lead, LeadStatus, Log
from backend.settings_service import get_email_accounts, get_app_settings
from backend.email_sender import EmailSender

logger = logging.getLogger(__name__)


class ReplyChecker:
    """Check for email replies across all configured IMAP accounts."""

    def __init__(self):
        self.processed_message_ids: Set[str] = set()

    def check_replies(self):
        """Check each active account's INBOX for replies from leads."""
        accounts = get_email_accounts(active_only=True)
        if not accounts:
            logger.warning("Reply check: no email accounts (add one in Settings or set .env)")
            return
        logger.info("Checking for replies (%s account(s))...", len(accounts))
        for acc in accounts:
            try:
                self._check_account(acc)
            except Exception as e:
                logger.exception("Error checking replies for %s: %s", getattr(acc, "email", "?"), e)

    def _check_account(self, acc):
        acc_label = getattr(acc, "label", None) or getattr(acc, "email", "?")
        logger.info("Reply check: checking INBOX for account %s", acc_label)
        mail = imaplib.IMAP4_SSL(acc.imap_server, acc.imap_port, timeout=30)
        mail.login(acc.email, acc.password)
        mail.select("INBOX")
        date_since = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
        _, message_numbers = mail.search(None, f"SINCE {date_since}")
        ids = (message_numbers[0] or b"").split()
        if not ids:
            mail.close()
            mail.logout()
            logger.info("Reply check: no messages in INBOX for %s", acc_label)
            return
        logger.info("Reply check: scanning %s message(s) for %s", len(ids), acc_label)
        for num in ids:
            self._process_email(mail, num, acc)
        mail.close()
        mail.logout()

    def _process_email(self, mail, message_number, acc):
        try:
            _, msg_data = mail.fetch(message_number, "(RFC822)")
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            message_id = email_message.get("Message-ID", "")
            if message_id in self.processed_message_ids:
                return
            from_header = email_message.get("From", "")
            sender_email = self._extract_email(from_header)
            if not sender_email or sender_email == acc.email:
                return

            session = SessionLocal()
            try:
                lead = session.query(Lead).filter(func.lower(Lead.email) == sender_email).first()
                if not lead:
                    return
                if lead.status == LeadStatus.REPLIED:
                    return
                # Mark as replied and associate with this account if not set
                lead.status = LeadStatus.REPLIED
                if lead.email_account_id is None:
                    lead.email_account_id = acc.id
                session.commit()
                session.add(
                    Log(email=sender_email, event=f"Reply received from {sender_email}")
                )
                session.commit()
                self.processed_message_ids.add(message_id)
                logger.info("Reply detected from %s, sending calendar link", sender_email)
                self._send_calendar_response(sender_email, acc)
            finally:
                session.close()
        except Exception as e:
            logger.exception("Error processing message: %s", e)

    @staticmethod
    def _extract_email(from_header: str) -> str:
        if "<" in from_header and ">" in from_header:
            start = from_header.index("<") + 1
            end = from_header.index(">")
            return from_header[start:end].strip().lower()
        return from_header.strip().lower()

    def _send_calendar_response(self, to_email: str, acc):
        """Send calendar link from the same account that received the reply."""
        session = SessionLocal()
        try:
            lead = session.query(Lead).filter(Lead.email == to_email).first()
            lead_data = {}
            if lead and lead.data_json:
                import json
                lead_data = json.loads(lead.data_json)
            settings = get_app_settings()
            calendar_link = settings.get("calendar_link", "https://calendly.com/your-link")
            from backend.database import CustomTemplate

            reply_template = (
                session.query(CustomTemplate)
                .filter(CustomTemplate.template_type == "reply")
                .first()
            )
            if reply_template:
                subject = reply_template.subject
                body = reply_template.body
            else:
                subject = "Let's schedule a call!"
                body = """Hi {{first_name}},

Thanks for your reply! I'd love to connect with you.

Please book a time that works best for you here:
{{calendar_link}}

Looking forward to our conversation!

Best regards"""
            lead_data["calendar_link"] = calendar_link
            lead_data["email"] = to_email
            for key, value in lead_data.items():
                subject = subject.replace(f"{{{{{key}}}}}", str(value))
                body = body.replace(f"{{{{{key}}}}}", str(value))

            sender = EmailSender(account=acc)
            # skip_rate_limit so reply flow does not block for 60-120s (calendar link is a single reply)
            success = sender.send_email(to_email, subject, body, skip_rate_limit=True)
            if success:
                logger.info("Sent calendar link to %s", to_email)
                session.add(Log(email=to_email, event=f"Sent calendar link to {to_email}"))
                session.commit()
            else:
                logger.warning("Failed to send calendar link to %s", to_email)
        finally:
            session.close()

    @staticmethod
    def test_connection(email_addr: str, password: str, imap_server: str, imap_port: int) -> tuple:
        from backend.settings_service import test_imap_connection

        return test_imap_connection(email_addr, password, imap_server, imap_port)
