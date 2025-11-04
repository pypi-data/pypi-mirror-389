# Simple Time Tracker (V3)

Overview
--------
Simple Time Tracker is a compact, command-line Time + Task management tool. Version 3 introduces project numbering, priority grouping, deadline-aware task highlighting, a high-value flag for urgent tasks, session-based time tracking (for accurate daily summaries), and administrative commands for managing projects and tasks.

Setup
-----
1. (Optional) Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install runtime dependencies:

# taskswitch

> zero friction pure progress

A powerful command-line time tracker with SQLite backend, intelligent task management, and zero-friction workflows.

## Overview

**taskswitch** is a modern CLI time tracker that combines simplicity with power. Built on SQLite with a clean peewee ORM layer, it offers sub-millisecond performance while tracking your work across projects and tasks with minimal keystrokes.

## Key Features

### Core Capabilities
- **Database-backed**: SQLite + peewee ORM for reliability and performance
- **Session-based timing**: Accurate time tracking with UTC timestamps
- **Project management**: 3-digit project numbers (001-999) with auto-padding
- **Task tracking**: 4-digit task IDs with full lifecycle management
- **Priority queue**: Track up to 3 high-priority projects
- **Daily summaries**: CET/CEST-aware Markdown logs in `logs/`

### Zero-Friction Workflows
- **Quick switching**: Type `5` to switch to project 005
- **Projectless tasks**: Start tracking by typing any text - gets auto-assigned task ID
- **Bulk operations**: `DELETE 1 2 3` to delete multiple projects at once
- **Smart display**: Hidden projects, priority views, single-project isolation
- **Task mobility**: Move tasks between projects with `MOVE #### ###`

### Smart Task Intelligence

**Deadline Awareness**
- Set deadlines: `0123 12252025` (task ID + mmddyyyy)
- Auto-detect deadlines in task descriptions
- Color-coded urgency:
  - 🔴 **RED**: Due in <4 days (critical)
  - 🟡 **YELLOW**: Due in 4-7 days (urgent)
  - 🔵 **CYAN**: Due in 8+ days (planned)

**High-Value Flagging**
- Mark important tasks: `0123 !!!`
- High-value tasks display in yellow (when no deadline overrides)
- Precedence: RED > YELLOW (deadline) > Yellow (value flag) > CYAN

## Installation

```bash
pip install taskswitch
```

Or from source:
```bash
git clone https://github.com/DP26112/simple-time-tracker.git
cd simple-time-tracker
pip install -r requirements.txt
python -m taskswitch
```

## Quick Start

```bash
# Launch the tracker
python -m taskswitch

# Create a project
ADD PROJECT MyProject

# Add a task with project number
ADD 001 TASK Fix the authentication bug

# Start working on task
0001

# Take a break
BREAK

# View all projects
LIST PROJECTS

# Get help
LIST COMMANDS
```

## Command Reference

Type `LIST COMMANDS` in the app for the full interactive reference. Here are the essentials:

### Project Management
```bash
ADD PROJECT <Name>              # Create new project
ADD ### TASK <Description>      # Add task by project number
END ### [### ...]               # End one or more projects
DELETE ### [### ...]            # Delete one or more projects
HIDE <Name> [UNTIL mmddyyyy]    # Hide project (optionally until date)
UNHIDE <Name>                   # Unhide project
```

### Priority Management
```bash
ADD PRIORITY ### [### ...]      # Add projects to priority (max 3)
END PRIORITY ###                # Remove from priority list
LIST PRIORITY (or LIST PRI)     # View priority projects
```

### Task Management
```bash
####                            # Start/resume task by ID
<text>                          # Start projectless task (auto-assigns ID)
TASK <Description>              # Add task to last active project
MOVE #### ###                   # Move task to different project
END #### [#### ...]             # End one or more tasks
DELETE #### [#### ...]          # Delete one or more tasks
#### !!!                        # Flag task as high-value
#### mmddyyyy                   # Set task deadline
```

### Viewing
```bash
LIST PROJECTS (or LIST PROJ)    # View all projects and tasks
LIST PROJ ###                   # View single project
###                             # Quick switch to project view
LIST HIDE                       # View hidden projects
LIST COMMANDS                   # Show full command reference
```

### Special
```bash
BREAK                           # Take a break
REST                            # Extended break
CLS or CLEAR                    # Clear screen
QUIT                            # Exit tracker
```


## Architecture

### Database Schema
- **Projects**: name (unique), number (001-999), priority/hidden flags, unhide_date
- **Tasks**: task_id (primary key), description, project (nullable FK), status, deadline, is_value
- **TimeEntry**: Historical time logs with duration and timestamps
- **Config**: Key-value store for app state (active_task, start_time, priority list)

### Performance
- SQLite with peewee ORM
- Indexed lookups on project names and task IDs
- Sub-millisecond response for typical operations
- Handles 1000+ projects/tasks without lag

## Configuration

Edit `config.yaml` to customize:
- Database path
- Log directory
- Timezone (for daily summaries)
- Auto-summary timing

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Project Structure
```
taskswitch/
├── __init__.py          # Package entry, version
├── __main__.py          # CLI entry point
├── commands.py          # Command handlers
├── db_state_manager.py  # Database operations
├── models.py            # Peewee ORM models
├── shell.py             # Interactive shell (cmd.Cmd)
├── display.py           # Output formatting
├── timer.py             # Time tracking logic
└── reporting.py         # Daily summaries
```

## Migration from V3

If you have existing JSON-based data from V3, contact the maintainer for migration assistance. V4 uses SQLite exclusively.

## Contributing

Pull requests welcome! Please:
1. Add tests for new features
2. Update documentation
3. Follow existing code style
4. Keep performance in mind

## License

MIT License - See LICENSE file for details

## Links

- **GitHub**: https://github.com/DP26112/simple-time-tracker
- **Issues**: https://github.com/DP26112/simple-time-tracker/issues
- **PyPI**: (coming soon)

