"""
Task modules package initialization.

This package contains task modules for different automation domains:
- rpa_tasks: RPA (Robotic Process Automation) tasks
- data_tasks: Data processing tasks
- ai_tasks: AI-related tasks
"""

from taskflow.tasks import rpa_tasks, data_tasks, ai_tasks

__all__ = ["rpa_tasks", "data_tasks", "ai_tasks"]
