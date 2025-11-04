"""
Parser Module.

This module provides functions to load and parse task configurations
from YAML or JSON files.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import yaml

logger = logging.getLogger(__name__)


def load_tasks(config_path: str) -> List[Dict[str, Any]]:
    """
    Load tasks from a YAML or JSON configuration file.
    
    Args:
        config_path: Path to the configuration file (.yaml, .yml, or .json)
    
    Returns:
        List of task dictionaries, each containing 'action' and optional 'params'
    
    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        ValueError: If the file format is unsupported or invalid
    """
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    suffix = path.suffix.lower()
    
    try:
        if suffix in [".yaml", ".yml"]:
            tasks = _load_yaml(path)
        elif suffix == ".json":
            tasks = _load_json(path)
        else:
            raise ValueError(
                f"Unsupported file format: {suffix}. "
                "Please use .yaml, .yml, or .json"
            )
        
        # Validate the structure
        _validate_tasks(tasks)
        
        return tasks
        
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        raise


def _load_yaml(path: Path) -> List[Dict[str, Any]]:
    """
    Load tasks from a YAML file.
    
    Args:
        path: Path object pointing to the YAML file
    
    Returns:
        List of task dictionaries
    """
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    if not isinstance(data, dict):
        raise ValueError("YAML file must contain a dictionary at the root level")
    
    tasks = data.get("tasks", [])
    
    if not isinstance(tasks, list):
        raise ValueError("'tasks' field must be a list")
    
    return tasks


def _load_json(path: Path) -> List[Dict[str, Any]]:
    """
    Load tasks from a JSON file.
    
    Args:
        path: Path object pointing to the JSON file
    
    Returns:
        List of task dictionaries
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not isinstance(data, dict):
        raise ValueError("JSON file must contain an object at the root level")
    
    tasks = data.get("tasks", [])
    
    if not isinstance(tasks, list):
        raise ValueError("'tasks' field must be an array")
    
    return tasks


def _validate_tasks(tasks: List[Dict[str, Any]]) -> None:
    """
    Validate the structure of loaded tasks.
    
    Args:
        tasks: List of task dictionaries to validate
    
    Raises:
        ValueError: If any task has an invalid structure
    """
    if not tasks:
        logger.warning("No tasks found in configuration file")
        return
    
    for idx, task in enumerate(tasks, start=1):
        if not isinstance(task, dict):
            raise ValueError(f"Task {idx} must be a dictionary")
        
        if "action" not in task:
            raise ValueError(f"Task {idx} is missing the required 'action' field")
        
        if not isinstance(task["action"], str):
            raise ValueError(f"Task {idx}: 'action' must be a string")
        
        if "params" in task and not isinstance(task["params"], dict):
            raise ValueError(f"Task {idx}: 'params' must be a dictionary")
