# ============================================================
# utils/validators.py — Input validation functions
# ============================================================
# Before processing any file or data, we validate it first.
# This catches errors early and gives helpful error messages
# instead of cryptic Python crashes.
# ============================================================

import re
from pathlib import Path
from typing import Union

from utils.logger import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """
    Custom exception for validation failures.

    Using a custom exception lets other code specifically catch
    validation errors separately from other types of errors.

    Example:
        try:
            validate_email("not-an-email")
        except ValidationError as e:
            print(f"Please fix this: {e}")
    """
    pass


def validate_file_exists(filepath: Union[str, Path]) -> Path:
    """
    Check that a file exists and is actually a file (not a folder).

    Args:
        filepath: Path to check.

    Returns:
        Path object if valid.

    Raises:
        ValidationError: If file doesn't exist or is a directory.
    """
    path = Path(filepath)

    if not path.exists():
        raise ValidationError(f"File not found: {path}")
    if path.is_dir():
        raise ValidationError(f"Expected a file but found a folder: {path}")

    logger.debug(f"File validated: {path}")
    return path


def validate_file_extension(filepath: Union[str, Path], allowed: list[str]) -> Path:
    """
    Check that a file has one of the allowed extensions.

    Args:
        filepath: Path to the file.
        allowed:  List of allowed extensions (e.g. [".csv", ".xlsx"]).

    Returns:
        Path object if valid.

    Raises:
        ValidationError: If extension is not in the allowed list.
    """
    path = Path(filepath)
    # Normalize: lowercase with leading dot
    allowed_lower = [ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in allowed]

    if path.suffix.lower() not in allowed_lower:
        raise ValidationError(
            f"File '{path.name}' has unsupported extension '{path.suffix}'. "
            f"Allowed: {', '.join(allowed_lower)}"
        )
    return path


def validate_email(email: str) -> str:
    """
    Check that a string looks like a valid email address.

    This uses a simple regex — it catches obvious mistakes but
    is not a guaranteed validator for all edge cases.

    Args:
        email: The email string to validate.

    Returns:
        The cleaned email string (stripped of whitespace).

    Raises:
        ValidationError: If the email format looks wrong.
    """
    email = email.strip()
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

    if not re.match(pattern, email):
        raise ValidationError(f"Invalid email address: '{email}'")

    return email


def validate_directory(dirpath: Union[str, Path], create_if_missing: bool = False) -> Path:
    """
    Check that a directory exists.

    Args:
        dirpath:            Path to check.
        create_if_missing:  If True, create the directory instead of raising an error.

    Returns:
        Path object if valid or created.

    Raises:
        ValidationError: If directory doesn't exist and create_if_missing is False.
    """
    path = Path(dirpath)

    if not path.exists():
        if create_if_missing:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
        else:
            raise ValidationError(f"Directory not found: {path}")

    if path.exists() and not path.is_dir():
        raise ValidationError(f"Expected a directory but found a file: {path}")

    return path


def validate_dataframe_columns(df, required_columns: list[str]):
    """
    Check that a pandas DataFrame contains all required columns.

    Args:
        df:               A pandas DataFrame to validate.
        required_columns: List of column names that must be present.

    Raises:
        ValidationError: If any required columns are missing.

    Example:
        validate_dataframe_columns(df, ["Name", "Email", "Sales"])
        # Raises if the DataFrame doesn't have all three columns
    """
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        available = list(df.columns)
        raise ValidationError(
            f"Missing required columns: {missing}. "
            f"Available columns are: {available}"
        )


def validate_positive_number(value, name: str = "value") -> float:
    """
    Check that a value is a number greater than zero.

    Args:
        value: The value to check.
        name:  A label used in the error message (e.g. "price", "quantity").

    Returns:
        The value as a float.

    Raises:
        ValidationError: If value is not a positive number.
    """
    try:
        num = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"'{name}' must be a number, got: {type(value).__name__}")

    if num <= 0:
        raise ValidationError(f"'{name}' must be greater than zero, got: {num}")

    return num
