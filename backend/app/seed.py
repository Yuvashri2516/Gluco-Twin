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

import os
import random
import math
from datetime import datetime, timedelta, timezone

import numpy as np
from sqlalchemy.orm import Session

from app.models import (
    Patient,
    GlucoseReading,
    VitalReading,
    LabResult,
    GeneticMarker,
    SleepRecord,
    StepRecord,
    User,
)
from app.auth import get_password_hash

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
        "historical_diagnoses": "Hypertension, Hyperlipidemia, Diabetic Neuropathy (Mild)",
        "weight_kg": 72.0,
        "height_cm": 160.0,
    },
    {
        "name": "Rajesh Kumar",
        "age": 45,
        "gender": "Male",
        "diabetes_type": "Type 2",
        "years_since_diagnosis": 5,
        "historical_diagnoses": "Hypertension, Essential Tremor",
        "weight_kg": 85.0,
        "height_cm": 175.0,
    },
    {
        "name": "Priya Patel",
        "age": 34,
        "gender": "Female",
        "diabetes_type": "Type 1",
        "years_since_diagnosis": 18,
        "historical_diagnoses": "Type 1 Diabetes (Brittle), Celiac Disease, Autoimmune Thyroiditis",
        "weight_kg": 58.0,
        "height_cm": 162.0,
    },
    {
        "name": "Vikram Singh",
        "age": 61,
        "gender": "Male",
        "diabetes_type": "Type 2",
        "years_since_diagnosis": 15,
        "historical_diagnoses": "Hypertension, Coronary Artery Disease (CAD), Microalbuminuria",
        "weight_kg": 90.0,
        "height_cm": 178.0,
    },
    {
        "name": "Meera Reddy",
        "age": 28,
        "gender": "Female",
        "diabetes_type": "Pre-diabetic",
        "years_since_diagnosis": 1,
        "historical_diagnoses": "Gestational Impaired Glucose Tolerance (Historical), Mild Dyslipidemia",
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


def seed_patient_labs_if_missing(db: Session, patient: Patient, now: datetime):
    """Seed historical laboratory panels (HbA1c, fasting glucose, lipids) if not already present."""
    if db.query(LabResult).filter(LabResult.patient_id == patient.id).first() is not None:
        return
    base_a1c = {
        "Type 1": 7.8,
        "Type 2": 7.4 if patient.age > 50 else 7.0,
        "Pre-diabetic": 5.9,
    }.get(patient.diabetes_type, 6.8)

    dates = [
        now - timedelta(days=365),
        now - timedelta(days=180),
        now - timedelta(days=30),
    ]

    for idx, d in enumerate(dates):
        a1c_val = round(base_a1c + (0.3 - idx * 0.2), 1)
        fasting_g = round(a1c_val * 18.0 - 10.0, 1)
        cholesterol = round(195.0 + (patient.id * 5) - (idx * 4), 1)
        hdl = round(48.0 + (idx * 2) if patient.gender == "Female" else 42.0 + (idx * 2), 1)
        ldl = round(cholesterol - hdl - 30.0, 1)
        trig = round(145.0 + (patient.id * 8) - (idx * 5), 1)

        db.add(LabResult(patient_id=patient.id, test_name="HbA1c", result=a1c_val, unit="%", measurement_date=d, reference_range="< 5.7%", is_synthetic=True))
        db.add(LabResult(patient_id=patient.id, test_name="Fasting Blood Glucose", result=fasting_g, unit="mg/dL", measurement_date=d, reference_range="70 - 99 mg/dL", is_synthetic=True))
        db.add(LabResult(patient_id=patient.id, test_name="Total Cholesterol", result=cholesterol, unit="mg/dL", measurement_date=d, reference_range="< 200 mg/dL", is_synthetic=True))
        db.add(LabResult(patient_id=patient.id, test_name="HDL Cholesterol", result=hdl, unit="mg/dL", measurement_date=d, reference_range="> 50 mg/dL" if patient.gender == "Female" else "> 40 mg/dL", is_synthetic=True))
        db.add(LabResult(patient_id=patient.id, test_name="LDL Cholesterol", result=ldl, unit="mg/dL", measurement_date=d, reference_range="< 100 mg/dL", is_synthetic=True))
        db.add(LabResult(patient_id=patient.id, test_name="Triglycerides", result=trig, unit="mg/dL", measurement_date=d, reference_range="< 150 mg/dL", is_synthetic=True))


def seed_patient_genetics_if_missing(db: Session, patient: Patient):
    """Seed synthetic genetic susceptibility markers if not already present."""
    if db.query(GeneticMarker).filter(GeneticMarker.patient_id == patient.id).first() is not None:
        return
    markers = [
        {"marker_id": "rs7903146", "gene": "TCF7L2", "genotype": "CT (Heterozygous risk variant)" if "Type 2" in patient.diabetes_type else "CC (Ancestral allele)"},
        {"marker_id": "rs1801282", "gene": "PPARG", "genotype": "Pro12Ala (Protective variant)" if patient.diabetes_type == "Pre-diabetic" else "Pro12Pro (Wild-type)"},
        {"marker_id": "rs5219", "gene": "KCNJ11", "genotype": "EK (Heterozygous risk variant)" if "Type" in patient.diabetes_type else "EE (Homozygous normal)"},
        {"marker_id": "rs13266634", "gene": "SLC30A8", "genotype": "CC (Elevated beta-cell susceptibility)" if patient.diabetes_type == "Type 1" else "CT (Heterozygous)"},
        {"marker_id": "rs2237892", "gene": "KCNQ1", "genotype": "TT (Reduced insulin secretion allele)" if patient.age > 50 else "CC (Reference allele)"},
    ]
    rec_date = datetime(2025, 4, 15, 10, 0, 0)
    for m in markers:
        db.add(GeneticMarker(
            patient_id=patient.id,
            marker_id=m["marker_id"],
            gene=m["gene"],
            genotype=m["genotype"],
            recorded_at=rec_date,
            data_source="Simulated Illumina Global Screening Array",
            is_synthetic=True,
        ))


def seed_patient_sleep_if_missing(db: Session, patient: Patient, start_time: datetime, now: datetime):
    """Seed synthetic sleep architecture records across the 72-hour historical window if not present."""
    if db.query(SleepRecord).filter(SleepRecord.patient_id == patient.id).first() is not None:
        return
    cur_day = start_time.date()
    end_day = now.date()
    import datetime as dt_module

    stages_cycle = ["light", "deep", "light", "rem", "light", "deep", "rem", "light", "awake"]
    durations_cycle = [45.0, 60.0, 40.0, 50.0, 55.0, 65.0, 60.0, 85.0, 20.0]  # Sums to 480 mins (8h)

    while cur_day <= end_day:
        bedtime = datetime(cur_day.year, cur_day.month, cur_day.day, 23, 0, 0)
        t_cursor = bedtime
        for stage, duration in zip(stages_cycle, durations_cycle):
            t_end = t_cursor + timedelta(minutes=duration)
            if t_cursor <= now and t_cursor >= start_time:
                db.add(SleepRecord(
                    patient_id=patient.id,
                    start_time=t_cursor,
                    end_time=min(t_end, now),
                    stage=stage,
                    duration_minutes=duration,
                    is_synthetic=True,
                ))
            t_cursor = t_end
        cur_day += dt_module.timedelta(days=1)


def seed_patient_steps_if_missing(db: Session, patient: Patient, start_time: datetime, now: datetime):
    """Seed synthetic 15-minute interval steps and daily cumulative totals across 72h window."""
    if db.query(StepRecord).filter(StepRecord.patient_id == patient.id).first() is not None:
        return
    rng = np.random.default_rng(RANDOM_SEED + patient.id * 400)
    t_cursor = start_time
    cur_date = None
    cum_steps = 0

    while t_cursor <= now:
        if cur_date != t_cursor.date():
            cur_date = t_cursor.date()
            cum_steps = 0

        hour = t_cursor.hour
        if 23 <= hour or hour < 7:
            step_val = 0
        elif 7 <= hour < 9:
            step_val = int(rng.uniform(250, 750))
        elif 9 <= hour < 17:
            step_val = int(rng.uniform(60, 280)) if rng.random() > 0.25 else 0
        elif 17 <= hour < 20:
            step_val = int(rng.uniform(350, 950))
        else:
            step_val = int(rng.uniform(20, 120))

        cum_steps += step_val
        db.add(StepRecord(
            patient_id=patient.id,
            timestamp=t_cursor,
            interval_steps=step_val,
            daily_cumulative_steps=cum_steps,
            is_synthetic=True,
        ))
        t_cursor += timedelta(minutes=15)


def seed_database(db: Session) -> bool:
    """
    Populate the database with synthetic patients, 72 hours of readings,
    historical lab panels, genetic markers, sleep stages, and step counts.
    If patient records already exist, non-destructively supplements missing streams.

    Returns:
        bool: True if initial fresh seeding was performed, False otherwise.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    start_time = now - timedelta(hours=72)

    # Check if patients already exist
    existing_patients = db.query(Patient).all()
    if existing_patients:
        print("[INFO] Patients exist -- checking and non-destructively supplementing missing EHR/streams.")
        refresh_synthetic_telemetry(db)
        diagnoses_map = {p["name"]: p.get("historical_diagnoses", "None") for p in SYNTHETIC_PATIENTS}
        for p in existing_patients:
            if not getattr(p, "historical_diagnoses", None) or p.historical_diagnoses == "None":
                p.historical_diagnoses = diagnoses_map.get(p.name, "None")
            seed_patient_labs_if_missing(db, p, now)
            seed_patient_genetics_if_missing(db, p)
            seed_patient_sleep_if_missing(db, p, start_time, now)
            seed_patient_steps_if_missing(db, p, start_time, now)
        seed_users_if_missing(db)
        db.commit()
        return False

    print("[SEED] Seeding database with synthetic patient data ...")
    rng = np.random.default_rng(RANDOM_SEED)

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

        # Seed labs, genetics, sleep, and steps
        seed_patient_labs_if_missing(db, patient, now)
        seed_patient_genetics_if_missing(db, patient)
        seed_patient_sleep_if_missing(db, patient, start_time, now)
        seed_patient_steps_if_missing(db, patient, start_time, now)

        print(f"  [+] Patient {patient.id}: {patient.name} seeded with multimodal EHR & telemetry.")

    seed_users_if_missing(db)
    db.commit()
    print("[DONE] Seeding complete.")
    return True


def seed_users_if_missing(db: Session) -> None:
    """
    Seed initial demonstrator user accounts with securely hashed passwords.
    Only executed in development environments. NEVER in production.
    Accounts:
      - 'dr_sharma' (clinician)
      - 'rajesh_kumar' (patient #2)
      - 'ananya_sharma' (patient #1)
    """
    env = os.environ.get("ENVIRONMENT", "development").strip().lower()
    if env in ("production", "prod"):
        print("[INFO] Production environment: demonstrator user account seeding is disabled.")
        return
    demo_users = [
        {
            "username": "dr_sharma",
            "email": "dr.sharma@glucotwin.hospital",
            "role": "clinician",
            "patient_id": None,
            "password": "Clinician123!",
        },
        {
            "username": "rajesh_kumar",
            "email": "rajesh.kumar@example.com",
            "role": "patient",
            "patient_id": 2,
            "password": "Patient123!",
        },
        {
            "username": "ananya_sharma",
            "email": "ananya.sharma@example.com",
            "role": "patient",
            "patient_id": 1,
            "password": "Patient123!",
        },
    ]

    for u_spec in demo_users:
        existing = db.query(User).filter(User.username == u_spec["username"]).first()
        if not existing:
            # Check if patient exists if patient_id is specified
            p_id = u_spec["patient_id"]
            if p_id is not None:
                p_exists = db.query(Patient).filter(Patient.id == p_id).first()
                if not p_exists:
                    p_id = None

            hashed_pw = get_password_hash(u_spec["password"])
            user = User(
                username=u_spec["username"],
                email=u_spec["email"],
                hashed_password=hashed_pw,
                role=u_spec["role"],
                patient_id=p_id,
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            db.add(user)
            print(f"  [+] Seeded demonstrator user: '{u_spec['username']}' (role: {u_spec['role']})")
