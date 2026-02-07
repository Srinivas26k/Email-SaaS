"""Background worker for email sending with crash recovery."""
import time
import json
from datetime import datetime, timedelta
from typing import Optional

from backend.config import config
from backend.database import SessionLocal, Lead, Campaign, Log, LeadStatus, CampaignStatus
from backend.email_sender import EmailSender
from backend.templates import render_template


class BackgroundWorker:
    """Background email sending loop with crash recovery."""
    
    def __init__(self):
        self.email_sender = EmailSender()
        self.running = False
    
    def start(self):
        """Start the background worker loop."""
        self.running = True
        print("🚀 Background worker started")
        
        while self.running:
            try:
                self._check_and_reset_daily_limit()
                self._process_pending_leads()
                
                # Sleep between iterations
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"❌ Error in background worker: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying
    
    def stop(self):
        """Stop the background worker."""
        self.running = False
        print("⏹️  Background worker stopped")
    
    def _check_and_reset_daily_limit(self):
        """Check if daily limit needs to be reset."""
        session = SessionLocal()
        try:
            campaign = session.query(Campaign).first()
            if not campaign:
                return
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Reset counter if it's a new day
            if campaign.last_reset_date != today:
                campaign.sent_today = 0
                campaign.last_reset_date = today
                session.commit()
                print(f"🔄 Daily email counter reset for {today}")
                
        finally:
            session.close()
    
    def _process_pending_leads(self):
        """Process pending leads and send emails."""
        session = SessionLocal()
        try:
            # Get campaign status
            campaign = session.query(Campaign).first()
            if not campaign:
                return
            
            # Check if campaign is running
            if campaign.status != CampaignStatus.RUNNING:
                return
            
            # Check daily limit
            if campaign.sent_today >= config.DAILY_EMAIL_LIMIT:
                print(f"⏸️  Daily limit reached ({campaign.sent_today}/{config.DAILY_EMAIL_LIMIT})")
                return
            
            # Get next lead to process
            lead = self._get_next_lead(session)
            
            if not lead:
                # No more leads, mark campaign as completed
                if campaign.status == CampaignStatus.RUNNING:
                    campaign.status = CampaignStatus.COMPLETED
                    session.commit()
                    print("✅ Campaign completed - no more leads to process")
                return
            
            # Send email to lead
            self._send_to_lead(session, lead, campaign)
            
        finally:
            session.close()
    
    def _get_next_lead(self, session) -> Optional[Lead]:
        """Get the next lead to send email to."""
        now = datetime.utcnow()
        
        # Priority 1: New leads (PENDING status)
        lead = session.query(Lead).filter(
            Lead.status == LeadStatus.PENDING
        ).first()
        
        if lead:
            return lead
        
        # Priority 2: Follow-ups (SENT status, 3+ days since last send, followup_count < 2)
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
            # Parse lead data
            lead_data = json.loads(lead.data_json) if lead.data_json else {}
            
            # Determine email type
            if lead.followup_count == 0:
                email_type = "initial"
            elif lead.followup_count == 1:
                email_type = "followup1"
            else:
                email_type = "followup2"
            
            # Get industry (default to healthcare if not specified)
            industry = lead_data.get("industry", "healthcare")
            
            # Prepare template variables
            variables = {
                "first_name": lead_data.get("first_name", "there"),
                "company": lead_data.get("company", "your company"),
                "industry": industry
            }
            
            # Render template
            rendered = render_template(industry, email_type, variables)
            
            # Send email
            success = self.email_sender.send_email(
                lead.email,
                rendered["subject"],
                rendered["body"]
            )
            
            if success:
                # Update lead
                lead.status = LeadStatus.SENT
                lead.last_sent_at = datetime.utcnow()
                lead.followup_count += 1
                
                # Update campaign
                campaign.sent_today += 1
                
                # Log success
                log = Log(
                    email=lead.email,
                    event=f"Sent {email_type} email to {lead.email}"
                )
                session.add(log)
                session.commit()
                
                print(f"✅ Sent {email_type} to {lead.email} ({campaign.sent_today}/{config.DAILY_EMAIL_LIMIT})")
                
            else:
                # Mark as failed
                lead.status = LeadStatus.FAILED
                
                # Log failure
                log = Log(
                    email=lead.email,
                    event=f"Failed to send email to {lead.email}"
                )
                session.add(log)
                session.commit()
                
                print(f"❌ Failed to send to {lead.email}")
                
        except Exception as e:
            print(f"❌ Error sending to {lead.email}: {str(e)}")
            
            # Log error
            log = Log(
                email=lead.email,
                event=f"Error sending to {lead.email}: {str(e)}"
            )
            session.add(log)
            session.commit()
