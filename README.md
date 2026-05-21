# 🗂 Business Workflow Automation Suite

> A production-quality Python automation toolkit for Excel/CSV processing, PDF reporting, file organization, email automation, and scheduled tasks — all driven by a professional GUI dashboard.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![pandas](https://img.shields.io/badge/pandas-2.x-150458?logo=pandas)](https://pandas.pydata.org)
[![ReportLab](https://img.shields.io/badge/ReportLab-PDF-red)](https://reportlab.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📸 Features at a Glance

| Feature | Description |
|---|---|
| 📊 **Data Processing** | Clean, merge, and analyze CSV/Excel files automatically |
| 📄 **PDF Reports** | Professional multi-page PDFs with cover, tables, branding |
| 📋 **Excel Reports** | Styled multi-sheet .xlsx files with auto-fit columns |
| 🗂 **File Organizer** | Sort files into subfolders by type with dry-run preview |
| 📧 **Email Automation** | Send reports via Gmail/SMTP with attachments |
| ⏰ **Task Scheduler** | Run jobs daily, hourly, or weekly in the background |
| 🖥 **GUI Dashboard** | Tabbed Tkinter interface — no command line required |
| 📋 **Logging** | Rotating log files + live log viewer tab |
| ✅ **Tests** | 40+ pytest unit tests across all modules |

---

## 🏗 Project Structure

```
business_automation/
│
├── main.py                    # ← Run this to launch the app
│
├── config/
│   ├── settings.py            # Central config (paths, colors, flags)
│   └── .env.example           # Template for secrets (email, etc.)
│
├── gui/
│   └── dashboard.py           # Tkinter GUI with 6 tabs
│
├── data_processor/
│   ├── cleaner.py             # Load + clean CSV/Excel files
│   ├── merger.py              # Merge multiple files (stack or join)
│   └── analyzer.py            # Statistical summaries & group-by
│
├── report_gen/
│   ├── pdf_report.py          # ReportLab PDF generation
│   └── excel_report.py        # openpyxl styled Excel generation
│
├── file_organizer/
│   └── organizer.py           # Auto-sort files by extension
│
├── email_sender/
│   └── mailer.py              # SMTP email with attachments
│
├── scheduler/
│   └── task_runner.py         # Background task scheduling
│
├── utils/
│   ├── logger.py              # Rotating log + @log_function_call
│   ├── helpers.py             # Shared utility functions
│   └── validators.py          # Input validation + custom exceptions
│
├── data/
│   ├── input/                 # Put your CSV/Excel files here
│   │   └── generate_samples.py
│   └── output/                # Reports are saved here automatically
│
├── tests/                     # pytest test suite (40+ tests)
├── logs/                      # Rotating log files
├── requirements.txt
└── .gitignore
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10 or newer ([download](https://python.org/downloads))
- Git ([download](https://git-scm.com))

### 2. Clone the repository

```bash
git clone https://github.com/PKrishnaS/business-workflow-automation.git
cd business-workflow-automation
```

### 3. Create a virtual environment (recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Set up your secrets (for email)

```bash
cp config/.env.example config/.env
# Now open config/.env and fill in your email credentials
```

### 6. Generate sample data

```bash
python data/input/generate_samples.py
```

### 7. Launch the app

```bash
python main.py
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=term-missing

# Run a specific test file
pytest tests/test_cleaner.py -v
```

---

## 📖 Module Usage (Code Examples)

### Clean a CSV file

```python
from data_processor.cleaner import DataCleaner

cleaner = DataCleaner("data/input/sales_data.csv")
df      = cleaner.load().clean().get_dataframe()
print(cleaner.get_summary())
cleaner.save("data/output/sales_clean.csv")
```

### Merge all CSVs in a folder

```python
from data_processor.merger import DataMerger

merger = DataMerger()
df     = merger.merge_folder("data/input/monthly_sales").get_dataframe()
merger.save("data/output/all_months.csv")
```

### Generate a PDF report

```python
from data_processor.cleaner import DataCleaner
from report_gen.pdf_report import PDFReport

df     = DataCleaner("data/input/sales_data.csv").load().clean().get_dataframe()
report = PDFReport(title="Q1 Sales Report", subtitle="January–March 2024")
report.add_cover_page()
report.add_summary_section({"Total Records": "300", "Total Revenue": "$48,250"})
report.add_dataframe_section("Sales Data", df.head(30))
path = report.save()
print(f"Saved: {path}")
```

### Generate an Excel report

```python
from report_gen.excel_report import ExcelReport

report = ExcelReport(title="Monthly Report")
report.add_summary_sheet({"Revenue": "$48,250", "Orders": "300"})
report.add_data_sheet("Raw Data", df)
report.save("monthly_report.xlsx")
```

### Organize files automatically

```python
from file_organizer.organizer import FileOrganizer

org = FileOrganizer("C:/Users/Me/Downloads", dry_run=True)  # Preview first
org.scan().organize()
print(org.generate_report())

# Then run for real:
org = FileOrganizer("C:/Users/Me/Downloads", dry_run=False)
org.scan().organize()
```

### Send an email with attachment

```python
from email_sender.mailer import Mailer

mailer = Mailer()
mailer.send(
    to="client@example.com",
    subject="Your Monthly Report",
    body="Please find your report attached.",
    attachments=["data/output/report.pdf"]
)
```

### Schedule daily tasks

```python
from scheduler.task_runner import TaskRunner

runner = TaskRunner()
runner.schedule_daily(my_report_function, at_time="08:00", job_name="Daily Report")
runner.start()   # Runs in background — your app keeps working
```

---

## ⚙️ Configuration

All settings are in `config/settings.py`. Key options:

| Setting | Default | Description |
|---|---|---|
| `PDF_PAGE_SIZE` | `"A4"` | PDF page size (`"A4"` or `"LETTER"`) |
| `PDF_PRIMARY_COLOR` | Blue | Branding color (R, G, B) |
| `SCHEDULER_DAILY_REPORT_TIME` | `"08:00"` | When daily reports run |
| `FILE_SORT_RULES` | dict | Maps extensions → folder names |
| `FEATURE_EMAIL_ENABLED` | `True` | Toggle email module |

Secrets (email passwords etc.) go in `config/.env` — never committed to Git.

---

## 🔧 Common Issues & Fixes

**`ModuleNotFoundError: No module named 'pandas'`**
```bash
pip install -r requirements.txt
```

**`ttkthemes not found` warning on startup**
```bash
pip install ttkthemes
```

**Gmail "Authentication failed"**
- Use an App Password, not your main Gmail password
- Enable 2-Step Verification in your Google account first
- [Get an App Password →](https://myaccount.google.com/apppasswords)

**PDF looks wrong / missing fonts**
```bash
pip install --upgrade reportlab Pillow
```

---

## 📦 Tech Stack

| Library | Version | Purpose |
|---|---|---|
| `pandas` | 2.x | Data manipulation |
| `openpyxl` | 3.x | Excel read/write |
| `reportlab` | 4.x | PDF generation |
| `tkinter` | built-in | GUI framework |
| `ttkthemes` | 3.x | GUI themes |
| `schedule` | 1.x | Task scheduling |
| `python-dotenv` | 1.x | Secrets management |
| `pytest` | 8.x | Testing |

---

## 📄 License

MIT License — free to use, modify, and sell to clients.

---

## 🤝 Contributing

Pull requests welcome. For major changes, open an issue first.
