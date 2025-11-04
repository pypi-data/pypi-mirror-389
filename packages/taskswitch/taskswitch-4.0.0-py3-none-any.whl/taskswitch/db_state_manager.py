"""Database-backed state persistence using peewee ORM.

This module provides the same interface as state_manager.py but uses SQLite database
instead of JSON file storage.
"""

import json
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

import pytz

from .models import db, Project, Task, TimeEntry, Config
from .types import ProjectMeta, Session, State, Task as TaskType
from .utils import _ensure_dir_for_file
from .logging_config import get_database_logger

# Get logger for database operations
logger = get_database_logger()


def parse_iso_to_utc(s: Optional[str]) -> Optional[datetime]:
    """Parse an ISO 8601 datetime string and convert to UTC-aware datetime object."""
    if s is None:
        return None
    s2 = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s2)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=pytz.utc)
    return dt.astimezone(pytz.utc)


def iso_from_dt(dt: Optional[datetime]) -> Optional[str]:
    """Convert a datetime object to UTC ISO 8601 string format."""
    if dt is None:
        return None
    return dt.astimezone(pytz.utc).isoformat()


def _ensure_db_connected() -> None:
    """Ensure database connection is open."""
    if db.is_closed():
        logger.debug("Opening database connection")
        db.connect()
        logger.info("Database connection established")


def _get_config(key: str, default=None):
    """Get a config value by key."""
    _ensure_db_connected()
    try:
        config = Config.get(Config.key == key)
        return config.value
    except Config.DoesNotExist:
        return default


def _set_config(key: str, value):
    """Set a config value by key."""
    _ensure_db_connected()
    Config.insert(key=key, value=str(value)).on_conflict(
        conflict_target=[Config.key],
        update={Config.value: str(value)}
    ).execute()


def load_state() -> State:
    """Load application state from database.
    
    Returns a state dictionary compatible with the JSON-based interface.
    """
    logger.debug("Loading application state from database")
    _ensure_db_connected()
    
    # Load config values
    active_task = _get_config('active_task')
    start_time_str = _get_config('start_time')
    start_time = parse_iso_to_utc(start_time_str) if start_time_str else None
    active_project = _get_config('active_project')
    last_summary_date = _get_config('last_summary_date')
    global_task_counter = int(_get_config('global_task_counter', 0))
    project_counter = int(_get_config('project_counter', 0))
    last_list_view = _get_config('last_list_view', 'PROJECTS')
    
    # Load priority_projects from JSON
    priority_projects_json = _get_config('priority_projects', '[]')
    priority_projects = json.loads(priority_projects_json) if priority_projects_json else []
    
    # Build project_numbers mapping
    project_numbers = {}
    projects = list(Project.select())
    logger.debug(f"Loaded {len(projects)} projects from database")
    for project in projects:
        project_numbers[project.name] = project.number
    
    # Build projects_meta
    projects_meta = {}
    for project in projects:
        projects_meta[project.name] = {
            'hidden': project.is_hidden,
            'unhide_date': project.unhide_date.strftime('%m%d%Y') if project.unhide_date else None
        }
    
    # Build tasks dictionary
    tasks = {}
    all_tasks = list(Task.select())
    logger.debug(f"Loaded {len(all_tasks)} tasks from database")
    for task in all_tasks:
        tasks[task.task_id] = {
            'id': task.task_id,
            'description': task.description,
            'project_name': task.project.name if task.project else None,
            'status': task.status,
            'value_flag': task.is_value,
            'deadline_mmddyyyy': task.deadline.strftime('%m%d%Y') if task.deadline else None,
        }
        if task.completed_at:
            # Handle both datetime objects and ISO strings (from migration)
            if isinstance(task.completed_at, str):
                tasks[task.task_id]['completed_at'] = task.completed_at
            else:
                tasks[task.task_id]['completed_at'] = task.completed_at.isoformat()
    
    # Build project_tasks mapping
    project_tasks = {}
    for project in Project.select():
        project_tasks[project.name] = [
            task.task_id for task in project.tasks.where(Task.status == 'open')
        ]
    
    # Build task_times list
    task_times = []
    time_entries = list(TimeEntry.select().order_by(TimeEntry.end_timestamp))
    logger.debug(f"Loaded {len(time_entries)} time entries from database")
    for entry in time_entries:
        # Handle both datetime objects and ISO strings (from migration)
        if isinstance(entry.end_timestamp, str):
            end_ts = entry.end_timestamp
        else:
            end_ts = entry.end_timestamp.isoformat()
        
        task_times.append({
            'task_name': entry.task_name,
            'duration_seconds': entry.duration_seconds,
            'end_timestamp': end_ts
        })
    
    logger.info("Application state loaded successfully")
    return {
        'active_task': active_task,
        'start_time': start_time,
        'task_times': task_times,
        'active_project': active_project,
        'priority_projects': priority_projects,
        'project_numbers': project_numbers,
        'projects_meta': projects_meta,
        'project_counter': project_counter,
        'last_summary_date': last_summary_date,
        'global_task_counter': global_task_counter,
        'tasks': tasks,
        'project_tasks': project_tasks,
        'last_list_view': last_list_view,
    }


def save_state(state: State) -> None:
    """Save application state to database.
    
    This is called frequently by other functions, but since we update the database
    immediately on each operation, this can be a lightweight operation that just
    ensures config values are synced.
    """
    logger.debug("Saving state configuration values")
    _ensure_db_connected()
    
    # Update config values
    _set_config('active_task', state.get('active_task') or '')
    _set_config('start_time', iso_from_dt(state.get('start_time')) or '')
    _set_config('active_project', state.get('active_project') or '')
    _set_config('last_summary_date', state.get('last_summary_date') or '')
    _set_config('global_task_counter', int(state.get('global_task_counter', 0)))
    _set_config('project_counter', int(state.get('project_counter', 0)))
    _set_config('last_list_view', state.get('last_list_view', 'PROJECTS'))
    
    # Save priority_projects as JSON
    _set_config('priority_projects', json.dumps(state.get('priority_projects', [])))
    logger.debug("State configuration saved")


def _next_task_id(state: State) -> str:
    """Generate next sequential 4-digit task ID."""
    state["global_task_counter"] = int(state.get("global_task_counter", 0)) + 1
    _set_config('global_task_counter', state["global_task_counter"])
    return f"{state['global_task_counter']:04d}"


def add_project(state: State, project_name: str) -> bool:
    """Create a new project in the database."""
    _ensure_db_connected()
    
    pname = project_name.strip().upper()
    logger.debug(f"Adding project: {pname}")
    
    # Check if project already exists
    existing = Project.select().where(Project.name == pname).count()
    if existing > 0:
        logger.warning(f"Project already exists: {pname}")
        return False
    
    # Generate project number
    state["project_counter"] = int(state.get("project_counter", 0)) + 1
    project_number = f"{state['project_counter']:03d}"
    
    # Create project
    Project.create(
        name=pname,
        number=project_number,
        is_priority=False,
        is_hidden=False,
        unhide_date=None
    )
    
    logger.info(f"Project created: {pname} (#{project_number})")
    save_state(state)
    return True


def add_priority(state: State, project_name: str) -> bool:
    """Add or move a project to the top of the priority list."""
    normalized_project_name = project_name.strip().upper()
    priority_list = state.setdefault("priority_projects", [])

    # Move to front: remove from current position if already present
    if normalized_project_name in priority_list:
        priority_list.remove(normalized_project_name)

    # Insert at the front
    priority_list.insert(0, normalized_project_name)

    # Enforce maximum capacity of 3 items
    while len(priority_list) > 3:
        priority_list.pop()

    save_state(state)
    return True


def remove_priority(state: State, project_name: str) -> bool:
    """Remove a project from the priority list.
    
    Args:
        state: State dictionary
        project_name: Name of the project to remove from priority
        
    Returns:
        bool: True if project was removed, False if not in priority list
    """
    normalized_project_name = project_name.strip().upper()
    priority_list = state.setdefault("priority_projects", [])
    
    if normalized_project_name in priority_list:
        priority_list.remove(normalized_project_name)
        save_state(state)
        logger.info(f"Removed project from priority: {normalized_project_name}")
        return True
    
    logger.warning(f"Project not in priority list: {normalized_project_name}")
    return False


def add_task(state: State, project_name: str, description: str) -> str:
    """Create a new task in the database."""
    _ensure_db_connected()
    
    pname = project_name.strip().upper()
    logger.debug(f"Adding task to project {pname}")
    
    # Ensure project exists
    try:
        project = Project.get(Project.name == pname)
    except Project.DoesNotExist:
        # Create project if it doesn't exist
        add_project(state, pname)
        project = Project.get(Project.name == pname)
    
    # Generate task ID
    tid = _next_task_id(state)
    
    # Detect value_flag marker '!!!'
    value_flag = "!!!" in description
    
    # Detect optional deadline in mmddyyyy format
    deadline = None
    parts = description.split()
    for p in parts:
        if len(p) == 8 and p.isdigit():
            try:
                mm = int(p[0:2])
                dd = int(p[2:4])
                yyyy = int(p[4:8])
                deadline_date = date(yyyy, mm, dd)
                deadline = deadline_date
                break
            except Exception:
                pass
    
    # Create task
    Task.create(
        task_id=tid,
        description=description,
        project=project,
        status='open',
        completed_at=None,
        is_value=value_flag,
        deadline=deadline
    )
    
    logger.info(f"Task created: {tid} for project {pname}")
    return tid


def add_task_without_project(state: State, description: str) -> str:
    """Create a new task without associating it to any project (projectless task).
    
    Args:
        state: State dictionary
        description: Task description
        
    Returns:
        str: 4-digit task ID
    """
    _ensure_db_connected()
    
    logger.debug(f"Adding projectless task: {description}")
    
    # Generate task ID
    tid = _next_task_id(state)
    
    # Detect value_flag marker '!!!'
    value_flag = "!!!" in description
    
    # Detect optional deadline in mmddyyyy format
    deadline = None
    parts = description.split()
    for p in parts:
        if len(p) == 8 and p.isdigit():
            try:
                mm = int(p[0:2])
                dd = int(p[2:4])
                yyyy = int(p[4:8])
                deadline_date = date(yyyy, mm, dd)
                deadline = deadline_date
                break
            except Exception:
                pass
    
    # Create task without project (project=None)
    Task.create(
        task_id=tid,
        description=description,
        project=None,  # No project for projectless tasks
        status='open',
        completed_at=None,
        is_value=value_flag,
        deadline=deadline
    )
    
    logger.info(f"Projectless task created: {tid}")
    return tid


def get_task_by_description(description: str, projectless_only: bool = False) -> Optional[Dict[str, Any]]:
    """Find a task by its description text.
    
    Args:
        description: Task description to search for
        projectless_only: If True, only search for tasks without a project
        
    Returns:
        Task dictionary if found, None otherwise
    """
    _ensure_db_connected()
    
    try:
        query = Task.select().where(
            Task.description == description,
            Task.status == 'open'
        )
        
        if projectless_only:
            query = query.where(Task.project.is_null())
        
        task = query.get()
        
        return {
            'task_id': task.task_id,
            'description': task.description,
            'status': task.status,
            'is_value': task.is_value,
            'deadline': task.deadline,
            'project_name': task.project.name if task.project else None
        }
    except Task.DoesNotExist:
        return None


def end_task(state: State, task_id: str) -> Tuple[bool, str]:
    """Mark a task as complete in the database."""
    _ensure_db_connected()
    
    try:
        task = Task.get(Task.task_id == task_id)
        task.status = 'complete'
        task.completed_at = datetime.now(pytz.utc)
        task.save()
        logger.info(f"Task completed: {task_id}")
        return True, f"Ended task {task_id}"
    except Task.DoesNotExist:
        logger.warning(f"Attempted to end non-existent task: {task_id}")
        return False, f"Task {task_id} not found"


def end_tasks(state: State, task_ids: List[str]) -> Dict[str, Dict[str, any]]:
    """Mark multiple tasks as complete."""
    results = {}
    for tid in task_ids:
        ok, msg = end_task(state, tid)
        results[tid] = {"ok": bool(ok), "message": msg}
    return results


def end_project(state: State, project_name: str) -> bool:
    """Mark all tasks in a project as complete and remove project."""
    _ensure_db_connected()
    
    pname = project_name.strip().upper()
    logger.debug(f"Ending project: {pname}")
    
    try:
        project = Project.get(Project.name == pname)
        
        # Complete all tasks
        now = datetime.now(pytz.utc)
        task_count = Task.update(status='complete', completed_at=now).where(
            Task.project == project
        ).execute()
        
        # Delete project
        project.delete_instance()
        
        # Clear active_project if it was this project
        if state.get('active_project') == pname:
            state['active_project'] = None
            save_state(state)
        
        logger.info(f"Project ended: {pname} ({task_count} tasks completed)")
        return True
    except Project.DoesNotExist:
        logger.warning(f"Attempted to end non-existent project: {pname}")
        return False


def delete_project(state: State, project_name: str) -> bool:
    """Permanently delete a project and all its tasks."""
    _ensure_db_connected()
    
    pname = project_name.strip().upper()
    logger.warning(f"Deleting project: {pname}")
    
    try:
        project = Project.get(Project.name == pname)
        
        # Delete all tasks
        task_count = Task.delete().where(Task.project == project).execute()
        
        # Delete project
        project.delete_instance()
        
        # Clear active_project if it was this project
        if state.get('active_project') == pname:
            state['active_project'] = None
            save_state(state)
        
        logger.info(f"Project deleted: {pname} ({task_count} tasks deleted)")
        return True
    except Project.DoesNotExist:
        logger.warning(f"Attempted to delete non-existent project: {pname}")
        return False


def get_task(state: State, task_id: str) -> Optional[TaskType]:
    """Retrieve task object by ID."""
    _ensure_db_connected()
    
    try:
        task = Task.get(Task.task_id == task_id)
        result = {
            'id': task.task_id,
            'description': task.description,
            'project_name': task.project.name if task.project else None,
            'status': task.status,
            'value_flag': task.is_value,
            'deadline_mmddyyyy': task.deadline.strftime('%m%d%Y') if task.deadline else None,
        }
        if task.completed_at:
            result['completed_at'] = task.completed_at.isoformat()
        return result
    except Task.DoesNotExist:
        return None


def delete_task(state: State, task_id: str) -> bool:
    """Permanently delete a single task."""
    _ensure_db_connected()
    
    try:
        task = Task.get(Task.task_id == task_id)
        task.delete_instance()
        return True
    except Task.DoesNotExist:
        return False


def move_task(state: State, task_id: str, target_project_name: str) -> Tuple[bool, str]:
    """Move a task from its current project to a different project.
    
    Args:
        state: State dictionary
        task_id: 4-digit task ID to move
        target_project_name: Name of the target project to move to
        
    Returns:
        tuple: (success: bool, message: str)
    """
    _ensure_db_connected()
    
    target_pname = target_project_name.strip().upper()
    
    try:
        # Get the task
        task = Task.get(Task.task_id == task_id)
        old_project_name = task.project.name if task.project else "(no project)"
        
        # Get or create the target project
        try:
            target_project = Project.get(Project.name == target_pname)
        except Project.DoesNotExist:
            # Create the project if it doesn't exist
            add_project(state, target_pname)
            target_project = Project.get(Project.name == target_pname)
        
        # Move the task
        task.project = target_project
        task.save()
        
        logger.info(f"Moved task {task_id} from '{old_project_name}' to '{target_pname}'")
        return True, f"Moved task [{task_id}] from '{old_project_name}' to '{target_pname}'"
        
    except Task.DoesNotExist:
        logger.warning(f"Attempted to move non-existent task: {task_id}")
        return False, f"Task {task_id} not found"


def hide_project(state: State, project_name: str, until: Optional[str] = None) -> bool:
    """Hide a project from standard project listings."""
    _ensure_db_connected()
    
    pname = project_name.strip().upper()
    
    try:
        project = Project.get(Project.name == pname)
        project.is_hidden = True
        
        # Parse until date if provided (mmddyyyy format)
        if until:
            try:
                mm = int(until[0:2])
                dd = int(until[2:4])
                yyyy = int(until[4:8])
                project.unhide_date = date(yyyy, mm, dd)
            except Exception:
                project.unhide_date = None
        else:
            project.unhide_date = None
        
        project.save()
        
        # Update state's projects_meta to reflect the change
        state.setdefault('projects_meta', {})[pname] = {
            'hidden': True,
            'unhide_date': project.unhide_date.strftime('%m%d%Y') if project.unhide_date else None
        }
        
        return True
    except Project.DoesNotExist:
        return False


def unhide_project(state: State, project_name: str) -> bool:
    """Make a previously hidden project visible."""
    _ensure_db_connected()
    
    pname = project_name.strip().upper()
    
    try:
        project = Project.get(Project.name == pname)
        project.is_hidden = False
        project.unhide_date = None
        project.save()
        
        # Update state's projects_meta to reflect the change
        state.setdefault('projects_meta', {})[pname] = {
            'hidden': False,
            'unhide_date': None
        }
        
        return True
    except Project.DoesNotExist:
        return False


def list_hide(state: State) -> List[Tuple[Optional[str], str, Optional[str]]]:
    """List all currently hidden projects."""
    _ensure_db_connected()
    
    out = []
    for project in Project.select().where(Project.is_hidden == True):
        unhide_date_str = project.unhide_date.strftime('%m%d%Y') if project.unhide_date else None
        out.append((project.number, project.name, unhide_date_str))
    
    return out


def list_open_projects_and_tasks(state: State) -> Dict[str, List[TaskType]]:
    """Build mapping of projects to their open tasks.
    
    Returns all projects (even those without tasks) plus projectless tasks under 'UNASSIGNED'.
    """
    _ensure_db_connected()
    
    out = {}
    
    # Get all projects (including those without tasks)
    for project in Project.select():
        open_tasks = []
        for task in project.tasks.where(Task.status == 'open'):
            task_dict = {
                'id': task.task_id,
                'description': task.description,
                'project_name': project.name,
                'status': task.status,
                'value_flag': task.is_value,
                'deadline_mmddyyyy': task.deadline.strftime('%m%d%Y') if task.deadline else None,
            }
            if task.completed_at:
                task_dict['completed_at'] = task.completed_at.isoformat()
            open_tasks.append(task_dict)
        
        # Include all projects, even if they have no tasks
        out[project.name] = open_tasks
    
    # Get projectless tasks (tasks with no project)
    projectless_tasks = []
    for task in Task.select().where(Task.project.is_null(), Task.status == 'open'):
        task_dict = {
            'id': task.task_id,
            'description': task.description,
            'project_name': None,
            'status': task.status,
            'value_flag': task.is_value,
            'deadline_mmddyyyy': task.deadline.strftime('%m%d%Y') if task.deadline else None,
        }
        if task.completed_at:
            task_dict['completed_at'] = task.completed_at.isoformat()
        projectless_tasks.append(task_dict)
    
    # Add projectless tasks under special "UNASSIGNED" key if any exist
    if projectless_tasks:
        out['UNASSIGNED'] = projectless_tasks
    
    return out
