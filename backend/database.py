"""Database models and initialization."""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Enum, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import enum

from backend.config import config

Base = declarative_base()


class LeadStatus(enum.Enum):
    """Lead status enum."""
    PENDING = "PENDING"
    SENT = "SENT"
    REPLIED = "REPLIED"
    FAILED = "FAILED"


class CampaignStatus(enum.Enum):
    """Campaign status enum."""
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class Lead(Base):
    """Lead model."""
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    data_json = Column(Text, nullable=True)  # JSON string with first_name, company, industry, etc.
    status = Column(Enum(LeadStatus), default=LeadStatus.PENDING, nullable=False)
    last_sent_at = Column(DateTime, nullable=True)
    followup_count = Column(Integer, default=0, nullable=False)
    email_account_id = Column(Integer, nullable=True, index=True)  # which account sent to this lead
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Campaign(Base):
    """Campaign model."""
    __tablename__ = "campaign"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.STOPPED, nullable=False)
    sent_today = Column(Integer, default=0, nullable=False)
    last_reset_date = Column(String(10), nullable=True)  # Format: YYYY-MM-DD
    available_columns = Column(Text, nullable=True)  # JSON string of CSV columns
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class CustomTemplate(Base):
    """Custom email template model."""
    __tablename__ = "custom_templates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    template_type = Column(String(20), nullable=False)  # initial, followup1, followup2, reply
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Log(Base):
    """Log model."""
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=True)
    event = Column(String(500), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


class AppSettings(Base):
    """Application settings (UI-configurable, no .env required)."""
    __tablename__ = "app_settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class EmailAccount(Base):
    """SMTP/IMAP account for sending and receiving."""
    __tablename__ = "email_accounts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String(120), nullable=False)  # e.g. "Sales Gmail"
    email = Column(String(255), nullable=False)
    password = Column(String(500), nullable=False)  # app password
    smtp_server = Column(String(255), nullable=False, default="smtp.gmail.com")
    smtp_port = Column(Integer, nullable=False, default=587)
    imap_server = Column(String(255), nullable=False, default="imap.gmail.com")
    imap_port = Column(Integer, nullable=False, default=993)
    is_active = Column(Integer, nullable=False, default=1)  # 1=active, 0=disabled
    sent_today = Column(Integer, nullable=False, default=0)  # for round-robin distribution
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# Database engine and session
engine = create_engine(
    config.DATABASE_URL.replace("sqlite:///", "sqlite:///"),
    connect_args={"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {},
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections every hour
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables with migrations."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    try:
        # Create initial campaign if doesn't exist
        campaign = session.query(Campaign).first()
        if not campaign:
            campaign = Campaign(status=CampaignStatus.STOPPED, sent_today=0)
            session.add(campaign)
            session.commit()
            print("✅ Created initial campaign")
    finally:
        session.close()
    
    # Migration: add email_account_id to leads if missing
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('leads')]
        
        if 'email_account_id' not in columns:
            from sqlalchemy import text
            with engine.connect() as conn:
                # PostgreSQL and SQLite compatible ALTER TABLE
                conn.execute(text("ALTER TABLE leads ADD COLUMN email_account_id INTEGER"))
                conn.commit()
            print("✅ Added email_account_id column to leads table")
    except Exception as e:
        # Column already exists or other minor issue - safe to continue
        print(f"ℹ️  Migration note: {e}")


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()