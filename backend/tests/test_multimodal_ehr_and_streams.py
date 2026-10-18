"""
test_multimodal_ehr_and_streams.py - Automated Unit & Integration Tests for Multimodal EHR, Dynamic Streams & Sensor Simulation
===============================================================================================================================

Tests cover:
  TEST 1: Patient historical EHR retrieval (diagnoses, BMI, demographics)
  TEST 2: Patient laboratory results endpoint (/api/patients/{id}/labs)
  TEST 3: Patient genetic markers endpoint (/api/patients/{id}/genetics)
  TEST 4: Patient data isolation (Patient 1 records never leak to Patient 2)
  TEST 5: Nonexistent patient 404 handling for labs and genetics
  TEST 6: Sleep stream endpoint (/api/readings/sleep/{id}) stages and duration
  TEST 7: Step-count stream endpoint (/api/readings/steps/{id}) interval vs cumulative steps
  TEST 8: Digital Twin summary aggregation with sleep and step metrics
  TEST 9: Demonstrable sensor feed simulation endpoint (/api/digital-twin/simulate-feed)
  TEST 10: Sensor simulation alert evaluation integration
  TEST 11: Sensor simulation invalid input validation
  TEST 12: Seed script populates all synthetic multimodal records with is_synthetic=True
"""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import (
    Patient, GlucoseReading, VitalReading, LabResult, GeneticMarker,
    SleepRecord, StepRecord, Alert
)
from app.seed import seed_database


@pytest.fixture(scope="function")
def test_db():
    """Isolated in-memory SQLite session with test fixtures."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    now = datetime.now(timezone.utc)

    # Seed Patient 1
    p1 = Patient(
        id=1,
        name="Elena Rostova",
        age=52,
        gender="Female",
        diabetes_type="Type 2",
        years_since_diagnosis=8,
        weight_kg=78.5,
        height_cm=165.0,
        historical_diagnoses="Essential Hypertension (2018), Dyslipidemia (2020), Mild Diabetic Neuropathy (2023)",
    )
    # Seed Patient 2 (Empty baseline)
    p2 = Patient(
        id=2,
        name="Marcus Vance",
        age=34,
        gender="Male",
        diabetes_type="Type 1",
        years_since_diagnosis=4,
        weight_kg=72.0,
        height_cm=180.0,
        historical_diagnoses="None",
    )
    session.add_all([p1, p2])
    session.commit()

    # Seed Lab Results for Patient 1 only
    labs = [
        LabResult(
            patient_id=1,
            test_name="HbA1c",
            result=7.8,
            unit="%",
            reference_range="< 5.7%",
            measurement_date=now - timedelta(days=30),
            is_synthetic=True,
        ),
        LabResult(
            patient_id=1,
            test_name="Fasting Blood Glucose",
            result=142.0,
            unit="mg/dL",
            reference_range="70-99 mg/dL",
            measurement_date=now - timedelta(days=30),
            is_synthetic=True,
        ),
        LabResult(
            patient_id=1,
            test_name="LDL Cholesterol",
            result=135.0,
            unit="mg/dL",
            reference_range="< 100 mg/dL",
            measurement_date=now - timedelta(days=30),
            is_synthetic=True,
        ),
    ]
    session.add_all(labs)

    # Seed Genetic Markers for Patient 1
    markers = [
        GeneticMarker(
            patient_id=1,
            marker_id="rs7903146",
            gene="TCF7L2",
            genotype="C/T (Risk allele T)",
            recorded_at=now - timedelta(days=120),
            data_source="Synthetic Pharmacogenomics Array v2",
            is_synthetic=True,
        ),
        GeneticMarker(
            patient_id=1,
            marker_id="rs1801282",
            gene="PPARG",
            genotype="Pro12Ala (C/G)",
            recorded_at=now - timedelta(days=120),
            data_source="Synthetic Pharmacogenomics Array v2",
            is_synthetic=True,
        ),
    ]
    session.add_all(markers)

    # Seed Telemetry for Patient 1 (within current window)
    readings_time = now.replace(tzinfo=None) - timedelta(minutes=15)
    session.add(GlucoseReading(patient_id=1, value=140.0, timestamp=readings_time, is_valid=True))
    session.add(VitalReading(patient_id=1, heart_rate=75.0, hrv=45.0, timestamp=readings_time))

    # Seed Sleep Records for Patient 1
    sleep_start = now.replace(tzinfo=None) - timedelta(hours=8)
    session.add(SleepRecord(
        patient_id=1,
        start_time=sleep_start,
        end_time=sleep_start + timedelta(minutes=90),
        stage="deep",
        duration_minutes=90,
        is_synthetic=True
    ))
    session.add(SleepRecord(
        patient_id=1,
        start_time=sleep_start + timedelta(minutes=90),
        end_time=sleep_start + timedelta(hours=7),
        stage="light",
        duration_minutes=330,
        is_synthetic=True
    ))

    # Seed Step Records for Patient 1
    session.add(StepRecord(
        patient_id=1,
        timestamp=now.replace(tzinfo=None) - timedelta(minutes=30),
        interval_steps=420,
        daily_cumulative_steps=4200,
        is_synthetic=True
    ))

    session.commit()

    yield session

    session.close()


@pytest.fixture(scope="function")
def client(test_db):
    """FastAPI TestClient bound to the isolated in-memory test DB."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# =============================================================================
# TEST 1: Patient Historical EHR Retrieval
# =============================================================================
def test_patient_ehr_retrieval(client):
    response = client.get("/api/patients/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Elena Rostova"
    assert "Essential Hypertension" in data["historical_diagnoses"]
    assert data["height_cm"] == 165.0
    assert data["weight_kg"] == 78.5
    expected_bmi = round(78.5 / ((165.0 / 100) ** 2), 1)
    assert abs(data["calculated_bmi"] - expected_bmi) < 0.2


# =============================================================================
# TEST 2: Patient Laboratory Results Endpoint
# =============================================================================
def test_patient_labs_endpoint(client):
    response = client.get("/api/patients/1/labs")
    assert response.status_code == 200
    labs = response.json()
    assert len(labs) == 3
    test_names = [l["test_name"] for l in labs]
    assert "HbA1c" in test_names
    assert "Fasting Blood Glucose" in test_names
    assert "LDL Cholesterol" in test_names
    for l in labs:
        assert l["patient_id"] == 1
        assert l["is_synthetic"] is True
        assert l["unit"] in ["%", "mg/dL"]


# =============================================================================
# TEST 3: Patient Genetic Markers Endpoint
# =============================================================================
def test_patient_genetics_endpoint(client):
    response = client.get("/api/patients/1/genetics")
    assert response.status_code == 200
    markers = response.json()
    assert len(markers) == 2
    genes = [m["gene"] for m in markers]
    assert "TCF7L2" in genes
    assert "PPARG" in genes
    for m in markers:
        assert m["patient_id"] == 1
        assert m["is_synthetic"] is True
        assert m["marker_id"].startswith("rs")


# =============================================================================
# TEST 4: Patient Data Isolation
# =============================================================================
def test_patient_data_isolation(client):
    labs_resp = client.get("/api/patients/2/labs")
    assert labs_resp.status_code == 200
    assert labs_resp.json() == []

    gen_resp = client.get("/api/patients/2/genetics")
    assert gen_resp.status_code == 200
    assert gen_resp.json() == []


# =============================================================================
# TEST 5: Nonexistent Patient 404 Handling
# =============================================================================
def test_nonexistent_patient_404(client):
    labs_resp = client.get("/api/patients/999/labs")
    assert labs_resp.status_code == 404
    assert "not found" in labs_resp.json()["detail"].lower()

    gen_resp = client.get("/api/patients/999/genetics")
    assert gen_resp.status_code == 404
    assert "not found" in gen_resp.json()["detail"].lower()


# =============================================================================
# TEST 6: Sleep Stream Endpoint
# =============================================================================
def test_sleep_stream_endpoint(client):
    response = client.get("/api/readings/sleep/1?hours=24")
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == 1
    assert data["total_sleep_hours"] == 7.0  # (90 + 330) / 60
    assert data["deep_sleep_hours"] == 1.5   # 90 / 60
    assert data["light_sleep_hours"] == 5.5  # 330 / 60
    assert len(data["records"]) == 2
    for r in data["records"]:
        assert r["is_synthetic"] is True
        assert r["stage"] in ["deep", "light", "rem", "awake"]


# =============================================================================
# TEST 7: Step-Count Stream Endpoint
# =============================================================================
def test_step_count_stream_endpoint(client):
    response = client.get("/api/readings/steps/1?hours=24")
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == 1
    assert data["total_steps_24h"] == 420
    assert data["latest_interval_steps"] == 420
    record = data["records"][0]
    assert record["interval_steps"] == 420
    assert record["daily_cumulative_steps"] == 4200
    assert record["is_synthetic"] is True


# =============================================================================
# TEST 8: Digital Twin Summary Aggregation with Sleep and Steps
# =============================================================================
def test_digital_twin_aggregates_multimodal(client):
    response = client.get("/api/digital-twin/1")
    assert response.status_code == 200
    twin = response.json()
    assert twin["patient_id"] == 1
    assert "latest_sleep_summary" in twin
    assert "latest_step_summary" in twin
    assert "historical_diagnoses" in twin
    assert twin["latest_sleep_summary"]["total_sleep_hours"] == 7.0
    assert twin["latest_step_summary"]["daily_cumulative_steps"] == 4200


# =============================================================================
# TEST 9: Sensor Feed Simulation Endpoint
# =============================================================================
def test_sensor_feed_simulation(client, test_db):
    now_str = datetime.now(timezone.utc).isoformat()
    payload = {
        "patient_id": 1,
        "glucose_value": 165.5,
        "heart_rate": 82.0,
        "hrv": 38.0,
        "interval_steps": 250,
        "timestamp": now_str,
    }

    response = client.post("/api/digital-twin/simulate-feed", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == 1
    assert data["ingested_glucose"] == 165.5
    assert data["ingested_heart_rate"] == 82.0
    assert data["ingested_hrv"] == 38.0
    assert data["ingested_interval_steps"] == 250
    assert data["new_cumulative_steps"] == 4200 + 250

    # Verify telemetry in database
    g_count = test_db.query(GlucoseReading).filter(GlucoseReading.patient_id == 1).count()
    assert g_count == 2
    step_count = test_db.query(StepRecord).filter(StepRecord.patient_id == 1).count()
    assert step_count == 2


# =============================================================================
# TEST 10: Sensor Simulation Alert Trigger
# =============================================================================
def test_sensor_simulation_triggers_alert(client, test_db):
    now_str = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
    payload = {
        "patient_id": 1,
        "glucose_value": 265.0,  # Severe hyperglycemia >= 250
        "heart_rate": 105.0,     # Tachycardia + depressed HRV
        "hrv": 18.0,
        "interval_steps": 50,
        "timestamp": now_str,
    }

    response = client.post("/api/digital-twin/simulate-feed", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["new_alerts_triggered"]) > 0

    crit_alert = test_db.query(Alert).filter(
        Alert.patient_id == 1,
        Alert.severity == "critical"
    ).first()
    assert crit_alert is not None
    assert crit_alert.trigger_value == 265.0


# =============================================================================
# TEST 11: Sensor Simulation Input Validation
# =============================================================================
def test_sensor_simulation_validation(client):
    resp_invalid_patient = client.post("/api/digital-twin/simulate-feed", json={
        "patient_id": 9999,
        "glucose_value": 120.0,
        "heart_rate": 70.0,
        "hrv": 50.0,
        "interval_steps": 100,
    })
    assert resp_invalid_patient.status_code == 404

    resp_invalid_bounds = client.post("/api/digital-twin/simulate-feed", json={
        "patient_id": 1,
        "glucose_value": -5.0,
        "heart_rate": 70.0,
        "hrv": 50.0,
    })
    assert resp_invalid_bounds.status_code == 422


# =============================================================================
# TEST 12: Seed Script Populates Synthetic Records
# =============================================================================
def test_seed_database_multimodal():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    seed_database(session)

    patients = session.query(Patient).all()
    assert len(patients) == 5
    for p in patients:
        assert p.historical_diagnoses is not None
        assert p.height_cm > 100
        assert p.weight_kg > 40

    lab_count = session.query(LabResult).count()
    assert lab_count >= 50
    assert all(l.is_synthetic for l in session.query(LabResult).all())

    genetic_count = session.query(GeneticMarker).count()
    assert genetic_count == 25
    assert all(g.is_synthetic for g in session.query(GeneticMarker).all())

    sleep_count = session.query(SleepRecord).count()
    assert sleep_count > 0
    assert all(s.is_synthetic for s in session.query(SleepRecord).all())

    step_count = session.query(StepRecord).count()
    assert step_count > 0
    assert all(st.is_synthetic for st in session.query(StepRecord).all())

    session.close()
