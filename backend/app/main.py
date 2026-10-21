"""
main.py - FastAPI application entry point

Responsibilities:
1. Create the FastAPI application.
2. Configure CORS for local and deployed frontends.
3. Register application routers.
4. Initialize database tables on startup.
5. Seed synthetic data in development environments.
6. Expose health-check endpoints.

Run locally from the project root:

    .\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --app-dir backend
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import engine, Base, SessionLocal

from app.models import (
    Patient,
    GlucoseReading,
    VitalReading,
    DigitalTwinState,
    Alert,
    LabResult,
    GeneticMarker,
    SleepRecord,
    StepRecord,
    MedicalDocument,
    User,
    DoctorPatientAssignment,
)  # noqa: F401

from app.seed import seed_database
from app.schemas import HealthCheck

from app.routers import (
    patients,
    readings,
    predictions,
    alerts,
    twin,
    documents,
    auth,
    reports,
)

from app.alerts_engine import (
    ensure_alert_columns,
    evaluate_all_alerts_for_patient,
)


# ============================================================
# DATABASE COMPATIBILITY HELPERS
# ============================================================

def ensure_patient_columns(engine) -> None:
    """
    Ensure legacy SQLite databases contain required columns.

    Existing data is preserved. Missing columns are added
    non-destructively.
    """

    with engine.connect() as conn:
        try:
            # Patients table
            patient_columns = conn.execute(
                text("PRAGMA table_info(patients)")
            ).fetchall()

            existing_patient_columns = {
                row[1] for row in patient_columns
            }

            if "historical_diagnoses" not in existing_patient_columns:
                conn.execute(
                    text(
                        "ALTER TABLE patients "
                        "ADD COLUMN historical_diagnoses "
                        "TEXT DEFAULT 'None'"
                    )
                )

            if "medical_history" not in existing_patient_columns:
                conn.execute(
                    text(
                        "ALTER TABLE patients "
                        "ADD COLUMN medical_history TEXT DEFAULT ''"
                    )
                )

            # Glucose readings table
            glucose_columns = conn.execute(
                text("PRAGMA table_info(glucose_readings)")
            ).fetchall()

            existing_glucose_columns = {
                row[1] for row in glucose_columns
            }

            if "unit" not in existing_glucose_columns:
                conn.execute(
                    text(
                        "ALTER TABLE glucose_readings "
                        "ADD COLUMN unit VARCHAR(20) DEFAULT 'mg/dL'"
                    )
                )

            if "data_source" not in existing_glucose_columns:
                conn.execute(
                    text(
                        "ALTER TABLE glucose_readings "
                        "ADD COLUMN data_source "
                        "VARCHAR(50) DEFAULT 'synthetic'"
                    )
                )

            # Vital readings table
            vital_columns = conn.execute(
                text("PRAGMA table_info(vital_readings)")
            ).fetchall()

            existing_vital_columns = {
                row[1] for row in vital_columns
            }

            if "data_source" not in existing_vital_columns:
                conn.execute(
                    text(
                        "ALTER TABLE vital_readings "
                        "ADD COLUMN data_source "
                        "VARCHAR(50) DEFAULT 'synthetic'"
                    )
                )

            # Lab results table
            lab_columns = conn.execute(
                text("PRAGMA table_info(lab_results)")
            ).fetchall()

            existing_lab_columns = {
                row[1] for row in lab_columns
            }

            if "data_source" not in existing_lab_columns:
                conn.execute(
                    text(
                        "ALTER TABLE lab_results "
                        "ADD COLUMN data_source "
                        "VARCHAR(50) DEFAULT 'synthetic'"
                    )
                )

            if "lab_source" not in existing_lab_columns:
                conn.execute(
                    text(
                        "ALTER TABLE lab_results "
                        "ADD COLUMN lab_source VARCHAR(120) "
                        "DEFAULT 'Simulated Diagnostic Laboratory'"
                    )
                )

            conn.commit()

        except Exception as exc:
            conn.rollback()
            print(
                "[WARNING] Could not verify legacy database columns: "
                f"{exc}"
            )


def ensure_user_table(engine) -> None:
    """Ensure the SQLite users table and doctor_patient_assignments table are present non-destructively."""
    with engine.connect() as conn:
        try:
            res = conn.execute(text("PRAGMA table_info(users)")).fetchall()
            if not res:
                User.__table__.create(bind=conn, checkfirst=True)
            else:
                existing_cols = {row[1] for row in res}
                if "full_name" not in existing_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(120) DEFAULT NULL"))
                if "medical_license_number" not in existing_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN medical_license_number VARCHAR(64) DEFAULT NULL"))
                if "approval_status" not in existing_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN approval_status VARCHAR(32) DEFAULT 'approved'"))

            res_d = conn.execute(text("PRAGMA table_info(doctor_patient_assignments)")).fetchall()
            if not res_d:
                DoctorPatientAssignment.__table__.create(bind=conn, checkfirst=True)

            conn.commit()
        except Exception as exc:
            conn.rollback()
            print(f"[WARNING] Could not verify users / assignments table: {exc}")


# ============================================================
# APPLICATION LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize database resources before serving requests.

    Automated tests must not initialize or seed the regular
    development database through this lifespan handler.
    """

    if (
        os.environ.get("PYTEST_CURRENT_TEST")
        or os.environ.get("TESTING") == "1"
    ):
        yield
        return

    # Create missing database tables.
    Base.metadata.create_all(bind=engine)

    # Verify legacy schema compatibility.
    ensure_alert_columns(engine)
    ensure_patient_columns(engine)
    ensure_user_table(engine)

    print("[OK] Database tables created / verified.")

    environment = (
        os.environ.get("ENVIRONMENT", "development")
        .strip()
        .lower()
    )

    # Synthetic data is only seeded outside production.
    if environment not in ("production", "prod"):
        db = SessionLocal()

        try:
            was_freshly_seeded = seed_database(db)

            if was_freshly_seeded:
                for patient in db.query(Patient).all():
                    evaluate_all_alerts_for_patient(
                        db,
                        patient,
                    )

        finally:
            db.close()

    else:
        print(
            "[INFO] Production mode: Automatic synthetic patient "
            "and demo user seeding is disabled."
        )

    yield

    print("[OK] Shutting down GlucoTwin backend.")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="GlucoTwin API",
    description=(
        "An Intelligent Predictive Digital Twin for "
        "Proactive Glucose-Risk Monitoring."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

# Exact origins allowed to call the API from a browser.
# Origins must not contain paths or trailing slashes.

ALLOWED_ORIGINS = [
    # Local Vite development servers
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:5176",
    "http://127.0.0.1:5176",

    # Alternative local development ports
    "http://localhost:3000",
    "http://127.0.0.1:3000",

    # Deployed frontend
    "https://gluco-twin-eta.vercel.app",
]


# Allow extra origins supplied through the environment.
# Example:
# ALLOWED_ORIGINS=https://example.com,https://another.example.com

custom_origins = os.environ.get("ALLOWED_ORIGINS", "")

if custom_origins:
    for origin in custom_origins.split(","):
        clean_origin = origin.strip().rstrip("/")

        if clean_origin and clean_origin not in ALLOWED_ORIGINS:
            ALLOWED_ORIGINS.append(clean_origin)


# Allow Vercel preview deployments whose hostnames begin
# with "gluco-twin-" and end with ".vercel.app".
#
# The expression matches hostnames such as:
# gluco-twin-preview.vercel.app
#
# It does not match arbitrary unrelated websites.

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=(
        r"^https://gluco-twin-[a-zA-Z0-9-]+\.vercel\.app$"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REGISTER API ROUTERS
# ============================================================

app.include_router(patients.router)
app.include_router(readings.router)
app.include_router(predictions.router)
app.include_router(alerts.router)
app.include_router(twin.router)
app.include_router(documents.router)
app.include_router(auth.router)
app.include_router(reports.router)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get(
    "/health",
    response_model=HealthCheck,
    tags=["System"],
)
@app.get(
    "/api/health",
    response_model=HealthCheck,
    tags=["System"],
)
def health_check():
    """
    Return the backend health status.
    """

    return HealthCheck(
        status="ok",
        version="0.1.0",
        database="sqlite (glucotwin.db)",
    )