"""Utility functions for the time tracker application.

This module contains all stateless helper functions used throughout the application,
including timezone handling, time formatting, display utilities, and file system operations.
"""

import os
from datetime import datetime
from typing import Optional

import pytz
from colorama import Fore, Style

from .config import TIMEZONE_STR
from .types import State, Task


def _get_tz() -> pytz.tzinfo.BaseTzInfo:
    """Get the configured timezone object for datetime display conversions.

    Attempts to load timezone specified in TIMEZONE_STR constant (default: "CET").
    Falls back to Europe/Paris if the configured timezone is invalid.

    Returns:
        pytz.timezone: Timezone object for converting UTC times to local display times.
    """
    try:
        return pytz.timezone(TIMEZONE_STR)
    except Exception:
        return pytz.timezone("Europe/Paris")


def _ensure_dir_for_file(path: str) -> None:
    """Ensure parent directory exists for a file path, creating it if necessary.

    Creates all parent directories recursively (like mkdir -p) to prevent errors
    when writing log files or other output files.

    Args:
        path: File path for which to ensure the parent directory exists.
    """
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def format_seconds_to_human_with_date(seconds: float, dt: datetime) -> str:
    """Format duration and datetime as human-readable timestamp for daily summaries.

    Converts elapsed seconds to HH:MM:SS format and appends date in MM-DD-YYYY format.
    Used in daily summary logs to show session end times with dates.

    Args:
        seconds: Duration in seconds (fractional seconds are rounded).
        dt: Datetime object representing the session end time.

    Returns:
        str: Formatted string like "02:30:45 10-29-2025" (duration + date).
    """
    # Format: hh:mm:ss mm-dd-yyyy
    s = int(round(seconds))
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:02d} {dt.strftime('%m-%d-%Y')}"


def format_time(seconds: float) -> str:
    """Convert elapsed seconds to HH:MM:SS string format for display.

    Rounds fractional seconds to nearest integer and formats as zero-padded
    hours:minutes:seconds. Used for displaying active task timers and session durations.

    Args:
        seconds: Duration in seconds (fractional seconds are rounded).

    Returns:
        str: Zero-padded time string like "02:30:45" or "123:05:17" (no hour limit).
    """
    s = int(round(seconds))
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}"


def _deadline_days_remaining(
    t: Task, ref_dt: Optional[datetime] = None
) -> Optional[float]:
    """Calculate days remaining until task deadline for priority color determination.

    Parses deadline_mmddyyyy field from task object and computes time delta between
    the reference datetime and the deadline (set to 23:59 UTC on deadline date).
    Used by color cascade logic to determine task bracket colors (RED/ORANGE/CYAN).

    Args:
        t: Task dictionary containing optional 'deadline_mmddyyyy' field (8-digit string).
        ref_dt: Reference datetime for calculation (defaults to current UTC time if None).

    Returns:
        float: Days remaining until deadline (can be negative if past due), or None
               if no deadline exists or parsing fails.
    """
    dm = t.get("deadline_mmddyyyy")
    if not dm:
        return None
    try:
        mm = int(dm[0:2])
        dd = int(dm[2:4])
        yyyy = int(dm[4:8])
        dead = datetime(yyyy, mm, dd, 23, 59, tzinfo=pytz.utc)
        now = ref_dt if ref_dt is not None else datetime.now(pytz.utc)
        delta = (dead - now).total_seconds()
        return delta / 86400.0
    except Exception:
        return None


def _format_due_date_for_display(t: Task) -> str:
    """Format task deadline as human-readable string for display in task listings.

    Converts mmddyyyy format to MM/DD/YYYY with "(Due: " prefix for inline display
    next to task descriptions.

    Args:
        t: Task dictionary containing optional 'deadline_mmddyyyy' field.

    Returns:
        str: Formatted deadline string like " (Due: 12/25/2025)", or empty string
             if no deadline exists or parsing fails.
    """
    dm = t.get("deadline_mmddyyyy")
    if not dm:
        return ""
    try:
        return f" (Due: {dm[0:2]}/{dm[2:4]}/{dm[4:8]})"
    except Exception:
        return ""


def _color_bracket_for_task(t: Task, ref_dt: Optional[datetime] = None) -> str:
    """Return a colored bracket string for a task dict depending on deadline or value_flag.

    Examples: '[0001]' colored RED/ORANGE/YELLOW or pale yellow when value_flag is True.
    """
    tid = t.get("id") or "????"
    # If task has a deadline, apply color cascade: RED (<4 days) > ORANGE (<8 days) > value_flag (pale yellow)
    days = _deadline_days_remaining(t, ref_dt=ref_dt)
    if days is not None:
        # RED: less than 4 days
        if days < 4:
            return f"[{Fore.RED}{tid}{Style.RESET_ALL}]"
        # ORANGE: less than 8 days (but not RED)
        if days < 8:
            # Use Fore.YELLOW to represent orange-ish urgency for now
            return f"[{Fore.YELLOW}{tid}{Style.RESET_ALL}]"
        # CYAN: 8+ days away (lowest deadline priority). If value_flag is set, it overrides CYAN.
        if t.get("value_flag"):
            return f"[{Fore.LIGHTYELLOW_EX}{tid}{Style.RESET_ALL}]"
        return f"[{Fore.CYAN}{tid}{Style.RESET_ALL}]"
    # Otherwise, value_flag (!!!) gets pale yellow
    # Medium priority: value_flag (!!!) overrides CYAN but is below RED/ORANGE
    if t.get("value_flag"):
        return f"[{Fore.LIGHTYELLOW_EX}{tid}{Style.RESET_ALL}]"
    # Default: no color
    return f"[{tid}]"


def _project_is_visible(state: State, proj: str) -> bool:
    """Return True if project should be shown in listings based on projects_meta (hidden/unhide_date)."""
    pm = state.get("projects_meta", {}) or {}
    meta = pm.get(proj, {})
    if not meta:
        return True
    if not meta.get("hidden"):
        return True
    ud = meta.get("unhide_date")
    if not ud:
        # hidden indefinitely
        return False
    # parse mmddyyyy
    try:
        mm = int(ud[0:2])
        dd = int(ud[2:4])
        yyyy = int(ud[4:8])
        tz = _get_tz()
        today_local = datetime.now(tz).date()
        unhide_dt = datetime(yyyy, mm, dd).date()
        return today_local >= unhide_dt
    except Exception:
        return False


def clear_screen() -> int:
    """Clear the terminal screen in a cross-platform way without affecting active timers.

    This administrative command clears the terminal display using the appropriate
    system command for the current platform (POSIX 'clear' or Windows 'cls').
    The function does not modify any state, finalize running tasks, or alter timers.

    Returns:
        int: Exit code from the system command (0 on success, non-zero on failure).
             Returns -1 if both POSIX and Windows clearing methods fail.
    """
    try:
        # POSIX (Linux, macOS, Unix-like systems)
        exit_code = os.system("clear")
        return exit_code
    except Exception:
        try:
            # Windows fallback
            exit_code = os.system("cls")
            return exit_code
        except Exception:
            # Both methods failed
            return -1
