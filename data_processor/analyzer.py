# ============================================================
# data_processor/analyzer.py — Statistical analysis of data
# ============================================================
# Generates summary statistics and key metrics from a DataFrame.
# Results are used by the report generator to populate reports.
# ============================================================

import pandas as pd
from typing import Union

from utils.logger import get_logger, log_function_call

logger = get_logger(__name__)


class DataAnalyzer:
    """
    Compute summary statistics and metrics from a pandas DataFrame.

    HOW TO USE:
        df = pd.read_csv("sales.csv")
        analyzer = DataAnalyzer(df)
        stats = analyzer.analyze()
        print(stats["numeric_summary"])
    """

    def __init__(self, df: pd.DataFrame, label: str = "Dataset"):
        """
        Args:
            df:    The DataFrame to analyze.
            label: A friendly name for this dataset (used in reports).
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")

        self.df = df.copy()
        self.label = label
        self.results: dict = {}

    @log_function_call(logger)
    def analyze(self) -> "DataAnalyzer":
        """
        Run all analysis steps and store results in self.results.

        Returns:
            self (for method chaining)
        """
        logger.info(f"Analyzing '{self.label}': {self.df.shape[0]} rows × {self.df.shape[1]} cols")

        self.results = {
            "label":           self.label,
            "row_count":       len(self.df),
            "col_count":       len(self.df.columns),
            "columns":         list(self.df.columns),
            "data_types":      self._get_data_types(),
            "missing_summary": self._get_missing_summary(),
            "numeric_summary": self._get_numeric_summary(),
            "categorical_summary": self._get_categorical_summary(),
        }

        return self

    def _get_data_types(self) -> dict:
        """Map each column to its data type (simplified)."""
        type_map = {}
        for col in self.df.columns:
            dtype = self.df[col].dtype
            if pd.api.types.is_integer_dtype(dtype):
                type_map[col] = "integer"
            elif pd.api.types.is_float_dtype(dtype):
                type_map[col] = "decimal"
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                type_map[col] = "date"
            elif pd.api.types.is_bool_dtype(dtype):
                type_map[col] = "boolean"
            else:
                type_map[col] = "text"
        return type_map

    def _get_missing_summary(self) -> dict:
        """Show count and percentage of missing values per column."""
        total_rows = len(self.df)
        missing_counts = self.df.isna().sum()
        summary = {}
        for col, count in missing_counts.items():
            if count > 0:
                summary[col] = {
                    "missing_count": int(count),
                    "missing_pct": round((count / total_rows) * 100, 1)
                }
        return summary

    def _get_numeric_summary(self) -> dict:
        """For each numeric column, compute: count, mean, median, min, max, std."""
        numeric_df = self.df.select_dtypes(include="number")
        if numeric_df.empty:
            return {}

        summary = {}
        for col in numeric_df.columns:
            series = numeric_df[col].dropna()
            summary[col] = {
                "count":  int(series.count()),
                "sum":    round(float(series.sum()), 2),
                "mean":   round(float(series.mean()), 2),
                "median": round(float(series.median()), 2),
                "min":    round(float(series.min()), 2),
                "max":    round(float(series.max()), 2),
                "std":    round(float(series.std()), 2),
            }
        return summary

    def _get_categorical_summary(self) -> dict:
        """For text columns, show top 5 most frequent values."""
        text_df = self.df.select_dtypes(exclude="number")
        if text_df.empty:
            return {}

        summary = {}
        for col in text_df.columns:
            value_counts = self.df[col].value_counts().head(5)
            summary[col] = {
                "unique_values": int(self.df[col].nunique()),
                "top_5": {str(k): int(v) for k, v in value_counts.items()}
            }
        return summary

    def get_results(self) -> dict:
        """
        Return the analysis results.

        Returns:
            dict with all computed statistics.

        Raises:
            RuntimeError: If .analyze() was not called first.
        """
        if not self.results:
            raise RuntimeError("Call .analyze() first.")
        return self.results

    def group_by_summary(self, group_col: str, agg_col: str,
                         agg_func: str = "sum") -> pd.DataFrame:
        """
        Group the data by a column and aggregate another column.

        Common use case: "Show me total sales BY region"

        Args:
            group_col: Column to group by (e.g. "region")
            agg_col:   Column to aggregate (e.g. "sales_amount")
            agg_func:  Aggregation function: "sum", "mean", "count", "max", "min"

        Returns:
            DataFrame with group_col and aggregated agg_col, sorted descending.

        Example:
            analyzer.group_by_summary("region", "sales", "sum")
            # Returns:
            #   region  | sales
            #   --------|--------
            #   North   | 150000
            #   South   | 120000
        """
        if group_col not in self.df.columns:
            raise ValueError(f"Column '{group_col}' not found. Available: {list(self.df.columns)}")
        if agg_col not in self.df.columns:
            raise ValueError(f"Column '{agg_col}' not found. Available: {list(self.df.columns)}")

        result = (
            self.df.groupby(group_col)[agg_col]
            .agg(agg_func)
            .reset_index()
            .rename(columns={agg_col: f"{agg_func}_{agg_col}"})
            .sort_values(f"{agg_func}_{agg_col}", ascending=False)
        )
        return result
