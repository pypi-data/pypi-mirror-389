"""
Configuration management for the taskswitch application.

This module provides YAML-based configuration with:
- Default configuration values
- YAML file loading and validation
- Environment variable overrides
- Type validation and conversion
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from .logging_config import get_database_logger

logger = get_database_logger()


# Default configuration values
DEFAULT_CONFIG = {
    'database': {
        'path': 'task_manager.db',
        'backup_enabled': True,
        'backup_dir': 'backups',
    },
    'logging': {
        'enabled': True,
        'level': 'INFO',
        'dir': 'logs',
        'max_file_size_mb': 10,
        'backup_count': 5,
        'privacy_filter': True,
    },
    'display': {
        'timezone': 'CET',
        'colors_enabled': True,
        'clear_screen': True,
        'theme': 'default',
    },
    'features': {
        'auto_summary': True,
        'priority_limit': 3,
        'break_tracking': True,
    },
    'state': {
        'json_file': 'data/current_state.json',  # Legacy support
    },
}


# Environment variable mapping to config paths
ENV_VAR_MAPPING = {
    'TASKSWITCH_DB_PATH': 'database.path',
    'TASKSWITCH_LOG_LEVEL': 'logging.level',
    'TASKSWITCH_LOG_DIR': 'logging.dir',
    'TASKSWITCH_TIMEZONE': 'display.timezone',
    'TASKSWITCH_COLORS': 'display.colors_enabled',
    'TASKSWITCH_PRIORITY_LIMIT': 'features.priority_limit',
}


def _get_nested_value(config: Dict, path: str) -> Any:
    """Get a value from a nested dictionary using dot notation.
    
    Args:
        config: The configuration dictionary
        path: Dot-separated path (e.g., 'database.path')
        
    Returns:
        The value at the specified path
    """
    keys = path.split('.')
    value = config
    for key in keys:
        value = value[key]
    return value


def _set_nested_value(config: Dict, path: str, value: Any) -> None:
    """Set a value in a nested dictionary using dot notation.
    
    Args:
        config: The configuration dictionary
        path: Dot-separated path (e.g., 'database.path')
        value: The value to set
    """
    keys = path.split('.')
    current = config
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


def _convert_type(value: str, target_type: type) -> Any:
    """Convert a string value to the target type.
    
    Args:
        value: String value to convert
        target_type: Target type (bool, int, float, str)
        
    Returns:
        Converted value
    """
    if target_type == bool:
        return value.lower() in ('true', '1', 'yes', 'on')
    elif target_type == int:
        return int(value)
    elif target_type == float:
        return float(value)
    return value


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from YAML file with environment variable overrides.
    
    Priority order (highest to lowest):
    1. Environment variables
    2. YAML configuration file
    3. Default configuration
    
    Args:
        config_path: Path to YAML config file (defaults to 'config.yaml' in project root)
        
    Returns:
        Merged configuration dictionary
    """
    # Start with default config
    config = DEFAULT_CONFIG.copy()
    
    # Determine config file path
    if config_path is None:
        # Look for config.yaml in the project root (parent of taskswitch/)
        project_root = Path(__file__).parent.parent
        config_path = project_root / 'config.yaml'
    else:
        config_path = Path(config_path)
    
    # Load YAML config if it exists
    if config_path.exists():
        logger.info(f"Loading configuration from {config_path}")
        try:
            with open(config_path, 'r') as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config:
                    config = _merge_configs(config, yaml_config)
                    logger.debug(f"YAML configuration loaded successfully")
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML config: {e}")
            logger.warning("Using default configuration")
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            logger.warning("Using default configuration")
    else:
        logger.debug(f"No config file found at {config_path}, using defaults")
    
    # Apply environment variable overrides
    config = _apply_env_overrides(config)
    
    # Validate configuration
    _validate_config(config)
    
    return config


def _merge_configs(base: Dict, override: Dict) -> Dict:
    """Recursively merge two configuration dictionaries.
    
    Args:
        base: Base configuration dictionary
        override: Override configuration dictionary
        
    Returns:
        Merged configuration dictionary
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result


def _apply_env_overrides(config: Dict) -> Dict:
    """Apply environment variable overrides to configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configuration with environment overrides applied
    """
    overrides_applied = []
    
    for env_var, config_path in ENV_VAR_MAPPING.items():
        env_value = os.environ.get(env_var)
        if env_value is not None:
            try:
                # Get the current value to determine the type
                current_value = _get_nested_value(config, config_path)
                target_type = type(current_value)
                
                # Convert and set the value
                converted_value = _convert_type(env_value, target_type)
                _set_nested_value(config, config_path, converted_value)
                
                overrides_applied.append(f"{env_var} -> {config_path}")
            except Exception as e:
                logger.warning(f"Failed to apply environment override {env_var}: {e}")
    
    if overrides_applied:
        logger.info(f"Applied {len(overrides_applied)} environment variable overrides")
        for override in overrides_applied:
            logger.debug(f"  {override}")
    
    return config


def _validate_config(config: Dict) -> None:
    """Validate configuration values.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ValueError: If configuration is invalid
    """
    # Validate logging level
    valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    log_level = config['logging']['level'].upper()
    if log_level not in valid_log_levels:
        raise ValueError(f"Invalid log level: {log_level}. Must be one of {valid_log_levels}")
    
    # Validate priority limit
    priority_limit = config['features']['priority_limit']
    if not isinstance(priority_limit, int) or priority_limit < 1 or priority_limit > 10:
        raise ValueError(f"Invalid priority_limit: {priority_limit}. Must be between 1 and 10")
    
    # Validate max file size
    max_size = config['logging']['max_file_size_mb']
    if not isinstance(max_size, (int, float)) or max_size <= 0:
        raise ValueError(f"Invalid max_file_size_mb: {max_size}. Must be positive number")
    
    logger.debug("Configuration validation passed")


def get_config() -> Dict[str, Any]:
    """Get the current application configuration.
    
    This is the main function to use when accessing configuration.
    
    Returns:
        Configuration dictionary
    """
    return load_config()


def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> None:
    """Save configuration to YAML file.
    
    Args:
        config: Configuration dictionary to save
        config_path: Path to save config file (defaults to 'config.yaml' in project root)
    """
    if config_path is None:
        project_root = Path(__file__).parent.parent
        config_path = project_root / 'config.yaml'
    else:
        config_path = Path(config_path)
    
    logger.info(f"Saving configuration to {config_path}")
    
    try:
        # Ensure parent directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        logger.info("Configuration saved successfully")
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")
        raise


# Load configuration once on module import
_global_config = None


def get_cached_config() -> Dict[str, Any]:
    """Get cached configuration (loaded once on first call).
    
    Returns:
        Cached configuration dictionary
    """
    global _global_config
    if _global_config is None:
        _global_config = load_config()
    return _global_config


def reload_config() -> Dict[str, Any]:
    """Reload configuration from file and environment.
    
    Returns:
        Reloaded configuration dictionary
    """
    global _global_config
    _global_config = load_config()
    return _global_config
