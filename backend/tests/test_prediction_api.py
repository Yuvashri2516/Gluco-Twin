"""
Integration Tests for Prediction API Endpoint and Core System Endpoints.
Uses an isolated in-memory SQLite database to preserve real data integrity.
"""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import Patient, GlucoseReading, VitalReading

# Isolated SQLite in-memory test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # Seed isolated test fixtures
    patient = Patient(
        id=1,
        name="Test Patient Alpha",
        age=50,
        gender="Female",
        diabetes_type="Type 2",
        years_since_diagnosis=7,
        weight_kg=70.0,
        height_cm=165.0,
    )
    db.add(patient)
    db.flush()

    # Seed 10 readings spaced 15 min apart
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for i in range(10):
        t = now - timedelta(minutes=(9 - i) * 15)
        db.add(GlucoseReading(
            patient_id=1,
            timestamp=t,
            value=135.0 + i * 2.0,
            is_valid=True,
        ))
        db.add(VitalReading(
            patient_id=1,
            timestamp=t,
            heart_rate=72.0 + i,
            hrv=50.0 - i,
        ))

    # Add a second patient with NO readings (for testing insufficient data)
    patient2 = Patient(
        id=2,
        name="Test Patient Empty",
        age=30,
        gender="Male",
        diabetes_type="Pre-diabetic",
        years_since_diagnosis=1,
        weight_kg=80.0,
        height_cm=175.0,
    )
    db.add(patient2)

    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_predict_glucose_spike_success(client):
    """Test successful spike prediction response for an existing patient."""
    response = client.post(
        "/api/predictions/glucose-spike",
        json={"patient_id": 1}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["patient_id"] == 1
    assert data["patient_name"] == "Test Patient Alpha"
    assert data["horizon_minutes"] == 120
    assert data["threshold_mg_dl"] == 180.0
    assert isinstance(data["spike_predicted"], bool)
    assert 0.0 <= data["risk_score"] <= 1.0
    assert data["risk_category"] in ["LOW", "MODERATE", "HIGH"]
    assert data["model_status"] == "TRAINED_PROTOTYPE"
    assert "curr_glucose" in data["features_used"]
    assert "feature_contributions" in data
    assert data["is_synthetic_data"] is True
    assert "RESEARCH PROTOTYPE" in data["clinical_disclaimer"]


def test_predict_glucose_spike_unknown_patient(client):
    """Unknown patient ID should return 404."""
    response = client.post(
        "/api/predictions/glucose-spike",
        json={"patient_id": 99999}
    )
    assert response.status_code == 404
    assert "Patient #99999 not found" in response.json()["detail"]


def test_predict_glucose_spike_insufficient_data(client):
    """Patient with no glucose readings should return 422 Unprocessable Entity."""
    response = client.post(
        "/api/predictions/glucose-spike",
        json={"patient_id": 2}
    )
    assert response.status_code == 422
    assert "no valid glucose readings" in response.json()["detail"]


def test_missing_model_artifact_returns_503(client, monkeypatch, tmp_path):
    """If model artifact is missing, endpoint returns 503 Service Unavailable."""
    import app.routers.predictions as pred_module
    monkeypatch.setattr(pred_module, "ML_ARTIFACT_DIR", str(tmp_path))
    response = client.post(
        "/api/predictions/glucose-spike",
        json={"patient_id": 1}
    )
    assert response.status_code == 503
    assert "model artifact is not available" in response.json()["detail"]


def test_existing_endpoints_preserved(client):
    """Verify that existing Phase 1 endpoints continue working with no regressions."""
    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "ok"

    r_patients = client.get("/api/patients")
    assert r_patients.status_code == 200
    assert len(r_patients.json()) == 2

    r_patient = client.get("/api/patients/1")
    assert r_patient.status_code == 200
    assert r_patient.json()["name"] == "Test Patient Alpha"

    r_glucose = client.get("/api/readings/glucose/1?hours=24")
    assert r_glucose.status_code == 200
    assert len(r_glucose.json()) == 10

    r_vitals = client.get("/api/readings/vitals/1?hours=24")
    assert r_vitals.status_code == 200
    assert len(r_vitals.json()) == 10
