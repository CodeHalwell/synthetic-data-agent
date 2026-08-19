"""Central database configuration.

Every component that needs a database connection (agent tools, utility
scripts, tests) should get its engine from here so the whole project agrees
on a single database location.

The database URL is resolved in this order:
1. The ``DATABASE_URL`` environment variable (any SQLAlchemy-compatible URL).
2. A SQLite database at ``db/synthetic_data.db`` in the project root.
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from schema.synthetic_data import Base

DEFAULT_SQLITE_PATH = PROJECT_ROOT / "db" / "synthetic_data.db"


def get_database_url() -> str:
    """Return the configured database URL, defaulting to the project SQLite file."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    DEFAULT_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"


def create_db_engine(database_url: str | None = None, *, echo: bool = False) -> Engine:
    """Create an engine for the configured database and ensure all tables exist.

    ``Base.metadata.create_all`` is idempotent, so calling this repeatedly is
    safe and removes the need for a separate initialization step.
    """
    engine = create_engine(database_url or get_database_url(), echo=echo)
    Base.metadata.create_all(engine)
    return engine


def create_session_factory(database_url: str | None = None) -> sessionmaker:
    """Create a session factory bound to a fresh engine."""
    return sessionmaker(bind=create_db_engine(database_url))
