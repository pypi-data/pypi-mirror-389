# TaskFlow

[![PyPI version](https://badge.fury.io/py/taskflow-pipeline.svg)](https://badge.fury.io/py/taskflow-pipeline)
[![Python Versions](https://img.shields.io/pypi/pyversions/taskflow-pipeline.svg)](https://pypi.org/project/taskflow-pipeline/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/berkterekli/taskflow-pipeline/workflows/Tests/badge.svg)](https://github.com/berkterekli/taskflow-pipeline/actions)

A Python library for orchestrating automated pipelines including RPA (desktop/web automation), data processing, and AI tasks using YAML or JSON configuration files.

## Features

- **Configuration-based execution**: Define your task pipelines in YAML or JSON
- **Modular task system**: Supports RPA, data processing, and AI tasks
- **Easy extensibility**: Add custom task modules with simple function definitions
- **Type-safe**: Built with type hints for better IDE support
- **Error handling**: Clear error messages for debugging pipelines

## Installation

```bash
pip install taskflow-pipeline
```

For development:

```bash
git clone https://github.com/berkterekli/taskflow-pipeline.git
cd taskflow-pipeline
pip install -e ".[dev]"
```

## Quick Start

1. Create a `tasks.yaml` file:

```yaml
tasks:
  - action: "rpa.click"
    params:
      target: "Submit Button"
  
  - action: "data.clean_data"
    params:
      data: "sample_data.csv"
```

2. Run your pipeline:

```python
from taskflow import TaskFlow

# Initialize and run the pipeline
pipeline = TaskFlow("tasks.yaml")
pipeline.run()
```

## Task Types

### RPA Tasks
- `rpa.click`: Simulate clicking on UI elements
- `rpa.extract_table_from_pdf`: Extract tables from PDF files

### Data Tasks
- `data.clean_data`: Clean and preprocess data

### AI Tasks
- `ai.generate_text`: Generate text using AI models

## Project Structure

```
taskflow/
├── __init__.py
├── core.py          # Main TaskFlow engine
├── parser.py        # YAML/JSON parser
└── tasks/
    ├── __init__.py
    ├── rpa_tasks.py      # RPA automation tasks
    ├── data_tasks.py     # Data processing tasks
    └── ai_tasks.py       # AI-related tasks
```

## Development

Run tests:

```bash
pytest
```

Format code:

```bash
black taskflow tests
```

Type checking:

```bash
mypy taskflow
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Publishing

See [PUBLISHING_GUIDE.md](PUBLISHING_GUIDE.md) for detailed instructions on publishing to PyPI.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.

## Author

**Berk Terekli**

## Support

- 📖 [Documentation](https://github.com/berkterekli/taskflow-pipeline#readme)
- 🐛 [Issue Tracker](https://github.com/berkterekli/taskflow-pipeline/issues)
- 💬 [Discussions](https://github.com/berkterekli/taskflow-pipeline/discussions)
