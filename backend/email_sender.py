"""Email sending with optional per-account credentials and rate limiting."""
import smtplib
import time
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Any, Tuple

from backend.settings_service import get_app_settings


class EmailSender:
    """Send email via SMTP using provided account or default config."""

    def __init__(self, account: Optional[Any] = None):
        """
        Args:
            account: Optional EmailAccount model instance (with email, password, smtp_server, smtp_port).
                     If None, uses first available account from DB or no-op.
        """
        self.account = account
        self.emails_sent_in_session = 0

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
        skip_rate_limit: bool = False,
    ) -> bool:
        """
        Send email via SMTP.
        skip_rate_limit: if True, do not apply delay after sending (use for reply/calendar link).
        """
        account = self._get_account()
        if not account:
            return False
        try:
            msg = MIMEMultipart()
            msg["From"] = account.email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html" if is_html else "plain"))

            with smtplib.SMTP(account.smtp_server, account.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(account.email, account.password)
                server.send_message(msg)

            self.emails_sent_in_session += 1
            if not is_html and not skip_rate_limit:
                self._apply_rate_limit()
            return True
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")
            return False

    def _get_account(self):
        if self.account:
            return self.account
        from backend.settings_service import get_email_accounts

        accounts = get_email_accounts(active_only=True)
        return accounts[0] if accounts else None

    def _apply_rate_limit(self):
        settings = get_app_settings()
        min_d = int(settings.get("min_delay_seconds", 60))
        max_d = int(settings.get("max_delay_seconds", 120))
        pause_n = int(settings.get("pause_every_n_emails", 20))
        pause_min = int(settings.get("pause_min_minutes", 5))
        pause_max = int(settings.get("pause_max_minutes", 8))
        delay = random.randint(min_d, max_d)
        time.sleep(delay)
        if pause_n and self.emails_sent_in_session % pause_n == 0:
            pause_minutes = random.randint(pause_min, pause_max)
            time.sleep(pause_minutes * 60)

    @staticmethod
    def test_connection(email: str, password: str, smtp_server: str, smtp_port: int) -> Tuple[bool, str]:
        from backend.settings_service import test_smtp_connection

        return test_smtp_connection(email, password, smtp_server, smtp_port)
