"""
routers/predictions.py - Glucose-Spike Prediction Endpoints
============================================================
Provides ML inference endpoint for predicting glucose-spike events (>= 180 mg/dL)
within a 2-hour forward horizon.
"""

import os
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd

from app.database import get_db
from app.models import Patient, GlucoseReading, VitalReading
from app.schemas import PredictionRequest, PredictionResponse
from app.ml.pipeline import (
    load_model_artifact,
    extract_features_at_timestamp,
    FEATURE_NAMES,
    SPIKE_THRESHOLD_MG_DL,
    PREDICTION_HORIZON_MINUTES,
)

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])

# Path to model artifact directory
ML_ARTIFACT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "ml",
    "artifacts"
)


@router.post("/glucose-spike", response_model=PredictionResponse)
def predict_glucose_spike(
    request: PredictionRequest,
    db: Session = Depends(get_db),
):
    """
    Predict whether a patient's glucose level will cross the 180.0 mg/dL threshold
    within the next 2 hours based on recent telemetry and clinical profile.
    """
    # 1. Load model artifact
    pipeline, metadata = load_model_artifact(ML_ARTIFACT_DIR)
    if pipeline is None or metadata is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Glucose-spike prediction model artifact is not available. "
                "Ensure training pipeline has been executed via `python -m app.ml.train`."
            )
        )

    # 2. Validate patient exists
    patient = db.query(Patient).filter(Patient.id == request.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient #{request.patient_id} not found."
        )

    patient_dict = {
        "id": patient.id,
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "diabetes_type": patient.diabetes_type,
        "years_since_diagnosis": patient.years_since_diagnosis,
    }

    # 3. Determine prediction timestamp
    if request.as_of_timestamp is not None:
        prediction_time = request.as_of_timestamp
        if prediction_time.tzinfo is None:
            prediction_time = prediction_time.replace(tzinfo=timezone.utc)
    else:
        # Default to latest glucose reading timestamp for this patient
        latest_r = (
            db.query(GlucoseReading)
            .filter(GlucoseReading.patient_id == patient.id, GlucoseReading.is_valid == True)
            .order_by(GlucoseReading.timestamp.desc())
            .first()
        )
        if not latest_r:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Patient #{patient.id} has no valid glucose readings recorded."
            )
        prediction_time = latest_r.timestamp
        if prediction_time.tzinfo is None:
            prediction_time = prediction_time.replace(tzinfo=timezone.utc)

    # 4. Fetch recent history (past 24 hours up to prediction_time)
    start_history = prediction_time.replace(tzinfo=None) - (prediction_time - (prediction_time - ... if False else prediction_time))
    # Using naive timestamps for SQLite comparison
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

    glucose_dicts = [
        {"id": r.id, "timestamp": r.timestamp, "value": r.value}
        for r in glucose_records
    ]
    vital_dicts = [
        {"id": r.id, "timestamp": r.timestamp, "heart_rate": r.heart_rate, "hrv": r.hrv}
        for r in vital_records
    ]

    # 5. Extract features with zero forward leakage
    features, warnings = extract_features_at_timestamp(
        patient_info=patient_dict,
        glucose_readings=glucose_dicts,
        vital_readings=vital_dicts,
        prediction_time=prediction_time,
    )

    if features is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Insufficient historical data at {prediction_time.isoformat()}: {'; '.join(warnings)}"
        )

    # 6. Model Inference
    X_df = pd.DataFrame([[features[k] for k in FEATURE_NAMES]], columns=FEATURE_NAMES)
    scaler = pipeline.named_steps["scaler"]
    model = pipeline.named_steps["model"]

    X_scaled = scaler.transform(X_df)
    prob = float(model.predict_proba(X_scaled)[0, 1])
    is_spike = bool(prob >= 0.5)

    # Risk categorization
    if prob >= 0.65:
        risk_category = "HIGH"
    elif prob >= 0.35:
        risk_category = "MODERATE"
    else:
        risk_category = "LOW"

    # Linear feature contributions (scaled_feature * coefficient)
    coefs = metadata["feature_coefficients"]
    contributions = {
        name: round(float(X_scaled[0, i] * coefs[name]), 4)
        for i, name in enumerate(FEATURE_NAMES)
    }

    return PredictionResponse(
        patient_id=patient.id,
        patient_name=patient.name,
        prediction_timestamp=prediction_time,
        horizon_minutes=PREDICTION_HORIZON_MINUTES,
        threshold_mg_dl=SPIKE_THRESHOLD_MG_DL,
        spike_predicted=is_spike,
        risk_score=round(prob, 4),
        risk_category=risk_category,
        model_version=metadata.get("model_version", "0.1.0-prototype"),
        model_status="TRAINED_PROTOTYPE",
        features_used=features,
        feature_contributions=contributions,
        data_quality_warnings=warnings,
        is_synthetic_data=True,
        clinical_disclaimer=(
            "RESEARCH PROTOTYPE ONLY: Built on synthetic patient data. "
            "Not clinically validated. Do not use for diagnosis or treatment decisions."
        ),
    )
