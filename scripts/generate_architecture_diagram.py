"""
generate_architecture_diagram.py - Generates Standalone High-Resolution Architecture Deliverables
Produces:
  - submission/GlucoTwin_Architecture.pdf
  - submission/GlucoTwin_Architecture.png
  - submission/GlucoTwin_Architecture.svg
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

os.makedirs("submission", exist_ok=True)

# Set up figure with clean medical tech styling
fig, ax = plt.subplots(figsize=(20, 11), dpi=300)
fig.patch.set_facecolor('#0b1120')
ax.set_facecolor('#0b1120')
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')

# Title & Header
ax.text(50, 96.5, "GlucoTwin System Architecture", fontsize=24, fontweight='bold', color='#f8fafc', ha='center')
ax.text(50, 93.5, "Multimodal Predictive Digital Twin for Proactive Glucose Risk Surveillance & Counterfactual Exploration",
        fontsize=12, color='#94a3b8', ha='center')
ax.plot([5, 95], [91.5, 91.5], color='#334155', lw=1.5)

# Helper function to draw rounded container boxes
def draw_box(x, y, w, h, bg_color, border_color, title, subtitle=None, title_color='#f8fafc'):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5,rounding_size=1.2",
                                  facecolor=bg_color, edgecolor=border_color, linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h - 2.8, title, fontsize=11, fontweight='bold', color=title_color, ha='center', va='center')
    if subtitle:
        ax.text(x + w/2, y + h - 5.0, subtitle, fontsize=8.5, color='#94a3b8', ha='center', va='center')

def draw_item(x, y, w, h, bg, border, text, subtext=None, text_color='#e2e8f0'):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=0.6",
                                  facecolor=bg, edgecolor=border, linewidth=1.0)
    ax.add_patch(rect)
    if subtext:
        ax.text(x + w/2, y + h/2 + 1.0, text, fontsize=9, fontweight='bold', color=text_color, ha='center', va='center')
        ax.text(x + w/2, y + h/2 - 1.2, subtext, fontsize=7.5, color='#94a3b8', ha='center', va='center')
    else:
        ax.text(x + w/2, y + h/2, text, fontsize=8.5, color=text_color, ha='center', va='center')

def draw_arrow(x1, y1, x2, y2, color='#38bdf8', label=None, style='solid'):
    linestyle = '-' if style == 'solid' else '--'
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(facecolor=color, edgecolor=color, arrowstyle="-|>", lw=1.8, linestyle=linestyle, mutation_scale=15))
    if label:
        ax.text((x1+x2)/2, (y1+y2)/2 + 1.2, label, fontsize=8, color=color, ha='center', va='center',
                bbox=dict(boxstyle="round,pad=0.2", facecolor='#0b1120', edgecolor='none', alpha=0.85))

# =============================================================================
# 1. COLUMN 1: MULTIMODAL SYNTHETIC DATA LAYER (x: 4 to 26)
# =============================================================================
draw_box(4, 18, 23, 70, '#131e33', '#1e293b', "1. MULTIMODAL SYNTHETIC DATA", "Simulated Clinical & Sensor Ingestion")

# Historical EHR Subpanel
draw_box(5.5, 54, 20, 31, '#1e293b', '#3b82f6', "Historical Synthetic EHR", "[Verified Stored Context]", '#60a5fa')
draw_item(6.5, 75.5, 18, 5.0, '#0f172a', '#475569', "Demographics & Phenotype", "Age, Subtype, Weight, Height, BMI")
draw_item(6.5, 68.5, 18, 5.0, '#0f172a', '#475569', "Historical Diagnoses", "HTN, Neuropathy, Dyslipidemia")
draw_item(6.5, 61.5, 18, 5.0, '#0f172a', '#475569', "Structured Lab Results", "HbA1c, Fasting Glucose, Lipids")
draw_item(6.5, 55.0, 18, 4.8, '#0f172a', '#475569', "Genetic Markers (EHR)", "TCF7L2, PPARG, KCNJ11 Risk Alleles")

# Dynamic Telemetry Subpanel
draw_box(5.5, 20, 20, 31, '#1e293b', '#06b6d4', "Dynamic Physiological Streams", "[15-Min Sampling Schedule]", '#22d3ee')
draw_item(6.5, 41.5, 18, 4.8, '#0f172a', '#475569', "Continuous Glucose (CGM)", "15-min intervals (40-400 mg/dL)")
draw_item(6.5, 35.0, 18, 4.8, '#0f172a', '#475569', "Cardiac Autonomic Vitals", "Heart Rate (bpm) & HRV (RMSSD)")
draw_item(6.5, 28.5, 18, 4.8, '#0f172a', '#475569', "Sleep Architecture Stream", "Deep, Light, REM Stages & Duration")
draw_item(6.5, 22.0, 18, 4.8, '#0f172a', '#475569', "Physical Activity Telemetry", "15-min Interval & Daily Cumulative Steps")


# =============================================================================
# 2. COLUMN 2: FASTAPI BACKEND & DATA PROCESSING (x: 32 to 67)
# =============================================================================
draw_box(31, 18, 37, 70, '#131e33', '#1e293b', "2. BACKEND & TWIN INTELLIGENCE", "FastAPI Core (Render Deployment: glucotwin-backend.onrender.com)")

# Ingestion & Validation Gateway
draw_box(32.5, 73, 34, 12, '#1e293b', '#64748b', "Data Ingestion & Controlled Simulation Feed", "Pydantic Schemas & Bounded Idempotence")
draw_item(34, 74.5, 15, 6.0, '#0f172a', '#334155', "Simulated Sensor Epoch Feed", "POST /api/digital-twin/simulate-feed")
draw_item(50, 74.5, 15, 6.0, '#0f172a', '#334155', "Idempotent Deduplication", "SQLite Unique Index on Alerts & Records")

# Digital Twin State & Feature Pipeline
draw_box(32.5, 45, 34, 25, '#1e293b', '#8b5cf6', "Digital Twin State Vector & Feature Engineering", "GET /api/digital-twin/{patient_id}", '#a78bfa')
draw_item(34, 57.5, 31, 7.5, '#0f172a', '#6d28d9', "Twin Dynamic Aggregation Engine",
          "Calculates 24h Baselines vs 1h Deltas (ΔG, ΔHR, ΔHRV), Sleep & Activity Summaries")
draw_item(34, 47.0, 31, 8.5, '#0f172a', '#475569', "14-Feature ML Vector (Leakage-Purged)",
          "Current G, 1h Mean, 1h StdDev, Trend Slope, HR, HRV, Circadian sin/cos, Subtypes")

# Analytical Engines (ML + Alerts + What-If)
draw_box(32.5, 20, 16.5, 22.5, '#1e293b', '#10b981', "ML Glucose Spike Engine", "Logistic Regression + Scaler", '#34d399')
draw_item(33.5, 22, 14.5, 15.5, '#0f172a', '#059669', "Binary Classifier (y >= 180)",
          "120-min Forward Horizon\nThreshold >= 180 mg/dL\nROC-AUC: 0.825\nStrict Purged Holdout")

draw_box(50.0, 20, 16.5, 22.5, '#1e293b', '#f59e0b', "Alerts & Counterfactual", "Surveillance & What-If", '#fbbf24')
draw_item(51.0, 31.5, 14.5, 6.0, '#0f172a', '#d97706', "Dual-Source Alert Engine", "Observed (<54, >250) vs Model")
draw_item(51.0, 22.0, 14.5, 8.0, '#0f172a', '#b45309', "What-If Sandbox (Heuristic)", "ΔG = Carbs*(0.40*K) - Act*(0.75)\nIllustrative Educational Sandbox")


# =============================================================================
# 3. COLUMN 3: CLINICIAN DASHBOARD & PRESENTATION (x: 72 to 96)
# =============================================================================
draw_box(72, 18, 24, 70, '#131e33', '#1e293b', "3. CLINICIAN DASHBOARD & TRIAGE", "React 19 / Vite SPA (Vercel: gluco-twin-eta.vercel.app)")

draw_item(73.5, 76.5, 21, 8.5, '#1e293b', '#38bdf8', "Patient Cohort Selector", "5 Diverse Clinical Personas\nInteractive Subject Switcher")
draw_item(73.5, 66.0, 21, 9.0, '#1e293b', '#38bdf8', "Multimodal Historical EHR Panel", "Longitudinal HbA1c, Fasting Glucose, Lipids,\n5 Genetic Marker Alleles with Synthetic Labels")
draw_item(73.5, 55.5, 21, 9.0, '#1e293b', '#38bdf8', "Dynamic Sensor Telemetry", "Synchronized CGM, HR, HRV Curves,\nSleep Hypnogram Stages & 15-Min Step Bars")
draw_item(73.5, 45.0, 21, 9.0, '#1e293b', '#38bdf8', "Digital Twin & Live Simulation", "State Vector Deltas, Sensor Coverage,\n+15m Simulated Sensor Feed Workflow")
draw_item(73.5, 34.5, 21, 9.0, '#1e293b', '#38bdf8', "Predictive Risk & What-If", "2h Spike Forecast with Explanations,\nCounterfactual Meal/Activity Sliders")
draw_item(73.5, 20.0, 21, 13.0, '#1e293b', '#f43f5e', "Alerts & Clinician Triage Pager",
          "Active, Acknowledged, Resolved Feed\n"
          "Simulated Hospital Pager Dispatch\n"
          "[Explicitly Disclaimed: Local Demo Only,\nNo External SMS/Email Sent]")


# =============================================================================
# CONNECTING ARROWS & DATA FLOWS
# =============================================================================
# EHR & Streams -> Ingestion Gateway
draw_arrow(27, 78, 32.5, 78, '#38bdf8', "Synthetic EHR & Labs")
draw_arrow(27, 35, 32.5, 74, '#22d3ee', "CGM, Vitals, Sleep, Steps")

# Gateway -> DB & Twin Engine
draw_arrow(49.5, 73, 49.5, 67, '#818cf8', "Validated Records")

# Twin Feature Vector -> ML Engine & What-If
draw_arrow(40.5, 45, 40.5, 37.5, '#34d399', "14-Feature Input")
draw_arrow(58.5, 45, 58.5, 37.5, '#fbbf24', "Baseline Telemetry")

# Engines -> UI
draw_arrow(68, 80, 72, 80, '#38bdf8', "Patient API")
draw_arrow(68, 60, 72, 60, '#a78bfa', "Digital Twin API")
draw_arrow(68, 31, 72, 31, '#34d399', "Spike Pred API")
draw_arrow(68, 23, 72, 23, '#fbbf24', "Alerts / What-If API")

# Demonstrable Simulation Feed Loop
draw_arrow(73.5, 48, 68, 77, '#f43f5e', "Trigger +15m Sensor Ingestion", style='dashed')

# =============================================================================
# FOOTER & LEGEND
# =============================================================================
ax.plot([5, 95], [14.0, 14.0], color='#334155', lw=1.0)
legend_text = (
    "LEGEND:  Solid Blue Lines = Implemented Automated Data Pipeline   |   "
    "Dashed Red Line = Demonstrable Interactive Simulated Sensor Update Workflow   |   "
    "Purple = Digital Twin Processing State   |   Green = Validated ML Model"
)
ax.text(50, 10.5, legend_text, fontsize=9.5, color='#cbd5e1', ha='center')

disclaimer_text = (
    "REGULATORY & ETHICAL NOTICE: GlucoTwin is an academic engineering research proof-of-concept for the Happiest Health Digital Twin Challenge. "
    "All telemetry, laboratory results, genetic markers, and clinician pagers are synthetic. Not for medical diagnosis, treatment, or clinical intervention."
)
ax.text(50, 7.5, disclaimer_text, fontsize=8.5, color='#94a3b8', style='italic', ha='center')

plt.tight_layout()

# Save PDF, PNG, SVG
pdf_path = "submission/GlucoTwin_Architecture.pdf"
png_path = "submission/GlucoTwin_Architecture.png"
svg_path = "submission/GlucoTwin_Architecture.svg"

plt.savefig(pdf_path, format='pdf', bbox_inches='tight', facecolor=fig.get_facecolor())
plt.savefig(png_path, format='png', bbox_inches='tight', facecolor=fig.get_facecolor(), dpi=300)
plt.savefig(svg_path, format='svg', bbox_inches='tight', facecolor=fig.get_facecolor())

plt.close()
print(f"Generated architecture diagrams successfully in submission/: {pdf_path}, {png_path}, {svg_path}")
