"""
TaskFlow Core Module.

This module contains the main TaskFlow engine that orchestrates
the execution of task pipelines defined in YAML or JSON files.
"""

import logging
from typing import Any, Callable, Dict, List

from taskflow.parser import load_tasks
from taskflow.tasks import rpa_tasks, data_tasks, ai_tasks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TaskFlow:
    """
    Main TaskFlow engine for executing task pipelines.
    
    The TaskFlow class loads tasks from a configuration file (YAML or JSON)
    and executes them sequentially, mapping action strings to their
    corresponding Python functions.
    
    Attributes:
        config_path: Path to the YAML or JSON configuration file
        tasks: List of task dictionaries loaded from the config file
        action_map: Dictionary mapping action strings to Python functions
    """
    
    def __init__(self, config_path: str) -> None:
        """
        Initialize TaskFlow with a configuration file.
        
        Args:
            config_path: Path to the YAML or JSON configuration file
        """
        self.config_path = config_path
        self.tasks: List[Dict[str, Any]] = []
        self.action_map: Dict[str, Callable[..., Any]] = self._build_action_map()
        logger.info(f"TaskFlow initialized with config: {config_path}")
    
    def _build_action_map(self) -> Dict[str, Callable[..., Any]]:
        """
        Build a mapping of action strings to their corresponding functions.
        
        Returns:
            Dictionary mapping action strings (e.g., "rpa.click") to functions
        """
        action_map = {
            # RPA tasks
            "rpa.click": rpa_tasks.click,
            "rpa.extract_table_from_pdf": rpa_tasks.extract_table_from_pdf,
            "rpa.type_text": rpa_tasks.type_text,
            "rpa.take_screenshot": rpa_tasks.take_screenshot,
            
            # Data tasks
            "data.clean_data": data_tasks.clean_data,
            "data.transform_data": data_tasks.transform_data,
            "data.merge_datasets": data_tasks.merge_datasets,
            "data.validate_data": data_tasks.validate_data,
            
            # AI tasks
            "ai.generate_text": ai_tasks.generate_text,
            "ai.classify_text": ai_tasks.classify_text,
            "ai.analyze_sentiment": ai_tasks.analyze_sentiment,
            "ai.extract_entities": ai_tasks.extract_entities,
        }
        return action_map
    
    def load(self) -> None:
        """
        Load tasks from the configuration file.
        
        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            ValueError: If the configuration file format is invalid
        """
        logger.info("Loading tasks from configuration file...")
        self.tasks = load_tasks(self.config_path)
        logger.info(f"Loaded {len(self.tasks)} tasks")
    
    def run(self) -> None:
        """
        Execute all tasks in the pipeline sequentially.
        
        Each task is executed by mapping its action string to the corresponding
        function and passing the task parameters.
        
        Raises:
            ValueError: If a task action is not found in the action map
            Exception: Any exception raised by individual task functions
        """
        # Load tasks if not already loaded
        if not self.tasks:
            self.load()
        
        logger.info("Starting pipeline execution...")
        
        for idx, task in enumerate(self.tasks, start=1):
            action = task.get("action")
            params = task.get("params", {})
            
            if not action:
                logger.error(f"Task {idx}: Missing 'action' field")
                raise ValueError(f"Task {idx} is missing the 'action' field")
            
            logger.info(f"Task {idx}/{len(self.tasks)}: Executing '{action}'")
            
            # Get the function corresponding to the action
            func = self.action_map.get(action)
            
            if func is None:
                error_msg = (
                    f"Action '{action}' is not implemented. "
                    f"Available actions: {', '.join(self.action_map.keys())}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            try:
                # Execute the task function with parameters
                if params:
                    result = func(**params)
                else:
                    result = func()
                
                logger.info(f"Task {idx}: Completed successfully")
                
                # Log result if function returns something
                if result is not None:
                    logger.debug(f"Task {idx} result: {result}")
                    
            except TypeError as e:
                error_msg = (
                    f"Task {idx}: Invalid parameters for action '{action}'. "
                    f"Error: {str(e)}"
                )
                logger.error(error_msg)
                raise TypeError(error_msg) from e
            
            except Exception as e:
                error_msg = f"Task {idx}: Failed with error: {str(e)}"
                logger.error(error_msg)
                raise Exception(error_msg) from e
        
        logger.info("Pipeline execution completed successfully!")
    
    def add_custom_action(self, action_name: str, func: Callable[..., Any]) -> None:
        """
        Register a custom action function.
        
        This allows users to extend TaskFlow with their own custom functions.
        
        Args:
            action_name: The action string (e.g., "custom.my_action")
            func: The Python function to execute for this action
        """
        self.action_map[action_name] = func
        logger.info(f"Registered custom action: {action_name}")
