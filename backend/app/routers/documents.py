"""
routers/documents.py - Medical Document Ingestion & Document Intelligence
==========================================================================

Endpoints for patient-associated medical document lifecycle:
  POST   /api/documents/upload               -> Upload PDF, image, CSV, or XLSX
  GET    /api/documents/patient/{patient_id} -> List patient documents
  GET    /api/documents/{id}                 -> Retrieve document metadata
  GET    /api/documents/{id}/preview         -> Inspect extracted draft & preview
  GET    /api/documents/{id}/download        -> Secure download of original file
  POST   /api/documents/{id}/extract         -> Re-trigger extraction
  POST   /api/documents/{id}/confirm         -> Confirm reviewable draft and save to EHR
  POST   /api/documents/{id}/cancel          -> Cancel draft without saving records
  DELETE /api/documents/{id}                 -> Remove document & file storage

Security & Access Control (Phase A & B):
  - Every endpoint requires valid Bearer authentication (get_current_user).
  - Explicit server-side validation guarantees patients cannot access or download
    another patient's documents (check_patient_authorization, check_document_authorization).
  - Confirming draft values into active patient EHR requires explicit clinician privileges.
  - Multi-backend persistent storage abstraction (local disk or private S3 object storage).
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Patient, MedicalDocument, LabResult, GlucoseReading, User
from app.schemas import (
    MedicalDocumentRead,
    DocumentConfirmRequest,
    LabResultRead,
)
from app.services.storage import storage_provider, FileValidationError, StorageError
from app.services.document_parser import parse_and_extract_document
from app.alerts_engine import evaluate_all_alerts_for_patient
from app.auth import (
    get_current_user,
    require_clinician,
    check_patient_authorization,
    check_document_authorization,
)

router = APIRouter(prefix="/api/documents", tags=["Medical Documents"])


@router.post("/upload", response_model=MedicalDocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_medical_document(
    patient_id: int = Form(...),
    document_category: str = Form(default="lab_report"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a medical report or telemetry file (PDF, PNG, JPG, JPEG, CSV, XLSX).
    Requires caller authorization for patient_id.
    Performs initial local parsing and entity extraction, creating an unconfirmed
    reviewable draft strictly isolated from verified patient EHR records.
    """
    check_patient_authorization(patient_id, current_user)

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{patient_id} not found.")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename in upload.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")

    # Save binary through abstract storage provider (local disk or S3 object storage)
    try:
        storage_filename, storage_path, file_size = storage_provider.save_file(
            content, file.filename
        )
    except FileValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # Parse and extract document entities (supports in-memory bytes and local path)
    try:
        extraction_dict = parse_and_extract_document(
            content, filename=file.filename, expected_patient_name=patient.name
        )
        extraction_json = json.dumps(extraction_dict)
        proc_status = "completed"
        err_msg = None
    except Exception as e:
        extraction_json = json.dumps({"error": str(e), "candidate_labs": [], "warnings": [f"Parsing error: {str(e)}"]})
        proc_status = "failed"
        err_msg = str(e)

    # Persist document metadata to database
    doc_record = MedicalDocument(
        patient_id=patient.id,
        original_filename=file.filename,
        storage_filename=storage_filename,
        storage_path=storage_path,
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        document_category=document_category,
        upload_timestamp=datetime.now(timezone.utc),
        processing_status=proc_status,
        raw_text=extraction_dict.get("raw_text") if proc_status == "completed" else None,
        extraction_metadata=extraction_json,
        error_message=err_msg,
        is_confirmed=False,
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)
    return doc_record


@router.get("/patient/{patient_id}", response_model=List[MedicalDocumentRead])
def list_patient_documents(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all uploaded medical documents associated with a patient.
    Enforces authorization check ensuring patients can only view their own records.
    """
    check_patient_authorization(patient_id, current_user)

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{patient_id} not found.")

    return (
        db.query(MedicalDocument)
        .filter(MedicalDocument.patient_id == patient_id)
        .order_by(MedicalDocument.upload_timestamp.desc())
        .all()
    )


@router.get("/{document_id}", response_model=MedicalDocumentRead)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve metadata for a specific document. Enforces document ownership check."""
    doc = db.query(MedicalDocument).filter(MedicalDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document #{document_id} not found.")

    check_document_authorization(doc, current_user)
    return doc


@router.get("/{document_id}/preview")
def get_document_preview(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return structured draft extraction results, candidate laboratory panels,
    table previews, and validation warnings for review.
    Enforces server-side document ownership check.
    """
    doc = db.query(MedicalDocument).filter(MedicalDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document #{document_id} not found.")

    check_document_authorization(doc, current_user)

    patient = db.query(Patient).filter(Patient.id == doc.patient_id).first()
    extraction_data = {}
    if doc.extraction_metadata:
        try:
            extraction_data = json.loads(doc.extraction_metadata)
        except Exception:
            extraction_data = {"raw_text": doc.raw_text, "candidate_labs": [], "warnings": []}

    return {
        "document_id": doc.id,
        "patient_id": doc.patient_id,
        "patient_name": patient.name if patient else "Unknown",
        "original_filename": doc.original_filename,
        "file_size": doc.file_size,
        "mime_type": doc.mime_type,
        "document_category": doc.document_category,
        "upload_timestamp": doc.upload_timestamp.isoformat() if doc.upload_timestamp else None,
        "processing_status": doc.processing_status,
        "is_confirmed": doc.is_confirmed,
        "confirmed_at": doc.confirmed_at.isoformat() if doc.confirmed_at else None,
        "extraction": extraction_data,
    }


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Download the original stored medical report file securely.
    Enforces authorization check; retrieves bytes from abstracted storage (local disk or S3);
    never exposes internal filesystem paths or public cloud URLs.
    """
    doc = db.query(MedicalDocument).filter(MedicalDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document #{document_id} not found.")

    check_document_authorization(doc, current_user)

    try:
        file_bytes = storage_provider.get_file_bytes(doc.storage_filename)
    except StorageError as e:
        raise HTTPException(status_code=404, detail=str(e))

    safe_ascii_name = doc.original_filename.encode("ascii", "ignore").decode() or "medical_document"
    return Response(
        content=file_bytes,
        media_type=doc.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_ascii_name}"',
            "Content-Length": str(len(file_bytes)),
        },
    )


@router.post("/{document_id}/extract", response_model=MedicalDocumentRead)
def reextract_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Re-run text parsing and entity extraction on an existing stored file."""
    doc = db.query(MedicalDocument).filter(MedicalDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document #{document_id} not found.")

    check_document_authorization(doc, current_user)

    patient = db.query(Patient).filter(Patient.id == doc.patient_id).first()
    try:
        file_bytes = storage_provider.get_file_bytes(doc.storage_filename)
        extraction_dict = parse_and_extract_document(
            file_bytes, filename=doc.original_filename, expected_patient_name=patient.name if patient else None
        )
        doc.raw_text = extraction_dict.get("raw_text")
        doc.extraction_metadata = json.dumps(extraction_dict)
        doc.processing_status = "completed"
        doc.error_message = None
    except Exception as e:
        doc.processing_status = "failed"
        doc.error_message = str(e)

    db.commit()
    db.refresh(doc)
    return doc


@router.post("/{document_id}/confirm")
def confirm_document_extraction(
    document_id: int,
    payload: DocumentConfirmRequest,
    current_user: User = Depends(require_clinician),
    db: Session = Depends(get_db),
):
    """
    Clinician confirmation step: commits reviewed laboratory values and readings
    into the active patient EHR and time-series tables.
    Requires server-validated clinician role. Prevents accidental duplicate imports.
    """
    doc = db.query(MedicalDocument).filter(MedicalDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document #{document_id} not found.")

    if doc.is_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document #{document_id} has already been confirmed and imported into the patient record."
        )

    patient = db.query(Patient).filter(Patient.id == doc.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient #{doc.patient_id} not found.")

    now_utc = datetime.now(timezone.utc)
    added_labs_count = 0
    added_readings_count = 0

    # 1. Commit confirmed laboratory results
    for lab_item in payload.confirmed_labs:
        m_date = lab_item.measurement_date or now_utc
        if m_date.tzinfo is not None:
            m_date = m_date.replace(tzinfo=None)

        lab_record = LabResult(
            patient_id=patient.id,
            test_name=lab_item.test_name.strip(),
            result=round(float(lab_item.result), 2),
            unit=lab_item.unit.strip(),
            reference_range=lab_item.reference_range.strip() if lab_item.reference_range else None,
            measurement_date=m_date,
            is_synthetic=False,
            data_source="imported",
            lab_source=f"Imported from {doc.original_filename}",
        )
        db.add(lab_record)
        added_labs_count += 1

    # 2. Commit confirmed glucose readings (if present in document/table)
    for g_item in payload.confirmed_readings:
        unit_clean = g_item.unit.strip().lower()
        if unit_clean in ["mmol/l", "mmol"]:
            val_mgdl = round(g_item.value * 18.0182, 1)
        else:
            val_mgdl = round(g_item.value, 1)

        ts = g_item.timestamp or now_utc
        if ts.tzinfo is not None:
            ts = ts.replace(tzinfo=None)

        db.add(GlucoseReading(
            patient_id=patient.id,
            timestamp=ts,
            value=val_mgdl,
            unit="mg/dL",
            is_valid=True,
            data_source="imported",
        ))
        added_readings_count += 1

    # 3. Optional clinical notes append
    if payload.clinical_notes:
        existing_history = patient.medical_history or ""
        note = f"[{now_utc.strftime('%Y-%m-%d %H:%M')}] Note on imported doc '{doc.original_filename}': {payload.clinical_notes.strip()}"
        patient.medical_history = f"{existing_history}\n{note}".strip()

    # Mark document as confirmed
    doc.is_confirmed = True
    doc.processing_status = "confirmed"
    doc.confirmed_at = now_utc

    db.commit()

    # Re-evaluate alerts if new readings or labs were ingested
    try:
        evaluate_all_alerts_for_patient(db, patient)
    except Exception:
        pass

    return {
        "status": "success",
        "message": f"Successfully confirmed document '{doc.original_filename}'.",
        "confirmed_labs_count": added_labs_count,
        "confirmed_readings_count": added_readings_count,
        "patient_id": patient.id,
        "confirmed_at": doc.confirmed_at.isoformat(),
    }


@router.post("/{document_id}/cancel")
def cancel_document_extraction(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel document extraction without saving any records to the patient's EHR."""
    doc = db.query(MedicalDocument).filter(MedicalDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document #{document_id} not found.")

    check_document_authorization(doc, current_user)

    doc.processing_status = "cancelled"
    db.commit()
    return {"status": "cancelled", "document_id": doc.id}


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a document record and its underlying stored file."""
    doc = db.query(MedicalDocument).filter(MedicalDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document #{document_id} not found.")

    check_document_authorization(doc, current_user)

    storage_provider.delete_file(doc.storage_filename)
    db.delete(doc)
    db.commit()
    return {"status": "deleted", "document_id": document_id}
