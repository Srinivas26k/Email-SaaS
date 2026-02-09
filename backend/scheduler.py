"""Background scheduler for 24/7 email operations with multi-account support."""
import logging
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.database import SessionLocal, Lead, Campaign, Log, LeadStatus, CampaignStatus
from backend.email_sender import EmailSender
from backend.reply_checker import ReplyChecker
from backend.daily_report import DailyReportGenerator
from backend.template_renderer import render_custom_template
from backend.settings_service import (
    get_app_settings,
    get_next_sending_account,
    increment_account_sent_today,
    reset_all_accounts_sent_today,
)

import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailScheduler:
    """Handles all background tasks with proper scheduling."""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.reply_checker = ReplyChecker()
        self.running = False

    def start(self):
        if self.running:
            logger.warning("Scheduler already running")
            return
        settings = get_app_settings()
        queue_sec = max(30, int(settings.get("email_queue_interval_seconds", "300") or 300))
        reply_sec = max(60, int(settings.get("reply_check_interval_seconds", "300") or 300))
        logger.info("Email queue every %s s, reply check every %s s", queue_sec, reply_sec)
        self.scheduler.add_job(
            func=self.process_email_queue,
            trigger=IntervalTrigger(seconds=queue_sec),
            id="email_sender",
            name="Process email queue",
            replace_existing=True,
        )
        self.scheduler.add_job(
            func=self.check_for_replies,
            trigger=IntervalTrigger(seconds=reply_sec),
            id="reply_checker",
            name="Check for email replies",
            replace_existing=True,
        )
        self.scheduler.add_job(
            func=self.reset_daily_counter,
            trigger="cron",
            hour=0,
            minute=0,
            id="daily_reset",
            name="Reset daily email counter",
            replace_existing=True,
        )
        self.scheduler.add_job(
            func=self.send_daily_report,
            trigger="cron",
            hour=1,
            minute=0,
            id="daily_report",
            name="Send daily analytics report",
            replace_existing=True,
        )
        self.scheduler.start()
        self.running = True
        logger.info("Scheduler started - email queue and reply checker active")

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            self.running = False
        logger.info("Scheduler stopped")

    def process_email_queue(self):
        session = SessionLocal()
        try:
            campaign = session.query(Campaign).first()
            if not campaign or campaign.status != CampaignStatus.RUNNING:
                logger.info("Email queue: campaign not running, skipping")
                return
            settings = get_app_settings()
            daily_limit = int(settings.get("daily_email_limit", "500"))
            if campaign.sent_today >= daily_limit:
                logger.info("Email queue: daily limit reached (%s/%s), skipping", campaign.sent_today, daily_limit)
                return

            account = get_next_sending_account()
            if not account:
                logger.warning("No email account configured. Add one in Settings, or set EMAIL_ADDRESS and EMAIL_PASSWORD in .env")
                return

            lead = self._get_next_lead(session)
            if not lead:
                logger.info("Email queue: no pending lead, skipping")
                return

            self._send_to_lead(session, lead, campaign, account)
        except Exception as e:
            logger.error("Error in email queue: %s", e, exc_info=True)
        finally:
            session.close()

    def check_for_replies(self):
        try:
            logger.info("Reply check job ran")
            self.reply_checker.check_replies()
        except Exception as e:
            logger.error("Error checking replies: %s", e, exc_info=True)

    def send_daily_report(self):
        try:
            gen = DailyReportGenerator()
            gen.send_daily_report()
        except Exception as e:
            logger.error("Error sending daily report: %s", e, exc_info=True)

    def reset_daily_counter(self):
        session = SessionLocal()
        try:
            campaign = session.query(Campaign).first()
            if campaign:
                today = datetime.now().strftime("%Y-%m-%d")
                campaign.sent_today = 0
                campaign.last_reset_date = today
                session.commit()
            reset_all_accounts_sent_today()
        except Exception as e:
            logger.error("Error resetting counter: %s", e)
        finally:
            session.close()

    def _get_next_lead(self, session) -> Optional[Lead]:
        now = datetime.utcnow()
        lead = (
            session.query(Lead)
            .filter(Lead.status == LeadStatus.PENDING)
            .first()
        )
        if lead:
            return lead
        followup_cutoff = now - timedelta(days=3)
        lead = (
            session.query(Lead)
            .filter(
                Lead.status == LeadStatus.SENT,
                Lead.followup_count < 2,
                Lead.last_sent_at <= followup_cutoff,
            )
            .first()
        )
        return lead

    def _send_to_lead(self, session, lead: Lead, campaign: Campaign, account):
        try:
            lead_data = json.loads(lead.data_json) if lead.data_json else {}
            if lead.followup_count == 0:
                template_type = "initial"
            elif lead.followup_count == 1:
                template_type = "followup1"
            else:
                template_type = "followup2"

            from backend.database import CustomTemplate

            custom_template = (
                session.query(CustomTemplate)
                .filter(CustomTemplate.template_type == template_type)
                .first()
            )
            if custom_template:
                rendered = render_custom_template(
                    custom_template.subject, custom_template.body, lead_data
                )
            else:
                from backend.templates import render_template

                industry = lead_data.get("industry", "healthcare")
                rendered = render_template(
                    industry,
                    template_type,
                    {
                        "first_name": lead_data.get("first_name", "there"),
                        "company": lead_data.get("company", "your company"),
                        "industry": industry,
                    },
                )

            sender = EmailSender(account=account)
            success = sender.send_email(
                lead.email, rendered["subject"], rendered["body"]
            )
            if success:
                lead.status = LeadStatus.SENT
                lead.last_sent_at = datetime.utcnow()
                lead.followup_count += 1
                lead.email_account_id = account.id
                campaign.sent_today += 1
                session.add(
                    Log(
                        email=lead.email,
                        event=f"Sent {template_type} to {lead.email}",
                    )
                )
                session.commit()
                acc_id = getattr(account, "id", None)
                increment_account_sent_today(acc_id)
                settings = get_app_settings()
                daily_limit = int(settings.get("daily_email_limit", "500"))
                logger.info(
                    "Sent %s to %s (%s/%s)",
                    template_type,
                    lead.email,
                    campaign.sent_today,
                    daily_limit,
                )
            else:
                lead.status = LeadStatus.FAILED
                session.add(
                    Log(email=lead.email, event=f"Failed to send to {lead.email}")
                )
                session.commit()
        except Exception as e:
            logger.error("Error sending to %s: %s", lead.email, e)


email_scheduler = EmailScheduler()
