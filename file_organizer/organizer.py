# ============================================================
# file_organizer/organizer.py — Automatic file sorting
# ============================================================
# Scans a folder and moves files into organized subfolders
# based on their extension (e.g. .pdf → Documents/PDFs/)
# ============================================================

import shutil
from pathlib import Path
from datetime import datetime
from typing import Union

from config.settings import FILE_SORT_RULES, DATA_OUTPUT_DIR
from utils.logger import get_logger, log_function_call
from utils.helpers import get_timestamp

logger = get_logger(__name__)


class FileOrganizer:
    """
    Automatically sort files in a folder into categorized subfolders.

    HOW TO USE:
        organizer = FileOrganizer("C:/Users/Me/Downloads")
        result = organizer.scan().organize()
        print(result["files_moved"])
    """

    def __init__(self, source_dir: Union[str, Path],
                 dry_run: bool = False):
        """
        Args:
            source_dir: The folder to organize.
            dry_run:    If True, only SIMULATE (log what would happen, don't move anything).
                        Great for previewing before committing.
        """
        self.source_dir = Path(source_dir)
        self.dry_run    = dry_run
        self.file_plan: list[dict] = []   # What we plan to do with each file
        self.results:   dict       = {}

        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {self.source_dir}")

        mode = "DRY RUN — simulation only" if dry_run else "LIVE"
        logger.info(f"FileOrganizer initialized [{mode}]: {self.source_dir}")

    @log_function_call(logger)
    def scan(self) -> "FileOrganizer":
        """
        Scan the source directory and build a plan of what to move where.

        Does NOT move any files — just creates the plan.
        Call .organize() to execute the plan.

        Returns:
            self (for method chaining)
        """
        self.file_plan = []
        files_found = 0
        files_skipped = 0

        for item in self.source_dir.iterdir():
            # Skip directories and hidden files (files starting with .)
            if item.is_dir():
                continue
            if item.name.startswith("."):
                continue

            files_found += 1
            ext = item.suffix.lower()

            # Look up the destination folder for this extension
            if ext in FILE_SORT_RULES:
                destination_subfolder = FILE_SORT_RULES[ext]
                destination_dir = self.source_dir / destination_subfolder
                destination_path = destination_dir / item.name

                # Handle filename conflicts: if a file with this name already exists,
                # add a timestamp to make the name unique
                if destination_path.exists():
                    stem      = item.stem
                    timestamp = get_timestamp()
                    new_name  = f"{stem}_{timestamp}{ext}"
                    destination_path = destination_dir / new_name
                    logger.debug(f"Name conflict: renaming to '{new_name}'")

                self.file_plan.append({
                    "file":        item.name,
                    "source":      str(item),
                    "destination": str(destination_path),
                    "category":    destination_subfolder,
                    "size_bytes":  item.stat().st_size,
                    "action":      "move",
                })
            else:
                # Unknown extension — put in "Others" folder
                destination_dir  = self.source_dir / "Others"
                destination_path = destination_dir / item.name

                self.file_plan.append({
                    "file":        item.name,
                    "source":      str(item),
                    "destination": str(destination_path),
                    "category":    "Others",
                    "size_bytes":  item.stat().st_size,
                    "action":      "move",
                })
                files_skipped += 1
                logger.debug(f"Unknown extension '{ext}': will move to 'Others/'")

        logger.info(f"Scan complete: {files_found} files found ({files_skipped} with unknown extension)")
        return self

    @log_function_call(logger)
    def organize(self) -> dict:
        """
        Execute the plan built by .scan() — actually move the files.

        Returns:
            dict with keys: files_moved, files_failed, categories_created,
                            dry_run, details (list of what happened to each file)
        """
        if not self.file_plan:
            logger.warning("No files to organize. Call .scan() first.")
            return {"files_moved": 0, "files_failed": 0, "details": []}

        files_moved   = 0
        files_failed  = 0
        categories    = set()
        details       = []

        for plan in self.file_plan:
            source_path = Path(plan["source"])
            dest_path   = Path(plan["destination"])
            category    = plan["category"]

            try:
                if self.dry_run:
                    # Simulation mode: just log, don't touch files
                    logger.info(f"[DRY RUN] Would move: {plan['file']} → {category}/")
                    details.append({**plan, "status": "simulated"})
                    files_moved += 1
                else:
                    # Create the destination folder if it doesn't exist
                    dest_path.parent.mkdir(parents=True, exist_ok=True)

                    # Move the file
                    shutil.move(str(source_path), str(dest_path))
                    logger.info(f"Moved: {plan['file']} → {category}/")

                    details.append({**plan, "status": "moved"})
                    files_moved += 1

                categories.add(category)

            except Exception as e:
                logger.error(f"Failed to move '{plan['file']}': {e}")
                details.append({**plan, "status": "failed", "error": str(e)})
                files_failed += 1

        self.results = {
            "files_moved":        files_moved,
            "files_failed":       files_failed,
            "categories_created": list(categories),
            "dry_run":            self.dry_run,
            "source_directory":   str(self.source_dir),
            "timestamp":          datetime.now().isoformat(),
            "details":            details,
        }

        logger.info(
            f"Organization {'simulated' if self.dry_run else 'complete'}: "
            f"{files_moved} moved, {files_failed} failed"
        )
        return self.results

    def generate_report(self) -> str:
        """
        Return a human-readable text summary of the organization results.

        Returns:
            Multi-line string suitable for displaying in the GUI or saving to a file.
        """
        if not self.results:
            return "No results yet. Run .scan().organize() first."

        lines = [
            "=" * 60,
            "  FILE ORGANIZATION REPORT",
            "=" * 60,
            f"  Source:       {self.results['source_directory']}",
            f"  Timestamp:    {self.results['timestamp']}",
            f"  Mode:         {'DRY RUN (simulation)' if self.results['dry_run'] else 'LIVE'}",
            f"  Files moved:  {self.results['files_moved']}",
            f"  Files failed: {self.results['files_failed']}",
            "",
            "  Categories:",
        ]

        for cat in sorted(self.results["categories_created"]):
            count = sum(1 for d in self.results["details"] if d["category"] == cat)
            lines.append(f"    {cat}: {count} file(s)")

        if self.results["files_failed"] > 0:
            lines.append("")
            lines.append("  FAILURES:")
            for d in self.results["details"]:
                if d["status"] == "failed":
                    lines.append(f"    {d['file']}: {d.get('error', 'unknown error')}")

        lines.append("=" * 60)
        return "\n".join(lines)
