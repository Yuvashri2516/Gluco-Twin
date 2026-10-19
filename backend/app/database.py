"""
database.py - SQLite database setup using SQLAlchemy
=====================================================

WHY SQLAlchemy?
  SQLAlchemy is the most popular Python ORM. It lets us define
  database tables as Python classes and query them with Python
  code instead of raw SQL. This makes the code safer (prevents
  SQL injection) and easier to read.

HOW IT WORKS:
  1. `create_engine` opens (or creates) the SQLite file.
  2. `SessionLocal` is a factory that produces database sessions.
     Each API request gets its own session via the `get_db` helper.
  3. `Base` is the parent class for all our ORM models.

The `get_db` function is a *dependency* that FastAPI injects into
route handlers automatically. It guarantees the session is closed
even if an error occurs (the `finally` block).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# ---------------------------------------------------------------------------
# Database file lives next to the backend/ folder for easy access.
# In production you would use PostgreSQL or similar; SQLite is perfect
# for a hackathon prototype because it needs zero setup.
# ---------------------------------------------------------------------------
DATABASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(DATABASE_DIR, "glucotwin.db")


class DatabaseConfigurationError(RuntimeError):
    """Raised when database persistence configuration is missing in production."""
    pass


env = os.environ.get("ENVIRONMENT", "development").strip().lower()
if env in ("production", "prod"):
    if "DATABASE_URL" not in os.environ:
        raise DatabaseConfigurationError(
            "CRITICAL DEPLOYMENT SAFETY ERROR: Running in production mode (ENVIRONMENT=production), "
            "but DATABASE_URL is not set. Ephemeral container disk storage will lose all patient records "
            "on container restart or redeploy. Please configure a managed database URL (e.g., PostgreSQL) "
            "or an explicit persistent volume mount path via DATABASE_URL (e.g., sqlite:////var/data/glucotwin.db)."
        )

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# `check_same_thread=False` is required for SQLite when used with FastAPI
# because FastAPI may serve requests from different threads.
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # Set to True to see generated SQL in the console (useful for debugging)
)

# Each call to SessionLocal() creates a new database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All ORM model classes will inherit from Base.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a database session per request.

    Usage in a route:
        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db  # The route handler runs while the session is open
    finally:
        db.close()  # Always close, even if the handler raised an error
