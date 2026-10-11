# GlucoTwin

**An Intelligent Predictive Digital Twin for Proactive Glucose-Risk Monitoring**

> [!WARNING]
> **ACADEMIC & HACKATHON RESEARCH PROTOTYPE ONLY**
> This application is built exclusively with synthetic patient data for educational and research demonstration purposes. It is **NOT** clinically validated, **NOT** a certified medical device, and **MUST NOT** be used for clinical diagnosis, treatment decisions, or medical management.

---

## 1. Problem Statement

Type 1, Type 2, and pre-diabetic patients continuously face acute glycemic excursions—sudden postprandial glucose spikes (hyperglycemia $\ge 180\text{ mg/dL}$) and severe nocturnal drops (hypoglycemia $< 70\text{ mg/dL}$). While Continuous Glucose Monitors (CGMs) provide retrospective and real-time telemetry, standard healthcare monitoring remains reactive: clinicians and patients typically review historical logs hours or days after adverse events occur. 

Key challenges in proactive diabetes care:
- **Reactive Alerting:** Standard CGMs alert only after thresholds have already been breached.
- **Cognitive Overload:** Clinicians lack continuous physiological context combining multi-vital signals (heart rate, HRV, circadian phase) with glycemic trends.
- **Lack of Counterfactual Sandboxing:** Patients cannot safely simulate *"What if I consume 45g carbs now?"* or *"What if I exercise for 30 minutes?"* before taking real-world actions.

---

## 2. Proposed Solution: The GlucoTwin Platform

**GlucoTwin** introduces a personalized Patient Digital Twin that bridges real-time telemetry ingestion, machine learning early warning, and counterfactual simulation:
1. **Multi-Vital Digital Twin State:** Aggregates time-series CGM readings, heart rate (HR), heart rate variability (HRV), and circadian rhythm into an active physiological snapshot with 24-hour baseline deltas.
2. **Experimental ML Glucose-Spike Forecaster:** Evaluates historical physiological signals ($t \le T$) to predict whether glucose will breach $180\text{ mg/dL}$ within a 2-hour forward horizon.
3. **Dual-Source Alert Engine:** Disentangles **Observed Telemetry Alerts** (real synthetic readings crossing demo thresholds) from **Model-Predicted Alerts** (experimental ML risk forecasts), complete with full acknowledgement and resolution workflows.
4. **What-If Counterfactual Sandbox:** Deterministic, software-only simulation calculating hypothetical meal carbohydrate and physical exertion impacts anchored to the patient's actual baseline.
5. **In-Dashboard Notification Workflow:** Real-time topbar notification center and sidebar badge counter alerting clinical staff to active risk events.

---

## 3. System Architecture & Tech Stack

```
   ┌──────────────────────────────────────────────────────────────┐
   │                  React 19 / Vite Frontend                    │
   │   - Patient Telemetry Dashboard & Multi-Vital Trends         │
   │   - Clinical Alerts Center (Observed vs Predicted)           │
   │   - Patient Digital Twin Intelligence Panel                  │
   │   - What-If Counterfactual Sandbox                           │
   │   - In-Dashboard Notification Center                         │
   └──────────────────────────────┬───────────────────────────────┘
                                  │ HTTP / REST API (port 8000)
   ┌──────────────────────────────▼───────────────────────────────┐
   │                     FastAPI Backend                          │
   │   - /api/patients              - /api/readings               │
   │   - /api/predictions           - /api/alerts                 │
   │   - /api/digital-twin          - /api/simulation/what-if     │
   └──────────────┬───────────────────────────────┬───────────────┘
                  │                               │
   ┌──────────────▼───────────────┐ ┌─────────────▼───────────────┐
   │    Alert & Twin Engine       │ │   Machine Learning Engine   │
   │  - Configurable Demo Limits  │ │  - StandardScaler + LogReg  │
   │  - Deterministic Dedup       │ │  - 1h Lookback Features     │
   │  - Idempotent Lifecycle      │ │  - 2h Horizon Spike Risk    │
   └──────────────┬───────────────┘ └─────────────┬───────────────┘
                  │                               │
   ┌──────────────▼───────────────────────────────▼───────────────┐
   │             SQLite Database (via SQLAlchemy ORM)             │
   │   Patients │ GlucoseReadings │ VitalReadings │ Alerts        │
   └──────────────────────────────────────────────────────────────┘
```

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend UI** | React 19, Vite, Recharts, Lucide Icons | Responsive clinical dashboard & visualizations |
| **Styling** | Vanilla CSS (CSS Variables, Flexbox/Grid) | High-performance medical dark-mode design system |
| **Backend API** | Python 3.14 / 3.11+, FastAPI, Uvicorn | Async REST endpoints, Pydantic v2 validation |
| **Persistence** | SQLite, SQLAlchemy ORM | Local, zero-configuration relational storage |
| **ML Engine** | scikit-learn, NumPy, Pandas, Joblib | Feature extraction and spike probability inference |

---

## 4. Quick Start & Execution Instructions

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Node.js 18+ (tested with npm 10+)

### Step 1: Start Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000
```
- API Swagger Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

*Note: On first startup, the database `glucotwin.db` is automatically created, verified, seeded with 5 synthetic patient cohorts (72 hours of 15-minute readings), and pre-evaluated with initial demo alerts.*

### Step 2: Start Frontend
```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```
- Open dashboard at: [http://127.0.0.1:5173](http://127.0.0.1:5173)

### Step 3: Run Test Suite
Run the backend automated test suite (21 unit, integration, and feature tests):
```bash
cd backend
python -m pytest tests/ -v
```

Run frontend linting and production build:
```bash
cd frontend
npm run lint
npm run build
```

---

## 5. API Endpoints Reference

### Core Telemetry & Patients
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Server status and database connectivity |
| `GET` | `/api/patients` | List all synthetic patient records |
| `GET` | `/api/patients/{id}` | Detailed patient profile (BMI, diagnosis vintage) |
| `GET` | `/api/readings/glucose/{id}?hours=24` | Historical CGM readings within window |
| `GET` | `/api/readings/vitals/{id}?hours=24` | Historical HR and HRV readings within window |

### Machine Learning Spike Prediction
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/predictions/glucose-spike` | Run experimental 2-hour hyperglycemia forecast (`patient_id` in body) |

### Clinical Alert Engine
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/alerts` | List alerts (supports `patient_id`, `status`, `source`, `limit` query filters) |
| `GET` | `/api/alerts/{id}` | Retrieve single alert record |
| `POST` | `/api/alerts/{id}/acknowledge` | Transition alert status from `active` to `acknowledged` |
| `POST` | `/api/alerts/{id}/resolve` | Transition alert status to `resolved` with timestamp |
| `POST` | `/api/alerts/evaluate` | Controlled on-demand evaluation trigger (`patient_id`, `hours`) |

### Digital Twin & What-If Simulation
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/digital-twin/{patient_id}` | Full computed twin state, baseline comparison, and warnings |
| `POST` | `/api/simulation/what-if` | Deterministic counterfactual sandbox (`carbs_grams`, `activity_minutes`) |

---

## 6. Alert Engine & Deduplication Strategy

The Alert Engine explicitly distinguishes two classes of clinical alerts:
1. **Observed-Reading Alerts (`source: observed_reading`)**: Triggered when actual stored synthetic readings cross demonstration boundaries:
   - Severe Hypoglycemia: $< 54.0\text{ mg/dL}$ (Critical)
   - Hypoglycemia: $< 70.0\text{ mg/dL}$ (Warning)
   - Hyperglycemia: $\ge 180.0\text{ mg/dL}$ (Warning)
   - Severe Hyperglycemia: $\ge 250.0\text{ mg/dL}$ (Critical)
   - Autonomic Distress / Elevated HR: $\text{HR} \ge 100\text{ bpm}$ and $\text{HRV} \le 25\text{ ms}$ (Warning)
2. **Model-Predicted Alerts (`source: experimental_prediction`)**: Triggered when the experimental ML spike model predicts an upcoming excursion ($\ge 180\text{ mg/dL}$ within 2 hours) with risk score $\ge 0.50$.

### Deduplication Strategy
To guarantee idempotence and prevent alert duplication on page refreshes or periodic scans:
- **Observed readings key:** `obs:{patient_id}:{alert_type}:{reading_id}`
- **Model predictions key:** `pred:{patient_id}:{timestamp_minute_slug}`
- **Database Unique Index:** Stored in `Alert.dedup_key` with a database unique index (`idx_alerts_dedup_key`).
- **Lifecycle Integrity:** If an alert is already acknowledged or resolved, subsequent evaluation passes recognize the `dedup_key` and leave the existing status untouched.

---

## 7. Patient Digital Twin Calculations

The Digital Twin intelligence summary (`GET /api/digital-twin/{patient_id}`) computes a real-time virtual profile:
- **Phenotype Vector:** Age, gender, diabetes subtype, years since diagnosis, calculated BMI ($kg/m^2$).
- **Telemetry Surveillance Window:** Anchored to the patient's latest sensor timestamp (default 24 hours).
- **Baseline vs Recent Deltas:** 
  - $\Delta \text{Glucose}_{1h} = \text{Mean}(G_{t \in [T-1h, T]}) - \text{Mean}(G_{t \in [T-24h, T]})$
  - $\Delta \text{HeartRate}_{1h} = \text{Mean}(HR_{t \in [T-1h, T]}) - \text{Mean}(HR_{t \in [T-24h, T]})$
  - $\Delta \text{HRV}_{1h} = \text{Mean}(HRV_{t \in [T-1h, T]}) - \text{Mean}(HRV_{t \in [T-24h, T]})$
- **Data Quality & Sensor Coverage:** Reports valid reading count in the 24h window and flags gaps (>45 min between readings).

---

## 8. What-If Counterfactual Sandbox Heuristics

Because synthetic training sets cannot support complex physiological pharmacokinetics, GlucoTwin implements a transparent, deterministic illustrative calculator rather than claiming clinical accuracy:

$$\Delta G_{\text{carbs}} = \Delta C \times \left(0.40 \times \frac{70}{\text{weight\_kg}} \times K_{\text{type}}\right)$$

Where sensitivity factor $K_{\text{type}}$ is:
- **Type 1 Diabetes:** $1.30$
- **Type 2 Diabetes:** $1.15$
- **Pre-diabetic:** $0.90$

$$\Delta G_{\text{activity}} = -\Delta A \times 0.75\text{ mg/dL per minute of moderate activity}$$

$$G_{\text{scenario}} = \max\left(40.0, \, G_{\text{baseline}} + \Delta G_{\text{carbs}} + \Delta G_{\text{activity}}\right)$$

### Assumptions & Limitations:
- Simplified linear single-compartment model.
- Constant glycemic index (approx. 50–55 min time-to-peak).
- Independent of insulin-on-board or stomach-emptying kinetics.
- Prominently marked: **"SIMULATED — NOT A CLINICAL PREDICTION"**.

---

## 9. Machine Learning Spike Prediction Engine

### Architecture
- **Task:** Binary classification ($y \in \{0, 1\}$) predicting glucose $\ge 180.0\text{ mg/dL}$ within next 2 hours ($120\text{ min}$).
- **Model:** `StandardScaler` + `LogisticRegression(penalty='l2', C=1.0)`.
- **Features Extracted ($t \le T$, 60-min lookback):**
  - Current glucose, 1h mean, 1h standard deviation (variability), 1h slope (rate of change).
  - Current HR, current HRV, 1h mean HR, 1h mean HRV.
  - Circadian diurnal features (`sin(2π * hour / 24)`, `cos(2π * hour / 24)`).
  - Demographic features: Age, years diagnosed, diabetes type one-hot indicators.
- **Leakage Prevention:** Purged holdout split with 2-hour gap between train and test sets.

---

## 10. Step-by-Step Hackathon Demonstration Script

Follow this 5-minute presentation script for a reliable demonstration:

1. **Dashboard Overview (0:00 - 0:45)**:
   - Open [http://127.0.0.1:5173](http://127.0.0.1:5173).
   - Point out system health indicator ("System Operational"), Time-in-Range (TIR) metrics, and dark medical aesthetic.
   - Point out the Topbar notification bell showing active risk alert counts.
2. **Patient Selection & Telemetry (0:45 - 1:30)**:
   - Select **Priya Patel (Patient #3 - Type 1 Diabetes)** from the dropdown.
   - Explain multi-vital telemetry: synchronized glucose, heart rate, and autonomic HRV curves.
3. **ML Glucose-Spike Prediction (1:30 - 2:30)**:
   - Click **Predictions** tab.
   - Click "Run Spike Risk Assessment".
   - Show predicted risk score (~0.54, MODERATE/HIGH risk) and explain the transparent feature contribution breakdown (e.g. rising slope, diabetes subtype, HRV suppression).
   - Highlight the disclaimer: *"Uncalibrated experimental score — Research prototype only"*.
4. **Clinical Alert Center & Workflow (2:30 - 3:30)**:
   - Click **Alerts** tab (or click the Topbar notification bell dropdown).
   - Show visual distinction:
     - **Observed Telemetry Alerts** (cyan badge, e.g. actual readings $>180\text{ mg/dL}$).
     - **Model-Predicted Alert** (purple brain badge, forecasting 2-hour spike).
   - Click **"Acknowledge"** on an alert $\rightarrow$ card updates to "ACKNOWLEDGED" with timestamp; notification badge count decrements immediately.
   - Demonstrate the status filter: Switch to "Acknowledged" or "Active".
5. **Digital Twin Intelligence (3:30 - 4:15)**:
   - Click **Digital Twin** tab.
   - Explain the patient digital twin state: Phenotype vector (Age 28, BMI 21.5), 24h baseline vs 1h recent delta ($\Delta G$, $\Delta HR$, $\Delta HRV$).
   - Show that sensor coverage count and data quality are computed from actual stored readings.
6. **What-If Counterfactual Sandbox (4:15 - 5:00)**:
   - Click **What-If Simulation** tab.
   - Adjust the **Carbohydrate** slider to `+45g` $\rightarrow$ projected glucose rises.
   - Adjust the **Physical Activity** slider to `30 min` $\rightarrow$ projected glucose drops, mitigating the spike excursion.
   - Emphasize the clear safety banner: *"SIMULATED — NOT A CLINICAL PREDICTION"*.
   - Switch to **Meera Reddy (Patient #5)** to show clean, well-controlled baseline with zero active alerts.

---

## 11. Implemented vs Planned Roadmap

### Implemented (Phases 1–6):
- [x] FastAPI REST API with SQLite persistence and CORS configuration.
- [x] Synthetic generator with 5 diverse diabetes cohorts over 72 hours.
- [x] Leak-free ML feature engineering pipeline with 1-hour lookback.
- [x] Serialized scikit-learn model artifact with linear feature contributions.
- [x] React 19 / Vite dashboard with multi-vital time-series visualizations.
- [x] Dual-source alert engine (observed readings vs model predictions).
- [x] Idempotent alert deduplication with SQLite unique constraint.
- [x] Alert acknowledgement and resolution clinical workflow.
- [x] Patient Digital Twin intelligence summary with 24h baseline delta.
- [x] What-If counterfactual scenario calculator with safety disclaimers.
- [x] In-dashboard notification bell and badge counter.
- [x] 21 backend unit and integration tests.

### Planned Future Work (Post-Hackathon):
- [ ] Ingestion from real Bluetooth Low Energy (BLE) CGM devices (e.g. Dexcom G6/G7, FreeStyle Libre).
- [ ] Pharmacokinetic differential equation modeling for insulin-on-board (IOB) decay curves.
- [ ] Deep learning recurrent architectures (LSTM / Transformer) on multi-day telemetry.
- [ ] Role-based access control (RBAC) and HIPAA-compliant audit logging.
- [ ] Real-time WebSockets / SSE for instant multi-clinician notification sync.

---

## 12. Known Scientific & Dataset Limitations

1. **Synthetic Data Characteristics**: The patient database uses synthetic physiological models. While diurnal circadian patterns and glycemic excursions are modeled, complex individual metabolic variations are not clinically validated.
2. **Demonstration Thresholds**: Boundaries ($54, 70, 180, 250\text{ mg/dL}$) are demonstration configuration parameters and must not be interpreted as individualized clinical guidelines.
3. **Illustrative Simulation**: The What-If simulation employs a simplified heuristic for educational purposes; real biological responses depend on gut motility, hormonal stress, and insulin timing.
4. **No Medical Device Claims**: GlucoTwin is strictly an engineering prototype.

---

## 13. License

MIT License — see repository root.
