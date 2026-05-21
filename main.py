# ============================================================
# main.py — Application Entry Point
# ============================================================
# Run this file to start the application:
#   python main.py
#
# This file does three things:
#   1. Checks that all required libraries are installed
#   2. Sets up the logger
#   3. Launches the GUI dashboard
# ============================================================

import sys
import os

# ── Ensure the project root is in Python's search path ───────
# This lets every module do: from config.settings import ...
# instead of: from business_automation.config.settings import ...
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def check_dependencies():
    """
    Verify all required packages are installed before launching.
    Gives a clear error message if something is missing.
    """
    required = {
        "pandas":     "pandas",
        "openpyxl":   "openpyxl",
        "reportlab":  "reportlab",
        "schedule":   "schedule",
        "dotenv":     "python-dotenv",
        "tqdm":       "tqdm",
        "colorama":   "colorama",
    }

    missing = []
    for module_name, pip_name in required.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print("=" * 60)
        print("  MISSING DEPENDENCIES")
        print("=" * 60)
        print("The following packages are not installed:\n")
        for pkg in missing:
            print(f"  • {pkg}")
        print("\nFix: Run this command in your terminal:\n")
        print(f"  pip install {' '.join(missing)}\n")
        print("Or install everything at once:\n")
        print("  pip install -r requirements.txt")
        print("=" * 60)
        sys.exit(1)


def main():
    """Main entry point."""
    # Step 1: Check dependencies
    check_dependencies()

    # Step 2: Set up logging
    from utils.logger import get_logger
    logger = get_logger("main")
    logger.info("=" * 50)
    logger.info("Business Workflow Automation Suite starting...")
    logger.info("=" * 50)

    # Step 3: Launch GUI
    try:
        from gui.dashboard import Dashboard
        app = Dashboard()
        app.run()
    except KeyboardInterrupt:
        logger.info("Application closed by user (Ctrl+C)")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        print(f"\nFATAL ERROR: {e}")
        print("Check logs/ folder for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
