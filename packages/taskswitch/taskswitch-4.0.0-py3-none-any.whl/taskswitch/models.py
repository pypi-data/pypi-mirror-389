"""
Database models for the task manager using peewee ORM.
"""
from peewee import (
    SqliteDatabase,
    Model,
    TextField,
    CharField,
    BooleanField,
    DateField,
    DateTimeField,
    ForeignKeyField,
    FloatField,
)

from .logging_config import get_database_logger

# Get logger for database operations
logger = get_database_logger()

# Get database path from configuration
try:
    from .config_manager import get_cached_config
    _config = get_cached_config()
    _db_path = _config['database']['path']
except Exception:
    # Fallback to default if config loading fails
    _db_path = 'task_manager.db'

# Database connection
db = SqliteDatabase(_db_path)


class BaseModel(Model):
    """Base model class that specifies the database."""
    class Meta:
        database = db


class Project(BaseModel):
    """
    Project model representing a project in the system.
    
    Attributes:
        name: Unique project name (main identifier)
        number: Project number (e.g., "001")
        is_priority: Whether the project is marked as priority
        is_hidden: Whether the project is hidden
        unhide_date: Date when a hidden project should be unhidden
    """
    name = TextField(unique=True, index=True)
    number = CharField()
    is_priority = BooleanField(default=False)
    is_hidden = BooleanField(default=False)
    unhide_date = DateField(null=True)

    class Meta:
        database = db

    def __str__(self):
        return f"Project({self.name}, {self.number})"


class Task(BaseModel):
    """
    Task model representing a task in the system.
    
    Attributes:
        task_id: String-based task ID (e.g., "0001") - primary key
        description: Task description
        project: Foreign key to Project (nullable for tasks without project)
        status: Current status of the task (default: "open")
        completed_at: Timestamp when task was completed
        is_value: Boolean flag for value tasks (value_flag)
        deadline: Optional deadline date for the task
    """
    task_id = CharField(primary_key=True)
    description = TextField()
    project = ForeignKeyField(Project, null=True, backref='tasks')
    status = CharField(default='open')
    completed_at = DateTimeField(null=True)
    is_value = BooleanField(default=False)
    deadline = DateField(null=True)

    class Meta:
        database = db

    def __str__(self):
        return f"Task({self.task_id}, {self.description[:30]}...)"


class TimeEntry(BaseModel):
    """
    TimeEntry model for historical task time logs.
    
    Represents entries from the task_times list, tracking how long
    tasks were worked on and when they ended.
    
    Attributes:
        task_name: Name of the task that was worked on
        duration_seconds: Duration of the time entry in seconds
        end_timestamp: Timestamp when this time entry ended
    """
    task_name = TextField()
    duration_seconds = FloatField()
    end_timestamp = DateTimeField()

    class Meta:
        database = db

    def __str__(self):
        return f"TimeEntry({self.task_name}, {self.duration_seconds}s, {self.end_timestamp})"


class Config(BaseModel):
    """
    Config model for key-value storage of application state.
    
    Used to store singleton state values like current_task, daily_goal,
    and other application configuration. Values can be stored as strings
    or JSON-serialized data.
    
    Attributes:
        key: Configuration key (primary key)
        value: Configuration value (string or JSON-serialized)
    """
    key = CharField(primary_key=True)
    value = TextField()

    class Meta:
        database = db

    def __str__(self):
        return f"Config({self.key}={self.value})"


def initialize_database():
    """
    Initialize the database by connecting, dropping existing tables, and creating new tables.
    
    This function:
    1. Connects to the database
    2. Drops existing tables in the correct order (respecting foreign key constraints)
    3. Creates tables in the correct order
    4. Closes the database connection
    
    Tables are dropped in this order: Task, Project, TimeEntry, Config
    (Task must be dropped before Project due to foreign key constraint)
    """
    logger.info("Initializing database: dropping and recreating tables")
    db.connect()
    
    # Drop tables in reverse order of dependencies (Task references Project)
    logger.debug("Dropping existing tables")
    db.drop_tables([Task, Project, TimeEntry, Config], safe=True)
    
    # Create tables in proper order (Project before Task due to foreign key)
    logger.debug("Creating tables")
    db.create_tables([Project, Task, TimeEntry, Config])
    
    logger.info("Database initialized successfully")
    db.close()
    

def close_database():
    """Close the database connection."""
    if not db.is_closed():
        logger.debug("Closing database connection")
        db.close()
        logger.info("Database connection closed")
