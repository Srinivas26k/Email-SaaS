"""FastAPI main application with APScheduler for 24/7 parallel processing."""
import json
import pandas as pd
from io import StringIO
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.config import config
from backend.database import init_db, get_db, Lead, Campaign, Log, LeadStatus, CampaignStatus
from backend.settings_service import (
    get_app_settings,
    save_app_settings,
    get_email_accounts,
    get_email_accounts_db_only,
    get_env_fallback_account,
    create_email_account,
    update_email_account,
    delete_email_account,
    test_smtp_connection,
    test_imap_connection,
)
from backend.license_validator import validate_on_startup
from backend.scheduler import email_scheduler

# Initialize FastAPI app
app = FastAPI(title="Email Outreach System", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    print("Starting Email Outreach System...")
    validate_on_startup()
    init_db()
    print("Database initialized")
    email_scheduler.start()
    print("Scheduler started (email queue + reply checker)")
    print("System ready.")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    print("Shutting down...")
    email_scheduler.stop()
    print("Scheduler stopped.")


# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "scheduler_running": email_scheduler.running,
        "scheduler_jobs": len(email_scheduler.scheduler.get_jobs()) if email_scheduler.running else 0,
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== API ENDPOINTS ====================

@app.post("/api/upload-leads")
async def upload_leads(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload leads CSV with deduplication."""
    try:
        print(f"📤 Received file upload: {file.filename}, content_type: {file.content_type}")
        
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        # Read CSV
        contents = await file.read()
        print(f"📊 File size: {len(contents)} bytes")
        
        df = pd.read_csv(StringIO(contents.decode('utf-8', errors='replace')))
        
        # Validate required column
        if 'email' not in df.columns:
            raise HTTPException(status_code=400, detail="CSV must contain 'email' column")
        
        # Store available columns in campaign
        available_columns = df.columns.tolist()
        campaign = db.query(Campaign).first()
        if campaign:
            campaign.available_columns = json.dumps(available_columns)
            db.commit()
        
        # Process leads
        added_count = 0
        duplicate_count = 0
        
        for _, row in df.iterrows():
            email = str(row['email']).strip().lower()
            
            if not email or '@' not in email:
                continue
            
            # Check if lead already exists
            existing = db.query(Lead).filter(Lead.email == email).first()
            if existing:
                duplicate_count += 1
                continue
            
            # Store ALL columns from CSV as lead data
            lead_data = {col: str(row[col]) if pd.notna(row[col]) else '' for col in df.columns if col != 'email'}
            
            # Create new lead
            lead = Lead(
                email=email,
                data_json=json.dumps(lead_data),
                status=LeadStatus.PENDING
            )
            db.add(lead)
            added_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "added": added_count,
            "duplicates": duplicate_count,
            "columns": available_columns,
            "message": f"Added {added_count} leads, skipped {duplicate_count} duplicates"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/campaign/start")
async def start_campaign(db: Session = Depends(get_db)):
    """Start the campaign."""
    campaign = db.query(Campaign).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign.status = CampaignStatus.RUNNING
    db.commit()
    
    # Log event
    log = Log(email=None, event="Campaign started")
    db.add(log)
    db.commit()
    
    return {"success": True, "message": "Campaign started"}


@app.post("/api/campaign/pause")
async def pause_campaign(db: Session = Depends(get_db)):
    """Pause the campaign."""
    campaign = db.query(Campaign).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign.status = CampaignStatus.PAUSED
    db.commit()
    
    # Log event
    log = Log(email=None, event="Campaign paused")
    db.add(log)
    db.commit()
    
    return {"success": True, "message": "Campaign paused"}


@app.post("/api/campaign/stop")
async def stop_campaign(db: Session = Depends(get_db)):
    """Stop the campaign."""
    campaign = db.query(Campaign).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign.status = CampaignStatus.STOPPED
    db.commit()
    
    # Log event
    log = Log(email=None, event="Campaign stopped")
    db.add(log)
    db.commit()
    
    return {"success": True, "message": "Campaign stopped"}


@app.get("/api/metrics")
async def get_metrics(db: Session = Depends(get_db)):
    """Get current metrics."""
    campaign = db.query(Campaign).first()
    
    # Count leads by status
    total_leads = db.query(Lead).count()
    sent_count = db.query(Lead).filter(Lead.status == LeadStatus.SENT).count()
    replied_count = db.query(Lead).filter(Lead.status == LeadStatus.REPLIED).count()
    failed_count = db.query(Lead).filter(Lead.status == LeadStatus.FAILED).count()
    pending_count = db.query(Lead).filter(Lead.status == LeadStatus.PENDING).count()
    
    settings = get_app_settings()
    daily_limit = int(settings.get("daily_email_limit", "500"))
    return {
        "sent_today": campaign.sent_today if campaign else 0,
        "daily_limit": daily_limit,
        "replies": replied_count,
        "failed": failed_count,
        "total_leads": total_leads,
        "pending_leads": pending_count,
        "sent_leads": sent_count,
        "campaign_status": campaign.status.value if campaign else "STOPPED"
    }


@app.get("/api/logs")
async def get_logs(
    page: int = 1,
    limit: int = 50,
    search: str = None,
    db: Session = Depends(get_db)
):
    """Get logs with pagination and optional search."""
    query = db.query(Log).order_by(Log.timestamp.desc())
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(or_(Log.event.like(term), Log.email.like(term)))
    total = query.count()
    offset = (page - 1) * limit
    logs = query.offset(offset).limit(limit).all()
    return {
        "logs": [
            {
                "id": log.id,
                "email": log.email or "",
                "event": log.event,
                "timestamp": log.timestamp.isoformat()
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit if total else 1,
        "limit": limit
    }


@app.get("/api/campaign/status")
async def get_campaign_status(db: Session = Depends(get_db)):
    """Get campaign status."""
    campaign = db.query(Campaign).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return {
        "status": campaign.status.value,
        "sent_today": campaign.sent_today,
        "last_reset_date": campaign.last_reset_date
    }


@app.get("/api/columns")
async def get_available_columns(db: Session = Depends(get_db)):
    """Get available CSV columns."""
    campaign = db.query(Campaign).first()
    if not campaign or not campaign.available_columns:
        return {"columns": []}
    try:
        return {"columns": json.loads(campaign.available_columns)}
    except (json.JSONDecodeError, TypeError):
        return {"columns": []}


@app.post("/api/templates/save")
async def save_templates(
    templates: dict,
    db: Session = Depends(get_db)
):
    """Save custom email templates."""
    from backend.database import CustomTemplate
    
    try:
        # Delete existing templates
        db.query(CustomTemplate).delete()
        
        # Save new templates (including reply template)
        for template_type in ['initial', 'followup1', 'followup2', 'reply']:
            if template_type in templates:
                template_data = templates[template_type]
                template = CustomTemplate(
                    template_type=template_type,
                    subject=template_data.get('subject', ''),
                    body=template_data.get('body', '')
                )
                db.add(template)
        
        db.commit()
        
        # Log event
        log = Log(email=None, event="Custom templates saved")
        db.add(log)
        db.commit()
        
        return {"success": True, "message": "Templates saved successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/templates")
async def get_templates(db: Session = Depends(get_db)):
    """Get current custom templates."""
    from backend.database import CustomTemplate
    
    templates_query = db.query(CustomTemplate).all()
    
    templates = {}
    for template in templates_query:
        templates[template.template_type] = {
            "subject": template.subject,
            "body": template.body
        }
    
    return {"templates": templates}


# Lead Management APIs

@app.get("/api/leads")
async def get_leads(
    page: int = 1,
    limit: int = 50,
    status: str = None,
    search: str = None,
    sort_by: str = "id",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
):
    """Get leads with pagination and filters."""
    try:
        # Base query
        query = db.query(Lead)
        
        # Filter by status (validate to avoid KeyError on invalid status)
        if status and status != "all":
            try:
                status_enum = LeadStatus[status.upper()]
            except KeyError:
                status_enum = None
            if status_enum is not None:
                query = query.filter(Lead.status == status_enum)
        
        # Search
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Lead.email.like(search_term)) |
                (Lead.data_json.like(search_term))
            )
        
        # Count total
        total = query.count()
        
        # Sort
        if sort_by == "email":
            sort_col = Lead.email
        elif sort_by == "status":
            sort_col = Lead.status
        elif sort_by == "last_sent_at":
            sort_col = Lead.last_sent_at
        else:
            sort_col = Lead.id
        
        if sort_order == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())
        
        # Paginate
        offset = (page - 1) * limit
        leads = query.offset(offset).limit(limit).all()
        
        # Format leads (safe parse data_json for corrupt/malformed data)
        leads_data = []
        for lead in leads:
            try:
                lead_json = json.loads(lead.data_json) if lead.data_json else {}
            except (json.JSONDecodeError, TypeError):
                lead_json = {}
            leads_data.append({
                "id": lead.id,
                "email": lead.email,
                "status": lead.status.value,
                "followup_count": lead.followup_count,
                "last_sent_at": lead.last_sent_at.isoformat() if lead.last_sent_at else None,
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
                "data": lead_json
            })
        
        return {
            "leads": leads_data,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/leads/{lead_id}")
async def update_lead(
    lead_id: int,
    update_data: dict,
    db: Session = Depends(get_db)
):
    """Update a lead."""
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Update status if provided (validate to avoid KeyError)
        if "status" in update_data:
            try:
                lead.status = LeadStatus[update_data["status"].upper()]
            except (KeyError, AttributeError):
                raise HTTPException(status_code=400, detail="Invalid status")
        
        # Update data if provided
        if "data" in update_data:
            lead.data_json = json.dumps(update_data["data"])
        
        # Reset follow-up count if status changed to pending
        if "status" in update_data and update_data["status"].upper() == "PENDING":
            lead.followup_count = 0
            lead.last_sent_at = None
        
        db.commit()
        
        # Log event
        log = Log(email=lead.email, event=f"Lead {lead.email} updated")
        db.add(log)
        db.commit()
        
        return {"success": True, "message": "Lead updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/leads/{lead_id}")
async def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """Delete a lead."""
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        email = lead.email
        db.delete(lead)
        db.commit()
        
        # Log event
        log = Log(email=email, event=f"Lead {email} deleted")
        db.add(log)
        db.commit()
        
        return {"success": True, "message": "Lead deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/leads/bulk-delete")
async def bulk_delete_leads(
    lead_ids: dict,
    db: Session = Depends(get_db)
):
    """Bulk delete leads."""
    try:
        ids = lead_ids.get("lead_ids", [])
        
        if not ids:
            raise HTTPException(status_code=400, detail="No lead IDs provided")
        
        # Delete leads
        deleted = db.query(Lead).filter(Lead.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        
        # Log event
        log = Log(email=None, event=f"Bulk deleted {deleted} leads")
        db.add(log)
        db.commit()
        
        return {"success": True, "deleted": deleted}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Analytics APIs

@app.get("/api/analytics")
async def get_analytics(
    date_from: str = None,
    date_to: str = None,
    db: Session = Depends(get_db)
):
    """Get analytics data."""
    try:
        from datetime import timedelta
        
        # Parse dates
        if date_from:
            start_date = datetime.strptime(date_from, "%Y-%m-%d")
        else:
            start_date = datetime.now() - timedelta(days=30)
        
        if date_to:
            end_date = datetime.strptime(date_to, "%Y-%m-%d")
        else:
            end_date = datetime.now()
        
        # Overall stats
        total_leads = db.query(Lead).count()
        total_sent = db.query(Lead).filter(Lead.status == LeadStatus.SENT).count()
        total_replied = db.query(Lead).filter(Lead.status == LeadStatus.REPLIED).count()
        total_failed = db.query(Lead).filter(Lead.status == LeadStatus.FAILED).count()
        total_pending = db.query(Lead).filter(Lead.status == LeadStatus.PENDING).count()
        
        # Calculate rates
        reply_rate = (total_replied / total_sent * 100) if total_sent > 0 else 0
        failure_rate = (total_failed / total_leads * 100) if total_leads > 0 else 0
        
        # Status distribution
        status_distribution = {
            "pending": total_pending,
            "sent": total_sent,
            "replied": total_replied,
            "failed": total_failed
        }
        
        # Daily stats
        daily_stats = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            day_start = current_date.replace(hour=0, minute=0, second=0)
            day_end = current_date.replace(hour=23, minute=59, second=59)
            
            sent_count = db.query(Lead).filter(
                Lead.last_sent_at >= day_start,
                Lead.last_sent_at <= day_end
            ).count()
            
            replied_count = db.query(Lead).filter(
                Lead.status == LeadStatus.REPLIED,
                Lead.last_sent_at >= day_start,
                Lead.last_sent_at <= day_end
            ).count()
            
            daily_stats.append({
                "date": date_str,
                "sent": sent_count,
                "replied": replied_count
            })
            
            current_date += timedelta(days=1)
        
        return {
            "total_leads": total_leads,
            "total_sent": total_sent,
            "total_replied": total_replied,
            "total_failed": total_failed,
            "total_pending": total_pending,
            "reply_rate": round(reply_rate, 2),
            "failure_rate": round(failure_rate, 2),
            "status_distribution": status_distribution,
            "daily_stats": daily_stats
        }
        
    except ValueError as e:
        if "date" in str(e).lower() or "time" in str(e).lower():
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Settings APIs (all config in UI; no .env required)

@app.get("/api/settings")
async def get_settings():
    """Get app settings and email accounts (passwords masked). Only DB accounts in list to avoid null id."""
    s = get_app_settings()
    accounts = get_email_accounts_db_only(active_only=False)
    using_env_fallback = len(accounts) == 0 and get_env_fallback_account() is not None
    return {
        "license_key": s.get("license_key", ""),
        "daily_limit": s.get("daily_email_limit", "500"),
        "min_delay": s.get("min_delay_seconds", "60"),
        "max_delay": s.get("max_delay_seconds", "120"),
        "pause_every_n": s.get("pause_every_n_emails", "20"),
        "pause_min_minutes": s.get("pause_min_minutes", "5"),
        "pause_max_minutes": s.get("pause_max_minutes", "8"),
        "calendar_link": s.get("calendar_link", ""),
        "email_queue_interval_seconds": s.get("email_queue_interval_seconds", "300"),
        "reply_check_interval_seconds": s.get("reply_check_interval_seconds", "300"),
        "using_env_fallback": using_env_fallback,
        "email_accounts": [
            {
                "id": a.id,
                "label": a.label,
                "email": a.email,
                "smtp_server": a.smtp_server,
                "smtp_port": a.smtp_port,
                "imap_server": a.imap_server,
                "imap_port": a.imap_port,
                "is_active": a.is_active,
                "sent_today": a.sent_today or 0,
            }
            for a in accounts
        ],
    }


@app.post("/api/settings")
async def save_settings(settings: dict):
    """Save app settings (from Settings page)."""
    # license_sheet_url is owner-only (.env), not saved from UI
    allowed = {
        "license_key", "daily_email_limit",
        "min_delay_seconds", "max_delay_seconds", "pause_every_n_emails",
        "pause_min_minutes", "pause_max_minutes", "calendar_link",
        "email_queue_interval_seconds", "reply_check_interval_seconds",
    }
    to_save = {k: str(v).strip() for k, v in (settings or {}).items() if k in allowed}
    save_app_settings(to_save)
    return {"success": True, "message": "Settings saved"}


@app.get("/api/email-accounts")
async def list_email_accounts():
    """List email accounts (no passwords)."""
    accounts = get_email_accounts(active_only=False)
    return {
        "accounts": [
            {
                "id": a.id,
                "label": a.label,
                "email": a.email,
                "smtp_server": a.smtp_server,
                "smtp_port": a.smtp_port,
                "imap_server": a.imap_server,
                "imap_port": a.imap_port,
                "is_active": a.is_active,
                "sent_today": a.sent_today or 0,
            }
            for a in accounts
        ]
    }


@app.post("/api/email-accounts")
async def add_email_account(data: dict):
    """Add an email account."""
    try:
        email = (data.get("email") or "").strip()
        password = data.get("password") or ""
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")
        acc = create_email_account(
            label=(data.get("label") or "").strip() or email,
            email=email,
            password=password,
            smtp_server=data.get("smtp_server", "smtp.gmail.com"),
            smtp_port=int(data.get("smtp_port", 587)),
            imap_server=data.get("imap_server", "imap.gmail.com"),
            imap_port=int(data.get("imap_port", 993)),
        )
        return {"success": True, "id": acc.id, "message": "Account added"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/email-accounts/{account_id}")
async def edit_email_account(account_id: int, data: dict):
    """Update an email account."""
    acc = update_email_account(
        account_id,
        label=data.get("label"),
        email=data.get("email"),
        password=data.get("password") or None,
        smtp_server=data.get("smtp_server"),
        smtp_port=data.get("smtp_port"),
        imap_server=data.get("imap_server"),
        imap_port=data.get("imap_port"),
        is_active=data.get("is_active"),
    )
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"success": True, "message": "Account updated"}


@app.delete("/api/email-accounts/{account_id}")
async def remove_email_account(account_id: int):
    """Delete an email account."""
    if not delete_email_account(account_id):
        raise HTTPException(status_code=404, detail="Account not found")
    return {"success": True, "message": "Account deleted"}


@app.post("/api/email-accounts/test")
async def test_email_account_connection(data: dict):
    """Test SMTP and IMAP for provided credentials (e.g. when adding new account)."""
    email_addr = (data.get("email") or "").strip()
    password = data.get("password", "")
    smtp_server = (data.get("smtp_server") or "smtp.gmail.com").strip()
    smtp_port = int(data.get("smtp_port", 587))
    imap_server = (data.get("imap_server") or "imap.gmail.com").strip()
    imap_port = int(data.get("imap_port", 993))
    if not email_addr or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    out = {}
    ok_smtp, msg_smtp = test_smtp_connection(email_addr, password, smtp_server, smtp_port)
    out["smtp"] = {"ok": ok_smtp, "message": msg_smtp}
    ok_imap, msg_imap = test_imap_connection(email_addr, password, imap_server, imap_port)
    out["imap"] = {"ok": ok_imap, "message": msg_imap}
    return out


@app.post("/api/email-accounts/{account_id}/test")
async def test_email_account_by_id(account_id: int):
    """Test SMTP and IMAP for an existing account (uses stored credentials)."""
    from backend.settings_service import get_email_account_by_id
    acc = get_email_account_by_id(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    ok_smtp, msg_smtp = test_smtp_connection(acc.email, acc.password, acc.smtp_server, acc.smtp_port)
    ok_imap, msg_imap = test_imap_connection(acc.email, acc.password, acc.imap_server, acc.imap_port)
    return {
        "smtp": {"ok": ok_smtp, "message": msg_smtp},
        "imap": {"ok": ok_imap, "message": msg_imap},
    }


# Daily Report APIs

@app.post("/api/report/send")
async def send_daily_report_now(email: str = None):
    """Manually trigger daily report send."""
    from backend.daily_report import DailyReportGenerator
    
    try:
        generator = DailyReportGenerator()
        success = generator.send_daily_report(email)
        
        if success:
            accs = get_email_accounts(active_only=True)
            default_to = accs[0].email if accs else ""
            return {"success": True, "message": f"Report sent to {email or default_to}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send report")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/report/preview")
async def preview_daily_report():
    """Get daily report data for preview."""
    from backend.daily_report import DailyReportGenerator
    
    try:
        generator = DailyReportGenerator()
        report = generator.generate_report()
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def serve_frontend():
    """Serve the frontend dashboard."""
    return FileResponse("frontend/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)