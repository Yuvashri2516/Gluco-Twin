"""
routers/patients.py - Patient API endpoints & Medical Data Ingestion
=====================================================================

Provides endpoints for patient registration, editing, and medical history:
  GET   /api/patients               -> list patients (clinician sees cohort, patient sees own profile)
  POST  /api/patients               -> register new patient (clinician only)
  GET   /api/patients/{id}          -> single patient detail (authorized caller only)
  PUT   /api/patients/{id}          -> update existing patient (authorized caller only)
  GET   /api/patients/{id}/labs     -> patient laboratory panels
  POST  /api/patients/{id}/labs     -> manual lab record entry
  GET   /api/patients/{id}/genetics -> patient genetic markers
  POST  /api/patients/{id}/diagnoses-> record diagnosis or medical history (clinician only)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.models import Patient, GlucoseReading, VitalReading, LabResult, GeneticMarker, User
from app.schemas import (
    PatientRead,
    PatientCreate,
    PatientUpdate,
    LabResultRead,
    GeneticMarkerRead,
    ManualLabCreate,
    ManualDiagnosisCreate,
)
from app.auth import (
    get_current_user,
    require_clinician,
    check_patient_authorization,
)

router = APIRouter(prefix="/api/patients", tags=["Patients"])


@router.get("", response_model=list[PatientRead])
@router.get("/", response_model=list[PatientRead], include_in_schema=False)
def list_patients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return registered patients based on caller authorization.
    - Clinicians view the complete cohort roster.
    - Patients view only their own profile, preventing cohort data scraping.
    """
    if current_user.role == "clinician":
        return db.query(Patient).order_by(Patient.id.asc()).all()

    # Patient user sees only their own profile
    if current_user.patient_id:
        p = db.query(Patient).filter(Patient.id == current_user.patient_id).first()
        return [p] if p else []

    return []


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=PatientRead, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_patient(
    payload: PatientCreate,
    current_user: User = Depends(require_clinician),
    db: Session = Depends(get_db),
):
    """
    Register a new patient into the cohort.
    Enforces server-validated clinician role.
    Enforces validation, duplicate submission prevention, and preserves existing synthetic patients.
    Never silently seeds fake telemetry for newly registered patients.
    """
    clean_name = payload.name.strip()
    if len(clean_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Patient name must be at least 2 characters long."
        )

    # Duplicate check: prevent rapid double submission of identical patient profile
    existing = (
        db.query(Patient)
        .filter(
            Patient.name == clean_name,
            Patient.age == payload.age,
            Patient.gender == payload.gender,
            Patient.diabetes_type == payload.diabetes_type,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Patient '{clean_name}' (Age {payload.age}, {payload.diabetes_type}) already exists with ID #{existing.id}."
        )

    patient = Patient(
        name=clean_name,
        age=payload.age,
        gender=payload.gender,
        diabetes_type=payload.diabetes_type,
        years_since_diagnosis=payload.years_since_diagnosis,
        historical_diagnoses=payload.historical_diagnoses or "None",
        medical_history=payload.medical_history or "",
        weight_kg=payload.weight_kg,
        height_cm=payload.height_cm,
        created_at=datetime.now(timezone.utc),
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a single patient by ID. Enforces server-side patient isolation check."""
    check_patient_authorization(patient_id, current_user)

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{patient_id} not found.")
    return patient


@router.put("/{patient_id}", response_model=PatientRead)
def update_patient(
    patient_id: int,
    payload: PatientUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update profile attributes for an existing patient. Enforces patient isolation check."""
    check_patient_authorization(patient_id, current_user)

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{patient_id} not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "name" and value is not None:
            clean_name = value.strip()
            if len(clean_name) < 2:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Patient name must be at least 2 characters long."
                )
            setattr(patient, field, clean_name)
        elif value is not None:
            setattr(patient, field, value)

    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}/labs", response_model=list[LabResultRead])
def get_patient_labs(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return structured laboratory panel records for a patient."""
    check_patient_authorization(patient_id, current_user)

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{patient_id} not found.")
    return (
        db.query(LabResult)
        .filter(LabResult.patient_id == patient_id)
        .order_by(LabResult.measurement_date.asc())
        .all()
    )


@router.post("/{patient_id}/labs", response_model=LabResultRead, status_code=status.HTTP_201_CREATED)
def create_patient_lab(
    patient_id: int,
    payload: ManualLabCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manually record a laboratory test result for a patient.
    Tagged explicitly with source (manual/imported) and never claimed as verified.
    """
    check_patient_authorization(patient_id, current_user)

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{patient_id} not found.")

    m_date = payload.measurement_date or datetime.now(timezone.utc)
    if m_date.tzinfo is not None:
        m_date = m_date.replace(tzinfo=None)

    lab_record = LabResult(
        patient_id=patient_id,
        test_name=payload.test_name.strip(),
        result=round(float(payload.result), 2),
        unit=payload.unit.strip(),
        reference_range=payload.reference_range.strip() if payload.reference_range else None,
        measurement_date=m_date,
        is_synthetic=False,
        data_source=payload.data_source or "manual",
        lab_source=payload.lab_source or "Manual Clinical Entry",
    )
    db.add(lab_record)
    db.commit()
    db.refresh(lab_record)
    return lab_record


@router.get("/{patient_id}/genetics", response_model=list[GeneticMarkerRead])
def get_patient_genetics(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return synthetic genetic marker profiles for a patient."""
    check_patient_authorization(patient_id, current_user)

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{patient_id} not found.")
    return (
        db.query(GeneticMarker)
        .filter(GeneticMarker.patient_id == patient_id)
        .order_by(GeneticMarker.id.asc())
        .all()
    )


@router.post("/{patient_id}/diagnoses", response_model=PatientRead)
def record_patient_diagnosis(
    patient_id: int,
    payload: ManualDiagnosisCreate,
    current_user: User = Depends(require_clinician),
    db: Session = Depends(get_db),
):
    """
    Append an active/historical diagnosis and clinical notes to a patient's medical profile.
    Requires server-validated clinician role.
    """
    check_patient_authorization(patient_id, current_user)

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{patient_id} not found.")

    diag_name = payload.diagnosis_name.strip()
    current_diag = patient.historical_diagnoses or ""
    if current_diag == "None" or not current_diag.strip():
        patient.historical_diagnoses = diag_name
    elif diag_name.lower() not in current_diag.lower():
        patient.historical_diagnoses = f"{current_diag}, {diag_name}"

    if payload.notes:
        existing_history = patient.medical_history or ""
        note_entry = f"[{payload.date or 'Undated'}] ({payload.status or 'active'}) {diag_name}: {payload.notes.strip()}"
        patient.medical_history = f"{existing_history}\n{note_entry}".strip()

    db.commit()
    db.refresh(patient)
    return patient
