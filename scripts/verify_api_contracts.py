"""
verify_api_contracts.py - Verifies all API endpoints against schemas, isolation, and error handling
"""
import sys
from fastapi.testclient import TestClient

# Add backend to path
sys.path.insert(0, "backend")

from app.main import app

client = TestClient(app)

def test_endpoint(name, func):
    try:
        func()
        print(f"[PASS] {name}")
    except Exception as e:
        print(f"[FAIL] {name}: {e}")
        raise e

# 1. Health & Patients
def check_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "version" in data
test_endpoint("GET /api/health", check_health)

def check_patients():
    res = client.get("/api/patients")
    assert res.status_code == 200
    patients = res.json()
    assert len(patients) == 5
    p1 = client.get("/api/patients/1").json()
    assert p1["name"] == "Ananya Sharma"
    assert p1["calculated_bmi"] > 0
    assert "historical_diagnoses" in p1
    # 404 test
    res_404 = client.get("/api/patients/999")
    assert res_404.status_code == 404
test_endpoint("GET /api/patients & /api/patients/{id}", check_patients)

# 2. Labs & Genetics
def check_labs():
    res = client.get("/api/patients/1/labs")
    assert res.status_code == 200
    labs = res.json()
    assert len(labs) > 0
    assert all(l["patient_id"] == 1 for l in labs)
    assert all(l["is_synthetic"] is True for l in labs)
    assert any(l["test_name"] == "HbA1c" for l in labs)
    # 404 test
    res_404 = client.get("/api/patients/999/labs")
    assert res_404.status_code == 404
test_endpoint("GET /api/patients/{id}/labs", check_labs)

def check_genetics():
    res = client.get("/api/patients/1/genetics")
    assert res.status_code == 200
    markers = res.json()
    assert len(markers) == 5
    assert all(m["patient_id"] == 1 for m in markers)
    assert all(m["is_synthetic"] is True for m in markers)
    assert any(m["gene"] == "TCF7L2" for m in markers)
    # 404 test
    res_404 = client.get("/api/patients/999/genetics")
    assert res_404.status_code == 404
test_endpoint("GET /api/patients/{id}/genetics", check_genetics)

# 3. Dynamic Streams: Glucose, Vitals, Sleep, Steps
def check_glucose():
    res = client.get("/api/readings/glucose/1?hours=24")
    assert res.status_code == 200
    readings = res.json()
    assert len(readings) > 0
    assert all(r["patient_id"] == 1 for r in readings)
    res_404 = client.get("/api/readings/glucose/999")
    assert res_404.status_code == 404
test_endpoint("GET /api/readings/glucose/{id}", check_glucose)

def check_vitals():
    res = client.get("/api/readings/vitals/1?hours=24")
    assert res.status_code == 200
    vitals = res.json()
    assert len(vitals) > 0
    assert all(v["patient_id"] == 1 for v in vitals)
    res_404 = client.get("/api/readings/vitals/999")
    assert res_404.status_code == 404
test_endpoint("GET /api/readings/vitals/{id}", check_vitals)

def check_sleep():
    res = client.get("/api/readings/sleep/1?hours=24")
    assert res.status_code == 200
    data = res.json()
    assert data["patient_id"] == 1
    assert data["total_sleep_hours"] > 0
    assert data["is_synthetic_data"] is True
    assert len(data["records"]) > 0
    res_404 = client.get("/api/readings/sleep/999")
    assert res_404.status_code == 404
test_endpoint("GET /api/readings/sleep/{id}", check_sleep)

def check_steps():
    res = client.get("/api/readings/steps/1?hours=24")
    assert res.status_code == 200
    data = res.json()
    assert data["patient_id"] == 1
    assert data["total_steps_24h"] >= 0
    assert data["is_synthetic_data"] is True
    assert len(data["records"]) > 0
    res_404 = client.get("/api/readings/steps/999")
    assert res_404.status_code == 404
test_endpoint("GET /api/readings/steps/{id}", check_steps)

# 4. Digital Twin Intelligence
def check_digital_twin():
    res = client.get("/api/digital-twin/1")
    assert res.status_code == 200
    twin = res.json()
    assert twin["patient_id"] == 1
    assert twin["patient_name"] == "Ananya Sharma"
    assert "mean_glucose_24h" in twin
    assert "glucose_change_1h" in twin
    assert "latest_sleep_summary" in twin
    assert "latest_step_summary" in twin
    assert "disclaimer" in twin
    res_404 = client.get("/api/digital-twin/999")
    assert res_404.status_code == 404
test_endpoint("GET /api/digital-twin/{id}", check_digital_twin)

# 5. Prediction
def check_prediction():
    res = client.post("/api/predictions/glucose-spike", json={"patient_id": 1})
    assert res.status_code == 200
    pred = res.json()
    assert pred["patient_id"] == 1
    assert pred["horizon_minutes"] == 120
    assert pred["threshold_mg_dl"] == 180.0
    assert 0.0 <= pred["risk_score"] <= 1.0
    assert "feature_contributions" in pred
    assert "clinical_disclaimer" in pred
    res_404 = client.post("/api/predictions/glucose-spike", json={"patient_id": 999})
    assert res_404.status_code == 404
test_endpoint("POST /api/predictions/glucose-spike", check_prediction)

# 6. Alerts
def check_alerts():
    res = client.get("/api/alerts?patient_id=1")
    assert res.status_code == 200
    alerts = res.json()
    assert len(alerts) > 0
    sources = set(a["source"] for a in alerts)
    assert "observed_reading" in sources or "experimental_prediction" in sources
test_endpoint("GET /api/alerts", check_alerts)

# 7. What-If Simulation
def check_what_if():
    res = client.post("/api/simulation/what-if", json={
        "patient_id": 1,
        "additional_carbs_g": 45.0,
        "activity_minutes": 30.0
    })
    assert res.status_code == 200
    sim = res.json()
    assert sim["patient_id"] == 1
    assert sim["additional_carbs_g"] == 45.0
    assert sim["activity_minutes"] == 30.0
    assert sim["projected_carb_impact_mg_dl"] > 0
    assert sim["projected_activity_impact_mg_dl"] < 0
    assert "disclaimer" in sim
    # Input validation
    res_bad = client.post("/api/simulation/what-if", json={
        "patient_id": 1,
        "additional_carbs_g": -10.0,
        "activity_minutes": 0.0
    })
    assert res_bad.status_code == 422
test_endpoint("POST /api/simulation/what-if", check_what_if)

print("\nALL 11 API CONTRACT VERIFICATIONS COMPLETED SUCCESSFULLY.")
