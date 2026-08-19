"""Shared pytest configuration for the test suite.

Two kinds of tests live in this directory:

- Offline tests: run against a throwaway SQLite database and never need a
  Gemini API key. These always run (they are what CI executes).
- Integration tests: drive live Gemini agents and require GOOGLE_API_KEY.
  They are only collected when the key is present in the environment.

Run everything from the repo root with ``uv run pytest``.
"""

import atexit
import os
import shutil
import tempfile

# Point the whole test process at a throwaway database before any project
# module is imported, so tests never touch db/synthetic_data.db.
_TMP_DIR = tempfile.mkdtemp(prefix="synthetic-data-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DIR}/test.db"
atexit.register(shutil.rmtree, _TMP_DIR, ignore_errors=True)

# Script-style test modules that exercise live Gemini agents.
_INTEGRATION_TEST_FILES = [
    "test_end_to_end.py",
    "test_orchestrator_workflows.py",
    "test_research_agent.py",
    "test_research_integration.py",
    "test_workflow_direct.py",
]

if not os.environ.get("GOOGLE_API_KEY"):
    collect_ignore = _INTEGRATION_TEST_FILES
