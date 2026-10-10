"""
routers/readings.py - Glucose & vital-sign reading endpoints
=============================================================

Provides time-series data for the frontend charts:
  GET  /api/readings/glucose/{patient_id}  -> glucose history
  GET  /api/readings/vitals/{patient_id}   -> HR + HRV history

Both endpoints accept an optional `hours` query parameter to
limit how far back to look (defaults to 24 hours).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models import GlucoseReading, VitalReading
from app.schemas import GlucoseReadingRead, VitalReadingRead

router = APIRouter(prefix="/api/readings", tags=["Readings"])


@router.get("/glucose/{patient_id}", response_model=list[GlucoseReadingRead])
def get_glucose_readings(
    patient_id: int,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history to return"),
    db: Session = Depends(get_db),
):
    """
    Return glucose readings for a patient within the last `hours` hours.

    The readings are sorted chronologically so the frontend can
    plot them directly on a time-series chart.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    readings = (
        db.query(GlucoseReading)
        .filter(
            GlucoseReading.patient_id == patient_id,
            GlucoseReading.timestamp >= cutoff,
        )
        .order_by(GlucoseReading.timestamp.asc())
        .all()
    )
    return readings


@router.get("/vitals/{patient_id}", response_model=list[VitalReadingRead])
def get_vital_readings(
    patient_id: int,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history to return"),
    db: Session = Depends(get_db),
):
    """Return heart-rate and HRV readings for a patient."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    readings = (
        db.query(VitalReading)
        .filter(
            VitalReading.patient_id == patient_id,
            VitalReading.timestamp >= cutoff,
        )
        .order_by(VitalReading.timestamp.asc())
        .all()
    )
    return readings
