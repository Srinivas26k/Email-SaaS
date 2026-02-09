"""Daily analytics report generator with PDF export."""
import io
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy import func

from backend.database import SessionLocal, Lead, Log, Campaign, LeadStatus
from backend.config import config as env_config
from backend.settings_service import get_app_settings, get_email_accounts
from backend.email_sender import EmailSender


class DailyReportGenerator:
    """Generate and send daily analytics reports."""
    
    def __init__(self):
        self.email_sender = EmailSender()
    
    def generate_report(self) -> Dict:
        """Generate daily analytics report."""
        session = SessionLocal()
        try:
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            # Get campaign info
            campaign = session.query(Campaign).first()
            
            # Today's stats
            today_sent = session.query(Lead).filter(
                func.date(Lead.last_sent_at) == today
            ).count()
            
            today_replied = session.query(Lead).filter(
                Lead.status == LeadStatus.REPLIED,
                func.date(Lead.last_sent_at) == today
            ).count()
            
            today_failed = session.query(Log).filter(
                func.date(Log.timestamp) == today,
                Log.event.like('%Failed%')
            ).count()
            
            # Overall stats
            total_leads = session.query(Lead).count()
            total_sent = session.query(Lead).filter(
                Lead.status.in_([LeadStatus.SENT, LeadStatus.REPLIED])
            ).count()
            total_replied = session.query(Lead).filter(
                Lead.status == LeadStatus.REPLIED
            ).count()
            total_failed = session.query(Lead).filter(
                Lead.status == LeadStatus.FAILED
            ).count()
            total_pending = session.query(Lead).filter(
                Lead.status == LeadStatus.PENDING
            ).count()
            
            # Calculate rates
            reply_rate = (total_replied / total_sent * 100) if total_sent > 0 else 0
            failure_rate = (total_failed / total_leads * 100) if total_leads > 0 else 0
            
            # Last 7 days trend
            last_7_days = []
            for i in range(7):
                date = today - timedelta(days=i)
                sent = session.query(Lead).filter(
                    func.date(Lead.last_sent_at) == date
                ).count()
                replied = session.query(Lead).filter(
                    Lead.status == LeadStatus.REPLIED,
                    func.date(Lead.last_sent_at) == date
                ).count()
                last_7_days.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'sent': sent,
                    'replied': replied
                })
            
            last_7_days.reverse()
            
            # Recent activity (last 10 events)
            recent_logs = session.query(Log).order_by(
                Log.timestamp.desc()
            ).limit(10).all()
            
            report = {
                'generated_at': datetime.now().isoformat(),
                'date': today.strftime('%Y-%m-%d'),
                'today': {
                    'sent': today_sent,
                    'replied': today_replied,
                    'failed': today_failed,
                    'daily_limit': int(get_app_settings().get("daily_email_limit", "500")),
                    'usage_percent': (today_sent / max(1, int(get_app_settings().get("daily_email_limit", "500"))) * 100)
                },
                'overall': {
                    'total_leads': total_leads,
                    'total_sent': total_sent,
                    'total_replied': total_replied,
                    'total_failed': total_failed,
                    'total_pending': total_pending,
                    'reply_rate': round(reply_rate, 2),
                    'failure_rate': round(failure_rate, 2)
                },
                'last_7_days': last_7_days,
                'recent_activity': [
                    {
                        'event': log.event or '',
                        'email': log.email or '',
                        'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else ''
                    }
                    for log in recent_logs
                ],
                'campaign_status': campaign.status.value if campaign else 'UNKNOWN'
            }
            
            return report
            
        finally:
            session.close()
    
    def generate_html_report(self, report: Dict) -> str:
        """Generate a modern, professional HTML email report."""
        today_data = report['today']
        overall_data = report['overall']
        
        # Color Palette
        primary = "#4F46E5"  # Indigo
        success = "#10B981"  # Emerald
        danger = "#EF4444"   # Rose
        warning = "#F59E0B"  # Amber
        dark = "#1F2937"     # Slate 800
        light_bg = "#F9FAFB" # Slate 50

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            background-color: {light_bg};
            margin: 0;
            padding: 40px 20px;
            color: {dark};
        }}
        .container {{
            max-width: 650px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            overflow: hidden;
            border: 1px solid #E5E7EB;
        }}
        .header {{
            padding: 40px 30px;
            background-color: {dark};
            color: white;
            text-align: left;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            background: rgba(255,255,255,0.2);
            margin-bottom: 12px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.025em;
        }}
        .metrics-grid {{
            display: table;
            width: 100%;
            border-collapse: separate;
            border-spacing: 20px;
            margin-top: -30px;
        }}
        .metric-card {{
            display: table-cell;
            background: white;
            padding: 24px;
            border-radius: 12px;
            border: 1px solid #E5E7EB;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
            width: 25%;
        }}
        .metric-label {{
            font-size: 11px;
            font-weight: 600;
            color: #6B7280;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: 700;
            color: {dark};
        }}
        .section {{
            padding: 30px;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 20px;
            color: {dark};
            display: flex;
            align-items: center;
        }}
        .progress-container {{
            background: #F3F4F6;
            border-radius: 8px;
            height: 12px;
            width: 100%;
            overflow: hidden;
            margin-bottom: 8px;
        }}
        .progress-bar {{
            height: 100%;
            background: {primary};
            border-radius: 8px;
        }}
        .table {{
            width: 100%;
            border-spacing: 0;
            margin-top: 10px;
        }}
        .table th {{
            text-align: left;
            font-size: 12px;
            font-weight: 600;
            color: #9CA3AF;
            padding: 12px 8px;
            border-bottom: 1px solid #F3F4F6;
        }}
        .table td {{
            padding: 16px 8px;
            font-size: 14px;
            border-bottom: 1px solid #F3F4F6;
        }}
        .status-pill {{
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
        }}
        .log-item {{
            padding: 12px;
            border-radius: 8px;
            background: {light_bg};
            margin-bottom: 8px;
            font-size: 13px;
        }}
        .log-meta {{
            font-size: 11px;
            color: #9CA3AF;
            margin-top: 4px;
        }}
        .footer {{
            padding: 30px;
            background: {light_bg};
            text-align: center;
            font-size: 12px;
            color: #9CA3AF;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="badge">{report['campaign_status']}</span>
            <h1>Daily Performance Analytics</h1>
            <p style="opacity: 0.7; margin: 8px 0 0 0;">Report for {report['date']}</p>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Sent</div>
                <div class="metric-value">{today_data['sent']}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Replies</div>
                <div class="metric-value" style="color: {success}">{today_data['replied']}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Efficiency</div>
                <div class="metric-value">{round(today_data['usage_percent'])}%</div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Daily Quota Usage</div>
            <div class="progress-container">
                <div class="progress-bar" style="width: {today_data['usage_percent']}%"></div>
            </div>
            <div style="font-size: 12px; color: #6B7280; text-align: right;">
                {today_data['sent']} of {today_data['daily_limit']} emails sent
            </div>
        </div>

        <div class="section" style="background: {light_bg};">
            <div class="section-title">Campaign Health</div>
            <table class="table">
                <tr>
                    <td>Total Leads</td>
                    <td style="text-align: right; font-weight: 600;">{overall_data['total_leads']}</td>
                </tr>
                <tr>
                    <td>Reply Rate</td>
                    <td style="text-align: right; font-weight: 600; color: {success};">{overall_data['reply_rate']}%</td>
                </tr>
                <tr>
                    <td>Failure Rate</td>
                    <td style="text-align: right; font-weight: 600; color: {danger};">{overall_data['failure_rate']}%</td>
                </tr>
            </table>
        </div>

        <div class="section">
            <div class="section-title">7-Day Trend</div>
            <table class="table">
                <thead>
                    <tr>
                        <th>DATE</th>
                        <th>SENT</th>
                        <th style="text-align: right;">REPLIES</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f'''
                    <tr>
                        <td>{day['date']}</td>
                        <td style="font-weight: 500;">{day['sent']}</td>
                        <td style="text-align: right; font-weight: 700; color: {success};">+{day['replied']}</td>
                    </tr>
                    ''' for day in report['last_7_days']])}
                </tbody>
            </table>
        </div>

        <div class="section">
            <div class="section-title">Recent Activity</div>
            {''.join([f'''
            <div class="log-item">
                <div style="font-weight: 500;">{activity['event']}</div>
                <div class="log-meta">{activity['timestamp']} • {activity['email']}</div>
            </div>
            ''' for activity in report['recent_activity'][:3]])}
        </div>

        <div class="footer">
            Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')} • 
            <strong>Outreach Intelligence</strong>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def send_daily_report(self, to_email: str = None):
        """Generate and send daily report via email."""
        try:
            # Use configured email if not specified
            if not to_email:
                accounts = get_email_accounts(active_only=True)
                to_email = accounts[0].email if accounts else getattr(env_config, "EMAIL_ADDRESS", "") or ""
            
            print(f"📊 Generating daily report for {to_email}...")
            
            # Generate report data
            report = self.generate_report()
            
            # Generate HTML
            html_body = self.generate_html_report(report)
            
            # Send email
            subject = f"📊 Daily Outreach Report - {report['date']}"
            
            success = self.email_sender.send_email(
                to_email,
                subject,
                html_body,
                is_html=True
            )
            
            if success:
                print(f"✅ Daily report sent to {to_email}")
                return True
            else:
                print(f"❌ Failed to send daily report to {to_email}")
                return False
                
        except Exception as e:
            print(f"❌ Error generating daily report: {str(e)}")
            return False
