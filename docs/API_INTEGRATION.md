# GlucoTwin — Backend API Integration & Contract Specification

**Target Backend**: Python FastAPI + Uvicorn  
**Protocol**: REST (HTTP/1.1 JSON) + WebSocket (Real-Time Telemetry Stream)  
**Authentication (Proposed)**: Bearer Token (JWT) / Clinical Session Header  
**Client Environment Variable**: `VITE_API_BASE_URL` (Default: `http://localhost:8000`)  
**Fallback Strategy**: `VITE_USE_MOCK_DATA=true` (Zero-backend standalone development)  

---

## 1. Overview & Architectural Decoupling

To prevent frontend development from being blocked by backend or machine learning model progress, all network communication in the React application is funneled through a centralized service client (`src/services/apiClient.js`).

```
┌────────────────────────────────────────────────────────┐
│                   React Components                     │
└──────────────────────────┬─────────────────────────────┘
                           │ (calls async methods)
                           ▼
┌────────────────────────────────────────────────────────┐
│            src/services/apiClient.js                   │
│                                                        │
│  if (import.meta.env.VITE_USE_MOCK_DATA === 'true') {  │
│      return mockDataService.getTrajectory(patientId);  │
│  } else {                                              │
│      return fetch(`${BASE_URL}/api/v1/...`);           │
│  }                                                     │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
        (Standalone Mock)           (Live Network)
               │                          │
               ▼                          ▼
    ┌──────────────────────┐   ┌─────────────────────────┐
    │ src/services/        │   │ FastAPI Server (Python) │
    │ mockData.js          │   │ http://localhost:8000   │
    └──────────────────────┘   └─────────────────────────┘
```

---

## 2. Expected REST Endpoints & JSON Schemas

### 2.1 Patient Management

#### `GET /api/v1/patients`
Retrieves the list of available synthetic patient archetypes for clinical review.

* **Response (200 OK)**:
```json
[
  {
    "id": "GT-9042",
    "name": "Sarah Jenkins",
    "age": 34,
    "gender": "Female",
    "archetype": "Type 1 Diabetes (Brittle / High Variability)",
    "bmi": 23.4,
    "current_glucose": 142,
    "trend": "rising",
    "risk_level": "moderate",
    "last_synced": "2026-10-10T14:30:00Z"
  },
  {
    "id": "GT-8105",
    "name": "Ramesh Sharma",
    "age": 52,
    "gender": "Male",
    "archetype": "Type 2 Diabetes (Postprandial Spikes)",
    "bmi": 28.1,
    "current_glucose": 118,
    "trend": "stable",
    "risk_level": "low",
    "last_synced": "2026-10-10T14:30:00Z"
  }
]
```

#### `GET /api/v1/patients/{id}`
Returns the comprehensive clinical background and baseline parameters for a specific patient.

* **Response (200 OK)**:
```json
{
  "id": "GT-9042",
  "name": "Sarah Jenkins",
  "age": 34,
  "gender": "Female",
  "archetype": "Type 1 Diabetes",
  "demographics": {
    "height_cm": 168,
    "weight_kg": 66.0,
    "bmi": 23.4,
    "diagnosis_year": 2018
  },
  "basal_profile": {
    "basal_rate_units_per_hour": 0.85,
    "insulin_sensitivity_factor": 45,
    "carb_insulin_ratio": 12,
    "target_range_mgdl": [70, 180]
  },
  "lab_history": [
    { "date": "2025-10-15", "hba1c": 7.4, "fasting_glucose": 138 },
    { "date": "2026-02-10", "hba1c": 7.1, "fasting_glucose": 126 },
    { "date": "2026-06-18", "hba1c": 6.8, "fasting_glucose": 118 }
  ],
  "active_medications": [
    { "name": "Insulin Glargine (Basal)", "dosage": "20 Units", "frequency": "Nightly" },
    { "name": "Insulin Aspart (Bolus)", "dosage": "1 Unit per 12g Carbs", "frequency": "Pre-meal" }
  ]
}
```

---

### 2.2 Telemetry & Continuous Sensor Signals

#### `GET /api/v1/patients/{id}/telemetry?hours=4`
Fetches high-resolution historical continuous glucose (CGM) readings synchronized with heart rate and HRV.

* **Response (200 OK)**:
```json
{
  "patient_id": "GT-9042",
  "window_hours": 4,
  "sampling_interval_minutes": 5,
  "readings": [
    {
      "timestamp": "2026-10-10T10:30:00Z",
      "glucose_mgdl": 115,
      "heart_rate_bpm": 72,
      "hrv_rmssd_ms": 48,
      "event": null
    },
    {
      "timestamp": "2026-10-10T12:00:00Z",
      "glucose_mgdl": 145,
      "heart_rate_bpm": 88,
      "hrv_rmssd_ms": 36,
      "event": { "type": "meal", "description": "Lunch", "carbs_g": 52 }
    },
    {
      "timestamp": "2026-10-10T12:15:00Z",
      "glucose_mgdl": 168,
      "heart_rate_bpm": 82,
      "hrv_rmssd_ms": 40,
      "event": { "type": "bolus", "description": "Rapid Insulin", "units": 4.2 }
    }
  ],
  "sensor_health": {
    "valid_packets_pct": 99.4,
    "battery_pct": 86,
    "drift_detected": false
  }
}
```

---

### 2.3 Predictions & Explainable AI (XAI)

#### `GET /api/v1/patients/{id}/predictions`
Fetches the ML model forward-looking 2-hour forecast, risk tier, and confidence bounds.

* **Response (200 OK)**:
```json
{
  "patient_id": "GT-9042",
  "forecast_generated_at": "2026-10-10T14:30:00Z",
  "horizon_minutes": 120,
  "risk_assessment": {
    "spike_probability_pct": 58.0,
    "risk_tier": "moderate",
    "projected_peak_mgdl": 198,
    "time_to_peak_minutes": 55,
    "hypo_risk_pct": 8.0
  },
  "projected_trajectory": [
    { "minutes_ahead": 15, "predicted_glucose": 152, "ci_lower_95": 144, "ci_upper_95": 160 },
    { "minutes_ahead": 30, "predicted_glucose": 174, "ci_lower_95": 160, "ci_upper_95": 188 },
    { "minutes_ahead": 45, "predicted_glucose": 192, "ci_lower_95": 172, "ci_upper_95": 210 },
    { "minutes_ahead": 60, "predicted_glucose": 198, "ci_lower_95": 175, "ci_upper_95": 220 },
    { "minutes_ahead": 90, "predicted_glucose": 176, "ci_lower_95": 150, "ci_upper_95": 204 },
    { "minutes_ahead": 120, "predicted_glucose": 150, "ci_lower_95": 124, "ci_upper_95": 180 }
  ]
}
```

#### `GET /api/v1/patients/{id}/xai`
Returns SHAP-style feature attribution weights explaining the primary physiological factors driving the prediction.

* **Response (200 OK)**:
```json
{
  "patient_id": "GT-9042",
  "model_type": "Proposed XGBoost Regressor (Demo)",
  "baseline_expected_glucose": 135,
  "predicted_glucose": 198,
  "features": [
    {
      "name": "Active Carbohydrate Digestion (Lunch)",
      "impact_mgdl": 42.4,
      "direction": "positive",
      "category": "lifestyle"
    },
    {
      "name": "Insulin on Board (IOB Deficit)",
      "impact_mgdl": 24.1,
      "direction": "positive",
      "category": "pharmacology"
    },
    {
      "name": "Resting Heart Rate Elevation (Stress/Autonomic)",
      "impact_mgdl": 6.8,
      "direction": "positive",
      "category": "biometric"
    },
    {
      "name": "Residual Physical Activity (Walking)",
      "impact_mgdl": -10.3,
      "direction": "negative",
      "category": "lifestyle"
    }
  ]
}
```

---

### 2.4 What-If Counterfactual Simulation

#### `POST /api/v1/simulation/counterfactual`
Simulates the Digital Twin metabolic response when candidate lifestyle or pharmacological inputs are adjusted.

* **Request Body**:
```json
{
  "patient_id": "GT-9042",
  "activity_adjustment_minutes": 20,
  "sleep_adjustment_hours": 1.0,
  "carb_adjustment_grams": 45,
  "insulin_adjustment_units": 2.0
}
```

* **Response (200 OK)**:
```json
{
  "simulation_id": "sim_77209",
  "baseline_peak_mgdl": 198,
  "simulated_peak_mgdl": 164,
  "peak_reduction_mgdl": 34,
  "baseline_tir_pct": 78,
  "simulated_tir_pct": 86,
  "risk_tier_change": {
    "before": "moderate",
    "after": "low"
  },
  "comparative_trajectory": [
    { "time_min": 0, "baseline_glucose": 142, "simulated_glucose": 142 },
    { "time_min": 30, "baseline_glucose": 174, "simulated_glucose": 158 },
    { "time_min": 60, "baseline_glucose": 198, "simulated_glucose": 164 },
    { "time_min": 90, "baseline_glucose": 176, "simulated_glucose": 148 },
    { "time_min": 120, "baseline_glucose": 150, "simulated_glucose": 132 }
  ]
}
```

---

### 2.5 Alert Center & Clinical Triage

#### `GET /api/v1/alerts?status=active`
* **Response (200 OK)**:
```json
[
  {
    "id": "alt-101",
    "patient_id": "GT-9042",
    "timestamp": "2026-10-10T14:15:00Z",
    "severity": "critical",
    "title": "Impending Hypoglycemia Predicted",
    "description": "Metabolic model projects glucose dropping below 65 mg/dL within 35 minutes.",
    "trigger_source": "ML Predictive Engine",
    "status": "unacknowledged"
  },
  {
    "id": "alt-102",
    "patient_id": "GT-9042",
    "timestamp": "2026-10-10T14:25:00Z",
    "severity": "warning",
    "title": "Postprandial Glucose Excursion",
    "description": "Simulated carbohydrate absorption exceeds current basal rate.",
    "trigger_source": "Compartmental Twin Model",
    "status": "unacknowledged"
  }
]
```

#### `POST /api/v1/alerts/{id}/acknowledge`
* **Request Body**: `{ "clinician_id": "DR-501", "action_taken": "Advised 15g fast-acting carbs" }`
* **Response (200 OK)**: `{ "id": "alt-101", "status": "acknowledged", "acknowledged_at": "2026-10-10T14:32:00Z" }`

---

### 2.6 Digital Twin State & Quality

#### `GET /api/v1/twin/{id}/status`
* **Response (200 OK)**:
```json
{
  "patient_id": "GT-9042",
  "engine_state": "synchronized",
  "latency_ms": 14,
  "last_calibration_time": "2026-10-10T14:00:00Z",
  "model_type": "Multi-Compartment PK/PD + LightGBM Residual",
  "active_iob_units": 1.2,
  "active_cob_grams": 35.0,
  "metabolic_drift_score": 0.04
}
```

---

## 3. Real-Time Telemetry via WebSocket (Proposed)

* **URL**: `ws://localhost:8000/ws/telemetry/{patient_id}`
* **Message Frame (JSON)**:
```json
{
  "type": "TELEMETRY_TICK",
  "timestamp": "2026-10-10T14:35:00Z",
  "glucose_mgdl": 144,
  "heart_rate_bpm": 74,
  "hrv_rmssd_ms": 46,
  "projected_60m": 196
}
```
* **Frontend Handling**: When connected, incoming frames push onto the Recharts time-series array. If disconnected, the frontend falls back to the local ticker hook (`useTelemetryStream.js`).

---

## 4. Frontend Network Resiliency & Mock Strategy

1. **Environment Flag**: In `.env`, setting `VITE_USE_MOCK_DATA=true` diverts all calls to `mockData.js`.
2. **Offline Detection**: An ambient banner appears if network requests fail: *"Backend Offline — Seamlessly Displaying Local Synthetic Demonstration Data"*.
3. **HTTP Status Code Guardrails**:
   - `404 Not Found`: Displays empty clinical state illustration.
   - `500 Internal Error`: Renders a non-intrusive alert card indicating simulation calculation error.
