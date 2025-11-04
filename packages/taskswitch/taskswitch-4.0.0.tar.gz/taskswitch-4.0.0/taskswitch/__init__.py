#!/usr/bin/env python3
"""taskswitch package init.

Top-level package marker for the simple-time-tracker refactor.
Exposes commonly used functions and constants from submodules.
"""

__version__ = "4.0.0"

# Command handlers
from .commands import (
    create_and_switch_task_for_project,
    handle_add_priority,
    handle_add_project,
    handle_add_task,
    handle_clear_screen,
    handle_delete_project,
    handle_delete_project_by_number,
    handle_delete_task,
    handle_end_priority,
    handle_end_project,
    handle_end_project_by_number,
    handle_end_tasks,
    handle_force_summary,
    handle_hide_project,
    handle_list_hide,
    handle_list_priority,
    handle_list_projects,
    handle_list_single_project,
    handle_list_tasks,
    handle_move_task,
    handle_project_as_task,
    handle_set_task_deadline,
    handle_start_task,
    handle_start_text_task,
    handle_task_shorthand,
    handle_toggle_task_value,
    handle_unhide_project,
)

# Configuration constants
from .config import LOGS_DIR, STATE_FILE, TIMEZONE_STR

# Display functions
from .display import (
    _format_task_display,
    contextual_refresh_for_projects,
    list_hidden_projects,
    list_priority,
    list_projects,
)

# Reporting functions
from .reporting import check_and_summarize_if_needed, summarize_day

# Interactive shell
from .shell import TaskSwitchShell

# State management functions (using database backend)
from .db_state_manager import (
    add_priority,
    add_project,
    add_task,
    add_task_without_project,
    delete_project,
    delete_task,
    end_project,
    end_task,
    end_tasks,
    get_task,
    get_task_by_description,
    hide_project,
    list_hide,
    list_open_projects_and_tasks,
    load_state,
    move_task,
    remove_priority,
    save_state,
    unhide_project,
)

# Timer management functions
from .timer import finalize_current_task_time, post_end_switch_to_break

# Utility functions
from .utils import (
    _color_bracket_for_task,
    _deadline_days_remaining,
    _ensure_dir_for_file,
    _format_due_date_for_display,
    _get_tz,
    _project_is_visible,
    clear_screen,
    format_seconds_to_human_with_date,
    format_time,
)

__all__ = [
    # Version
    "__version__",
    # Config
    "LOGS_DIR",
    "TIMEZONE_STR",
    "STATE_FILE",
    # Utils
    "_get_tz",
    "_ensure_dir_for_file",
    "format_seconds_to_human_with_date",
    "format_time",
    "_deadline_days_remaining",
    "_format_due_date_for_display",
    "_color_bracket_for_task",
    "_project_is_visible",
    "clear_screen",
    # Timer management
    "finalize_current_task_time",
    "post_end_switch_to_break",
    # Reporting
    "summarize_day",
    "check_and_summarize_if_needed",
    # Display
    "_format_task_display",
    "list_hidden_projects",
    "list_projects",
    "list_priority",
    "contextual_refresh_for_projects",
    # State management
    "load_state",
    "save_state",
    "get_task",
    "get_task_by_description",
    "add_project",
    "add_task",
    "add_task_without_project",
    "end_task",
    "end_tasks",
    "end_project",
    "delete_project",
    "delete_task",
    "hide_project",
    "unhide_project",
    "list_hide",
    "add_priority",
    "remove_priority",
    "list_open_projects_and_tasks",
    # Command handlers
    "handle_force_summary",
    "handle_set_task_deadline",
    "handle_toggle_task_value",
    "handle_clear_screen",
    "handle_end_priority",
    "handle_end_project_by_number",
    "handle_delete_project_by_number",
    "handle_hide_project",
    "handle_unhide_project",
    "handle_add_project",
    "handle_add_priority",
    "handle_add_task",
    "handle_list_hide",
    "handle_list_projects",
    "handle_list_single_project",
    "handle_list_priority",
    "handle_list_tasks",
    "handle_move_task",
    "handle_end_project",
    "handle_end_tasks",
    "handle_delete_project",
    "handle_delete_task",
    "handle_start_task",
    "handle_start_text_task",
    "handle_task_shorthand",
    "handle_project_as_task",
    "create_and_switch_task_for_project",
    # Shell
    "TaskSwitchShell",
]
