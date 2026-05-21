# ============================================================
# data_processor/merger.py — Merge multiple data files into one
# ============================================================
# Common client task: "I have 12 monthly CSV files, combine them
# into one master spreadsheet."
# This module handles that automatically.
# ============================================================

import pandas as pd
from pathlib import Path
from typing import Union

from utils.logger import get_logger, log_function_call
from utils.helpers import find_files
from utils.validators import validate_directory, ValidationError
from data_processor.cleaner import DataCleaner

logger = get_logger(__name__)


class DataMerger:
    """
    Merge multiple CSV/Excel files into a single DataFrame.

    Supports two merge strategies:
      - "stack" (default): Append all files vertically (like stacking spreadsheets)
      - "join": Merge files side-by-side on a common column (like SQL JOIN)

    HOW TO USE:
        # Stack all CSVs in a folder into one DataFrame:
        merger = DataMerger()
        df = merger.merge_folder("data/input/monthly_reports").get_dataframe()

        # Join two files on a common "customer_id" column:
        df = merger.merge_files(["customers.xlsx", "orders.xlsx"],
                                join_on="customer_id").get_dataframe()
    """

    def __init__(self):
        self.df: pd.DataFrame = pd.DataFrame()
        self.source_files: list[str] = []
        self.merge_log: list[str] = []

    @log_function_call(logger)
    def merge_folder(self, folder: Union[str, Path],
                     extensions: list[str] = None,
                     add_source_column: bool = True) -> "DataMerger":
        """
        Load and vertically stack ALL matching files in a folder.

        Args:
            folder:            Path to the folder containing data files.
            extensions:        File types to include (default: .csv, .xlsx, .xls)
            add_source_column: If True, adds a "source_file" column so you can
                               tell which row came from which file.

        Returns:
            self (for method chaining)
        """
        validate_directory(folder)

        if extensions is None:
            extensions = [".csv", ".xlsx", ".xls"]

        files = find_files(folder, extensions=extensions, recursive=False)

        if not files:
            raise ValidationError(f"No matching files found in: {folder}")

        logger.info(f"Found {len(files)} files to merge in '{folder}'")
        return self.merge_files(files, add_source_column=add_source_column)

    @log_function_call(logger)
    def merge_files(self, filepaths: list[Union[str, Path]],
                    join_on: str = None,
                    how: str = "outer",
                    add_source_column: bool = True) -> "DataMerger":
        """
        Load and merge a specific list of files.

        Args:
            filepaths:         List of file paths to merge.
            join_on:           Column name to join on. If None, files are stacked vertically.
            how:               Join type: "outer" (keep all rows), "inner" (only matching rows),
                               "left" (keep all rows from first file).
            add_source_column: Add a "source_file" column (only for vertical stacking).

        Returns:
            self (for method chaining)
        """
        if not filepaths:
            raise ValidationError("No files provided to merge")

        dataframes = []
        self.source_files = []

        # ── Load and clean each file ─────────────────────────
        for fp in filepaths:
            fp = Path(fp)
            logger.info(f"Loading: {fp.name}")
            try:
                cleaner = DataCleaner(fp).load().clean()
                df = cleaner.get_dataframe()

                if add_source_column and join_on is None:
                    df["source_file"] = fp.name   # Track which file each row came from

                dataframes.append(df)
                self.source_files.append(fp.name)

            except Exception as e:
                logger.error(f"Skipping '{fp.name}' due to error: {e}")
                self.merge_log.append(f"SKIPPED: {fp.name} — {e}")

        if not dataframes:
            raise RuntimeError("All files failed to load. Nothing to merge.")

        # ── Merge strategy ───────────────────────────────────
        if join_on is None:
            # STACK: vertically concatenate all DataFrames
            # ignore_index=True renumbers rows from 0,1,2... instead of repeating
            self.df = pd.concat(dataframes, ignore_index=True, sort=False)
            logger.info(f"Stacked {len(dataframes)} files → {len(self.df)} total rows")
            self.merge_log.append(f"Stacked {len(dataframes)} files: {len(self.df)} rows")

        else:
            # JOIN: merge DataFrames on a common column (like a SQL JOIN)
            if len(dataframes) < 2:
                self.df = dataframes[0]
            else:
                self.df = dataframes[0]
                for i, df in enumerate(dataframes[1:], start=2):
                    before = len(self.df)
                    self.df = pd.merge(self.df, df, on=join_on, how=how)
                    logger.info(f"Joined file {i} on '{join_on}': {before} → {len(self.df)} rows")

                self.merge_log.append(
                    f"Joined {len(dataframes)} files on '{join_on}' ({how}): {len(self.df)} rows"
                )

        return self

    def get_dataframe(self) -> pd.DataFrame:
        """Return the merged DataFrame."""
        if self.df.empty:
            raise RuntimeError("No data merged yet. Call .merge_folder() or .merge_files() first.")
        return self.df.copy()

    def save(self, output_path: Union[str, Path]) -> Path:
        """Save the merged DataFrame to a file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        ext = output_path.suffix.lower()

        if ext == ".csv":
            self.df.to_csv(output_path, index=False, encoding="utf-8")
        elif ext in (".xlsx",):
            self.df.to_excel(output_path, index=False, engine="openpyxl")
        else:
            raise ValueError(f"Unsupported save format: {ext}")

        logger.info(f"Saved merged data ({len(self.df)} rows) → {output_path}")
        return output_path

    def get_summary(self) -> dict:
        """Return a summary of the merge operation."""
        return {
            "files_merged":  len(self.source_files),
            "source_files":  self.source_files,
            "total_rows":    len(self.df),
            "total_columns": len(self.df.columns),
            "columns":       list(self.df.columns),
            "merge_log":     self.merge_log,
        }
