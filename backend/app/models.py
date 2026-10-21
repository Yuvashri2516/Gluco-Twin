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
    historical_diagnoses  = Column(Text, default="None")
    medical_history       = Column(Text, default="")
    weight_kg     = Column(Float)
    height_cm     = Column(Float)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # One-to-many relationships  (lazy="dynamic" returns a query, not a list,
    # which is more efficient for large datasets)
    glucose_readings = relationship("GlucoseReading", back_populates="patient", lazy="dynamic")
    vital_readings   = relationship("VitalReading",   back_populates="patient", lazy="dynamic")
    twin_states      = relationship("DigitalTwinState", back_populates="patient", lazy="dynamic")
    alerts           = relationship("Alert", back_populates="patient", lazy="dynamic")
    lab_results      = relationship("LabResult", back_populates="patient", lazy="dynamic", cascade="all, delete-orphan")
    genetic_markers  = relationship("GeneticMarker", back_populates="patient", lazy="dynamic", cascade="all, delete-orphan")
    sleep_records    = relationship("SleepRecord", back_populates="patient", lazy="dynamic", cascade="all, delete-orphan")
    step_records     = relationship("StepRecord", back_populates="patient", lazy="dynamic", cascade="all, delete-orphan")
    medical_documents= relationship("MedicalDocument", back_populates="patient", lazy="dynamic", cascade="all, delete-orphan")
    user_account     = relationship("User", back_populates="patient", uselist=False)

    @property
    def calculated_bmi(self):
        if self.weight_kg and self.height_cm and self.height_cm > 0:
            return round(self.weight_kg / ((self.height_cm / 100.0) ** 2), 1)
        return None


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
    unit       = Column(String(20), default="mg/dL")
    is_valid   = Column(Boolean, default=True)    # Flag for data-quality checks
    data_source= Column(String(50), default="synthetic") # 'manual', 'imported', 'synthetic', 'measured'

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
    data_source   = Column(String(50), default="synthetic") # 'manual', 'imported', 'synthetic', 'measured'

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


# ---------------------------------------------------------------------------
# Laboratory Results (Historical EHR panel: HbA1c, Lipids, Fasting Glucose)
# ---------------------------------------------------------------------------
class LabResult(Base):
    """
    Structured synthetic laboratory panel records.
    Explicitly labeled as synthetic to comply with healthcare privacy requirements.
    """
    __tablename__ = "lab_results"

    id               = Column(Integer, primary_key=True, index=True)
    patient_id       = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    test_name        = Column(String(80), nullable=False, index=True)  # HbA1c, Fasting Blood Glucose, Total Cholesterol, HDL, LDL, Triglycerides
    result           = Column(Float, nullable=False)
    unit             = Column(String(30), nullable=False)              # %, mg/dL
    measurement_date = Column(DateTime, nullable=False, index=True)
    reference_range  = Column(String(50), nullable=True)               # e.g., "< 5.7%", "< 100 mg/dL"
    is_synthetic     = Column(Boolean, default=True, nullable=False)
    data_source      = Column(String(50), default="synthetic")         # 'manual', 'imported', 'synthetic', 'measured'
    lab_source       = Column(String(120), default="Simulated Diagnostic Laboratory")

    patient = relationship("Patient", back_populates="lab_results")


# ---------------------------------------------------------------------------
# Genetic Markers (Synthetic Genotypic Context)
# ---------------------------------------------------------------------------
class GeneticMarker(Base):
    """
    Simulated genotype records for diabetes susceptibility markers (e.g., TCF7L2, PPARG).
    Explicitly labeled as synthetic demonstration data without clinical claims.
    """
    __tablename__ = "genetic_markers"

    id               = Column(Integer, primary_key=True, index=True)
    patient_id       = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    marker_id        = Column(String(80), nullable=False, index=True)  # e.g., "rs7903146"
    gene             = Column(String(50), nullable=False)              # e.g., "TCF7L2"
    genotype         = Column(String(60), nullable=False)              # e.g., "CT (Elevated risk allele)"
    recorded_at      = Column(DateTime, nullable=False)
    data_source      = Column(String(100), default="Simulated Microarray Panel")
    is_synthetic     = Column(Boolean, default=True, nullable=False)

    patient = relationship("Patient", back_populates="genetic_markers")


# ---------------------------------------------------------------------------
# Sleep Telemetry (Dynamic Time-Series: Stages & Durations)
# ---------------------------------------------------------------------------
class SleepRecord(Base):
    """
    Synthetic sleep architecture records (light, deep, REM, awake).
    """
    __tablename__ = "sleep_records"

    id               = Column(Integer, primary_key=True, index=True)
    patient_id       = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    start_time       = Column(DateTime, nullable=False, index=True)
    end_time         = Column(DateTime, nullable=False, index=True)
    stage            = Column(String(30), nullable=False)              # "light", "deep", "rem", "awake"
    duration_minutes = Column(Float, nullable=False)
    is_synthetic     = Column(Boolean, default=True, nullable=False)

    patient = relationship("Patient", back_populates="sleep_records")


# ---------------------------------------------------------------------------
# Step-Count Telemetry (Dynamic Time-Series: Interval & Daily Cumulative)
# ---------------------------------------------------------------------------
class StepRecord(Base):
    """
    Synthetic physical activity records distinguishing 15-minute interval steps
    from daily cumulative step totals.
    """
    __tablename__ = "step_records"

    id                    = Column(Integer, primary_key=True, index=True)
    patient_id            = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    timestamp             = Column(DateTime, nullable=False, index=True)
    interval_steps        = Column(Integer, nullable=False)             # Steps taken in the 15-min interval
    daily_cumulative_steps= Column(Integer, nullable=False)             # Cumulative steps on that calendar day up to timestamp
    is_synthetic          = Column(Boolean, default=True, nullable=False)

    patient = relationship("Patient", back_populates="step_records")


# ---------------------------------------------------------------------------
# Medical Documents & Uploaded Diagnostic Artifacts
# ---------------------------------------------------------------------------
class MedicalDocument(Base):
    """
    Stores metadata for patient-associated uploaded medical records (PDF, Images, CSV, XLSX).
    Physical binaries reside in secure, unguessable storage paths outside public directories.
    Unconfirmed extraction results remain strictly isolated in extraction_metadata.
    """
    __tablename__ = "medical_documents"

    id                  = Column(Integer, primary_key=True, index=True)
    patient_id          = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    original_filename   = Column(String(255), nullable=False)
    storage_filename    = Column(String(255), nullable=False, unique=True, index=True)
    storage_path        = Column(String(500), nullable=False)
    file_size           = Column(Integer, nullable=False)
    mime_type           = Column(String(100), nullable=False)
    document_category   = Column(String(50), default="lab_report")      # 'lab_report', 'clinical_note', 'cgm_export', 'other'
    upload_timestamp    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processing_status   = Column(String(50), default="completed")      # 'pending', 'processing', 'completed', 'failed', 'confirmed', 'cancelled'
    raw_text            = Column(Text, nullable=True)
    extraction_metadata = Column(Text, nullable=True)                  # JSON string containing candidate extractions & warnings
    error_message       = Column(Text, nullable=True)
    is_confirmed        = Column(Boolean, default=False)
    confirmed_at        = Column(DateTime, nullable=True)

    patient = relationship("Patient", back_populates="medical_documents")


# ---------------------------------------------------------------------------
# User Accounts & Access Control (Authentication / RBAC)
# ---------------------------------------------------------------------------
class User(Base):
    """
    User account model for authentication and role-based access control (RBAC).
    Roles:
      - 'clinician': Authorized to view, create, edit, and manage all cohort patients and documents.
      - 'patient': Authorized only to access their own patient profile, readings, and documents.
    """
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(64), unique=True, index=True, nullable=False)
    email           = Column(String(120), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role            = Column(String(32), default="patient", nullable=False)  # 'clinician' or 'patient'
    full_name       = Column(String(120), nullable=True)
    medical_license_number = Column(String(64), nullable=True)
    approval_status = Column(String(32), default="approved", nullable=False)  # 'approved', 'pending', 'rejected'
    patient_id      = Column(Integer, ForeignKey("patients.id"), nullable=True, index=True)
    is_active       = Column(Boolean, default=True, nullable=False)
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    patient = relationship("Patient", back_populates="user_account")
    patient_assignments = relationship("DoctorPatientAssignment", foreign_keys="[DoctorPatientAssignment.doctor_id]", back_populates="doctor", lazy="dynamic", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Doctor-Patient Assignments (Clinician Scope Isolation)
# ---------------------------------------------------------------------------
class DoctorPatientAssignment(Base):
    """
    Explicit assignment linking a clinician (User) to a specific Patient.
    Enforces granular doctor-to-patient authorization scope.
    """
    __tablename__ = "doctor_patient_assignments"

    id          = Column(Integer, primary_key=True, index=True)
    doctor_id   = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    patient_id  = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    doctor  = relationship("User", foreign_keys=[doctor_id], back_populates="patient_assignments")
    patient = relationship("Patient", foreign_keys=[patient_id])


