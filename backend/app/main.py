"""
main.py - FastAPI application entry point
==========================================

This is the file Uvicorn runs.  It:
  1. Creates the FastAPI app with metadata (shown in auto-docs).
  2. Configures CORS so the React frontend can call the API.
  3. Registers all routers (patients, readings, ...).
  4. Creates database tables on startup.
  5. Seeds the database with synthetic data on first run.
  6. Exposes a /health endpoint for quick sanity checks.

RUN WITH:
    cd backend
    uvicorn app.main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base, SessionLocal
from app.models import Patient, GlucoseReading, VitalReading, DigitalTwinState, Alert  # noqa: F401  (imported so Base.metadata knows about them)
from app.seed import seed_database
from app.schemas import HealthCheck
from app.routers import patients, readings


# ---------------------------------------------------------------------------
# Lifespan event  (replaces deprecated @app.on_event("startup"))
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Code before `yield` runs on startup; code after runs on shutdown.
    We use it to create tables and seed data once.
    """
    # Create all tables that don't exist yet
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created / verified.")

    # Seed synthetic data (idempotent -- safe to call every restart)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    yield  # Application runs here

    print("[OK] Shutting down GlucoTwin backend.")


# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="GlucoTwin API",
    description=(
        "An Intelligent Predictive Digital Twin for "
        "Proactive Glucose-Risk Monitoring."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS  -- allow the React dev server (port 5173) to call the API.
# In production you would restrict `allow_origins` to your domain.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permissive for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Register routers
# ---------------------------------------------------------------------------
app.include_router(patients.router)
app.include_router(readings.router)


# ---------------------------------------------------------------------------
# Health-check endpoint  (the simplest possible smoke test)
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthCheck, tags=["System"])
def health_check():
    """
    Returns OK if the server is running and the database file exists.
    Useful for monitoring tools, CI/CD pipelines, and the frontend
    connection indicator.
    """
    return HealthCheck(
        status="ok",
        version="0.1.0",
        database="sqlite (glucotwin.db)",
    )
