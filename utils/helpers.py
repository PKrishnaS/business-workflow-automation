# ============================================================
# utils/helpers.py — Reusable utility functions
# ============================================================
# These small helper functions are used throughout the project.
# Putting them here means we write the code once and reuse it everywhere.
# ============================================================

import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from utils.logger import get_logger

logger = get_logger(__name__)


def get_timestamp(fmt: str = "%Y%m%d_%H%M%S") -> str:
    """
    Return the current date and time as a formatted string.

    Useful for creating unique filenames (e.g. "report_20240515_142301.pdf").

    Args:
        fmt: A strftime format string. Default produces "20240515_142301".

    Returns:
        Current datetime as a string.

    Example:
        >>> get_timestamp()
        '20240515_142301'
        >>> get_timestamp("%d/%m/%Y")
        '15/05/2024'
    """
    return datetime.now().strftime(fmt)


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """
    Remove characters from a string that are not safe to use in a filename.

    Windows, Mac, and Linux have different rules about what characters are
    allowed in filenames. This function makes a string safe for all systems.

    Args:
        name:       The string to sanitize (e.g. a report title)
        max_length: Trim the result to this many characters (default 100)

    Returns:
        A filename-safe string.

    Example:
        >>> sanitize_filename("Sales Report: Q1/2024 (Final!)")
        'Sales_Report_Q1_2024_Final'
    """
    # Replace spaces and slashes with underscores
    name = name.strip().replace(" ", "_").replace("/", "_").replace("\\", "_")

    # Remove any character that isn't a letter, number, underscore, or hyphen
    name = re.sub(r"[^\w\-]", "", name)

    # Remove leading/trailing underscores and collapse multiple underscores
    name = re.sub(r"_+", "_", name).strip("_")

    # Truncate if too long
    return name[:max_length] if name else "unnamed"


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Create a directory (and all parent directories) if it doesn't exist.

    This prevents "FileNotFoundError: No such file or directory" when
    trying to save files to folders that don't exist yet.

    Args:
        path: The folder path to create.

    Returns:
        The Path object of the created/existing directory.

    Example:
        >>> ensure_dir("data/output/reports/2024")
        # Creates all folders in the path if they don't exist
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size_str(filepath: Union[str, Path]) -> str:
    """
    Return a human-readable file size string (e.g. "2.3 MB").

    Args:
        filepath: Path to the file.

    Returns:
        A string like "1.5 KB", "2.3 MB", or "Unknown" if file doesn't exist.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return "Unknown"

    size_bytes = filepath.stat().st_size

    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.1f} TB"


def file_checksum(filepath: Union[str, Path]) -> str:
    """
    Calculate the MD5 checksum of a file.

    A checksum is like a fingerprint for a file — if any byte changes,
    the checksum changes. Useful for verifying that a file was not corrupted.

    Args:
        filepath: Path to the file.

    Returns:
        MD5 hex string (e.g. "d41d8cd98f00b204e9800998ecf8427e")
        or empty string if file doesn't exist.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        logger.warning(f"Checksum requested for non-existent file: {filepath}")
        return ""

    hasher = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            # Read in 64KB chunks — efficient for large files
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except OSError as e:
        logger.error(f"Could not compute checksum for {filepath}: {e}")
        return ""


def format_number(value: float, decimals: int = 2, prefix: str = "", suffix: str = "") -> str:
    """
    Format a number with thousands separators and optional prefix/suffix.

    Args:
        value:    The number to format
        decimals: Decimal places (default 2)
        prefix:   String before the number (e.g. "$" for currency)
        suffix:   String after the number (e.g. "%" for percentages)

    Returns:
        Formatted string.

    Examples:
        >>> format_number(1234567.89)
        '1,234,567.89'
        >>> format_number(0.954, decimals=1, suffix="%")
        '95.4%'
        >>> format_number(9500, decimals=0, prefix="$")
        '$9,500'
    """
    try:
        formatted = f"{value:,.{decimals}f}"
        return f"{prefix}{formatted}{suffix}"
    except (TypeError, ValueError):
        return str(value)


def chunk_list(lst: list, chunk_size: int) -> list:
    """
    Split a list into smaller lists of a given size.

    Useful when processing large datasets in batches to avoid memory issues.

    Args:
        lst:        The list to split.
        chunk_size: How many items per chunk.

    Returns:
        A list of smaller lists.

    Example:
        >>> chunk_list([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def find_files(directory: Union[str, Path], extensions: Optional[list] = None,
               recursive: bool = True) -> list[Path]:
    """
    Find all files in a directory, optionally filtered by extension.

    Args:
        directory:  The folder to search.
        extensions: List of extensions to include (e.g. [".csv", ".xlsx"]).
                    If None, returns ALL files.
        recursive:  If True, also search subfolders (default True).

    Returns:
        Sorted list of Path objects for matching files.

    Example:
        >>> find_files("data/input", extensions=[".csv", ".xlsx"])
        [PosixPath('data/input/sales.csv'), PosixPath('data/input/report.xlsx')]
    """
    directory = Path(directory)
    if not directory.exists():
        logger.warning(f"Directory not found: {directory}")
        return []

    # Choose glob pattern: ** searches recursively, * searches current folder only
    pattern = "**/*" if recursive else "*"
    all_files = [p for p in directory.glob(pattern) if p.is_file()]

    if extensions:
        # Normalize extensions to lowercase with a dot (e.g. "CSV" → ".csv")
        exts = {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions}
        all_files = [f for f in all_files if f.suffix.lower() in exts]

    return sorted(all_files)
