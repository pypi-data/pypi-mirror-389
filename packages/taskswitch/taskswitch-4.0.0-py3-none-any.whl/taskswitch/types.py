"""Core data structure type definitions for the time tracker application.

This module defines TypedDict types for all application data structures to provide
type safety and documentation for the state dictionary and its nested objects.
"""

from datetime import datetime
from typing import Dict, List, Optional, TypedDict


class Task(TypedDict):
    """Task object representing a single trackable work item.

    Attributes:
        id: 4-digit zero-padded task identifier (e.g., "0001", "0042").
        description: User-provided task description text.
        project_name: Uppercase project name to which this task belongs.
        status: Task lifecycle status, either "open" or "complete".
        value_flag: High-value marker set by '!!!' command.
        deadline_mmddyyyy: Optional deadline in mmddyyyy format (e.g., "12252025").
        completed_at: Optional ISO 8601 UTC timestamp when task was marked complete.
    """

    id: str
    description: str
    project_name: str
    status: str
    value_flag: bool
    deadline_mmddyyyy: Optional[str]
    completed_at: Optional[str]


class ProjectMeta(TypedDict):
    """Project metadata for visibility and hiding features.

    Attributes:
        hidden: Whether the project is currently hidden from standard listings.
        unhide_date: Optional auto-unhide date in mmddyyyy format (e.g., "12252025").
    """

    hidden: bool
    unhide_date: Optional[str]


class Session(TypedDict):
    """Time tracking session representing a completed work interval.

    Attributes:
        task_name: Full task display name (e.g., "[0001] Description (PROJECT)").
        duration_seconds: Elapsed time for this session in seconds.
        end_timestamp: ISO 8601 UTC timestamp when the session ended.
    """

    task_name: str
    duration_seconds: float
    end_timestamp: str


class State(TypedDict):
    """Complete application state dictionary.

    This is the root state object that gets persisted to current_state.json
    and loaded at application startup. All application data flows through this
    central state dictionary.

    Attributes:
        active_task: Currently active task display name, or None if no task active.
        start_time: UTC datetime when current task timer started, or None.
        task_times: List of completed time tracking sessions.
        active_project: Last used project name for TASK shorthand commands.
        priority_projects: Up to 3 project names in most-recent-first order.
        project_numbers: Mapping of project names to 3-digit IDs (e.g., "001").
        projects_meta: Per-project metadata for hiding and visibility features.
        project_counter: Counter for generating next sequential 3-digit project ID.
        last_summary_date: ISO date string of last generated daily summary.
        global_task_counter: Counter for generating next sequential 4-digit task ID.
        tasks: All task objects keyed by 4-digit task ID.
        project_tasks: Mapping of project names to lists of task IDs.
        last_list_view: User's last viewed list type, either "PROJECTS" or "PRIORITY".
    """

    active_task: Optional[str]
    start_time: Optional[datetime]
    task_times: List[Session]
    active_project: Optional[str]
    priority_projects: List[str]
    project_numbers: Dict[str, str]
    projects_meta: Dict[str, ProjectMeta]
    project_counter: int
    last_summary_date: Optional[str]
    global_task_counter: int
    tasks: Dict[str, Task]
    project_tasks: Dict[str, List[str]]
    last_list_view: str
