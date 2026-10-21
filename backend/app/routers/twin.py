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
from app.models import Patient, GlucoseReading, VitalReading, Alert, SleepRecord, StepRecord, User
from app.auth import get_current_user, check_patient_authorization
from app.schemas import (
    DigitalTwinDetailResponse,
    WhatIfSimulationRequest,
    WhatIfSimulationResponse,
    AlertRead,
    SimulatedSensorFeedRequest,
    SimulatedSensorFeedResponse,
    GlucoseReadingRead,
    VitalReadingRead,
    StepRecordRead,
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
    current_user: User = Depends(get_current_user),
):
    """
    Compute and return a patient-specific digital twin intelligence summary
    using real stored synthetic telemetry, historical trends, data quality warnings,
    recent alerts, and experimental prediction output.
    """
    check_patient_authorization(patient_id, current_user, db)

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
    min_glucose_24h = (
        round(float(np.min([r.value for r in glucose_records_24h])), 1)
        if glucose_records_24h else None
    )
    max_glucose_24h = (
        round(float(np.max([r.value for r in glucose_records_24h])), 1)
        if glucose_records_24h else None
    )

    mean_glucose_1h = None
    min_glucose_1h = None
    max_glucose_1h = None
    glucose_change_1h = None
    glucose_std_1h = None
    glucose_trend_slope = None

    data_quality_warnings = []

    if glucose_records_1h:
        vals_1h = [r.value for r in glucose_records_1h]
        mean_glucose_1h = round(float(np.mean(vals_1h)), 1)
        min_glucose_1h = round(float(np.min(vals_1h)), 1)
        max_glucose_1h = round(float(np.max(vals_1h)), 1)
        if len(vals_1h) > 1:
            glucose_change_1h = round(float(vals_1h[-1] - vals_1h[0]), 1)
            glucose_std_1h = round(float(np.std(vals_1h, ddof=1)), 2)
            # Slope in mg/dL per minute
            t_span_min = (glucose_records_1h[-1].timestamp - glucose_records_1h[0].timestamp).total_seconds() / 60.0
            if t_span_min > 0:
                glucose_trend_slope = round((vals_1h[-1] - vals_1h[0]) / t_span_min, 4)
        else:
            glucose_change_1h = 0.0
            glucose_std_1h = 0.0
            glucose_trend_slope = 0.0

    # Freshness evaluation
    if not latest_g:
        data_freshness_status = "no_data"
        hours_since_last_reading = None
        data_quality_warnings.append("No recorded glucose telemetry for this synthetic patient.")
    else:
        now_utc_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        hours_diff = (now_utc_naive - latest_g.timestamp).total_seconds() / 3600.0
        hours_since_last_reading = round(max(0.0, hours_diff), 1)
        if hours_since_last_reading > 2.0:
            data_freshness_status = "stale"
            data_quality_warnings.append(
                f"Telemetry is stale: latest reading was recorded {hours_since_last_reading} hours ago."
            )
        else:
            data_freshness_status = "fresh"

    if latest_g and len(glucose_records_1h) < 2:
        data_quality_warnings.append("Sparse glucose telemetry in the most recent 1-hour monitoring window.")

    if latest_g and not vital_records_1h:
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
        .limit(10)
        .all()
    )
    active_alerts_count = (
        db.query(Alert)
        .filter(Alert.patient_id == patient.id, Alert.status == "active")
        .count()
    )
    acknowledged_alerts_count = (
        db.query(Alert)
        .filter(Alert.patient_id == patient.id, Alert.status == "acknowledged")
        .count()
    )
    resolved_alerts_count = (
        db.query(Alert)
        .filter(Alert.patient_id == patient.id, Alert.status == "resolved")
        .count()
    )
    alert_severity_distribution = {
        "critical": db.query(Alert).filter(Alert.patient_id == patient.id, Alert.severity == "critical").count(),
        "warning": db.query(Alert).filter(Alert.patient_id == patient.id, Alert.severity == "warning").count(),
        "info": db.query(Alert).filter(Alert.patient_id == patient.id, Alert.severity == "info").count(),
    }

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
    most_recent_alert = recent_alerts[0] if recent_alerts else None

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
                    "prediction_timestamp": pred_time.isoformat(),
                    "prediction_horizon_minutes": 120,
                    "is_uncalibrated_experimental": True,
                    "clinical_disclaimer": "Uncalibrated prototype score; not a validated clinical probability.",
                }
    except Exception:
        latest_prediction = None

    # Fetch latest sleep records & step records for twin context
    latest_sleep = (
        db.query(SleepRecord)
        .filter(SleepRecord.patient_id == patient.id)
        .order_by(SleepRecord.end_time.desc())
        .first()
    )
    latest_step = (
        db.query(StepRecord)
        .filter(StepRecord.patient_id == patient.id)
        .order_by(StepRecord.timestamp.desc())
        .first()
    )

    sleep_summary = None
    if latest_sleep:
        sleep_records_24h = (
            db.query(SleepRecord)
            .filter(
                SleepRecord.patient_id == patient.id,
                SleepRecord.end_time >= cutoff_24h,
            )
            .all()
        )
        total_sleep_m = sum(r.duration_minutes for r in sleep_records_24h if r.stage in ("light", "deep", "rem"))
        sleep_summary = {
            "total_sleep_hours": round(total_sleep_m / 60.0, 1),
            "stages_recorded": len(sleep_records_24h),
            "latest_stage": latest_sleep.stage,
        }

    step_summary = None
    if latest_step:
        step_records_24h = (
            db.query(StepRecord)
            .filter(
                StepRecord.patient_id == patient.id,
                StepRecord.timestamp >= cutoff_24h,
            )
            .all()
        )
        total_steps = sum(r.interval_steps for r in step_records_24h)
        step_summary = {
            "total_steps_24h": total_steps,
            "latest_interval_steps": latest_step.interval_steps,
            "daily_cumulative_steps": latest_step.daily_cumulative_steps,
        }

    return DigitalTwinDetailResponse(
        patient_id=patient.id,
        patient_name=patient.name,
        diabetes_type=patient.diabetes_type,
        age=patient.age,
        gender=patient.gender,
        years_since_diagnosis=patient.years_since_diagnosis,
        historical_diagnoses=getattr(patient, "historical_diagnoses", "None") or "None",
        weight_kg=patient.weight_kg,
        height_cm=patient.height_cm,
        bmi=bmi,
        latest_glucose=latest_g.value if latest_g else None,
        latest_glucose_timestamp=latest_g.timestamp if latest_g else None,
        latest_heart_rate=latest_v.heart_rate if latest_v else None,
        latest_hrv=latest_v.hrv if latest_v else None,
        latest_vital_timestamp=latest_v.timestamp if latest_v else None,
        mean_glucose_1h=mean_glucose_1h,
        mean_glucose_24h=mean_glucose_24h,
        min_glucose_24h=min_glucose_24h,
        max_glucose_24h=max_glucose_24h,
        min_glucose_1h=min_glucose_1h,
        max_glucose_1h=max_glucose_1h,
        glucose_change_1h=glucose_change_1h,
        glucose_std_1h=glucose_std_1h,
        glucose_trend_slope=glucose_trend_slope,
        mean_hr_1h=mean_hr_1h,
        mean_hrv_1h=mean_hrv_1h,
        latest_sleep_summary=sleep_summary,
        latest_step_summary=step_summary,
        data_freshness_status=data_freshness_status,
        hours_since_last_reading=hours_since_last_reading,
        data_quality_warnings=data_quality_warnings,
        total_readings_24h=len(glucose_records_24h),
        total_vital_readings_24h=len(vital_records_24h),
        active_alerts_count=active_alerts_count,
        acknowledged_alerts_count=acknowledged_alerts_count,
        resolved_alerts_count=resolved_alerts_count,
        alert_severity_distribution=alert_severity_distribution,
        most_recent_alert=most_recent_alert,
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Deterministic illustrative scenario calculator:
    Simulates hypothetical meal carbohydrate and physical activity perturbations
    against patient baseline glucose using documented, software-only assumptions.
    """
    check_patient_authorization(request.patient_id, current_user, db)

    patient = db.query(Patient).filter(Patient.id == request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{request.patient_id} not found.")

    sim_warnings: List[str] = []

    # Determine baseline glucose
    baseline_g = request.as_of_glucose
    if baseline_g is None:
        latest_r = (
            db.query(GlucoseReading)
            .filter(GlucoseReading.patient_id == patient.id, GlucoseReading.is_valid == True)
            .order_by(GlucoseReading.timestamp.desc())
            .first()
        )
        if latest_r:
            baseline_g = float(latest_r.value)
        else:
            baseline_g = 110.0
            sim_warnings.append(
                "Patient has no recorded glucose readings; using standard simulated baseline of 110.0 mg/dL."
            )

    # Inputs bounded by schema validation
    carbs = float(request.additional_carbs_g)
    activity_mins = float(request.activity_minutes)

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
        formula_version="1.0.0-illustrative-heuristic",
        data_quality_warnings=sim_warnings,
        assumptions=assumptions,
        disclaimer=(
            "SIMULATED — NOT A CLINICAL PREDICTION. "
            "Illustrative academic scenario calculator only. "
            "Do not use for insulin dosing, dietary prescriptions, or medical decisions."
        ),
    )


@router.post("/api/digital-twin/simulate-feed", response_model=SimulatedSensorFeedResponse)
def simulate_sensor_feed(
    request: SimulatedSensorFeedRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Demonstrable controlled synthetic sensor-update workflow:
    Advances the selected patient's telemetry by a 15-minute sensor epoch.
    Generates new glucose, heart rate, HRV, and step readings, persists them safely,
    re-evaluates alerts, and computes updated digital twin intelligence.
    """
    check_patient_authorization(request.patient_id, current_user, db)

    patient = db.query(Patient).filter(Patient.id == request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{request.patient_id} not found.")

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
    latest_step = (
        db.query(StepRecord)
        .filter(StepRecord.patient_id == patient.id)
        .order_by(StepRecord.timestamp.desc())
        .first()
    )

    ref_time = latest_g.timestamp if latest_g else datetime.now(timezone.utc).replace(tzinfo=None)
    next_ts = ref_time + timedelta(minutes=15)

    # 1. Calculate new synthetic readings
    if request.glucose_value is not None:
        new_g_val = float(request.glucose_value)
    else:
        prev_g = float(latest_g.value) if latest_g else 125.0
        # Modest random walk + user-specified perturbation
        noise = np.random.normal(0.0, 3.5)
        new_g_val = round(max(45.0, min(350.0, prev_g + noise + float(request.glucose_offset_mg_dl))), 1)

    if request.heart_rate is not None:
        new_hr_val = float(request.heart_rate)
    else:
        prev_hr = float(latest_v.heart_rate) if latest_v and latest_v.heart_rate else 72.0
        new_hr_val = round(max(48.0, min(160.0, prev_hr + np.random.normal(0.0, 2.0) + float(request.heart_rate_offset))), 1)

    if request.hrv is not None:
        new_hrv_val = float(request.hrv)
    else:
        prev_hrv = float(latest_v.hrv) if latest_v and latest_v.hrv else 48.0
        new_hrv_val = round(max(15.0, min(100.0, prev_hrv + np.random.normal(0.0, 2.5))), 1)

    # Step interval & daily cumulative steps
    if request.interval_steps is not None:
        interval_steps = int(max(0, request.interval_steps))
    else:
        interval_steps = int(max(0, request.steps_delta or 120))
    prev_cum_steps = latest_step.daily_cumulative_steps if latest_step else 0
    # Reset cumulative steps if day changes
    if latest_step and latest_step.timestamp.date() != next_ts.date():
        cum_steps = interval_steps
    else:
        cum_steps = prev_cum_steps + interval_steps

    # 2. Persist new telemetry
    new_g = GlucoseReading(
        patient_id=patient.id,
        timestamp=next_ts,
        value=new_g_val,
        is_valid=True,
    )
    new_v = VitalReading(
        patient_id=patient.id,
        timestamp=next_ts,
        heart_rate=new_hr_val,
        hrv=new_hrv_val,
    )
    new_s = StepRecord(
        patient_id=patient.id,
        timestamp=next_ts,
        interval_steps=interval_steps,
        daily_cumulative_steps=cum_steps,
        is_synthetic=True,
    )

    db.add(new_g)
    db.add(new_v)
    db.add(new_s)
    db.commit()
    db.refresh(new_g)
    db.refresh(new_v)
    db.refresh(new_s)

    # 3. Re-evaluate alerts
    new_alerts = evaluate_all_alerts_for_patient(db, patient)

    # 4. Re-calculate twin intelligence
    updated_twin = get_digital_twin_intelligence(patient.id, db=db, current_user=current_user)

    return SimulatedSensorFeedResponse(
        patient_id=patient.id,
        patient_name=patient.name,
        feed_timestamp=next_ts,
        ingested_glucose=new_g_val,
        ingested_heart_rate=new_hr_val,
        ingested_hrv=new_hrv_val,
        ingested_interval_steps=interval_steps,
        new_cumulative_steps=cum_steps,
        new_glucose_reading=GlucoseReadingRead(
            id=new_g.id,
            patient_id=new_g.patient_id,
            timestamp=new_g.timestamp,
            value=new_g.value,
            is_valid=new_g.is_valid,
        ),
        new_vital_reading=VitalReadingRead(
            id=new_v.id,
            patient_id=new_v.patient_id,
            timestamp=new_v.timestamp,
            heart_rate=new_v.heart_rate,
            hrv=new_v.hrv,
        ),
        new_step_reading=StepRecordRead(
            id=new_s.id,
            patient_id=new_s.patient_id,
            timestamp=new_s.timestamp,
            interval_steps=new_s.interval_steps,
            daily_cumulative_steps=new_s.daily_cumulative_steps,
            is_synthetic=True,
        ),
        recalculated_twin=updated_twin,
        recalculated_prediction=updated_twin.latest_prediction,
        new_alerts_triggered=[
            AlertRead(
                id=a.id,
                patient_id=a.patient_id,
                patient_name=patient.name,
                timestamp=a.timestamp,
                severity=a.severity,
                message=a.message,
                alert_type=a.alert_type,
                source=a.source or "observed_reading",
                status=a.status or "active",
                trigger_value=a.trigger_value,
                threshold=a.threshold,
                acknowledged=bool(a.acknowledged),
                acknowledged_at=a.acknowledged_at,
                resolved_at=a.resolved_at,
                dedup_key=a.dedup_key,
            )
            for a in new_alerts
        ],
        feed_status="INGESTED_AND_EVALUATED",
        is_synthetic_data=True,
        message=f"Simulated sensor feed epoch ingested for {patient.name} at {next_ts.isoformat()}. Telemetry, alerts, and digital twin state updated.",
    )
