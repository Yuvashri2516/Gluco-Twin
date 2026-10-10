# GlucoTwin — Project Brief & Product Specification

**Project Title**: GlucoTwin: Predictive Patient Digital Twin with Early Warning & Intelligent Clinical Alerts  
**Tagline**: *Predict • Prevent • Protect | Smarter Insights. Healthier Tomorrows.*  
**Target Platform**: Web-based Clinical Dashboard (Responsive Desktop, Tablet, Mobile)  
**Version**: 0.1.0-alpha (Demonstration Prototype)  
**Safety Classification**: Research & Software Demonstration Prototype — Synthetic Data Only  

---

## 1. Project Goal & Overview

GlucoTwin is a software-only healthcare demonstration prototype engineered to advance metabolic care from reactive treatment to proactive risk prevention. 

Traditional Continuous Glucose Monitoring (CGM) systems alert patients and clinicians only after glycemic thresholds are crossed (e.g., alarming when blood glucose drops below $70\text{ mg/dL}$ or spikes above $180\text{ mg/dL}$). GlucoTwin introduces a **Patient Digital Twin Engine** that continuously assimilates historical clinical context (EHR) and streaming wearable signals (CGM, Heart Rate, Heart Rate Variability) to:
1. Maintain a dynamic, in-memory virtual representation of a patient's metabolic state.
2. Predict forward-looking glucose trajectories and spike/drop probabilities **up to 2 hours into the future**.
3. Demystify artificial intelligence predictions using **Explainable AI (SHAP-style feature attribution)**.
4. Provide a **Counterfactual "What-If" Simulation Sandbox** to evaluate prospective lifestyle or pharmacological interventions before they are executed.
5. Coordinate an **Intelligent Clinical Alert Management System** that prioritizes notifications, prevents alert fatigue, and tracks clinical acknowledgements.

> [!IMPORTANT]
> **Mandatory Safety & Compliance Notice**:
> This software is a demonstration prototype running exclusively on synthetic, simulated data (e.g., Synthea-derived EHR records and simulated physiological streams). It does **not** provide medical diagnoses, treatment recommendations, or verified clinical accuracy. The persistent label **"Synthetic Demonstration Environment — Not for Diagnostic Use"** must be visible across all screens.

---

## 2. Team Responsibilities & Separation of Concerns

To enable efficient, unblocked parallel execution, the project is strictly divided between frontend and backend domains:

```
┌────────────────────────────────────────────────────────┐
│            FRONTEND (Me - Lead UI/UX & React)          │
│                                                        │
│ • Figma UI/UX Design System & Prototypes               │
│ • React (Vite) Single Page Application                 │
│ • Responsive Layouts (Desktop, Tablet, Mobile)         │
│ • Data Visualizations (Recharts: CGM, XAI, What-If)   │
│ • Client-side Synthetic Mock Data & Fallback Services  │
│ • Interactive Simulation State & UX Workflows          │
└──────────────────────────┬─────────────────────────────┘
                           │ 
                 REST APIs / WebSockets
                           │ 
┌──────────────────────────┴─────────────────────────────┐
│          BACKEND (Teammate - Lead Backend & AI)        │
│                                                        │
│ • Python FastAPI Server & Uvicorn Runtime              │
│ • Data Ingestion Pipelines (Synthea & Wearable Stream) │
│ • Digital Twin Physiological Modeling Engine           │
│ • Machine Learning Models (XGBoost / LightGBM)         │
│ • Explainable AI Computation (SHAP Values)             │
│ • Database Schema, Migrations & Persistence (Postgres) │
│ • Alert Prioritization, Routing & Escalation Logic     │
└────────────────────────────────────────────────────────┘
```

---

## 3. Target User Roles & Clinical Personas

The GlucoTwin interface is optimized for multi-disciplinary healthcare teams:

### 1. Primary User: Attending Endocrinologist / Physician
* **Primary Need**: Rapid, high-density clinical triage.
* **Key Tasks**: 
  - Review 2-hour projected glycemic excursions during clinical rounds.
  - Inspect Explainable AI (XAI) factors to identify why a patient is experiencing unstable variability.
  - Review What-If simulation outputs to test regimen modifications (e.g., adjusting pre-meal boluses or physical activity).
  - Acknowledge critical alerts and document escalation protocols.

### 2. Secondary User: Diabetes Care Specialist / Clinical Nurse
* **Primary Need**: Longitudinal monitoring and patient routine optimization.
* **Key Tasks**:
  - Track daily Time-in-Range (TIR) metrics and Ambulatory Glucose Profile (AGP) compliance.
  - Review patient history, medication adherence, and lab milestones (HbA1c trends).
  - Respond to early-warning alerts before acute hypo/hyperglycemic events occur.

### 3. Tertiary User: Clinical Researcher / Digital Twin Engineer
* **Primary Need**: Assessment of twin model stability and simulation fidelity.
* **Key Tasks**:
  - Inspect sensor data quality (missing packet frequency, signal noise).
  - Monitor digital twin calibration status and prediction uncertainty bounds.

---

## 4. Scope: Six Required Dashboard Screens

| # | Screen Name | Architecture Stage Mapping | Primary Clinical Purpose |
| :- | :--- | :--- | :--- |
| **1** | **Overview Dashboard** | Stages 1, 3, 4, 6 | Clinical command center: real-time patient vitals, active twin status, 2-hour risk badge, recent telemetry preview, urgent alerts. |
| **2** | **Patient History** | Stage 1 (Static EHR) | Longitudinal clinical profile: demographics, diagnostic timeline, historical HbA1c/FBG labs, medication regimens, past encounters. |
| **3** | **Glucose Monitoring** | Stages 1 & 2 (Wearables/IoT) | High-resolution sensor inspection: continuous CGM curve, clinical target zones ($70\text{--}180\text{ mg/dL}$), synchronized HR/HRV stress telemetry. |
| **4** | **Predictive Analytics & XAI**| Stage 4 (ML & SHAP) | Forward-looking intelligence: 2-hour prediction cone with confidence bands, 3-tier risk gauge (Low/Mod/High), SHAP feature attribution waterfall. |
| **5** | **What-If Simulation** | Stage 5 (Counterfactuals) | Interactive sandbox: adjust activity, sleep, meal carbs, and insulin to compare baseline vs. simulated twin trajectories side-by-side. |
| **6** | **Alert Centre** | Stage 6 (Alert Management) | Operational triage: categorized alert feed (Critical, Warning, Info), acknowledgement tracking, escalation audit history. |

---

## 5. Ethical, Safety & Regulatory Standards

1. **Synthetic Data Integrity**: All demonstrated clinical records, sensor streams, and predictive curves are derived from synthetic generators (e.g., Synthea) or deterministic mathematical models.
2. **No Unsubstantiated Claims**: The prototype must not claim regulatory clearance (e.g., FDA 510(k), CE Mark, or CDSCO approval) nor publish unverified model accuracy statistics (e.g., claiming "99.8% clinical accuracy").
3. **Explicit Visual Differentiation**: The UI must maintain an unambiguous distinction between **historical recorded telemetry** (solid clinical blue line) and **simulated model projections** (dashed violet line with shaded uncertainty cone).
4. **Non-Blocking Architecture**: The frontend must function reliably in standalone mode using comprehensive local mock datasets so that UI validation is never blocked by backend availability.
