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

from pydantic import BaseModel, ConfigDict, Field
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
    historical_diagnoses: Optional[str] = "None"
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None


class PatientCreate(PatientBase):
    """Schema for creating a new patient (POST body)."""
    pass


class PatientRead(PatientBase):
    """Schema returned when reading a patient (GET response)."""
    id: int
    calculated_bmi: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Laboratory & Genetic Schemas (Historical EHR Extensions)
# ---------------------------------------------------------------------------
class LabResultRead(BaseModel):
    id: int
    patient_id: int
    test_name: str
    result: float
    unit: str
    measurement_date: datetime
    reference_range: Optional[str] = None
    is_synthetic: bool = True

    model_config = ConfigDict(from_attributes=True)


class GeneticMarkerRead(BaseModel):
    id: int
    patient_id: int
    marker_id: str
    gene: str
    genotype: str
    recorded_at: datetime
    data_source: str
    is_synthetic: bool = True

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Sleep & Step Telemetry Schemas (Dynamic Time-Series Extensions)
# ---------------------------------------------------------------------------
class SleepRecordRead(BaseModel):
    id: int
    patient_id: int
    start_time: datetime
    end_time: datetime
    stage: str
    duration_minutes: float
    is_synthetic: bool = True

    model_config = ConfigDict(from_attributes=True)


class SleepSummaryResponse(BaseModel):
    patient_id: int
    total_sleep_hours: float
    deep_sleep_hours: float
    rem_sleep_hours: float
    light_sleep_hours: float
    sleep_efficiency_pct: float
    records: list[SleepRecordRead]
    is_synthetic_data: bool = True


class StepRecordRead(BaseModel):
    id: int
    patient_id: int
    timestamp: datetime
    interval_steps: int
    daily_cumulative_steps: int
    is_synthetic: bool = True

    model_config = ConfigDict(from_attributes=True)


class StepSummaryResponse(BaseModel):
    patient_id: int
    total_steps_24h: int
    latest_interval_steps: int
    peak_interval_steps: int
    hourly_average_steps: float
    records: list[StepRecordRead]
    is_synthetic_data: bool = True


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
# Digital Twin Detail & Summary Schema (Phase 3 / Phase 5)
# ---------------------------------------------------------------------------
class DigitalTwinDetailResponse(BaseModel):
    patient_id: int
    patient_name: str
    diabetes_type: str
    age: int
    gender: str
    years_since_diagnosis: int
    historical_diagnoses: Optional[str] = "None"
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    bmi: Optional[float] = None
    
    # Observed telemetry stats
    latest_glucose: Optional[float] = None
    latest_glucose_timestamp: Optional[datetime] = None
    latest_heart_rate: Optional[float] = None
    latest_hrv: Optional[float] = None
    latest_vital_timestamp: Optional[datetime] = None
    
    # Rolling metrics
    mean_glucose_1h: Optional[float] = None
    mean_glucose_24h: Optional[float] = None
    min_glucose_24h: Optional[float] = None
    max_glucose_24h: Optional[float] = None
    min_glucose_1h: Optional[float] = None
    max_glucose_1h: Optional[float] = None
    glucose_change_1h: Optional[float] = None
    glucose_std_1h: Optional[float] = None
    glucose_trend_slope: Optional[float] = None
    mean_hr_1h: Optional[float] = None
    mean_hrv_1h: Optional[float] = None

    # Sleep & Activity summaries
    latest_sleep_summary: Optional[dict] = None
    latest_step_summary: Optional[dict] = None
    
    # Status and data quality
    data_freshness_status: str = "fresh"  # "fresh", "stale", "no_data"
    hours_since_last_reading: Optional[float] = None
    data_quality_warnings: list[str] = []
    total_readings_24h: int = 0
    total_vital_readings_24h: int = 0

    # Alert state summary
    active_alerts_count: int = 0
    acknowledged_alerts_count: int = 0
    resolved_alerts_count: int = 0
    alert_severity_distribution: dict[str, int] = {}
    most_recent_alert: Optional[AlertRead] = None
    recent_alerts: list[AlertRead] = []
    
    # Experimental model inference summary
    latest_prediction: Optional[dict] = None
    disclaimer: str


# ---------------------------------------------------------------------------
# What-If Counterfactual Simulation Schemas (Phase 3 / Phase 5)
# ---------------------------------------------------------------------------
class WhatIfSimulationRequest(BaseModel):
    patient_id: int
    additional_carbs_g: float = Field(
        default=30.0,
        ge=0.0,
        le=300.0,
        description="Hypothetical meal carbohydrates in grams (0 to 300g)",
    )
    activity_minutes: float = Field(
        default=0.0,
        ge=0.0,
        le=360.0,
        description="Hypothetical moderate physical activity in minutes (0 to 360 min)",
    )
    as_of_glucose: Optional[float] = Field(
        default=None,
        ge=20.0,
        le=600.0,
        description="Optional baseline glucose in mg/dL (20 to 600 mg/dL)",
    )


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
    formula_version: str = "1.0.0-illustrative-heuristic"
    data_quality_warnings: list[str] = []
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


# ---------------------------------------------------------------------------
# Simulated Sensor Feed Schemas (Phase 5: Demonstrable Twin Update Workflow)
# ---------------------------------------------------------------------------
class SimulatedSensorFeedRequest(BaseModel):
    patient_id: int
    glucose_value: Optional[float] = Field(default=None, ge=20.0, le=600.0, description="Optional explicit target glucose in mg/dL")
    heart_rate: Optional[float] = Field(default=None, ge=30.0, le=220.0, description="Optional explicit heart rate in bpm")
    hrv: Optional[float] = Field(default=None, ge=1.0, le=300.0, description="Optional explicit HRV in ms")
    interval_steps: Optional[int] = Field(default=None, ge=0, le=10000, description="Optional explicit interval steps")
    glucose_offset_mg_dl: Optional[float] = Field(default=0.0, ge=-100.0, le=100.0, description="Optional glucose perturbation in mg/dL")
    heart_rate_offset: Optional[float] = Field(default=0.0, ge=-50.0, le=50.0)
    steps_delta: Optional[int] = Field(default=120, ge=0, le=3000)


class SimulatedSensorFeedResponse(BaseModel):
    patient_id: int
    patient_name: str
    feed_timestamp: datetime
    ingested_glucose: float
    ingested_heart_rate: float
    ingested_hrv: float
    ingested_interval_steps: int
    new_cumulative_steps: int
    new_glucose_reading: GlucoseReadingRead
    new_vital_reading: VitalReadingRead
    new_step_reading: StepRecordRead
    recalculated_twin: DigitalTwinDetailResponse
    recalculated_prediction: Optional[dict] = None
    new_alerts_triggered: list[AlertRead] = []
    feed_status: str = "INGESTED_AND_EVALUATED"
    is_synthetic_data: bool = True
    message: str

