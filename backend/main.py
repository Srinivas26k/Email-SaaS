"""FastAPI main application with all endpoints."""
import threading
import json
import pandas as pd
from io import StringIO
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.config import config
from backend.database import init_db, get_db, Lead, Campaign, Log, LeadStatus, CampaignStatus
from backend.license_validator import validate_on_startup
from backend.background_worker import BackgroundWorker
from backend.reply_checker import ReplyChecker

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

# Background worker and reply checker
background_worker: Optional[BackgroundWorker] = None
reply_checker: Optional[ReplyChecker] = None
reply_checker_thread: Optional[threading.Thread] = None


@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    global background_worker, reply_checker, reply_checker_thread
    
    print("🚀 Starting Email Outreach System...")
    
    # Validate license (blocks startup if invalid)
    validate_on_startup()
    
    # Initialize database
    init_db()
    print("✅ Database initialized")
    
    # Start background worker in a separate thread
    background_worker = BackgroundWorker()
    worker_thread = threading.Thread(target=background_worker.start, daemon=True)
    worker_thread.start()
    print("✅ Background worker started")
    
    # Start reply checker in a separate thread
    reply_checker = ReplyChecker()
    
    def reply_checker_loop():
        import time
        while True:
            try:
                reply_checker.check_replies()
            except Exception as e:
                print(f"❌ Reply checker error: {str(e)}")
            time.sleep(300)  # Check every 5 minutes
    
    reply_checker_thread = threading.Thread(target=reply_checker_loop, daemon=True)
    reply_checker_thread.start()
    print("✅ Reply checker started")
    
    print("🎉 System ready!")


# ==================== API ENDPOINTS ====================

@app.post("/api/upload-leads")
async def upload_leads(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload leads CSV with deduplication."""
    try:
        # Read CSV
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode('utf-8')))
        
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
    
    return {
        "sent_today": campaign.sent_today if campaign else 0,
        "daily_limit": config.DAILY_EMAIL_LIMIT,
        "replies": replied_count,
        "failed": failed_count,
        "total_leads": total_leads,
        "pending_leads": pending_count,
        "sent_leads": sent_count,
        "campaign_status": campaign.status.value if campaign else "STOPPED"
    }


@app.get("/api/logs")
async def get_logs(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent logs."""
    logs = db.query(Log).order_by(Log.timestamp.desc()).limit(limit).all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "email": log.email,
                "event": log.event,
                "timestamp": log.timestamp.isoformat()
            }
            for log in logs
        ]
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
    
    return {"columns": json.loads(campaign.available_columns)}


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
        
        # Save new templates
        for template_type in ['initial', 'followup1', 'followup2']:
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


# Serve frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def serve_frontend():
    """Serve the frontend dashboard."""
    return FileResponse("frontend/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)
