"""
routers/patients.py - Patient API endpoints
=============================================

Provides CRUD-style endpoints for patient data:
  GET  /api/patients          -> list all patients
  GET  /api/patients/{id}     -> single patient with recent readings
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models import Patient, GlucoseReading, VitalReading
from app.schemas import PatientRead, GlucoseReadingRead, VitalReadingRead

router = APIRouter(prefix="/api/patients", tags=["Patients"])


@router.get("", response_model=list[PatientRead])
@router.get("/", response_model=list[PatientRead], include_in_schema=False)
def list_patients(db: Session = Depends(get_db)):
    """Return all synthetic patients."""
    return db.query(Patient).all()


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    """Return a single patient by ID."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
