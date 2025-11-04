# TaskFlow - Quick Reference Guide

## Installation

```bash
# Install in development mode
pip install -e .

# Or install from PyPI (when published)
pip install taskflow
```

## Basic Usage

### 1. Create a configuration file (YAML or JSON)

**tasks.yaml:**
```yaml
tasks:
  - action: "rpa.click"
    params:
      target: "Submit Button"
  
  - action: "data.clean_data"
    params:
      data: "mydata.csv"
```

**tasks.json:**
```json
{
  "tasks": [
    {
      "action": "rpa.click",
      "params": {"target": "Submit Button"}
    }
  ]
}
```

### 2. Run the pipeline

```python
from taskflow import TaskFlow

# Load and execute pipeline
pipeline = TaskFlow("tasks.yaml")
pipeline.run()
```

## Available Actions

### RPA Tasks
- `rpa.click` - Simulate clicking UI elements
  - Parameters: `target` (str)
  
- `rpa.extract_table_from_pdf` - Extract tables from PDFs
  - Parameters: `file_path` (str)
  
- `rpa.type_text` - Type text into input fields
  - Parameters: `target` (str), `text` (str)
  
- `rpa.take_screenshot` - Capture screenshots
  - Parameters: `output_path` (str)

### Data Tasks
- `data.clean_data` - Clean and preprocess data
  - Parameters: `data` (str or list)
  
- `data.transform_data` - Transform data with operations
  - Parameters: `input_path` (str), `output_path` (str), `operations` (list)
  
- `data.merge_datasets` - Merge multiple datasets
  - Parameters: `datasets` (list), `output_path` (str)
  
- `data.validate_data` - Validate data against schema
  - Parameters: `data` (str), `schema` (dict)

### AI Tasks
- `ai.generate_text` - Generate text using AI
  - Parameters: `prompt` (str), `max_tokens` (int, optional)
  
- `ai.classify_text` - Classify text into categories
  - Parameters: `text` (str), `categories` (list)
  
- `ai.analyze_sentiment` - Analyze text sentiment
  - Parameters: `text` (str)
  
- `ai.extract_entities` - Extract named entities
  - Parameters: `text` (str)

## Advanced Usage

### Adding Custom Actions

```python
from taskflow import TaskFlow

def my_custom_action(param1: str, param2: int) -> None:
    print(f"Custom action: {param1}, {param2}")

# Register custom action
pipeline = TaskFlow("tasks.yaml")
pipeline.add_custom_action("custom.my_action", my_custom_action)
pipeline.run()
```

### Error Handling

```python
from taskflow import TaskFlow

try:
    pipeline = TaskFlow("tasks.yaml")
    pipeline.run()
except FileNotFoundError:
    print("Configuration file not found")
except ValueError as e:
    print(f"Invalid action or configuration: {e}")
except Exception as e:
    print(f"Pipeline execution failed: {e}")
```

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=taskflow

# Run specific test
pytest tests/test_pipeline.py::test_taskflow_run_yaml
```

## Development

```bash
# Format code
black taskflow tests

# Type checking
mypy taskflow

# Install development dependencies
pip install -e ".[dev]"
```

## Project Structure

```
taskflow/
├── __init__.py          # Package initialization
├── core.py              # Main TaskFlow engine
├── parser.py            # YAML/JSON parser
└── tasks/
    ├── rpa_tasks.py     # RPA automation functions
    ├── data_tasks.py    # Data processing functions
    └── ai_tasks.py      # AI/ML functions
```

## Examples

Run the included examples:

```bash
# YAML example
python examples/run_pipeline.py

# Or use the JSON example
python -c "from taskflow import TaskFlow; TaskFlow('examples/tasks.json').run()"
```

## Tips

1. **Always validate your YAML/JSON** - Use a validator to check syntax
2. **Start small** - Test with simple pipelines first
3. **Use logging** - Check logs for detailed execution information
4. **Extend easily** - Add new task modules in `taskflow/tasks/`
5. **Test thoroughly** - Write tests for custom actions

## Common Patterns

### Sequential Processing
```yaml
tasks:
  - action: "rpa.extract_table_from_pdf"
    params:
      file_path: "input.pdf"
  
  - action: "data.clean_data"
    params:
      data: "extracted_table.csv"
  
  - action: "ai.generate_text"
    params:
      prompt: "Summarize the cleaned data"
```

### Data Pipeline
```yaml
tasks:
  - action: "data.merge_datasets"
    params:
      datasets: ["data1.csv", "data2.csv"]
      output_path: "merged.csv"
  
  - action: "data.validate_data"
    params:
      data: "merged.csv"
      schema: {"id": "int", "name": "str"}
```

## Publishing to PyPI

```bash
# Build distribution
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

## Support

- Documentation: See README.md
- Issues: Create an issue on GitHub
- License: MIT (see LICENSE file)
