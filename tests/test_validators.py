# ============================================================
# tests/test_validators.py — Unit tests for utils/validators.py
# ============================================================

import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.validators import (
    validate_file_exists, validate_file_extension,
    validate_email, validate_directory,
    validate_positive_number, ValidationError
)


class TestValidateFileExists:
    def test_valid_file(self, tmp_path):
        f = tmp_path / "test.csv"
        f.write_text("data")
        result = validate_file_exists(f)
        assert result == f

    def test_missing_file(self, tmp_path):
        with pytest.raises(ValidationError, match="not found"):
            validate_file_exists(tmp_path / "ghost.csv")

    def test_directory_raises(self, tmp_path):
        with pytest.raises(ValidationError, match="folder"):
            validate_file_exists(tmp_path)


class TestValidateFileExtension:
    def test_allowed_extension(self, tmp_path):
        f = tmp_path / "data.csv"
        f.write_text("x")
        result = validate_file_extension(f, [".csv", ".xlsx"])
        assert result == f

    def test_disallowed_extension(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text("x")
        with pytest.raises(ValidationError, match="unsupported"):
            validate_file_extension(f, [".csv", ".xlsx"])

    def test_case_insensitive(self, tmp_path):
        f = tmp_path / "data.CSV"
        f.write_text("x")
        result = validate_file_extension(f, [".csv"])
        assert result == f


class TestValidateEmail:
    def test_valid_email(self):
        assert validate_email("user@example.com") == "user@example.com"

    def test_strips_whitespace(self):
        assert validate_email("  user@example.com  ") == "user@example.com"

    def test_invalid_no_at(self):
        with pytest.raises(ValidationError):
            validate_email("notanemail.com")

    def test_invalid_no_domain(self):
        with pytest.raises(ValidationError):
            validate_email("user@")

    def test_invalid_empty(self):
        with pytest.raises(ValidationError):
            validate_email("")


class TestValidatePositiveNumber:
    def test_integer(self):
        assert validate_positive_number(5) == 5.0

    def test_float_string(self):
        assert validate_positive_number("3.14") == 3.14

    def test_zero_raises(self):
        with pytest.raises(ValidationError, match="greater than zero"):
            validate_positive_number(0)

    def test_negative_raises(self):
        with pytest.raises(ValidationError):
            validate_positive_number(-1)

    def test_non_numeric_raises(self):
        with pytest.raises(ValidationError, match="must be a number"):
            validate_positive_number("abc")
