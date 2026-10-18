"""
routers/readings.py - Glucose & vital-sign reading endpoints
=============================================================

Provides time-series data for the frontend charts:
  GET  /api/readings/glucose/{patient_id}  -> glucose history
  GET  /api/readings/vitals/{patient_id}   -> HR + HRV history

Both endpoints accept an optional `hours` query parameter to
limit how far back to look (defaults to 24 hours).
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models import GlucoseReading, VitalReading, Patient, SleepRecord, StepRecord
from app.schemas import (
    GlucoseReadingRead,
    VitalReadingRead,
    SleepRecordRead,
    SleepSummaryResponse,
    StepRecordRead,
    StepSummaryResponse,
)

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
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{patient_id} not found.")

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).replace(tzinfo=None)
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
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{patient_id} not found.")

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).replace(tzinfo=None)
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


@router.get("/sleep/{patient_id}", response_model=SleepSummaryResponse)
def get_sleep_readings(
    patient_id: int,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history to return"),
    db: Session = Depends(get_db),
):
    """
    Return synthetic sleep architecture stages and aggregate metrics for a patient.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{patient_id} not found.")

    latest_s = (
        db.query(SleepRecord)
        .filter(SleepRecord.patient_id == patient_id)
        .order_by(SleepRecord.end_time.desc())
        .first()
    )
    ref_time = latest_s.end_time if latest_s else datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = ref_time - timedelta(hours=hours)

    records = (
        db.query(SleepRecord)
        .filter(
            SleepRecord.patient_id == patient_id,
            SleepRecord.end_time >= cutoff,
            SleepRecord.start_time <= ref_time,
        )
        .order_by(SleepRecord.start_time.asc())
        .all()
    )

    total_sleep_mins = sum(r.duration_minutes for r in records if r.stage in ("light", "deep", "rem"))
    deep_mins = sum(r.duration_minutes for r in records if r.stage == "deep")
    rem_mins = sum(r.duration_minutes for r in records if r.stage == "rem")
    light_mins = sum(r.duration_minutes for r in records if r.stage == "light")
    awake_mins = sum(r.duration_minutes for r in records if r.stage == "awake")
    total_time_in_bed = total_sleep_mins + awake_mins
    efficiency = round((total_sleep_mins / total_time_in_bed * 100.0), 1) if total_time_in_bed > 0 else 0.0

    return SleepSummaryResponse(
        patient_id=patient.id,
        total_sleep_hours=round(total_sleep_mins / 60.0, 1),
        deep_sleep_hours=round(deep_mins / 60.0, 1),
        rem_sleep_hours=round(rem_mins / 60.0, 1),
        light_sleep_hours=round(light_mins / 60.0, 1),
        sleep_efficiency_pct=efficiency,
        records=records,
        is_synthetic_data=True,
    )


@router.get("/steps/{patient_id}", response_model=StepSummaryResponse)
def get_step_readings(
    patient_id: int,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history to return"),
    db: Session = Depends(get_db),
):
    """
    Return physical activity step counts distinguishing 15-minute interval steps
    from daily cumulative step totals.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{patient_id} not found.")

    latest_step = (
        db.query(StepRecord)
        .filter(StepRecord.patient_id == patient_id)
        .order_by(StepRecord.timestamp.desc())
        .first()
    )
    ref_time = latest_step.timestamp if latest_step else datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = ref_time - timedelta(hours=hours)

    records = (
        db.query(StepRecord)
        .filter(
            StepRecord.patient_id == patient_id,
            StepRecord.timestamp >= cutoff,
            StepRecord.timestamp <= ref_time,
        )
        .order_by(StepRecord.timestamp.asc())
        .all()
    )

    total_steps_in_window = sum(r.interval_steps for r in records)
    latest_interval = records[-1].interval_steps if records else 0
    peak_interval = max((r.interval_steps for r in records), default=0)
    hourly_avg = round(total_steps_in_window / max(1, hours), 1)

    return StepSummaryResponse(
        patient_id=patient.id,
        total_steps_24h=total_steps_in_window,
        latest_interval_steps=latest_interval,
        peak_interval_steps=peak_interval,
        hourly_average_steps=hourly_avg,
        records=records,
        is_synthetic_data=True,
    )
