PYTHON_DIRS = src/rock_paper_scissors tests app

.PHONY: setup setup-ci sync lint lint-ci format check-format lint-check-fix lint-check test test-cov upgrade release clean

# Environment Setup
# This is for a full, local developer setup.
setup:
	@echo "Setting up the development environment..."
	@uv sync --extra dev
	@uv pip install -e .
	@uv run pre-commit install
	@echo "Development environment setup complete!"

# This is a lean setup, specifically for the CI runner.
setup-ci:
	@echo "Setting up CI environment..."
	@uv sync --extra dev
	@uv pip install -e .
	@echo "CI environment is ready!"

# This is just for updating an existing local environment.
sync:
	@echo "Syncing dependencies from uv.lock..."
	@uv sync --extra dev
	@echo "Virtual environment is up to date!"

# Linting & Formatting
# The main target for local development. Fixes what it can.
lint: format lint-check-fix
	@echo "All local checks passed and auto-fixes applied!"

# The main target for CI. Checks everything but changes nothing.
lint-ci: check-format lint-check test
	@echo "All CI checks passed!"

# Helper target to auto-format the code.
format:
	@echo "Formatting code with Ruff..."
	@uv run ruff format $(PYTHON_DIRS)

# Helper target to check if code is formatted (for CI).
check-format:
	@echo "Checking code formatting with Ruff..."
	@uv run ruff format --check $(PYTHON_DIRS)

# Helper target to run static analysis and auto-fix (for local use).
lint-check-fix:
	@echo "Running linter with auto-fix (Ruff) and type checker (Mypy)..."
	@uv run ruff check --fix $(PYTHON_DIRS)
	@uv run mypy $(PYTHON_DIRS)

# Helper target to run static analysis without fixing (for CI).
lint-check:
	@echo "Checking for linting errors and type issues..."
	@uv run ruff check $(PYTHON_DIRS)
	@uv run mypy $(PYTHON_DIRS)

# Testing
test:
	@echo "Running test suite with pytest..."
	@uv run pytest

test-cov:
	@echo "Running tests and generating coverage report..."
	@uv run pytest --cov=rock_paper_scissors --cov-report=term-missing

# Dependency Management
upgrade:
	@echo "Upgrading all project dependencies..."
	@uv pip install --upgrade --extra dev .
	@echo "Dependencies upgraded!"

# Release & Cleanup
release:
	@echo "Starting release process..."
	@./release.sh

clean:
	@echo "Cleaning up temporary and build files..."
	@rm -rf .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "Cleanup complete!"