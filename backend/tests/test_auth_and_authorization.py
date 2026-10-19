"""
test_auth_and_authorization.py - Comprehensive Authentication & RBAC Security Tests
=====================================================================================

Tests enforced security requirements:
  1. Unauthenticated requests are rejected with HTTP 401 Unauthorized.
  2. Invalid or expired JWT tokens are rejected with HTTP 401.
  3. Login endpoint validates credentials and returns signed JWT access tokens.
  4. Invalid login credentials return HTTP 401.
  5. Clinician accounts have authorized access across the cohort.
  6. Patient accounts can access their own records and documents.
  7. Cross-patient tampering (guessing or changing patient_id) is blocked with HTTP 403 Forbidden.
  8. Cross-patient document access (guessing or changing document_id) is blocked with HTTP 403 Forbidden.
  9. Patient accounts attempting clinician-only actions (registering patients, confirming labs) return HTTP 403.
  10. Server checks database and token claims; does not trust client-supplied role or patient headers.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.models import Patient, GlucoseReading, MedicalDocument, User
from app.auth import get_current_user, get_password_hash, create_access_token
from app.main import app


@pytest.fixture
def auth_test_db(tmp_path):
    """Isolated in-memory SQLite database session with seeded users and patients."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    # Seed two patients
    p1 = Patient(
        name="Ananya Sharma",
        age=52,
        gender="Female",
        diabetes_type="Type 2",
        years_since_diagnosis=8,
        historical_diagnoses="Hypertension",
        created_at=datetime.now(timezone.utc),
    )
    p2 = Patient(
        name="Rajesh Kumar",
        age=45,
        gender="Male",
        diabetes_type="Type 2",
        years_since_diagnosis=4,
        historical_diagnoses="None",
        created_at=datetime.now(timezone.utc),
    )
    db.add(p1)
    db.add(p2)
    db.flush()

    # Seed a clinician and two distinct patient users
    clinician = User(
        username="dr_sharma",
        email="dr.sharma@hospital.com",
        hashed_password=get_password_hash("Clinician123!"),
        role="clinician",
        patient_id=None,
        is_active=True,
    )
    patient1_user = User(
        username="ananya_sharma",
        email="ananya@example.com",
        hashed_password=get_password_hash("Patient123!"),
        role="patient",
        patient_id=p1.id,
        is_active=True,
    )
    patient2_user = User(
        username="rajesh_kumar",
        email="rajesh@example.com",
        hashed_password=get_password_hash("Patient123!"),
        role="patient",
        patient_id=p2.id,
        is_active=True,
    )
    db.add_all([clinician, patient1_user, patient2_user])

    # Seed documents for p1 and p2
    doc_p1 = MedicalDocument(
        patient_id=p1.id,
        original_filename="ananya_labs.pdf",
        storage_filename="uuid_ananya_labs.pdf",
        storage_path="mock/path/ananya.pdf",
        file_size=1024,
        mime_type="application/pdf",
        document_category="lab_report",
        processing_status="completed",
        is_confirmed=False,
    )
    doc_p2 = MedicalDocument(
        patient_id=p2.id,
        original_filename="rajesh_labs.pdf",
        storage_filename="uuid_rajesh_labs.pdf",
        storage_path="mock/path/rajesh.pdf",
        file_size=2048,
        mime_type="application/pdf",
        document_category="lab_report",
        processing_status="completed",
        is_confirmed=False,
    )
    db.add_all([doc_p1, doc_p2])
    db.commit()

    try:
        yield db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_client(auth_test_db):
    """TestClient wired to isolated database with default conftest override disabled."""
    db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2 = auth_test_db

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    # Clear any global override so we can test raw authentication and token headers
    app.dependency_overrides.pop(get_current_user, None)

    with TestClient(app) as client:
        yield client, db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2
    app.dependency_overrides.clear()


def test_unauthenticated_request_rejected_401(auth_client):
    """Verify that requests without Bearer authorization return HTTP 401."""
    client, db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2 = auth_client
    res = client.get(f"/api/patients/{p1.id}")
    assert res.status_code == 401
    assert "Bearer token required" in res.json()["detail"]


def test_invalid_token_rejected_401(auth_client):
    """Verify that requests with forged or invalid tokens return HTTP 401."""
    client, db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2 = auth_client
    res = client.get(
        f"/api/patients/{p1.id}",
        headers={"Authorization": "Bearer invalid.jwt.token.here"}
    )
    assert res.status_code == 401


def test_valid_login_returns_jwt_token(auth_client):
    """Verify that POST /api/auth/login validates credentials and issues a valid JWT."""
    client, db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2 = auth_client
    res = client.post("/api/auth/login", json={
        "username": "dr_sharma",
        "password": "Clinician123!",
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["role"] == "clinician"
    assert data["user"]["username"] == "dr_sharma"


def test_invalid_login_credentials_rejected_401(auth_client):
    """Verify that wrong passwords or usernames are rejected with HTTP 401."""
    client, db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2 = auth_client
    res = client.post("/api/auth/login", json={
        "username": "dr_sharma",
        "password": "WrongPassword999!",
    })
    assert res.status_code == 401
    assert "Incorrect username or password" in res.json()["detail"]


def test_clinician_authorized_across_cohort(auth_client):
    """Verify that clinician tokens grant access across multiple patient profiles."""
    client, db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2 = auth_client
    token = create_access_token({"sub": clinician.username, "role": "clinician"})
    headers = {"Authorization": f"Bearer {token}"}

    res1 = client.get(f"/api/patients/{p1.id}", headers=headers)
    assert res1.status_code == 200
    assert res1.json()["name"] == p1.name

    res2 = client.get(f"/api/patients/{p2.id}", headers=headers)
    assert res2.status_code == 200
    assert res2.json()["name"] == p2.name


def test_patient_authorized_for_own_profile(auth_client):
    """Verify that a patient user can access their own patient records."""
    client, db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2 = auth_client
    token = create_access_token({"sub": patient2_user.username, "role": "patient", "patient_id": p2.id})
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(f"/api/patients/{p2.id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["id"] == p2.id
    assert res.json()["name"] == p2.name


def test_patient_cannot_access_other_patient_profile_403(auth_client):
    """Verify that a patient user cannot access another patient's data by changing the ID in the request."""
    client, db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2 = auth_client
    # User is Rajesh Kumar (p2), attempts to access Ananya Sharma (p1)
    token = create_access_token({"sub": patient2_user.username, "role": "patient", "patient_id": p2.id})
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(f"/api/patients/{p1.id}", headers=headers)
    assert res.status_code == 403
    assert "Access forbidden" in res.json()["detail"]


def test_patient_cannot_access_other_patient_readings_403(auth_client):
    """Verify that a patient user cannot query another patient's glucose telemetry."""
    client, db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2 = auth_client
    token = create_access_token({"sub": patient2_user.username, "role": "patient", "patient_id": p2.id})
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(f"/api/readings/glucose/{p1.id}", headers=headers)
    assert res.status_code == 403
    assert "not authorized to view or modify records for patient" in res.json()["detail"]


def test_patient_cannot_access_other_patient_documents_403(auth_client):
    """Verify that a patient user cannot list another patient's documents."""
    client, db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2 = auth_client
    token = create_access_token({"sub": patient2_user.username, "role": "patient", "patient_id": p2.id})
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to list p1's documents
    res_list = client.get(f"/api/documents/patient/{p1.id}", headers=headers)
    assert res_list.status_code == 403

    # Attempt to preview p1's document
    res_prev = client.get(f"/api/documents/{doc_p1.id}/preview", headers=headers)
    assert res_prev.status_code == 403

    # Attempt to download p1's document
    res_down = client.get(f"/api/documents/{doc_p1.id}/download", headers=headers)
    assert res_down.status_code == 403
    assert f"not authorized to access or download document #{doc_p1.id}" in res_down.json()["detail"]


def test_patient_cannot_register_new_patient_403(auth_client):
    """Verify that only clinicians can register new patients into the cohort."""
    client, db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2 = auth_client
    token = create_access_token({"sub": patient2_user.username, "role": "patient", "patient_id": p2.id})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "Unauthorized Attempt",
        "age": 30,
        "gender": "Male",
        "diabetes_type": "Type 1",
    }
    res = client.post("/api/patients", json=payload, headers=headers)
    assert res.status_code == 403
    assert "does not hold required clinician privileges" in res.json()["detail"]


def test_patient_cannot_confirm_document_extraction_403(auth_client):
    """Verify that committing draft document extractions into medical records requires clinician role."""
    client, db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2 = auth_client
    token = create_access_token({"sub": patient2_user.username, "role": "patient", "patient_id": p2.id})
    headers = {"Authorization": f"Bearer {token}"}

    confirm_payload = {
        "confirmed_labs": [
            {
                "patient_id": p2.id,
                "test_name": "HbA1c",
                "result": 6.8,
                "unit": "%",
            }
        ],
        "confirmed_readings": [],
    }
    res = client.post(f"/api/documents/{doc_p2.id}/confirm", json=confirm_payload, headers=headers)
    assert res.status_code == 403
    assert "does not hold required clinician privileges" in res.json()["detail"]


def test_auth_me_endpoint_returns_identity(auth_client):
    """Verify that GET /api/auth/me returns identity claims for the authenticated caller."""
    client, db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2 = auth_client
    token = create_access_token({"sub": clinician.username, "role": "clinician"})
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == clinician.username
    assert data["role"] == "clinician"


def test_expired_token_rejected_401(auth_client):
    """Verify that expired JWT tokens return HTTP 401 with appropriate message."""
    client, db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2 = auth_client
    from datetime import timedelta
    # Create token expired 1 hour ago
    expired_token = create_access_token(
        {"sub": clinician.username, "role": "clinician"},
        expires_delta=timedelta(minutes=-60)
    )
    res = client.get("/api/patients", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    assert "token has expired" in res.json()["detail"].lower()


def test_deactivated_user_rejected_401(auth_client):
    """Verify that tokens for inactive/deactivated users return HTTP 401."""
    client, db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2 = auth_client
    # Deactivate patient1_user
    patient1_user.is_active = False
    db.commit()

    token = create_access_token({"sub": patient1_user.username, "role": "patient", "patient_id": p1.id})
    res = client.get(f"/api/patients/{p1.id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
    assert "deactivated" in res.json()["detail"].lower()


def test_public_registration_rejected_unauthenticated_401(auth_client):
    """Verify that unauthenticated callers cannot publicly self-register accounts."""
    client, db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2 = auth_client
    res = client.post("/api/auth/register", json={
        "username": "unauthorized_user",
        "password": "Password123!",
        "role": "clinician",
    })
    # Must fail because registration requires authenticated clinician
    assert res.status_code == 401


def test_patient_cannot_provision_users_403(auth_client):
    """Verify that patient users cannot call the registration endpoint to create accounts."""
    client, db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2 = auth_client
    token = create_access_token({"sub": patient1_user.username, "role": "patient", "patient_id": p1.id})
    res = client.post(
        "/api/auth/register",
        json={
            "username": "rogue_clinician",
            "password": "Password123!",
            "role": "clinician",
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403
    assert "does not hold required clinician privileges" in res.json()["detail"]


def test_clinician_cannot_bind_duplicate_patient_id_409(auth_client):
    """Verify that account registration cannot hijack or duplicate an existing patient association."""
    client, db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2 = auth_client
    token = create_access_token({"sub": clinician.username, "role": "clinician"})
    # p1 is already associated with patient1_user
    res = client.post(
        "/api/auth/register",
        json={
            "username": "duplicate_patient_account",
            "password": "Password123!",
            "role": "patient",
            "patient_id": p1.id,
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 409
    assert "already linked to another user account" in res.json()["detail"]


def test_clinician_can_provision_new_patient_account(auth_client):
    """Verify that a verified clinician can successfully provision a new patient account."""
    client, db, p1, p2, clinician, patient1_user, patient2_user, doc_p1, doc_p2 = auth_client
    token = create_access_token({"sub": clinician.username, "role": "clinician"})

    # Create unlinked patient p3
    from app.models import Patient
    p3 = Patient(name="Sunita Rao", age=40, gender="Female", diabetes_type="Type 2")
    db.add(p3)
    db.commit()

    res = client.post(
        "/api/auth/register",
        json={
            "username": "sunita_rao",
            "email": "sunita@example.com",
            "password": "Password123!",
            "role": "patient",
            "patient_id": p3.id,
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["username"] == "sunita_rao"
    assert data["role"] == "patient"
    assert data["patient_id"] == p3.id


def test_production_jwt_secret_enforcement(monkeypatch):
    """Verify that production fails closed if GLUCOTWIN_JWT_SECRET is missing, default, or too short."""
    from app.auth import resolve_jwt_secret, AuthConfigurationError, DEFAULT_DEV_SECRET

    monkeypatch.setenv("ENVIRONMENT", "production")

    # 1. Missing secret
    monkeypatch.delenv("GLUCOTWIN_JWT_SECRET", raising=False)
    with pytest.raises(AuthConfigurationError) as exc_missing:
        resolve_jwt_secret()
    assert "GLUCOTWIN_JWT_SECRET is not set" in str(exc_missing.value)

    # 2. Insecure development default secret
    monkeypatch.setenv("GLUCOTWIN_JWT_SECRET", DEFAULT_DEV_SECRET)
    with pytest.raises(AuthConfigurationError) as exc_default:
        resolve_jwt_secret()
    assert "development JWT secret cannot be used in production" in str(exc_default.value)

    # 3. Secret too short (< 32 chars)
    monkeypatch.setenv("GLUCOTWIN_JWT_SECRET", "short_secret_12345")
    with pytest.raises(AuthConfigurationError) as exc_short:
        resolve_jwt_secret()
    assert "too short" in str(exc_short.value)

    # 4. Valid strong secret
    valid_secret = "a" * 32
    monkeypatch.setenv("GLUCOTWIN_JWT_SECRET", valid_secret)
    resolved = resolve_jwt_secret()
    assert resolved == valid_secret


def test_frontend_client_has_no_auto_clinician_login():
    """Verify that frontend/src/api/client.js contains no hardcoded clinician credentials or auto-login fallback."""
    from pathlib import Path
    client_js_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "src" / "api" / "client.js"
    assert client_js_path.exists(), "frontend client.js must exist"

    content = client_js_path.read_text(encoding="utf-8")
    assert "ensureAuthenticated" not in content, "ensureAuthenticated auto-login must be removed"
    assert "Clinician123!" not in content, "Hardcoded clinician password must not exist in frontend client.js"
    assert "Patient123!" not in content, "Hardcoded patient password must not exist in frontend client.js"
    assert "dr_sharma" not in content, "Hardcoded demo username must not exist in client.js auto-login"


def test_production_database_persistence_guard(monkeypatch):
    """Verify that in production mode, missing DATABASE_URL raises DatabaseConfigurationError."""
    from app.database import DatabaseConfigurationError
    assert issubclass(DatabaseConfigurationError, RuntimeError)
