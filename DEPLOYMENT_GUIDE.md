# Streamlit Cloud Deployment Guide

## Quick Start: Deploy to Streamlit Cloud (5 minutes)

## Hybrid Backend (Google Sheets + SQLite Fallback)

The dashboard now supports a hybrid data backend:
- Primary: Google Sheets (shared live data)
- Fallback: SQLite (`plan_data.db`) if Sheets is unavailable

To use Google Sheets, set both environment/secrets values:
- `USE_GOOGLE_SHEETS=true`
- `GOOGLE_SHEET_ID=<your spreadsheet id>`

And provide service account credentials as:
- `gcp_service_account` in Streamlit secrets (recommended), or
- `GOOGLE_SERVICE_ACCOUNT_JSON` as a JSON string environment variable

### Google Sheets Setup (One-time)

1. Create a Google Sheet and copy its ID from the URL:
   - `https://docs.google.com/spreadsheets/d/<THIS_PART>/edit`
2. Create a Google Cloud service account and download the JSON key.
3. Share the sheet with the service account email as **Editor**.
4. In Streamlit Cloud app settings, add secrets:

```toml
USE_GOOGLE_SHEETS = "true"
GOOGLE_SHEET_ID = "your_google_sheet_id"

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
universe_domain = "googleapis.com"
```

On startup, the app auto-creates these tabs in the sheet:
- `phases`
- `tasks`
- `milestones`
- `task_updates`
- `activity_log`

### Prerequisites
- GitHub account (free)
- Streamlit account (free, sign in with GitHub)

### Step 1: Push Your Code to GitHub

1. Create a new GitHub repository:
   - Go to [github.com/new](https://github.com/new)
   - Name it `100-day-plan` (or similar)
   - Keep it public or private

2. Push your local files to GitHub:
   ```bash
   cd "C:\Users\damia\Documents\100 Day Plan"
   git init
   git add .
   git commit -m "Initial commit: 100-Day Plan Dashboard with SQLite backend"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/100-day-plan.git
   git push -u origin main
   ```

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Select your GitHub repository, branch, and file:
   - Repository: `your-username/100-day-plan`
   - Branch: `main`
   - Main file path: `streamlit_app.py`
4. Click **"Deploy!"**

Your app will be live in ~2-3 minutes at: `https://your-app-name.streamlit.app`

---

## Running Locally (for testing)

### Prerequisites
- Python 3.8+
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### Run the app
```bash
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

---

## Key Features: Team Collaboration

### 👤 User Authentication
- Simple name-based login (no password needed)
- All updates are attributed to the logged-in user

### 💾 Data Persistence
- **Google Sheets** stores shared team data when enabled
- **SQLite Database** (`plan_data.db`) is automatic fallback
- **Automatic backup**: code and local fallback data can still be synced via GitHub

### 📋 Activity Log
- Complete audit trail of all changes
- See who updated what and when
- Track team contributions

### 🔄 Real-time Updates
- All changes visible to everyone immediately
- No manual syncing required

---

## Team Workflow

### For Your Team Members:
1. **Visit** the shared Streamlit Cloud URL
2. **Enter your name** in the sidebar (left panel)
3. **Update tasks** in the "Task Updates" section
4. All changes are automatically saved and visible to others

### Example Workflow:
```
Team Member A logs in → Updates Task "Open SPV Bank Accounts" to 100% Complete
↓
(Activity logged: "Updated task" at 14:32 by Team Member A)
↓
Team Member B logs in → Sees the update immediately
↓
Team Member B comments in notes and updates related task
```

---

## Sharing the Dashboard

### Internal Team:
- Share the Streamlit Cloud URL with your team
- Everyone can access from any device with internet
- No installation required

### Example URL:
```
https://100-day-plan.streamlit.app
```

---

## Data Management

### Backing Up Data:
The database is stored in `plan_data.db`. To back it up:
1. Download the file from your workspace
2. Keep a copy in cloud storage (Google Drive, OneDrive, etc.)

### Exporting for Reports:
Use the **Data Management** section in the app to:
- Export JSON for full data backup
- Export CSV for Excel/Board reports

---

## Troubleshooting

### ❌ App not loading?
- Check your internet connection
- Clear browser cache (Ctrl+F5)
- Restart Streamlit: `streamlit run streamlit_app.py`

### ❌ Database errors?
- Database is created automatically on first run
- If corrupted, delete `plan_data.db` and restart

### ❌ Updates not showing?
- Refresh the page (F5)
- Make sure you're logged in
- Check Activity Log to confirm the update was recorded

---

## Environment Variables (Optional)

For production deployment with enhanced security, you can set:

```bash
# In Streamlit Cloud Advanced Settings:
STREAMLIT_LOGGER_LEVEL=warning
```

---

## Support & Resources

- **Streamlit Docs**: https://docs.streamlit.io
- **GitHub Help**: https://docs.github.com
- **Troubleshooting**: See app's Data Management section for status

---

## Architecture Overview

```
┌─────────────────────────────────┐
│  Streamlit Cloud (Live App)     │
│  - Hosted at streamlit.app      │
│  - Auto-reloads on GitHub push  │
└──────────────┬──────────────────┘
               │
        ┌──────▼──────┐
        │   GitHub    │
        │ (Repository)│
        │             │
        │ - Code      │
        │ - Data      │
        └──────┬──────┘
               │
        ┌──────▼────────────┐
        │  SQLite Database  │
        │  (plan_data.db)   │
        │                   │
        │ - Tasks           │
        │ - Phases          │
        │ - Activity Log    │
        │ - User Updates    │
        └───────────────────┘
```

---

## Next Steps

1. ✅ Deploy to Streamlit Cloud (this guide)
2. ✅ Share URL with team
3. ✅ Have team members log in and test
4. ✅ Start tracking updates in Activity Log
5. ✅ Export data regularly as backups

---

**Created**: April 2026
**Version**: 1.0 with SQLite Team Backend
