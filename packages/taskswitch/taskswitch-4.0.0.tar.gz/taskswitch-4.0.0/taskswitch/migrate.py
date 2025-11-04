"""
Data migration script to populate the database from current_state.json
"""
import json
from datetime import datetime, date
from .models import db, Project, Task


def parse_date_mmddyyyy(date_str):
    """
    Parse a date string in mmddyyyy format to a date object.
    
    Args:
        date_str: String in format mmddyyyy (e.g., "10312025")
        
    Returns:
        date object or None if invalid/empty
    """
    if not date_str or date_str == "None":
        return None
    
    try:
        # Parse mmddyyyy format
        month = int(date_str[0:2])
        day = int(date_str[2:4])
        year = int(date_str[4:8])
        return date(year, month, day)
    except (ValueError, IndexError):
        return None


def parse_datetime_iso(datetime_str):
    """
    Parse an ISO format datetime string to a datetime object.
    
    Args:
        datetime_str: ISO format datetime string
        
    Returns:
        datetime object or None if invalid/empty
    """
    if not datetime_str:
        return None
    
    try:
        # Parse ISO format (handles timezone info)
        return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None


def migrate_core_data(json_file_path):
    """
    Migrate projects and tasks from current_state.json to the database.
    
    This function:
    1. Loads the JSON data
    2. Creates Project records with metadata from project_numbers, projects_meta, and priority_projects
    3. Creates Task records with proper date parsing and project linking
    
    Args:
        json_file_path: Path to the current_state.json file
    """
    # Load JSON data
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    # Extract data sections
    project_numbers = data.get('project_numbers', {})
    projects_meta = data.get('projects_meta', {})
    priority_projects = data.get('priority_projects', [])
    tasks = data.get('tasks', {})
    
    # Connect to database if not already connected
    was_closed = db.is_closed()
    if was_closed:
        db.connect()
    
    try:
        with db.atomic():
            # Migrate Projects
            print("Migrating projects...")
            project_map = {}  # Maps project_name -> Project instance
            
            for project_name, project_number in project_numbers.items():
                # Get metadata for this project
                meta = projects_meta.get(project_name, {})
                is_hidden = meta.get('hidden', False)
                unhide_date_str = meta.get('unhide_date')
                unhide_date = parse_date_mmddyyyy(unhide_date_str)
                
                # Check if project is in priority list
                is_priority = project_name in priority_projects
                
                # Create Project instance
                project = Project.create(
                    name=project_name,
                    number=project_number,
                    is_priority=is_priority,
                    is_hidden=is_hidden,
                    unhide_date=unhide_date
                )
                project_map[project_name] = project
                print(f"  Created project: {project_name} ({project_number})")
            
            # Migrate Tasks
            print("\nMigrating tasks...")
            for task_id, task_data in tasks.items():
                # Get task fields
                description = task_data.get('description', '')
                project_name = task_data.get('project_name')
                status = task_data.get('status', 'open')
                completed_at_str = task_data.get('completed_at')
                value_flag = task_data.get('value_flag', False)
                deadline_str = task_data.get('deadline_mmddyyyy')
                
                # Parse dates
                completed_at = parse_datetime_iso(completed_at_str)
                deadline = parse_date_mmddyyyy(deadline_str)
                
                # Find related project (may be None)
                project = None
                if project_name:
                    project = project_map.get(project_name)
                    if not project:
                        print(f"  Warning: Project '{project_name}' not found for task {task_id}")
                
                # Create Task instance
                task = Task.create(
                    task_id=task_id,
                    description=description,
                    project=project,
                    status=status,
                    completed_at=completed_at,
                    is_value=value_flag,
                    deadline=deadline
                )
                print(f"  Created task: {task_id} - {description[:50]}...")
            
            print("\nMigration completed successfully!")
            
    finally:
        # Close database connection only if we opened it
        if was_closed and not db.is_closed():
            db.close()


def migrate_aux_data(json_file_path):
    """
    Migrate auxiliary data (TimeEntry and Config) from current_state.json to the database.
    
    This function:
    1. Loads the JSON data
    2. Creates TimeEntry records from task_times list
    3. Creates Config records for singleton state values
    
    Args:
        json_file_path: Path to the current_state.json file
    """
    # Load JSON data
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    # Import TimeEntry and Config models
    from .models import TimeEntry, Config
    
    # Connect to database if not already connected
    was_closed = db.is_closed()
    if was_closed:
        db.connect()
    
    try:
        with db.atomic():
            # Migrate TimeEntry records
            print("Migrating time entries...")
            task_times = data.get('task_times', [])
            
            for entry in task_times:
                task_name = entry.get('task_name', '')
                duration_seconds = entry.get('duration_seconds', 0.0)
                end_timestamp_str = entry.get('end_timestamp')
                
                # Parse the end_timestamp
                end_timestamp = parse_datetime_iso(end_timestamp_str)
                
                if end_timestamp:
                    TimeEntry.create(
                        task_name=task_name,
                        duration_seconds=duration_seconds,
                        end_timestamp=end_timestamp
                    )
            
            print(f"  Created {len(task_times)} time entries")
            
            # Migrate Config records
            print("\nMigrating config values...")
            
            # Simple key-value pairs
            config_keys = [
                'active_task',
                'start_time',
                'active_project',
                'project_counter',
                'last_summary_date',
                'global_task_counter',
                'last_list_view'
            ]
            
            for key in config_keys:
                value = data.get(key, '')
                if value is not None:
                    Config.create(key=key, value=str(value))
                    print(f"  Created config: {key} = {value}")
            
            # Serialize priority_projects as JSON
            priority_projects = data.get('priority_projects', [])
            Config.create(
                key='priority_projects',
                value=json.dumps(priority_projects)
            )
            print(f"  Created config: priority_projects = {priority_projects}")
            
            print("\nAuxiliary data migration completed successfully!")
            
    finally:
        # Close database connection only if we opened it
        if was_closed and not db.is_closed():
            db.close()


if __name__ == '__main__':
    # Run migration
    import os
    from .models import initialize_database
    
    # Construct path to current_state.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, '..', 'data', 'current_state.json')
    
    print("=" * 60)
    print("Initializing Database")
    print("=" * 60)
    initialize_database()
    print("Database tables created successfully!")
    
    print("\n" + "=" * 60)
    print("Running Core Data Migration")
    print("=" * 60)
    migrate_core_data(json_path)
    
    print("\n" + "=" * 60)
    print("Running Auxiliary Data Migration")
    print("=" * 60)
    migrate_aux_data(json_path)
