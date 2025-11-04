# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Web scraping tasks module
- Database integration tasks
- Conditional task execution
- Parallel task execution
- Task retry mechanisms
- Custom error handlers

## [0.1.0] - 2025-11-03

### Added
- Initial release of TaskFlow
- Core TaskFlow engine for pipeline orchestration
- YAML and JSON configuration support
- Parser module with validation
- RPA tasks module:
  - `click()` - Simulate UI clicks
  - `extract_table_from_pdf()` - Extract tables from PDFs
  - `type_text()` - Type text into UI elements
  - `take_screenshot()` - Capture screenshots
- Data processing tasks module:
  - `clean_data()` - Clean and preprocess data
  - `transform_data()` - Transform data with operations
  - `merge_datasets()` - Merge multiple datasets
  - `validate_data()` - Validate data against schemas
- AI tasks module:
  - `generate_text()` - AI text generation
  - `classify_text()` - Text classification
  - `analyze_sentiment()` - Sentiment analysis
  - `extract_entities()` - Named entity extraction
- Custom action registration support
- Comprehensive error handling and logging
- Type hints throughout the codebase
- Complete test suite with pytest
- Example YAML and JSON configurations
- Example usage scripts
- Full documentation (README, Quick Start Guide)

### Features
- ✅ Configuration-based pipeline execution
- ✅ Action mapping system
- ✅ Parameter validation
- ✅ Detailed logging
- ✅ Extensible architecture
- ✅ Python 3.8+ support

---

## Version History

- **0.1.0** (2025-11-03) - Initial Release

---

## Upgrade Guide

### From Development to 0.1.0
This is the first public release. No upgrade steps required.

---

## Notes

- All placeholder implementations are clearly documented
- Production usage requires implementing actual automation logic
- Each task module can be extended with real libraries (Selenium, Playwright, etc.)

[Unreleased]: https://github.com/berkterekli/taskflow-pipeline/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/berkterekli/taskflow-pipeline/releases/tag/v0.1.0
