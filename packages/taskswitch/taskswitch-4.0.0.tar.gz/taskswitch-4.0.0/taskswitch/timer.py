"""Timer management for the time tracker application.

This module handles active timer state management including session finalization
and timer switching operations.
"""

from datetime import datetime
from typing import Optional

import pytz

from .db_state_manager import save_state  # Using database backend
from .models import db, TimeEntry
from .types import State
from .logging_config import get_timer_logger

# Get logger for timer operations
logger = get_timer_logger()


def finalize_current_task_time(
    state: State, until_dt: Optional[datetime] = None
) -> None:
    """Record elapsed time for the currently active task as a completed session.

    Calculates duration from start_time to until_dt (or now), creates a session object,
    and appends it to the task_times list. Clears active_task and start_time from state.
    Does nothing if no task is currently active.

    Args:
        state: State dictionary containing active_task, start_time, and task_times list.
        until_dt: Session end datetime (defaults to current UTC time if None).
    """
    active = state.get("active_task")
    start = state.get("start_time")
    if not active or not start:
        logger.debug("No active task to finalize")
        return

    if until_dt is None:
        until = datetime.now(pytz.utc)
    else:
        until = until_dt.astimezone(pytz.utc)

    elapsed = (until - start).total_seconds()
    if elapsed < 0:
        elapsed = 0

    logger.info(f"Finalizing task time: {active}, duration: {elapsed:.1f}s")
    
    # Append a session object to task_times list (for in-memory state)
    sessions = state.setdefault("task_times", [])
    session = {
        "task_name": active,
        "duration_seconds": float(elapsed),
        # record end timestamp as UTC ISO
        "end_timestamp": until.astimezone(pytz.utc).isoformat(),
    }
    sessions.append(session)
    
    # Also save to database TimeEntry table
    if db.is_closed():
        db.connect()
    TimeEntry.create(
        task_name=active,
        duration_seconds=float(elapsed),
        end_timestamp=until.astimezone(pytz.utc)
    )
    logger.debug(f"Time entry saved to database for task: {active}")
    
    state["start_time"] = None


def post_end_switch_to_break(st: State) -> None:
    """Finalize the currently active task and immediately start a BREAK timer.

    Stops the current task timer by calling finalize_current_task_time, then
    switches to a special "BREAK" task and starts a new timer. Used after END
    commands to track break time separately.

    Args:
        st: State dictionary (modified in place to update active_task and start_time).
    """
    logger.info("Switching to BREAK after ending task")
    finalize_current_task_time(st)
    st["active_task"] = "BREAK"
    st["start_time"] = datetime.now(pytz.utc)
    st.setdefault("task_times", [])
    save_state(st)
    logger.debug("BREAK timer started")
