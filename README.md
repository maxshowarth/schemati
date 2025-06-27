# schemati

Extract critical information from P&ID diagrams and other similar schematics using ML on Databricks

## Development

### CI/CD

This repository uses GitHub Actions for continuous integration and deployment:

- **Backend Tests**: Automated testing on Python 3.12 and 3.13
- **Code Quality**: Linting, formatting, and type checking with ruff, black, isort, and mypy
- **Dependency Updates**: Automated via Dependabot

### Running Tests Locally

```bash
# Install dependencies
pip install -e .

# Run tests
python -m pytest backend/tests/ -v

# Run code quality checks
pip install -e .[dev]
python -m ruff check backend/
python -m black --check backend/
python -m isort --check-only backend/
python -m mypy backend/
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Repository Setup

See [docs/repository-setup.md](docs/repository-setup.md) for instructions on configuring branch protection rules and required status checks.
