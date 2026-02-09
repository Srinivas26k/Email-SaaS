"""Settings and email accounts: DB-backed config for non-technical users."""
import os
import smtplib
import imaplib
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from backend.database import SessionLocal, AppSettings, EmailAccount
from backend.config import config as env_config

# Keys for app_settings table
KEYS = {
    "license_sheet_url": "",
    "license_key": "",
    "daily_email_limit": "500",
    "min_delay_seconds": "60",
    "max_delay_seconds": "120",
    "pause_every_n_emails": "20",
    "pause_min_minutes": "5",
    "pause_max_minutes": "8",
    "calendar_link": "https://calendly.com/your-link",
}


def _get_env_fallback(key: str) -> str:
    """Fallback to .env for server/deploy. Map our keys to env names."""
    env_map = {
        "license_sheet_url": "LICENSE_SHEET_URL",
        "license_key": "LICENSE_KEY",
        "daily_email_limit": "DAILY_EMAIL_LIMIT",
        "min_delay_seconds": "MIN_DELAY_SECONDS",
        "max_delay_seconds": "MAX_DELAY_SECONDS",
        "pause_every_n_emails": "PAUSE_EVERY_N_EMAILS",
        "pause_min_minutes": "PAUSE_MIN_MINUTES",
        "pause_max_minutes": "PAUSE_MAX_MINUTES",
        "calendar_link": "CALENDAR_LINK",
    }
    env_name = env_map.get(key)
    if env_name:
        val = os.getenv(env_name)
        if val is not None:
            return val
    return KEYS.get(key, "")


def get_app_settings() -> Dict[str, str]:
    """Get all app settings from DB with fallback to env then defaults."""
    session = SessionLocal()
    try:
        rows = session.query(AppSettings).all()
        db_map = {r.key: (r.value or "") for r in rows}
        out = {}
        for key, default in KEYS.items():
            out[key] = db_map.get(key) if key in db_map else _get_env_fallback(key) or default
        return out
    finally:
        session.close()


def save_app_settings(settings: Dict[str, str]) -> None:
    """Save app settings to DB."""
    session = SessionLocal()
    try:
        for key, value in settings.items():
            if key not in KEYS:
                continue
            row = session.query(AppSettings).filter(AppSettings.key == key).first()
            if row:
                row.value = (value or "").strip()
            else:
                session.add(AppSettings(key=key, value=(value or "").strip()))
        session.commit()
    finally:
        session.close()


def get_email_accounts(active_only: bool = True) -> List[EmailAccount]:
    """Get email accounts from DB, optionally only active."""
    session = SessionLocal()
    try:
        q = session.query(EmailAccount).order_by(EmailAccount.id)
        if active_only:
            q = q.filter(EmailAccount.is_active == 1)
        return q.all()
    finally:
        session.close()


def get_email_account_by_id(account_id: int) -> Optional[EmailAccount]:
    """Get a single email account."""
    session = SessionLocal()
    try:
        return session.query(EmailAccount).filter(EmailAccount.id == account_id).first()
    finally:
        session.close()


def create_email_account(
    label: str,
    email: str,
    password: str,
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 587,
    imap_server: str = "imap.gmail.com",
    imap_port: int = 993,
) -> EmailAccount:
    """Create a new email account."""
    session = SessionLocal()
    try:
        acc = EmailAccount(
            label=label.strip(),
            email=email.strip().lower(),
            password=password,
            smtp_server=(smtp_server or "smtp.gmail.com").strip(),
            smtp_port=int(smtp_port or 587),
            imap_server=(imap_server or "imap.gmail.com").strip(),
            imap_port=int(imap_port or 993),
            is_active=1,
        )
        session.add(acc)
        session.commit()
        session.refresh(acc)
        return acc
    finally:
        session.close()


def update_email_account(
    account_id: int,
    label: Optional[str] = None,
    email: Optional[str] = None,
    password: Optional[str] = None,
    smtp_server: Optional[str] = None,
    smtp_port: Optional[int] = None,
    imap_server: Optional[str] = None,
    imap_port: Optional[int] = None,
    is_active: Optional[int] = None,
) -> Optional[EmailAccount]:
    """Update an email account."""
    session = SessionLocal()
    try:
        acc = session.query(EmailAccount).filter(EmailAccount.id == account_id).first()
        if not acc:
            return None
        if label is not None:
            acc.label = label.strip()
        if email is not None:
            acc.email = email.strip().lower()
        if password is not None and password != "":
            acc.password = password
        if smtp_server is not None:
            acc.smtp_server = smtp_server.strip()
        if smtp_port is not None:
            acc.smtp_port = int(smtp_port)
        if imap_server is not None:
            acc.imap_server = imap_server.strip()
        if imap_port is not None:
            acc.imap_port = int(imap_port)
        if is_active is not None:
            acc.is_active = int(is_active)
        session.commit()
        session.refresh(acc)
        return acc
    finally:
        session.close()


def delete_email_account(account_id: int) -> bool:
    """Delete an email account."""
    session = SessionLocal()
    try:
        acc = session.query(EmailAccount).filter(EmailAccount.id == account_id).first()
        if not acc:
            return False
        session.delete(acc)
        session.commit()
        return True
    finally:
        session.close()


def test_smtp_connection(
    email: str,
    password: str,
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 587,
) -> Tuple[bool, str]:
    """Test SMTP connection. Returns (success, message)."""
    try:
        with smtplib.SMTP(str(smtp_server).strip(), int(smtp_port), timeout=10) as server:
            server.starttls()
            server.login(email.strip(), password)
        return True, "Connected successfully"
    except smtplib.SMTPAuthenticationError as e:
        return False, f"Invalid credentials: {str(e)}"
    except Exception as e:
        return False, str(e)


def test_imap_connection(
    email: str,
    password: str,
    imap_server: str = "imap.gmail.com",
    imap_port: int = 993,
) -> Tuple[bool, str]:
    """Test IMAP connection. Returns (success, message)."""
    try:
        mail = imaplib.IMAP4_SSL(str(imap_server).strip(), int(imap_port), timeout=10)
        mail.login(email.strip(), password)
        mail.logout()
        return True, "Connected successfully"
    except Exception as e:
        return False, str(e)


def get_next_sending_account():
    """Return the email account to use for the next send (round-robin by sent_today)."""
    accounts = get_email_accounts(active_only=True)
    if not accounts:
        return None
    # Use account with smallest sent_today for even distribution
    return min(accounts, key=lambda a: a.sent_today)


def increment_account_sent_today(account_id: int) -> None:
    """Increment sent_today for an account (call after successful send)."""
    session = SessionLocal()
    try:
        acc = session.query(EmailAccount).filter(EmailAccount.id == account_id).first()
        if acc:
            acc.sent_today = (acc.sent_today or 0) + 1
            session.commit()
    finally:
        session.close()


def reset_all_accounts_sent_today() -> None:
    """Reset sent_today for all accounts (call at daily reset)."""
    session = SessionLocal()
    try:
        session.query(EmailAccount).update({EmailAccount.sent_today: 0})
        session.commit()
    finally:
        session.close()
