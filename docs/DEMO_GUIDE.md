# GlucoTwin — 5-Minute Hackathon Demonstration Guide

## Executive Overview
**GlucoTwin** is a software-only predictive digital twin prototype designed for proactive glucose-risk surveillance. It integrates continuous synthetic glucose telemetry, autonomic vital vectors, heuristic counterfactual scenario simulation, and experimental machine-learning spike forecasting into a unified clinical monitoring dashboard.

> **Mandatory Disclaimer**: This application is an educational and research prototype built entirely on synthetic telemetry models. It does NOT connect to physical IoT hardware, medical sensors, or external clinical services, and must NOT be used for insulin dosing, dietary prescription, or medical diagnostic decision-making.

---

## 1. Local Environment & Startup Commands

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Node.js 18+ & npm
- Local SQLite (bundled with Python)

### Step 1: Start the FastAPI Backend
Open a terminal in the project root:
```bash
cd D:\Projects\Gluco-Twin\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Backend Health Check**: http://127.0.0.1:8000/health
- **Swagger Interactive API Documentation**: http://127.0.0.1:8000/docs

### Step 2: Start the Vite React Frontend
Open a second terminal in the project root:
```bash
cd D:\Projects\Gluco-Twin\frontend
npm run dev -- --host 127.0.0.1 --port 5173
```
- **Live Application URL**: http://127.0.0.1:5173/

---

## 2. Repeatable 5-Minute Presentation Script

### Minute 1: The Problem & The Software-Only Approach (0:00 – 1:00)
- **Hook**: "Continuous glucose management is fundamentally reactive today — patients only discover a dangerous glucose spike after it occurs. GlucoTwin demonstrates an intelligent digital twin that synthesizes continuous telemetry, physiological trend trajectory, and forward risk forecasting."
- **Architecture**: Point to the status badge on the top right showing `Backend: Online` and explain the software-only synthetic architecture.
- **Key Message**: "To protect privacy and ensure total reproducibility, GlucoTwin operates entirely on synthetic patient profiles seeded into a local SQLite database, without requiring physical IoT sensors or paid cloud APIs."

### Minute 2: Synthetic Cohort & Continuous Telemetry (1:00 – 2:00)
- **Action**: Select **Patient 1 (Ananya Sharma, Type 2 Diabetes)** using the Topbar patient selector or Cohort cards.
- **Highlight**:
  - Show the **Current Glucose Card** (`mg/dL`) and Target Time-In-Range badge (`70–180 mg/dL`).
  - Point out autonomic vital telemetry: **Heart Rate (bpm)** and **Heart Rate Variability (ms)** synchronised at 15-minute sampling intervals.
  - Show the **Glucose Monitoring Time-Series Chart**: Switch between the 24h, 48h, and 7d monitoring windows to demonstrate real-time data filtering.

### Minute 3: Digital Twin Intelligence Vector (2:00 – 3:00)
- **Action**: Scroll to the **Patient Digital Twin Intelligence** section.
- **Highlight**:
  - **Phenotype Profile Vector**: Patient age, clinical diagnosis type, diagnosis span, weight, height, and computed BMI.
  - **Telemetry & Baseline Delta**: 24-hour baseline mean, 24-hour extrema (`min – max mg/dL`), 1-hour glycemic trajectory rate of change ($\text{mg/dL/min}$ slope), and 1-hour trajectory delta ($\Delta$).
  - **Surveillance State**: Display the `SYNCHRONIZED` telemetry freshness badge and active alert count with severity breakdown (`critical`, `warning`, `info`).

### Minute 4: Machine Learning Forecasting & Alert Triage (3:00 – 4:00)
- **Action**: Scroll to the **Glucose Spike Prediction Engine**.
  - Show the **Forward Horizon (2 hours)** and **Glycemic Cut-off (180 mg/dL)**.
  - Highlight the **Uncalibrated Model Score** with explicit caution: *"We explicitly report this score as uncalibrated rather than fabricating statistical confidence. It is an experimental demonstration model."*
  - Review the **Feature Contributions (XAI)**: Show how current glucose and rate of change contribute to the spike risk tier.
- **Action**: Scroll to the **Clinical Risk Alert Engine**.
  - Identify an active `observed_hyperglycemia` alert.
  - Click **Acknowledge**: Note the status transition to `acknowledged` with recorded timestamp.
  - Click **Resolve**: Note the final state transition to `resolved`.
  - Click **Scan / Re-evaluate**: Demonstrate that the alert engine is completely idempotent and does not create duplicate alerts.

### Minute 5: What-If Counterfactual Sandbox & Conclusion (4:00 – 5:00)
- **Action**: Scroll to the **What-If Counterfactual Sandbox**.
  - Adjust the **Additional Meal Carbohydrates slider** to **45g**.
  - Adjust the **Physical Exertion slider** to **25 min**.
  - Observe the reactive recalculation of the scenario projection:
    - Postprandial glucose projection (`mg/dL`).
    - Glycemic influx from carbs ($+\Delta$) and muscular clearance ($-\Delta$).
    - Dynamic status badge indicating whether target range is maintained or breached ($\ge 180 \text{ mg/dL}$).
  - Point out the **Documented Heuristic Assumptions** and the **Formula Version** badge (`1.0.0-illustrative-heuristic`).
- **Wrap-up**: Switch cohort to **Patient 2 (Rajesh Kumar)** to prove live race-free cohort switching, and conclude: *"GlucoTwin demonstrates how predictive digital twins empower proactive glycemic oversight while upholding strict explainability and scientific honesty."*

---

## 3. Automated Test Verification
Run the backend automated test suite:
```bash
cd D:\Projects\Gluco-Twin\backend
python -m pytest tests/ -v
```
**Expected Outcome**: 59 passed tests in ~12 seconds.

Run frontend code validation:
```bash
cd D:\Projects\Gluco-Twin\frontend
npm run lint
npm run build
```
**Expected Outcome**: 0 lint errors, production bundle built in < 1 second.

---

## 4. Troubleshooting & FAQ

| Issue | Cause | Resolution |
|---|---|---|
| **Backend Unreachable in Topbar** | FastAPI server not started on port 8000 | Run `python -m uvicorn app.main:app --port 8000` |
| **Model Artifact Unavailable (503)** | Missing `pipeline.joblib` | Check `backend/app/ml/artifacts/pipeline.joblib` exists |
| **Empty Chart on Patient Selection** | Selected patient has no readings in window | Check hours window dropdown (select 24h or 48h) |
| **Alert Action Fails** | Attempting to acknowledge a resolved alert | Resolved alerts are locked; only active/acknowledged alerts can transition |
| **What-If Sliders Frozen** | Viewport constraint or mobile touch event | Use mouse drag or keyboard arrow keys |
