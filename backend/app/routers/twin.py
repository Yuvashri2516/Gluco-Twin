"""
routers/twin.py - Patient Digital Twin Intelligence & What-If Simulation (Phase 5)
==================================================================================

Provides:
  GET   /api/digital-twin/{patient_id}  -> full computed digital twin intelligence summary
  POST  /api/simulation/what-if         -> deterministic illustrative scenario calculator
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List
import math
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Patient, GlucoseReading, VitalReading, Alert
from app.schemas import (
    DigitalTwinDetailResponse,
    WhatIfSimulationRequest,
    WhatIfSimulationResponse,
    AlertRead,
)
from app.alerts_engine import evaluate_all_alerts_for_patient
from app.ml.pipeline import (
    load_model_artifact,
    extract_features_at_timestamp,
    FEATURE_NAMES,
)

router = APIRouter(prefix="", tags=["Digital Twin & Simulation"])


@router.get("/api/digital-twin/{patient_id}", response_model=DigitalTwinDetailResponse)
def get_digital_twin_intelligence(
    patient_id: int,
    db: Session = Depends(get_db),
):
    """
    Compute and return a patient-specific digital twin intelligence summary
    using real stored synthetic telemetry, historical trends, data quality warnings,
    recent alerts, and experimental prediction output.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{patient_id} not found.")

    # Calculate BMI
    bmi = None
    if patient.weight_kg and patient.height_cm:
        height_m = patient.height_cm / 100.0
        bmi = round(patient.weight_kg / (height_m * height_m), 1)

    # Fetch latest readings
    latest_g = (
        db.query(GlucoseReading)
        .filter(GlucoseReading.patient_id == patient.id, GlucoseReading.is_valid == True)
        .order_by(GlucoseReading.timestamp.desc())
        .first()
    )
    latest_v = (
        db.query(VitalReading)
        .filter(VitalReading.patient_id == patient.id)
        .order_by(VitalReading.timestamp.desc())
        .first()
    )

    # Anchor monitoring window relative to latest reading timestamp or current time
    ref_time = latest_g.timestamp if latest_g else datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff_24h = ref_time - timedelta(hours=24)
    cutoff_1h = ref_time - timedelta(hours=1)

    glucose_records_24h = (
        db.query(GlucoseReading)
        .filter(
            GlucoseReading.patient_id == patient.id,
            GlucoseReading.is_valid == True,
            GlucoseReading.timestamp >= cutoff_24h,
            GlucoseReading.timestamp <= ref_time,
        )
        .order_by(GlucoseReading.timestamp.asc())
        .all()
    )

    vital_records_24h = (
        db.query(VitalReading)
        .filter(
            VitalReading.patient_id == patient.id,
            VitalReading.timestamp >= cutoff_24h,
            VitalReading.timestamp <= ref_time,
        )
        .order_by(VitalReading.timestamp.asc())
        .all()
    )

    # 1h subset
    glucose_records_1h = [r for r in glucose_records_24h if r.timestamp >= cutoff_1h]
    vital_records_1h = [r for r in vital_records_24h if r.timestamp >= cutoff_1h]

    # Metrics
    mean_glucose_24h = (
        round(float(np.mean([r.value for r in glucose_records_24h])), 1)
        if glucose_records_24h else None
    )

    mean_glucose_1h = None
    glucose_std_1h = None
    glucose_trend_slope = None

    data_quality_warnings = []

    if glucose_records_1h:
        vals_1h = [r.value for r in glucose_records_1h]
        mean_glucose_1h = round(float(np.mean(vals_1h)), 1)
        if len(vals_1h) > 1:
            glucose_std_1h = round(float(np.std(vals_1h, ddof=1)), 2)
            # Slope in mg/dL per minute
            t_span_min = (glucose_records_1h[-1].timestamp - glucose_records_1h[0].timestamp).total_seconds() / 60.0
            if t_span_min > 0:
                glucose_trend_slope = round((vals_1h[-1] - vals_1h[0]) / t_span_min, 4)
        else:
            glucose_std_1h = 0.0
            glucose_trend_slope = 0.0

    if len(glucose_records_1h) < 2:
        data_quality_warnings.append("Sparse glucose telemetry in the most recent 1-hour monitoring window.")

    if not vital_records_1h:
        data_quality_warnings.append("No autonomic vital readings (HR/HRV) in the past 1 hour.")

    mean_hr_1h = (
        round(float(np.mean([v.heart_rate for v in vital_records_1h if v.heart_rate is not None])), 1)
        if any(v.heart_rate is not None for v in vital_records_1h) else None
    )
    mean_hrv_1h = (
        round(float(np.mean([v.hrv for v in vital_records_1h if v.hrv is not None])), 1)
        if any(v.hrv is not None for v in vital_records_1h) else None
    )

    # Active alerts & recent alerts
    recent_alerts_orm = (
        db.query(Alert)
        .filter(Alert.patient_id == patient.id)
        .order_by(Alert.timestamp.desc())
        .limit(5)
        .all()
    )
    active_alerts_count = (
        db.query(Alert)
        .filter(Alert.patient_id == patient.id, Alert.status == "active")
        .count()
    )

    recent_alerts = [
        AlertRead(
            id=a.id,
            patient_id=a.patient_id,
            patient_name=patient.name,
            timestamp=a.timestamp,
            severity=a.severity,
            message=a.message,
            alert_type=a.alert_type,
            source=a.source or "observed_reading",
            status=a.status or ("acknowledged" if a.acknowledged else "active"),
            trigger_value=a.trigger_value,
            threshold=a.threshold,
            acknowledged=bool(a.acknowledged),
            acknowledged_at=a.acknowledged_at,
            resolved_at=a.resolved_at,
            dedup_key=a.dedup_key,
        )
        for a in recent_alerts_orm
    ]

    # Optional experimental prediction snapshot
    latest_prediction = None
    try:
        from app.routers.predictions import ML_ARTIFACT_DIR
        pipeline, metadata = load_model_artifact(ML_ARTIFACT_DIR)
        if pipeline and latest_g:
            pred_time = latest_g.timestamp
            if pred_time.tzinfo is None:
                pred_time = pred_time.replace(tzinfo=timezone.utc)
            patient_dict = {
                "id": patient.id,
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender,
                "diabetes_type": patient.diabetes_type,
                "years_since_diagnosis": patient.years_since_diagnosis,
            }
            g_dicts = [{"id": r.id, "timestamp": r.timestamp, "value": r.value} for r in glucose_records_24h]
            v_dicts = [{"id": r.id, "timestamp": r.timestamp, "heart_rate": r.heart_rate, "hrv": r.hrv} for r in vital_records_24h]
            features, _ = extract_features_at_timestamp(
                patient_info=patient_dict,
                glucose_readings=g_dicts,
                vital_readings=v_dicts,
                prediction_time=pred_time,
            )
            if features:
                import pandas as pd
                X_df = pd.DataFrame([[features[k] for k in FEATURE_NAMES]], columns=FEATURE_NAMES)
                X_scaled = pipeline.named_steps["scaler"].transform(X_df)
                prob = float(pipeline.named_steps["model"].predict_proba(X_scaled)[0, 1])
                latest_prediction = {
                    "risk_score": round(prob, 4),
                    "spike_predicted": bool(prob >= 0.5),
                    "risk_category": "HIGH" if prob >= 0.65 else ("MODERATE" if prob >= 0.35 else "LOW"),
                    "model_version": metadata.get("model_version", "0.1.0-prototype"),
                }
    except Exception:
        latest_prediction = None

    return DigitalTwinDetailResponse(
        patient_id=patient.id,
        patient_name=patient.name,
        diabetes_type=patient.diabetes_type,
        age=patient.age,
        gender=patient.gender,
        years_since_diagnosis=patient.years_since_diagnosis,
        weight_kg=patient.weight_kg,
        height_cm=patient.height_cm,
        bmi=bmi,
        latest_glucose=latest_g.value if latest_g else None,
        latest_glucose_timestamp=latest_g.timestamp if latest_g else None,
        latest_heart_rate=latest_v.heart_rate if latest_v else None,
        latest_hrv=latest_v.hrv if latest_v else None,
        mean_glucose_1h=mean_glucose_1h,
        mean_glucose_24h=mean_glucose_24h,
        glucose_std_1h=glucose_std_1h,
        glucose_trend_slope=glucose_trend_slope,
        mean_hr_1h=mean_hr_1h,
        mean_hrv_1h=mean_hrv_1h,
        data_quality_warnings=data_quality_warnings,
        total_readings_24h=len(glucose_records_24h),
        active_alerts_count=active_alerts_count,
        recent_alerts=recent_alerts,
        latest_prediction=latest_prediction,
        disclaimer=(
            "RESEARCH PROTOTYPE ONLY: Built on synthetic telemetry. "
            "Not clinically validated. Not for diagnosis or treatment decisions."
        ),
    )


@router.post("/api/simulation/what-if", response_model=WhatIfSimulationResponse)
def run_what_if_simulation(
    request: WhatIfSimulationRequest,
    db: Session = Depends(get_db),
):
    """
    Deterministic illustrative scenario calculator:
    Simulates hypothetical meal carbohydrate and physical activity perturbations
    against patient baseline glucose using documented, software-only assumptions.
    """
    patient = db.query(Patient).filter(Patient.id == request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{request.patient_id} not found.")

    # Determine baseline glucose
    baseline_g = request.as_of_glucose
    if baseline_g is None:
        latest_r = (
            db.query(GlucoseReading)
            .filter(GlucoseReading.patient_id == patient.id, GlucoseReading.is_valid == True)
            .order_by(GlucoseReading.timestamp.desc())
            .first()
        )
        baseline_g = float(latest_r.value) if latest_r else 120.0

    # Bounded inputs
    carbs = max(0.0, min(150.0, float(request.additional_carbs_g)))
    activity_mins = max(0.0, min(180.0, float(request.activity_minutes)))

    # Documented physiological heuristic parameters:
    # Body weight adjustment factor (default 70kg if unspecified)
    weight = patient.weight_kg if patient.weight_kg and patient.weight_kg > 30 else 70.0
    weight_factor = 70.0 / weight

    # Type-specific insulin sensitivity scalar
    type_scalars = {
        "Type 1": 1.30,       # Lower endogenous insulin buffer
        "Type 2": 1.15,       # Insulin resistance
        "Pre-diabetic": 0.90, # Mild impairment
    }
    k_type = type_scalars.get(patient.diabetes_type, 1.0)

    # Carb impact: ~4.0 mg/dL per 10g carbs adjusted by weight and clinical type
    carb_impact = carbs * (0.40 * weight_factor * k_type)

    # Activity impact: ~0.75 mg/dL drop per minute of light/moderate physical exertion
    activity_impact = -(activity_mins * 0.75)

    # Net scenario projection
    scenario_g = round(max(40.0, baseline_g + carb_impact + activity_impact), 1)
    is_spike_breach = bool(scenario_g >= 180.0)

    assumptions = [
        "Linear carbohydrate glycemic index model (assuming rapid postprandial absorption without delayed gastric emptying).",
        f"Weight-scaled volume of distribution: reference 70kg, patient scale {weight:.1f}kg.",
        f"Clinical sensitivity modifier applied: {k_type:.2f}x for {patient.diabetes_type}.",
        "Uniform moderate physical exertion (approx. 0.75 mg/dL glycemic clearance per minute of activity).",
        "Assumes stable baseline basal insulin coverage without additional bolus compensation.",
    ]

    return WhatIfSimulationResponse(
        patient_id=patient.id,
        patient_name=patient.name,
        baseline_glucose=round(baseline_g, 1),
        additional_carbs_g=carbs,
        activity_minutes=activity_mins,
        projected_carb_impact_mg_dl=round(carb_impact, 1),
        projected_activity_impact_mg_dl=round(activity_impact, 1),
        projected_scenario_glucose=scenario_g,
        projected_spike_risk_breach=is_spike_breach,
        spike_threshold_mg_dl=180.0,
        assumptions=assumptions,
        disclaimer=(
            "SIMULATED — NOT A CLINICAL PREDICTION. "
            "Illustrative academic scenario calculator only. "
            "Do not use for insulin dosing, dietary prescriptions, or medical decisions."
        ),
    )
