"""Reporting and daily summary generation for the time tracker application.

This module handles daily summary generation, historical reporting, and automated
summary checks.
"""

import os
from datetime import date, datetime, timedelta

import pytz

from .config import LOGS_DIR
from .db_state_manager import list_open_projects_and_tasks, save_state  # Using database backend
from .timer import finalize_current_task_time
from .types import State
from .utils import _ensure_dir_for_file, _get_tz, format_time


def summarize_day(state: State, summary_date: date) -> None:
    """Generate a daily summary markdown log for a specific date.

    Creates a comprehensive daily report including:
    - Aggregated task durations (sessions >= 10 seconds)
    - Current project/task inventory snapshot
    - Daily completion log (tasks ended on this date)

    Writes two files:
    - logs/YYYY-MM-DD_log.md (daily summary)
    - logs/completed_history.md (appends completions)

    Args:
        state: State dictionary containing task_times, tasks, and project data.
        summary_date: The date to summarize (uses CET timezone boundaries).
    """
    tz = _get_tz()
    # Finalize current task up to 23:59 CET on the summary date
    cutoff_cet = datetime(
        summary_date.year, summary_date.month, summary_date.day, 23, 59, 0
    )
    cutoff_cet = tz.localize(cutoff_cet)
    cutoff_utc = cutoff_cet.astimezone(pytz.utc)
    finalize_current_task_time(state, until_dt=cutoff_utc)

    # Compute start and end bounds in CET
    start_cet = tz.localize(
        datetime(summary_date.year, summary_date.month, summary_date.day, 0, 0, 0)
    )
    end_cet = cutoff_cet

    # Filter sessions by end_timestamp falling within the CET day and duration >= 10s
    sessions = state.get("task_times", [])
    filtered = []
    for s in sessions:
        try:
            et = datetime.fromisoformat(s["end_timestamp"]).astimezone(tz)
        except Exception:
            continue
        if start_cet <= et <= end_cet and float(s.get("duration_seconds", 0)) >= 10.0:
            filtered.append((s["task_name"], float(s["duration_seconds"]), et))

    # Aggregate durations per task_name
    agg = {}
    for name, dur, et in filtered:
        agg[name] = agg.get(name, 0.0) + dur

    # Build markdown lines
    lines = []
    lines.append(f"# Date: {summary_date.isoformat()}")
    lines.append(f"**Day:** {summary_date.strftime('%A')}")
    lines.append("")
    lines.append("## Task totals")
    total_all = 0.0
    for task, secs in sorted(agg.items()):
        fmt = format_time(secs)
        lines.append(f"- {task}: {fmt}")
        total_all += secs

    lines.append("")
    lines.append(f"**Total:** {format_time(total_all)}")

    # Project and Task Inventory
    lines.append("")
    lines.append("## Project and Task Inventory:")
    inv = list_open_projects_and_tasks(state)
    if not inv:
        lines.append("(no open projects/tasks)")
    else:
        for proj, tasks in inv.items():
            lines.append(f"### {proj}")
            for t in tasks:
                lines.append(f"- [{t['id']}] {t['description']}")

    # Daily completion log: list tasks/projects ended on this day
    lines.append("")
    lines.append("## Daily Completion Log")
    completed_today = []
    # tasks dict may have status and we need to check a hypothetical completed_timestamp stored in task object
    for tid, task in (state.get("tasks") or {}).items():
        # completed_at may be stored when ending tasks; check and include if on this date
        comp = task.get("completed_at")
        if not comp:
            continue
        try:
            comp_dt = datetime.fromisoformat(comp).astimezone(tz)
        except Exception:
            continue
        if start_cet.date() <= comp_dt.date() <= end_cet.date():
            completed_today.append((tid, task))

    if not completed_today:
        lines.append("(no tasks/projects completed today)")
    else:
        for tid, task in completed_today:
            lines.append(
                f"- [{tid}] {task.get('description')} (Project: {task.get('project_name')})"
            )

    # Write markdown log file
    _ensure_dir_for_file(os.path.join(LOGS_DIR, f"{summary_date.isoformat()}_log.md"))
    fname = os.path.join(LOGS_DIR, f"{summary_date.isoformat()}_log.md")
    with open(fname, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # Append daily completions to running history
    history_fname = os.path.join(LOGS_DIR, "completed_history.md")
    _ensure_dir_for_file(history_fname)
    with open(history_fname, "a", encoding="utf-8") as hf:
        if completed_today:
            hf.write(f"\n## {summary_date.strftime('%m/%d/%Y')}\n")
            for tid, task in completed_today:
                hf.write(
                    f"- [{tid}] {task.get('description')} (Project: {task.get('project_name')})\n"
                )

    state["last_summary_date"] = summary_date.isoformat()
    save_state(state)


def check_and_summarize_if_needed(state: State) -> bool:
    """Check if daily summaries need generation and create them for unsummarized dates.

    Compares last_summary_date with current date (respecting 23:59 cutoff in local timezone)
    to determine which days need summarization. Generates summaries for all missing dates
    in sequence from last_summary_date+1 to the most recent completable date.

    Uses 23:59 cutoff logic: if current time is before today's 23:59, yesterday is the
    last completable date; otherwise today is completable.

    Args:
        state: State dictionary containing last_summary_date and task_times.

    Returns:
        bool: True if any summaries were generated, False otherwise.
    """
    tz = _get_tz()
    # Anchor 'now' to the configured CET timezone to make cutoff comparisons reliable.
    now_cet = datetime.now(tz)
    today = now_cet.date()
    # Cutoff is today's 23:59 local time. If current local time is past that cutoff,
    # we should consider today as the end_date; otherwise end_date is yesterday.
    cutoff_today = tz.localize(datetime(today.year, today.month, today.day, 23, 59, 0))
    end_date = today if now_cet >= cutoff_today else (today - timedelta(days=1))

    last = state.get("last_summary_date")
    if last is None:
        # If we've never summarized, only summarize the most-recent unprocessed day (end_date)
        start_date = end_date
    else:
        try:
            last_date = date.fromisoformat(last)
            start_date = last_date + timedelta(days=1)
        except Exception:
            # If parsing fails for some reason, fall back to summarizing end_date only
            start_date = end_date

    did_any = False
    if start_date > end_date:
        return False

    cur = start_date
    while cur <= end_date:
        summarize_day(state, cur)
        did_any = True
        cur = cur + timedelta(days=1)

    return did_any
