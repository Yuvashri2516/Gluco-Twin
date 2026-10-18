# GlucoTwin: An Intelligent Predictive Digital Twin for Proactive Glucose-Risk Monitoring

*Happiest Health Digital Twin Challenge — Phase 1 Proof-of-Concept*

[![Backend Tests](https://img.shields.io/badge/pytest-71%20passed%20(100%25)-success)](backend/tests)
[![Frontend Build](https://img.shields.io/badge/vite%20build-passing-brightgreen)](frontend)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Deployment: Vercel](https://img.shields.io/badge/Frontend-Vercel%20Live-black)](https://gluco-twin-eta.vercel.app/)
[![Deployment: Render](https://img.shields.io/badge/Backend-Render%20Live-46E3B7)](https://gluco-twin.onrender.com)

> [!WARNING]
> **ACADEMIC & HACKATHON RESEARCH PROTOTYPE ONLY**
> GlucoTwin is built exclusively with clinically modeled synthetic patient telemetry, laboratory panels, genetic records, and simulated clinical pagers. It is **NOT** clinically validated, **NOT** a certified medical device, and **MUST NOT** be used for clinical diagnosis, treatment decisions, or medical management.

---

## Official Hackathon Submission Checklist

| # | Submission Item | Status | Verified Location in README |
|---|---|:---:|---|
| 1 | **Team details** | Prepared | [Section 16: Team Details](#team-details) |
| 2 | **College/Incubator information** | Prepared | [Section 16: College / Incubator Information](#college--incubator-information) |
| 3 | **Project Title** | Verified | [Header](#glucotwin-an-intelligent-predictive-digital-twin-for-proactive-glucose-risk-monitoring) |
| 4 | **Problem Statement** | Verified | [Section 2: Problem Statement](#the-problem-the-reactive-care-paradox) |
| 5 | **Healthcare Use Case** | Verified | [Section 2: Healthcare Use Case](#intended-healthcare-use-case--target-audience) |
| 6 | **Technical Stack** | Verified | [Section 4: Technical Stack](#technical-stack) |
| 7 | **AI/ML Model or Framework Details** | Verified | [Section 7: AI/ML Model & Framework Details](#7-aiml-model--framework-details) |
| 8 | **15-20 minute Demo Video is uploaded as an Unlisted YouTube video and the link is added to the README** | Ready for Link | [Section 15: 15–20 Minute Demo Video Link](#15-20-minute-demo-video-is-uploaded-as-an-unlisted-youtube-video-and-the-link-is-added-to-the-readme) |
| 9 | **Open-source License Details** | Verified | [Section 17: Open-Source License Details](#17-open-source-license-details) |
| 10 | **Architecture Diagram in PDF/PPT format** | Verified | [Section 4 & Section 15: Architecture Deliverables](#architecture-diagram-in-pdfppt-format) |
| 11 | **Presentation in PDF/PPT format covering project details and outcomes** | Verified | [Section 15: Presentation Deliverables](#presentation-in-pdfppt-format-covering-project-details-and-outcomes) |
| 12 | **All files and links are publicly accessible without additional permissions** | Verified | [Section 18: Public Accessibility Verification](#18-all-files-and-links-are-publicly-accessible-without-additional-permissions) |

---

## 1. Executive Summary & Project Overview

**GlucoTwin** is a multimodal software-only healthcare digital twin designed to shift diabetes management from **reactive threshold alerting** to **proactive risk forecasting and counterfactual exploration**.

Commercial Continuous Glucose Monitors (CGMs) alert patients only after acute excursions have already occurred (hypoglycemia $< 70\text{ mg/dL}$ or hyperglycemia $\ge 180\text{ mg/dL}$). Furthermore, real-time sensor streams operate in complete isolation from Electronic Health Records (historical diagnoses, laboratory panels, and genetic risk markers).

GlucoTwin bridges this gap by unifying:
1. **Historical Synthetic EHR:** Patient demographics, calculated BMI, historical diagnoses, structured longitudinal laboratory results (HbA1c, Fasting Glucose, Lipids), and synthetic genetic susceptibility alleles (TCF7L2, PPARG, KCNJ11, SLC30A8, KCNQ1).
2. **Dynamic Physiological Streams:** 15-minute sampling intervals of continuous glucose (CGM), heart rate (HR), heart-rate variability (HRV), polysomnographic sleep stages (Deep, Light, REM, Awake), and 15-minute interval vs daily cumulative physical activity steps.
3. **Personalized Patient Digital Twin:** Maintains a continuous virtual profile computing 24-hour baseline vs 1-hour recent excursion deltas ($\Delta G$, $\Delta HR$, $\Delta HRV$).
4. **Machine Learning Spike Predictor:** A leak-free logistic regression pipeline predicting whether glucose will breach $180\text{ mg/dL}$ within a forward 120-minute window (Chronological Holdout ROC-AUC: 0.945; Baseline Partition: 0.705).
5. **Dual-Source Alert Surveillance:** Explicitly distinguishes **Observed Telemetry Breaches** from **Model-Predicted Excursions**, complete with acknowledgement, resolution, and simulated hospital clinician pager dispatch.
6. **What-If Counterfactual Sandbox:** An educational scenario calculator modeling postprandial carbohydrate impacts and physical exertion offsets.

---

## 2. Problem Statement & Healthcare Use Case

### The Problem: The Reactive Care Paradox
1. **Delayed Clinical Intervention:** Conventional sensor alarms trigger only when acute excursions are in progress, leaving patients with narrow reaction windows.
2. **Siloed Physiological Signals:** Autonomic nervous system markers (heart rate elevations and depressed HRV) frequently precede or accompany glycemic distress, but are rarely analyzed alongside CGM data.
3. **Fragmented Patient Context:** Clinicians reviewing telemetry lack instant access to baseline glycemic control (HbA1c), metabolic comorbidities, or sleep fragmentation.
4. **Lack of Safe Experimentation:** Patients lack safe, transparent tools to answer: *"What happens to my glucose trajectory if I consume a 45g carbohydrate meal or take a 30-minute walk?"*

### Intended Healthcare Use Case & Target Audience
- **Outpatient Endocrinology & Primary Care Teams:** Continuous surveillance of high-risk diabetic cohorts with automated severity-based triage.
- **Diabetes Care & Education Specialists (CDCES):** Educating patients on feature contributions driving glycemic spikes using transparent linear coefficients.
- **Remote Patient Monitoring (RPM):** Proactive escalation before nocturnal hypoglycemia or daytime postprandial hyperosmolar spikes.
- **Strict Clinical Non-Prescriptive Scope:** GlucoTwin provides surveillance and risk forecasting; it never provides automated insulin dosing, drug prescriptions, or diagnostic pronouncements.

---

## 3. Implemented Features

- [x] **Multimodal Patient EHR History:** Height, weight, calculated BMI ($kg/m^2$), historical diagnoses, longitudinal lab panels (HbA1c, Fasting Glucose, Total/HDL/LDL Cholesterol, Triglycerides), and 5 genetic susceptibility markers.
- [x] **5 Dynamic Physiological Time-Series Streams:** Continuous glucose, heart rate, heart-rate variability, sleep architecture stages, and 15-minute step intervals with daily cumulative totals.
- [x] **Digital Twin Phenotyping & Excursion Deltas:** Computes 24h baseline vs 1h recent deltas ($\Delta G_{1h}, \Delta HR_{1h}, \Delta HRV_{1h}$), reading density, and data freshness flags.
- [x] **Demonstrable Live Sensor Simulation Feed:** Controlled simulated sensor ingestion (`POST /api/digital-twin/simulate-feed`) advancing patient telemetry by +15m epochs, persisting readings, re-evaluating alerts, and updating the twin state.
- [x] **Leak-Free ML Spike Prediction Engine:** 120-minute forward prediction horizon with StandardScaler fitted strictly on training data, 2-hour purged holdout split, and transparent feature contribution breakdown.
- [x] **Dual-Source Alert Engine & Clinical Workflow:** Distinguishes observed telemetry breaches from model predictions with Active -> Acknowledged -> Resolved state transitions and database deduplication constraints.
- [x] **Simulated Clinician Triage Notification Center:** Demonstrates alert escalation to on-call hospital staff and nurses (explicitly disclaimed: local demonstration mode, no external SMS/email).
- [x] **What-If Counterfactual Sandbox:** Deterministic simulation calculating carb spike vs physical activity offset with subtype sensitivity factors ($K_{type}$) and safety watermarks.
- [x] **Professional Doctor-Facing Dashboard:** Dark medical aesthetic with patient cohort switching, Recharts visualizations, loading/empty/error states, and notification bell counter.
- [x] **Automated Testing Suite:** 71 passing pytest backend tests on isolated in-memory databases; 0-error frontend linting; 942ms Vite production build.
- [x] **Complete Hackathon Submission Package:** Standalone Architecture Diagram (PDF/SVG), Presentation Deck (PPTX/PDF), and 20-minute Demo Script.

---

## 4. Technical Stack & System Architecture

### Technical Stack

| Domain | Technologies & Libraries | Purpose & Implementation Details |
|---|---|---|
| **Frontend Framework** | **React 19, Vite 5** | High-performance reactive clinician SPA with lightning-fast sub-second build times (~835ms). |
| **Styling & Design System** | **Tailwind-free Vanilla CSS** | Custom glassmorphic cards, deep slate medical tech palette (`#0b1120`, `#1e293b`, `#38bdf8`), responsive typography. |
| **Data Visualization** | **Recharts 2.x** | Synchronized multi-vital telemetry (CGM, HR, HRV), sleep hypnogram stages, and 15-minute interval step bars. |
| **UI Components & Icons** | **Lucide-React** | Accessible, medical-grade iconography and alert badges. |
| **Backend Framework** | **Python 3.10+ / FastAPI** | Asynchronous high-throughput REST API with automatic OpenAPI documentation and CORS support. |
| **Schemas & Validation** | **Pydantic v2** | Strict bidirectional type validation and serialization for multi-vital telemetry, labs, genetics, and twin state. |
| **AI / ML Framework** | **Scikit-Learn, NumPy, Pandas, Joblib** | 120-minute forward glucose spike classification with leak-free `StandardScaler` + `LogisticRegression(L2)`. |
| **Database & ORM** | **SQLite 3, SQLAlchemy 2.x** | Transactional relational persistence with WAL mode, parameterized queries, and idempotent alert deduplication constraints. |
| **Automated Testing Suite** | **Pytest, Pytest-Asyncio** | 71 automated tests executing against isolated in-memory SQLite (`sqlite:///:memory:`) databases. |
| **Production Cloud Hosting** | **Vercel (Frontend), Render (Backend)** | Continuous deployment with automated build triggers and `/api/health` monitoring probes. |
| **Version Control** | **Git / GitHub** | Full source tracking under permissive open-source licensing. |

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CLINICIAN DASHBOARD (React 19 / Vite)                 │
│  - Patient Cohort Selector (5 Personas)    - Multimodal EHR & Lab Timeline  │
│  - Multi-Vital Telemetry Curves (CGM/HR)   - Sleep Hypnogram & Step Bars    │
│  - Digital Twin State & +15m Feed Button   - 2h ML Spike Risk & Explanations│
│  - Dual-Source Alert Center (Ack/Resolve)  - Simulated Clinician Pager      │
│  - What-If Counterfactual Sandbox          - In-Dashboard Notification Bell │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTPS / JSON REST API
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                        API ROUTING & SCHEMAS (FastAPI)                      │
│  /api/patients/{id}/labs                   /api/patients/{id}/genetics      │
│  /api/readings/glucose/{id}                /api/readings/vitals/{id}        │
│  /api/readings/sleep/{id}                  /api/readings/steps/{id}         │
│  /api/digital-twin/{id}                    /api/digital-twin/simulate-feed  │
│  /api/predict/spike                        /api/alerts                      │
│  /api/simulation/what-if                   /api/health                      │
└──────────────┬──────────────────────────────────────────────┬───────────────┘
               │                                              │
┌──────────────▼──────────────────────────────┐ ┌─────────────▼───────────────┐
│   DIGITAL TWIN & SURVEILLANCE ENGINES       │ │   MACHINE LEARNING ENGINE   │
│  - 24h Baseline vs 1h Recent Deltas         │ │  - StandardScaler Pipeline  │
│  - Data Freshness & Telemetry Coverage      │ │  - Logistic Regression (L2) │
│  - Observed Threshold Evaluator (<54, >250) │ │  - 120-min Forward Horizon  │
│  - Idempotent SQLite Dedup Keys             │ │  - Linear Risk Contributions│
└──────────────┬──────────────────────────────┘ └─────────────┬───────────────┘
               │                                              │
┌──────────────▼──────────────────────────────────────────────▼───────────────┐
│                      PERSISTENCE TIER (SQLite / SQLAlchemy)                 │
│  patients | glucose_readings | vital_readings | lab_results | genetic_markers│
│  sleep_records | step_records | alerts | digital_twin_states                │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Architecture Diagram in PDF/PPT Format
- **PDF Deliverable (High-Resolution):** [`submission/GlucoTwin_Architecture.pdf`](submission/GlucoTwin_Architecture.pdf)
- **Editable Vector Deliverable (SVG):** [`submission/GlucoTwin_Architecture.svg`](submission/GlucoTwin_Architecture.svg)
- **Image Deliverable (PNG):** [`submission/GlucoTwin_Architecture.png`](submission/GlucoTwin_Architecture.png)
- **Presentation Integration:** The complete system architecture is also embedded within Slide 7 of [`submission/GlucoTwin_Presentation.pptx`](submission/GlucoTwin_Presentation.pptx).

---

## 5. Multimodal EHR & Physiological Data Streams

### Historical EHR Data Models

#### 1. Patient Demographics & Phenotype (`patients`)
- `id`: Integer primary key.
- `name`: Patient display name.
- `age`: Age in years (28 to 61).
- `gender`: Biological sex.
- `diabetes_type`: Clinical classification (`Type 1`, `Type 2`, `Pre-diabetic`).
- `years_since_diagnosis`: Chronological disease duration.
- `historical_diagnoses`: Text string of historical comorbidities (e.g. *"Essential Hypertension, Dyslipidemia, Mild Diabetic Neuropathy"*).
- `height_cm`: Height in centimeters.
- `weight_kg`: Weight in kilograms.
- `calculated_bmi`: Derived property: $\text{BMI} = \frac{\text{weight\_kg}}{(\text{height\_cm}/100)^2}$.

#### 2. Structured Laboratory Results (`lab_results`)
- `test_name`: HbA1c, Fasting Blood Glucose, Total Cholesterol, HDL Cholesterol, LDL Cholesterol, Triglycerides.
- `result`: Numerical test value.
- `unit`: Clinical measurement unit (`%`, `mg/dL`).
- `reference_range`: Standard clinical reference threshold (e.g. `"< 5.7%"`, `"70-99 mg/dL"`).
- `measurement_date`: Historical measurement timestamp.
- `is_synthetic`: Boolean flag (`True`).

#### 3. Synthetic Genetic Markers (`genetic_markers`)
- `marker_id`: NCBI dbSNP identifier (e.g. `rs7903146`, `rs1801282`, `rs5219`, `rs13266634`, `rs10946398`).
- `gene`: Gene symbol (`TCF7L2`, `PPARG`, `KCNJ11`, `SLC30A8`, `KCNQ1`).
- `genotype`: Simulated allele pairing (e.g. `"C/T (Risk allele T)"`).
- `data_source`: Annotation origin (`"Simulated Pharmacogenomics Microarray Panel"`).
- `is_synthetic`: Boolean flag (`True`).

### Dynamic Physiological Time-Series Streams

| Stream | Sampling Interval | Measurement Range | Storage Table | Purpose |
|---|---|---|---|---|
| **Continuous Glucose (CGM)** | 15 Minutes | 40.0 – 400.0 mg/dL | `glucose_readings` | Core glycemic tracking & ML target generation |
| **Heart Rate (HR)** | 15 Minutes | 45.0 – 160.0 bpm | `vital_readings` | Autonomic stress & physical exertion tracking |
| **Heart-Rate Variability (HRV)** | 15 Minutes | 15.0 – 110.0 ms | `vital_readings` | Parasympathetic tone & hypoglycemia stress detection |
| **Sleep Architecture** | Stage Intervals | Deep, Light, REM, Awake | `sleep_records` | Restorative baseline & sleep efficiency calculation |
| **Physical Activity (Steps)** | 15 Minutes | 0 – 1,500 steps/interval | `step_records` | Exertion tracking (interval vs daily cumulative) |

---

## 6. Multimodal Data Fusion Architecture

To ensure scientific and clinical integrity, GlucoTwin enforces a strict distinction between clinical context and machine learning inputs:

| Data Stream | Stored in DB | Displayed in Dashboard | In Twin State Vector | Input to ML Model | Context / Purpose |
|---|:---:|:---:|:---:|:---:|---|
| **Demographics (Age, Subtype)** | Yes | Yes | Yes | **Yes** | Baseline metabolic risk weighting |
| **Weight, Height, Calculated BMI** | Yes | Yes | Yes | Context | Phenotypic stratification & What-If scaling |
| **Historical Diagnoses** | Yes | Yes | Yes | Context | Clinical comorbidity context |
| **Laboratory Panels (HbA1c, Lipids)** | Yes | Yes | Yes | Context | Longitudinal glycemic & lipid baseline |
| **Genetic Susceptibility Markers** | Yes | Yes | Yes | Context | Pharmacogenomic susceptibility context |
| **Continuous Glucose (CGM)** | Yes | Yes | Yes | **Yes** | Current value, 1h mean, std dev, trend slope |
| **Heart Rate & HRV** | Yes | Yes | Yes | **Yes** | Current value, 1h rolling mean |
| **Circadian Hour (sin/cos)** | Derived | Yes | Yes | **Yes** | Diurnal metabolic fluctuations |
| **Sleep Architecture (Stages)** | Yes | Yes | Yes | Context | Sleep duration & efficiency context |
| **Step-Count Telemetry** | Yes | Yes | Yes | Context | Exertion context & What-If activity input |

> [!IMPORTANT]
> **Data Fusion Discipline:** Genetic markers and laboratory panels are displayed for clinical context but are **not** forced into the 14-feature machine learning matrix. Forcing uncalibrated genomic data into small sample models produces spurious correlations. Our model uses strictly leak-free physiological and demographic features.

---

## 7. AI/ML Model & Framework Details

### Framework & Model Architecture
- **ML Frameworks & Libraries:** Python `scikit-learn` (v1.4+), `numpy`, `pandas`, `joblib`.
- **Pipeline Architecture:**
  1. `StandardScaler`: Normalizes continuous features, fitted strictly on historical training data to guarantee zero future data leakage.
  2. `LogisticRegression`: Linear regularized classifier with $L_2$ Ridge penalty (`penalty='l2'`, $C = 1.0$, solver `lbfgs`, `max_iter=1000`).
- **Explainability (XAI):** Linear feature log-odds weights provide instant, mathematically transparent feature contribution breakdowns directly to the clinician interface.
- **Model Serialization:** Pipeline artifact saved in [`backend/app/ml/artifacts/glucose_spike_model.joblib`](backend/app/ml/artifacts/glucose_spike_model.joblib) with metadata in [`backend/app/ml/artifacts/model_metadata.json`](backend/app/ml/artifacts/model_metadata.json).

### Prediction Target & Horizon
- **Task:** Binary classification ($y \in \{0, 1\}$).
- **Target Event:** Will glucose reach or exceed $180.0\text{ mg/dL}$ at any time within the next 120 minutes ($t \in (T, T + 120\text{ min}]$)?
- **Lookback Window:** Features extracted strictly from historical readings at $t \le T$ (60-minute lookback).
- **Leakage Prevention:** 2-hour purged holdout buffer between training and testing sets prevents overlapping window contamination. Preprocessing (`StandardScaler`) is fitted strictly on the training partition.

### Feature Schema (14 Input Dimensions)
1. `current_glucose`: Latest glucose reading at time $T$.
2. `mean_glucose_1h`: Rolling 1-hour average glucose.
3. `glucose_std_1h`: Rolling 1-hour glucose standard deviation.
4. `glucose_trend`: Linear slope of glucose over last hour ($mg/dL\text{ per min}$).
5. `current_heart_rate`: Latest heart rate at time $T$.
6. `current_hrv`: Latest heart rate variability at time $T$.
7. `mean_heart_rate_1h`: Rolling 1-hour average heart rate.
8. `mean_hrv_1h`: Rolling 1-hour average HRV.
9. `time_of_day_sin`: Circadian cyclical feature $\sin(2\pi \cdot \text{hour} / 24)$.
10. `time_of_day_cos`: Circadian cyclical feature $\cos(2\pi \cdot \text{hour} / 24)$.
11. `age`: Patient chronological age.
12. `years_diagnosed`: Duration of diabetes.
13. `diabetes_type_Type 1`: One-hot indicator for Type 1 diabetes.
14. `diabetes_type_Type 2`: One-hot indicator for Type 2 diabetes.

### Empirical Evaluation & Evaluation Split Distinctions

To ensure scientific honesty and reproducibility, GlucoTwin strictly separates and documents two fundamentally different evaluation methodologies:

#### 1. Chronological Holdout Evaluation (Temporal Trajectory Forecasting)
In this evaluation split, observations are ordered chronologically by time. A 2-hour purge buffer is applied, and the model is trained on past time intervals and tested on strictly forward, held-out future intervals. Preprocessing (`StandardScaler`) is fitted strictly on the training partition.

- **Current Evaluation (3,980 usable rows, 1,114 test samples, 15.2% positive rate):**
  - **ROC-AUC:** `0.9445`
  - **Accuracy:** `87.61%` (907 true negatives, 69 true positives, 38 false positives, 100 false negatives)
  - **Precision:** `0.6449`
  - **Recall:** `0.4083`
  - **F1-Score:** `0.5000`
  - **Brier Score:** `0.0688`
- **Baseline Metadata Partition (Saved in `model_metadata.json`, 1,400 samples):**
  - **ROC-AUC:** `0.7046` | **F1-Score:** `0.5053` | **Accuracy:** `60.28%` | **Precision:** `0.4737` | **Recall:** `0.5414`
- **Baseline Comparison (Holdout Set):**
  - **Majority-Class Baseline:** Accuracy `84.8%`, Precision `0.000`, Recall `0.000`, F1 `0.000`, ROC-AUC `0.500`
  - **Persistence Baseline:** Accuracy `78.2%`, Precision `0.410`, Recall `0.380`, F1 `0.394`, ROC-AUC `0.612`

#### 2. Cross-Patient Generalization (Leave-One-Patient-Out Evaluation)
When evaluated across unseen patients (training on 4 patient profiles and evaluating on the 5th unseen patient persona):

| Held-Out Unseen Patient | Cohort Classification | Total Samples | Spikes (Positive) | Unseen ROC-AUC | Unseen F1-Score |
|---|---|:---:|:---:|:---:|:---:|
| **Patient #1** (Elena Rostova) | Type 1 Diabetes | 796 | 364 (45.7%) | **0.5322** | 0.4014 |
| **Patient #2** (Marcus Chen) | Type 2 Diabetes | 796 | 380 (47.7%) | **0.4678** | 0.3728 |
| **Patient #3** (Amina Diallo) | Type 1 Brittle | 796 | 412 (51.8%) | **0.4959** | 0.6696 |
| **Patient #4** (Rajesh Patel) | Type 2 Uncontrolled | 796 | 384 (48.2%) | **0.5665** | 0.4063 |
| **Patient #5** (Sarah Jenkins) | Pre-diabetic | 796 | 0 (0.0%) | *Single class (N/A)* | *Single class (N/A)* |
| **Cohort Mean (Excl. Single-Class)** | Multi-Type | 3,184 | 1,540 (48.4%) | **0.5156** | 0.4625 |

#### 3. Why These Results Are Not Interchangeable (Model Generalization Boundary)
- **Chronological Holdout** measures how accurately the model predicts forward 120-minute trajectory excursions for patients whose physiological baseline, circadian rhythm, and glycemic volatility patterns have been observed during historical training epochs.
- **Unseen-Patient Generalization** measures whether a model trained on a small cohort (4 patients) can generalize to an entirely unseen patient with different insulin sensitivity, body mass, and metabolic dynamics.
- **Scientific Limitation:** With only 5 synthetic patient personas in this proof-of-concept, cross-patient transfer achieves near-random performance (~0.52 ROC-AUC). Consequently, **GlucoTwin's ML model is designed and validated as a personalized trajectory monitoring system, not a universal population screening tool.** In clinical deployment, personalized calibration or transfer learning on an individual's historical telemetry is mandatory.

---

## 8. Clinical Risk Alert Engine & Triage Workflow

GlucoTwin explicitly separates alerts into two distinct clinical classes:
1. **Observed-Reading Alerts (`source: observed_reading`):**
   - Severe Hypoglycemia: $< 54.0\text{ mg/dL}$ (Critical)
   - Hypoglycemia: $< 70.0\text{ mg/dL}$ (Warning)
   - Hyperglycemia: $\ge 180.0\text{ mg/dL}$ (Warning)
   - Severe Hyperglycemia: $\ge 250.0\text{ mg/dL}$ (Critical)
   - Autonomic Distress: $\text{HR} \ge 100\text{ bpm}$ and $\text{HRV} \le 25\text{ ms}$ (Warning)
2. **Model-Predicted Alerts (`source: experimental_prediction`):**
   - Predicted Hyperglycemic Excursion: Risk score $\ge 0.50$ (Warning)

### Lifecycle & Idempotence
- **State Machine:** `active` $\rightarrow$ `acknowledged` $\rightarrow$ `resolved`.
- **Deduplication Strategy:** Stored in `Alert.dedup_key` with a database unique constraint:
  - Observed: `obs:{patient_id}:{alert_type}:{reading_id}`
  - Model: `pred:{patient_id}:{timestamp_minute_slug}`
- **Simulated Clinician Triage Pager:** An in-dashboard dispatch log demonstrating how high-severity alerts route to on-call endocrinologists and diabetes educators (local simulation; external SMS/email deliberately unconfigured).

---

## 9. Demonstrable Digital Twin Simulation Workflow

Clinicians can verify real-time digital twin updates through an interactive simulated sensor feed:
1. **Select Patient:** Load the active patient state.
2. **Click "⚡ Simulate Sensor Feed (+15m)":** Sends a controlled POST request to `/api/digital-twin/simulate-feed`.
3. **Ingestion & Validation:** Generates a synchronized +15m epoch (glucose, HR, HRV, interval steps).
4. **Safe Persistence:** Writes records to SQLite without duplicating existing timestamps.
5. **Surveillance Evaluation:** Alerts engine scans new readings and triggers notifications if thresholds are crossed.
6. **State Recomputation:** Twin recalculates baseline deltas, data freshness flags, and updates the UI instantly.

---

## 10. What-If Counterfactual Sandbox

A deterministic educational calculator anchored to the patient's baseline glucose:

$$\Delta G_{\text{carbs}} = \Delta C \times \left(0.40 \times \frac{70}{\text{weight\_kg}} \times K_{\text{type}}\right)$$

Where sensitivity factor $K_{\text{type}}$ is:
- **Type 1 Diabetes:** $1.30$
- **Type 2 Diabetes:** $1.15$
- **Pre-diabetic:** $0.90$

$$\Delta G_{\text{activity}} = -\Delta A \times 0.75\text{ mg/dL per minute of moderate activity}$$

$$G_{\text{scenario}} = \max\left(40.0, \, G_{\text{baseline}} + \Delta G_{\text{carbs}} + \Delta G_{\text{activity}}\right)$$

> [!NOTE]
> The sandbox is explicitly labeled **"SIMULATED — NOT A CLINICAL PREDICTION"** to reinforce that heuristic estimates cannot substitute for pharmacokinetics.

---

## 11. Complete REST API Specifications

| Method | Endpoint | Description | Query / Body Params |
|---|---|---|---|
| `GET` | `/api/health` | Health check & DB status probe | None |
| `GET` | `/api/patients` | List all 5 patient cohorts | None |
| `GET` | `/api/patients/{id}` | Patient profile with calculated BMI | None |
| `GET` | `/api/patients/{id}/labs` | Longitudinal laboratory results | None |
| `GET` | `/api/patients/{id}/genetics`| Synthetic genetic susceptibility markers | None |
| `GET` | `/api/readings/glucose/{id}` | Windowed CGM readings | `hours` (1 to 168, default 24) |
| `GET` | `/api/readings/vitals/{id}` | Windowed HR & HRV readings | `hours` (1 to 168, default 24) |
| `GET` | `/api/readings/sleep/{id}` | Sleep stages, duration & efficiency | `hours` (1 to 168, default 24) |
| `GET` | `/api/readings/steps/{id}` | Interval steps & daily cumulative | `hours` (1 to 168, default 24) |
| `GET` | `/api/digital-twin/{id}` | Digital twin intelligence summary | None |
| `POST`| `/api/digital-twin/simulate-feed` | Ingest +15m simulated sensor epoch | `patient_id`, `glucose_value`, etc. |
| `POST`| `/api/predict/spike` | 2-hour ML spike risk assessment | `patient_id`, `as_of_timestamp` |
| `GET` | `/api/alerts` | List alerts with filters | `patient_id`, `status`, `source` |
| `POST`| `/api/alerts/{id}/acknowledge` | Acknowledge alert | None |
| `POST`| `/api/alerts/{id}/resolve` | Resolve alert | None |
| `POST`| `/api/simulation/what-if` | Counterfactual meal/exercise sandbox | `patient_id`, `additional_carbs_g`, `activity_minutes` |

---

## 12. Automated Testing Suite

GlucoTwin includes an extensive automated test suite maintaining 100% database isolation using in-memory SQLite (`sqlite:///:memory:`):

```bash
cd backend
python -m pytest tests/ -v
```

### Test Suite Summary (71 Passed, 0 Failed):
- `tests/test_alerts_engine.py`: 10 tests covering alert rules, deduplication, filtering, lifecycle, and prediction fallback.
- `tests/test_feature_engineering.py`: 4 tests verifying exact 14-feature calculations, leakage prevention, and missing reading handling.
- `tests/test_label_construction.py`: 3 tests confirming 120-minute forward horizon labeling and partial coverage exclusion.
- `tests/test_multimodal_ehr_and_streams.py`: 12 tests verifying EHR history, lab results, genetic markers, sleep stages, step counts, twin aggregation, and simulated sensor feed workflow.
- `tests/test_phase3_digital_twin.py`: 12 tests validating twin baselines, alert transitions, and What-If input bounds.
- `tests/test_phase4_integration.py`: 10 tests verifying unified API responses and 404 error contracts.
- `tests/test_prediction_api.py`: 5 tests validating prediction outputs, model loading, and 503 handling.
- `tests/test_readings_api.py`: 14 tests checking database idempotence, 15-minute schedules, and UTC timezone logic.

### Frontend Quality Verification:
```bash
cd frontend
npm run lint    # ESLint passed: 0 errors
npm run build   # Vite build passed: 606 modules transformed in 942ms
```

---

## 13. Local Installation & Setup Instructions

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Node.js 18+ (tested on Node.js 20)
- Git

### 1. Clone & Protect
```bash
git clone https://github.com/Yuvashri2516/Gluco-Twin.git
cd Gluco-Twin
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Database Initialization
```bash
# Initializes tables and non-destructively populates synthetic cohort data:
python app/seed.py

# Start FastAPI server on port 8000:
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Backend API will be accessible at: `http://127.0.0.1:8000` (Swagger docs at `/docs`).

### 4. Frontend Setup
```bash
cd ../frontend
npm install

# Start Vite dev server on port 5173:
npm run dev
```
Open `http://127.0.0.1:5173` in your browser.

---

## 14. Deployment Information

- **Frontend Deployment:** Hosted on Vercel at [https://gluco-twin-eta.vercel.app/](https://gluco-twin-eta.vercel.app/)
- **Backend Deployment:** Hosted on Render at [https://gluco-twin.onrender.com](https://gluco-twin.onrender.com)
- **Deployment Health Probes:** Live backend verified at `/api/health` with automatic CORS handling.

---

## 15. Submission Deliverables & Demo Video

All hackathon submission deliverables are organized inside the root [`submission/`](submission) directory:

### Architecture Diagram in PDF/PPT Format
- **PDF Deliverable (High-Resolution Vector):** [`submission/GlucoTwin_Architecture.pdf`](submission/GlucoTwin_Architecture.pdf)
- **Editable Vector Deliverable (SVG):** [`submission/GlucoTwin_Architecture.svg`](submission/GlucoTwin_Architecture.svg)
- **High-Resolution Graphic (PNG):** [`submission/GlucoTwin_Architecture.png`](submission/GlucoTwin_Architecture.png)
- *Note:* Architecture diagrams are also embedded within the presentation deck (Slide 7).

### Presentation in PDF/PPT Format Covering Project Details and Outcomes
- **PowerPoint Presentation (19 Widescreen 16:9 Slides):** [`submission/GlucoTwin_Presentation.pptx`](submission/GlucoTwin_Presentation.pptx)
- **PDF Export (19 Pages High-Resolution):** [`submission/GlucoTwin_Presentation.pdf`](submission/GlucoTwin_Presentation.pdf)
- *Content Coverage:* Project motivation, clinical use case, multimodal data fusion, leak-free ML spike prediction, doctor-facing dashboard walkthrough, interactive live sensor simulation, dual-source alert triage pager, counterfactual What-If sandbox, automated test results, limitations, and future roadmap.

### 15-20 Minute Demo Video is Uploaded as an Unlisted YouTube Video and the Link is Added to the README
- **Unlisted YouTube Video Link:** `[Unlisted YouTube Video Link: Insert URL here — e.g., https://youtu.be/XXXXXXXXXXX]`
- **Video Target Duration:** 15–20 Minutes
- **Video Rehearsal Script & Scene Guide:** [`submission/DEMO_VIDEO_SCRIPT.md`](submission/DEMO_VIDEO_SCRIPT.md) (Complete 20-minute scripted walkthrough covering every evaluation rubric).

---

## 16. Team Details & College/Incubator Information

### Team Details
- **Project Lead / Submitter:** `Yuvashri2516`
- **Primary Contact Email:** `yuvashrinarasimman25@gmail.com`
- **Team Members:** `[Team Member Names, Roles, and Email Addresses — Pending User Input]`

### College/Incubator Information
- **College / University / Institution:** `[College / University Name — Pending User Input]`
- **Incubator / Department / Research Center:** `[Incubator / Department / Center Name — Pending User Input]`
- **Faculty Mentor / Academic Advisor:** `[Faculty Mentor Name & Title — Pending User Input]`

---

## 17. Open-Source License Details

Distributed under the permissive **MIT License**. See [`LICENSE`](LICENSE) for full legal text:
```
MIT License
Copyright (c) 2026 GlucoTwin Contributors
```

### Medical & Synthetic Data Disclaimer
GlucoTwin is an academic engineering prototype developed for the Happiest Health Digital Twin Challenge. All patient records, telemetry time-series, laboratory results, genetic markers, and clinician pagers are clinically modeled synthetic data. The software does not provide medical advice, diagnosis, or treatment recommendations.

---

## 18. All Files and Links Are Publicly Accessible Without Additional Permissions

All resources associated with GlucoTwin are verified to be **completely publicly accessible without requiring login credentials, request forms, or elevated permissions**:

1. **Public Source Repository:** [https://github.com/Yuvashri2516/Gluco-Twin](https://github.com/Yuvashri2516/Gluco-Twin) — Public GitHub repository, cloneable by anyone via `git clone`.
2. **Public Live Frontend Web Application:** [https://gluco-twin-eta.vercel.app/](https://gluco-twin-eta.vercel.app/) — Hosted on Vercel Edge; publicly accessible in any browser with zero authentication gates.
3. **Public Live Backend REST API:** [https://gluco-twin.onrender.com](https://gluco-twin.onrender.com) — Hosted on Render; public `/api/health` and OpenAPI documentation (`/docs`) accessible without API keys.
4. **Public Submission Deliverables:** All architectural diagrams, presentation decks, and video scripts reside directly in the root [`submission/`](submission) folder of the public repository and can be viewed or downloaded without permission hurdles.
