"""
Test suite for TaskFlow pipeline execution.

This module contains pytest tests to verify that the TaskFlow engine
correctly loads and executes task pipelines.
"""

import pytest
from pathlib import Path
from taskflow import TaskFlow
from taskflow.parser import load_tasks


@pytest.fixture
def example_yaml_path() -> str:
    """
    Fixture providing the path to the example YAML file.
    
    Returns:
        Path to examples/tasks.yaml
    """
    return "examples/tasks.yaml"


@pytest.fixture
def example_json_path() -> str:
    """
    Fixture providing the path to the example JSON file.
    
    Returns:
        Path to examples/tasks.json
    """
    return "examples/tasks.json"


def test_load_yaml_tasks(example_yaml_path: str) -> None:
    """
    Test that YAML tasks can be loaded successfully.
    
    Args:
        example_yaml_path: Path to the example YAML file
    """
    tasks = load_tasks(example_yaml_path)
    
    assert isinstance(tasks, list)
    assert len(tasks) > 0
    
    # Verify each task has required fields
    for task in tasks:
        assert "action" in task
        assert isinstance(task["action"], str)


def test_load_json_tasks(example_json_path: str) -> None:
    """
    Test that JSON tasks can be loaded successfully.
    
    Args:
        example_json_path: Path to the example JSON file
    """
    tasks = load_tasks(example_json_path)
    
    assert isinstance(tasks, list)
    assert len(tasks) > 0
    
    # Verify each task has required fields
    for task in tasks:
        assert "action" in task
        assert isinstance(task["action"], str)


def test_taskflow_initialization(example_yaml_path: str) -> None:
    """
    Test that TaskFlow can be initialized with a config file.
    
    Args:
        example_yaml_path: Path to the example YAML file
    """
    pipeline = TaskFlow(example_yaml_path)
    
    assert pipeline.config_path == example_yaml_path
    assert isinstance(pipeline.action_map, dict)
    assert len(pipeline.action_map) > 0


def test_taskflow_run_yaml(example_yaml_path: str) -> None:
    """
    Test that TaskFlow can execute a YAML pipeline without errors.
    
    Args:
        example_yaml_path: Path to the example YAML file
    """
    pipeline = TaskFlow(example_yaml_path)
    
    # Should execute without raising exceptions
    pipeline.run()
    
    # Verify tasks were loaded
    assert len(pipeline.tasks) > 0


def test_taskflow_run_json(example_json_path: str) -> None:
    """
    Test that TaskFlow can execute a JSON pipeline without errors.
    
    Args:
        example_json_path: Path to the example JSON file
    """
    pipeline = TaskFlow(example_json_path)
    
    # Should execute without raising exceptions
    pipeline.run()
    
    # Verify tasks were loaded
    assert len(pipeline.tasks) > 0


def test_invalid_action() -> None:
    """
    Test that TaskFlow raises an error for invalid actions.
    """
    # Create a temporary config with an invalid action
    import tempfile
    import yaml
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config = {
            "tasks": [
                {"action": "invalid.action", "params": {}}
            ]
        }
        yaml.dump(config, f)
        temp_path = f.name
    
    try:
        pipeline = TaskFlow(temp_path)
        
        with pytest.raises(ValueError, match="not implemented"):
            pipeline.run()
    finally:
        Path(temp_path).unlink()


def test_missing_config_file() -> None:
    """
    Test that TaskFlow raises an error for missing config files.
    """
    with pytest.raises(FileNotFoundError):
        pipeline = TaskFlow("nonexistent.yaml")
        pipeline.run()


def test_custom_action() -> None:
    """
    Test that custom actions can be registered and executed.
    """
    import tempfile
    import yaml
    
    # Create a custom action function
    def custom_function(message: str) -> None:
        print(f"Custom: {message}")
    
    # Create a temporary config with a custom action
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config = {
            "tasks": [
                {"action": "custom.test", "params": {"message": "Hello"}}
            ]
        }
        yaml.dump(config, f)
        temp_path = f.name
    
    try:
        pipeline = TaskFlow(temp_path)
        pipeline.add_custom_action("custom.test", custom_function)
        
        # Should execute without raising exceptions
        pipeline.run()
    finally:
        Path(temp_path).unlink()


def test_task_with_no_params() -> None:
    """
    Test that tasks without params can be executed.
    """
    import tempfile
    import yaml
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config = {
            "tasks": [
                {"action": "rpa.click", "params": {"target": "Button"}}
            ]
        }
        yaml.dump(config, f)
        temp_path = f.name
    
    try:
        pipeline = TaskFlow(temp_path)
        pipeline.run()
        
        assert len(pipeline.tasks) == 1
    finally:
        Path(temp_path).unlink()


def test_all_task_types() -> None:
    """
    Test that all built-in task types can be executed.
    """
    import tempfile
    import yaml
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config = {
            "tasks": [
                {"action": "rpa.click", "params": {"target": "Button"}},
                {"action": "rpa.extract_table_from_pdf", "params": {"file_path": "test.pdf"}},
                {"action": "data.clean_data", "params": {"data": "test.csv"}},
                {"action": "ai.generate_text", "params": {"prompt": "Test", "max_tokens": 50}},
            ]
        }
        yaml.dump(config, f)
        temp_path = f.name
    
    try:
        pipeline = TaskFlow(temp_path)
        pipeline.run()
        
        assert len(pipeline.tasks) == 4
    finally:
        Path(temp_path).unlink()
