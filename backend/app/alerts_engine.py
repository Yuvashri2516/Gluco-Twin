"""
alerts_engine.py - GlucoTwin Alert Engine (Phase 5)
===================================================

Provides a rule-based & model-driven alert evaluation engine that:
1. Detects OBSERVED-READING ALERTS from actual stored synthetic telemetry.
2. Detects MODEL-PREDICTED ALERTS from the experimental ML glucose-spike model.
3. Distinguishes observed vs predicted alerts clearly.
4. Employs a deterministic deduplication strategy using `dedup_key`.
5. Exposes explicit demonstration thresholds without representing them as clinical guidelines.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
import os
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import Patient, GlucoseReading, VitalReading, Alert
from app.ml.pipeline import (
    load_model_artifact,
    extract_features_at_timestamp,
    FEATURE_NAMES,
)

# ---------------------------------------------------------------------------
# DEMONSTRATION THRESHOLDS
# RESEARCH DEMO ONLY - THESE DO NOT CONSTITUTE MEDICAL OR CLINICAL GUIDELINES
# ---------------------------------------------------------------------------
DEMO_THRESHOLDS = {
    "glucose_severe_hypo": 54.0,       # mg/dL (Demonstration threshold for severe hypoglycemia)
    "glucose_hypo": 70.0,              # mg/dL (Demonstration threshold for low glucose)
    "glucose_hyper": 180.0,            # mg/dL (Demonstration threshold for Level 1 hyperglycemia)
    "glucose_severe_hyper": 250.0,     # mg/dL (Demonstration threshold for Level 2 hyperglycemia)
    "vital_elevated_hr": 100.0,        # bpm (Demonstration tachycardia threshold)
    "vital_depressed_hrv": 25.0,       # ms (Demonstration depressed autonomic HRV)
    "pred_risk_high": 0.65,            # Uncalibrated score threshold for high predicted spike risk
    "pred_risk_mod": 0.50,             # Uncalibrated score threshold for moderate predicted spike risk
}

# Path to model artifact directory
ML_ARTIFACT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "ml",
    "artifacts"
)


def ensure_alert_columns(engine) -> None:
    """
    Ensure the SQLite `alerts` table contains all Phase 5 columns.
    Safe and non-destructive.
    """
    with engine.connect() as conn:
        try:
            res = conn.execute(text("PRAGMA table_info(alerts)")).fetchall()
            existing_cols = {row[1] for row in res}
            columns_to_add = [
                ("alert_type", "VARCHAR(50)"),
                ("source", "VARCHAR(30) DEFAULT 'observed_reading'"),
                ("status", "VARCHAR(20) DEFAULT 'active'"),
                ("trigger_value", "FLOAT"),
                ("threshold", "FLOAT"),
                ("resolved_at", "DATETIME"),
                ("dedup_key", "VARCHAR(120)"),
            ]
            for col_name, col_def in columns_to_add:
                if col_name not in existing_cols:
                    conn.execute(text(f"ALTER TABLE alerts ADD COLUMN {col_name} {col_def}"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_alerts_dedup_key ON alerts (dedup_key) WHERE dedup_key IS NOT NULL"))
            conn.commit()
        except Exception:
            pass


def evaluate_observed_reading_alerts(
    db: Session,
    patient: Patient,
    hours: int = 24,
) -> List[Alert]:
    """
    Evaluate actual stored synthetic readings against demonstration thresholds.
    Deduplicates using `obs:{patient_id}:{alert_type}:{reading_id}`.
    """
    latest_r = (
        db.query(GlucoseReading)
        .filter(GlucoseReading.patient_id == patient.id, GlucoseReading.is_valid == True)
        .order_by(GlucoseReading.timestamp.desc())
        .first()
    )

    new_alerts: List[Alert] = []

    # Check for DATA_MISSING category if no readings exist
    if not latest_r:
        dedup_key = f"obs:{patient.id}:data_missing:no_readings"
        existing = db.query(Alert).filter(Alert.dedup_key == dedup_key).first()
        if not existing:
            alert = Alert(
                patient_id=patient.id,
                timestamp=datetime.now(timezone.utc),
                severity="info",
                message="Data Missing: System lacks recorded sensor telemetry for this synthetic patient.",
                alert_type="data_missing",
                source="observed_reading",
                status="active",
                trigger_value=0.0,
                threshold=1.0,
                acknowledged=False,
                dedup_key=dedup_key,
            )
            db.add(alert)
            new_alerts.append(alert)
        return new_alerts

    ref_time = latest_r.timestamp
    cutoff = ref_time - timedelta(hours=hours)

    # Check for DATA_STALE category if latest reading is older than 24h
    now_utc_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    hours_diff = (now_utc_naive - latest_r.timestamp).total_seconds() / 3600.0
    if hours_diff > 24.0:
        day_slug = latest_r.timestamp.strftime("%Y%m%d")
        dedup_key = f"obs:{patient.id}:data_stale:{day_slug}"
        existing = db.query(Alert).filter(Alert.dedup_key == dedup_key).first()
        if not existing:
            alert = Alert(
                patient_id=patient.id,
                timestamp=latest_r.timestamp if latest_r.timestamp.tzinfo else latest_r.timestamp.replace(tzinfo=timezone.utc),
                severity="warning",
                message=f"Data Stale: Stored telemetry is older than the 24-hour freshness window ({hours_diff:.1f} hours elapsed).",
                alert_type="data_stale",
                source="observed_reading",
                status="active",
                trigger_value=round(hours_diff, 1),
                threshold=24.0,
                acknowledged=False,
                dedup_key=dedup_key,
            )
            db.add(alert)
            new_alerts.append(alert)

    glucose_records = (
        db.query(GlucoseReading)
        .filter(
            GlucoseReading.patient_id == patient.id,
            GlucoseReading.is_valid == True,
            GlucoseReading.timestamp >= cutoff,
            GlucoseReading.timestamp <= ref_time,
        )
        .order_by(GlucoseReading.timestamp.asc())
        .all()
    )

    vital_records = (
        db.query(VitalReading)
        .filter(
            VitalReading.patient_id == patient.id,
            VitalReading.timestamp >= cutoff,
            VitalReading.timestamp <= ref_time,
        )
        .order_by(VitalReading.timestamp.asc())
        .all()
    )

    # 1. Glucose Threshold Alerts
    for r in glucose_records:
        val = float(r.value)
        alert_info: Optional[Tuple[str, str, float, str]] = None

        if val < DEMO_THRESHOLDS["glucose_severe_hypo"]:
            alert_info = (
                "observed_severe_hypoglycemia",
                "critical",
                DEMO_THRESHOLDS["glucose_severe_hypo"],
                f"Severe hypoglycemia reading: {val:.1f} mg/dL is below critical demonstration threshold (< {DEMO_THRESHOLDS['glucose_severe_hypo']} mg/dL)."
            )
        elif val < DEMO_THRESHOLDS["glucose_hypo"]:
            alert_info = (
                "observed_hypoglycemia",
                "warning",
                DEMO_THRESHOLDS["glucose_hypo"],
                f"Low glucose reading: {val:.1f} mg/dL is below demonstration threshold (< {DEMO_THRESHOLDS['glucose_hypo']} mg/dL)."
            )
        elif val >= DEMO_THRESHOLDS["glucose_severe_hyper"]:
            alert_info = (
                "observed_severe_hyperglycemia",
                "critical",
                DEMO_THRESHOLDS["glucose_severe_hyper"],
                f"Severe hyperglycemia reading: {val:.1f} mg/dL breached high demonstration threshold (≥ {DEMO_THRESHOLDS['glucose_severe_hyper']} mg/dL)."
            )
        elif val >= DEMO_THRESHOLDS["glucose_hyper"]:
            alert_info = (
                "observed_hyperglycemia",
                "warning",
                DEMO_THRESHOLDS["glucose_hyper"],
                f"Hyperglycemia reading: {val:.1f} mg/dL crossed demonstration threshold (≥ {DEMO_THRESHOLDS['glucose_hyper']} mg/dL)."
            )

        if alert_info:
            atype, severity, thresh, msg = alert_info
            dedup_key = f"obs:{patient.id}:{atype}:{r.id}"

            # Check if alert with this dedup_key already exists
            existing = db.query(Alert).filter(Alert.dedup_key == dedup_key).first()
            if not existing:
                alert = Alert(
                    patient_id=patient.id,
                    timestamp=r.timestamp if r.timestamp.tzinfo else r.timestamp.replace(tzinfo=timezone.utc),
                    severity=severity,
                    message=msg,
                    alert_type=atype,
                    source="observed_reading",
                    status="active",
                    trigger_value=round(val, 2),
                    threshold=thresh,
                    acknowledged=False,
                    dedup_key=dedup_key,
                )
                db.add(alert)
                new_alerts.append(alert)

    # 2. Vital Signs Autonomic Alerts
    for v in vital_records:
        hr = float(v.heart_rate) if v.heart_rate is not None else None
        hrv = float(v.hrv) if v.hrv is not None else None

        if hr and hrv and hr >= DEMO_THRESHOLDS["vital_elevated_hr"] and hrv <= DEMO_THRESHOLDS["vital_depressed_hrv"]:
            dedup_key = f"obs:{patient.id}:autonomic:{v.id}"
            existing = db.query(Alert).filter(Alert.dedup_key == dedup_key).first()
            if not existing:
                alert = Alert(
                    patient_id=patient.id,
                    timestamp=v.timestamp if v.timestamp.tzinfo else v.timestamp.replace(tzinfo=timezone.utc),
                    severity="warning",
                    message=(
                        f"Autonomic coupling alert: Tachycardia ({hr:.0f} bpm ≥ {DEMO_THRESHOLDS['vital_elevated_hr']} bpm) "
                        f"with depressed HRV ({hrv:.1f} ms ≤ {DEMO_THRESHOLDS['vital_depressed_hrv']} ms)."
                    ),
                    alert_type="observed_autonomic_depression",
                    source="observed_reading",
                    status="active",
                    trigger_value=round(hr, 1),
                    threshold=DEMO_THRESHOLDS["vital_elevated_hr"],
                    acknowledged=False,
                    dedup_key=dedup_key,
                )
                db.add(alert)
                new_alerts.append(alert)

    return new_alerts


def evaluate_model_predicted_alerts(
    db: Session,
    patient: Patient,
) -> List[Alert]:
    """
    Evaluate experimental ML glucose-spike prediction for the patient.
    Generates a predicted alert if the model predicts a spike.
    Deduplicates using `pred:{patient_id}:{timestamp_str}`.
    """
    new_alerts: List[Alert] = []
    try:
        # 1. Load model artifact
        pipeline, metadata = load_model_artifact(ML_ARTIFACT_DIR)
        if pipeline is None or metadata is None:
            return new_alerts

        # 2. Latest glucose reading
        latest_r = (
            db.query(GlucoseReading)
            .filter(GlucoseReading.patient_id == patient.id, GlucoseReading.is_valid == True)
            .order_by(GlucoseReading.timestamp.desc())
            .first()
        )
        if not latest_r:
            return new_alerts

        prediction_time = latest_r.timestamp
        if prediction_time.tzinfo is None:
            prediction_time = prediction_time.replace(tzinfo=timezone.utc)

        # 3. Fetch history up to prediction_time
        pred_time_naive = prediction_time.replace(tzinfo=None)
        glucose_records = (
            db.query(GlucoseReading)
            .filter(
                GlucoseReading.patient_id == patient.id,
                GlucoseReading.is_valid == True,
                GlucoseReading.timestamp <= pred_time_naive,
            )
            .order_by(GlucoseReading.timestamp.asc())
            .all()
        )
        vital_records = (
            db.query(VitalReading)
            .filter(
                VitalReading.patient_id == patient.id,
                VitalReading.timestamp <= pred_time_naive,
            )
            .order_by(VitalReading.timestamp.asc())
            .all()
        )

        patient_dict = {
            "id": patient.id,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "diabetes_type": patient.diabetes_type,
            "years_since_diagnosis": patient.years_since_diagnosis,
        }

        glucose_dicts = [{"id": r.id, "timestamp": r.timestamp, "value": r.value} for r in glucose_records]
        vital_dicts = [{"id": r.id, "timestamp": r.timestamp, "heart_rate": r.heart_rate, "hrv": r.hrv} for r in vital_records]

        features, warnings = extract_features_at_timestamp(
            patient_info=patient_dict,
            glucose_readings=glucose_dicts,
            vital_readings=vital_dicts,
            prediction_time=prediction_time,
        )
        if features is None:
            return new_alerts

        # 4. Model inference
        X_df = pd.DataFrame([[features[k] for k in FEATURE_NAMES]], columns=FEATURE_NAMES)
        scaler = pipeline.named_steps["scaler"]
        model = pipeline.named_steps["model"]
        X_scaled = scaler.transform(X_df)
        prob = float(model.predict_proba(X_scaled)[0, 1])

        # If predicted probability indicates a spike
        if prob >= DEMO_THRESHOLDS["pred_risk_mod"]:
            severity = "critical" if prob >= DEMO_THRESHOLDS["pred_risk_high"] else "warning"
            tier = "HIGH" if prob >= DEMO_THRESHOLDS["pred_risk_high"] else "MODERATE"

            # Unique dedup key per patient and minute of prediction timestamp
            time_slug = prediction_time.strftime("%Y%m%d%H%M")
            dedup_key = f"pred:{patient.id}:{time_slug}"

            existing = db.query(Alert).filter(Alert.dedup_key == dedup_key).first()
            if not existing:
                alert = Alert(
                    patient_id=patient.id,
                    timestamp=prediction_time,
                    severity=severity,
                    message=(
                        f"Predicted Spike Alert: Experimental model forecasts glucose breach "
                        f"(≥ 180 mg/dL within 2 hours) with uncalibrated score of {prob:.4f} ({tier} tier)."
                    ),
                    alert_type="predicted_glucose_spike",
                    source="experimental_prediction",
                    status="active",
                    trigger_value=round(prob, 4),
                    threshold=DEMO_THRESHOLDS["pred_risk_mod"],
                    acknowledged=False,
                    dedup_key=dedup_key,
                )
                db.add(alert)
                new_alerts.append(alert)
    except Exception:
        # Prediction failure must not crash alert evaluation
        return new_alerts

    return new_alerts


def evaluate_all_alerts_for_patient(db: Session, patient: Patient) -> List[Alert]:
    """
    Run full evaluation for a patient: observed reading alerts + model predicted alerts.
    Commits newly created alerts to the DB safely against concurrent requests.
    """
    created_observed = evaluate_observed_reading_alerts(db, patient)
    created_predicted = []
    try:
        created_predicted = evaluate_model_predicted_alerts(db, patient)
    except Exception:
        created_predicted = []

    all_created = created_observed + created_predicted
    if all_created:
        try:
            db.commit()
            for a in all_created:
                db.refresh(a)
        except Exception:
            db.rollback()
            return []
    return all_created
