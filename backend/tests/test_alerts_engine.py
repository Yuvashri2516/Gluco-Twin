"""
Integration and Unit Tests for Alert Engine, Alert Endpoints,
Digital Twin Intelligence, and What-If Simulation (Phase 5).
"""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import Patient, GlucoseReading, VitalReading, Alert
from app.alerts_engine import (
    evaluate_observed_reading_alerts,
    evaluate_all_alerts_for_patient,
    DEMO_THRESHOLDS,
)

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

    # Seed isolated patient Alpha
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

    # Add 10 normal readings
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for i in range(10):
        t = now - timedelta(minutes=(10 - i) * 15)
        db.add(GlucoseReading(
            id=100 + i,
            patient_id=1,
            timestamp=t,
            value=120.0 + i,
            is_valid=True,
        ))
        db.add(VitalReading(
            id=100 + i,
            patient_id=1,
            timestamp=t,
            heart_rate=72.0,
            hrv=45.0,
        ))

    # Add an observed hyperglycemia reading (210.0 mg/dL)
    db.add(GlucoseReading(
        id=201,
        patient_id=1,
        timestamp=now - timedelta(minutes=10),
        value=210.0,
        is_valid=True,
    ))

    # Add an observed hypoglycemia reading (50.0 mg/dL)
    db.add(GlucoseReading(
        id=202,
        patient_id=1,
        timestamp=now - timedelta(minutes=5),
        value=50.0,
        is_valid=True,
    ))

    # Add an autonomic depression reading (HR: 105, HRV: 20)
    db.add(VitalReading(
        id=203,
        patient_id=1,
        timestamp=now - timedelta(minutes=5),
        heart_rate=105.0,
        hrv=20.0,
    ))

    # Add patient Beta with NO readings
    patient2 = Patient(
        id=2,
        name="Test Patient Beta",
        age=32,
        gender="Male",
        diabetes_type="Type 1",
        years_since_diagnosis=2,
        weight_kg=75.0,
        height_cm=180.0,
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


# ---------------------------------------------------------------------------
# Test 1: Alert Generation & Threshold Handling
# ---------------------------------------------------------------------------
def test_observed_alert_generation(test_db):
    patient = test_db.query(Patient).filter(Patient.id == 1).first()
    new_alerts = evaluate_observed_reading_alerts(test_db, patient)

    # Should detect hypo (50.0 < 54.0 -> severe hypo), hyper (210.0 >= 180.0 -> hyper), and autonomic (105 / 20)
    alert_types = [a.alert_type for a in new_alerts]
    assert "observed_severe_hypoglycemia" in alert_types
    assert "observed_hyperglycemia" in alert_types
    assert "observed_autonomic_depression" in alert_types

    hypo_alert = next(a for a in new_alerts if a.alert_type == "observed_severe_hypoglycemia")
    assert hypo_alert.severity == "critical"
    assert hypo_alert.trigger_value == 50.0
    assert hypo_alert.threshold == DEMO_THRESHOLDS["glucose_severe_hypo"]
    assert hypo_alert.source == "observed_reading"
    assert hypo_alert.status == "active"


# ---------------------------------------------------------------------------
# Test 2: Duplicate Prevention (Idempotence)
# ---------------------------------------------------------------------------
def test_alert_deduplication(test_db):
    patient = test_db.query(Patient).filter(Patient.id == 1).first()
    
    # First evaluation creates alerts
    first_run = evaluate_all_alerts_for_patient(test_db, patient)
    initial_count = test_db.query(Alert).filter(Alert.patient_id == 1).count()
    assert initial_count > 0

    # Second evaluation must NOT create duplicate alerts for same readings
    second_run = evaluate_all_alerts_for_patient(test_db, patient)
    assert len(second_run) == 0
    final_count = test_db.query(Alert).filter(Alert.patient_id == 1).count()
    assert final_count == initial_count


# ---------------------------------------------------------------------------
# Test 3: Alert API Endpoints - Listing, Filtering, and Patient Validation
# ---------------------------------------------------------------------------
def test_alerts_api_listing_and_filtering(client, test_db):
    # Pre-evaluate alerts
    patient = test_db.query(Patient).filter(Patient.id == 1).first()
    evaluate_all_alerts_for_patient(test_db, patient)

    # List all
    r = client.get("/api/alerts")
    assert r.status_code == 200
    alerts = r.json()
    assert len(alerts) >= 3

    # Filter by patient_id = 1
    r_p1 = client.get("/api/alerts?patient_id=1")
    assert r_p1.status_code == 200
    assert all(a["patient_id"] == 1 for a in r_p1.json())

    # Filter by patient_id = 2 (empty)
    r_p2 = client.get("/api/alerts?patient_id=2")
    assert r_p2.status_code == 200
    assert len(r_p2.json()) == 0

    # Invalid patient ID returns 404
    r_invalid = client.get("/api/alerts?patient_id=99999")
    assert r_invalid.status_code == 404
    assert "not found" in r_invalid.json()["detail"]


# ---------------------------------------------------------------------------
# Test 4: Acknowledgement and Resolution Lifecycle
# ---------------------------------------------------------------------------
def test_alert_acknowledgement_and_resolution(client, test_db):
    patient = test_db.query(Patient).filter(Patient.id == 1).first()
    created = evaluate_all_alerts_for_patient(test_db, patient)
    alert_id = created[0].id

    # 1. Check initial active state
    r_get = client.get(f"/api/alerts/{alert_id}")
    assert r_get.status_code == 200
    assert r_get.json()["status"] == "active"
    assert r_get.json()["acknowledged"] is False

    # 2. Acknowledge alert
    r_ack = client.post(f"/api/alerts/{alert_id}/acknowledge")
    assert r_ack.status_code == 200
    assert r_ack.json()["status"] == "acknowledged"
    assert r_ack.json()["acknowledged"] is True
    assert r_ack.json()["acknowledged_at"] is not None

    # 3. Resolve alert
    r_res = client.post(f"/api/alerts/{alert_id}/resolve")
    assert r_res.status_code == 200
    assert r_res.json()["status"] == "resolved"
    assert r_res.json()["resolved_at"] is not None

    # 4. Unknown alert ID returns 404
    r_not_found = client.post("/api/alerts/999999/acknowledge")
    assert r_not_found.status_code == 404


# ---------------------------------------------------------------------------
# Test 5: Observed vs Model-Predicted Alert Distinction
# ---------------------------------------------------------------------------
def test_observed_vs_predicted_alert_distinction(test_db):
    # Manually insert one predicted alert and one observed alert
    a_obs = Alert(
        patient_id=1,
        timestamp=datetime.now(timezone.utc),
        severity="warning",
        message="Observed hyperglycemia reading",
        alert_type="observed_hyperglycemia",
        source="observed_reading",
        status="active",
        trigger_value=195.0,
        threshold=180.0,
        dedup_key="obs:1:test",
    )
    a_pred = Alert(
        patient_id=1,
        timestamp=datetime.now(timezone.utc),
        severity="critical",
        message="Predicted glucose spike by ML model",
        alert_type="predicted_glucose_spike",
        source="experimental_prediction",
        status="active",
        trigger_value=0.74,
        threshold=0.50,
        dedup_key="pred:1:test",
    )
    test_db.add(a_obs)
    test_db.add(a_pred)
    test_db.commit()

    assert a_obs.source == "observed_reading"
    assert a_pred.source == "experimental_prediction"
    assert a_obs.alert_type != a_pred.alert_type


# ---------------------------------------------------------------------------
# Test 6: Digital Twin Intelligence API
# ---------------------------------------------------------------------------
def test_digital_twin_intelligence_endpoint(client):
    r = client.get("/api/digital-twin/1")
    assert r.status_code == 200
    data = r.json()

    assert data["patient_id"] == 1
    assert data["patient_name"] == "Test Patient Alpha"
    assert data["diabetes_type"] == "Type 2"
    assert data["bmi"] is not None
    assert data["latest_glucose"] is not None
    assert data["mean_glucose_24h"] is not None
    assert "RESEARCH PROTOTYPE ONLY" in data["disclaimer"]

    # Unknown patient
    r_404 = client.get("/api/digital-twin/99999")
    assert r_404.status_code == 404


# ---------------------------------------------------------------------------
# Test 7: What-If Counterfactual Simulation Endpoint
# ---------------------------------------------------------------------------
def test_what_if_simulation_calculation(client):
    payload = {
        "patient_id": 1,
        "additional_carbs_g": 45.0,
        "activity_minutes": 30.0,
        "as_of_glucose": 130.0,
    }
    r = client.post("/api/simulation/what-if", json=payload)
    assert r.status_code == 200
    data = r.json()

    assert data["patient_id"] == 1
    assert data["baseline_glucose"] == 130.0
    assert data["additional_carbs_g"] == 45.0
    assert data["activity_minutes"] == 30.0
    assert data["projected_carb_impact_mg_dl"] > 0
    assert data["projected_activity_impact_mg_dl"] < 0
    assert isinstance(data["projected_spike_risk_breach"], bool)
    assert "SIMULATED — NOT A CLINICAL PREDICTION" in data["disclaimer"]
    assert len(data["assumptions"]) > 0

    # Patient not found
    r_bad = client.post("/api/simulation/what-if", json={"patient_id": 99999})
    assert r_bad.status_code == 404


# ---------------------------------------------------------------------------
# Test 8: Acknowledged & Resolved States Persist Across Evaluations
# ---------------------------------------------------------------------------
def test_acknowledged_and_resolved_alerts_persist_across_evaluations(client, test_db):
    patient = test_db.query(Patient).filter(Patient.id == 1).first()
    evaluate_all_alerts_for_patient(test_db, patient)

    # Acknowledge first alert and resolve second alert
    alerts = test_db.query(Alert).filter(Alert.patient_id == 1).all()
    assert len(alerts) >= 2
    a1_id = alerts[0].id
    a2_id = alerts[1].id

    client.post(f"/api/alerts/{a1_id}/acknowledge")
    client.post(f"/api/alerts/{a2_id}/resolve")

    # Re-run alert evaluation
    evaluate_all_alerts_for_patient(test_db, patient)

    # Verify states remain acknowledged and resolved
    a1_reloaded = test_db.query(Alert).filter(Alert.id == a1_id).first()
    a2_reloaded = test_db.query(Alert).filter(Alert.id == a2_id).first()
    assert a1_reloaded.status == "acknowledged"
    assert a1_reloaded.acknowledged is True
    assert a2_reloaded.status == "resolved"
    assert a2_reloaded.resolved_at is not None


# ---------------------------------------------------------------------------
# Test 9: New Triggering Readings Create New Alerts
# ---------------------------------------------------------------------------
def test_new_triggering_readings_create_new_alerts(client, test_db):
    patient = test_db.query(Patient).filter(Patient.id == 1).first()
    initial_alerts = evaluate_all_alerts_for_patient(test_db, patient)
    initial_count = test_db.query(Alert).filter(Alert.patient_id == 1).count()

    # Add a brand new severe hyperglycemia reading (290 mg/dL) with a distinct timestamp and ID
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    new_reading = GlucoseReading(
        id=999,
        patient_id=1,
        timestamp=now + timedelta(minutes=1),
        value=290.0,
        is_valid=True,
    )
    test_db.add(new_reading)
    test_db.commit()

    # Re-run evaluation
    new_alerts = evaluate_all_alerts_for_patient(test_db, patient)
    assert len(new_alerts) >= 1
    new_severe = next((a for a in new_alerts if a.trigger_value == 290.0), None)
    assert new_severe is not None
    assert new_severe.severity == "critical"
    assert new_severe.status == "active"
    assert test_db.query(Alert).filter(Alert.patient_id == 1).count() == initial_count + len(new_alerts)


# ---------------------------------------------------------------------------
# Test 10: Prediction Failure Fault Tolerance
# ---------------------------------------------------------------------------
def test_prediction_failure_fault_tolerance(monkeypatch, test_db):
    patient = test_db.query(Patient).filter(Patient.id == 1).first()

    # Mock evaluate_model_predicted_alerts to raise an unexpected runtime error
    def mock_broken_prediction(db, p):
        raise RuntimeError("Simulated ML model failure / artifact corruption")

    from app import alerts_engine
    monkeypatch.setattr(alerts_engine, "evaluate_model_predicted_alerts", mock_broken_prediction)

    # evaluate_all_alerts_for_patient must not raise and should still evaluate observed alerts safely
    created = alerts_engine.evaluate_all_alerts_for_patient(test_db, patient)
    assert isinstance(created, list)
    assert any(a.source == "observed_reading" for a in created)

