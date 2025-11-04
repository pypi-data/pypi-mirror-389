"""State persistence and management for the time tracker application."""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pytz

from .config import STATE_FILE
from .types import ProjectMeta, Session, State, Task
from .utils import _ensure_dir_for_file


def parse_iso_to_utc(s: Optional[str]) -> Optional[datetime]:
    """Parse an ISO 8601 datetime string and convert to UTC-aware datetime object.

    Handles both timezone-aware and naive datetime strings. Converts 'Z' suffix
    to '+00:00' for compatibility with Python's fromisoformat(). If the parsed
    datetime is naive (no timezone), assumes UTC and attaches tzinfo. Otherwise,
    converts to UTC timezone.

    Args:
        s: ISO 8601 formatted datetime string (e.g., "2025-10-27T14:30:00Z" or
           "2025-10-27T14:30:00+00:00"), or None.

    Returns:
        datetime: UTC-aware datetime object, or None if input is None.
    """
    if s is None:
        return None
    s2 = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s2)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=pytz.utc)
    return dt.astimezone(pytz.utc)


def iso_from_dt(dt: Optional[datetime]) -> Optional[str]:
    """Convert a datetime object to UTC ISO 8601 string format for serialization.

    Ensures the datetime is converted to UTC before formatting. Used when saving
    state to JSON to maintain consistent timezone representation across all timestamps.

    Args:
        dt: A datetime object (timezone-aware or naive), or None.

    Returns:
        str: ISO 8601 formatted UTC datetime string (e.g., "2025-10-27T14:30:00+00:00"),
             or None if input is None.
    """
    if dt is None:
        return None
    return dt.astimezone(pytz.utc).isoformat()


def load_state() -> State:
    """Load application state from JSON file with automatic migration support.

    Handles V1 (legacy flat structure), V2 (tasks dictionary), and V3 (session-based)
    state formats. Performs automatic migrations to current V3 format including:
    - Converting task_times from dict (cumulative) to list (session-based) structure
    - Adding 3-digit numeric project IDs retroactively based on project_name order
    - Initializing projects_meta for project hiding feature
    - Adding last_list_view state for session-aware view persistence

    Creates default empty state if file doesn't exist.

    Returns:
        dict: State dictionary with keys:
            - active_task: Optional[str] - currently active task name
            - start_time: Optional[datetime] - UTC timestamp when active task started
            - task_times: list[dict] - session objects with task_name, duration_seconds, end_timestamp
            - active_project: Optional[str] - last used project for shorthand TASK commands
            - priority_projects: list[str] - up to 3 project names in most-recent-first order
            - project_numbers: dict[str -> str] - mapping of PROJECT_NAME to 3-digit ID
            - projects_meta: dict[str -> dict] - project metadata with hidden flag and unhide_date
            - project_counter: int - counter for generating next 3-digit project ID
            - last_summary_date: Optional[str] - date of last summary generation
            - global_task_counter: int - counter for generating next 4-digit task ID
            - tasks: dict[str -> dict] - task objects keyed by 4-digit ID
            - project_tasks: dict[str -> list[str]] - mapping of project name to task IDs
            - last_list_view: str - either "PROJECTS" or "PRIORITY"
    """
    if not os.path.exists(STATE_FILE):
        return {
            "active_task": None,
            "start_time": None,
            # task_times is now a list of session objects
            "task_times": [],
            # active_project remembers the last used project for shorthand TASK commands
            "active_project": None,
            "priority_projects": [],
            # per-project metadata (hidden flag and optional unhide date mmddyyyy)
            "projects_meta": {},
            # project numbering mapping: PROJECT_NAME -> '001'
            "project_numbers": {},
            "project_counter": 0,
            "last_summary_date": None,
            "global_task_counter": 0,
            "tasks": {},
            "project_tasks": {},
            "last_list_view": "PROJECTS",
        }
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return {
            "active_task": None,
            "start_time": None,
            "task_times": [],
            "active_project": None,
            "priority_projects": [],
            "project_numbers": {},
            "project_counter": 0,
            "last_summary_date": None,
            "global_task_counter": 0,
            "tasks": {},
            "project_tasks": {},
        }
    # Migration: if an old state file used a dict for task_times (legacy cumulative model),
    # replace it with an empty list so the newer session-based code can operate safely.
    tt = raw.get("task_times")
    if isinstance(tt, dict):
        raw["task_times"] = []

    state = {
        "active_task": raw.get("active_task"),
        "start_time": parse_iso_to_utc(raw.get("start_time")),
        # task_times stored as list of session dicts
        "task_times": raw.get("task_times") or [],
        "active_project": raw.get("active_project"),
        "priority_projects": raw.get("priority_projects") or [],
        "project_numbers": raw.get("project_numbers") or {},
        "projects_meta": raw.get("projects_meta") or {},
        "project_counter": int(raw.get("project_counter") or 0),
        "last_summary_date": raw.get("last_summary_date"),
        "global_task_counter": int(raw.get("global_task_counter") or 0),
        "tasks": raw.get("tasks") or {},
        "project_tasks": raw.get("project_tasks") or {},
        "last_list_view": raw.get("last_list_view") or "PROJECTS",
    }

    # Retroactive project numbering: ensure every project in project_tasks has a three-digit project number
    pnums = state.setdefault("project_numbers", {})
    pcounter = int(state.get("project_counter", 0) or 0)
    for proj in list(state.get("project_tasks", {}).keys()):
        if proj not in pnums:
            pcounter += 1
            pnums[proj] = f"{pcounter:03d}"
    state["project_counter"] = pcounter
    # Ensure projects_meta contains entries for all known projects (migration support)
    pm = state.setdefault("projects_meta", {})
    for proj in list(state.get("project_tasks", {}).keys()):
        if proj not in pm:
            pm[proj] = {"hidden": False, "unhide_date": None}
    return state


def save_state(state: State) -> None:
    """Persist application state to JSON file with proper serialization.

    Converts all datetime objects to ISO 8601 UTC strings before saving.
    Creates parent directories if they don't exist.

    Args:
        state: State dictionary containing all application data. Expected keys:
            - active_task, start_time (datetime -> ISO string conversion)
            - task_times (list of sessions), tasks, priority_projects
            - project_numbers, projects_meta, project_tasks
            - project_counter, global_task_counter, last_summary_date
            - last_list_view
    """
    _ensure_dir_for_file(STATE_FILE)
    serial = {
        "active_task": state.get("active_task"),
        "start_time": iso_from_dt(state.get("start_time")),
        # task_times is a list of session objects; ensure serializable types
        "task_times": state.get("task_times", []),
        "active_project": state.get("active_project"),
        "priority_projects": state.get("priority_projects", []),
        "project_numbers": state.get("project_numbers", {}),
        "projects_meta": state.get("projects_meta", {}),
        "project_counter": int(state.get("project_counter", 0)),
        "last_summary_date": state.get("last_summary_date"),
        "global_task_counter": int(state.get("global_task_counter", 0)),
        "tasks": state.get("tasks", {}),
        "project_tasks": state.get("project_tasks", {}),
        "last_list_view": state.get("last_list_view", "PROJECTS"),
    }
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(serial, f, indent=2)


def _next_task_id(state: State) -> str:
    """Generate next sequential 4-digit task ID.

    Increments global_task_counter and formats result as zero-padded 4-digit string.
    Used when creating new tasks to ensure unique, sequential identifiers.

    Args:
        state: State dictionary (modified in place to update global_task_counter).

    Returns:
        str: 4-digit zero-padded task ID (e.g., "0001", "0042", "1234").
    """
    state["global_task_counter"] = int(state.get("global_task_counter", 0)) + 1
    return f"{state['global_task_counter']:04d}"


def add_project(state: State, project_name: str) -> bool:
    """Create a new project with automatic 3-digit ID assignment.

    Normalizes project name to uppercase for consistent storage. Prevents duplicate
    projects by checking project_tasks keys. Assigns sequential 3-digit project ID
    (001, 002, etc.) and initializes projects_meta with default hiding settings.

    Args:
        state: State dictionary (modified in place to add project).
        project_name: User-provided project name (will be normalized to uppercase).

    Returns:
        bool: True if project was created successfully, False if project already exists.
    """
    # Normalize project name to ALL CAPS for storage
    pname = project_name.strip().upper()
    if pname in state.get("project_tasks", {}):
        return False
    state.setdefault("project_tasks", {})[pname] = []
    # assign a project number if not present
    pnums = state.setdefault("project_numbers", {})
    if pname not in pnums:
        state["project_counter"] = int(state.get("project_counter", 0)) + 1
        pnums[pname] = f"{state['project_counter']:03d}"
    # initialize projects_meta for this project
    pm = state.setdefault("projects_meta", {})
    pm.setdefault(pname, {"hidden": False, "unhide_date": None})
    save_state(state)
    return True


def add_priority(state: State, project_name: str) -> bool:
    """Add or move a project to the top of the priority list with enforced capacity limit.

    This function manages the priority_projects list, which stores up to 3 project names
    in most-recent-first order. The list is used by the CLI to display a focused view
    of high-priority projects via the LIST PRIORITY command.

    Implementation details:
    1. Normalizes the project name to uppercase for consistency
    2. Removes the project from its current position if already in the list (deduplication)
    3. Inserts the project at the front of the list (index 0) to mark it as most recent
    4. Trims the list to maintain the maximum capacity of 3 items by removing oldest entries
    5. Persists the updated state to disk

    Args:
        state: The current application state dictionary containing the priority_projects list.
        project_name: The name of the project to add or move to the top of the priority list.
                      Will be normalized to uppercase before processing.

    Returns:
        bool: Always returns True to indicate the operation completed successfully.
              (The function does not fail; it always updates the priority list.)
    """
    normalized_project_name = project_name.strip().upper()
    priority_list = state.setdefault("priority_projects", [])

    # Move to front: remove from current position if already present (deduplication)
    if normalized_project_name in priority_list:
        priority_list.remove(normalized_project_name)

    # Insert at the front (most recent position)
    priority_list.insert(0, normalized_project_name)

    # Enforce maximum capacity of 3 items by trimming oldest entries
    while len(priority_list) > 3:
        priority_list.pop()

    save_state(state)
    return True


def add_task(state: State, project_name: str, description: str) -> str:
    """Create a new task with automatic ID generation, deadline detection, and value flag parsing.

    Automatically creates the parent project if it doesn't exist. Parses the description
    for optional features:
    - Value flag: '!!!' anywhere in description marks task as high-value
    - Deadline: 8-digit mmddyyyy date format (e.g., 12252025 for Dec 25, 2025)

    Args:
        state: State dictionary (modified in place to add task).
        project_name: Name of parent project (normalized to uppercase).
        description: Task description text (may contain '!!!' marker and/or mmddyyyy deadline).

    Returns:
        str: Newly assigned 4-digit task ID (e.g., "0001", "0042").
    """
    # Normalize project name and ensure project exists
    pname = project_name.strip().upper()
    state.setdefault("project_tasks", {})
    if pname not in state["project_tasks"]:
        state["project_tasks"][pname] = []

    tid = _next_task_id(state)
    # detect value_flag marker '!!!' anywhere, but preserve the description text
    value_flag = False
    if "!!!" in description:
        value_flag = True

    # detect optional deadline in mmddyyyy anywhere in description (simple regex-free scan)
    deadline = None
    parts = description.split()
    for p in parts:
        if len(p) == 8 and p.isdigit():
            try:
                mm = int(p[0:2])
                dd = int(p[2:4])
                yyyy = int(p[4:8])
                # basic validation by constructing a date
                from datetime import datetime as _dt

                _dt(yyyy, mm, dd)
                deadline = f"{mm:02d}{dd:02d}{yyyy:04d}"
                break
            except Exception:
                deadline = None

    task_obj = {
        "id": tid,
        "description": description,
        "project_name": pname,
        "status": "open",
        "value_flag": value_flag,
        "deadline_mmddyyyy": deadline,
    }
    state.setdefault("tasks", {})[tid] = task_obj
    state["project_tasks"].setdefault(pname, []).append(tid)
    save_state(state)
    return tid


def end_task(state: State, task_id: str) -> Tuple[bool, str]:
    """Mark a task as complete and record completion timestamp.

    Sets task status to "complete", records UTC completion timestamp, and removes
    the task ID from its parent project's open task list.

    Args:
        state: State dictionary (modified in place).
        task_id: 4-digit task ID to mark as complete.

    Returns:
        tuple: (success: bool, message: str) - success status and descriptive message.
    """
    tasks = state.setdefault("tasks", {})
    if task_id not in tasks:
        return False, f"Task {task_id} not found"
    # Mark complete and remove from project open list
    tasks[task_id]["status"] = "complete"
    # Record completion timestamp in UTC ISO
    tasks[task_id]["completed_at"] = datetime.now(pytz.utc).isoformat()
    proj = tasks[task_id].get("project_name")
    if proj and proj in state.get("project_tasks", {}):
        if task_id in state["project_tasks"][proj]:
            state["project_tasks"][proj].remove(task_id)
            if not state["project_tasks"][proj]:
                # keep empty list to indicate project exists
                state["project_tasks"][proj] = []
    save_state(state)
    return True, f"Ended task {task_id}"


def end_tasks(state: State, task_ids: List[str]) -> Dict[str, Dict[str, any]]:
    """Mark multiple tasks as complete in a single operation.

    Processes each task ID sequentially using end_task(). Useful for batch
    operations and CLI commands that accept multiple task IDs.

    Args:
        state: State dictionary (modified in place by end_task calls).
        task_ids: List of 4-digit task IDs to mark as complete.

    Returns:
        dict: Mapping of task_id -> {ok: bool, message: str} with per-task results.
    """
    results = {}
    for tid in task_ids:
        ok, msg = end_task(state, tid)
        results[tid] = {"ok": bool(ok), "message": msg}
    return results


def end_project(state: State, project_name: str) -> bool:
    """Mark all tasks in a project as complete and remove project.

    Completes all open tasks within the project, records completion timestamps,
    removes the project from project_tasks, and cleans up projects_meta entry.

    Args:
        state: State dictionary (modified in place).
        project_name: Name of project to end (normalized to uppercase).

    Returns:
        bool: True if project existed and was ended, False if project not found.
    """
    pname = project_name.strip().upper()
    if pname not in state.get("project_tasks", {}):
        return False
    tids = list(state["project_tasks"][pname])
    for tid in tids:
        if tid in state.get("tasks", {}):
            state["tasks"][tid]["status"] = "complete"
            state["tasks"][tid]["completed_at"] = datetime.now(pytz.utc).isoformat()
    # Remove project mapping
    state["project_tasks"].pop(pname, None)
    # Remove project metadata as well
    state.get("projects_meta", {}).pop(pname, None)
    # If active_project was this project, clear it
    if state.get("active_project") == pname:
        state["active_project"] = None
    save_state(state)
    return True


def delete_project(state: State, project_name: str) -> bool:
    """Permanently delete a project and all its associated tasks.

    Removes all task objects from tasks dictionary, removes project from
    project_tasks, clears projects_meta entry, clears project number,
    and clears active_project if it was the deleted project.

    Args:
        state: State dictionary (modified in place).
        project_name: Name of project to delete (normalized to uppercase).

    Returns:
        bool: True if project existed and was deleted, False if project not found.
    """
    pname = project_name.strip().upper()
    if pname not in state.get("project_tasks", {}):
        return False
    tids = list(state["project_tasks"][pname])
    for tid in tids:
        # remove tasks completely
        state.get("tasks", {}).pop(tid, None)
    state["project_tasks"].pop(pname, None)
    # Remove metadata
    state.get("projects_meta", {}).pop(pname, None)
    if state.get("active_project") == pname:
        state["active_project"] = None
    save_state(state)
    return True


def get_task(state: State, task_id: str) -> Optional[Task]:
    """Retrieve task object by ID.

    Args:
        state: State dictionary.
        task_id: 4-digit task ID to look up.

    Returns:
        dict or None: Task object with keys (id, description, project_name, status,
                      value_flag, deadline_mmddyyyy, completed_at), or None if not found.
    """
    return state.get("tasks", {}).get(task_id)


def delete_task(state: State, task_id: str) -> bool:
    """Permanently delete a single task and remove from project mapping.

    Removes task object from tasks dictionary and removes task ID from parent
    project's task list. Leaves empty list in project_tasks to indicate project
    still exists. Does not modify active_task (admin operation shouldn't affect timer).

    Args:
        state: State dictionary (modified in place).
        task_id: 4-digit task ID to delete.

    Returns:
        bool: True if task existed and was deleted, False if task not found.
    """
    tasks = state.get("tasks", {})
    if task_id not in tasks:
        return False
    proj = tasks[task_id].get("project_name")
    # remove from tasks dict
    tasks.pop(task_id, None)
    # remove from project_tasks mapping if present
    if proj and proj in state.get("project_tasks", {}):
        if task_id in state["project_tasks"][proj]:
            state["project_tasks"][proj].remove(task_id)
            # leave empty list to indicate project still exists
            if not state["project_tasks"][proj]:
                state["project_tasks"][proj] = []
    # If active_task referenced this id, leave active_task unchanged (admin op shouldn't touch timers)
    save_state(state)
    return True


def hide_project(state: State, project_name: str, until: Optional[str] = None) -> bool:
    """Hide a project from standard project listings with optional auto-unhide date.

    Sets the project's hidden flag in projects_meta. Hidden projects are excluded
    from LIST PROJECTS display. If an auto-unhide date is provided, the project will
    automatically become visible again on or after that date.

    Args:
        state: State dictionary (modified in place).
        project_name: Name of project to hide (normalized to uppercase).
        until: Optional auto-unhide date in mmddyyyy format (e.g., "12252025" for Dec 25, 2025).
               None for indefinite hiding until manually unhidden.

    Returns:
        bool: True if project existed and was hidden, False if project not found.
    """
    pname = project_name.strip().upper()
    if pname not in state.get("project_tasks", {}):
        return False
    pm = state.setdefault("projects_meta", {})
    pm.setdefault(pname, {"hidden": False, "unhide_date": None})
    pm[pname]["hidden"] = True
    pm[pname]["unhide_date"] = until
    save_state(state)
    return True


def unhide_project(state: State, project_name: str) -> bool:
    """Make a previously hidden project visible in standard project listings.

    Clears the hidden flag and unhide_date in projects_meta, restoring the project
    to normal visibility in LIST PROJECTS display.

    Args:
        state: State dictionary (modified in place).
        project_name: Name of project to unhide (normalized to uppercase).

    Returns:
        bool: True if project existed and was unhidden, False if project not found.
    """
    pname = project_name.strip().upper()
    if pname not in state.get("project_tasks", {}):
        return False
    pm = state.setdefault("projects_meta", {})
    pm.setdefault(pname, {"hidden": False, "unhide_date": None})
    pm[pname]["hidden"] = False
    pm[pname]["unhide_date"] = None
    save_state(state)
    return True


def list_hide(state: State) -> List[Tuple[Optional[str], str, Optional[str]]]:
    """List all currently hidden projects with their auto-unhide dates.

    Scans projects_meta to find all projects with hidden flag set to True.
    Returns project metadata for display by LIST HIDE command.

    Args:
        state: State dictionary (read-only access).

    Returns:
        list: List of tuples (project_number: str|None, project_name: str, unhide_date: str|None)
              where project_number is 3-digit ID, project_name is uppercase name, and
              unhide_date is mmddyyyy format or None for indefinite hiding.
    """
    out = []
    pm = state.get("projects_meta", {}) or {}
    pnums = state.get("project_numbers", {}) or {}
    for proj, meta in pm.items():
        if meta.get("hidden"):
            pnum = pnums.get(proj)
            out.append((pnum, proj, meta.get("unhide_date")))
    return out


def list_open_projects_and_tasks(state: State) -> Dict[str, List[Task]]:
    """Build mapping of projects to their open tasks for display purposes.

    Iterates through all projects and collects tasks with status="open".
    Only includes projects that have at least one open task. Used by LIST PROJECTS
    command to render the hierarchical project -> task view.

    Args:
        state: State dictionary (read-only access).

    Returns:
        dict: Mapping of project_name (str) -> list of open task objects (dict).
              Each task dict contains: id, description, project_name, status,
              value_flag, deadline_mmddyyyy, completed_at (if applicable).
    """
    out = {}
    for proj, tids in (state.get("project_tasks") or {}).items():
        open_tasks = []
        for tid in tids:
            t = state.get("tasks", {}).get(tid)
            if t and t.get("status") == "open":
                open_tasks.append(t)
        if open_tasks:
            out[proj] = open_tasks
    return out
