# GitDo

[![CI](https://github.com/s0b0lev/gitdo/actions/workflows/ci.yml/badge.svg)](https://github.com/s0b0lev/gitdo/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/s0b0lev/gitdo/branch/main/graph/badge.svg)](https://codecov.io/gh/s0b0lev/gitdo)
[![PyPI version](https://badge.fury.io/py/gitdo.svg)](https://badge.fury.io/py/gitdo)

Simple CLI tool to plan your work. Tasks are stored locally in a `.gitdo/` folder.

## Installation

```bash
pip install gitdo
```

## Usage

```bash
$ gitdo [command] [options]
```

## Commands

- `init`: Initialize a new GitDo project
- `add <task>`: Add a new task to your project
- `list`: List all tasks (use `--all` to show completed tasks)
- `complete <task_id>`: Mark a task as completed
- `remove <task_id>`: Remove a task from your project

## Example

```bash
# Initialize GitDo in your project
$ gitdo init
✓ GitDo initialized successfully!

# Add some tasks
$ gitdo add "Implement user authentication"
✓ Added task: Implement user authentication
ID: a1b2c3d4

$ gitdo add "Write unit tests"
✓ Added task: Write unit tests
ID: e5f6g7h8

# List all pending tasks
$ gitdo list

# Complete a task (you can use just the first few characters of the ID)
$ gitdo complete a1b2

# List all tasks including completed ones
$ gitdo list --all

# Remove a task
$ gitdo remove e5f6
```

## Development

### Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

1. Install uv:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/gitdo.git
   cd gitdo
   ```

3. Install dependencies:
   ```bash
   uv sync --extra dev
   ```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=gitdo --cov-report=html

# Run specific test file
uv run pytest tests/test_cli.py

# Run tests in watch mode (requires pytest-watch)
uv run ptw
```

### Code Quality

This project uses Ruff for linting and formatting:

```bash
# Check code
uv run ruff check .

# Format code
uv run ruff format .

# Check and fix
uv run ruff check --fix .
```

### Project Structure

```
gitdo/
├── src/
│   └── gitdo/
│       ├── __init__.py
│       ├── cli.py          # CLI interface
│       ├── models.py       # Data models
│       └── storage.py      # Storage handling
├── tests/
│   ├── conftest.py         # Pytest fixtures
│   ├── test_cli.py         # CLI tests
│   ├── test_models.py      # Model tests
│   └── test_storage.py     # Storage tests
├── pyproject.toml          # Project configuration
└── README.md
```

### Releasing to PyPI

This project uses GitHub Actions for automated publishing to PyPI. Releases are triggered by pushing version tags.

#### Automated Release (Recommended)

Use the release script to create a new version:

```bash
# Create a new release (e.g., 0.2.0)
./scripts/release.sh 0.2.0

# Push to trigger the release
git push origin main --tags
```

The script will:
1. Update version in `pyproject.toml` and `__init__.py`
2. Create a git commit
3. Create a version tag (e.g., `v0.2.0`)

When you push the tag, GitHub Actions will:
1. Extract version from the tag
2. Build the package
3. Publish to PyPI using [Trusted Publishing](https://docs.pypi.org/trusted-publishers/)


#### Manual Build (Testing)

```bash
# Build the package locally
uv build

# Check the built package
ls -la dist/
```

## License

MIT