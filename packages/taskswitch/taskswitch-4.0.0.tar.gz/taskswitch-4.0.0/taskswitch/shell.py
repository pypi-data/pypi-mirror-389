#!/usr/bin/env python3
"""Interactive shell interface using cmd.Cmd for the time tracker application.

This module provides TaskSwitchShell, a cmd.Cmd-based interactive command-line
interface that preserves the original ambiguous input style while providing
a robust command processing framework.
"""
import cmd

from colorama import init as colorama_init

from .commands import (
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
    handle_project_as_task,
    handle_set_task_deadline,
    handle_start_task,
    handle_start_text_task,
    handle_task_shorthand,
    handle_toggle_task_value,
    handle_unhide_project,
)
from .display import _format_task_display
from .reporting import check_and_summarize_if_needed
from .db_state_manager import load_state  # Using database backend
from .types import State

# Initialize colorama for cross-platform colored output
colorama_init(autoreset=True)


class TaskSwitchShell(cmd.Cmd):
    """Interactive shell for time tracking using cmd.Cmd framework.

    This shell provides both explicit commands (via do_* methods) and ambiguous
    input handling (via default() method) to maintain the flexible input style
    of the original tracker while leveraging cmd.Cmd's robust parsing.

    Attributes:
        intro (str): Welcome message displayed at shell startup.
        prompt (str): Dynamic prompt showing current task status.
        state (State): Application state dictionary.
    """

    intro = """taskswitch - zero friction pure progress

Type 'LIST COMMANDS' for full command reference | Type 'QUIT' to exit
"""

    help_text = """
═══════════════════════════════════════════════════════════════════════════════
                         TASKSWITCH COMMAND REFERENCE
═══════════════════════════════════════════════════════════════════════════════

PROJECT MANAGEMENT:
  ADD PROJECT <Name>              Create new project
  ADD ### TASK <Description>      Add task using project number (e.g., ADD 053 TASK ...)
  ADD <Name> TASK <Description>   Add task using project name
  END ### [### ...]               End one or more projects by number
  END PROJECT <Name>              End project by name
  DELETE ### [### ...]            Delete one or more projects by number
  DELETE PROJECT <Name>           Delete project by name
  HIDE <Name> [UNTIL mmddyyyy]    Hide project (optionally until date)
  UNHIDE <Name>                   Unhide project
  LIST HIDE                       View all hidden projects

PRIORITY MANAGEMENT:
  ADD PRIORITY ### [### ...]      Add projects to priority (chainable, max 3)
  ADD PRIORITY <Name> [<Name>]    Add projects by name
  END PRIORITY ###                Remove project from priority list
  LIST PRIORITY (or LIST PRI)     View priority projects

TASK MANAGEMENT:
  ####                            Start/resume task by 4-digit ID
  <Text>                          Start projectless task (auto-assigns task ID)
  TASK <Description>              Add task to last active project
  MOVE #### ###                   Move task to different project (by number)
  MOVE #### <ProjectName>         Move task to different project (by name)
  END #### [#### ...]             End one or more tasks by ID
  DELETE #### [#### ...]          Delete one or more tasks by ID
  #### !!!                        Flag task as high-value
  #### mmddyyyy                   Set task deadline

VIEWING:
  LIST PROJECTS (or LIST PROJ)    View all projects and tasks
  LIST PROJ ###                   View single project by number
  LIST PROJ <ProjectName>         View single project by name
  ###                             Quick switch to project view (1-3 digits)

BREAKS & SPECIAL:
  BREAK                           Take a break
  REST                            Take extended break
  CLS or CLEAR                    Clear screen
  QUIT                            Exit tracker

NOTES:
  - Project numbers: 1-3 digits auto-pad to 3 (e.g., 5 → 005)
  - Projectless tasks appear under "UNASSIGNED TASKS" in LIST PROJECTS
  - Task IDs are always 4 digits (e.g., 0001, 0299)
  - High-value tasks (marked with !!!) show in red brackets
  - Tasks with deadlines show color-coded based on urgency
  
═══════════════════════════════════════════════════════════════════════════════
"""

    def __init__(self):
        """Initialize the shell, load state, and check for pending summaries."""
        super().__init__()
        self.state = load_state()
        check_and_summarize_if_needed(self.state)
        self.prompt = self._get_prompt()

    def _get_prompt(self) -> str:
        """Generate dynamic prompt showing current task status.

        Returns:
            str: Formatted prompt string with current task info.
        """
        status = _format_task_display(self.state)
        return f"{status} - Enter next task/command: "

    def postcmd(self, stop: bool, line: str) -> bool:
        """Update prompt after each command execution.

        Args:
            stop: Whether to stop the command loop.
            line: The command line that was executed.

        Returns:
            bool: Whether to stop the command loop.
        """
        self.prompt = self._get_prompt()
        return stop
    
    def _resolve_project_identifier(self, identifier: str) -> str:
        """Resolve project number or name to project name.
        
        Args:
            identifier: Either a 1-3 digit project number or project name
            
        Returns:
            Project name (normalized to uppercase)
        """
        # If it's a number (1-3 digits), pad and look up the project name
        if identifier.isdigit() and 1 <= len(identifier) <= 3:
            # Pad to 3 digits
            project_number = f"{int(identifier):03d}"
            project_numbers = self.state.get('project_numbers', {})
            # Reverse lookup: number -> name
            for name, num in project_numbers.items():
                if num == project_number:
                    return name.upper()
            # Number not found, return as-is (will fail downstream)
            return identifier.upper()
        # Otherwise, treat as project name
        return identifier.upper()

    def emptyline(self) -> bool:
        """Handle empty input (just pressing Enter).

        Returns:
            bool: False to continue the command loop.
        """
        return False

    # ========== Explicit Command Methods (do_*) ==========

    def do_ADD(self, line: str) -> None:
        """Handle ADD commands: ADD PROJECT, ADD PRIORITY, ADD [Project] TASK.

        Args:
            line: Everything after 'ADD' keyword.
        """
        tokens = line.split()
        if not tokens:
            print(
                "Unrecognized ADD command. Use 'ADD PROJECT <Name>' or 'ADD <ProjectName> TASK <Description>'."
            )
            return

        cmd = tokens[0].upper()

        if cmd == "PROJECT":
            pname = " ".join(tokens[1:])
            success, msg = handle_add_project(self.state, pname)
            print(msg)
        elif cmd == "PRIORITY":
            # Support multiple projects: ADD PRIORITY 001 002 PROJ_C
            project_identifiers = tokens[1:]
            if not project_identifiers:
                print("Usage: ADD PRIORITY <ProjectName|###> [<ProjectName|###> ...]")
                return
            success, msg = handle_add_priority(self.state, project_identifiers)
            print(msg)
        elif "TASK" in [t.upper() for t in tokens]:
            idx = next(i for i, t in enumerate(tokens) if t.upper() == "TASK")
            identifier = " ".join(tokens[:idx])
            desc = " ".join(tokens[idx + 1 :])
            # Support both project name and project number
            pname = self._resolve_project_identifier(identifier)
            success, msg = handle_add_task(self.state, pname, desc)
            print(msg)
        else:
            print(
                "Unrecognized ADD command. Use 'ADD PROJECT <Name>' or 'ADD <ProjectName> TASK <Description>'."
            )

    def do_END(self, line: str) -> None:
        """Handle END commands: END ###, END PROJECT, END PRIORITY ###, END ####.

        Args:
            line: Everything after 'END' keyword.
        """
        tokens = line.split()
        if not tokens:
            print(
                "Unrecognized END command. Use 'END PROJECT <Name>', 'END PRIORITY <###>', or 'END <####> [<####> ...]'."
            )
            return

        # END ### ### ### - Multiple project numbers (1-3 digits each)
        if all(t.isdigit() and 1 <= len(t) <= 3 for t in tokens):
            ended_count = 0
            for proj_num in tokens:
                # Pad to 3 digits
                project_number = f"{int(proj_num):03d}"
                success, msg = handle_end_project_by_number(self.state, project_number)
                print(msg)
                if success:
                    ended_count += 1
        # END ### - Quick single project end by number (1-3 digits)
        elif len(tokens) == 1 and tokens[0].isdigit() and 1 <= len(tokens[0]) <= 3:
            # Pad to 3 digits
            project_number = f"{int(tokens[0]):03d}"
            success, msg = handle_end_project_by_number(self.state, project_number)
            print(msg)
        elif tokens[0].upper() == "PRIORITY":
            # END PRIORITY ### or END PRIORITY ProjectName
            if len(tokens) < 2:
                print("Usage: END PRIORITY <ProjectName|###>")
                return
            project_identifier = tokens[1]
            success, msg = handle_end_priority(self.state, project_identifier)
            print(msg)
        elif tokens[0].upper() == "PROJECT":
            # END PROJECT can accept multiple project numbers: END PROJECT 048 049 051
            rest_tokens = tokens[1:]
            if all(t.isdigit() and 1 <= len(t) <= 3 for t in rest_tokens):
                # Multiple project numbers
                ended_count = 0
                for proj_num in rest_tokens:
                    project_number = f"{int(proj_num):03d}"
                    success, msg = handle_end_project_by_number(self.state, project_number)
                    print(msg)
                    if success:
                        ended_count += 1
            else:
                # Single project name
                pname = " ".join(rest_tokens)
                success, msg = handle_end_project(self.state, pname)
                print(msg)
        else:
            # END [####] [####] ... - End tasks by IDs
            ids = [t for t in tokens if t.isdigit() and len(t) == 4]
            if ids:
                success, msg = handle_end_tasks(self.state, ids)
                print(msg)
            else:
                print(
                    "Unrecognized END command. Use 'END PROJECT <Name>', 'END PRIORITY <###>', or 'END <####> [<####> ...]'."
                )

    def do_DELETE(self, line: str) -> None:
        """Handle DELETE commands: DELETE ###, DELETE PROJECT, DELETE #### [#### ...].

        Args:
            line: Everything after 'DELETE' keyword.
        """
        tokens = line.split()
        if not tokens:
            print(
                "Unrecognized DELETE command. Use 'DELETE PROJECT <Name>' or 'DELETE <####> [<####> ...]'."
            )
            return

        # DELETE ### ### ### - Multiple project numbers (1-3 digits each)
        if all(t.isdigit() and 1 <= len(t) <= 3 for t in tokens):
            deleted_count = 0
            for proj_num in tokens:
                # Pad to 3 digits
                project_number = f"{int(proj_num):03d}"
                success, msg = handle_delete_project_by_number(self.state, project_number)
                print(msg)
                if success:
                    deleted_count += 1
            if deleted_count > 0:
                handle_list_projects(self.state)
        # DELETE ### - Quick single project delete by number (1-3 digits)
        elif len(tokens) == 1 and tokens[0].isdigit() and 1 <= len(tokens[0]) <= 3:
            # Pad to 3 digits
            project_number = f"{int(tokens[0]):03d}"
            success, msg = handle_delete_project_by_number(self.state, project_number)
            print(msg)
            if success:
                handle_list_projects(self.state)
        elif tokens[0].upper() == "PROJECT":
            # DELETE PROJECT can accept multiple project numbers: DELETE PROJECT 048 049 051
            rest_tokens = tokens[1:]
            if all(t.isdigit() and 1 <= len(t) <= 3 for t in rest_tokens):
                # Multiple project numbers
                deleted_count = 0
                for proj_num in rest_tokens:
                    project_number = f"{int(proj_num):03d}"
                    success, msg = handle_delete_project_by_number(self.state, project_number)
                    print(msg)
                    if success:
                        deleted_count += 1
                if deleted_count > 0:
                    handle_list_projects(self.state)
            else:
                # Single project name
                pname = " ".join(rest_tokens)
                success, msg = handle_delete_project(self.state, pname)
                print(msg)
                if success:
                    handle_list_projects(self.state)
        # Support multiple task IDs: DELETE #### #### ####
        elif all(t.isdigit() and len(t) == 4 for t in tokens):
            deleted_count = 0
            for task_id in tokens:
                success, msg = handle_delete_task(self.state, task_id)
                print(msg)
                if success:
                    deleted_count += 1
            if deleted_count > 0:
                # Refresh the display after deletions
                # Determine which project to show based on the last deleted task
                handle_list_projects(self.state)
        else:
            print(
                "Unrecognized DELETE command. Use 'DELETE PROJECT <Name>' or 'DELETE <####> [<####> ...]'."
            )

    def do_LIST(self, line: str) -> None:
        """Handle LIST commands: LIST PROJECTS, LIST PRIORITY, LIST HIDE, LIST TASKS, LIST COMMANDS.

        Args:
            line: Everything after 'LIST' keyword.
        """
        tokens = line.split()
        if not tokens:
            print("Use 'LIST PROJECTS' (or PROJ), 'LIST PRIORITY' (or PRI), 'LIST HIDE', 'LIST TASKS', or 'LIST COMMANDS'.")
            return

        cmd = tokens[0].upper()

        if cmd == "COMMANDS":
            print(self.help_text)
            return
        elif cmd == "HIDE":
            success, msg = handle_list_hide(self.state)
        elif cmd == "PROJECTS" or cmd == "PROJ":
            # Check if a specific project identifier was provided
            if len(tokens) > 1:
                # LIST PROJECTS ### or LIST PROJECTS ProjectName
                # If single token and it's a number, treat as project number
                # Otherwise join all remaining tokens as project name
                if len(tokens) == 2 and tokens[1].isdigit() and 1 <= len(tokens[1]) <= 3:
                    project_identifier = tokens[1]
                else:
                    project_identifier = " ".join(tokens[1:])
                success, msg = handle_list_single_project(self.state, project_identifier)
                if not success:
                    print(msg)
            else:
                # No identifier - list all projects
                success, msg = handle_list_projects(self.state)
        elif cmd == "PRIORITY" or cmd == "PRI":
            success, msg = handle_list_priority(self.state)
        elif cmd == "TASKS":
            pname = " ".join(tokens[1:]) if len(tokens) > 1 else None
            success, msg = handle_list_tasks(self.state, pname)
        else:
            print("Use 'LIST PROJECTS' (or PROJ), 'LIST PRIORITY' (or PRI), 'LIST HIDE', 'LIST TASKS', or 'LIST COMMANDS'.")

    def do_HIDE(self, line: str) -> None:
        """Handle HIDE command: HIDE <ProjectName|###> [UNTIL mmddyyyy].

        Args:
            line: Everything after 'HIDE' keyword.
        """
        tokens = line.split()
        if not tokens:
            print("Usage: HIDE <ProjectName|###> [UNTIL mmddyyyy]")
            return

        # Parse HIDE UNTIL syntax
        until = None
        until_idx = None
        if "UNTIL" in [t.upper() for t in tokens]:
            try:
                until_idx = next(i for i, t in enumerate(tokens) if t.upper() == "UNTIL")
                if until_idx + 1 < len(tokens):
                    until = tokens[until_idx + 1]
            except Exception:
                print("Invalid HIDE UNTIL syntax")
                return
        
        # Get project identifier - everything before UNTIL or all tokens if no UNTIL
        if until_idx is not None:
            proj_tokens = tokens[:until_idx]
        else:
            proj_tokens = tokens
        
        # If single token is a number, it's a project number; otherwise join as project name
        if len(proj_tokens) == 1 and proj_tokens[0].isdigit() and 1 <= len(proj_tokens[0]) <= 3:
            proj_identifier = proj_tokens[0]
        else:
            proj_identifier = " ".join(proj_tokens)

        success, msg = handle_hide_project(self.state, proj_identifier, until)
        print(msg)

    def do_UNHIDE(self, line: str) -> None:
        """Handle UNHIDE command: UNHIDE <ProjectName|###>.

        Args:
            line: Everything after 'UNHIDE' keyword.
        """
        tokens = line.split()
        if not tokens:
            print("Usage: UNHIDE <ProjectName|###>")
            return

        # If single token is a number, it's a project number; otherwise join as project name
        if len(tokens) == 1 and tokens[0].isdigit() and 1 <= len(tokens[0]) <= 3:
            proj_identifier = tokens[0]
        else:
            proj_identifier = " ".join(tokens)
        
        success, msg = handle_unhide_project(self.state, proj_identifier)
        print(msg)

    def do_MOVE(self, line: str) -> None:
        """Move a task to a different project.

        Syntax:
            MOVE #### ### (task ID to project number)
            MOVE #### ProjectName (task ID to project name)

        Args:
            line: Task ID and target project identifier (number or name).
        """
        from .commands import handle_move_task

        tokens = line.strip().split(maxsplit=1)
        if len(tokens) < 2:
            print("Usage: MOVE #### ### or MOVE #### ProjectName")
            return

        task_id, project_identifier = tokens
        if not task_id.isdigit() or len(task_id) != 4:
            print("Invalid task ID. Must be 4 digits (e.g., 0001)")
            return

        handle_move_task(self.state, task_id, project_identifier)
        self.prompt = self._get_prompt()

    def do_QUIT(self, line: str) -> bool:
        """Exit the shell.

        Args:
            line: Ignored.

        Returns:
            bool: True to stop the command loop.
        """
        print("Exiting...")
        return True

    def do_EOF(self, line: str) -> bool:
        """Handle Ctrl+D (EOF) to exit the shell.

        Args:
            line: Ignored.

        Returns:
            bool: True to stop the command loop.
        """
        print("\nExiting...")
        return True

    # ========== Ambiguous Input Handler ==========

    def default(self, line: str) -> None:
        """Handle all ambiguous/shorthand input that doesn't match a do_* method.

        This method preserves the original flexible input style, handling:
        - Task IDs: #### (4 digits)
        - Project names: Any text matching a project
        - TASK shorthand: TASK [Description]
        - Special commands: BREAK, REST, CLS, CLEAR
        - Task operations: #### !!!, #### mmddyyyy
        - Development commands: FORCE_SUMMARY mmddyyyy
        - Default: Start text task (projectless)

        Args:
            line: The unrecognized input line.
        """
        up = line.strip()
        up_upper = up.upper()

        if not up:
            return

        # FORCE_SUMMARY mmddyyyy (development command)
        if up_upper.startswith("FORCE_SUMMARY"):
            parts = up_upper.split()
            if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) == 8:
                success, msg = handle_force_summary(self.state, parts[1])
                print(msg)
            else:
                print("Usage: FORCE_SUMMARY mmddyyyy")
            return

        tokens = up.split()

        # [####] [mmddyyyy] - Set task deadline
        if (
            len(tokens) == 2
            and tokens[0].isdigit()
            and len(tokens[0]) == 4
            and tokens[1].isdigit()
            and len(tokens[1]) == 8
        ):
            success, msg = handle_set_task_deadline(self.state, tokens[0], tokens[1])
            print(msg)
            return

        # [####] !!! - Toggle task value flag
        if (
            len(tokens) == 2
            and tokens[0].isdigit()
            and len(tokens[0]) == 4
            and tokens[1] == "!!!"
        ):
            success, msg = handle_toggle_task_value(self.state, tokens[0])
            print(msg)
            return

        # CLS/CLEAR - Clear screen
        if up_upper in ("CLS", "CLEAR"):
            success, msg = handle_clear_screen(self.state)
            print(msg)
            return

        # Time-tracking logic: Task ID (####)
        if len(up) == 4 and up.isdigit():
            success, msg = handle_start_task(self.state, up)
            print(msg)
            return

        # ### - Quick project number lookup (for END PRIORITY ### shorthand)
        if len(up) <= 3 and up.isdigit():
            # Pad to 3 digits if less than 3
            project_number = f"{int(up):03d}"
            inv = {v: k for k, v in self.state.get("project_numbers", {}).items()}
            pname = inv.get(project_number)
            if pname:
                # Treat as project name for creating task
                success, msg = handle_project_as_task(self.state, pname)
                print(msg)
                return
            else:
                print(f"Project number '{project_number}' not found.")
                return

        # Check if input matches existing project name
        proj_lookup = up_upper.strip()
        if proj_lookup in self.state.get("project_tasks", {}):
            success, msg = handle_project_as_task(self.state, proj_lookup)
            print(msg)
            return

        # TASK [Description] shorthand
        if up_upper.startswith("TASK "):
            desc = up[5:]
            success, msg = handle_task_shorthand(self.state, desc)
            print(msg)
            return

        # Default: Start text task (projectless)
        success, msg = handle_start_text_task(self.state, up)
        print(msg)
