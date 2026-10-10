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
    timestamp: datetime
    severity: str
    message: str
    acknowledged: bool
    acknowledged_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Health-check response
# ---------------------------------------------------------------------------
class HealthCheck(BaseModel):
    status: str
    version: str
    database: str
