"""
models.py - SQLAlchemy ORM models
==================================

Each class here maps to a table in the SQLite database.
Columns are defined as class attributes using SQLAlchemy's
`Column` type.  Relationships (e.g. a Patient has many
GlucoseReadings) are expressed with `relationship()`.

TABLE OVERVIEW:
  patients          - demographic & clinical profile
  glucose_readings  - time-series glucose values (mg/dL)
  vital_readings    - heart rate (bpm) and HRV (ms)
  digital_twin_state - latest computed twin snapshot per patient
  alerts            - generated risk alerts
"""

from sqlalchemy import (
    Column, Integer, Float, String, DateTime, Boolean,
    ForeignKey, Text,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


# ---------------------------------------------------------------------------
# Patient profile
# ---------------------------------------------------------------------------
class Patient(Base):
    """
    Represents a synthetic patient.

    Fields like diabetes_type and years_since_diagnosis help the
    prediction model contextualise glucose readings.
    """
    __tablename__ = "patients"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(120), nullable=False)
    age           = Column(Integer, nullable=False)
    gender        = Column(String(10), nullable=False)
    diabetes_type = Column(String(20), nullable=False)          # "Type 1", "Type 2", "Pre-diabetic"
    years_since_diagnosis = Column(Integer, default=0)
    weight_kg     = Column(Float)
    height_cm     = Column(Float)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # One-to-many relationships  (lazy="dynamic" returns a query, not a list,
    # which is more efficient for large datasets)
    glucose_readings = relationship("GlucoseReading", back_populates="patient", lazy="dynamic")
    vital_readings   = relationship("VitalReading",   back_populates="patient", lazy="dynamic")
    twin_states      = relationship("DigitalTwinState", back_populates="patient", lazy="dynamic")
    alerts           = relationship("Alert", back_populates="patient", lazy="dynamic")


# ---------------------------------------------------------------------------
# Glucose readings  (the primary time-series we predict on)
# ---------------------------------------------------------------------------
class GlucoseReading(Base):
    """
    A single glucose measurement at a point in time.

    In a real system this would come from a CGM sensor;
    here we generate synthetic values in seed.py.
    """
    __tablename__ = "glucose_readings"

    id         = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    timestamp  = Column(DateTime, nullable=False, index=True)
    value      = Column(Float, nullable=False)   # mg/dL
    is_valid   = Column(Boolean, default=True)    # Flag for data-quality checks

    patient = relationship("Patient", back_populates="glucose_readings")


# ---------------------------------------------------------------------------
# Vital-sign readings  (heart rate + heart-rate variability)
# ---------------------------------------------------------------------------
class VitalReading(Base):
    """
    Supplementary physiological signals that correlate with
    glucose regulation (e.g. elevated HR can accompany hypo events).
    """
    __tablename__ = "vital_readings"

    id            = Column(Integer, primary_key=True, index=True)
    patient_id    = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    timestamp     = Column(DateTime, nullable=False, index=True)
    heart_rate    = Column(Float)  # bpm
    hrv           = Column(Float)  # ms  (RMSSD or SDNN)

    patient = relationship("Patient", back_populates="vital_readings")


# ---------------------------------------------------------------------------
# Digital Twin state  (computed summary that evolves over time)
# ---------------------------------------------------------------------------
class DigitalTwinState(Base):
    """
    A snapshot of the patient's digital twin at a given moment.

    The twin aggregates recent readings into a compact state vector
    that the prediction model consumes.  Keeping the latest state
    in the DB lets us serve it instantly without re-computing.
    """
    __tablename__ = "digital_twin_states"

    id                = Column(Integer, primary_key=True, index=True)
    patient_id        = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    timestamp         = Column(DateTime, nullable=False)
    avg_glucose_1h    = Column(Float)   # Rolling 1-hour average glucose
    avg_glucose_3h    = Column(Float)   # Rolling 3-hour average glucose
    glucose_std_1h    = Column(Float)   # Glucose variability in last hour
    glucose_trend     = Column(Float)   # Slope of glucose over last hour (mg/dL per min)
    avg_heart_rate_1h = Column(Float)
    avg_hrv_1h        = Column(Float)
    risk_score        = Column(Float, default=0.0)   # 0-1 spike probability
    status            = Column(String(20), default="normal")  # normal / warning / critical

    patient = relationship("Patient", back_populates="twin_states")


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------
class Alert(Base):
    """
    A risk alert generated by observed telemetry rules or experimental prediction models.
    Clinical staff can view, acknowledge, and resolve alerts via the dashboard.
    """
    __tablename__ = "alerts"

    id              = Column(Integer, primary_key=True, index=True)
    patient_id      = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    timestamp       = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    severity        = Column(String(20), nullable=False)  # critical / warning / info
    message         = Column(Text, nullable=False)
    acknowledged    = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)

    # Phase 5 Alert Engine fields:
    alert_type      = Column(String(50), nullable=True)  # observed_hypoglycemia, observed_hyperglycemia, etc.
    source          = Column(String(30), default="observed_reading", nullable=True)  # observed_reading | experimental_prediction
    status          = Column(String(20), default="active", nullable=True)  # active | acknowledged | resolved
    trigger_value   = Column(Float, nullable=True)
    threshold       = Column(Float, nullable=True)
    resolved_at     = Column(DateTime, nullable=True)
    dedup_key       = Column(String(120), nullable=True, unique=True, index=True)

    patient = relationship("Patient", back_populates="alerts")

