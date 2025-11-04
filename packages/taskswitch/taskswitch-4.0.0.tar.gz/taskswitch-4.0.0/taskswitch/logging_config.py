"""
Logging infrastructure for the taskswitch application.

This module provides a centralized logging system with:
- Rotating file handlers to prevent log files from growing indefinitely
- Separate loggers for different components (database, timer, commands, etc.)
- Privacy-safe logging that sanitizes sensitive information
- Configurable log levels and formatting
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class PrivacyFilter(logging.Filter):
    """Filter to sanitize sensitive information from log records."""
    
    def filter(self, record):
        """Sanitize task descriptions and other sensitive data from log messages."""
        # Replace potentially sensitive task descriptions with placeholders
        if hasattr(record, 'task_desc'):
            record.task_desc = self._sanitize(record.task_desc)
        
        # Sanitize message content if it contains task descriptions
        if 'description' in str(record.msg).lower():
            # Keep the structure but hide details
            record.msg = str(record.msg).replace(
                record.msg[record.msg.find('description'):record.msg.find('description')+100],
                'description=<sanitized>'
            )
        
        return True
    
    @staticmethod
    def _sanitize(text: str, max_length: int = 30) -> str:
        """Sanitize text by truncating and adding ellipsis."""
        if not text:
            return text
        if len(text) > max_length:
            return f"{text[:max_length]}..."
        return text


def setup_logging(
    log_dir: Optional[str] = None,
    log_level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    enable_privacy_filter: bool = True
) -> None:
    """
    Set up the logging infrastructure for the application.
    
    Args:
        log_dir: Directory for log files (defaults to logs/ in project root)
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup log files to keep
        enable_privacy_filter: Whether to enable privacy filtering
    """
    # Determine log directory
    if log_dir is None:
        log_dir = Path(__file__).parent.parent / 'logs'
    else:
        log_dir = Path(log_dir)
    
    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create rotating file handler for main log
    main_log_file = log_dir / 'tracker.log'
    main_handler = RotatingFileHandler(
        main_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    main_handler.setLevel(numeric_level)
    main_handler.setFormatter(detailed_formatter)
    
    # Create rotating file handler for errors only
    error_log_file = log_dir / 'errors.log'
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Create console handler for warnings and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(simple_formatter)
    
    # Add privacy filter if enabled
    if enable_privacy_filter:
        privacy_filter = PrivacyFilter()
        main_handler.addFilter(privacy_filter)
        error_handler.addFilter(privacy_filter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove any existing handlers
    root_logger.handlers.clear()
    
    # Add handlers to root logger
    root_logger.addHandler(main_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)
    
    # Log initial message
    logging.info("=" * 60)
    logging.info("Logging system initialized")
    logging.info(f"Log directory: {log_dir}")
    logging.info(f"Log level: {log_level}")
    logging.info(f"Privacy filter: {'enabled' if enable_privacy_filter else 'disabled'}")
    logging.info("=" * 60)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific component.
    
    Args:
        name: Name of the component (e.g., 'database', 'timer', 'commands')
    
    Returns:
        Logger instance for the specified component
    """
    return logging.getLogger(f'taskswitch.{name}')


# Convenience function to create component-specific loggers
def get_database_logger() -> logging.Logger:
    """Get logger for database operations."""
    return get_logger('database')


def get_timer_logger() -> logging.Logger:
    """Get logger for timer operations."""
    return get_logger('timer')


def get_commands_logger() -> logging.Logger:
    """Get logger for command execution."""
    return get_logger('commands')


def get_migration_logger() -> logging.Logger:
    """Get logger for migration operations."""
    return get_logger('migration')


def get_reporting_logger() -> logging.Logger:
    """Get logger for reporting operations."""
    return get_logger('reporting')


# Initialize logging when module is imported
# Load configuration and set up logging
try:
    # Import here to avoid circular dependency
    try:
        from .config_manager import get_cached_config
        config = get_cached_config()
        
        # Use config values if available
        if config['logging']['enabled']:
            setup_logging(
                log_dir=config['logging']['dir'],
                log_level=config['logging']['level'],
                max_bytes=config['logging']['max_file_size_mb'] * 1024 * 1024,
                backup_count=config['logging']['backup_count'],
                enable_privacy_filter=config['logging']['privacy_filter']
            )
        else:
            # Logging disabled in config
            logging.basicConfig(level=logging.WARNING)
    except ImportError:
        # Config manager not available, use defaults
        setup_logging()
except Exception as e:
    # Fallback to basic logging if setup fails
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logging.error(f"Failed to set up advanced logging: {e}")
