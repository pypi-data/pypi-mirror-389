"""Command handlers for the time tracker application.

This module contains dedicated functions for each user command, separating
command logic from parsing logic. Each function takes state and relevant
arguments, executes the command logic, and returns any results or messages.
"""

from datetime import date, datetime
from typing import Iterable, List, Optional, Tuple, Union

import pytz

from .display import (
    _format_task_display,
    contextual_refresh_for_projects,
    list_hidden_projects,
    list_priority,
    list_projects,
)
from .reporting import summarize_day
from .db_state_manager import (  # Using database backend
    add_priority,
    add_project,
    add_task,
    delete_project,
    delete_task,
    end_project,
    end_tasks,
    get_task,
    hide_project,
    list_hide,
    list_open_projects_and_tasks,
    remove_priority,
    save_state,
    unhide_project,
)
from .timer import finalize_current_task_time, post_end_switch_to_break
from .types import State
from .utils import _format_due_date_for_display, _get_tz, clear_screen
from .logging_config import get_commands_logger

# Get logger for command operations
logger = get_commands_logger()


def handle_force_summary(state: State, date_str: str) -> Tuple[bool, str]:
    """Handle FORCE_SUMMARY command for development/debugging.

    Args:
        state: State dictionary
        date_str: Date in mmddyyyy format

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        mm = int(date_str[0:2])
        dd = int(date_str[2:4])
        yyyy = int(date_str[4:8])
        target = date(yyyy, mm, dd)
        summarize_day(state, target)
        return True, f"Forced summary for {target.isoformat()} completed."
    except Exception:
        return False, "Invalid date for FORCE_SUMMARY. Use mmddyyyy."


def handle_set_task_deadline(
    state: State, task_id: str, deadline_str: str
) -> Tuple[bool, str]:
    """Handle setting a task deadline ([####] [mmddyyyy]).

    Args:
        state: State dictionary
        task_id: 4-digit task ID
        deadline_str: Deadline in mmddyyyy format

    Returns:
        tuple: (success: bool, message: str)
    """
    t = get_task(state, task_id)
    if not t:
        return False, f"Task {task_id} not found."

    try:
        mm = int(deadline_str[0:2])
        dd = int(deadline_str[2:4])
        yyyy = int(deadline_str[4:8])
        # basic validation
        datetime(yyyy, mm, dd)
        # Administrative change: do not finalize or touch the active timer
        t["deadline_mmddyyyy"] = f"{mm:02d}{dd:02d}{yyyy:04d}"
        save_state(state)

        # Session-aware contextual auto-refresh
        contextual_refresh_for_projects(state, t.get("project_name"))
        return True, f"Task [{task_id}] deadline set to {mm:02d}/{dd:02d}/{yyyy:04d}."
    except Exception:
        return False, f"Invalid date format: {deadline_str}. Use mmddyyyy."


def handle_toggle_task_value(state: State, task_id: str) -> Tuple[bool, str]:
    """Handle toggling a task's value flag ([####] !!!).

    Args:
        state: State dictionary
        task_id: 4-digit task ID

    Returns:
        tuple: (success: bool, message: str)
    """
    t = get_task(state, task_id)
    if not t:
        return False, f"Task {task_id} not found."

    # Administrative change: toggle value_flag (invert boolean) without touching timers
    current_flag_value = bool(t.get("value_flag"))
    t["value_flag"] = not current_flag_value
    save_state(state)

    # Session-aware contextual auto-refresh
    contextual_refresh_for_projects(state, t.get("project_name"))

    if t["value_flag"]:
        return True, f"Task [{task_id}] marked as high value (!!!)."
    else:
        return True, f"Task [{task_id}] unmarked as high value."


def handle_clear_screen(state: State) -> Tuple[bool, str]:
    """Handle clear screen command (CLS/CLEAR).

    Args:
        state: State dictionary

    Returns:
        tuple: (success: bool, message: str)
    """
    clear_screen()
    return True, "Screen cleared."


def handle_end_project_by_number(state: State, project_number: str) -> Tuple[bool, str]:
    """Handle ending a project by 3-digit project number.

    Args:
        state: State dictionary
        project_number: 3-digit project number

    Returns:
        tuple: (success: bool, message: str)
    """
    proj_map = state.get("project_numbers", {})
    inv = {v: k for k, v in proj_map.items()}
    pname = inv.get(project_number)
    if not pname:
        return False, f"Project number '{project_number}' not found."

    ok = end_project(state, pname)
    return ok, f"Ended project '{pname}' (#{project_number}): {ok}"


def handle_delete_project_by_number(
    state: State, project_number: str
) -> Tuple[bool, str]:
    """Handle deleting a project by 3-digit project number.

    Args:
        state: State dictionary
        project_number: 3-digit project number

    Returns:
        tuple: (success: bool, message: str)
    """
    proj_map = state.get("project_numbers", {})
    inv = {v: k for k, v in proj_map.items()}
    pname = inv.get(project_number)
    if not pname:
        return False, f"Project number '{project_number}' not found."

    ok = delete_project(state, pname)
    return ok, f"Deleted project '{pname}' (#{project_number}): {ok}"


def handle_hide_project(
    state: State, project_identifier: str, until_date: Optional[str] = None
) -> Tuple[bool, str]:
    """Handle hiding a project with optional auto-unhide date.

    Args:
        state: State dictionary
        project_identifier: Project name or 1-3 digit project number
        until_date: Optional unhide date in mmddyyyy format

    Returns:
        tuple: (success: bool, message: str)
    """
    # Check if identifier is a 1-3 digit project number
    pname = project_identifier
    if project_identifier.strip().isdigit() and 1 <= len(project_identifier.strip()) <= 3:
        # Pad to 3 digits
        project_number = f"{int(project_identifier.strip()):03d}"
        inv = {v: k for k, v in state.get("project_numbers", {}).items()}
        pname = inv.get(project_number)
        if not pname:
            return False, f"Project number '{project_identifier}' (padded: {project_number}) not found."
    else:
        pname = project_identifier.strip().upper()

    ok = hide_project(state, pname, until_date)
    if ok:
        contextual_refresh_for_projects(state, pname)
    return ok, f"Hide project '{pname}': {ok} (until={until_date})"


def handle_unhide_project(state: State, project_identifier: str) -> Tuple[bool, str]:
    """Handle unhiding a project.

    Args:
        state: State dictionary
        project_identifier: Project name or 1-3 digit project number

    Returns:
        tuple: (success: bool, message: str)
    """
    # Check if identifier is a 1-3 digit project number
    pname = project_identifier
    if project_identifier.strip().isdigit() and 1 <= len(project_identifier.strip()) <= 3:
        # Pad to 3 digits
        project_number = f"{int(project_identifier.strip()):03d}"
        inv = {v: k for k, v in state.get("project_numbers", {}).items()}
        pname = inv.get(project_number)
        if not pname:
            return False, f"Project number '{project_identifier}' (padded: {project_number}) not found."
    else:
        pname = project_identifier.strip().upper()

    ok = unhide_project(state, pname)
    if ok:
        contextual_refresh_for_projects(state, pname)
    return ok, f"Unhide project '{pname}': {ok}"


def handle_add_project(state: State, project_name: str) -> Tuple[bool, str]:
    """Handle adding a new project.

    Args:
        state: State dictionary
        project_name: Name of the project to add

    Returns:
        tuple: (success: bool, message: str)
    """
    ok = add_project(state, project_name)
    if ok:
        state["active_project"] = project_name.strip().upper()
        save_state(state)
        # contextual refresh for the newly added project
        contextual_refresh_for_projects(state, project_name.strip().upper())
    return ok, f"Added project '{project_name}': {ok}"


def handle_add_priority(state: State, project_identifiers: List[str]) -> Tuple[bool, str]:
    """Handle adding one or more projects to the priority list.

    Args:
        state: State dictionary
        project_identifiers: List of project names or 1-3 digit project numbers

    Returns:
        tuple: (success: bool, message: str)
    """
    if not project_identifiers:
        return False, "No project identifiers provided"
    
    messages = []
    last_added = None
    
    for identifier in project_identifiers:
        # Resolve project number to name if needed
        pname = identifier.strip().upper()
        if identifier.strip().isdigit() and 1 <= len(identifier.strip()) <= 3:
            # Pad to 3 digits and look up project name by number
            project_number = f"{int(identifier.strip()):03d}"
            inv = {v: k for k, v in state.get("project_numbers", {}).items()}
            pname = inv.get(project_number)
            if not pname:
                messages.append(f"Project number '{identifier}' (padded: {project_number}) not found")
                continue
        
        # Ensure project exists before marking priority
        add_project(state, pname)
        ok = add_priority(state, pname)
        if ok:
            last_added = pname
            messages.append(f"Added priority project '{pname}'")
        else:
            messages.append(f"Failed to add priority project '{pname}'")
    
    # Set active project to the last successfully added project
    if last_added:
        state["active_project"] = last_added
        save_state(state)
        # Refresh display if user was viewing priority list
        contextual_refresh_for_projects(state, last_added)
    
    return True, "\n".join(messages)


def handle_end_priority(state: State, project_identifier: str) -> Tuple[bool, str]:
    """Handle removing a project from the priority list.

    Args:
        state: State dictionary
        project_identifier: Project name or 1-3 digit project number

    Returns:
        tuple: (success: bool, message: str)
    """
    # Resolve project number to name if needed
    pname = project_identifier.strip().upper()
    if project_identifier.strip().isdigit() and 1 <= len(project_identifier.strip()) <= 3:
        # Pad to 3 digits and look up project name by number
        project_number = f"{int(project_identifier.strip()):03d}"
        inv = {v: k for k, v in state.get("project_numbers", {}).items()}
        pname = inv.get(project_number)
        if not pname:
            return False, f"Project number '{project_identifier}' (padded: {project_number}) not found"
    
    ok = remove_priority(state, pname)
    if ok:
        # Refresh display if user was viewing priority list
        contextual_refresh_for_projects(state, pname)
        return True, f"Removed '{pname}' from priority list"
    else:
        return False, f"Project '{pname}' not in priority list"


def handle_add_task(
    state: State, project_name: str, description: str
) -> Tuple[bool, str]:
    """Handle adding a new task to a project.

    Args:
        state: State dictionary
        project_name: Name of the project
        description: Task description

    Returns:
        tuple: (success: bool, message: str with task_id)
    """
    tid = add_task(state, project_name, description)
    # set the active project to pname
    state["active_project"] = project_name.strip().upper()
    save_state(state)
    # contextual refresh for the project that received the new task
    contextual_refresh_for_projects(state, project_name.strip().upper())
    return True, f"Added task [{tid}] {description} (Project: {project_name})"


def handle_list_hide(state: State) -> Tuple[bool, str]:
    """Handle LIST HIDE command to display hidden projects.

    Args:
        state: State dictionary

    Returns:
        tuple: (success: bool, message: str)
    """
    hidden = list_hide(state)
    list_hidden_projects(hidden)
    return True, ""


def handle_list_projects(state: State) -> Tuple[bool, str]:
    """Handle LIST PROJECTS command.

    Args:
        state: State dictionary

    Returns:
        tuple: (success: bool, message: str)
    """
    inv = list_open_projects_and_tasks(state)
    project_numbers = state.get("project_numbers", {})
    list_projects(inv, project_numbers, state)
    # record user's last view
    state["last_list_view"] = "PROJECTS"
    save_state(state)
    return True, ""


def handle_list_single_project(state: State, project_identifier: str) -> Tuple[bool, str]:
    """Handle LIST PROJECTS ### or LIST PROJECTS ProjectName - show single project only.

    Args:
        state: State dictionary
        project_identifier: Project name or 1-3 digit project number

    Returns:
        tuple: (success: bool, message: str)
    """
    # Resolve project number to name if needed
    pname = project_identifier.strip().upper()
    if project_identifier.strip().isdigit() and 1 <= len(project_identifier.strip()) <= 3:
        # Pad to 3 digits and look up project name by number
        project_number = f"{int(project_identifier.strip()):03d}"
        inv = {v: k for k, v in state.get("project_numbers", {}).items()}
        pname = inv.get(project_number)
        if not pname:
            return False, f"Project number '{project_identifier}' (padded: {project_number}) not found"
    
    # Get all projects and filter to just the one requested
    inv = list_open_projects_and_tasks(state)
    if pname not in inv:
        return False, f"Project '{pname}' not found"
    
    # Create filtered inventory with just this project
    filtered_inv = {pname: inv[pname]}
    project_numbers = state.get("project_numbers", {})
    
    # Clear screen and display single project
    clear_screen()
    list_projects(filtered_inv, project_numbers, state)
    
    # record user's last view
    state["last_list_view"] = "PROJECTS"
    save_state(state)
    return True, ""


def handle_list_priority(state: State) -> Tuple[bool, str]:
    """Handle LIST PRIORITY command.

    Args:
        state: State dictionary

    Returns:
        tuple: (success: bool, message: str)
    """
    # Clear screen before displaying priority list
    clear_screen()
    inv = list_open_projects_and_tasks(state)
    priority_projects_list = state.get("priority_projects", [])
    project_numbers = state.get("project_numbers", {})
    list_priority(priority_projects_list, inv, project_numbers, state)
    # record user's last view
    state["last_list_view"] = "PRIORITY"
    save_state(state)
    return True, ""


def handle_list_tasks(
    state: State, project_name: Optional[str] = None
) -> Tuple[bool, str]:
    """Handle LIST TASKS command.

    Args:
        state: State dictionary
        project_name: Optional project name to filter tasks

    Returns:
        tuple: (success: bool, message: str)
    """
    inv = list_open_projects_and_tasks(state)
    if project_name:
        tasks = inv.get(project_name, [])
        if not tasks:
            print(f"No open tasks for project '{project_name}'.")
        else:
            for t in tasks:
                print(f" - [{t['id']}] {t['description']}")
    else:
        for proj, tasks in inv.items():
            print(f"Project: {proj}")
            for t in tasks:
                print(f" - [{t['id']}] {t['description']}")
    return True, ""


def handle_end_project(state: State, project_name: str) -> Tuple[bool, str]:
    """Handle ending a project by name.

    Args:
        state: State dictionary
        project_name: Name of the project to end

    Returns:
        tuple: (success: bool, message: str)
    """
    logger.info(f"Command: END project '{project_name}'")
    ok = end_project(state, project_name)
    if ok:
        contextual_refresh_for_projects(state, project_name.strip().upper())
    return ok, f"Ended project '{project_name}': {ok}"


def handle_end_tasks(state: State, task_ids: List[str]) -> Tuple[bool, str]:
    """Handle ending one or more tasks.

    Args:
        state: State dictionary
        task_ids: List of 4-digit task IDs

    Returns:
        tuple: (success: bool, message: str)
    """
    logger.info(f"Command: END tasks {task_ids}")
    # call batch end; end_tasks returns mapping
    results = end_tasks(state, task_ids)
    messages = []
    for tid, res in results.items():
        if res.get("ok"):
            messages.append(f"Ended task '{tid}': {res.get('message')}")
        else:
            messages.append(f"Failed to end task '{tid}': {res.get('message')}")

    # After ending tasks, switch to BREAK (start a break timer)
    post_end_switch_to_break(state)
    messages.append("Switched to BREAK")

    # contextual refresh for the projects affected by ended tasks
    affected_projects = []
    for tid in task_ids:
        t = state.get("tasks", {}).get(tid)
        if t:
            affected_projects.append(t.get("project_name"))
    contextual_refresh_for_projects(state, affected_projects)

    return True, "\n".join(messages)


def handle_delete_project(state: State, project_name: str) -> Tuple[bool, str]:
    """Handle deleting a project by name.

    Args:
        state: State dictionary
        project_name: Name of the project to delete

    Returns:
        tuple: (success: bool, message: str)
    """
    logger.warning(f"Command: DELETE project '{project_name}'")
    ok = delete_project(state, project_name)
    if ok:
        contextual_refresh_for_projects(state, project_name.strip().upper())
    return ok, f"Deleted project '{project_name}': {ok}"


def handle_delete_task(state: State, task_id: str) -> Tuple[bool, str]:
    """Handle deleting a task by ID.

    Args:
        state: State dictionary
        task_id: 4-digit task ID

    Returns:
        tuple: (success: bool, message: str)
    """
    logger.warning(f"Command: DELETE task '{task_id}'")
    ok = delete_task(state, task_id)
    return ok, f"Deleted task '{task_id}': {ok}"


def handle_move_task(state: State, task_id: str, project_identifier: str) -> Tuple[bool, str]:
    """Handle moving a task to a different project.

    Args:
        state: State dictionary
        task_id: 4-digit task ID
        project_identifier: Target project name or 1-3 digit project number

    Returns:
        tuple: (success: bool, message: str)
    """
    from .db_state_manager import move_task
    
    # Resolve project number to name if needed
    target_pname = project_identifier.strip().upper()
    if project_identifier.strip().isdigit() and 1 <= len(project_identifier.strip()) <= 3:
        # Pad to 3 digits and look up project name by number
        project_number = f"{int(project_identifier.strip()):03d}"
        inv = {v: k for k, v in state.get("project_numbers", {}).items()}
        target_pname = inv.get(project_number)
        if not target_pname:
            return False, f"Project number '{project_identifier}' (padded: {project_number}) not found"
    
    logger.info(f"Command: MOVE task '{task_id}' to project '{target_pname}'")
    ok, msg = move_task(state, task_id, target_pname)
    
    if ok:
        # Refresh display to show the changes
        contextual_refresh_for_projects(state, target_pname)
    
    return ok, msg


def handle_start_task(state: State, task_id: str) -> Tuple[bool, str]:
    """Handle starting/resuming a task by ID.

    Args:
        state: State dictionary
        task_id: 4-digit task ID

    Returns:
        tuple: (success: bool, message: str)
    """
    t = get_task(state, task_id)
    if not t:
        logger.warning(f"Command: START non-existent task '{task_id}'")
        return False, f"Task id '{task_id}' not found."

    # include due date in the active display if present
    desc = t.get("description", "")
    key = f"[{t['id']}] {desc}{_format_due_date_for_display(t)} ({t['project_name']})"
    if state.get("active_task") == key:
        return False, f"Already on '{key}'. No change."

    logger.info(f"Command: START task '{task_id}'")
    finalize_current_task_time(state)
    state["active_task"] = key
    state["start_time"] = datetime.now(pytz.utc)
    state.setdefault("task_times", [])
    save_state(state)

    timestamp = state["start_time"].astimezone(_get_tz()).strftime("%H:%M:%S %m-%d-%Y")
    return True, f"Switched to '{key}' at {timestamp}"


def handle_start_text_task(state: State, task_text: str) -> Tuple[bool, str]:
    """Handle starting a task by text (creates projectless task with task ID).

    Args:
        state: State dictionary
        task_text: Text description of the task

    Returns:
        tuple: (success: bool, message: str)
    """
    from .db_state_manager import add_task_without_project, get_task_by_description
    
    # Check if a task with this description already exists (projectless)
    existing_task = get_task_by_description(task_text, projectless_only=True)
    
    if existing_task:
        # Use existing task
        task_id = existing_task['task_id']
    else:
        # Create new projectless task with 4-digit ID
        task_id = add_task_without_project(state, task_text)
    
    key = f"[{task_id}]"
    if state.get("active_task") == key:
        return False, f"Already on task [{task_id}]. No change."

    logger.info(f"Command: START projectless task [{task_id}]: {task_text}")
    finalize_current_task_time(state)
    state["active_task"] = key
    state["start_time"] = datetime.now(pytz.utc)
    state.setdefault("task_times", [])
    save_state(state)

    timestamp = state["start_time"].astimezone(_get_tz()).strftime("%H:%M:%S %m-%d-%Y")
    return True, f"Started task [{task_id}]: {task_text} at {timestamp}"


def handle_task_shorthand(state: State, description: str) -> Tuple[bool, str]:
    """Handle TASK [Description] shorthand command.

    Args:
        state: State dictionary
        description: Task description

    Returns:
        tuple: (success: bool, message: str)
    """
    ap = state.get("active_project")
    if not ap:
        return (
            False,
            "No active project set. Use 'ADD PROJECT [Name]' or 'ADD [Project] TASK [Desc]')",
        )

    tid = add_task(state, ap, description)
    # After adding a task via the TASK shorthand, perform contextual auto-refresh
    contextual_refresh_for_projects(state, ap.strip().upper())
    return True, f"Added task [{tid}] {description} (Project: {ap})"


def create_and_switch_task_for_project(state: State, project_name: str) -> str:
    """Create a new task using project name as description and switch timer to it.

    Finalizes any currently active task, creates a new task with the project name
    as the description, and immediately starts a timer for that task. Used by the
    TASK shorthand command for quick project switching.

    Args:
        state: State dictionary (modified in place).
        project_name: Name of project for which to create task (normalized to uppercase).

    Returns:
        str: The newly assigned 4-digit task ID.
    """
    pname = project_name.strip().upper()
    # create a new task with project name as description
    tid = add_task(state, pname, pname)
    t = state["tasks"][tid]
    task_key = f"[{t['id']}] {t.get('description','')} ({t['project_name']})"
    finalize_current_task_time(state)
    state["active_task"] = task_key
    state["start_time"] = datetime.now(pytz.utc)
    state.setdefault("task_times", [])
    save_state(state)
    return tid


def handle_project_as_task(state: State, project_name: str) -> Tuple[bool, str]:
    """Handle entering an existing project name to create and switch to a task.

    Args:
        state: State dictionary
        project_name: Name of the existing project

    Returns:
        tuple: (success: bool, message: str with task_id)
    """
    tid = create_and_switch_task_for_project(state, project_name)
    return True, f"Created and switched to new task [{tid}] for project {project_name}"
