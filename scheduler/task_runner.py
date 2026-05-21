# ============================================================
# scheduler/task_runner.py — Automated task scheduling
# ============================================================
# Runs tasks automatically on a schedule (e.g. every day at 8 AM).
# The scheduler runs in a background thread so the GUI stays responsive.
# ============================================================

import threading
import time
import schedule
from datetime import datetime
from typing import Callable

from config.settings import SCHEDULER_DAILY_REPORT_TIME
from utils.logger import get_logger

logger = get_logger(__name__)


class TaskRunner:
    """
    Schedule and run tasks automatically in the background.

    HOW TO USE:
        runner = TaskRunner()

        # Run a function every day at 8 AM
        runner.schedule_daily(my_report_function, at_time="08:00")

        # Run a function every hour
        runner.schedule_hourly(my_cleanup_function)

        # Start the scheduler (runs in background)
        runner.start()

        # To stop later:
        runner.stop()
    """

    def __init__(self):
        self._thread: threading.Thread = None
        self._running: bool = False
        self._scheduled_jobs: list[str] = []   # Human-readable list of scheduled jobs

    def schedule_daily(self, func: Callable, at_time: str = None, job_name: str = None):
        """
        Schedule a function to run every day at a specific time.

        Args:
            func:     The function to call (must take no arguments).
                      If your function needs arguments, wrap it:
                        runner.schedule_daily(lambda: my_func(arg1, arg2))
            at_time:  Time in "HH:MM" format (24-hour). Defaults to settings value.
            job_name: A friendly label for log messages.
        """
        at_time  = at_time  or SCHEDULER_DAILY_REPORT_TIME
        job_name = job_name or getattr(func, "__name__", "unnamed_task")

        def wrapped():
            """Wrapper that adds logging around the scheduled function."""
            logger.info(f"⏰ Scheduler: Running scheduled job '{job_name}'")
            try:
                func()
                logger.info(f"✓ Scheduled job '{job_name}' completed successfully")
            except Exception as e:
                logger.error(f"✗ Scheduled job '{job_name}' failed: {type(e).__name__}: {e}")

        schedule.every().day.at(at_time).do(wrapped)
        description = f"Daily at {at_time}: {job_name}"
        self._scheduled_jobs.append(description)
        logger.info(f"Scheduled: {description}")

    def schedule_hourly(self, func: Callable, job_name: str = None):
        """Schedule a function to run every hour."""
        job_name = job_name or getattr(func, "__name__", "unnamed_task")

        def wrapped():
            logger.info(f"⏰ Scheduler: Running hourly job '{job_name}'")
            try:
                func()
                logger.info(f"✓ Hourly job '{job_name}' completed")
            except Exception as e:
                logger.error(f"✗ Hourly job '{job_name}' failed: {e}")

        schedule.every().hour.do(wrapped)
        description = f"Every hour: {job_name}"
        self._scheduled_jobs.append(description)
        logger.info(f"Scheduled: {description}")

    def schedule_weekly(self, func: Callable, day: str = "monday",
                        at_time: str = "09:00", job_name: str = None):
        """
        Schedule a function to run weekly on a specific day.

        Args:
            func:     The function to call.
            day:      Day of week: "monday", "tuesday", ..., "sunday"
            at_time:  Time in "HH:MM" format.
            job_name: Label for logging.
        """
        job_name = job_name or getattr(func, "__name__", "unnamed_task")

        def wrapped():
            logger.info(f"⏰ Scheduler: Running weekly job '{job_name}'")
            try:
                func()
                logger.info(f"✓ Weekly job '{job_name}' completed")
            except Exception as e:
                logger.error(f"✗ Weekly job '{job_name}' failed: {e}")

        # schedule library uses: schedule.every().monday.at("09:00").do(job)
        getattr(schedule.every(), day.lower()).at(at_time).do(wrapped)
        description = f"Every {day.capitalize()} at {at_time}: {job_name}"
        self._scheduled_jobs.append(description)
        logger.info(f"Scheduled: {description}")

    def run_now(self, func: Callable, job_name: str = None):
        """
        Run a function immediately (in a background thread so GUI doesn't freeze).

        Args:
            func:     The function to run.
            job_name: Label for logging.
        """
        job_name = job_name or getattr(func, "__name__", "task")

        def run():
            logger.info(f"▶ Running immediately: '{job_name}'")
            try:
                func()
                logger.info(f"✓ Completed: '{job_name}'")
            except Exception as e:
                logger.error(f"✗ Failed: '{job_name}': {e}")

        t = threading.Thread(target=run, daemon=True, name=f"task-{job_name}")
        t.start()

    def start(self):
        """
        Start the scheduler in a background thread.

        "Daemon thread" means it automatically stops when the main program exits —
        you don't need to explicitly stop it.
        """
        if self._running:
            logger.warning("Scheduler is already running")
            return

        self._running = True

        def run_loop():
            logger.info(f"Scheduler started. Watching {len(self._scheduled_jobs)} job(s).")
            while self._running:
                # Check if any scheduled jobs are due and run them
                schedule.run_pending()
                # Sleep 30 seconds between checks (saves CPU)
                time.sleep(30)
            logger.info("Scheduler stopped.")

        self._thread = threading.Thread(target=run_loop, daemon=True, name="task-scheduler")
        self._thread.start()
        logger.info("Background scheduler thread started")

    def stop(self):
        """Stop the scheduler."""
        self._running = False
        schedule.clear()
        logger.info("Scheduler stopped and all jobs cleared")

    def get_status(self) -> dict:
        """Return the current status of the scheduler."""
        return {
            "running":         self._running,
            "scheduled_jobs":  self._scheduled_jobs,
            "job_count":       len(self._scheduled_jobs),
            "next_run":        str(schedule.next_run()) if schedule.jobs else "None scheduled",
        }

    def get_scheduled_jobs_text(self) -> str:
        """Return a readable list of all scheduled jobs."""
        if not self._scheduled_jobs:
            return "No jobs scheduled."
        return "\n".join(f"  • {j}" for j in self._scheduled_jobs)
