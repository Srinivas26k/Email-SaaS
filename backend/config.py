"""Configuration management for email outreach system."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration."""
    
    # License Configuration
    LICENSE_SHEET_URL = os.getenv("LICENSE_SHEET_URL", "")
    LICENSE_KEY = os.getenv("LICENSE_KEY", "")
    
    # Email Configuration
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    
    # SMTP Configuration
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    
    # IMAP Configuration
    IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
    IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
    
    # Sending Limits
    DAILY_EMAIL_LIMIT = int(os.getenv("DAILY_EMAIL_LIMIT", "500"))
    MIN_DELAY_SECONDS = int(os.getenv("MIN_DELAY_SECONDS", "60"))
    MAX_DELAY_SECONDS = int(os.getenv("MAX_DELAY_SECONDS", "120"))
    PAUSE_EVERY_N_EMAILS = int(os.getenv("PAUSE_EVERY_N_EMAILS", "20"))
    PAUSE_MIN_MINUTES = int(os.getenv("PAUSE_MIN_MINUTES", "5"))
    PAUSE_MAX_MINUTES = int(os.getenv("PAUSE_MAX_MINUTES", "8"))
    
    # Calendar Link
    CALENDAR_LINK = os.getenv("CALENDAR_LINK", "https://calendly.com/your-link")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./email_system.db")
    
    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        required_fields = [
            "LICENSE_SHEET_URL",
            "LICENSE_KEY",
            "EMAIL_ADDRESS",
            "EMAIL_PASSWORD",
        ]
        
        missing = [field for field in required_fields if not getattr(cls, field)]
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")


config = Config()
