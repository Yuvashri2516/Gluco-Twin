# Phase 3: Digital Twin Intelligence, Alert Management, and What-If Simulation Report

## 1. Phase Objective
The objective of Phase 3 is to audit, harden, and complete the Digital Twin intelligence summary, alert management engine, and counterfactual What-If simulation components in GlucoTwin. This ensures a clinically explainable, deterministic, interactive, and testable hackathon demonstration utilizing synthetic patient profiles and simulated sensor telemetry without external paid dependencies.

---

## 2. Existing Implementation Reviewed
The following components were audited prior to making any modifications:
- **Backend Schemas & Models**: `backend/app/schemas.py`, `backend/app/models.py`, `backend/app/database.py`
- **FastAPI Endpoints**:
  - Digital Twin & Simulation: `backend/app/routers/twin.py`
  - Alert Engine & Triage: `backend/app/routers/alerts.py`, `backend/app/alerts_engine.py`
  - Glucose Prediction: `backend/app/routers/predictions.py`
  - Readings & Telemetry: `backend/app/routers/readings.py`
- **Frontend Dashboard Components**:
  - `frontend/src/components/DigitalTwinPanel.jsx`
  - `frontend/src/components/AlertsPanel.jsx`
  - `frontend/src/components/WhatIfSimulation.jsx`
  - `frontend/src/api/client.js`
- **Automated Test Suites**:
  - `backend/tests/test_alerts_engine.py`
  - `backend/tests/test_feature_engineering.py`
  - `backend/tests/test_label_construction.py`
  - `backend/tests/test_prediction_api.py`
  - `backend/tests/test_readings_api.py`

---

## 3. Features Already Present
- **FastAPI Framework & SQLite Database**: 5 seeded synthetic patients (`#1` through `#5`) with multi-day 15-minute continuous glucose and autonomic vital readings.
- **Initial Digital Twin Summary**: Basic patient profile demographic vector, latest glucose and vitals, 24h/1h mean glucose, glycemic variability ($\sigma$), and trend trajectory slope.
- **Alert Engine Core**: Rule-based evaluation of observed telemetry thresholds (hypoglycemia, severe hypoglycemia, hyperglycemia, severe hyperglycemia, autonomic depression) and ML spike prediction flags.
- **Deduplication Strategy**: Preliminary deduplication keys using `obs:{patient_id}:{alert_type}:{reading_id}` and `pred:{patient_id}:{time_slug}`.
- **Basic What-If Simulation**: Weight-adjusted and clinical-phenotype-adjusted heuristic for postprandial carbohydrate influx and physical exertion clearance.
- **React Frontend**: Modern, dark-mode medical dashboard utilizing modular cards, interactive sliders, filter toolbars, and patient cohort switching.

---

## 4. Confirmed Bugs & Deficiencies Found Before Changes
1. **Missing Digital Twin Trend Metrics**: `DigitalTwinDetailResponse` lacked 24h glucose extrema (`min_glucose_24h`, `max_glucose_24h`), 1h extrema (`min_glucose_1h`, `max_glucose_1h`), 1h net trajectory delta (`glucose_change_1h`), and latest vital timestamps (`latest_vital_timestamp`).
2. **Missing Alert Breakdown in Twin Summary**: The twin summary only exposed `active_alerts_count`, omitting `acknowledged_alerts_count`, `resolved_alerts_count`, `most_recent_alert`, and the severity distribution (`critical`, `warning`, `info`).
3. **Unchecked Alert Lifecycle Transitions**: Acknowledging an alert that had already been resolved succeeded with HTTP 200 without raising an error. Resolving an already-resolved alert was not strictly rejected. Invalid transitions did not return HTTP 400 Bad Request.
4. **Unvalidated What-If Simulation Inputs**: Negative values for additional carbohydrates (`additional_carbs_g: -50`) or physical activity (`activity_minutes: -30`) were silently clamped via `max(0.0, ...)` rather than returning strict HTTP 422 Unprocessable Entity validation errors. Unreasonably large inputs were also accepted without schema constraints.
5. **Missing Telemetry & Freshness Warnings**: Patients with zero readings or stale readings (>24 hours) did not have formal `data_freshness_status` indicators or explicit data-quality alert categories (`data_missing`, `data_stale`).
6. **Simulation Baseline Ambiguity**: When simulating a patient with zero historical records without providing an `as_of_glucose`, the endpoint defaulted silently to 120 mg/dL without recording this assumption in `data_quality_warnings`.

---

## 5. Changes Implemented
1. **Schema Enhancements (`backend/app/schemas.py`)**:
   - Expanded `DigitalTwinDetailResponse` with: `latest_vital_timestamp`, `min_glucose_24h`, `max_glucose_24h`, `min_glucose_1h`, `max_glucose_1h`, `glucose_change_1h`, `data_freshness_status` ("fresh" | "stale" | "no_data"), `hours_since_last_reading`, `total_vital_readings_24h`, `acknowledged_alerts_count`, `resolved_alerts_count`, `alert_severity_distribution`, and `most_recent_alert`.
   - Added Pydantic `Field` validation constraints to `WhatIfSimulationRequest`:
     - `additional_carbs_g`: `ge=0.0`, `le=300.0`
     - `activity_minutes`: `ge=0.0`, `le=360.0`
     - `as_of_glucose`: `ge=20.0`, `le=600.0`
   - Added `formula_version` (`1.0.0-illustrative-heuristic`) and `data_quality_warnings` to `WhatIfSimulationResponse`.
2. **Alert Engine Triage & Lifecycle Hardening (`backend/app/routers/alerts.py`)**:
   - Enforced strict state transitions:
     - Transition from `active` -> `acknowledged`: HTTP 200.
     - Transition from `acknowledged` -> `resolved` or `active` -> `resolved`: HTTP 200.
     - Transition from `resolved` -> `acknowledged`: HTTP 400 (`Invalid alert transition: Alert #X is already resolved and cannot be acknowledged`).
     - Transition from `resolved` -> `resolved`: HTTP 400 (`Invalid alert transition: Alert #X is already resolved`).
3. **Data Quality & Stale Alerts (`backend/app/alerts_engine.py`)**:
   - Added `data_missing` alert generation when evaluating synthetic patients with no sensor readings (`obs:{patient_id}:data_missing:no_readings`).
   - Added `data_stale` alert generation when evaluating telemetry older than 24 hours (`obs:{patient_id}:data_stale:{day_slug}`).
   - Ensured deterministic deduplication keys across all alert categories to prevent alert table bloat.
4. **Digital Twin Intelligence Router (`backend/app/routers/twin.py`)**:
   - Computed 24h min/max and 1h min/max/change metrics safely using NumPy.
   - Handled empty patient telemetry cleanly (returning `null` stats and `data_freshness_status: "no_data"` without raising 500 exceptions).
   - Formatted experimental prediction snapshots with horizon, timestamp, model version, and uncalibrated risk disclaimer.
   - Handled simulations without baseline by applying a default 110.0 mg/dL baseline with an explicit notice in `data_quality_warnings`.
5. **Frontend UI Enhancements**:
   - `frontend/src/components/DigitalTwinPanel.jsx`: Integrated 24h Extrema (`min – max mg/dL`), 1h Trajectory Delta (`±Δ mg/dL`), Telemetry Freshness status badge (`SYNCHRONIZED`, `STALE TELEMETRY`, or `NO TELEMETRY`), and alert breakdown by severity (`X Active (Y crit, Z warn)`).
   - `frontend/src/components/WhatIfSimulation.jsx`: Displayed heuristic formula version badge (`1.0.0-illustrative-heuristic`) and dynamic data quality warning boxes.
6. **Automated Verification Suite (`backend/tests/test_phase3_digital_twin.py`)**:
   - Created a comprehensive 13-test regression suite covering empty patients, stale patients, partial vitals, patient isolation, alert lifecycle transitions, negative input rejection, excessive input rejection, and default baseline handling.

---

## 6. Digital Twin Response Structure
```json
{
  "patient_id": 1,
  "patient_name": "Patient Alpha",
  "diabetes_type": "Type 2",
  "age": 45,
  "gender": "Female",
  "years_since_diagnosis": 5,
  "weight_kg": 72.0,
  "height_cm": 168.0,
  "bmi": 25.5,
  "latest_glucose": 205.0,
  "latest_glucose_timestamp": "2026-10-18T05:00:00",
  "latest_heart_rate": 79.0,
  "latest_hrv": 38.0,
  "latest_vital_timestamp": "2026-10-18T05:00:00",
  "mean_glucose_1h": 195.0,
  "mean_glucose_24h": 162.5,
  "min_glucose_24h": 140.0,
  "max_glucose_24h": 205.0,
  "min_glucose_1h": 175.0,
  "max_glucose_1h": 205.0,
  "glucose_change_1h": 30.0,
  "glucose_std_1h": 12.5,
  "glucose_trend_slope": 0.5,
  "mean_hr_1h": 76.5,
  "mean_hrv_1h": 40.2,
  "data_freshness_status": "fresh",
  "hours_since_last_reading": 0.2,
  "data_quality_warnings": [],
  "total_readings_24h": 9,
  "total_vital_readings_24h": 8,
  "active_alerts_count": 1,
  "acknowledged_alerts_count": 0,
  "resolved_alerts_count": 0,
  "alert_severity_distribution": {
    "critical": 0,
    "warning": 1,
    "info": 0
  },
  "most_recent_alert": { ... },
  "recent_alerts": [ ... ],
  "latest_prediction": {
    "risk_score": 0.378,
    "spike_predicted": false,
    "risk_category": "MODERATE",
    "model_version": "0.1.0-prototype",
    "prediction_timestamp": "2026-10-18T05:00:00",
    "prediction_horizon_minutes": 120,
    "is_uncalibrated_experimental": true,
    "clinical_disclaimer": "Uncalibrated prototype score; not a validated clinical probability."
  },
  "disclaimer": "RESEARCH PROTOTYPE ONLY: Built on synthetic telemetry. Not clinically validated. Not for diagnosis or treatment decisions."
}
```

---

## 7. Alert Categories and Demonstration Thresholds
| Category | Alert Type | Trigger Condition | Severity | Source |
|---|---|---|---|---|
| **GLUCOSE_THRESHOLD** | `observed_severe_hypoglycemia` | Value < 54.0 mg/dL | Critical | `observed_reading` |
| **GLUCOSE_THRESHOLD** | `observed_hypoglycemia` | Value < 70.0 mg/dL | Warning | `observed_reading` |
| **GLUCOSE_THRESHOLD** | `observed_hyperglycemia` | Value $\ge$ 180.0 mg/dL | Warning | `observed_reading` |
| **GLUCOSE_THRESHOLD** | `observed_severe_hyperglycemia` | Value $\ge$ 250.0 mg/dL | Critical | `observed_reading` |
| **HEART_RATE_THRESHOLD** | `observed_autonomic_depression` | HR $\ge$ 100 bpm & HRV $\le$ 25 ms | Warning | `observed_reading` |
| **DATA_STALE** | `data_stale` | Reading age > 24.0 hours | Warning | `observed_reading` |
| **DATA_MISSING** | `data_missing` | Total readings = 0 | Info | `observed_reading` |
| **MODEL_FLAG** | `predicted_glucose_spike` | Risk score $\ge$ 0.50 (score $\ge$ 0.65 for critical) | Warning / Critical | `experimental_prediction` |

*Note: All thresholds are demonstration values for hackathon prototyping and do not represent medical clinical guidelines.*

---

## 8. Deduplication Strategy
To prevent uncontrolled alert growth during repeated evaluations or dashboard polling, deterministic deduplication keys are assigned:
- **Observed Reading Alerts**: `obs:{patient_id}:{alert_type}:{reading_id}`
- **Data Missing Alerts**: `obs:{patient_id}:data_missing:no_readings`
- **Data Stale Alerts**: `obs:{patient_id}:data_stale:{YYYYMMDD}`
- **Model Prediction Alerts**: `pred:{patient_id}:{YYYYMMDDHHMM}`

Before creating any alert in the database, the engine queries `Alert.dedup_key`. If an alert with the key exists, generation is skipped.

---

## 9. Alert Lifecycle
State transitions follow a strict unidirectional workflow:
$$\text{ACTIVE} \longrightarrow \text{ACKNOWLEDGED} \longrightarrow \text{RESOLVED}$$

- `POST /api/alerts/{id}/acknowledge`:
  - Allowed from: `active`, `acknowledged` (idempotent).
  - Prohibited from: `resolved` $\rightarrow$ returns **HTTP 400 Bad Request**.
  - Updates: `acknowledged = True`, `acknowledged_at = UTC NOW`, `status = "acknowledged"`.
- `POST /api/alerts/{id}/resolve`:
  - Allowed from: `active`, `acknowledged`.
  - Prohibited from: `resolved` $\rightarrow$ returns **HTTP 400 Bad Request**.
  - Updates: `status = "resolved"`, `resolved_at = UTC NOW`.

---

## 10. What-If Simulation Formula and Assumptions
The counterfactual simulation uses a deterministic, software-only heuristic:

$$\text{Projected Glucose} = \max(40.0, \; G_{\text{baseline}} + \Delta_{\text{carb}} + \Delta_{\text{activity}})$$

Where:
1. **Body Weight Scaling Factor**:
   $$W_{\text{factor}} = \frac{70.0}{\max(30.0, \; \text{weight\_kg})}$$
2. **Clinical Diabetes Type Sensitivity Modifier ($k_{\text{type}}$)**:
   - Type 1: $1.30$ (reduced endogenous insulin buffer)
   - Type 2: $1.15$ (insulin resistance)
   - Pre-diabetic: $0.90$ (mild glycemic impairment)
   - Default: $1.00$
3. **Carbohydrate Glycemic Influx**:
   $$\Delta_{\text{carb}} = \text{carbs} \times (0.40 \times W_{\text{factor}} \times k_{\text{type}})$$
4. **Physical Exertion Glycemic Clearance**:
   $$\Delta_{\text{activity}} = -(\text{activity\_minutes} \times 0.75)$$

### Documented Heuristic Assumptions
1. Linear carbohydrate absorption curve without delayed gastric emptying.
2. Volume of distribution inversely proportional to patient body weight (referenced to 70 kg standard).
3. Uniform moderate physical exertion (~0.75 mg/dL clearance per minute of activity).
4. Stable basal coverage without bolus compensation.
5. Strictly illustrative and non-diagnostic; does not prescribe insulin doses.

---

## 11. API Examples

### Digital Twin Detail
```http
GET /api/digital-twin/1 HTTP/1.1
Host: 127.0.0.1:8000
```
*Response*: HTTP 200 OK (Returns `DigitalTwinDetailResponse` JSON).

### What-If Simulation
```http
POST /api/simulation/what-if HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json

{
  "patient_id": 1,
  "additional_carbs_g": 45.0,
  "activity_minutes": 30.0,
  "as_of_glucose": 135.0
}
```
*Response*: HTTP 200 OK. Returns projected glucose `142.1 mg/dL`, carb impact `+29.6 mg/dL`, activity impact `-22.5 mg/dL`, breach status `false`.

### Negative Input Validation Rejection
```http
POST /api/simulation/what-if HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json

{
  "patient_id": 1,
  "additional_carbs_g": -15.0
}
```
*Response*: HTTP 422 Unprocessable Entity (`Input should be greater than or equal to 0`).

---

## 12. Tests Executed and Actual Results
All 49 automated backend tests passed cleanly in `11.19s`:

| Test Module | Tests | Result |
|---|---|---|
| `test_phase3_digital_twin.py` | 13 | **13 PASSED** |
| `test_alerts_engine.py` | 10 | **10 PASSED** |
| `test_prediction_api.py` | 5 | **5 PASSED** |
| `test_readings_api.py` | 14 | **14 PASSED** |
| `test_feature_engineering.py` | 4 | **4 PASSED** |
| `test_label_construction.py` | 3 | **3 PASSED** |
| **Total** | **49** | **49 PASSED (100%)** |

Frontend checks:
- `npm run lint`: **0 errors**, 13 warnings (all pre-existing unused variable notices).
- `npm run build`: **0 errors**, production bundle built successfully in `941ms`.

---

## 13. Known Limitations
1. **Synthetic Telemetry Only**: Telemetry is generated via mathematical simulation models and does not represent real continuous glucose monitors or wearable ECG monitors.
2. **Simplified What-If Heuristics**: The counterfactual simulation uses linear approximations of postprandial glucose dynamics rather than complex compartmental differential equations (e.g., Hovorka or Bergman minimal models).
3. **Uncalibrated Spike Model**: The experimental logistic regression spike model was trained on synthetic data and exhibits weak generalization on some evaluation splits. Model scores must remain labeled as uncalibrated risk scores.

---

## 14. Steps to Run the Backend
```bash
cd D:\Projects\Gluco-Twin\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 15. Steps to Run the Frontend
```bash
cd D:\Projects\Gluco-Twin\frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

---

## 16. Manual Verification Checklist
- [x] Select Patient 1 (Ananya Sharma) -> Verify Digital Twin intelligence loads with complete stats.
- [x] Check 24h extrema (`min – max mg/dL`) and 1h trajectory delta (`±Δ mg/dL`).
- [x] Verify Telemetry Freshness status badge displays `SYNCHRONIZED`.
- [x] Adjust carbohydrate and physical activity sliders in What-If Sandbox -> Verify real-time projection update.
- [x] Verify heuristic formula version badge (`1.0.0-illustrative-heuristic`) is visible.
- [x] Review Alert Center -> Verify active alerts list severity breakdown, triggering values, and timestamps.
- [x] Acknowledge an alert -> Verify status updates to `acknowledged`.
- [x] Resolve an alert -> Verify status updates to `resolved`.
- [x] Switch cohort patient to Patient 2 (Rajesh Kumar) -> Verify all cards update immediately without stale data or race conditions.

---

## 17. Safety Disclaimers
> **RESEARCH & HACKATHON PROTOTYPE ONLY**
> 
> GlucoTwin is designed solely for demonstration, academic, and research purposes. All telemetry, patient records, and vitals are synthetically generated.
> 
> The Digital Twin representations, What-If counterfactual scenario calculations, and experimental glucose-spike predictions do NOT constitute medical diagnosis, clinical treatment plans, or insulin dosing guidelines. Never alter insulin administration or medical regimens based on software prototype outputs.
