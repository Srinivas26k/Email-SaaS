# 📧 Email Outreach System

A private, reliable, 24/7 email outreach system with automatic follow-ups and reply detection.

## ✨ Features

- ✅ Send up to 500 emails/day with intelligent rate limiting
- ✅ Automatic follow-ups (3-day intervals, max 2 follow-ups)
- ✅ Reply detection with automatic calendar link responses
- ✅ Industry-specific templates (Healthcare, Fintech, EdTech)
- ✅ Crash recovery - system resumes automatically after restarts
- ✅ License validation via Google Sheets
- ✅ Real-time dashboard with charts and metrics
- ✅ 24/7 operation (runs independently of browser)

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- UV package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))
- Email account with SMTP/IMAP access (Gmail recommended)
- Google Sheet for license validation

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd /home/srinivas/Projects/Python-projects/SaaS/email
   ```

2. **Install dependencies with UV:**
   ```bash
   uv sync
   ```

3. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

4. **Configure environment variables** (edit `.env`):

   **License Configuration:**
   - Create a Google Sheet with columns: `license_key`, `status`, `expiry_date`
   - Make it public (Anyone with link can view)
   - Get the CSV export URL: File → Share → Publish to web → Select CSV
   - Add your license key to the sheet with status "ACTIVE" and future expiry date

   **Email Configuration:**
   - For Gmail: Enable 2FA and create an [App Password](https://myaccount.google.com/apppasswords)
   - Update `.env` with your email and app password

   **Calendar Link:**
   - Add your Calendly or booking link

### Running the System

```bash
uv run python -m backend.main
```

The system will:
1. Validate your license (blocks startup if invalid)
2. Initialize the database
3. Start the background email sender
4. Start the reply checker (polls every 5 minutes)
5. Launch the web dashboard at `http://localhost:8000`

## 📊 Using the Dashboard

1. **Upload Leads:**
   - Prepare a CSV with columns: `email` (required), `first_name`, `company`, `industry` (optional)
   - Click "Upload CSV" in the dashboard
   - System automatically deduplicates by email

2. **Start Campaign:**
   - Click "Start" button
   - System begins sending emails with rate limiting
   - Random delays: 60-120 seconds between emails
   - Pause every 20 emails for 5-8 minutes

3. **Monitor Progress:**
   - View real-time metrics (sent today, replies, failed)
   - Check activity logs
   - See email send chart

4. **Automatic Follow-ups:**
   - System sends follow-up 1 after 3 days (no reply)
   - System sends follow-up 2 after 6 days (no reply)
   - Stops after 2 follow-ups or when reply detected

5. **Reply Handling:**
   - System checks IMAP every 5 minutes
   - When reply detected: marks lead as REPLIED, sends calendar link automatically

## 🗄️ Database Schema

**SQLite database:** `email_system.db`

**Tables:**
- `leads`: Email addresses, status, follow-up count
- `campaign`: Campaign state, daily counter
- `logs`: Activity logs with timestamps

## 🔧 Configuration

Key settings in `.env`:

```env
DAILY_EMAIL_LIMIT=500         # Max emails per day
MIN_DELAY_SECONDS=60          # Minimum delay between emails
MAX_DELAY_SECONDS=120         # Maximum delay between emails
PAUSE_EVERY_N_EMAILS=20       # Pause frequency
PAUSE_MIN_MINUTES=5           # Minimum pause duration
PAUSE_MAX_MINUTES=8           # Maximum pause duration
```

## 🛡️ Crash Recovery

The system is designed to survive crashes and restarts:

- State is written to SQLite after every email send
- On restart, system reads state from database
- Duplicate sends are prevented
- Follow-up schedules are maintained
- Campaign continues from where it left off

## 📝 Industry Templates

**Pre-configured industries:**
- Healthcare
- Fintech
- EdTech

Each industry has 3 email templates (initial + 2 follow-ups) with variable substitution:
- `{{first_name}}`
- `{{company}}`
- `{{industry}}`

Edit templates in `backend/templates.py`.

## 🚢 Deployment (Cloud VM)

For 24/7 operation, deploy to a cloud VM:

1. **Upload files to server:**
   ```bash
   rsync -avz . user@your-server:/path/to/email-system
   ```

2. **SSH into server:**
   ```bash
   ssh user@your-server
   cd /path/to/email-system
   ```

3. **Install UV and dependencies:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv sync
   ```

4. **Configure .env file**

5. **Run with screen or tmux (keeps running after disconnect):**
   ```bash
   screen -S email-system
   uv run python -m backend.main
   # Press Ctrl+A, then D to detach
   ```

6. **Reattach later:**
   ```bash
   screen -r email-system
   ```

**Alternative: Use systemd service** (recommended for production)

Create `/etc/systemd/system/email-outreach.service`:

```ini
[Unit]
Description=Email Outreach System
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/email-system
ExecStart=/home/your-user/.cargo/bin/uv run python -m backend.main
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable email-outreach
sudo systemctl start email-outreach
sudo systemctl status email-outreach
```

## 🐛 Troubleshooting

**License validation fails:**
- Check Google Sheet is public
- Verify CSV export URL is correct
- Ensure license key matches exactly
- Check expiry date format (YYYY-MM-DD recommended)

**SMTP connection errors:**
- For Gmail: Use App Password, not regular password
- Check firewall allows outbound connections on port 587
- Verify SMTP server and port are correct

**Emails not sending:**
- Check campaign status (must be RUNNING)
- Verify daily limit not reached
- Check logs for error messages
- Test SMTP connection manually

**Reply detection not working:**
- Verify IMAP credentials
- Check IMAP port (993 for SSL)
- Ensure inbox has recent emails

## 📖 API Endpoints

- `POST /api/upload-leads` - Upload CSV with leads
- `POST /api/campaign/start` - Start campaign
- `POST /api/campaign/pause` - Pause campaign
- `POST /api/campaign/stop` - Stop campaign
- `GET /api/metrics` - Get current metrics
- `GET /api/logs` - Get activity logs
- `GET /api/campaign/status` - Get campaign status

## 📄 License

This is a proprietary system. Valid license required to run.

## 🆘 Support

For issues or questions, check the logs in the dashboard or database.
