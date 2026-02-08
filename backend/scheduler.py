"""Production-ready background scheduler for 24/7 email operations."""
import time
import logging
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.config import config
from backend.database import SessionLocal, Lead, Campaign, Log, LeadStatus, CampaignStatus
from backend.email_sender import EmailSender
from backend.reply_checker import ReplyChecker
from backend.template_renderer import render_custom_template
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailScheduler:
    """Handles all background tasks with proper scheduling."""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.email_sender = EmailSender()
        self.reply_checker = ReplyChecker()
        self.running = False
    
    def start(self):
        """Start all scheduled tasks."""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        # Task 1: Send emails every 30 seconds
        self.scheduler.add_job(
            func=self.process_email_queue,
            trigger=IntervalTrigger(seconds=30),
            id='email_sender',
            name='Process email queue',
            replace_existing=True
        )
        
        # Task 2: Check replies every 5 minutes
        self.scheduler.add_job(
            func=self.check_for_replies,
            trigger=IntervalTrigger(minutes=5),
            id='reply_checker',
            name='Check for email replies',
            replace_existing=True
        )
        
        # Task 3: Reset daily counter at midnight
        self.scheduler.add_job(
            func=self.reset_daily_counter,
            trigger='cron',
            hour=0,
            minute=0,
            id='daily_reset',
            name='Reset daily email counter',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.running = True
        logger.info("🚀 Scheduler started - all background tasks active")
    
    def stop(self):
        """Stop all scheduled tasks."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            self.running = False
            logger.info("⏹️ Scheduler stopped")
    
    def process_email_queue(self):
        """Process pending emails (runs every 30 seconds)."""
        session = SessionLocal()
        try:
            # Get campaign
            campaign = session.query(Campaign).first()
            if not campaign or campaign.status != CampaignStatus.RUNNING:
                return
            
            # Check daily limit
            if campaign.sent_today >= config.DAILY_EMAIL_LIMIT:
                logger.info(f"⏸️ Daily limit reached ({campaign.sent_today}/{config.DAILY_EMAIL_LIMIT})")
                return
            
            # Get next lead
            lead = self._get_next_lead(session)
            if not lead:
                return
            
            # Send email
            self._send_to_lead(session, lead, campaign)
            
        except Exception as e:
            logger.error(f"❌ Error in email queue: {str(e)}", exc_info=True)
        finally:
            session.close()
    
    def check_for_replies(self):
        """Check for email replies (runs every 5 minutes)."""
        try:
            logger.info("📬 Checking for replies...")
            self.reply_checker.check_replies()
        except Exception as e:
            logger.error(f"❌ Error checking replies: {str(e)}", exc_info=True)
    
    def reset_daily_counter(self):
        """Reset daily email counter at midnight."""
        session = SessionLocal()
        try:
            campaign = session.query(Campaign).first()
            if campaign:
                today = datetime.now().strftime("%Y-%m-%d")
                campaign.sent_today = 0
                campaign.last_reset_date = today
                session.commit()
                logger.info(f"🔄 Daily counter reset for {today}")
        except Exception as e:
            logger.error(f"❌ Error resetting counter: {str(e)}")
        finally:
            session.close()
    
    def _get_next_lead(self, session) -> Optional[Lead]:
        """Get the next lead to send email to."""
        now = datetime.utcnow()
        
        # Priority 1: New leads
        lead = session.query(Lead).filter(
            Lead.status == LeadStatus.PENDING
        ).first()
        
        if lead:
            return lead
        
        # Priority 2: Follow-ups (3+ days since last send)
        followup_cutoff = now - timedelta(days=3)
        lead = session.query(Lead).filter(
            Lead.status == LeadStatus.SENT,
            Lead.followup_count < 2,
            Lead.last_sent_at <= followup_cutoff
        ).first()
        
        return lead
    
    def _send_to_lead(self, session, lead: Lead, campaign: Campaign):
        """Send email to a specific lead."""
        try:
            lead_data = json.loads(lead.data_json) if lead.data_json else {}
            
            # Determine template type
            if lead.followup_count == 0:
                template_type = "initial"
            elif lead.followup_count == 1:
                template_type = "followup1"
            else:
                template_type = "followup2"
            
            # Get custom template
            from backend.database import CustomTemplate
            custom_template = session.query(CustomTemplate).filter(
                CustomTemplate.template_type == template_type
            ).first()
            
            if custom_template:
                rendered = render_custom_template(
                    custom_template.subject,
                    custom_template.body,
                    lead_data
                )
            else:
                # Fallback
                from backend.templates import render_template
                industry = lead_data.get("industry", "healthcare")
                variables = {
                    "first_name": lead_data.get("first_name", "there"),
                    "company": lead_data.get("company", "your company"),
                    "industry": industry
                }
                rendered = render_template(industry, template_type, variables)
            
            # Send email
            success = self.email_sender.send_email(
                lead.email,
                rendered["subject"],
                rendered["body"]
            )
            
            if success:
                lead.status = LeadStatus.SENT
                lead.last_sent_at = datetime.utcnow()
                lead.followup_count += 1
                campaign.sent_today += 1
                
                log = Log(
                    email=lead.email,
                    event=f"Sent {template_type} email to {lead.email}"
                )
                session.add(log)
                session.commit()
                
                logger.info(f"✅ Sent {template_type} to {lead.email} ({campaign.sent_today}/{config.DAILY_EMAIL_LIMIT})")
            else:
                lead.status = LeadStatus.FAILED
                log = Log(
                    email=lead.email,
                    event=f"Failed to send email to {lead.email}"
                )
                session.add(log)
                session.commit()
                
        except Exception as e:
            logger.error(f"❌ Error sending to {lead.email}: {str(e)}")


# Global scheduler instance
email_scheduler = EmailScheduler()