"""
routers/readings.py - Glucose & vital-sign reading endpoints
=============================================================

Provides time-series data for the frontend charts:
  GET  /api/readings/glucose/{patient_id}  -> glucose history
  GET  /api/readings/vitals/{patient_id}   -> HR + HRV history
  GET  /api/readings/sleep/{patient_id}    -> sleep architecture
  GET  /api/readings/steps/{patient_id}    -> step count telemetry
  POST /api/readings/glucose               -> manual glucose entry
  POST /api/readings/vitals                -> manual vitals entry

All endpoints enforce server-side authentication and authorization.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models import GlucoseReading, VitalReading, Patient, SleepRecord, StepRecord, User
from app.schemas import (
    GlucoseReadingRead,
    VitalReadingRead,
    SleepRecordRead,
    SleepSummaryResponse,
    StepRecordRead,
    StepSummaryResponse,
    ManualGlucoseCreate,
    ManualVitalCreate,
)
from app.alerts_engine import evaluate_all_alerts_for_patient
from app.auth import get_current_user, check_patient_authorization

router = APIRouter(prefix="/api/readings", tags=["Readings"])


@router.get("/glucose/{patient_id}", response_model=list[GlucoseReadingRead])
def get_glucose_readings(
    patient_id: int,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return glucose readings for a patient within the last `hours` hours.
    Enforces server-side patient isolation check.
    """
    check_patient_authorization(patient_id, current_user)

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return heart-rate and HRV readings for a patient. Enforces patient isolation check."""
    check_patient_authorization(patient_id, current_user)

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return synthetic sleep architecture stages and aggregate metrics for a patient."""
    check_patient_authorization(patient_id, current_user)

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return physical activity step counts distinguishing 15-minute interval steps
    from daily cumulative step totals.
    """
    check_patient_authorization(patient_id, current_user)

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


# ---------------------------------------------------------------------------
# Manual Telemetry Ingestion (Phase 2 & Phase A Auth)
# ---------------------------------------------------------------------------
@router.post("/glucose", response_model=GlucoseReadingRead, status_code=status.HTTP_201_CREATED)
def create_glucose_reading(
    payload: ManualGlucoseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manually record a glucose measurement for a patient.
    Requires caller authorization for payload.patient_id.
    Supports units 'mg/dL' and 'mmol/L' (with automatic conversion to standard mg/dL).
    Validates range and evaluates clinical alerts for the patient.
    """
    check_patient_authorization(payload.patient_id, current_user)

    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{payload.patient_id} not found.")

    unit_clean = payload.unit.strip().lower()
    if unit_clean in ["mmol/l", "mmol"]:
        val_mgdl = round(payload.value * 18.0182, 1)
        stored_unit = "mmol/L"
    elif unit_clean in ["mg/dl", "mgdl"]:
        val_mgdl = round(payload.value, 1)
        stored_unit = "mg/dL"
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported glucose unit '{payload.unit}'. Supported units: 'mg/dL' or 'mmol/L'."
        )

    if val_mgdl < 20.0 or val_mgdl > 800.0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Glucose value {val_mgdl} mg/dL is outside physiological bounds (20 - 800 mg/dL)."
        )

    now_utc = datetime.now(timezone.utc)
    ts = payload.timestamp or now_utc
    if ts.tzinfo is not None:
        ts = ts.replace(tzinfo=None)

    # Check future timestamps (allow 5-min margin for clock drift)
    if ts > (now_utc.replace(tzinfo=None) + timedelta(minutes=5)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Measurement timestamp cannot be in the future."
        )

    reading = GlucoseReading(
        patient_id=patient.id,
        timestamp=ts,
        value=val_mgdl,
        unit=stored_unit,
        is_valid=True,
        data_source=payload.data_source or "manual",
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    # Evaluate alerts dynamically
    try:
        evaluate_all_alerts_for_patient(db, patient)
    except Exception:
        pass

    return reading


@router.post("/vitals", response_model=VitalReadingRead, status_code=status.HTTP_201_CREATED)
def create_vital_reading(
    payload: ManualVitalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manually record autonomic vitals (heart rate and/or HRV) for a patient.
    Requires caller authorization for payload.patient_id.
    """
    check_patient_authorization(payload.patient_id, current_user)

    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{payload.patient_id} not found.")

    if payload.heart_rate is None and payload.hrv is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one vital measurement (heart_rate or hrv) must be provided."
        )

    now_utc = datetime.now(timezone.utc)
    ts = payload.timestamp or now_utc
    if ts.tzinfo is not None:
        ts = ts.replace(tzinfo=None)

    if ts > (now_utc.replace(tzinfo=None) + timedelta(minutes=5)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Measurement timestamp cannot be in the future."
        )

    reading = VitalReading(
        patient_id=patient.id,
        timestamp=ts,
        heart_rate=round(payload.heart_rate, 1) if payload.heart_rate is not None else None,
        hrv=round(payload.hrv, 1) if payload.hrv is not None else None,
        data_source=payload.data_source or "manual",
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    try:
        evaluate_all_alerts_for_patient(db, patient)
    except Exception:
        pass

    return reading
