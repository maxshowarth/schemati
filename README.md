# schemati

Extract critical information from P&ID diagrams and other similar schematics using ML on Databricks

## Development

### CI/CD

This repository uses GitHub Actions for continuous integration and deployment:

- **Backend Tests**: Automated testing on Python 3.13.2
- **Code Quality**: Linting, formatting, and type checking with ruff, black, isort, and mypy
- **Dependency Updates**: Automated via Dependabot

### Running Tests Locally

```bash
# Install dependencies with uv
uv sync --dev

# Run tests
PYTHONPATH=. uv run pytest backend/tests/ -v

# Run code quality checks
PYTHONPATH=. uv run ruff check backend/
PYTHONPATH=. uv run black --check backend/
PYTHONPATH=. uv run isort --check-only backend/
PYTHONPATH=. uv run mypy backend/
```

### Pre-commit Hooks

```bash
# Install pre-commit with uv
uv run pip install pre-commit

# Install hooks
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

## Repository Setup

See [docs/repository-setup.md](docs/repository-setup.md) for instructions on configuring branch protection rules and required status checks.
