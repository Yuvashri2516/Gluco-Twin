# GlucoTwin — Hackathon Demonstration Video Recording Script & Checklist
**Happiest Health Digital Twin Challenge — Phase 1 Proof-of-Concept**

- **Target Video Duration:** 20 Minutes (Structured Comprehensive Clinical & Engineering Walkthrough)
- **Application URL (Local):** `http://127.0.0.1:5173`
- **Application URL (Live Production):** `https://gluco-twin-eta.vercel.app/`
- **Backend API (Live Production):** `https://gluco-twin.onrender.com`
- **Submission Output Location:** `submission/DEMO_VIDEO_SCRIPT.md`
- **Notice:** Research Prototype with Clinically Modeled Synthetic Telemetry. All demonstrations use synthetic data.

---

## Shot-by-Shot Timing & Segment Map

| Section | Timestamp | Focus Area | Visual / Screen Action |
|---|---|---|---|
| **Part 1** | 00:00 – 02:00 | Title, Motivation & Clinical Problem | Slide deck: Slides 1–3 (Problem Statement & Reactive CGM Paradox) |
| **Part 2** | 02:00 – 04:00 | Digital Twin Concept & Proposed Solution | Slide deck: Slides 4–5 & System Architecture Diagram |
| **Part 3** | 04:00 – 06:30 | Multimodal Synthetic EHR Deep-Dive | Dashboard: Patient Selector & **EHR & Lab History** Tab |
| **Part 4** | 06:30 – 09:00 | Dynamic Physiological Streams & Sleep | Dashboard: **Monitoring** & **Sleep & Activity** Tabs |
| **Part 5** | 09:00 – 12:00 | Demonstrable Digital Twin Simulation | Dashboard: **Digital Twin** Tab & "⚡ Simulate Sensor Feed" Trigger |
| **Part 6** | 12:00 – 14:30 | ML Spike Prediction Engine & Explanations | Dashboard: **Predictions** Tab & 2h Risk Assessment |
| **Part 7** | 14:30 – 16:30 | Clinical Risk Surveillance & Staff Pager | Dashboard: **Alerts** Tab & "Simulated Clinician Pager" Tab |
| **Part 8** | 16:30 – 18:30 | Counterfactual What-If Sandbox | Dashboard: **What-If Simulation** Tab & Sliders |
| **Part 9** | 18:30 – 20:00 | Model Evaluation, Limitations & Conclusion | Slide deck: Slides 10, 15, 17, 19 & Automated Tests summary |

---

## Detailed Speaker Dialogue & Action Script

### Part 1: Title, Clinical Motivation & The Reactive Care Paradox (00:00 – 02:00)
- **Screen:** Show Slide 1 (`GlucoTwin Title`) then transition to Slide 2 (`Problem Statement`).
- **Speaker Dialogue:**
  > *"Welcome evaluators. Today we are presenting **GlucoTwin**, an intelligent predictive digital twin for proactive glucose risk monitoring, developed for Phase 1 of the Happiest Health Digital Twin Challenge.*
  > 
  > *In modern diabetes management, both patients and clinical care teams face a fundamental limitation: current commercial CGM systems are almost entirely **reactive**. Alerts trigger only after an acute glycemic threshold has already been breached — after a patient has plunged into hypoglycemia below 54 or 70 mg/dL, or spiked above 180 or 250 mg/dL.*
  > 
  > *Furthermore, real-time sensor streams operate in complete silos from historical Electronic Health Records. Clinicians cannot readily see how historical diagnoses, longitudinal HbA1c lab panels, genetic susceptibility alleles, sleep architecture, and cardiac autonomic regulation correlate with real-time glucose dynamics. GlucoTwin was engineered to solve this fragmentation by creating a synchronized virtual digital twin."*

---

### Part 2: Architecture & System Overview (02:00 – 04:00)
- **Screen:** Show `submission/GlucoTwin_Architecture.pdf` or Slide 7 (`System Architecture`).
- **Speaker Dialogue:**
  > *"Before demonstrating the live software, let us examine the system architecture. GlucoTwin is designed with a modern decoupled stack: a React 19 single-page application communicating over strict Pydantic REST contracts with a FastAPI backend deployed on Render, backed by an ACID-compliant SQLite database.*
  > 
  > *Our data architecture unifies two major streams:
  > First, the **Historical Synthetic EHR layer**, encompassing demographic phenotype vectors, historical diagnoses, structured laboratory panels, and synthetic genetic markers.
  > Second, the **Dynamic Physiological Time-Series layer**, capturing synchronized continuous glucose, heart rate, autonomic HRV, polysomnographic sleep stages, and 15-minute physical activity steps.*
  > 
  > *These streams feed into our Digital Twin engine, which maintains continuous 24-hour moving baselines, computes 1-hour excursion deltas, powers our leak-free 14-feature Machine Learning spike prediction engine, drives a dual-source alert surveillance subsystem, and enables counterfactual what-if exploration. Let us now transition to the live application."*

---

### Part 3: Patient Selection & Historical EHR Deep-Dive (04:00 – 06:30)
- **Screen:** Switch to live dashboard at `http://127.0.0.1:5173`. Select **Elena Rostova (#1 - Type 2 Diabetes)**. Click on the sidebar item **EHR & Lab History**.
- **Speaker Dialogue:**
  > *"Here we are in the live doctor-facing clinical dashboard. In the top bar, you see our patient switcher. We have seeded five diverse synthetic patient personas representing Type 1 Diabetes, Type 2 Diabetes, and Pre-diabetes.*
  > 
  > *Let us examine Patient #1, Elena Rostova, a 52-year-old female with Type 2 diabetes. Clicking on the **EHR & Lab History** panel reveals her longitudinal profile:
  > Notice her verified clinical metrics: weight 78.5 kg, height 165 cm, and a derived BMI of 28.8 kg/m². Her historical diagnoses include Essential Hypertension, Dyslipidemia, and Mild Diabetic Neuropathy.*
  > 
  > *Below, we see her longitudinal laboratory results panel: HbA1c of 7.8% (above the 5.7% reference threshold), Fasting Blood Glucose of 142.0 mg/dL, and LDL Cholesterol of 135.0 mg/dL, clearly tracked with measurement dates and reference boundaries.*
  > 
  > *In the adjacent section, we inspect her synthetic genetic susceptibility markers: TCF7L2 (rs7903146 risk allele T) associated with impaired beta-cell secretion, and PPARG Pro12Ala associated with baseline insulin sensitivity. Notice our clear ethical notice: all genetic and lab records are synthetic demonstration data and are not presented as actual medical prognostications."*

---

### Part 4: Dynamic Sensor Streams & Sleep Architecture (06:30 – 09:00)
- **Screen:** Click sidebar item **Monitoring**, show synchronized CGM / HR / HRV curves. Then click **Sleep & Activity**.
- **Speaker Dialogue:**
  > *"Returning to the main **Monitoring** panel, observe how GlucoTwin renders synchronized multi-vital telemetry. The top card tracks glucose readings with time-in-range metrics. Directly below, we display synchronized cardiac autonomic vitals: heart rate in beats per minute and heart rate variability in milliseconds.*
  > 
  > *Now let us navigate to our newly implemented **Sleep & Activity** panel. Sleep architecture is a critical restorative modifier of insulin sensitivity. GlucoTwin tracks polysomnographic stages — deep sleep, light sleep, REM, and awake intervals — alongside calculated metrics such as total sleep duration (7.0 hours for Elena) and sleep efficiency percentage (85.7%).*
  > 
  > *Below the hypnogram, we inspect physical activity tracking. To prevent semantic confusion between interval exertion and daily totals, GlucoTwin clearly distinguishes 15-minute interval step counts from the daily cumulative total (4,200 steps). When we switch patients — for example to Marcus Vance (Patient #2) — the entire dashboard dynamically re-queries the backend, demonstrating complete patient data isolation with zero stale cache leakage."*

---

### Part 5: Demonstrable Digital Twin Live Simulation Workflow (09:00 – 12:00)
- **Screen:** Switch back to Patient #1 (Elena) and click **Digital Twin** in sidebar. Point out baseline vs 1h deltas, reading coverage, and latest sensor timestamp.
- **Speaker Dialogue:**
  > *"In Phase 5 of the challenge, we were tasked with making the digital twin update demonstrable without requiring physical wearable hardware. In the **Digital Twin Panel**, you see the real-time calculated phenotype vector and baseline comparisons: 24-hour mean glucose versus 1-hour recent delta, along with vital deltas (ΔHR and ΔHRV).*
  > 
  > *Notice the 'Simulate Sensor Ingestion Feed' module at the top of the panel. Here, a clinician or reviewer can simulate the passage of real-world time. Notice the current latest sensor timestamp displayed on screen.
  > 
  > *Let us click the button: **⚡ Simulate Sensor Feed (+15m)**.
  > 
  > *[Click the button]*
  > 
  > *Notice what just happened in real-time:
  > 1. The frontend issued a POST request to `/api/digital-twin/simulate-feed`.
  > 2. The backend ingested a new 15-minute sensor epoch advancing the patient's timeline.
  > 3. New glucose, HR, HRV, and interval step readings were safely committed to SQLite with idempotence protection.
  > 4. The alert surveillance engine automatically evaluated the new readings against clinical thresholds.
  > 5. The digital twin state vector recalculated instantaneously, updating the rolling 1-hour deltas and sensor coverage metrics.
  > 
  > *This demonstrates a fully functional, controlled digital twin loop without uncontrolled runaway background writes."*

---

### Part 6: Machine Learning Spike Prediction Engine (12:00 – 14:30)
- **Screen:** Click sidebar item **Predictions**. Click **"Run Spike Risk Assessment"**.
- **Speaker Dialogue:**
  > *"Now let us evaluate GlucoTwin's core machine learning capability: forward-looking glucose spike prediction.
  > 
  > *Clicking 'Run Spike Risk Assessment' sends a POST request to `/api/predict/spike`. Our prediction target is defined as: **Will glucose reach or exceed 180.0 mg/dL within the next 120 minutes?**
  > 
  > *Notice the transparent output card:
  > - Prediction Target: Hyperglycemic Spike (≥ 180 mg/dL)
  > - Prediction Horizon: 120 minutes (2 hours forward)
  > - Risk Score: 54.2% (Moderate Risk)
  > 
  > *Crucially, look at the **Feature Contribution Breakdown**. Rather than presenting an opaque black box, our logistic regression pipeline exposes exact feature contributions: rising glucose trend slope (+0.42), diabetes subtype weighting (+0.31), and depressed autonomic HRV (+0.18).
  > 
  > *Most importantly, our training pipeline was audited with extreme scientific discipline: preprocessing (StandardScaler) was fitted strictly on training data, and a 2-hour purged holdout split guarantees zero data leakage between past inputs and future prediction windows."*

---

### Part 7: Clinical Risk Surveillance & Simulated Staff Pager (14:30 – 16:30)
- **Screen:** Click sidebar item **Alerts**. Show the **Surveillance Feed** tab, then toggle to **Simulated Clinician Pager**.
- **Speaker Dialogue:**
  > *"In the **Clinical Risk Alert Engine**, GlucoTwin implements a dual-source surveillance framework. Look at the badges on each alert card:
  > - Cyan badges indicate **Observed Telemetry Alerts**, triggered when recorded historical readings cross safety thresholds (<54 mg/dL severe hypo, <70 mg/dL hypo, ≥180 mg/dL hyper, or tachycardia with depressed HRV).
  > - Purple badges indicate **Model-Predicted Alerts**, forecasting excursions 2 hours ahead.
  > 
  > *Clinicians can manage alerts through a full lifecycle: clicking 'Acknowledge' marks the alert as acknowledged with an immutable UTC timestamp. Clicking 'Resolve' closes the event. Deduplication keys prevent repeated duplicate alerts on page refreshes.
  > 
  > *Now, notice the new tab at the top: **Simulated Clinician Pager**.
  > 
  > *[Click Simulated Clinician Pager tab]*
  > 
  > *This screen demonstrates how a hospital triage desk routes critical alerts to on-call endocrinologists. Notice our clear ethical notice: external SMS and SMTP email are deliberately unconfigured in this demonstration build to ensure privacy and safety; all items represent simulated local dispatch events."*

---

### Part 8: Counterfactual What-If Sandbox (16:30 – 18:30)
- **Screen:** Click sidebar item **What-If Simulation**. Move the **Carbohydrate** slider to `+45g`, then adjust the **Physical Activity** slider to `30 min`.
- **Speaker Dialogue:**
  > *"Our next feature is the **What-If Counterfactual Sandbox**. Patients and clinicians often ask: 'What will happen to my glucose trajectory if I consume a meal with 45 grams of carbohydrates?'
  > 
  > *Adjusting the carbohydrate slider to +45g immediately projects a postprandial glucose rise from baseline 140 mg/dL to 171 mg/dL.
  > 
  > *Now, what if the patient engages in 30 minutes of moderate walking?
  > 
  > *[Move activity slider to 30 min]*
  > 
  > *The simulation dynamically calculates the muscular glucose uptake offset, bringing the projected peak down to 148.5 mg/dL and averting a hyperglycemic spike.
  > 
  > *Notice our prominent disclaimer banner: GlucoTwin explicitly documents this formula as an illustrative academic heuristic based on single-compartment kinetics. We never present heuristic estimates as validated pharmacological pharmacokinetics."*

---

### Part 9: Evaluation, Limitations & Conclusion (18:30 – 20:00)
- **Screen:** Return to Slide Deck: Slide 10 (`Model Evaluation & Baselines`), Slide 15 (`Automated Testing`), and Slide 19 (`Conclusion`).
- **Speaker Dialogue:**
  > *"To conclude our presentation, let us review our empirical evaluation and testing:
  > 
  > *In rigorous offline testing on purged holdout cohorts:
  > - GlucoTwin achieved an **ROC-AUC of 0.825**, Precision of 0.742, Recall of 0.718, and F1-score of 0.730.
  > - It substantially outperforms both the majority-class baseline (Accuracy 58.2%, F1 0.0) and the persistence baseline (F1 0.52).
  > - Calibration is confirmed with a Brier score of 0.162.
  > 
  > *Our codebase is validated by **71 automated unit and integration tests** in pytest — all passing with 100% success on isolated in-memory test databases without altering persistent data. Frontend ESLint is clean with 0 errors, and production builds compile in under 1 second.
  > 
  > *All submission deliverables — including our root MIT License, high-resolution Architecture Diagram PDF and SVG, PowerPoint presentation deck, and this recording checklist — are preserved in the repository.
  > 
  > *Thank you to the Happiest Health evaluation committee. We invite your questions and review of our live deployment at `gluco-twin-eta.vercel.app`."*

---

## Pre-Recording Verification Checklist

Before starting screen recording software (OBS Studio / Loom / Camtasia):

- [ ] **Backend Running:** Verify `python app/main.py` is running on `http://127.0.0.1:8000` (or verify live backend `https://gluco-twin.onrender.com/api/health`).
- [ ] **Frontend Running:** Verify `npm run dev` is running on `http://127.0.0.1:5173` (or verify live frontend `https://gluco-twin-eta.vercel.app/`).
- [ ] **Browser Resolution:** Set recording window to 1080p (1920x1080) at 100% zoom.
- [ ] **Clean Session:** Ensure test patient #1 (Elena) and patient #3 (Priya) load without console errors.
- [ ] **Audio Check:** Test microphone input levels; minimize background fan and keyboard noise.
- [ ] **Deliverables Present:** Verify `submission/GlucoTwin_Architecture.pdf` and `submission/GlucoTwin_Presentation.pptx` are open in background tabs for quick switching.
- [ ] **Submission Placeholder:** Keep YouTube/Vimeo recording URL field marked as pending user recording.
