# ============================================================
# gui/dashboard.py — Main GUI Dashboard (Tkinter)
# ============================================================
# The visual window the user interacts with.
# Built with tkinter (built into Python) + ttkthemes (better styling).
# Split into tabs: Data, Reports, Files, Email, Scheduler, Logs
# ============================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from pathlib import Path
from datetime import datetime

# Try to import ttkthemes; if not installed, fall back to default style
try:
    from ttkthemes import ThemedTk
    HAS_THEMES = True
except ImportError:
    HAS_THEMES = False

from config.settings import (
    APP_TITLE, APP_VERSION, APP_WIDTH, APP_HEIGHT, APP_THEME,
    DATA_INPUT_DIR, DATA_OUTPUT_DIR, FEATURE_EMAIL_ENABLED,
    FEATURE_SCHEDULER_ENABLED
)
from utils.logger import get_logger

logger = get_logger(__name__)


class Dashboard:
    """
    The main application window.

    All GUI code lives here. The Dashboard talks to the core modules
    (DataCleaner, PDFReport, etc.) and displays results to the user.
    """

    def __init__(self):
        logger.info(f"Launching {APP_TITLE} v{APP_VERSION}")

        # ── Create the main window ───────────────────────────
        if HAS_THEMES:
            self.root = ThemedTk(theme=APP_THEME)
        else:
            self.root = tk.Tk()
            logger.warning("ttkthemes not installed. Using default style. Run: pip install ttkthemes")

        self.root.title(f"{APP_TITLE}  v{APP_VERSION}")
        self.root.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.root.minsize(800, 550)

        # Keep track of the currently selected input file
        self.selected_file = tk.StringVar(value="No file selected")
        self.status_text   = tk.StringVar(value="Ready")

        # Build the GUI
        self._build_menu()
        self._build_header()
        self._build_tabs()
        self._build_status_bar()

        logger.info("GUI initialized successfully")

    # ────────────────────────────────────────────────────────
    # TOP MENU BAR
    # ────────────────────────────────────────────────────────
    def _build_menu(self):
        """Build the top menu bar (File, Tools, Help)."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open File...",    command=self.browse_input_file)
        file_menu.add_command(label="Open Output Folder", command=self._open_output_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="View Logs", command=lambda: self.tabs.select(5))
        menubar.add_cascade(label="Help", menu=help_menu)

    # ────────────────────────────────────────────────────────
    # HEADER
    # ────────────────────────────────────────────────────────
    def _build_header(self):
        """Build the top banner with the app title."""
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=0, pady=0)

        # Blue banner
        banner = tk.Label(
            header_frame,
            text=f"  🗂  {APP_TITLE}",
            font=("Helvetica", 14, "bold"),
            bg="#2962FF",
            fg="white",
            padx=16,
            pady=10,
            anchor="w"
        )
        banner.pack(fill="x")

        version_label = tk.Label(
            header_frame,
            text=f"v{APP_VERSION}  |  Automate. Analyse. Report.",
            font=("Helvetica", 8),
            bg="#1a3fa8",
            fg="#a0b8ff",
            padx=16,
            pady=3,
            anchor="w"
        )
        version_label.pack(fill="x")

    # ────────────────────────────────────────────────────────
    # TABS
    # ────────────────────────────────────────────────────────
    def _build_tabs(self):
        """Build the main tabbed interface."""
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        # Create each tab
        self.tab_data      = ttk.Frame(self.tabs)
        self.tab_reports   = ttk.Frame(self.tabs)
        self.tab_files     = ttk.Frame(self.tabs)
        self.tab_email     = ttk.Frame(self.tabs)
        self.tab_scheduler = ttk.Frame(self.tabs)
        self.tab_logs      = ttk.Frame(self.tabs)

        self.tabs.add(self.tab_data,      text="📊  Data")
        self.tabs.add(self.tab_reports,   text="📄  Reports")
        self.tabs.add(self.tab_files,     text="🗂  Files")
        self.tabs.add(self.tab_email,     text="📧  Email")
        self.tabs.add(self.tab_scheduler, text="⏰  Scheduler")
        self.tabs.add(self.tab_logs,      text="📋  Logs")

        # Populate each tab
        self._build_data_tab()
        self._build_reports_tab()
        self._build_files_tab()
        self._build_email_tab()
        self._build_scheduler_tab()
        self._build_logs_tab()

    # ────────────────────────────────────────────────────────
    # TAB 1: DATA
    # ────────────────────────────────────────────────────────
    def _build_data_tab(self):
        """Data cleaning and merging tab."""
        tab = self.tab_data
        ttk.Label(tab, text="Data Processing", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        ttk.Separator(tab, orient="horizontal").pack(fill="x", padx=12)

        # File selection row
        file_frame = ttk.LabelFrame(tab, text="Input File", padding=8)
        file_frame.pack(fill="x", padx=12, pady=8)

        ttk.Label(file_frame, textvariable=self.selected_file,
                  wraplength=500, foreground="gray").pack(side="left", fill="x", expand=True)
        ttk.Button(file_frame, text="Browse...", command=self.browse_input_file).pack(side="right")

        # Action buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", padx=12, pady=4)

        ttk.Button(btn_frame, text="🧹  Clean Data",
                   command=self._run_clean_data).pack(side="left", padx=(0, 6))
        ttk.Button(btn_frame, text="🔗  Merge Folder",
                   command=self._run_merge_folder).pack(side="left", padx=(0, 6))
        ttk.Button(btn_frame, text="📊  Analyze",
                   command=self._run_analyze).pack(side="left")

        # Results area
        results_frame = ttk.LabelFrame(tab, text="Results", padding=8)
        results_frame.pack(fill="both", expand=True, padx=12, pady=8)

        self.data_results_text = scrolledtext.ScrolledText(
            results_frame, height=15, font=("Courier", 9), state="disabled"
        )
        self.data_results_text.pack(fill="both", expand=True)

    # ────────────────────────────────────────────────────────
    # TAB 2: REPORTS
    # ────────────────────────────────────────────────────────
    def _build_reports_tab(self):
        """PDF and Excel report generation tab."""
        tab = self.tab_reports
        ttk.Label(tab, text="Report Generation", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        ttk.Separator(tab, orient="horizontal").pack(fill="x", padx=12)

        # Report title input
        settings_frame = ttk.LabelFrame(tab, text="Report Settings", padding=8)
        settings_frame.pack(fill="x", padx=12, pady=8)

        ttk.Label(settings_frame, text="Report Title:").grid(row=0, column=0, sticky="w", pady=3)
        self.report_title_var = tk.StringVar(value="Business Report")
        ttk.Entry(settings_frame, textvariable=self.report_title_var, width=40).grid(
            row=0, column=1, sticky="ew", padx=(8, 0), pady=3)

        ttk.Label(settings_frame, text="Subtitle:").grid(row=1, column=0, sticky="w", pady=3)
        self.report_subtitle_var = tk.StringVar(value=datetime.now().strftime("%B %Y"))
        ttk.Entry(settings_frame, textvariable=self.report_subtitle_var, width=40).grid(
            row=1, column=1, sticky="ew", padx=(8, 0), pady=3)

        settings_frame.columnconfigure(1, weight=1)

        # Buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", padx=12, pady=4)

        ttk.Button(btn_frame, text="📄  Generate PDF Report",
                   command=self._run_generate_pdf).pack(side="left", padx=(0, 6))
        ttk.Button(btn_frame, text="📊  Generate Excel Report",
                   command=self._run_generate_excel).pack(side="left", padx=(0, 6))
        ttk.Button(btn_frame, text="📂  Open Output Folder",
                   command=self._open_output_folder).pack(side="left")

        # Results
        results_frame = ttk.LabelFrame(tab, text="Output", padding=8)
        results_frame.pack(fill="both", expand=True, padx=12, pady=8)

        self.report_results_text = scrolledtext.ScrolledText(
            results_frame, height=12, font=("Courier", 9), state="disabled"
        )
        self.report_results_text.pack(fill="both", expand=True)

    # ────────────────────────────────────────────────────────
    # TAB 3: FILES
    # ────────────────────────────────────────────────────────
    def _build_files_tab(self):
        """File organization tab."""
        tab = self.tab_files
        ttk.Label(tab, text="File Organizer", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        ttk.Separator(tab, orient="horizontal").pack(fill="x", padx=12)

        # Folder selection
        folder_frame = ttk.LabelFrame(tab, text="Target Folder", padding=8)
        folder_frame.pack(fill="x", padx=12, pady=8)

        self.organize_folder_var = tk.StringVar(value="Select a folder to organize...")
        ttk.Label(folder_frame, textvariable=self.organize_folder_var,
                  wraplength=500, foreground="gray").pack(side="left", fill="x", expand=True)
        ttk.Button(folder_frame, text="Browse...", command=self._browse_organize_folder).pack(side="right")

        # Options
        options_frame = ttk.LabelFrame(tab, text="Options", padding=8)
        options_frame.pack(fill="x", padx=12, pady=4)

        self.dry_run_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Dry Run (simulate only — don't actually move files)",
                        variable=self.dry_run_var).pack(anchor="w")

        # Buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", padx=12, pady=4)

        ttk.Button(btn_frame, text="🔍  Scan Folder",
                   command=self._run_scan_files).pack(side="left", padx=(0, 6))
        ttk.Button(btn_frame, text="🗂  Organize Files",
                   command=self._run_organize_files).pack(side="left")

        # Results
        results_frame = ttk.LabelFrame(tab, text="Results", padding=8)
        results_frame.pack(fill="both", expand=True, padx=12, pady=8)

        self.files_results_text = scrolledtext.ScrolledText(
            results_frame, height=12, font=("Courier", 9), state="disabled"
        )
        self.files_results_text.pack(fill="both", expand=True)

    # ────────────────────────────────────────────────────────
    # TAB 4: EMAIL
    # ────────────────────────────────────────────────────────
    def _build_email_tab(self):
        """Email sending tab."""
        tab = self.tab_email
        ttk.Label(tab, text="Email Automation", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        ttk.Separator(tab, orient="horizontal").pack(fill="x", padx=12)

        form_frame = ttk.LabelFrame(tab, text="Email Details", padding=8)
        form_frame.pack(fill="x", padx=12, pady=8)

        labels = ["To:", "Subject:", "Attachment:"]
        self.email_to_var      = tk.StringVar()
        self.email_subject_var = tk.StringVar(value="Automated Report")
        self.email_attach_var  = tk.StringVar(value="None selected")

        for i, (label, var) in enumerate(zip(labels, [self.email_to_var, self.email_subject_var, self.email_attach_var])):
            ttk.Label(form_frame, text=label).grid(row=i, column=0, sticky="w", pady=4)
            ttk.Entry(form_frame, textvariable=var, width=50).grid(row=i, column=1, sticky="ew", padx=(8, 0))

        form_frame.columnconfigure(1, weight=1)

        ttk.Button(form_frame, text="Browse...",
                   command=self._browse_attachment).grid(row=2, column=2, padx=(6, 0))

        ttk.Label(form_frame, text="Message:").grid(row=3, column=0, sticky="nw", pady=4)
        self.email_body_text = tk.Text(form_frame, height=5, width=50, font=("Helvetica", 10))
        self.email_body_text.insert("1.0", "Please find the attached report.")
        self.email_body_text.grid(row=3, column=1, sticky="ew", padx=(8, 0), columnspan=2)

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", padx=12, pady=4)

        ttk.Button(btn_frame, text="📧  Send Email",
                   command=self._run_send_email).pack(side="left", padx=(0, 6))

        # Status
        self.email_status_text = scrolledtext.ScrolledText(
            tab, height=8, font=("Courier", 9), state="disabled"
        )
        self.email_status_text.pack(fill="both", expand=True, padx=12, pady=8)

    # ────────────────────────────────────────────────────────
    # TAB 5: SCHEDULER
    # ────────────────────────────────────────────────────────
    def _build_scheduler_tab(self):
        """Scheduler status and control tab."""
        tab = self.tab_scheduler
        ttk.Label(tab, text="Task Scheduler", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        ttk.Separator(tab, orient="horizontal").pack(fill="x", padx=12)

        info_frame = ttk.LabelFrame(tab, text="Scheduler Status", padding=8)
        info_frame.pack(fill="x", padx=12, pady=8)

        self.scheduler_status_var = tk.StringVar(value="Not started")
        ttk.Label(info_frame, text="Status:").grid(row=0, column=0, sticky="w")
        ttk.Label(info_frame, textvariable=self.scheduler_status_var,
                  foreground="green").grid(row=0, column=1, sticky="w", padx=8)

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", padx=12, pady=4)

        ttk.Button(btn_frame, text="▶  Start Scheduler",
                   command=self._start_scheduler).pack(side="left", padx=(0, 6))
        ttk.Button(btn_frame, text="⏹  Stop Scheduler",
                   command=self._stop_scheduler).pack(side="left", padx=(0, 6))
        ttk.Button(btn_frame, text="▶▶  Run Report Now",
                   command=self._run_report_now).pack(side="left")

        jobs_frame = ttk.LabelFrame(tab, text="Scheduled Jobs", padding=8)
        jobs_frame.pack(fill="both", expand=True, padx=12, pady=8)

        self.scheduler_jobs_text = scrolledtext.ScrolledText(
            jobs_frame, height=10, font=("Courier", 9), state="disabled"
        )
        self.scheduler_jobs_text.pack(fill="both", expand=True)

    # ────────────────────────────────────────────────────────
    # TAB 6: LOGS
    # ────────────────────────────────────────────────────────
    def _build_logs_tab(self):
        """Live log viewer tab."""
        tab = self.tab_logs
        ttk.Label(tab, text="Application Logs", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        ttk.Separator(tab, orient="horizontal").pack(fill="x", padx=12)

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", padx=12, pady=4)

        ttk.Button(btn_frame, text="🔄  Refresh", command=self._refresh_logs).pack(side="left", padx=(0, 6))
        ttk.Button(btn_frame, text="🗑  Clear", command=self._clear_log_display).pack(side="left")

        self.log_text = scrolledtext.ScrolledText(
            tab, height=25, font=("Courier", 9), state="disabled",
            background="#1e1e1e", foreground="#d4d4d4"
        )
        self.log_text.pack(fill="both", expand=True, padx=12, pady=8)

        # Auto-load logs on first open
        self._refresh_logs()

    # ────────────────────────────────────────────────────────
    # STATUS BAR (bottom of window)
    # ────────────────────────────────────────────────────────
    def _build_status_bar(self):
        """Build the status bar at the bottom of the window."""
        status_bar = ttk.Frame(self.root)
        status_bar.pack(fill="x", side="bottom")
        ttk.Separator(status_bar, orient="horizontal").pack(fill="x")
        ttk.Label(status_bar, textvariable=self.status_text,
                  anchor="w", padding=(8, 3)).pack(side="left")
        ttk.Label(status_bar,
                  text=f"Output: {DATA_OUTPUT_DIR}",
                  anchor="e", padding=(8, 3), foreground="gray").pack(side="right")

    # ────────────────────────────────────────────────────────
    # HELPER: Write to a results text box
    # ────────────────────────────────────────────────────────
    def _write_to(self, widget: scrolledtext.ScrolledText, text: str, clear_first: bool = True):
        """Write text to a ScrolledText widget (enables/disables state correctly)."""
        widget.config(state="normal")
        if clear_first:
            widget.delete("1.0", "end")
        widget.insert("end", text + "\n")
        widget.see("end")   # Scroll to the bottom
        widget.config(state="disabled")

    def _set_status(self, message: str):
        """Update the status bar text."""
        self.status_text.set(f"  {message}")
        self.root.update_idletasks()   # Force GUI refresh

    # ────────────────────────────────────────────────────────
    # ACTIONS: Data Tab
    # ────────────────────────────────────────────────────────
    def browse_input_file(self):
        """Open file picker dialog."""
        path = filedialog.askopenfilename(
            title="Select a data file",
            filetypes=[("Data files", "*.csv *.xlsx *.xls"), ("All files", "*.*")],
            initialdir=str(DATA_INPUT_DIR)
        )
        if path:
            self.selected_file.set(path)
            self._set_status(f"Selected: {Path(path).name}")

    def _run_clean_data(self):
        """Run data cleaning in a background thread."""
        filepath = self.selected_file.get()
        if filepath == "No file selected" or not Path(filepath).exists():
            messagebox.showwarning("No File", "Please browse and select a data file first.")
            return

        def task():
            self._set_status("Cleaning data...")
            try:
                from data_processor.cleaner import DataCleaner
                cleaner = DataCleaner(filepath).load().clean()
                summary = cleaner.get_summary()

                output = [
                    "✓ Data Cleaning Complete",
                    "=" * 40,
                    f"File:           {summary['filename']}",
                    f"Original rows:  {summary['original_rows']:,}",
                    f"Final rows:     {summary['final_rows']:,}",
                    f"Columns:        {summary['final_cols']}",
                    f"Missing values: {summary['missing_values']}",
                    "",
                    "Columns: " + ", ".join(summary['columns']),
                    "",
                    "Cleaning steps:",
                ]
                for step in summary['cleaning_steps']:
                    output.append(f"  • {step}")

                # Save the cleaned file
                out_path = DATA_OUTPUT_DIR / f"cleaned_{Path(filepath).name}"
                cleaner.save(out_path)
                output.append(f"\n✓ Saved to: {out_path}")

                self._write_to(self.data_results_text, "\n".join(output))
                self._set_status("Data cleaning complete")

            except Exception as e:
                self._write_to(self.data_results_text, f"✗ Error: {e}")
                self._set_status("Error during cleaning")
                logger.error(f"GUI error in clean task: {e}")

        threading.Thread(target=task, daemon=True).start()

    def _run_merge_folder(self):
        """Merge all files in a folder."""
        folder = filedialog.askdirectory(title="Select folder with files to merge",
                                         initialdir=str(DATA_INPUT_DIR))
        if not folder:
            return

        def task():
            self._set_status("Merging files...")
            try:
                from data_processor.merger import DataMerger
                merger = DataMerger()
                merger.merge_folder(folder)
                summary = merger.get_summary()

                out_path = DATA_OUTPUT_DIR / f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                merger.save(out_path)

                output = [
                    "✓ Merge Complete",
                    "=" * 40,
                    f"Files merged:  {summary['files_merged']}",
                    f"Total rows:    {summary['total_rows']:,}",
                    f"Total columns: {summary['total_columns']}",
                    "",
                    "Source files:",
                ]
                for f in summary['source_files']:
                    output.append(f"  • {f}")
                output.append(f"\n✓ Saved to: {out_path}")

                self._write_to(self.data_results_text, "\n".join(output))
                self._set_status("Merge complete")

            except Exception as e:
                self._write_to(self.data_results_text, f"✗ Error: {e}")
                self._set_status("Error during merge")

        threading.Thread(target=task, daemon=True).start()

    def _run_analyze(self):
        """Run analysis on the selected file."""
        filepath = self.selected_file.get()
        if filepath == "No file selected":
            messagebox.showwarning("No File", "Please select a file first.")
            return

        def task():
            self._set_status("Analyzing data...")
            try:
                from data_processor.cleaner import DataCleaner
                from data_processor.analyzer import DataAnalyzer
                df = DataCleaner(filepath).load().clean().get_dataframe()
                analyzer = DataAnalyzer(df, label=Path(filepath).name)
                analyzer.analyze()
                results = analyzer.get_results()

                output = [
                    "✓ Analysis Complete",
                    "=" * 40,
                    f"Rows:    {results['row_count']:,}",
                    f"Columns: {results['col_count']}",
                    "",
                    "Numeric column statistics:",
                ]
                for col, stats in results['numeric_summary'].items():
                    output.append(f"  {col}:")
                    output.append(f"    min={stats['min']}, max={stats['max']}, mean={stats['mean']}, sum={stats['sum']}")

                if results['categorical_summary']:
                    output.append("\nTop values (text columns):")
                    for col, info in list(results['categorical_summary'].items())[:3]:
                        output.append(f"  {col}: {list(info['top_5'].keys())[:3]}")

                self._write_to(self.data_results_text, "\n".join(output))
                self._set_status("Analysis complete")

            except Exception as e:
                self._write_to(self.data_results_text, f"✗ Error: {e}")
                self._set_status("Error during analysis")

        threading.Thread(target=task, daemon=True).start()

    # ────────────────────────────────────────────────────────
    # ACTIONS: Reports Tab
    # ────────────────────────────────────────────────────────
    def _run_generate_pdf(self):
        filepath = self.selected_file.get()
        title    = self.report_title_var.get() or "Business Report"
        subtitle = self.report_subtitle_var.get()

        if filepath == "No file selected":
            messagebox.showwarning("No File", "Please select a data file first.")
            return

        def task():
            self._set_status("Generating PDF...")
            try:
                from data_processor.cleaner import DataCleaner
                from data_processor.analyzer import DataAnalyzer
                from report_gen.pdf_report import PDFReport
                from utils.helpers import format_number

                df = DataCleaner(filepath).load().clean().get_dataframe()
                analyzer = DataAnalyzer(df).analyze()
                results  = analyzer.get_results()

                # Build summary metrics dict
                metrics = {
                    "Total Records": format_number(results['row_count'], 0),
                    "Total Columns": results['col_count'],
                }
                for col, stats in list(results['numeric_summary'].items())[:4]:
                    clean_col = col.replace("_", " ").title()
                    metrics[f"Total {clean_col}"]   = format_number(stats['sum'])
                    metrics[f"Average {clean_col}"] = format_number(stats['mean'])

                report = PDFReport(title=title, subtitle=subtitle)
                report.add_cover_page()
                report.add_summary_section(metrics)
                report.add_dataframe_section("Data Preview", df)

                out_path = report.save()

                self._write_to(self.report_results_text,
                               f"✓ PDF report generated!\n\nSaved to:\n  {out_path}\n\n"
                               f"Pages: see file  |  Size: see file")
                self._set_status(f"PDF saved: {out_path.name}")
                messagebox.showinfo("Success", f"PDF report saved to:\n{out_path}")

            except Exception as e:
                self._write_to(self.report_results_text, f"✗ Error: {e}")
                self._set_status("Error generating PDF")
                logger.error(f"PDF generation error: {e}", exc_info=True)

        threading.Thread(target=task, daemon=True).start()

    def _run_generate_excel(self):
        filepath = self.selected_file.get()
        title    = self.report_title_var.get() or "Business Report"

        if filepath == "No file selected":
            messagebox.showwarning("No File", "Please select a data file first.")
            return

        def task():
            self._set_status("Generating Excel report...")
            try:
                from data_processor.cleaner import DataCleaner
                from data_processor.analyzer import DataAnalyzer
                from report_gen.excel_report import ExcelReport

                df      = DataCleaner(filepath).load().clean().get_dataframe()
                results = DataAnalyzer(df).analyze().get_results()

                metrics = {
                    "Total Records": f"{results['row_count']:,}",
                    "Total Columns": results['col_count'],
                    "Source File":   Path(filepath).name,
                    "Generated":     datetime.now().strftime("%d %B %Y"),
                }
                for col, stats in list(results['numeric_summary'].items())[:3]:
                    metrics[col.replace("_", " ").title() + " (sum)"] = f"{stats['sum']:,.2f}"

                report = ExcelReport(title=title)
                report.add_summary_sheet(metrics)
                report.add_data_sheet("Cleaned Data", df)

                out_path = report.save()
                self._write_to(self.report_results_text,
                               f"✓ Excel report generated!\n\nSaved to:\n  {out_path}")
                self._set_status(f"Excel saved: {out_path.name}")
                messagebox.showinfo("Success", f"Excel report saved to:\n{out_path}")

            except Exception as e:
                self._write_to(self.report_results_text, f"✗ Error: {e}")
                self._set_status("Error generating Excel")

        threading.Thread(target=task, daemon=True).start()

    # ────────────────────────────────────────────────────────
    # ACTIONS: Files Tab
    # ────────────────────────────────────────────────────────
    def _browse_organize_folder(self):
        folder = filedialog.askdirectory(title="Select folder to organize")
        if folder:
            self.organize_folder_var.set(folder)

    def _run_scan_files(self):
        folder = self.organize_folder_var.get()
        if "Select a folder" in folder:
            messagebox.showwarning("No Folder", "Please select a folder first.")
            return

        def task():
            from file_organizer.organizer import FileOrganizer
            try:
                org = FileOrganizer(folder, dry_run=True)
                org.scan()
                lines = [f"Found {len(org.file_plan)} files:\n"]
                for p in org.file_plan[:30]:
                    lines.append(f"  {p['file']} → {p['category']}/")
                if len(org.file_plan) > 30:
                    lines.append(f"  ... and {len(org.file_plan) - 30} more")
                self._write_to(self.files_results_text, "\n".join(lines))
                self._set_status("Scan complete")
            except Exception as e:
                self._write_to(self.files_results_text, f"✗ Error: {e}")

        threading.Thread(target=task, daemon=True).start()

    def _run_organize_files(self):
        folder  = self.organize_folder_var.get()
        dry_run = self.dry_run_var.get()

        if "Select a folder" in folder:
            messagebox.showwarning("No Folder", "Please select a folder first.")
            return

        if not dry_run:
            if not messagebox.askyesno("Confirm",
                "This will MOVE files. Make sure you have a backup.\nContinue?"):
                return

        def task():
            from file_organizer.organizer import FileOrganizer
            try:
                org = FileOrganizer(folder, dry_run=dry_run)
                org.scan().organize()
                report = org.generate_report()
                self._write_to(self.files_results_text, report)
                self._set_status("Files organized" if not dry_run else "Simulation complete")
            except Exception as e:
                self._write_to(self.files_results_text, f"✗ Error: {e}")

        threading.Thread(target=task, daemon=True).start()

    # ────────────────────────────────────────────────────────
    # ACTIONS: Email Tab
    # ────────────────────────────────────────────────────────
    def _browse_attachment(self):
        path = filedialog.askopenfilename(title="Select file to attach",
                                          initialdir=str(DATA_OUTPUT_DIR))
        if path:
            self.email_attach_var.set(path)

    def _run_send_email(self):
        to      = self.email_to_var.get().strip()
        subject = self.email_subject_var.get().strip()
        body    = self.email_body_text.get("1.0", "end").strip()
        attach  = self.email_attach_var.get()

        if not to:
            messagebox.showwarning("Missing Field", "Please enter a recipient email address.")
            return

        def task():
            self._set_status("Sending email...")
            try:
                from email_sender.mailer import Mailer
                mailer = Mailer()
                attachments = [attach] if attach and attach != "None selected" else None
                success = mailer.send(to=to, subject=subject, body=body, attachments=attachments)
                if success:
                    self._write_to(self.email_status_text, f"✓ Email sent to {to}")
                    self._set_status(f"Email sent to {to}")
                else:
                    self._write_to(self.email_status_text, "✗ Email failed. Check logs.")
                    self._set_status("Email failed")
            except Exception as e:
                self._write_to(self.email_status_text, f"✗ Error: {e}")
                self._set_status("Email error")

        threading.Thread(target=task, daemon=True).start()

    # ────────────────────────────────────────────────────────
    # ACTIONS: Scheduler Tab
    # ────────────────────────────────────────────────────────
    def _start_scheduler(self):
        try:
            from scheduler.task_runner import TaskRunner
            self._task_runner = TaskRunner()

            def daily_report():
                """The actual task that runs on schedule."""
                logger.info("Scheduled daily report task running...")
                # Add your automated report logic here

            self._task_runner.schedule_daily(daily_report, job_name="Daily Report")
            self._task_runner.start()
            self.scheduler_status_var.set("Running ✓")
            self._write_to(self.scheduler_jobs_text, self._task_runner.get_scheduled_jobs_text())
            self._set_status("Scheduler started")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start scheduler: {e}")

    def _stop_scheduler(self):
        if hasattr(self, "_task_runner"):
            self._task_runner.stop()
            self.scheduler_status_var.set("Stopped")
            self._set_status("Scheduler stopped")

    def _run_report_now(self):
        if hasattr(self, "_task_runner"):
            self._task_runner.run_now(lambda: logger.info("Manual run triggered from GUI"))
            self._set_status("Manual run triggered")

    # ────────────────────────────────────────────────────────
    # ACTIONS: Logs Tab
    # ────────────────────────────────────────────────────────
    def _refresh_logs(self):
        from config.settings import LOG_FILE
        try:
            if Path(LOG_FILE).exists():
                with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
                    # Read last 100 lines (logs can be very long)
                    lines = f.readlines()[-100:]
                content = "".join(lines) if lines else "(Log file is empty)"
            else:
                content = "(Log file not yet created — it appears after first action)"
            self._write_to(self.log_text, content)
        except Exception as e:
            self._write_to(self.log_text, f"Could not read log file: {e}")

    def _clear_log_display(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    # ────────────────────────────────────────────────────────
    # UTILITIES
    # ────────────────────────────────────────────────────────
    def _open_output_folder(self):
        """Open the output folder in the system file explorer."""
        import subprocess, sys
        folder = str(DATA_OUTPUT_DIR)
        if sys.platform == "win32":
            subprocess.Popen(f'explorer "{folder}"')
        elif sys.platform == "darwin":   # macOS
            subprocess.Popen(["open", folder])
        else:   # Linux
            subprocess.Popen(["xdg-open", folder])

    def _show_about(self):
        messagebox.showinfo(
            "About",
            f"{APP_TITLE}\n"
            f"Version {APP_VERSION}\n\n"
            "A modular Python automation suite for:\n"
            "• Excel/CSV data processing\n"
            "• PDF & Excel report generation\n"
            "• File organization\n"
            "• Email automation\n"
            "• Scheduled tasks\n\n"
            "Built with Python, pandas, ReportLab, tkinter"
        )

    # ────────────────────────────────────────────────────────
    # LAUNCH
    # ────────────────────────────────────────────────────────
    def run(self):
        """Start the GUI event loop. This call blocks until the window is closed."""
        logger.info("Starting GUI event loop")
        self.root.mainloop()
        logger.info("GUI closed")
