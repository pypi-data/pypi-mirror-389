#!/usr/bin/env python3
"""Entry point for running taskswitch as a module: python -m taskswitch"""
from .shell import TaskSwitchShell


def main():
    """Main entry point for the taskswitch command."""
    shell = TaskSwitchShell()
    shell.cmdloop()


if __name__ == "__main__":
    main()
