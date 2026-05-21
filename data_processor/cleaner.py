# ============================================================
# data_processor/cleaner.py — Data cleaning module
# ============================================================
# Takes raw, messy CSV/Excel files and produces clean DataFrames.
# "Cleaning" means:
#   - Removing duplicate rows
#   - Handling missing/blank values
#   - Fixing column name formatting
#   - Converting data types
#   - Removing junk columns
# ============================================================

import pandas as pd
from pathlib import Path
from typing import Optional, Union

from config.settings import (
    ALLOWED_INPUT_EXTENSIONS,
    COLUMNS_TO_DROP,
    FILL_NUMERIC_NAN_WITH,
    FILL_TEXT_NAN_WITH
)
from utils.logger import get_logger, log_function_call
from utils.validators import validate_file_exists, validate_file_extension, ValidationError

logger = get_logger(__name__)


class DataCleaner:
    """
    Loads and cleans a single data file (CSV or Excel).

    HOW TO USE:
        cleaner = DataCleaner("data/input/sales.csv")
        df = cleaner.load().clean().get_dataframe()

    This is called "method chaining" — each method returns `self`
    so you can chain calls with dots.
    """

    def __init__(self, filepath: Union[str, Path]):
        """
        Initialize the cleaner with a file path.

        Args:
            filepath: Path to a .csv, .xlsx, or .xls file.
        """
        self.filepath = Path(filepath)
        self.df: Optional[pd.DataFrame] = None     # Will hold the data after loading
        self.original_shape: tuple = (0, 0)         # (rows, columns) before cleaning
        self.cleaning_log: list[str] = []           # Track what changes were made

    @log_function_call(logger)
    def load(self) -> "DataCleaner":
        """
        Read the file into a pandas DataFrame.

        Supports .csv, .xlsx, .xls automatically.

        Returns:
            self (so you can chain: .load().clean())

        Raises:
            ValidationError: If the file doesn't exist or has wrong extension.
            Exception: If the file is corrupted or unreadable.
        """
        # Validate the file before trying to read it
        validate_file_exists(self.filepath)
        validate_file_extension(self.filepath, ALLOWED_INPUT_EXTENSIONS)

        ext = self.filepath.suffix.lower()

        try:
            if ext == ".csv":
                # Try UTF-8 first, fall back to latin-1 (handles special characters in European files)
                try:
                    self.df = pd.read_csv(self.filepath, encoding="utf-8")
                except UnicodeDecodeError:
                    logger.warning(f"UTF-8 failed for {self.filepath.name}, trying latin-1 encoding")
                    self.df = pd.read_csv(self.filepath, encoding="latin-1")

            elif ext in (".xlsx", ".xls"):
                self.df = pd.read_excel(self.filepath, engine="openpyxl" if ext == ".xlsx" else "xlrd")

            else:
                raise ValidationError(f"Unsupported file type: {ext}")

            self.original_shape = self.df.shape
            logger.info(f"Loaded '{self.filepath.name}': {self.df.shape[0]} rows × {self.df.shape[1]} columns")
            self.cleaning_log.append(f"Loaded file: {self.filepath.name} ({self.df.shape[0]} rows)")

        except Exception as e:
            logger.error(f"Failed to load '{self.filepath}': {e}")
            raise

        return self   # Return self for method chaining

    @log_function_call(logger)
    def clean(self) -> "DataCleaner":
        """
        Apply all cleaning steps to the loaded DataFrame.

        Steps applied in order:
          1. Standardize column names
          2. Drop known junk columns
          3. Remove completely empty rows
          4. Remove duplicate rows
          5. Fill missing values

        Returns:
            self (for method chaining)

        Raises:
            RuntimeError: If .load() was not called first.
        """
        if self.df is None:
            raise RuntimeError("Call .load() before .clean()")

        # ── Step 1: Standardize column names ────────────────
        # Strips whitespace, lowercases, and replaces spaces with underscores.
        # "First Name " → "first_name"
        original_cols = list(self.df.columns)
        self.df.columns = (
            self.df.columns
            .str.strip()
            .str.lower()
            .str.replace(r"\s+", "_", regex=True)
            .str.replace(r"[^\w]", "", regex=True)
        )
        renamed = [(o, n) for o, n in zip(original_cols, self.df.columns) if str(o) != str(n)]
        if renamed:
            logger.debug(f"Renamed {len(renamed)} columns: {renamed[:5]}{'...' if len(renamed) > 5 else ''}")
            self.cleaning_log.append(f"Standardized {len(renamed)} column names")

        # ── Step 2: Drop known junk columns ─────────────────
        # Pandas sometimes creates "Unnamed: 0" columns when saving without index=False
        drop_targets = [col for col in COLUMNS_TO_DROP if col in self.df.columns]
        if drop_targets:
            self.df.drop(columns=drop_targets, inplace=True)
            logger.info(f"Dropped {len(drop_targets)} junk columns: {drop_targets}")
            self.cleaning_log.append(f"Dropped columns: {drop_targets}")

        # ── Step 3: Remove completely empty rows ─────────────
        empty_row_count = self.df.isna().all(axis=1).sum()
        if empty_row_count > 0:
            self.df.dropna(how="all", inplace=True)
            self.df.reset_index(drop=True, inplace=True)
            logger.info(f"Removed {empty_row_count} completely empty rows")
            self.cleaning_log.append(f"Removed {empty_row_count} empty rows")

        # ── Step 4: Remove duplicate rows ────────────────────
        dup_count = self.df.duplicated().sum()
        if dup_count > 0:
            self.df.drop_duplicates(inplace=True)
            self.df.reset_index(drop=True, inplace=True)
            logger.info(f"Removed {dup_count} duplicate rows")
            self.cleaning_log.append(f"Removed {dup_count} duplicates")

        # ── Step 5: Fill missing values ──────────────────────
        # Numeric columns (int, float): fill blanks with 0
        # Text columns: fill blanks with "N/A"
        numeric_cols = self.df.select_dtypes(include="number").columns
        text_cols    = self.df.select_dtypes(exclude="number").columns

        if len(numeric_cols) > 0:
            self.df[numeric_cols] = self.df[numeric_cols].fillna(FILL_NUMERIC_NAN_WITH)

        if len(text_cols) > 0:
            self.df[text_cols] = self.df[text_cols].fillna(FILL_TEXT_NAN_WITH)

        final_rows = len(self.df)
        logger.info(f"Cleaning complete. Rows: {self.original_shape[0]} → {final_rows}")
        self.cleaning_log.append(f"Final shape: {self.df.shape[0]} rows × {self.df.shape[1]} cols")

        return self

    def get_dataframe(self) -> pd.DataFrame:
        """
        Return the cleaned DataFrame.

        Returns:
            pandas DataFrame

        Raises:
            RuntimeError: If no data has been loaded yet.
        """
        if self.df is None:
            raise RuntimeError("No data loaded. Call .load() first.")
        return self.df.copy()   # Return a copy so callers can't accidentally modify our data

    def get_summary(self) -> dict:
        """
        Return a summary of the loaded/cleaned data.

        Useful for showing statistics in the GUI dashboard.

        Returns:
            dict with keys: filename, original_rows, final_rows, columns,
                            missing_values, numeric_columns, text_columns,
                            cleaning_steps
        """
        if self.df is None:
            return {"error": "No data loaded"}

        return {
            "filename":        self.filepath.name,
            "original_rows":   self.original_shape[0],
            "original_cols":   self.original_shape[1],
            "final_rows":      len(self.df),
            "final_cols":      len(self.df.columns),
            "columns":         list(self.df.columns),
            "missing_values":  int(self.df.isna().sum().sum()),
            "numeric_columns": list(self.df.select_dtypes(include="number").columns),
            "text_columns":    list(self.df.select_dtypes(exclude="number").columns),
            "cleaning_steps":  self.cleaning_log,
        }

    def save(self, output_path: Union[str, Path], overwrite: bool = True) -> Path:
        """
        Save the cleaned DataFrame back to a file.

        Args:
            output_path: Where to save the file (.csv or .xlsx)
            overwrite:   If False, raises an error if file already exists.

        Returns:
            Path to the saved file.
        """
        if self.df is None:
            raise RuntimeError("No data to save. Call .load() and .clean() first.")

        output_path = Path(output_path)

        if not overwrite and output_path.exists():
            raise FileExistsError(f"File already exists: {output_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        ext = output_path.suffix.lower()

        if ext == ".csv":
            self.df.to_csv(output_path, index=False, encoding="utf-8")
        elif ext in (".xlsx", ".xls"):
            self.df.to_excel(output_path, index=False, engine="openpyxl")
        else:
            raise ValueError(f"Cannot save to '{ext}' format. Use .csv or .xlsx")

        logger.info(f"Saved cleaned data to: {output_path}")
        return output_path
