"""
test_patient_mgmt_and_document_intelligence.py - Comprehensive Phase 1-5 Test Suite
====================================================================================

Tests cover:
  1. Patient Management (Creation, editing, unique IDs, duplicate prevention, validation).
  2. Manual Medical Ingestion (Glucose, vitals, lab panels, diagnoses, unit conversions).
  3. Medical Document Uploads (Storage isolation, size limits, extension whitelist, download).
  4. Document Intelligence (PDF text extraction, OCR behavior, tabular preview, draft confirmation, cancellation).
  5. Digital Twin & Prediction Safety (Safe handling of newly created patients with insufficient history).
"""

import io
import json
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import Patient, GlucoseReading, VitalReading, LabResult, MedicalDocument
from app.services.storage import (
    LocalStorageProvider,
    storage_provider,
    FileValidationError,
)


@pytest.fixture
def test_db_session(tmp_path):
    """Isolated in-memory SQLite database session fixture."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(test_db_session, tmp_path, monkeypatch):
    """TestClient wired to isolated in-memory DB and temporary upload directory."""
    temp_upload_dir = tmp_path / "uploads"
    temp_upload_dir.mkdir(parents=True, exist_ok=True)
    temp_storage = LocalStorageProvider(upload_dir=str(temp_upload_dir))

    # Use temporary storage for the storage module and documents router.
    monkeypatch.setattr(
        "app.services.storage.storage_provider",
        temp_storage,
    )
    monkeypatch.setattr(
        "app.routers.documents.storage_provider",
        temp_storage,
    )

    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)


# ===========================================================================
# PHASE 1: PATIENT MANAGEMENT TESTS
# ===========================================================================

def test_create_patient_success(client, test_db_session):
    """Test registering a new patient with valid data."""
    payload = {
        "name": "Sunita Rao",
        "age": 48,
        "gender": "Female",
        "diabetes_type": "Type 2",
        "years_since_diagnosis": 4,
        "historical_diagnoses": "Mild Hypertension",
        "medical_history": "First diagnosed during routine health checkup in 2022.",
        "weight_kg": 68.0,
        "height_cm": 162.0,
    }

    res = client.post("/api/patients", json=payload)

    assert res.status_code == 201

    data = res.json()
    assert data["name"] == "Sunita Rao"
    assert data["age"] == 48
    assert data["calculated_bmi"] == round(68.0 / ((162.0 / 100) ** 2), 1)
    assert data["id"] is not None

    # Verify the patient was saved in the test database.
    db_patient = (
        test_db_session.query(Patient)
        .filter(Patient.id == data["id"])
        .first()
    )

    assert db_patient is not None
    assert db_patient.name == "Sunita Rao"


def test_create_patient_duplicate_rejection(client):
    """Test duplicate registration prevention."""
    payload = {
        "name": "Kavita Nair",
        "age": 39,
        "gender": "Female",
        "diabetes_type": "Type 1",
        "years_since_diagnosis": 12,
    }

    res1 = client.post("/api/patients", json=payload)
    assert res1.status_code == 201

    # A duplicate submission must return 409 Conflict.
    res2 = client.post("/api/patients", json=payload)

    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_create_patient_validation_errors(client):
    """Test invalid patient inputs."""

    # 1. Name too short.
    res = client.post(
        "/api/patients",
        json={
            "name": "A",
            "age": 40,
            "gender": "Male",
            "diabetes_type": "Type 2",
        },
    )
    assert res.status_code == 422

    # 2. Negative age.
    res = client.post(
        "/api/patients",
        json={
            "name": "Valid Name",
            "age": -5,
            "gender": "Male",
            "diabetes_type": "Type 2",
        },
    )
    assert res.status_code == 422

    # 3. Excessive weight.
    res = client.post(
        "/api/patients",
        json={
            "name": "Valid Name",
            "age": 40,
            "gender": "Male",
            "diabetes_type": "Type 2",
            "weight_kg": 999.0,
        },
    )
    assert res.status_code == 422


def test_update_patient_profile(client):
    """Test editing an existing patient's clinical profile."""
    p_res = client.post(
        "/api/patients",
        json={
            "name": "Amit Shah",
            "age": 55,
            "gender": "Male",
            "diabetes_type": "Type 2",
            "years_since_diagnosis": 6,
        },
    )

    assert p_res.status_code == 201
    p_id = p_res.json()["id"]

    update_res = client.put(
        f"/api/patients/{p_id}",
        json={
            "weight_kg": 82.5,
            "height_cm": 174.0,
            "historical_diagnoses": "Hypertension, Hyperlipidemia",
            "medical_history": "Started ACE inhibitor 2024.",
        },
    )

    assert update_res.status_code == 200

    updated = update_res.json()
    assert updated["weight_kg"] == 82.5
    assert updated["height_cm"] == 174.0
    assert "Hyperlipidemia" in updated["historical_diagnoses"]
    assert updated["calculated_bmi"] == round(82.5 / ((174.0 / 100) ** 2), 1)


# ===========================================================================
# PHASE 2: MANUAL MEDICAL INGESTION TESTS
# ===========================================================================

def test_manual_glucose_entry_mgdl_and_mmol(client, test_db_session):
    """Test glucose entry in mg/dL and mmol/L with standard conversion."""
    p = Patient(
        name="Test Patient",
        age=45,
        gender="Male",
        diabetes_type="Type 2",
    )
    test_db_session.add(p)
    test_db_session.commit()

    # 1. Entry in mg/dL.
    res_mg = client.post(
        "/api/readings/glucose",
        json={
            "patient_id": p.id,
            "value": 154.0,
            "unit": "mg/dL",
            "data_source": "manual",
        },
    )

    assert res_mg.status_code == 201
    assert res_mg.json()["value"] == 154.0
    assert res_mg.json()["data_source"] == "manual"

    # 2. Entry in mmol/L: 7.0 mmol/L is approximately 126.1 mg/dL.
    res_mmol = client.post(
        "/api/readings/glucose",
        json={
            "patient_id": p.id,
            "value": 7.0,
            "unit": "mmol/L",
            "data_source": "manual",
        },
    )

    assert res_mmol.status_code == 201
    assert abs(res_mmol.json()["value"] - 126.1) < 0.2
    assert res_mmol.json()["unit"] == "mmol/L"


def test_manual_glucose_future_timestamp_rejected(client, test_db_session):
    """Reject measurement timestamps situated in the future."""
    p = Patient(
        name="Future Time Patient",
        age=50,
        gender="Female",
        diabetes_type="Type 2",
    )
    test_db_session.add(p)
    test_db_session.commit()

    future_time = (
        datetime.now(timezone.utc) + timedelta(days=2)
    ).isoformat()

    res = client.post(
        "/api/readings/glucose",
        json={
            "patient_id": p.id,
            "value": 120.0,
            "timestamp": future_time,
        },
    )

    assert res.status_code == 422
    assert "future" in res.json()["detail"].lower()


def test_manual_vitals_entry(client, test_db_session):
    """Test manual vital-sign readings entry and validation."""
    p = Patient(
        name="Vitals Patient",
        age=33,
        gender="Male",
        diabetes_type="Type 1",
    )
    test_db_session.add(p)
    test_db_session.commit()

    res = client.post(
        "/api/readings/vitals",
        json={
            "patient_id": p.id,
            "heart_rate": 76.0,
            "hrv": 44.0,
            "data_source": "manual",
        },
    )

    assert res.status_code == 201
    assert res.json()["heart_rate"] == 76.0
    assert res.json()["hrv"] == 44.0
    assert res.json()["data_source"] == "manual"


def test_manual_lab_result_entry(client, test_db_session):
    """Test manually recording a clinical laboratory result."""
    p = Patient(
        name="Lab Patient",
        age=58,
        gender="Female",
        diabetes_type="Type 2",
    )
    test_db_session.add(p)
    test_db_session.commit()

    res = client.post(
        f"/api/patients/{p.id}/labs",
        json={
            "patient_id": p.id,
            "test_name": "HbA1c",
            "result": 7.2,
            "unit": "%",
            "reference_range": "< 5.7%",
            "lab_source": "Metropolitan Pathology Labs",
            "data_source": "manual",
        },
    )

    assert res.status_code == 201

    data = res.json()
    assert data["test_name"] == "HbA1c"
    assert data["result"] == 7.2
    assert data["is_synthetic"] is False
    assert data["data_source"] == "manual"
    assert data["lab_source"] == "Metropolitan Pathology Labs"


def test_manual_diagnosis_and_history_logging(client, test_db_session):
    """Test appending diagnoses and clinical encounter history."""
    p = Patient(
        name="Diagnosis Patient",
        age=62,
        gender="Male",
        diabetes_type="Type 2",
        historical_diagnoses="None",
    )
    test_db_session.add(p)
    test_db_session.commit()

    res = client.post(
        f"/api/patients/{p.id}/diagnoses",
        json={
            "patient_id": p.id,
            "diagnosis_name": "Diabetic Retinopathy (Background)",
            "date": "2026-04-10",
            "notes": "Annual dilated fundus exam revealed microaneurysms.",
            "status": "active",
        },
    )

    assert res.status_code == 200

    updated = res.json()
    assert "Diabetic Retinopathy" in updated["historical_diagnoses"]
    assert "microaneurysms" in updated["medical_history"]


# ===========================================================================
# PHASE 3: DOCUMENT UPLOAD & STORAGE TESTS
# ===========================================================================

def test_document_upload_csv(client, test_db_session):
    """Test uploading a CSV report and generating an unconfirmed draft."""
    p = Patient(
        name="CSV Patient",
        age=41,
        gender="Female",
        diabetes_type="Type 2",
    )
    test_db_session.add(p)
    test_db_session.commit()

    csv_content = (
        b"timestamp,glucose_mg_dl\n"
        b"2026-10-18T08:00:00,128\n"
        b"2026-10-18T08:15:00,135\n"
        b"2026-10-18T08:30:00,142\n"
    )

    res = client.post(
        "/api/documents/upload",
        data={
            "patient_id": p.id,
            "document_category": "cgm_export",
        },
        files={
            "file": (
                "cgm_readings.csv",
                io.BytesIO(csv_content),
                "text/csv",
            )
        },
    )

    assert res.status_code == 201

    data = res.json()
    assert data["original_filename"] == "cgm_readings.csv"
    assert data["is_confirmed"] is False
    assert data["processing_status"] == "completed"

    # Verify the preview endpoint returns candidate readings.
    doc_id = data["id"]
    prev_res = client.get(f"/api/documents/{doc_id}/preview")

    assert prev_res.status_code == 200

    preview = prev_res.json()
    assert "extraction" in preview
    assert len(preview["extraction"]["candidate_readings"]) == 3


def test_document_upload_unsupported_file_rejected(client, test_db_session):
    """Reject executable or unsupported formats such as .exe or .bin."""
    p = Patient(
        name="Bad File Patient",
        age=30,
        gender="Male",
        diabetes_type="Type 1",
    )
    test_db_session.add(p)
    test_db_session.commit()

    res = client.post(
        "/api/documents/upload",
        data={"patient_id": p.id},
        files={
            "file": (
                "malware.exe",
                io.BytesIO(b"MZ\x90\x00"),
                "application/octet-stream",
            )
        },
    )

    assert res.status_code == 422
    assert "Unsupported file extension" in res.json()["detail"]


def test_document_download(client, test_db_session):
    """Test downloading the uploaded document binary."""
    p = Patient(
        name="Download Patient",
        age=50,
        gender="Female",
        diabetes_type="Type 2",
    )
    test_db_session.add(p)
    test_db_session.commit()

    sample_text = (
        b"Patient: Download Patient\n"
        b"HbA1c: 6.8 %\n"
        b"Fasting Blood Glucose: 112 mg/dL\n"
    )

    upload_response = client.post(
        "/api/documents/upload",
        data={"patient_id": p.id},
        files={
            "file": (
                "lab_report.csv",
                io.BytesIO(sample_text),
                "text/csv",
            )
        },
    )

    assert upload_response.status_code == 201
    doc_id = upload_response.json()["id"]

    download_response = client.get(
        f"/api/documents/{doc_id}/download"
    )

    assert download_response.status_code == 200
    assert download_response.content == sample_text


# ===========================================================================
# PHASE 4: DOCUMENT INTELLIGENCE, PREVIEW & CONFIRMATION TESTS
# ===========================================================================

def test_document_confirmation_saves_to_ehr(client, test_db_session):
    """Test reviewing extracted labs and committing them into the active EHR."""
    p = Patient(
        name="Review Patient",
        age=54,
        gender="Male",
        diabetes_type="Type 2",
    )
    test_db_session.add(p)
    test_db_session.commit()

    sample_doc = (
        b"Patient: Review Patient\n"
        b"HbA1c: 7.4 %\n"
        b"Total Cholesterol: 195 mg/dL\n"
    )

    upload_response = client.post(
        "/api/documents/upload",
        data={"patient_id": p.id},
        files={
            "file": (
                "lab_review.csv",
                io.BytesIO(sample_doc),
                "text/csv",
            )
        },
    )

    assert upload_response.status_code == 201
    doc_id = upload_response.json()["id"]

    confirm_payload = {
        "confirmed_labs": [
            {
                "patient_id": p.id,
                "test_name": "HbA1c",
                "result": 7.4,
                "unit": "%",
                "reference_range": "< 5.7%",
            },
            {
                "patient_id": p.id,
                "test_name": "Total Cholesterol",
                "result": 195.0,
                "unit": "mg/dL",
                "reference_range": "< 200 mg/dL",
            },
        ],
        "confirmed_readings": [],
        "clinical_notes": "Reviewed by clinician. Target A1c < 7.0%.",
    }

    confirm_response = client.post(
        f"/api/documents/{doc_id}/confirm",
        json=confirm_payload,
    )

    assert confirm_response.status_code == 200
    assert confirm_response.json()["confirmed_labs_count"] == 2

    # Verify lab results exist in the active lab_results table.
    labs_response = client.get(f"/api/patients/{p.id}/labs")

    assert labs_response.status_code == 200

    test_names = [
        item["test_name"]
        for item in labs_response.json()
    ]

    assert "HbA1c" in test_names
    assert "Total Cholesterol" in test_names

    # Duplicate confirmation must be prevented.
    second_confirm = client.post(
        f"/api/documents/{doc_id}/confirm",
        json=confirm_payload,
    )

    assert second_confirm.status_code == 400
    assert "already been confirmed" in second_confirm.json()["detail"]


def test_document_cancellation_does_not_save_to_ehr(client, test_db_session):
    """Test canceling a draft report leaves the active EHR untouched."""
    p = Patient(
        name="Cancel Patient",
        age=47,
        gender="Female",
        diabetes_type="Type 1",
    )
    test_db_session.add(p)
    test_db_session.commit()

    upload_response = client.post(
        "/api/documents/upload",
        data={"patient_id": p.id},
        files={
            "file": (
                "unwanted.csv",
                io.BytesIO(b"HbA1c,8.5\n"),
                "text/csv",
            )
        },
    )

    assert upload_response.status_code == 201
    doc_id = upload_response.json()["id"]

    cancel_response = client.post(
        f"/api/documents/{doc_id}/cancel"
    )

    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"

    # Active labs must remain empty.
    labs_response = client.get(f"/api/patients/{p.id}/labs")

    assert labs_response.status_code == 200
    assert len(labs_response.json()) == 0


def test_patient_name_mismatch_warning(client, test_db_session):
    """Verify that a document containing a different patient name generates a warning."""
    p = Patient(
        name="Deepak Joshi",
        age=50,
        gender="Male",
        diabetes_type="Type 2",
    )
    test_db_session.add(p)
    test_db_session.commit()

    doc_content = (
        b"Patient Name: Ananya Sharma\n"
        b"Date: 2026-10-10\n"
        b"HbA1c: 6.9 %\n"
    )

    upload_response = client.post(
        "/api/documents/upload",
        data={"patient_id": p.id},
        files={
            "file": (
                "ananya_labs.csv",
                io.BytesIO(doc_content),
                "text/csv",
            )
        },
    )

    assert upload_response.status_code == 201
    doc_id = upload_response.json()["id"]

    preview_response = client.get(
        f"/api/documents/{doc_id}/preview"
    )

    assert preview_response.status_code == 200

    extraction = preview_response.json()["extraction"]

    assert extraction["patient_name_match"] is False
    assert any(
        "MISMATCH" in warning
        for warning in extraction["warnings"]
    )


# ===========================================================================
# PHASE 5: DIGITAL TWIN INTEGRATION & PREDICTION SAFETY
# ===========================================================================

def test_new_patient_insufficient_history_safety(client, test_db_session):
    """A new patient without telemetry returns a safe insufficient-data response."""
    p = Patient(
        name="New Empty Patient",
        age=40,
        gender="Male",
        diabetes_type="Type 2",
    )
    test_db_session.add(p)
    test_db_session.commit()

    # Prediction must safely return 422 when no readings exist.
    prediction_response = client.post(
        "/api/predictions/glucose-spike",
        json={"patient_id": p.id},
    )

    assert prediction_response.status_code == 422
    assert (
        "no valid glucose readings"
        in prediction_response.json()["detail"].lower()
    )

    # Digital twin intelligence should return an empty baseline safely.
    twin_response = client.get(
        f"/api/digital-twin/{p.id}"
    )

    assert twin_response.status_code == 200

    twin_data = twin_response.json()

    assert twin_data["data_freshness_status"] == "no_data"
    assert twin_data["latest_glucose"] is None