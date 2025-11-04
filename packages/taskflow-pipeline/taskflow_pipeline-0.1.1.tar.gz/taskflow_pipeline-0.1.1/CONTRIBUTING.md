# Contributing to TaskFlow

First off, thank you for considering contributing to TaskFlow! 🎉

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)

## Code of Conduct

This project and everyone participating in it is governed by respect and professionalism. Please be kind and courteous to others.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue tracker as you might find that you don't need to create one. When you create a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** (code snippets, YAML configs)
- **Describe the behavior you observed and what you expected**
- **Include your Python version and OS**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. Create an issue and provide:

- **A clear and descriptive title**
- **A detailed description of the suggested enhancement**
- **Examples of how the enhancement would be used**
- **Why this enhancement would be useful**

### Your First Code Contribution

Unsure where to begin? Look for issues labeled:
- `good-first-issue` - Simple issues for beginners
- `help-wanted` - Issues that need assistance

### Adding New Task Modules

To add a new task module (e.g., database tasks):

1. Create a new file: `taskflow/tasks/database_tasks.py`
2. Implement task functions with type hints and docstrings
3. Update `taskflow/tasks/__init__.py` to export the module
4. Register actions in `taskflow/core.py`'s `_build_action_map()`
5. Add tests in `tests/test_database_tasks.py`
6. Update documentation

Example:

```python
# taskflow/tasks/database_tasks.py
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def query_database(connection_string: str, query: str) -> List[Dict[str, Any]]:
    """
    Execute a database query.
    
    Args:
        connection_string: Database connection string
        query: SQL query to execute
    
    Returns:
        List of result rows as dictionaries
    """
    logger.info(f"Executing query: {query}")
    # Implementation here
    return []
```

## Development Setup

1. **Fork and clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/taskflow-pipeline.git
cd taskflow-pipeline
```

2. **Create a virtual environment**

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install development dependencies**

```bash
pip install -e ".[dev]"
```

4. **Create a branch**

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

## Pull Request Process

1. **Update tests** - Ensure all existing tests pass and add new tests for your changes

```bash
pytest
```

2. **Format your code** - Use black for code formatting

```bash
black taskflow tests
```

3. **Type checking** - Run mypy

```bash
mypy taskflow
```

4. **Update documentation** - Update README.md, docstrings, and CHANGELOG.md

5. **Commit your changes** - Use clear commit messages

```bash
git commit -m "Add feature: description of your changes"
```

6. **Push to your fork**

```bash
git push origin feature/your-feature-name
```

7. **Create a Pull Request** - Go to GitHub and create a PR with:
   - Clear title and description
   - Reference to related issues
   - Screenshots/examples if applicable

## Coding Standards

### Python Style Guide

- Follow PEP 8
- Use type hints for all function parameters and return values
- Maximum line length: 88 characters (Black default)
- Use descriptive variable names

### Documentation

- Every module, class, and function must have a docstring
- Use Google-style docstrings
- Include examples in docstrings for complex functions

Example:

```python
def example_function(param1: str, param2: int = 10) -> bool:
    """
    Brief description of the function.
    
    More detailed explanation if needed. Can span multiple lines
    and include examples.
    
    Args:
        param1: Description of param1
        param2: Description of param2, defaults to 10
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When param2 is negative
    
    Example:
        >>> result = example_function("test", 5)
        >>> print(result)
        True
    """
    if param2 < 0:
        raise ValueError("param2 must be non-negative")
    return True
```

### Logging

- Use the logging module, not print statements
- Log levels:
  - DEBUG: Detailed information for debugging
  - INFO: General information about task execution
  - WARNING: Warning messages
  - ERROR: Error messages

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.info("Starting process")
    logger.debug(f"Processing with parameters: {params}")
    logger.error("An error occurred")
```

## Testing Guidelines

### Writing Tests

- Write tests for all new features
- Test both success and failure cases
- Use descriptive test names: `test_<functionality>_<scenario>`
- Use pytest fixtures for common setup

Example:

```python
import pytest
from taskflow import TaskFlow

def test_custom_action_executes_successfully():
    """Test that custom actions can be registered and executed."""
    def custom_func(message: str) -> None:
        print(message)
    
    pipeline = TaskFlow("test_config.yaml")
    pipeline.add_custom_action("custom.test", custom_func)
    pipeline.run()
    
    assert len(pipeline.tasks) > 0
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=taskflow --cov-report=html

# Run specific test file
pytest tests/test_pipeline.py

# Run specific test
pytest tests/test_pipeline.py::test_taskflow_run_yaml
```

### Test Coverage

- Aim for >80% code coverage
- All new code must have tests
- Critical paths must have 100% coverage

## Adding Dependencies

When adding new dependencies:

1. Add to `dependencies` in `pyproject.toml` for runtime deps
2. Add to `dev` optional dependencies for development deps
3. Document why the dependency is needed
4. Consider the dependency's maintenance status

## Release Process

(For maintainers only)

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Run full test suite
4. Create a git tag
5. Build and publish to PyPI

## Questions?

Feel free to open an issue with the `question` label if you need help!

## Thank You!

Your contributions make TaskFlow better for everyone! 🙏
