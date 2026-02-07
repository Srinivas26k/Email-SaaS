"""Database models and initialization."""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Enum
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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Campaign(Base):
    """Campaign model."""
    __tablename__ = "campaign"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.STOPPED, nullable=False)
    sent_today = Column(Integer, default=0, nullable=False)
    last_reset_date = Column(String(10), nullable=True)  # Format: YYYY-MM-DD
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Log(Base):
    """Log model."""
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=True)
    event = Column(String(500), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


# Database engine and session
engine = create_engine(
    config.DATABASE_URL.replace("sqlite:///", "sqlite:///"),
    connect_args={"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    
    # Create initial campaign if doesn't exist
    session = SessionLocal()
    try:
        campaign = session.query(Campaign).first()
        if not campaign:
            campaign = Campaign(status=CampaignStatus.STOPPED, sent_today=0)
            session.add(campaign)
            session.commit()
    finally:
        session.close()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
