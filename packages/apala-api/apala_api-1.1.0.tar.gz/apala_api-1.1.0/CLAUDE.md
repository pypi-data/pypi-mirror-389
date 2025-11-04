# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is `apala-api`, a Python API project in its early stages. The codebase is minimal and appears to be a starter template for a loan/financial AI API service.

## Development Environment

- **Python Version**: 3.12 (specified in `.python-version`)
- **Package Manager**: Uses `uv` for Python package management
- **Project Structure**: Simple flat structure with main entry point in `main.py`

## Common Commands

### Environment Setup
```bash
# Install specific Python version if needed
uv python install 3.12

# Create virtual environment (uv handles this automatically)
uv sync

# Add dependencies
uv add <package-name>

# Add development dependencies
uv add --dev pytest ruff mypy
```

### Running the Application
```bash
# Run the main application
uv run python main.py

# Or run directly
uv run main.py
```

### Testing
```bash
# Run tests (once pytest is added)
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Run specific test file
uv run pytest tests/test_example.py
```

### Development Tools
```bash
# Run linting
uv run ruff check .

# Run type checking
uv run mypy .

# Format code
uv run ruff format .
```

### Documentation Commands
```bash
# Build HTML documentation
uv run sphinx-build -b html docs docs/_build/html

# Clean documentation build directory
uv run python -c "import shutil; shutil.rmtree('docs/_build', ignore_errors=True)"

# Live documentation with auto-reload (opens on http://localhost:8001)
uv run sphinx-autobuild docs docs/_build/html --port 8001

# Check for broken links in documentation
uv run sphinx-build -b linkcheck docs docs/_build/linkcheck

# Open documentation in browser (macOS)
open docs/_build/html/index.html
```

## Architecture

The current codebase is minimal:
- `main.py`: Contains a simple entry point with a "Hello World" style function
- `pyproject.toml`: Basic Python project configuration with no dependencies yet
- No additional modules, tests, or complex architecture present

This appears to be a greenfield project ready for API development, likely intended for loan/financial AI services based on the project name.

## Key Files

- `main.py`: Application entry point
- `pyproject.toml`: Python project configuration and dependencies
- `.python-version`: Specifies Python 3.12 requirement
- `.gitignore`: Standard Python gitignore patterns