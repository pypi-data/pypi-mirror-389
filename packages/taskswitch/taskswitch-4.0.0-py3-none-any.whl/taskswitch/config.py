"""Configuration constants for the time tracker application.

This module provides backward-compatible access to configuration values,
now loaded from YAML configuration file with environment variable overrides.

For new code, consider using config_manager.get_config() directly.
"""
from .config_manager import get_cached_config

# Load configuration
_config = get_cached_config()

# Logging configuration
LOGS_DIR = _config['logging']['dir']

# Timezone configuration
TIMEZONE_STR = _config['display']['timezone']

# State persistence configuration (legacy)
STATE_FILE = _config['state']['json_file']

# Database configuration
DATABASE_PATH = _config['database']['path']

# Feature flags
AUTO_SUMMARY = _config['features']['auto_summary']
PRIORITY_LIMIT = _config['features']['priority_limit']
BREAK_TRACKING = _config['features']['break_tracking']

# Display configuration
COLORS_ENABLED = _config['display']['colors_enabled']
CLEAR_SCREEN = _config['display']['clear_screen']
