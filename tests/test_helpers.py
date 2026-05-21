# ============================================================
# tests/test_helpers.py — Unit tests for utils/helpers.py
# ============================================================

import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.helpers import (
    get_timestamp, sanitize_filename, ensure_dir,
    get_file_size_str, format_number, chunk_list, find_files
)


class TestGetTimestamp:
    def test_returns_string(self):
        assert isinstance(get_timestamp(), str)

    def test_default_format(self):
        ts = get_timestamp()
        assert len(ts) == 15      # "20240515_142301" = 15 chars
        assert "_" in ts

    def test_custom_format(self):
        ts = get_timestamp("%Y")
        assert len(ts) == 4       # Just the year


class TestSanitizeFilename:
    def test_removes_special_chars(self):
        result = sanitize_filename("Hello: World/2024!")
        assert ":" not in result
        assert "/" not in result
        assert "!" not in result

    def test_replaces_spaces(self):
        result = sanitize_filename("my report")
        assert " " not in result
        assert "_" in result

    def test_handles_empty_string(self):
        result = sanitize_filename("")
        assert result == "unnamed"

    def test_max_length(self):
        long_name = "a" * 200
        result = sanitize_filename(long_name, max_length=50)
        assert len(result) <= 50


class TestFormatNumber:
    def test_basic(self):
        assert format_number(1234567.89) == "1,234,567.89"

    def test_zero_decimals(self):
        assert format_number(9500, decimals=0) == "9,500"

    def test_with_prefix(self):
        assert format_number(100, decimals=0, prefix="$") == "$100"

    def test_with_suffix(self):
        result = format_number(0.5, decimals=0, suffix="%")
        assert result.endswith("%")

    def test_invalid_input(self):
        # Should not crash, just return str(value)
        result = format_number("not_a_number")
        assert isinstance(result, str)


class TestChunkList:
    def test_even_split(self):
        result = chunk_list([1, 2, 3, 4], 2)
        assert result == [[1, 2], [3, 4]]

    def test_uneven_split(self):
        result = chunk_list([1, 2, 3, 4, 5], 2)
        assert result == [[1, 2], [3, 4], [5]]

    def test_empty_list(self):
        assert chunk_list([], 3) == []

    def test_chunk_larger_than_list(self):
        result = chunk_list([1, 2], 10)
        assert result == [[1, 2]]


class TestFindFiles:
    def test_finds_files(self, tmp_path):
        (tmp_path / "a.csv").write_text("data")
        (tmp_path / "b.xlsx").write_text("data")
        (tmp_path / "c.txt").write_text("data")

        result = find_files(tmp_path, extensions=[".csv", ".xlsx"])
        names  = [f.name for f in result]
        assert "a.csv"  in names
        assert "b.xlsx" in names
        assert "c.txt"  not in names

    def test_missing_directory(self, tmp_path):
        result = find_files(tmp_path / "nonexistent")
        assert result == []

    def test_returns_all_files_when_no_filter(self, tmp_path):
        (tmp_path / "a.csv").write_text("x")
        (tmp_path / "b.pdf").write_text("x")
        result = find_files(tmp_path)
        assert len(result) == 2


class TestEnsureDir:
    def test_creates_directory(self, tmp_path):
        new_dir = tmp_path / "level1" / "level2"
        assert not new_dir.exists()
        ensure_dir(new_dir)
        assert new_dir.exists()

    def test_existing_directory_ok(self, tmp_path):
        # Should not raise if directory already exists
        ensure_dir(tmp_path)
        assert tmp_path.exists()
