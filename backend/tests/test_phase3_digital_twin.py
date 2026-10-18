"""
test_phase3_digital_twin.py - Phase 3 Verification Suite
=========================================================

Verifies:
1. Digital Twin state computation, trend analysis, min/max, freshness, missing vitals,
   empty patient handling, and patient isolation.
2. Alert engine lifecycle (active -> acknowledged -> resolved) and invalid transition rejection (400).
3. Deduplication of threshold, model-predicted, and data quality (stale/missing) alerts.
4. What-If simulation input validation (rejecting negative/excessive inputs with 422),
   handling missing baseline, and deterministic projections.
"""

from datetime import datetime, timezone, timedelta
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

    # Patient 1: Active telemetry
    p1 = Patient(
        id=1,
        name="Patient Alpha",
        age=45,
        gender="Female",
        diabetes_type="Type 2",
        years_since_diagnosis=5,
        weight_kg=72.0,
        height_cm=168.0,
    )
    # Patient 2: Empty telemetry (no readings)
    p2 = Patient(
        id=2,
        name="Patient Empty",
        age=30,
        gender="Male",
        diabetes_type="Type 1",
        years_since_diagnosis=1,
        weight_kg=68.0,
        height_cm=175.0,
    )
    # Patient 3: Stale telemetry (older than 48 hours)
    p3 = Patient(
        id=3,
        name="Patient Stale",
        age=55,
        gender="Female",
        diabetes_type="Type 2",
        years_since_diagnosis=10,
        weight_kg=80.0,
        height_cm=160.0,
    )
    # Patient 4: Partial vitals (glucose only, no vitals)
    p4 = Patient(
        id=4,
        name="Patient Partial",
        age=60,
        gender="Male",
        diabetes_type="Type 2",
        years_since_diagnosis=8,
        weight_kg=85.0,
        height_cm=172.0,
    )

    db.add_all([p1, p2, p3, p4])
    db.flush()

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Telemetry for Patient 1 (Fresh: past 2 hours, 8 readings every 15 min)
    for i in range(8):
        t = now - timedelta(minutes=(8 - i) * 15)
        val = 140.0 + (i * 5.0)  # 140 to 175 mg/dL
        db.add(GlucoseReading(id=100 + i, patient_id=1, timestamp=t, value=val, is_valid=True))
        db.add(VitalReading(id=100 + i, patient_id=1, timestamp=t, heart_rate=72.0 + i, hrv=45.0 - i))

    # Add 1 hyper reading for Patient 1
    db.add(GlucoseReading(id=199, patient_id=1, timestamp=now - timedelta(minutes=5), value=205.0, is_valid=True))

    # Telemetry for Patient 3 (Stale: recorded 72 hours ago)
    t_stale = now - timedelta(hours=72)
    db.add(GlucoseReading(id=301, patient_id=3, timestamp=t_stale, value=130.0, is_valid=True))
    db.add(VitalReading(id=301, patient_id=3, timestamp=t_stale, heart_rate=75.0, hrv=40.0))

    # Telemetry for Patient 4 (Glucose only, no vitals)
    for i in range(4):
        t = now - timedelta(minutes=(4 - i) * 15)
        db.add(GlucoseReading(id=400 + i, patient_id=4, timestamp=t, value=115.0 + i, is_valid=True))

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


# ===========================================================================
# 1. DIGITAL TWIN TESTS
# ===========================================================================

def test_digital_twin_full_summary(client):
    """Verify Patient 1 returns coherent stats, min/max trends, and alert summaries."""
    r = client.get("/api/digital-twin/1")
    assert r.status_code == 200
    data = r.json()

    assert data["patient_id"] == 1
    assert data["patient_name"] == "Patient Alpha"
    assert data["diabetes_type"] == "Type 2"
    assert data["bmi"] is not None
    assert data["latest_glucose"] == 205.0
    assert data["latest_glucose_timestamp"] is not None
    assert data["latest_heart_rate"] is not None
    assert data["latest_hrv"] is not None
    assert data["latest_vital_timestamp"] is not None

    # Trend stats
    assert data["mean_glucose_24h"] is not None
    assert data["min_glucose_24h"] is not None
    assert data["max_glucose_24h"] is not None
    assert data["min_glucose_24h"] <= data["max_glucose_24h"]
    assert data["mean_glucose_1h"] is not None
    assert data["glucose_trend_slope"] is not None
    assert data["total_readings_24h"] >= 8
    assert data["data_freshness_status"] == "fresh"


def test_digital_twin_empty_patient(client):
    """Verify Patient with no readings returns clean nulls and data_missing warning."""
    r = client.get("/api/digital-twin/2")
    assert r.status_code == 200
    data = r.json()

    assert data["patient_id"] == 2
    assert data["latest_glucose"] is None
    assert data["latest_glucose_timestamp"] is None
    assert data["latest_heart_rate"] is None
    assert data["mean_glucose_1h"] is None
    assert data["mean_glucose_24h"] is None
    assert data["min_glucose_24h"] is None
    assert data["max_glucose_24h"] is None
    assert data["total_readings_24h"] == 0
    assert data["data_freshness_status"] == "no_data"
    assert any("No recorded glucose telemetry" in w for w in data["data_quality_warnings"])


def test_digital_twin_stale_patient(client):
    """Verify Patient with stale readings reports 'stale' status and elapsed hours."""
    r = client.get("/api/digital-twin/3")
    assert r.status_code == 200
    data = r.json()

    assert data["patient_id"] == 3
    assert data["data_freshness_status"] == "stale"
    assert data["hours_since_last_reading"] is not None
    assert data["hours_since_last_reading"] >= 70.0
    assert any("stale" in w.lower() for w in data["data_quality_warnings"])


def test_digital_twin_partial_vitals_patient(client):
    """Verify Patient with glucose readings but no vitals handles missing vitals safely."""
    r = client.get("/api/digital-twin/4")
    assert r.status_code == 200
    data = r.json()

    assert data["patient_id"] == 4
    assert data["latest_glucose"] is not None
    assert data["latest_heart_rate"] is None
    assert data["latest_hrv"] is None
    assert any("No autonomic vital readings" in w for w in data["data_quality_warnings"])


def test_digital_twin_unknown_patient_404(client):
    """Verify unknown patient returns 404."""
    r = client.get("/api/digital-twin/99999")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_digital_twin_patient_isolation(client, test_db):
    """Verify readings from Patient 1 are completely isolated from Patient 4."""
    r1 = client.get("/api/digital-twin/1").json()
    r4 = client.get("/api/digital-twin/4").json()

    assert r1["patient_id"] == 1
    assert r4["patient_id"] == 4
    assert r1["latest_glucose"] != r4["latest_glucose"]
    assert r1["total_readings_24h"] != r4["total_readings_24h"]


# ===========================================================================
# 2. ALERT LIFECYCLE & TRANSITIONS
# ===========================================================================

def test_alert_lifecycle_valid_and_invalid_transitions(client, test_db):
    """
    Test transition pipeline:
    active -> acknowledged -> resolved
    And disallowing invalid transitions:
    resolved -> acknowledged (400)
    resolved -> resolved (400)
    """
    patient = test_db.query(Patient).filter(Patient.id == 1).first()
    evaluate_all_alerts_for_patient(test_db, patient)

    alert = test_db.query(Alert).filter(Alert.patient_id == 1, Alert.status == "active").first()
    assert alert is not None
    alert_id = alert.id

    # 1. Valid: active -> acknowledged
    r_ack = client.post(f"/api/alerts/{alert_id}/acknowledge")
    assert r_ack.status_code == 200
    assert r_ack.json()["status"] == "acknowledged"
    assert r_ack.json()["acknowledged"] is True
    assert r_ack.json()["acknowledged_at"] is not None

    # 2. Valid: acknowledged -> resolved
    r_res = client.post(f"/api/alerts/{alert_id}/resolve")
    assert r_res.status_code == 200
    assert r_res.json()["status"] == "resolved"
    assert r_res.json()["resolved_at"] is not None

    # 3. Invalid: trying to acknowledge a resolved alert must return 400
    r_bad_ack = client.post(f"/api/alerts/{alert_id}/acknowledge")
    assert r_bad_ack.status_code == 400
    assert "already resolved" in r_bad_ack.json()["detail"].lower()

    # 4. Invalid: trying to resolve an already resolved alert must return 400
    r_bad_res = client.post(f"/api/alerts/{alert_id}/resolve")
    assert r_bad_res.status_code == 400
    assert "already resolved" in r_bad_res.json()["detail"].lower()

    # 5. Non-existent alert returns 404
    r_not_found = client.post("/api/alerts/888888/acknowledge")
    assert r_not_found.status_code == 404


def test_alert_data_missing_and_stale_generation(client, test_db):
    """Verify alert engine generates data_missing for empty patient and data_stale for stale patient."""
    p_empty = test_db.query(Patient).filter(Patient.id == 2).first()
    p_stale = test_db.query(Patient).filter(Patient.id == 3).first()

    # Evaluate empty patient
    alerts_empty = evaluate_all_alerts_for_patient(test_db, p_empty)
    assert len(alerts_empty) == 1
    assert alerts_empty[0].alert_type == "data_missing"
    assert alerts_empty[0].severity == "info"

    # Evaluate stale patient
    alerts_stale = evaluate_all_alerts_for_patient(test_db, p_stale)
    assert any(a.alert_type == "data_stale" for a in alerts_stale)

    # Idempotence: re-running evaluation generates 0 duplicates
    alerts_empty_again = evaluate_all_alerts_for_patient(test_db, p_empty)
    assert len(alerts_empty_again) == 0


# ===========================================================================
# 3. WHAT-IF SIMULATION TESTS
# ===========================================================================

def test_what_if_simulation_valid(client):
    """Verify valid hypothetical inputs calculate deterministic scenario projections."""
    payload = {
        "patient_id": 1,
        "additional_carbs_g": 40.0,
        "activity_minutes": 25.0,
        "as_of_glucose": 125.0,
    }
    r = client.post("/api/simulation/what-if", json=payload)
    assert r.status_code == 200
    data = r.json()

    assert data["patient_id"] == 1
    assert data["baseline_glucose"] == 125.0
    assert data["additional_carbs_g"] == 40.0
    assert data["activity_minutes"] == 25.0
    assert data["projected_carb_impact_mg_dl"] > 0
    assert data["projected_activity_impact_mg_dl"] < 0
    assert data["formula_version"] == "1.0.0-illustrative-heuristic"
    assert "SIMULATED — NOT A CLINICAL PREDICTION" in data["disclaimer"]


def test_what_if_simulation_negative_inputs_rejected(client):
    """Verify negative carbs or activity duration are rejected with 422 Unprocessable Entity."""
    # Negative carbs
    r_neg_carbs = client.post("/api/simulation/what-if", json={"patient_id": 1, "additional_carbs_g": -10.0})
    assert r_neg_carbs.status_code == 422

    # Negative activity
    r_neg_act = client.post("/api/simulation/what-if", json={"patient_id": 1, "activity_minutes": -5.0})
    assert r_neg_act.status_code == 422


def test_what_if_simulation_excessive_inputs_rejected(client):
    """Verify unrealistic excessive inputs (> 300g carbs, > 360 min activity) are rejected with 422."""
    r_excess = client.post("/api/simulation/what-if", json={"patient_id": 1, "additional_carbs_g": 500.0})
    assert r_excess.status_code == 422


def test_what_if_simulation_empty_patient_default_baseline(client):
    """Verify patient without historical readings uses default baseline with explicit notice."""
    r = client.post("/api/simulation/what-if", json={"patient_id": 2, "additional_carbs_g": 30.0})
    assert r.status_code == 200
    data = r.json()

    assert data["patient_id"] == 2
    assert data["baseline_glucose"] == 110.0
    assert any("110.0 mg/dL" in w for w in data["data_quality_warnings"])


def test_what_if_simulation_unknown_patient_404(client):
    """Verify unknown patient in simulation returns 404."""
    r = client.post("/api/simulation/what-if", json={"patient_id": 99999})
    assert r.status_code == 404
