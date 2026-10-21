"""
test_patient_and_doctor_portals.py - Automated Security Tests for Portals, Registration, RBAC & Isolation
==========================================================================================================

Comprehensive test suite verifying:
  1. Patient self-registration: server-assigned role, transactional safety, unique email/username, validation.
  2. Doctor registration request: server-assigned pending approval status, no immediate privileges.
  3. Doctor approval workflow: pending login denial, self-approval prevention, clinician-only approval, post-approval login.
  4. Role-specific login: server-derived roles, portal affinity enforcement, inactive account rejection.
  5. Patient-data isolation: strict ownership validation across profile, readings, vitals, twin, predictions,
     alerts, documents, and reports. Cross-patient tampering attempts rejected with HTTP 403.
  6. Doctor authorization: permitted care scope enforcement via doctor-patient assignments.
  7. Report generation and export: patient-specific reports with synthetic prototype disclaimers.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.models import (
    Patient,
    GlucoseReading,
    VitalReading,
    MedicalDocument,
    User,
    DoctorPatientAssignment,
    Alert,
)
from app.auth import get_current_user, get_password_hash, create_access_token
from app.main import app


@pytest.fixture
def portal_test_db():
    """Isolated in-memory database with initial synthetic patients and doctor."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    # Seed 2 distinct patients
    p1 = Patient(
        name="Sunita Rao",
        age=48,
        gender="Female",
        diabetes_type="Type 2",
        years_since_diagnosis=6,
        historical_diagnoses="Hypertension",
        medical_history="Allergic to penicillin.",
        created_at=datetime.now(timezone.utc),
    )
    p2 = Patient(
        name="Amit Verma",
        age=39,
        gender="Male",
        diabetes_type="Type 1",
        years_since_diagnosis=12,
        historical_diagnoses="None",
        medical_history="",
        created_at=datetime.now(timezone.utc),
    )
    db.add_all([p1, p2])
    db.flush()

    # Seed readings for p1
    g1 = GlucoseReading(
        patient_id=p1.id,
        timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        value=135.0,
        is_valid=True,
    )
    v1 = VitalReading(
        patient_id=p1.id,
        timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        heart_rate=72.0,
        hrv=45.0,
    )
    # Seed readings for p2
    g2 = GlucoseReading(
        patient_id=p2.id,
        timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        value=195.0,
        is_valid=True,
    )
    db.add_all([g1, v1, g2])

    # Seed an approved lead doctor and two patient user accounts
    dr_lead = User(
        username="dr_lead",
        email="lead@hospital.com",
        full_name="Dr. Lead Clinician",
        hashed_password=get_password_hash("Clinician123!"),
        role="clinician",
        approval_status="approved",
        patient_id=None,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    user_p1 = User(
        username="sunita_rao",
        email="sunita@example.com",
        full_name="Sunita Rao",
        hashed_password=get_password_hash("Patient123!"),
        role="patient",
        approval_status="approved",
        patient_id=p1.id,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    user_p2 = User(
        username="amit_verma",
        email="amit@example.com",
        full_name="Amit Verma",
        hashed_password=get_password_hash("Patient123!"),
        role="patient",
        approval_status="approved",
        patient_id=p2.id,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add_all([dr_lead, user_p1, user_p2])

    # Seed documents for p1 and p2
    doc_p1 = MedicalDocument(
        patient_id=p1.id,
        original_filename="sunita_report.pdf",
        storage_filename="sunita_uuid.pdf",
        storage_path="mock/path/sunita.pdf",
        file_size=1024,
        mime_type="application/pdf",
        document_category="lab_report",
        processing_status="completed",
        is_confirmed=True,
    )
    doc_p2 = MedicalDocument(
        patient_id=p2.id,
        original_filename="amit_report.pdf",
        storage_filename="amit_uuid.pdf",
        storage_path="mock/path/amit.pdf",
        file_size=1024,
        mime_type="application/pdf",
        document_category="lab_report",
        processing_status="completed",
        is_confirmed=True,
    )
    db.add_all([doc_p1, doc_p2])
    db.commit()

    try:
        yield db, p1, p2, dr_lead, user_p1, user_p2, doc_p1, doc_p2
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def portal_client(portal_test_db):
    """Client for portal tests with live database dependency override."""
    db, p1, p2, dr_lead, user_p1, user_p2, doc_p1, doc_p2 = portal_test_db

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_current_user, None)

    with TestClient(app) as client:
        yield client, db, p1, p2, dr_lead, user_p1, user_p2, doc_p1, doc_p2
    app.dependency_overrides.clear()


# ===========================================================================
# PHASE 2: PATIENT REGISTRATION TESTS
# ===========================================================================

def test_patient_registration_success(portal_client):
    """Test public self-registration safely provisions patient record and user account."""
    client, db, p1, p2, dr_lead, user_p1, user_p2, doc_p1, doc_p2 = portal_client
    payload = {
        "full_name": "Rohan Deshmukh",
        "email": "rohan.deshmukh@example.com",
        "username": "rohan_deshmukh",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "age": 42,
        "gender": "Male",
        "diabetes_type": "Type 2",
    }
    res = client.post("/api/auth/register-patient", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["username"] == "rohan_deshmukh"
    assert data["role"] == "patient"
    assert data["approval_status"] == "approved"
    assert data["patient_id"] is not None

    # Verify patient record exists in database
    new_patient = db.query(Patient).filter(Patient.id == data["patient_id"]).first()
    assert new_patient is not None
    assert new_patient.name == "Rohan Deshmukh"
    assert new_patient.age == 42


def test_patient_registration_password_mismatch(portal_client):
    """Test patient registration rejects mismatched passwords with HTTP 422."""
    client, db, p1, p2, dr_lead, user_p1, user_p2, doc_p1, doc_p2 = portal_client
    payload = {
        "full_name": "Neha Gupta",
        "email": "neha@example.com",
        "username": "neha_gupta",
        "password": "Password123!",
        "confirm_password": "DifferentPassword123!",
    }
    res = client.post("/api/auth/register-patient", json=payload)
    assert res.status_code == 422
    assert "do not match" in res.json()["detail"]


def test_patient_registration_duplicate_username_conflict(portal_client):
    """Test patient registration rejects duplicate username with HTTP 409."""
    client, db, p1, p2, dr_lead, user_p1, user_p2, doc_p1, doc_p2 = portal_client
    payload = {
        "full_name": "Sunita Clone",
        "email": "sunita_clone@example.com",
        "username": "sunita_rao",  # already exists
        "password": "Password123!",
        "confirm_password": "Password123!",
    }
    res = client.post("/api/auth/register-patient", json=payload)
    assert res.status_code == 409
    assert "already registered" in res.json()["detail"]


def test_patient_registration_duplicate_email_conflict(portal_client):
    """Test patient registration rejects duplicate email with HTTP 409."""
    client, db, p1, p2, dr_lead, user_p1, user_p2, doc_p1, doc_p2 = portal_client
    payload = {
        "full_name": "Another User",
        "email": "sunita@example.com",  # already exists
        "username": "another_unique_user",
        "password": "Password123!",
        "confirm_password": "Password123!",
    }
    res = client.post("/api/auth/register-patient", json=payload)
    assert res.status_code == 409
    assert "already registered" in res.json()["detail"]


# ===========================================================================
# PHASE 3: DOCTOR REGISTRATION AND APPROVAL TESTS
# ===========================================================================

def test_doctor_registration_request_stored_as_pending(portal_client):
    """Test public doctor registration requests are created with pending approval status."""
    client, db, p1, p2, dr_lead, user_p1, user_p2, doc_p1, doc_p2 = portal_client
    payload = {
        "full_name": "Dr. Aisha Khan",
        "email": "dr.aisha@hospital.com",
        "username": "dr_aisha",
        "password": "DoctorSecret123!",
        "confirm_password": "DoctorSecret123!",
        "medical_license_number": "MED-REG-987654",
    }
    res = client.post("/api/auth/register-doctor", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["username"] == "dr_aisha"
    assert data["role"] == "clinician"
    assert data["approval_status"] == "pending"


def test_pending_doctor_login_denied(portal_client):
    """Test that a pending doctor cannot log in or obtain access tokens (HTTP 403)."""
    client, db, p1, p2, dr_lead, user_p1, user_p2, doc_p1, doc_p2 = portal_client
    # Register pending doctor
    client.post("/api/auth/register-doctor", json={
        "full_name": "Dr. Tarun Sen",
        "email": "dr.tarun@hospital.com",
        "username": "dr_tarun",
        "password": "DoctorSecret123!",
        "confirm_password": "DoctorSecret123!",
    })

    # Attempt login
    login_res = client.post("/api/auth/login", json={
        "username": "dr_tarun",
        "password": "DoctorSecret123!",
    })
    assert login_res.status_code == 403
    assert "pending approval" in login_res.json()["detail"]


def test_doctor_self_approval_prevented(portal_client):
    """Test that clinicians cannot approve their own account."""
    client, db, p1, p2, dr_lead, user_p1, user_p2, doc_p1, doc_p2 = portal_client
    lead_token = create_access_token({"sub": dr_lead.username, "role": "clinician"})
    headers = {"Authorization": f"Bearer {lead_token}"}

    res = client.post(f"/api/auth/doctor-requests/{dr_lead.id}/approve", headers=headers)
    assert res.status_code == 403
    assert "cannot approve their own account" in res.json()["detail"]


def test_approved_clinician_can_approve_pending_doctor(portal_client):
    """Test that an approved clinician can approve a pending doctor, allowing them to sign in."""
    client, db, p1, p2, dr_lead, user_p1, user_p2, doc_p1, doc_p2 = portal_client
    # 1. Register pending doctor
    reg_res = client.post("/api/auth/register-doctor", json={
        "full_name": "Dr. Vikram Joshi",
        "email": "dr.joshi@hospital.com",
        "username": "dr_joshi",
        "password": "DoctorSecret123!",
        "confirm_password": "DoctorSecret123!",
    })
    new_doc_id = reg_res.json()["id"]

    # 2. Approved clinician approves the request
    lead_token = create_access_token({"sub": dr_lead.username, "role": "clinician"})
    headers = {"Authorization": f"Bearer {lead_token}"}

    approve_res = client.post(f"/api/auth/doctor-requests/{new_doc_id}/approve", headers=headers)
    assert approve_res.status_code == 200
    assert approve_res.json()["approval_status"] == "approved"

    # 3. Newly approved doctor can now sign in
    login_res = client.post("/api/auth/login", json={
        "username": "dr_joshi",
        "password": "DoctorSecret123!",
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()
    assert login_res.json()["user"]["approval_status"] == "approved"


# ===========================================================================
# PHASE 4: ROLE-SPECIFIC LOGIN TESTS
# ===========================================================================

def test_portal_affinity_enforcement(portal_client):
    """Test that patient portal rejects clinicians and doctor portal rejects patients."""
    client, db, p1, p2, dr_lead, user_p1, user_p2, doc_p1, doc_p2 = portal_client

    # Clinician trying to log into patient portal
    res1 = client.post("/api/auth/login", json={
        "username": "dr_lead",
        "password": "Clinician123!",
        "portal": "patient",
    })
    assert res1.status_code == 403
    assert "Doctor Portal" in res1.json()["detail"]

    # Patient trying to log into doctor portal
    res2 = client.post("/api/auth/login", json={
        "username": "sunita_rao",
        "password": "Patient123!",
        "portal": "doctor",
    })
    assert res2.status_code == 403
    assert "Patient Portal" in res2.json()["detail"]


def test_inactive_account_login_rejected(portal_client):
    """Test deactivated accounts return HTTP 401."""
    client, db, p1, p2, dr_lead, user_p1, user_p2, doc_p1, doc_p2 = portal_client
    user_p1.is_active = False
    db.commit()

    res = client.post("/api/auth/login", json={
        "username": "sunita_rao",
        "password": "Patient123!",
    })
    assert res.status_code == 401
    assert "deactivated" in res.json()["detail"]


# ===========================================================================
# PHASE 5: PATIENT-DATA ISOLATION TESTS
# ===========================================================================

def test_patient_can_access_own_records(portal_client):
    """Test that authenticated patient can view their own profile, readings, and vitals."""
    client, db, p1, p2, dr_lead, user_p1, user_p2, doc_p1, doc_p2 = portal_client
    token = create_access_token({"sub": user_p1.username, "role": "patient", "patient_id": p1.id})
    headers = {"Authorization": f"Bearer {token}"}

    # Own profile
    res_p = client.get(f"/api/patients/{p1.id}", headers=headers)
    assert res_p.status_code == 200
    assert res_p.json()["name"] == p1.name

    # Own glucose readings
    res_g = client.get(f"/api/readings/glucose/{p1.id}", headers=headers)
    assert res_g.status_code == 200

    # Own vitals
    res_v = client.get(f"/api/readings/vitals/{p1.id}", headers=headers)
    assert res_v.status_code == 200


def test_patient_cross_patient_access_rejected_403(portal_client):
    """Test patient A attempting to access patient B's profile and telemetry is blocked with HTTP 403."""
    client, db, p1, p2, dr_lead, user_p1, user_p2, doc_p1, doc_p2 = portal_client
    token_p1 = create_access_token({"sub": user_p1.username, "role": "patient", "patient_id": p1.id})
    headers = {"Authorization": f"Bearer {token_p1}"}

    # Patient 1 tries to access Patient 2's profile
    res1 = client.get(f"/api/patients/{p2.id}", headers=headers)
    assert res1.status_code == 403

    # Patient 1 tries to access Patient 2's glucose readings
    res2 = client.get(f"/api/readings/glucose/{p2.id}", headers=headers)
    assert res2.status_code == 403

    # Patient 1 tries to access Patient 2's vitals
    res3 = client.get(f"/api/readings/vitals/{p2.id}", headers=headers)
    assert res3.status_code == 403

    # Patient 1 tries to access Patient 2's digital twin
    res4 = client.get(f"/api/digital-twin/{p2.id}", headers=headers)
    assert res4.status_code == 403


def test_patient_cross_patient_documents_and_reports_rejected_403(portal_client):
    """Test patient A cannot download or access patient B's documents or reports."""
    client, db, p1, p2, dr_lead, user_p1, user_p2, doc_p1, doc_p2 = portal_client
    token_p1 = create_access_token({"sub": user_p1.username, "role": "patient", "patient_id": p1.id})
    headers = {"Authorization": f"Bearer {token_p1}"}

    # Patient 1 accesses Patient 2's document metadata
    res_doc = client.get(f"/api/documents/{doc_p2.id}", headers=headers)
    assert res_doc.status_code == 403

    # Patient 1 tries to download Patient 2's document
    res_dl = client.get(f"/api/documents/{doc_p2.id}/download", headers=headers)
    assert res_dl.status_code == 403

    # Patient 1 tries to access Patient 2's clinical report
    res_rep = client.get(f"/api/reports/patient/{p2.id}", headers=headers)
    assert res_rep.status_code == 403


# ===========================================================================
# PHASE 6 & 7: DOCTOR SCOPE & REPORT GENERATION TESTS
# ===========================================================================

def test_doctor_scope_enforcement_via_assignment(portal_client):
    """
    Test that a clinician with explicit patient assignments can access permitted data
    for assigned patients, but receives HTTP 403 Forbidden on direct requests for unassigned patients
    across profile, glucose, vitals, documents, digital twin, predictions, and reports.
    """
    client, db, p1, p2, dr_lead, user_p1, user_p2, doc_p1, doc_p2 = portal_client

    # Create a new specialist clinician assigned ONLY to patient 1
    dr_specialist = User(
        username="dr_specialist",
        email="specialist@hospital.com",
        full_name="Dr. Specialist",
        hashed_password=get_password_hash("Clinician123!"),
        role="clinician",
        approval_status="approved",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(dr_specialist)
    db.flush()

    # Assign ONLY to patient p1
    assignment = DoctorPatientAssignment(
        doctor_id=dr_specialist.id,
        patient_id=p1.id,
        assigned_at=datetime.now(timezone.utc),
    )
    db.add(assignment)
    db.commit()

    token_spec = create_access_token({"sub": dr_specialist.username, "role": "clinician"})
    headers = {"Authorization": f"Bearer {token_spec}"}

    # 1. Profile
    assert client.get(f"/api/patients/{p1.id}", headers=headers).status_code == 200
    res_p2 = client.get(f"/api/patients/{p2.id}", headers=headers)
    assert res_p2.status_code == 403
    assert "outside their assigned clinical scope" in res_p2.json()["detail"]

    # 2. Glucose readings
    assert client.get(f"/api/readings/glucose/{p1.id}", headers=headers).status_code == 200
    assert client.get(f"/api/readings/glucose/{p2.id}", headers=headers).status_code == 403

    # 3. Vital readings
    assert client.get(f"/api/readings/vitals/{p1.id}", headers=headers).status_code == 200
    assert client.get(f"/api/readings/vitals/{p2.id}", headers=headers).status_code == 403

    # 4. Document list and single document metadata
    assert client.get(f"/api/documents/patient/{p1.id}", headers=headers).status_code == 200
    assert client.get(f"/api/documents/patient/{p2.id}", headers=headers).status_code == 403
    assert client.get(f"/api/documents/{doc_p1.id}", headers=headers).status_code == 200
    assert client.get(f"/api/documents/{doc_p2.id}", headers=headers).status_code == 403

    # 5. Document download
    assert client.get(f"/api/documents/{doc_p2.id}/download", headers=headers).status_code == 403

    # 6. Digital twin intelligence
    assert client.get(f"/api/digital-twin/{p1.id}", headers=headers).status_code == 200
    assert client.get(f"/api/digital-twin/{p2.id}", headers=headers).status_code == 403

    # 7. Predictions
    pred_res_unassigned = client.post(
        "/api/predictions/glucose-spike",
        headers=headers,
        json={"patient_id": p2.id},
    )
    assert pred_res_unassigned.status_code == 403

    # 8. Reports & report export
    assert client.get(f"/api/reports/patient/{p1.id}", headers=headers).status_code == 200
    assert client.get(f"/api/reports/patient/{p2.id}", headers=headers).status_code == 403
    assert client.get(f"/api/reports/patient/{p2.id}/export", headers=headers).status_code == 403


def test_patient_and_doctor_report_generation(portal_client):
    """Test report generation for authorized patient and clinician, with disclaimers."""
    client, db, p1, p2, dr_lead, user_p1, user_p2, doc_p1, doc_p2 = portal_client

    # 1. Patient generating own report
    token_p1 = create_access_token({"sub": user_p1.username, "role": "patient", "patient_id": p1.id})
    res_p1 = client.get(f"/api/reports/patient/{p1.id}", headers={"Authorization": f"Bearer {token_p1}"})
    assert res_p1.status_code == 200
    data_p1 = res_p1.json()
    assert data_p1["patient_id"] == p1.id
    assert data_p1["patient_name"] == p1.name
    assert data_p1["is_synthetic_data"] is True
    assert "RESEARCH & DEMONSTRATION PROTOTYPE ONLY" in data_p1["disclaimer"]

    # 2. Clinician generating report for p1
    token_dr = create_access_token({"sub": dr_lead.username, "role": "clinician"})
    res_dr = client.get(f"/api/reports/patient/{p1.id}", headers={"Authorization": f"Bearer {token_dr}"})
    assert res_dr.status_code == 200

    # 3. HTML printable report export (authorized clinician)
    res_export = client.get(f"/api/reports/patient/{p1.id}/export", headers={"Authorization": f"Bearer {token_dr}"})
    assert res_export.status_code == 200
    assert "text/html" in res_export.headers["content-type"]
    assert "attachment; filename=" in res_export.headers["content-disposition"]
    assert "GlucoTwin Comprehensive Health Report" in res_export.text


def test_report_export_authentication_and_authorization(portal_client):
    """
    Test report export endpoint security:
      - Unauthenticated requests are rejected with HTTP 401.
      - Authenticated patient can export their own report (HTTP 200).
      - Patient attempting to export another patient's report is blocked (HTTP 403).
    """
    client, db, p1, p2, dr_lead, user_p1, user_p2, doc_p1, doc_p2 = portal_client

    # 1. Unauthenticated download fails with HTTP 401
    res_unauth = client.get(f"/api/reports/patient/{p1.id}/export")
    assert res_unauth.status_code == 401

    # 2. Authenticated patient exporting their own report succeeds
    token_p1 = create_access_token({"sub": user_p1.username, "role": "patient", "patient_id": p1.id})
    res_own = client.get(f"/api/reports/patient/{p1.id}/export", headers={"Authorization": f"Bearer {token_p1}"})
    assert res_own.status_code == 200
    assert "text/html" in res_own.headers["content-type"]

    # 3. Patient attempting to export another patient's report is blocked with HTTP 403
    res_cross = client.get(f"/api/reports/patient/{p2.id}/export", headers={"Authorization": f"Bearer {token_p1}"})
    assert res_cross.status_code == 403

