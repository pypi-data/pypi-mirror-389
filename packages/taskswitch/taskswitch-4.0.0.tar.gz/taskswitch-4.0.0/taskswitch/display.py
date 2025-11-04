"""Display and presentation logic for the time tracker application.

This module handles all console output and UI presentation, separating the
presentation layer from business logic. Functions accept data as arguments
rather than directly accessing state_manager, making them pure presentation functions.
"""

from typing import Dict, Iterable, List, Optional, Tuple, Union

from .db_state_manager import get_task, list_open_projects_and_tasks  # Using database backend
from .types import State, Task
from .utils import (
    _color_bracket_for_task,
    _format_due_date_for_display,
    _project_is_visible,
    clear_screen,
)


def _format_task_display(state: State) -> str:
    """Format the currently active task for display in the status line.

    Looks up the active task by ID and formats it with task ID, description,
    deadline (if present), and project name. Falls back to raw active_task
    string if lookup fails.

    Args:
        state: State dictionary containing active_task and tasks.

    Returns:
        str: Formatted task display like "Current: [0001] Task desc (Due: 12/25/2025) (PROJECT)"
             or "No active task" if none is active.
    """
    active = state.get("active_task")
    if not active:
        return "No active task"
    # active key expected to be like [####] Description (Project)
    # But we store task ids; try to lookup
    if active.startswith("[") and "]" in active:
        tid = active[1:5]
        t = get_task(state, tid)
        if t:
            return f"Current: [{t['id']}] {t.get('description','')}{_format_due_date_for_display(t)} ({t['project_name']})"
    return f"Current: {active}"


def list_hidden_projects(
    hidden_list: List[Tuple[Optional[str], str, Optional[str]]],
) -> None:
    """Display all currently hidden projects with their auto-unhide dates.

    Pure presentation function that prints hidden projects in a formatted list
    showing project number, name, and unhide date (if scheduled).

    Args:
        hidden_list: List of tuples (project_number, project_name, unhide_date)
                     where project_number is 3-digit ID or None, project_name is
                     uppercase name, and unhide_date is mmddyyyy format or None
                     for indefinite hiding.
    """
    if not hidden_list:
        print("(no hidden projects)")
        return
    print("")
    for pnum, proj, ud in hidden_list:
        display_num = f"[{pnum}]" if pnum else "[---]"
        ud_display = ud or "Indefinite"
        print(f"{display_num} {proj}  -> Unhide: {ud_display}")
    print("")


def list_projects(
    inventory: Dict[str, List[Task]], project_numbers: Dict[str, str], state: State
) -> None:
    """Display all open projects with their tasks, respecting visibility settings.

    Pure presentation function that prints hierarchical project -> task view
    excluding hidden projects. Shows project numbers, color-coded task IDs
    based on deadlines, task descriptions, and due dates.

    Args:
        inventory: Mapping of project_name -> list of open task dicts
        project_numbers: Mapping of project_name -> 3-digit project ID
        state: State dictionary for visibility checks (projects_meta)
    """
    if not inventory:
        print("No open projects.")
        return
    print("")
    
    # Separate UNASSIGNED from regular projects
    unassigned_tasks = inventory.pop('UNASSIGNED', None)
    proj_items = list(inventory.items())
    
    for i, (proj, tasks) in enumerate(proj_items):
        if not _project_is_visible(state, proj):
            continue
        pnum = project_numbers.get(proj)
        header = f"{proj.upper()}"
        if pnum:
            header = f"[{pnum}] {header}"
        print(header)
        if tasks:
            for t in tasks:
                bracket = _color_bracket_for_task(t)
                print(
                    f"{bracket} {t.get('description','')}{_format_due_date_for_display(t)}"
                )
        else:
            # Show placeholder for projects with no tasks
            print("  (no tasks yet)")
        if i != len(proj_items) - 1:
            print("-----")
    
    # Display unassigned tasks at the end if any exist
    if unassigned_tasks:
        if proj_items:  # Add separator if there were regular projects
            print("-----")
        print("UNASSIGNED TASKS")
        for t in unassigned_tasks:
            bracket = _color_bracket_for_task(t)
            print(
                f"{bracket} {t.get('description','')}{_format_due_date_for_display(t)}"
            )
    
    print("")


def list_priority(
    priority_projects: List[str],
    inventory: Dict[str, List[Task]],
    project_numbers: Dict[str, str],
    state: State,
) -> None:
    """Display the priority projects list with formatted task details.

    Pure presentation function that prints the LIST PRIORITY output, showing
    up to 3 priority projects in most-recent-first order. The output includes:
    - A "PRIORITY" section header
    - Each visible (non-hidden) priority project with its 3-digit project number
    - All open tasks for each project with colored bracket IDs and deadline info
    - Visual separators (-----) between projects
    - Appropriate spacing before and after the list

    Filtering and display rules:
    - Projects marked as hidden are skipped unless their unhide_date has passed
    - Tasks are displayed with color-coded bracket IDs based on deadline urgency
    - Task descriptions include optional deadline annotations "(Due: mm/dd/yyyy)"
    - Project headers show the 3-digit project number if available: "[001] PROJECTNAME"

    Args:
        priority_projects: List of up to 3 project names in most-recent-first order
        inventory: Mapping of project_name -> list of open task dicts
        project_numbers: Mapping of project_name -> 3-digit project ID
        state: State dictionary for visibility checks (projects_meta)
    """
    if not priority_projects:
        print("No priority projects set.")
        return

    # Header with spacing
    print("")
    print("PRIORITY")
    print("")

    # Iterate through priority projects in most-recent-first order
    for index, project_name in enumerate(priority_projects):
        # Skip hidden projects unless unhide_date has passed
        if not _project_is_visible(state, project_name):
            continue

        # Build project header with optional 3-digit project number
        project_number = project_numbers.get(project_name)
        header = f"{project_name}"
        if project_number:
            header = f"[{project_number}] {header}"
        print(header)

        # Display all open tasks for this project
        project_inventory = inventory.get(project_name, [])
        for task in project_inventory:
            colored_bracket = _color_bracket_for_task(task)
            task_description = task.get("description", "")
            due_date_display = _format_due_date_for_display(task)
            print(f"{colored_bracket} {task_description}{due_date_display}")

        # Print separator between projects (but not after the last one)
        if index != len(priority_projects) - 1:
            print("-----")

    # Closing spacing
    print("")


def contextual_refresh_for_projects(
    state: State, proj_names: Union[str, Iterable[str], None]
) -> None:
    """Execute session-aware contextual auto-refresh after administrative updates.

    This function implements the session-aware view refresh logic by:
    1. Clearing the terminal screen via clear_screen()
    2. Restoring the user's last viewed list (PRIORITY or PROJECTS) based on
       the persistent state['last_list_view'] preference
    3. Falling back to project-membership heuristics if no preference is set

    The refresh preserves the user's workflow context without modifying active timers
    or finalizing running tasks. This is invoked after admin commands like task updates
    ([####] !!!), deadline changes ([####] [mmddyyyy]), and project/task lifecycle
    operations (ADD, END, DELETE).

    Args:
        state: The current application state dictionary containing task data,
               project metadata, and the last_list_view preference.
        proj_names: A single project name (str), an iterable of project names,
                    or None. Used for fallback heuristic when last_list_view is unset.
                    If a project in proj_names is found in priority_projects,
                    LIST PRIORITY is shown; otherwise LIST PROJECTS is shown.

    Returns:
        None. Outputs directly to the terminal via print statements.
    """
    clear_screen()

    # Fetch data needed for display
    inventory = list_open_projects_and_tasks(state)
    project_numbers = state.get("project_numbers", {})
    priority_projects_list = state.get("priority_projects", []) or []

    # Honor the user's persisted last-list view preference (session-aware behavior)
    last_view = state.get("last_list_view")
    if last_view == "PRIORITY":
        list_priority(priority_projects_list, inventory, project_numbers, state)
        return
    if last_view == "PROJECTS":
        list_projects(inventory, project_numbers, state)
        return

    # Fallback behavior: if no last_list_view is present, determine by project membership
    if not proj_names:
        list_projects(inventory, project_numbers, state)
        return
    if isinstance(proj_names, str):
        proj_iter = [proj_names]
    else:
        proj_iter = list(proj_names)
    for proj in proj_iter:
        if proj and proj in priority_projects_list:
            list_priority(priority_projects_list, inventory, project_numbers, state)
            return
    list_projects(inventory, project_numbers, state)
