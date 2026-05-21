# ============================================================
# tests/test_organizer.py — Unit tests for FileOrganizer
# ============================================================

import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_organizer.organizer import FileOrganizer


@pytest.fixture
def messy_folder(tmp_path):
    """Create a folder with mixed file types."""
    (tmp_path / "report.pdf").write_bytes(b"pdf content")
    (tmp_path / "data.csv").write_bytes(b"csv content")
    (tmp_path / "photo.jpg").write_bytes(b"jpg content")
    (tmp_path / "notes.txt").write_bytes(b"txt content")
    (tmp_path / "archive.zip").write_bytes(b"zip content")
    (tmp_path / "unknown.xyz").write_bytes(b"unknown")
    return tmp_path


class TestFileOrganizer:
    def test_scan_finds_files(self, messy_folder):
        org = FileOrganizer(messy_folder, dry_run=True)
        org.scan()
        assert len(org.file_plan) == 6

    def test_dry_run_does_not_move(self, messy_folder):
        org = FileOrganizer(messy_folder, dry_run=True)
        org.scan().organize()
        # In dry run, original files should still be there
        assert (messy_folder / "report.pdf").exists()
        assert (messy_folder / "data.csv").exists()

    def test_live_run_moves_files(self, messy_folder):
        org = FileOrganizer(messy_folder, dry_run=False)
        org.scan().organize()
        # Files should now be in subfolders, not root
        assert not (messy_folder / "report.pdf").exists()
        assert (messy_folder / "Documents" / "PDFs" / "report.pdf").exists()

    def test_csv_goes_to_spreadsheets(self, messy_folder):
        org = FileOrganizer(messy_folder, dry_run=False)
        org.scan().organize()
        assert (messy_folder / "Spreadsheets" / "data.csv").exists()

    def test_unknown_extension_goes_to_others(self, messy_folder):
        org = FileOrganizer(messy_folder, dry_run=False)
        org.scan().organize()
        assert (messy_folder / "Others" / "unknown.xyz").exists()

    def test_results_dict_has_expected_keys(self, messy_folder):
        org     = FileOrganizer(messy_folder, dry_run=True)
        results = org.scan().organize()
        for key in ["files_moved", "files_failed", "categories_created", "dry_run"]:
            assert key in results

    def test_nonexistent_directory_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            FileOrganizer(tmp_path / "does_not_exist")

    def test_generate_report_returns_string(self, messy_folder):
        org = FileOrganizer(messy_folder, dry_run=True)
        org.scan().organize()
        report = org.generate_report()
        assert isinstance(report, str)
        assert "FILES MOVED" in report or "FILE ORGANIZATION" in report
