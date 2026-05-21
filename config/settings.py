# ============================================================
# config/settings.py — Central configuration for the entire app
# ============================================================
# This file is the "control panel" of the project.
# All file paths, feature flags, and settings live here.
# Other modules import from this file instead of hardcoding values.

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env file (for secrets like email password) ─────────
# The .env file sits in the project root and is never uploaded to GitHub.
# If it doesn't exist, that's fine — we just use defaults.
load_dotenv()

# ── Base directory ───────────────────────────────────────────
# Path(__file__) is this file's location: config/settings.py
# .parent    → config/
# .parent    → project root  (business_automation/)
BASE_DIR = Path(__file__).parent.parent

# ── Key folders ──────────────────────────────────────────────
DATA_INPUT_DIR  = BASE_DIR / "data" / "input"
DATA_OUTPUT_DIR = BASE_DIR / "data" / "output"
TEMPLATES_DIR   = BASE_DIR / "templates"
LOGS_DIR        = BASE_DIR / "logs"
ASSETS_DIR      = BASE_DIR / "assets"

# ── Auto-create folders if they don't exist ──────────────────
# This prevents "FileNotFoundError" when the app runs for the first time.
for folder in [DATA_INPUT_DIR, DATA_OUTPUT_DIR, TEMPLATES_DIR, LOGS_DIR, ASSETS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# ── Logging settings ─────────────────────────────────────────
LOG_LEVEL        = os.getenv("LOG_LEVEL", "INFO")   # DEBUG, INFO, WARNING, ERROR
LOG_FILE         = LOGS_DIR / "app.log"
LOG_MAX_BYTES    = 5 * 1024 * 1024   # 5 MB before log file rotates
LOG_BACKUP_COUNT = 3                 # Keep 3 old log files

# ── Email settings (loaded from .env, never hardcoded) ───────
EMAIL_SENDER    = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD  = os.getenv("EMAIL_PASSWORD", "")
EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))

# ── Data processing settings ─────────────────────────────────
# File types the app will accept as input
ALLOWED_INPUT_EXTENSIONS = [".csv", ".xlsx", ".xls"]

# Columns to always drop when cleaning data
# (Add column names your clients commonly have that are junk)
COLUMNS_TO_DROP = ["Unnamed: 0", "Unnamed: 0.1"]

# How to handle missing (NaN) values in numeric columns
FILL_NUMERIC_NAN_WITH = 0

# How to handle missing values in text columns
FILL_TEXT_NAN_WITH = "N/A"

# ── Report settings ──────────────────────────────────────────
REPORT_COMPANY_NAME = os.getenv("COMPANY_NAME", "Business Automation Suite")
REPORT_AUTHOR       = os.getenv("REPORT_AUTHOR", "Automation Bot")
REPORT_LOGO_PATH    = ASSETS_DIR / "logo.png"   # Optional: add your logo here

# PDF page size: "A4" or "LETTER"
PDF_PAGE_SIZE = "A4"

# Brand colors (R, G, B) — change these to match your client's branding
PDF_PRIMARY_COLOR   = (41, 98, 255)    # Blue
PDF_SECONDARY_COLOR = (100, 100, 100)  # Gray
PDF_SUCCESS_COLOR   = (34, 197, 94)    # Green
PDF_DANGER_COLOR    = (239, 68, 68)    # Red

# ── File organizer settings ───────────────────────────────────
# Maps file extensions to folder names.
# Files will be sorted into these folders automatically.
FILE_SORT_RULES = {
    # Documents
    ".pdf":  "Documents/PDFs",
    ".docx": "Documents/Word",
    ".doc":  "Documents/Word",
    ".txt":  "Documents/Text",
    # Spreadsheets
    ".xlsx": "Spreadsheets",
    ".xls":  "Spreadsheets",
    ".csv":  "Spreadsheets",
    # Images
    ".jpg":  "Images",
    ".jpeg": "Images",
    ".png":  "Images",
    ".gif":  "Images",
    # Archives
    ".zip":  "Archives",
    ".rar":  "Archives",
    ".7z":   "Archives",
    # Code
    ".py":   "Code/Python",
    ".js":   "Code/JavaScript",
    ".html": "Code/Web",
}

# ── Scheduler settings ───────────────────────────────────────
# When to run the automated daily report
SCHEDULER_DAILY_REPORT_TIME = os.getenv("SCHEDULER_TIME", "08:00")   # 8:00 AM

# ── App appearance ───────────────────────────────────────────
APP_TITLE   = "Business Workflow Automation Suite"
APP_VERSION = "1.0.0"
APP_WIDTH   = 1000
APP_HEIGHT  = 700
APP_THEME   = "arc"   # GUI theme name (from ttkthemes)

# ── Feature flags ────────────────────────────────────────────
# Set to False to disable features (useful for clients who don't need email)
FEATURE_EMAIL_ENABLED     = True
FEATURE_SCHEDULER_ENABLED = True
FEATURE_PDF_REPORTS       = True
FEATURE_FILE_ORGANIZER    = True
