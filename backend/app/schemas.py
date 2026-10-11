"""
schemas.py - Pydantic response/request schemas
================================================

WHY SEPARATE SCHEMAS FROM MODELS?
  ORM models (models.py) describe the *database*.
  Pydantic schemas describe the *API contract* -- what the
  frontend sends and receives.  Keeping them separate means
  we can change the database without breaking the API, and
  vice versa.

  `model_config = ConfigDict(from_attributes=True)` tells
  Pydantic v2 to read data directly from SQLAlchemy model
  instances (which use attribute access, not dict access).
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Patient schemas
# ---------------------------------------------------------------------------
class PatientBase(BaseModel):
    """Fields shared by create and read operations."""
    name: str
    age: int
    gender: str
    diabetes_type: str
    years_since_diagnosis: int = 0
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None


class PatientCreate(PatientBase):
    """Schema for creating a new patient (POST body)."""
    pass


class PatientRead(PatientBase):
    """Schema returned when reading a patient (GET response)."""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Glucose reading schemas
# ---------------------------------------------------------------------------
class GlucoseReadingRead(BaseModel):
    id: int
    patient_id: int
    timestamp: datetime
    value: float
    is_valid: bool

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Vital reading schemas
# ---------------------------------------------------------------------------
class VitalReadingRead(BaseModel):
    id: int
    patient_id: int
    timestamp: datetime
    heart_rate: Optional[float]
    hrv: Optional[float]

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Digital Twin state schemas
# ---------------------------------------------------------------------------
class DigitalTwinStateRead(BaseModel):
    id: int
    patient_id: int
    timestamp: datetime
    avg_glucose_1h: Optional[float]
    avg_glucose_3h: Optional[float]
    glucose_std_1h: Optional[float]
    glucose_trend: Optional[float]
    avg_heart_rate_1h: Optional[float]
    avg_hrv_1h: Optional[float]
    risk_score: float
    status: str

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Alert schemas
# ---------------------------------------------------------------------------
class AlertRead(BaseModel):
    id: int
    patient_id: int
    patient_name: Optional[str] = None
    timestamp: datetime
    severity: str
    message: str
    alert_type: Optional[str] = None
    source: Optional[str] = "observed_reading"
    status: Optional[str] = "active"
    trigger_value: Optional[float] = None
    threshold: Optional[float] = None
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    dedup_key: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AlertEvaluationRequest(BaseModel):
    patient_id: Optional[int] = None


class AlertEvaluationResponse(BaseModel):
    evaluated_patients: int
    new_alerts_created: int
    alerts: list[AlertRead]


# ---------------------------------------------------------------------------
# Digital Twin Detail & Summary Schema (Phase 5)
# ---------------------------------------------------------------------------
class DigitalTwinDetailResponse(BaseModel):
    patient_id: int
    patient_name: str
    diabetes_type: str
    age: int
    gender: str
    years_since_diagnosis: int
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    bmi: Optional[float] = None
    
    # Observed telemetry stats
    latest_glucose: Optional[float] = None
    latest_glucose_timestamp: Optional[datetime] = None
    latest_heart_rate: Optional[float] = None
    latest_hrv: Optional[float] = None
    
    # Rolling metrics
    mean_glucose_1h: Optional[float] = None
    mean_glucose_24h: Optional[float] = None
    glucose_std_1h: Optional[float] = None
    glucose_trend_slope: Optional[float] = None
    mean_hr_1h: Optional[float] = None
    mean_hrv_1h: Optional[float] = None
    
    # Status and data quality
    data_quality_warnings: list[str] = []
    total_readings_24h: int = 0
    active_alerts_count: int = 0
    recent_alerts: list[AlertRead] = []
    
    # Experimental model inference summary
    latest_prediction: Optional[dict] = None
    disclaimer: str


# ---------------------------------------------------------------------------
# What-If Counterfactual Simulation Schemas (Phase 5)
# ---------------------------------------------------------------------------
class WhatIfSimulationRequest(BaseModel):
    patient_id: int
    additional_carbs_g: float = 30.0
    activity_minutes: float = 0.0
    as_of_glucose: Optional[float] = None


class WhatIfSimulationResponse(BaseModel):
    patient_id: int
    patient_name: str
    baseline_glucose: float
    additional_carbs_g: float
    activity_minutes: float
    projected_carb_impact_mg_dl: float
    projected_activity_impact_mg_dl: float
    projected_scenario_glucose: float
    projected_spike_risk_breach: bool
    spike_threshold_mg_dl: float = 180.0
    assumptions: list[str]
    disclaimer: str


# ---------------------------------------------------------------------------
# Health-check response
# ---------------------------------------------------------------------------
class HealthCheck(BaseModel):
    status: str
    version: str
    database: str


# ---------------------------------------------------------------------------
# Prediction schemas (Phase 3: Glucose-Spike Prediction Engine)
# ---------------------------------------------------------------------------
class PredictionRequest(BaseModel):
    patient_id: int
    as_of_timestamp: Optional[datetime] = None


class PredictionResponse(BaseModel):
    patient_id: int
    patient_name: str
    prediction_timestamp: datetime
    horizon_minutes: int
    threshold_mg_dl: float
    spike_predicted: bool
    risk_score: float
    risk_category: str
    model_version: str
    model_status: str
    features_used: dict[str, float]
    feature_contributions: dict[str, float]
    data_quality_warnings: list[str]
    is_synthetic_data: bool = True
    clinical_disclaimer: str

