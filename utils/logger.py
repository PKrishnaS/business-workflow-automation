# ============================================================
# utils/logger.py — Centralized logging for the entire project
# ============================================================
# WHAT IS LOGGING?
#   Instead of using print() everywhere, we use a "logger".
#   A logger writes messages to:
#     1. The terminal (so you see it while the app runs)
#     2. A log file (so you can review it later)
#   Each message has a severity level:
#     DEBUG   → very detailed developer notes
#     INFO    → normal progress ("Report generated successfully")
#     WARNING → something unexpected but not broken ("File already exists")
#     ERROR   → something failed ("Could not read file")
#     CRITICAL → app-breaking failure
# ============================================================

import logging
import logging.handlers
import sys
from pathlib import Path


def get_logger(name: str) -> logging.Logger:
    """
    Create and return a logger for any module in the project.

    HOW TO USE THIS IN OTHER FILES:
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Task started")
        logger.error("Something went wrong")

    Args:
        name: Usually pass __name__ — Python automatically fills in
              the module's name (e.g. "data_processor.cleaner")

    Returns:
        A configured Logger object ready to use.
    """
    # Import settings here (inside function) to avoid circular imports
    from config.settings import LOG_LEVEL, LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT

    # Get or create a logger with this name
    # (If called twice with the same name, returns the same logger — no duplicates)
    logger = logging.getLogger(name)

    # Only set up handlers once per logger name
    # (prevents duplicate log messages if the function is called multiple times)
    if logger.handlers:
        return logger

    # Set the minimum severity level to record
    # e.g. if level is INFO, DEBUG messages are silently ignored
    numeric_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # ── Format: what each log line looks like ────────────────
    # Example output:
    #   2024-05-15 14:23:01,456 | INFO     | data_processor.cleaner | Cleaning started
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # ── Handler 1: Write to terminal ─────────────────────────
    terminal_handler = logging.StreamHandler(sys.stdout)
    terminal_handler.setFormatter(formatter)
    terminal_handler.setLevel(numeric_level)

    # ── Handler 2: Write to rotating log file ────────────────
    # "Rotating" means: when the file gets too big (LOG_MAX_BYTES),
    # it renames the old file to app.log.1, app.log.2 etc. and starts fresh.
    # This prevents the log from growing forever and filling your disk.
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=LOG_FILE,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)   # Always save DEBUG to file even if terminal shows INFO
        logger.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        # If we can't write to the log file, warn but don't crash the app
        print(f"WARNING: Could not set up log file: {e}. Logging to terminal only.")

    # Add terminal handler last (so file errors don't prevent terminal logging)
    logger.addHandler(terminal_handler)

    # Prevent log messages from bubbling up to the root logger (avoids duplicates)
    logger.propagate = False

    return logger


def log_function_call(logger: logging.Logger):
    """
    Decorator that automatically logs when a function starts and finishes.

    HOW TO USE:
        from utils.logger import get_logger, log_function_call
        logger = get_logger(__name__)

        @log_function_call(logger)
        def process_data(filepath):
            ...  # your code here

    When process_data() is called, you'll automatically see:
        INFO | → Starting: process_data
        INFO | ✓ Finished: process_data (0.23s)
    """
    import functools
    import time

    def decorator(func):
        @functools.wraps(func)    # Preserve the original function's name and docstring
        def wrapper(*args, **kwargs):
            logger.info(f"→ Starting: {func.__name__}")
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start_time
                logger.info(f"✓ Finished: {func.__name__} ({elapsed:.2f}s)")
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                logger.error(f"✗ Failed: {func.__name__} ({elapsed:.2f}s) — {type(e).__name__}: {e}")
                raise   # Re-raise the exception so it still propagates normally
        return wrapper
    return decorator
