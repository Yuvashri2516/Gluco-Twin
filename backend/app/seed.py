"""
seed.py - Synthetic patient-data generator
============================================

This module creates *realistic but entirely synthetic* patient
profiles and time-series readings.  No real patient data is used.

HOW THE GLUCOSE SIMULATION WORKS:
  1. A baseline fasting glucose is drawn per patient type
     (e.g. ~100 mg/dL for Type 2, ~90 for Pre-diabetic).
  2. We layer three effects on top:
     a) A slow circadian wave  (glucose rises in the morning).
     b) Random meal spikes     (sharp rise then exponential decay).
     c) Gaussian noise         (sensor jitter).
  3. Heart rate and HRV are generated with similar layered logic.

This approach produces data that *looks* physiologically plausible
in charts without claiming clinical accuracy.
"""

import random
import math
from datetime import datetime, timedelta, timezone

import numpy as np
from sqlalchemy.orm import Session

from app.models import Patient, GlucoseReading, VitalReading

# ---------------------------------------------------------------------------
# Reproducibility: fix the random seed so the demo always generates
# the same patients.  Remove this in production.
# ---------------------------------------------------------------------------
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Synthetic patient profiles
# ---------------------------------------------------------------------------
SYNTHETIC_PATIENTS = [
    {
        "name": "Ananya Sharma",
        "age": 52,
        "gender": "Female",
        "diabetes_type": "Type 2",
        "years_since_diagnosis": 8,
        "weight_kg": 72.0,
        "height_cm": 160.0,
    },
    {
        "name": "Rajesh Kumar",
        "age": 45,
        "gender": "Male",
        "diabetes_type": "Type 2",
        "years_since_diagnosis": 5,
        "weight_kg": 85.0,
        "height_cm": 175.0,
    },
    {
        "name": "Priya Patel",
        "age": 34,
        "gender": "Female",
        "diabetes_type": "Type 1",
        "years_since_diagnosis": 18,
        "weight_kg": 58.0,
        "height_cm": 162.0,
    },
    {
        "name": "Vikram Singh",
        "age": 61,
        "gender": "Male",
        "diabetes_type": "Type 2",
        "years_since_diagnosis": 15,
        "weight_kg": 90.0,
        "height_cm": 178.0,
    },
    {
        "name": "Meera Reddy",
        "age": 28,
        "gender": "Female",
        "diabetes_type": "Pre-diabetic",
        "years_since_diagnosis": 1,
        "weight_kg": 65.0,
        "height_cm": 158.0,
    },
]

# ---------------------------------------------------------------------------
# Glucose-generation parameters per diabetes type
# ---------------------------------------------------------------------------
GLUCOSE_PARAMS = {
    "Type 1": {"baseline": 130, "variability": 45, "spike_prob": 0.12, "spike_mag": 80},
    "Type 2": {"baseline": 145, "variability": 30, "spike_prob": 0.10, "spike_mag": 60},
    "Pre-diabetic": {"baseline": 108, "variability": 18, "spike_prob": 0.06, "spike_mag": 40},
}


def _generate_glucose_series(
    diabetes_type: str,
    num_hours: int = 72,
    interval_minutes: int = 15,
    rng: np.random.Generator | None = None,
) -> list[tuple[timedelta, float]]:
    """
    Generate a synthetic glucose time-series.

    Returns a list of (time_offset, glucose_mg_dl) tuples.
    Each tuple represents one reading spaced `interval_minutes` apart.
    """
    if rng is None:
        rng = np.random.default_rng(RANDOM_SEED)

    params = GLUCOSE_PARAMS.get(diabetes_type, GLUCOSE_PARAMS["Type 2"])
    total_points = (num_hours * 60) // interval_minutes
    series: list[tuple[timedelta, float]] = []

    for i in range(total_points):
        minutes_elapsed = i * interval_minutes
        hours_elapsed = minutes_elapsed / 60.0

        # --- Layer 1: Circadian rhythm (peaks around 7 AM = hour 7) ---
        circadian = 10 * math.sin(2 * math.pi * (hours_elapsed - 7) / 24)

        # --- Layer 2: Random meal spikes ---
        spike = 0.0
        if rng.random() < params["spike_prob"]:
            spike = rng.uniform(0.5, 1.0) * params["spike_mag"]

        # --- Layer 3: Sensor noise ---
        noise = rng.normal(0, params["variability"] * 0.15)

        glucose = params["baseline"] + circadian + spike + noise
        # Clamp to physiologically possible range
        glucose = float(np.clip(glucose, 40, 400))

        series.append((timedelta(minutes=minutes_elapsed), glucose))

    return series


def _generate_vital_series(
    num_hours: int = 72,
    interval_minutes: int = 15,
    rng: np.random.Generator | None = None,
) -> list[tuple[timedelta, float, float]]:
    """
    Generate synthetic heart-rate and HRV readings.

    Returns list of (time_offset, heart_rate_bpm, hrv_ms).
    """
    if rng is None:
        rng = np.random.default_rng(RANDOM_SEED)

    total_points = (num_hours * 60) // interval_minutes
    series: list[tuple[timedelta, float, float]] = []

    for i in range(total_points):
        minutes_elapsed = i * interval_minutes
        hours_elapsed = minutes_elapsed / 60.0

        # Resting HR ~72 bpm with circadian dip at night
        hr = 72 + 5 * math.sin(2 * math.pi * (hours_elapsed - 14) / 24)
        hr += rng.normal(0, 4)
        hr = float(np.clip(hr, 50, 120))

        # HRV inversely related to HR (higher HR -> lower HRV)
        hrv = 50 - 0.3 * (hr - 72) + rng.normal(0, 8)
        hrv = float(np.clip(hrv, 10, 120))

        series.append((timedelta(minutes=minutes_elapsed), hr, hrv))

    return series


def refresh_synthetic_telemetry(db: Session, max_catchup_hours: int = 72) -> int:
    """
    Safely advance synthetic demo telemetry forward to current wall-clock UTC time.

    BEHAVIOR & SAFETY CONSTRAINTS:
      1. Strictly preserves all existing patient profiles, historical readings, and alerts.
      2. Zero deletions or overwrites: only appends new synthetic readings with current timestamps.
      3. Idempotent: If readings are already within 15 minutes of current UTC time, does nothing.
      4. Capped batch size: Caps forward generation at `max_catchup_hours` (default 72h = 288 points per patient)
         to prevent unexpected data volume explosion after prolonged server downtime.
      5. Explicit synthetic demo data: Generated exclusively using the circadian/noise simulation model.

    Returns:
        int: Total number of new glucose readings added across all patients.
    """
    patients = db.query(Patient).order_by(Patient.id.asc()).all()
    if not patients:
        return 0

    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    interval_minutes = 15
    total_added = 0

    for patient in patients:
        latest_glucose = (
            db.query(GlucoseReading)
            .filter(GlucoseReading.patient_id == patient.id)
            .order_by(GlucoseReading.timestamp.desc())
            .first()
        )
        if not latest_glucose:
            continue

        latest_ts = (
            latest_glucose.timestamp.replace(tzinfo=None)
            if latest_glucose.timestamp.tzinfo
            else latest_glucose.timestamp
        )
        elapsed_seconds = (now_utc - latest_ts).total_seconds()

        # If latest reading is within one sampling interval (15 mins), patient is already up to date
        if elapsed_seconds < interval_minutes * 60:
            continue

        steps = int(elapsed_seconds // (interval_minutes * 60))
        max_steps = (max_catchup_hours * 60) // interval_minutes

        if steps > max_steps:
            start_ts = now_utc - timedelta(hours=max_catchup_hours)
            steps = max_steps
        else:
            start_ts = latest_ts

        params = GLUCOSE_PARAMS.get(patient.diabetes_type, GLUCOSE_PARAMS["Type 2"])
        rng_glucose = np.random.default_rng(RANDOM_SEED + patient.id * 1000 + int(start_ts.timestamp()))
        rng_vital = np.random.default_rng(RANDOM_SEED + patient.id * 2000 + int(start_ts.timestamp()))

        for step in range(1, steps + 1):
            point_time = start_ts + timedelta(minutes=step * interval_minutes)
            if point_time > now_utc:
                break
            hours_elapsed = point_time.hour + (point_time.minute / 60.0)

            # --- Glucose generation (circadian wave + meal spikes + sensor jitter) ---
            circadian = 10 * math.sin(2 * math.pi * (hours_elapsed - 7) / 24)
            spike = 0.0
            if rng_glucose.random() < params["spike_prob"]:
                spike = float(rng_glucose.uniform(0.5, 1.0) * params["spike_mag"])
            noise = float(rng_glucose.normal(0, params["variability"] * 0.15))
            glucose_val = float(np.clip(params["baseline"] + circadian + spike + noise, 40, 400))

            db.add(GlucoseReading(
                patient_id=patient.id,
                timestamp=point_time,
                value=round(glucose_val, 1),
                is_valid=True,
            ))

            # --- Vitals generation (heart rate + HRV) ---
            hr = 72 + 5 * math.sin(2 * math.pi * (hours_elapsed - 14) / 24) + float(rng_vital.normal(0, 4))
            hr = float(np.clip(hr, 50, 120))
            hrv = 50 - 0.3 * (hr - 72) + float(rng_vital.normal(0, 8))
            hrv = float(np.clip(hrv, 10, 120))

            db.add(VitalReading(
                patient_id=patient.id,
                timestamp=point_time,
                heart_rate=round(hr, 1),
                hrv=round(hrv, 1),
            ))

            total_added += 1

    if total_added > 0:
        try:
            db.commit()
            print(f"[REFRESH] Added {total_added} synthetic readings to advance telemetry up to {now_utc.isoformat()}.")
        except Exception:
            db.rollback()
            raise
    else:
        print("[INFO] Synthetic telemetry already up to date -- 0 readings added.")

    return total_added


def seed_database(db: Session) -> bool:
    """
    Populate the database with synthetic patients and 72 hours
    of readings if the patients table is empty.
    If patient records already exist, safely refreshes synthetic demo telemetry.

    This function is *idempotent*: calling it again when data
    already exists does not duplicate records or modify existing data.

    Returns:
        bool: True if initial fresh seeding was performed, False otherwise.
    """
    # Check if data already exists
    if db.query(Patient).first() is not None:
        print("[INFO] Database already seeded -- refreshing synthetic telemetry if needed.")
        refresh_synthetic_telemetry(db)
        return False

    print("[SEED] Seeding database with synthetic patient data ...")
    rng = np.random.default_rng(RANDOM_SEED)

    # Time anchor: readings start 72 hours before "now"
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    start_time = now - timedelta(hours=72)

    for i, profile in enumerate(SYNTHETIC_PATIENTS):
        # Create patient
        patient = Patient(**profile)
        db.add(patient)
        db.flush()  # Assigns patient.id without committing

        # Generate glucose readings
        glucose_series = _generate_glucose_series(
            profile["diabetes_type"], rng=np.random.default_rng(RANDOM_SEED + i)
        )
        for offset, value in glucose_series:
            db.add(GlucoseReading(
                patient_id=patient.id,
                timestamp=start_time + offset,
                value=round(value, 1),
                is_valid=True,
            ))

        # Generate vital readings
        vital_series = _generate_vital_series(
            rng=np.random.default_rng(RANDOM_SEED + i + 100)
        )
        for offset, hr, hrv in vital_series:
            db.add(VitalReading(
                patient_id=patient.id,
                timestamp=start_time + offset,
                heart_rate=round(hr, 1),
                hrv=round(hrv, 1),
            ))

        print(f"  [+] Patient {patient.id}: {patient.name}  "
              f"({len(glucose_series)} glucose + {len(vital_series)} vital readings)")

    db.commit()
    print("[DONE] Seeding complete.")
    return True
