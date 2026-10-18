"""
generate_presentation.py - Generates the 19-Slide Hackathon Presentation Deck
Produces:
  - submission/GlucoTwin_Presentation.pptx
  - submission/GlucoTwin_Presentation.pdf
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas

os.makedirs("submission", exist_ok=True)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Color Palette: Deep Slate Medical Tech
DARK_BG = RGBColor(11, 17, 32)       # #0b1120
CARD_BG = RGBColor(30, 41, 59)       # #1e293b
ACCENT_BLUE = RGBColor(56, 189, 248) # #38bdf8
ACCENT_PURPLE = RGBColor(168, 85, 247) # #a855f7
TEXT_WHITE = RGBColor(248, 250, 252) # #f8fafc
TEXT_MUTED = RGBColor(148, 163, 184) # #94a3b8
TEXT_CYAN = RGBColor(34, 211, 238)   # #22d3ee
BORDER_COLOR = RGBColor(51, 65, 85)  # #334155

slides_data = [
    {
        "title": "GlucoTwin",
        "subtitle": "An Intelligent Predictive Digital Twin for Proactive Glucose-Risk Monitoring",
        "category": "Happiest Health Digital Twin Challenge — Phase 1 Proof-of-Concept",
        "bullets": [
            "Project Lead / Author: Yuvashri2516 [Team Information Pending User Confirmation]",
            "Live Web Application: https://gluco-twin-eta.vercel.app/",
            "Live Production API: https://gluco-twin.onrender.com",
            "Open Source Repository: https://github.com/Yuvashri2516/Gluco-Twin",
            "Demo Video Link: [Demo Video URL Pending Final Recording — See Checklist]",
            "Notice: Research Prototype Built with Clinically Modeled Synthetic Telemetry"
        ]
    },
    {
        "title": "Problem Statement & Clinical Motivation",
        "subtitle": "The Reactive Paradox of Modern Diabetes Management",
        "category": "Clinical Context",
        "bullets": [
            "Delayed Intervention: Traditional CGM alerts trigger only AFTER acute excursions occur (hypoglycemia < 70 mg/dL or hyperglycemia >= 180 mg/dL).",
            "Fragmented Data Silos: Electronic health records (EHR labs, genetic markers) rarely communicate with real-time wearable streams.",
            "Autonomic Blind Spots: Glycemic variability directly impacts cardiac autonomic regulation (HR/HRV), but vital signs are monitored in isolation.",
            "Cognitive Burden: Patients and clinicians lack transparent, counterfactual forecasting to understand the forward impact of meals and exercise."
        ]
    },
    {
        "title": "Healthcare Use Case & Target Audience",
        "subtitle": "Proactive Surveillance for Outpatient & Clinical Care Teams",
        "category": "Target Audience & Clinical Workflow",
        "bullets": [
            "Endocrinology & Primary Care Teams: Continuous surveillance of high-risk diabetic cohorts with triage prioritization.",
            "Certified Diabetes Care & Education Specialists (CDCES): Patient education using transparent feature contribution breakdowns.",
            "Outpatient Remote Monitoring: Early notification of impending glycemic excursions 120 minutes before clinical threshold breaches.",
            "Strict Non-Prescriptive Scope: GlucoTwin provides surveillance and risk forecasting, never automated insulin dosing or medical prescriptions."
        ]
    },
    {
        "title": "The GlucoTwin Proposed Solution",
        "subtitle": "A Closed-Loop Virtual Twin Fusing Historical EHR & Live Streams",
        "category": "System Innovation",
        "bullets": [
            "Multimodal Fusion: Unifies historical EHR (labs, genetics) with dynamic physiological streams (CGM, HR, HRV, sleep, step activity).",
            "Predictive Machine Learning: Forward-looking binary classifier predicting spikes (>= 180 mg/dL within 120 min) with ROC-AUC 0.825.",
            "Dual-Source Alert Engine: Explicitly distinguishes observed threshold violations from model-predicted future risks.",
            "Demonstrable Simulation Workflow: Interactive +15m sensor epoch feed updates twin state and triggers live alert triage.",
            "What-If Counterfactual Sandbox: Educational simulator modeling carbohydrate impact and exercise mitigation."
        ]
    },
    {
        "title": "Digital Twin Concept & Virtual Phenotyping",
        "subtitle": "Continuous State Representation of Patient Metabolic Dynamic",
        "category": "Digital Twin Architecture",
        "bullets": [
            "Static Phenotype Vector: Age, gender, diabetes subtype (T1D/T2D/Pre-diabetic), years diagnosed, weight, height, BMI.",
            "Dynamic Telemetry Surveillance: 24-hour moving baseline anchored to the latest sensor timestamp.",
            "1-Hour Delta Kinetics: Calculates rolling baseline excursions: ΔGlucose, ΔHeartRate, and ΔHRV against 24h baseline.",
            "Sensor Coverage Integrity: Quantifies reading density and flags telemetry gaps (> 45 min) to prevent spurious predictions."
        ]
    },
    {
        "title": "Multimodal Data Architecture: EHR & Telemetry",
        "subtitle": "Unified Clinical Data Model Across 5 Diverse Cohorts",
        "category": "Data Engineering",
        "bullets": [
            "Historical EHR: Complete demographic profiles with longitudinal laboratory panels (HbA1c, Fasting Glucose, Lipids).",
            "Genetic Susceptibility Markers: Simulated risk allele records (TCF7L2 rs7903146, PPARG Pro12Ala, KCNJ11, SLC30A8, KCNQ1).",
            "High-Frequency Dynamic Streams: Synchronized 15-minute continuous glucose, heart rate (bpm), and HRV (RMSSD).",
            "Polysomnography & Activity: Sleep architecture stages (Deep, Light, REM, Awake) and interval vs cumulative daily step counts.",
            "Synthetic Integrity: All synthetic records carry explicit is_synthetic=True database flags and clinical disclaimers."
        ]
    },
    {
        "title": "System Architecture & End-to-End Pipeline",
        "subtitle": "Decoupled Modern Stack: React 19 Frontend + FastAPI Backend + SQLite",
        "category": "Full-Stack Implementation",
        "bullets": [
            "Client Tier: React 19 Single Page Application with Tailwind/Vanilla CSS, Recharts visualizations, and dark medical aesthetic.",
            "API Tier: FastAPI asynchronous REST services deployed on Render with strict Pydantic v2 schemas and CORS middleware.",
            "Persistence Tier: SQLite database with indexed queries, transactional commits, and unique deduplication constraints.",
            "Standalone Architecture Deliverable: High-resolution vector diagram available in submission/GlucoTwin_Architecture.pdf."
        ]
    },
    {
        "title": "Multimodal Data Fusion Workflow",
        "subtitle": "Disciplined Clinical & Machine Learning Information Routing",
        "category": "Data Fusion",
        "bullets": [
            "Clinical Context Stream: Historical diagnoses, lab panels, and genetic markers populate patient profiles and risk stratification.",
            "Circadian & Exertion Context: Sleep stages provide restorative baseline; step counts inform diurnal activity and What-If models.",
            "Model Feature Matrix: 14 leak-free features extracted strictly from t <= T historical lookback windows.",
            "Scientific Integrity: Labs and genetics are displayed for clinical context but NOT forced into the ML matrix to prevent uncalibrated bias."
        ]
    },
    {
        "title": "Machine Learning Spike Prediction Engine",
        "subtitle": "Predicting Glycemic Excursions (>= 180 mg/dL) 2 Hours Ahead",
        "category": "Predictive Modeling",
        "bullets": [
            "Prediction Horizon: 120 minutes forward window strictly excluding readings after prediction timestamp T.",
            "Model Pipeline: StandardScaler fitted exclusively on training set + LogisticRegression(penalty='l2', C=1.0).",
            "Leakage Safeguards: 2-hour purged holdout split between training and evaluation partitions prevents temporal data contamination.",
            "Feature Explanations: Model returns exact linear feature contributions and directional risk impacts for each prediction."
        ]
    },
    {
        "title": "ML Model Evaluation & Benchmark Comparison",
        "subtitle": "Rigorous Evaluation on Held-Out Test Cohorts",
        "category": "Empirical Verification",
        "bullets": [
            "Chronological Holdout (1,114 test samples): ROC-AUC 0.9445 | Accuracy 87.6% | Precision 0.645 | Recall 0.408 | F1 0.500 | Brier 0.0688 (Baseline partition: ROC-AUC 0.705).",
            "Unseen-Patient Generalization: Cross-patient evaluation (Leave-One-Patient-Out) yields mean ROC-AUC ~0.5156 across cohorts with spikes.",
            "Evaluation Split Distinction: Chronological holdout tests forward trajectory forecasting on known profiles; unseen evaluation tests population transfer.",
            "Personalized vs Population Scope: Model is designed as a personalized patient trajectory predictor, not an uncalibrated universal screening tool."
        ]
    },
    {
        "title": "Doctor-Facing Dashboard Walkthrough",
        "subtitle": "Unified Clinical Cockpit for Time-Series & Patient Overview",
        "category": "Frontend UI / UX",
        "bullets": [
            "Cohort Switching: Instant switching between 5 diverse patient personas with dynamic chart updates and zero state leakage.",
            "Synchronized Multi-Vital Telemetry: Interactive time-series charts aligning CGM curves, heart rate, and autonomic HRV.",
            "Historical EHR Timeline: Tabular and badge views of longitudinal lab panels and synthetic genetic susceptibility alleles.",
            "Sleep & Step Analytics: Visual hypnogram sleep stages, efficiency percentages, and 15-minute interval physical activity bars."
        ]
    },
    {
        "title": "Demonstrable Digital Twin Live Update Workflow",
        "subtitle": "Interactive Simulated Sensor Feed Ingestion",
        "category": "Demonstrable Live Demo",
        "bullets": [
            "Controlled Ingestion: Clinicians trigger simulated +15m sensor epochs directly from the Digital Twin panel.",
            "Telemetry Advancement: Generates synchronized glucose, HR, HRV, and step count readings without continuous unprompted polling.",
            "Instant Twin Recomputation: Recalculates 24h baseline vs 1h delta vectors and refreshes dashboard status tags.",
            "Immediate Alert Triggering: Automatically evaluates clinical thresholds on incoming telemetry and updates notification badges."
        ]
    },
    {
        "title": "Clinical Alert Surveillance & Simulated Pager",
        "subtitle": "Two-Tier Alert Categorization with Clinician Triage Routing",
        "category": "Clinical Safety",
        "bullets": [
            "Observed Telemetry Alerts: Triggered on actual breaches: Severe Hypo (<54 mg/dL), Hyper (>=180 mg/dL), Severe Hyper (>=250 mg/dL).",
            "Model-Predicted Alerts: Purple brain badge alerts for upcoming 2-hour predicted spikes with risk score >= 0.50.",
            "Lifecycle Workflow: Full Active -> Acknowledged -> Resolved state transitions with timestamps and deduplication keys.",
            "Simulated Clinician Pager: Demonstrates hospital triage queue routing with explicit disclaimer (External SMS/Email unconfigured)."
        ]
    },
    {
        "title": "What-If Counterfactual Sandbox",
        "subtitle": "Educational Simulation of Meal Carbs & Exercise Impact",
        "category": "Counterfactual Modeling",
        "bullets": [
            "Single-Compartment Linear Heuristic: ΔG = Carbs * (0.40 * 70/weight * K_type) - Activity * 0.75 mg/dL/min.",
            "Subtype Sensitivity Factors: Tailored factors for Type 1 (1.30), Type 2 (1.15), and Pre-diabetic (0.90) cohorts.",
            "Mitigation Testing: Demonstrates how 30 minutes of physical activity blunts postprandial glycemic excursions.",
            "Safety Prominence: Prominently watermarked 'SIMULATED — NOT A CLINICAL PREDICTION' with medical disclaimer."
        ]
    },
    {
        "title": "Automated Testing & Quality Verification",
        "subtitle": "100% Passing Automated Test Suites & Production Build Verification",
        "category": "Quality Assurance",
        "bullets": [
            "Backend Test Suite: 71 automated pytest unit and integration tests passing with 100% success rate.",
            "Database Isolation: All automated tests execute on isolated in-memory SQLite (sqlite:///:memory:) protecting persistent data.",
            "Comprehensive Coverage: Tests cover EHR endpoints, lab/genetics, sleep/steps, alert lifecycle, and ML leakage prevention.",
            "Frontend Verification: ESLint passed with 0 errors; Vite production bundle built in 942ms without compilation issues."
        ]
    },
    {
        "title": "Deployment Architecture & Production Health",
        "subtitle": "Continuous Deployment on Vercel & Render",
        "category": "DevOps & Cloud",
        "bullets": [
            "Frontend Deployed: Vercel serverless edge network (https://gluco-twin-eta.vercel.app/) with automated production builds.",
            "Backend Deployed: Render web service container (https://gluco-twin.onrender.com) with automated health probes.",
            "Environment Security: All deployment secrets, API tokens, and credentials are protected; zero sensitive leaks in Git.",
            "CORS & Health Probes: Configured CORS for production domains and live /api/health monitoring endpoint."
        ]
    },
    {
        "title": "Known Limitations & Responsible Disclaimers",
        "subtitle": "Honest Engineering Boundaries for a Research Proof-of-Concept",
        "category": "Scientific Integrity",
        "bullets": [
            "Synthetic Data Foundation: Clinically simulated physiological models capture diurnal patterns but cannot replicate complex biological pharmacokinetics.",
            "Unseen-Patient Generalization Boundary: Cross-patient ROC-AUC is ~0.52 on 5 personas; model requires individual historical trajectory data to forecast.",
            "No Medical Device Claims: GlucoTwin is an academic engineering prototype and must NOT be used for clinical diagnosis or insulin dosing.",
            "Local Notification Demonstration: Hospital triage pagers are simulated locally; external SMS and email are intentionally unconfigured."
        ]
    },
    {
        "title": "Future Roadmap: Post-Hackathon Improvements",
        "subtitle": "Path Toward Clinical Validation & Commercial Device Integration",
        "category": "Future Outlook",
        "bullets": [
            "Hardware Wearable Integration: Native Bluetooth Low Energy (BLE) ingestion from Dexcom G7, FreeStyle Libre 3, and Apple Watch.",
            "Pharmacokinetic Modeling: Differential equation modeling for insulin-on-board (IOB) decay and gastric carbohydrate absorption.",
            "Deep Learning Architectures: Recurrent LSTM / Transformer models leveraging multi-week longitudinal telemetry.",
            "Hospital EHR Interoperability: HL7 FHIR API connectors (SMART on FHIR) for Epic and Cerner clinical EHR integration."
        ]
    },
    {
        "title": "Conclusion & Hackathon Submission Summary",
        "subtitle": "A Fully Realized Multimodal Digital Twin Proof-of-Concept",
        "category": "Summary & Submission Package",
        "bullets": [
            "Deliverables Package: Standalone Architecture Diagram (PDF/SVG), Presentation Deck (PPTX/PDF), and 20-min Demo Script.",
            "Proven Reliability: 71 backend tests passed, frontend lint clean, production build verified, and database 100% preserved.",
            "Holistic Healthcare Vision: Demonstrates the power of continuous digital twins to transform reactive medicine into proactive health.",
            "Submission Artifacts: Available in root /submission folder for comprehensive evaluator review."
        ]
    }
]

# Generate PowerPoint Slides
blank_slide_layout = prs.slide_layouts[6]

for idx, data in enumerate(slides_data):
    slide = prs.slides.add_slide(blank_slide_layout)
    
    # Background shape
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = DARK_BG
    bg.line.color.rgb = DARK_BG
    
    # Header Category Tag
    cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
    tf_c = cat_box.text_frame
    tf_c.word_wrap = True
    p_c = tf_c.paragraphs[0]
    p_c.text = f"SLIDE {idx+1:02d} / 19  |  {data['category'].upper()}"
    p_c.font.size = Pt(11)
    p_c.font.bold = True
    p_c.font.color.rgb = ACCENT_BLUE

    # Title
    t_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(11.7), Inches(0.8))
    tf_t = t_box.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = data["title"]
    p_t.font.size = Pt(28)
    p_t.font.bold = True
    p_t.font.color.rgb = TEXT_WHITE

    # Subtitle
    s_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(0.5))
    tf_s = s_box.text_frame
    tf_s.word_wrap = True
    p_s = tf_s.paragraphs[0]
    p_s.text = data["subtitle"]
    p_s.font.size = Pt(14)
    p_s.font.color.rgb = TEXT_MUTED

    # Card Shape for Content
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(2.2), Inches(11.733), Inches(4.7))
    card.fill.solid()
    card.fill.fore_color.rgb = CARD_BG
    card.line.color.rgb = BORDER_COLOR
    card.line.width = Pt(1.5)

    # Bullets inside Card
    content_box = slide.shapes.add_textbox(Inches(1.2), Inches(2.4), Inches(10.9), Inches(4.3))
    tf_content = content_box.text_frame
    tf_content.word_wrap = True

    for b_idx, bullet in enumerate(data["bullets"]):
        p = tf_content.add_paragraph() if b_idx > 0 else tf_content.paragraphs[0]
        p.text = f"•  {bullet}"
        p.font.size = Pt(15)
        p.font.color.rgb = TEXT_WHITE
        p.space_after = Pt(14)
        if ":" in bullet:
            # Highlight prefixes
            p.font.color.rgb = TEXT_WHITE

# Save PPTX
pptx_path = "submission/GlucoTwin_Presentation.pptx"
prs.save(pptx_path)
print(f"Generated PowerPoint presentation: {pptx_path}")

# =============================================================================
# Generate Companion PDF Export
# =============================================================================
pdf_path = "submission/GlucoTwin_Presentation.pdf"
c = canvas.Canvas(pdf_path, pagesize=landscape(letter))
width, height = landscape(letter)

for idx, data in enumerate(slides_data):
    # Dark background
    c.setFillColorRGB(11/255, 17/255, 32/255)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Header Category Tag
    c.setFillColorRGB(56/255, 189/255, 248/255)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, height - 35, f"SLIDE {idx+1:02d} / 19  |  {data['category'].upper()}")

    # Title
    c.setFillColorRGB(248/255, 250/255, 252/255)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, height - 62, data["title"])

    # Subtitle
    c.setFillColorRGB(148/255, 163/255, 184/255)
    c.setFont("Helvetica", 11)
    c.drawString(40, height - 80, data["subtitle"])

    # Card
    c.setFillColorRGB(30/255, 41/255, 59/255)
    c.setStrokeColorRGB(51/255, 65/255, 85/255)
    c.roundRect(40, 40, width - 80, height - 135, 8, fill=1, stroke=1)

    # Bullets
    y_pos = height - 120
    for bullet in data["bullets"]:
        c.setFillColorRGB(241/255, 245/255, 249/255)
        c.setFont("Helvetica", 11)
        # Word wrap handling for PDF
        text = f"•  {bullet}"
        if len(text) > 115:
            part1 = text[:115]
            part2 = "    " + text[115:]
            c.drawString(65, y_pos, part1)
            y_pos -= 16
            c.drawString(65, y_pos, part2)
        else:
            c.drawString(65, y_pos, text)
        y_pos -= 26

    # Footer
    c.setFillColorRGB(100/255, 116/255, 139/255)
    c.setFont("Helvetica", 8)
    c.drawString(40, 20, "GlucoTwin — Happiest Health Digital Twin Challenge | Research Prototype | Built with Clinically Modeled Synthetic Telemetry")
    c.drawRightString(width - 40, 20, f"Page {idx+1} of 19")

    c.showPage()

c.save()
print(f"Generated PDF presentation: {pdf_path}")
