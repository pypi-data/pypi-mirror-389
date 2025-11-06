# Domolibrary

A Python library for interacting with Domo APIs.

## Installation

```bash
pip install domolibrary
```

## Usage

```python
from domolibrary import DomoUser
# Your code here
```

## Project Structure

```
src/                      # Main package source code
├── classes/              # Domain model classes
├── client/               # API client utilities
├── integrations/         # Integration modules
├── routes/               # API route implementations
├── utils/                # Utility functions
├── __init__.py           # Package initialization
└── _modidx.py           # Module index
scripts/                  # Development scripts
tests/                    # Test files
.vscode/                  # VS Code configuration
.github/workflows/        # CI/CD workflows
```

## Development

This project uses `uv` for dependency management and development.

### Setup Development Environment

```bash
# Initial setup (run once)
.\scripts\setup-dev.ps1
```

### Development Scripts

All development scripts are located in the `scripts/` folder:

- **`.\scripts\setup-dev.ps1`** - Setup development environment
- **`.\scripts\lint.ps1`** - Run linting and formatting
- **`.\scripts\test.ps1`** - Run tests with coverage
- **`.\scripts\build.ps1`** - Build the package
- **`.\scripts\publish.ps1`** - Publish to PyPI

### Manual Development Commands

```bash
# Install dependencies
uv sync --dev

# Run linting
uv run ruff check src/
uv run pylint src/domolibrary

# Run formatting
uv run black src/
uv run isort src/

# Run tests
uv run pytest tests/

# Build package
uv build
```
