# Convenience targets for common development tasks (all run through uv).

.PHONY: install lint fix test run db-init db-inspect

install:  ## Install all dependencies including dev tools
	uv sync --all-groups

lint:  ## Check lint and formatting without changing files
	uv run ruff check .
	uv run ruff format --check .

fix:  ## Auto-fix lint issues and reformat
	uv run ruff check . --fix
	uv run ruff format .

test:  ## Run the test suite (offline unless GOOGLE_API_KEY is set)
	uv run pytest

run:  ## Run the demo pipeline
	uv run python main.py

db-init:  ## Create the database tables
	uv run python utils/create_database.py

db-inspect:  ## Print database contents
	uv run python utils/inspect_database.py
