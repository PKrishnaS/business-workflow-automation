# ============================================================
# tests/test_cleaner.py — Unit tests for DataCleaner
# ============================================================
# Run with:  pytest tests/ -v
# ============================================================

import pytest
import pandas as pd
import tempfile
from pathlib import Path

# Add project root to path so imports work
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_processor.cleaner import DataCleaner
from utils.validators import ValidationError


# ── Fixtures: reusable test data ──────────────────────────────
@pytest.fixture
def sample_csv(tmp_path):
    """Create a temporary CSV file for testing."""
    content = """Name,Sales,Region,Score
Alice,100,North,9.5
Bob,200,South,8.0
Alice,100,North,9.5
,,, 
Charlie,300,,7.5
"""
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(content)
    return csv_file


@pytest.fixture
def sample_xlsx(tmp_path):
    """Create a temporary Excel file for testing."""
    df = pd.DataFrame({
        "First Name ": ["Alice", "Bob", "Bob"],
        "Sales":       [100, 200, 200],
        "Region":      ["North", "South", "South"],
    })
    xlsx_file = tmp_path / "test_data.xlsx"
    df.to_excel(xlsx_file, index=False)
    return xlsx_file


# ── Tests ─────────────────────────────────────────────────────
class TestDataCleaner:

    def test_load_csv(self, sample_csv):
        """DataCleaner should load a CSV without errors."""
        cleaner = DataCleaner(sample_csv).load()
        assert cleaner.df is not None
        assert len(cleaner.df) > 0

    def test_load_xlsx(self, sample_xlsx):
        """DataCleaner should load an Excel file without errors."""
        cleaner = DataCleaner(sample_xlsx).load()
        assert cleaner.df is not None

    def test_load_nonexistent_file(self, tmp_path):
        """Loading a missing file should raise ValidationError."""
        with pytest.raises(ValidationError):
            DataCleaner(tmp_path / "ghost.csv").load()

    def test_load_wrong_extension(self, tmp_path):
        """Loading an unsupported file type should raise ValidationError."""
        bad_file = tmp_path / "data.json"
        bad_file.write_text('{"key": "value"}')
        with pytest.raises(ValidationError):
            DataCleaner(bad_file).load()

    def test_removes_duplicates(self, sample_csv):
        """Clean should remove duplicate rows."""
        cleaner = DataCleaner(sample_csv).load().clean()
        df = cleaner.get_dataframe()
        # The CSV has Alice duplicated — after cleaning, no duplicates
        assert not df.duplicated().any()

    def test_removes_empty_rows(self, sample_csv):
        """Clean should remove completely empty rows."""
        cleaner = DataCleaner(sample_csv).load().clean()
        df = cleaner.get_dataframe()
        # No row should be entirely NaN
        assert not df.isna().all(axis=1).any()

    def test_column_names_normalized(self, sample_xlsx):
        """Clean should standardize column names to snake_case."""
        cleaner = DataCleaner(sample_xlsx).load().clean()
        df = cleaner.get_dataframe()
        for col in df.columns:
            assert col == col.lower(), f"Column '{col}' should be lowercase"
            assert " " not in col, f"Column '{col}' should not have spaces"

    def test_numeric_nan_filled(self, sample_csv):
        """Missing numeric values should be filled with 0."""
        cleaner = DataCleaner(sample_csv).load().clean()
        df = cleaner.get_dataframe()
        numeric_cols = df.select_dtypes(include="number").columns
        for col in numeric_cols:
            assert df[col].isna().sum() == 0, f"Column '{col}' still has NaN after cleaning"

    def test_get_summary_returns_dict(self, sample_csv):
        """get_summary() should return a dict with expected keys."""
        cleaner = DataCleaner(sample_csv).load().clean()
        summary = cleaner.get_summary()
        for key in ["filename", "original_rows", "final_rows", "columns", "cleaning_steps"]:
            assert key in summary, f"Missing key in summary: {key}"

    def test_save_csv(self, sample_csv, tmp_path):
        """save() should create a CSV file at the given path."""
        cleaner   = DataCleaner(sample_csv).load().clean()
        out_path  = tmp_path / "cleaned.csv"
        saved     = cleaner.save(out_path)
        assert saved.exists()
        df_reload = pd.read_csv(saved)
        assert len(df_reload) > 0

    def test_save_xlsx(self, sample_csv, tmp_path):
        """save() should create an Excel file."""
        cleaner  = DataCleaner(sample_csv).load().clean()
        out_path = tmp_path / "cleaned.xlsx"
        saved    = cleaner.save(out_path)
        assert saved.exists()

    def test_clean_without_load_raises(self, sample_csv):
        """Calling clean() before load() should raise RuntimeError."""
        with pytest.raises(RuntimeError):
            DataCleaner(sample_csv).clean()

    def test_get_dataframe_without_load_raises(self, sample_csv):
        """get_dataframe() before load() should raise RuntimeError."""
        with pytest.raises(RuntimeError):
            DataCleaner(sample_csv).get_dataframe()
