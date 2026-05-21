# ============================================================
# tests/conftest.py — Shared pytest configuration
# ============================================================
# pytest automatically reads this file before running tests.
# Fixtures defined here are available to ALL test files.
# ============================================================

import sys
import pytest
import pandas as pd
from pathlib import Path

# Ensure the project root is on sys.path so imports work in tests
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def sample_dataframe():
    """A clean sample DataFrame shared across all tests."""
    return pd.DataFrame({
        "name":   ["Alice", "Bob", "Carol", "Dave", "Eve"],
        "region": ["North", "South", "East", "West", "North"],
        "sales":  [100.0, 200.0, 150.0, 300.0, 250.0],
        "month":  ["Jan", "Jan", "Feb", "Feb", "Mar"],
    })


@pytest.fixture
def temp_csv(tmp_path, sample_dataframe):
    """Write the sample DataFrame to a temp CSV file and return its path."""
    path = tmp_path / "sample.csv"
    sample_dataframe.to_csv(path, index=False)
    return path


@pytest.fixture
def temp_xlsx(tmp_path, sample_dataframe):
    """Write the sample DataFrame to a temp Excel file and return its path."""
    path = tmp_path / "sample.xlsx"
    sample_dataframe.to_excel(path, index=False)
    return path
