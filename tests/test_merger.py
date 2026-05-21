# ============================================================
# tests/test_merger.py — Unit tests for DataMerger
# ============================================================

import pytest
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_processor.merger import DataMerger
from utils.validators import ValidationError


@pytest.fixture
def two_csv_folder(tmp_path):
    """Create a folder with two compatible CSV files."""
    pd.DataFrame({"name": ["Alice", "Bob"], "sales": [100, 200]}).to_csv(
        tmp_path / "jan.csv", index=False)
    pd.DataFrame({"name": ["Carol", "Dave"], "sales": [300, 400]}).to_csv(
        tmp_path / "feb.csv", index=False)
    return tmp_path


class TestDataMerger:
    def test_stack_folder(self, two_csv_folder):
        merger = DataMerger()
        merger.merge_folder(two_csv_folder)
        df = merger.get_dataframe()
        assert len(df) == 4   # 2 rows from each file

    def test_source_column_added(self, two_csv_folder):
        merger = DataMerger()
        merger.merge_folder(two_csv_folder, add_source_column=True)
        df = merger.get_dataframe()
        assert "source_file" in df.columns

    def test_no_source_column(self, two_csv_folder):
        merger = DataMerger()
        merger.merge_folder(two_csv_folder, add_source_column=False)
        df = merger.get_dataframe()
        assert "source_file" not in df.columns

    def test_empty_folder_raises(self, tmp_path):
        with pytest.raises(ValidationError):
            DataMerger().merge_folder(tmp_path)

    def test_join_on_column(self, tmp_path):
        pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]}).to_csv(
            tmp_path / "a.csv", index=False)
        pd.DataFrame({"id": [1, 2], "score": [95, 87]}).to_csv(
            tmp_path / "b.csv", index=False)

        merger = DataMerger()
        merger.merge_files(
            [tmp_path / "a.csv", tmp_path / "b.csv"],
            join_on="id"
        )
        df = merger.get_dataframe()
        assert "name"  in df.columns
        assert "score" in df.columns
        assert len(df) == 2

    def test_save_csv(self, two_csv_folder, tmp_path):
        merger   = DataMerger()
        merger.merge_folder(two_csv_folder)
        out_path = tmp_path / "merged.csv"
        merger.save(out_path)
        assert out_path.exists()
        df = pd.read_csv(out_path)
        assert len(df) == 4

    def test_summary_keys(self, two_csv_folder):
        merger = DataMerger()
        merger.merge_folder(two_csv_folder)
        summary = merger.get_summary()
        for key in ["files_merged", "total_rows", "total_columns", "source_files"]:
            assert key in summary
