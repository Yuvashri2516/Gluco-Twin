# GlucoTwin — Frontend Architecture Specification

**Framework**: React (Vite)  
**Language**: JavaScript (ES Modules / Modern ECMAScript)  
**Visualization Engine**: Recharts (Composable SVG)  
**Styling Paradigm**: Vanilla CSS with CSS Custom Properties (Design Tokens)  
**Iconography**: Lucide React  
**Target Resolution**: Fully Responsive (Desktop 1440px+, Tablet 768px–1024px, Mobile 375px–767px)  

---

## 1. Technical Stack & Architectural Principles

### 1.1 Technology Choices

* **Vite**: Chosen for near-instant development server startup, optimized Rollup-based production builds, and zero-configuration ES module support.
* **React 18+**: Provides a component-driven declarative architecture ideal for complex clinical dashboards with concurrent UI states.
* **Vanilla CSS + Custom Properties**: Provides full design control without third-party framework overhead. Design tokens (`--color-primary`, `--spacing-md`, etc.) ensure 1:1 mapping with Figma styles.
* **Recharts**: Built on React and SVG. Offers declarative primitives (`<LineChart>`, `<ReferenceArea>`, `<ResponsiveContainer>`) required for physiological time-series, target glucose bands, and uncertainty envelopes.
* **Lucide React**: Featherweight, tree-shakeable clinical and navigation icons.

### 1.2 Core Architectural Principles

1. **Decoupled Service Boundary**: The UI must interact with backend capabilities strictly through an API service abstraction layer (`src/services/apiClient.js`). A toggle (`VITE_USE_MOCK_DATA=true`) enables the frontend to run entirely standalone with realistic synthetic fixtures.
2. **Deterministic UI State**: The dashboard avoids hidden or mutable side-effects. Simulated continuous telemetry is driven by a predictable tick hook (`useTelemetryStream`) that can be paused, resumed, or scrubbed.
3. **Clinical Hierarchy & Density**: Visual hierarchy ensures critical indicators (current glucose, impending hypo/hyper risks, system notices) are readable within 3 seconds of screen viewing.
4. **Resilient Offline / Mock Fallback**: When backend APIs are unreachable or unimplemented, the application displays clear non-blocking placeholder states and informs the clinician that local synthetic data is active.

---

## 2. Directory Structure & File Hierarchy

```
d:\Projects\Gluco-Twin\
├── docs/                             # Engineering and architecture documentation
│   ├── PROJECT_BRIEF.md
│   ├── FRONTEND_ARCHITECTURE.md
│   ├── FIGMA_DESIGN_NOTES.md
│   └── API_INTEGRATION.md
│
├── public/                           # Static assets, favicon, medical symbols
│
└── src/
    ├── assets/                       # Brand logos, illustrations
    │
    ├── styles/                       # Global design system
    │   ├── tokens.css                # CSS custom properties (colors, typography, spacing)
    │   ├── reset.css                 # Modern CSS normalization
    │   └── global.css                # Base typographic, utility, and layout rules
    │
    ├── components/
    │   ├── common/                   # Reusable atomic UI primitives
    │   │   ├── Badge.jsx             # Clinical status pills (Target, Warning, Critical)
    │   │   ├── Button.jsx            # Standard, ghost, outline, and icon buttons
    │   │   ├── Card.jsx              # Surface wrapper with uniform border & shadow
    │   │   ├── MetricCard.jsx        # Top-row KPI summary cards with trend arrows
    │   │   ├── Modal.jsx             # Accessible overlay dialog
    │   │   ├── SliderInput.jsx       # Controlled slider with numeric readout
    │   │   ├── SyntheticNotice.jsx   # Mandatory persistent synthetic disclaimer banner
    │   │   └── Tooltip.jsx           # Clinical glossary definition tooltip
    │   │
    │   ├── layout/                   # Global shell components
    │   │   ├── AppLayout.jsx         # Frame holding TopNav, Sidebar, and View content
    │   │   ├── TopNav.jsx            # Patient switcher, twin status indicator, alerts bell
    │   │   ├── SidebarNav.jsx        # Navigation links for the 6 core screens
    │   │   └── Footer.jsx            # Disclaimer footer, version, architecture credits
    │   │
    │   ├── charts/                   # Recharts visualization wrappers
    │   │   ├── TrajectoryChart.jsx   # Historical CGM + 2h forecast + target reference band
    │   │   ├── BiometricsChart.jsx   # Heart Rate (BPM) & HRV (RMSSD) time-series
    │   │   ├── TimeInRangeBar.jsx    # Stacked clinical percentage bar (TIR / TAR / TBR)
    │   │   ├── ShapWaterfallChart.jsx# Horizontal feature attribution bars (XAI)
    │   │   └── SimulationChart.jsx   # Baseline vs. counterfactual comparison chart
    │   │
    │   ├── twin/                     # Digital Twin status modules
    │   │   ├── TwinStatusCard.jsx    # Sync latency, model calibration, parameter summary
    │   │   └── MetabolicStateCard.jsx# Active Insulin-on-Board (IOB) & Carbs-on-Board (COB)
    │   │
    │   ├── simulation/               # What-if sandbox modules
    │   │   ├── SimulationControls.jsx# Sliders for Activity, Sleep, Carbs, Medication
    │   │   ├── DeltaSummary.jsx      # Metrics table comparing baseline vs. projected
    │   │   └── PresetSelector.jsx    # Quick scenario buttons (High Carb, Post-Gym, etc.)
    │   │
    │   └── alerts/                   # Alert centre modules
    │       ├── AlertCard.jsx         # Severity-coded card with triage action triggers
    │       ├── AlertFilterTabs.jsx   # Filter pills: All, Critical, Warning, Info
    │       └── EscalationModal.jsx   # Doctor acknowledgement/escalation workflow
    │
    ├── screens/                      # The 6 primary dashboard views
    │   ├── OverviewScreen.jsx        # Screen 1: Command Center & Triage
    │   ├── PatientHistoryScreen.jsx  # Screen 2: Longitudinal EHR & Encounter Log
    │   ├── MonitoringScreen.jsx      # Screen 3: High-Resolution Sensor Telemetry
    │   ├── PredictionXaiScreen.jsx   # Screen 4: 2-Hour Horizon & Feature Drivers
    │   ├── SimulationScreen.jsx      # Screen 5: Counterfactual What-If Sandbox
    │   └── AlertCentreScreen.jsx     # Screen 6: Operational Alert Management
    │
    ├── context/                      # Lightweight React Context providers
    │   ├── PatientContext.jsx        # Active patient archetype, demographics, medical baseline
    │   ├── SimulationContext.jsx     # What-if scenario parameters and comparison output
    │   └── AlertContext.jsx          # Alert feed, unread counter, acknowledgement actions
    │
    ├── hooks/                        # Custom reusable React hooks
    │   ├── usePatient.js             # Consumes PatientContext
    │   ├── useTelemetryStream.js     # Simulated real-time tick and streaming array
    │   └── useSimulation.js          # Client-side deterministic metabolic response formula
    │
    ├── services/                     # Data and API integration layer
    │   ├── mockData.js               # Comprehensive synthetic patient archetypes and curves
    │   └── apiClient.js              # REST / WebSocket adapter with mock fallback
    │
    ├── App.jsx                       # Screen routing and global state providers
    └── main.jsx                      # Vite application entry point
```

---

## 3. Screen Layout & Component Mapping

### Screen 1: Overview Dashboard
* **Route / State**: `currentScreen === 'overview'`
* **Primary Layout**:
  - **Header Region**: `SyntheticNotice` + Patient Quick Info Pill.
  - **Metric Grid (4 Columns)**: 
    1. `MetricCard` — Current Glucose ($142\text{ mg/dL}$, upward vector, Target Zone badge).
    2. `MetricCard` — 2-Hour Forecast ($198\text{ mg/dL}$, Amber badge, Spike probability $58\%$).
    3. `MetricCard` — Time-in-Range ($78\%$, Target: $>70\%$, subtext: $18\text{h }42\text{m}$).
    4. `MetricCard` — Active Metabolic Load ($\text{IOB}: 1.2\text{ U} \mid \text{COB}: 35\text{g}$).
  - **Main Split Area (65% / 35%)**:
    - **Left**: `TrajectoryChart` (Past 4 hours continuous telemetry in solid blue, target zone in translucent green $70\text{--}180\text{ mg/dL}$, 2-hour dashed violet projection).
    - **Right**: `TwinStatusCard` (Synchronization health, drift index, model type: XGBoost/Compartmental) + `AlertCard` (top unacknowledged warning).
  - **Bottom Row**: Mini `ShapWaterfallChart` preview + `TimeInRangeBar`.

### Screen 2: Patient History
* **Route / State**: `currentScreen === 'history'`
* **Primary Layout**:
  - **Left Profile Column (30%)**: Patient demographic card (Age, Gender, BMI, Diabetes duration, Current Regimen, Emergency Contact, Baseline Insulin Sensitivity Factor).
  - **Right Clinical Column (70%)**:
    - **Longitudinal Lab Trends Card**: Recharts area chart showing HbA1c progression over the last 18 months against the $<7.0\%$ clinical goal.
    - **Medication Regimen Table**: Active medications (Basal Glargine, Rapid Aspart, Metformin), dosing, schedule, adherence status.
    - **Clinical Encounter Timeline**: Chronological log of recent outpatient consultations, notes, and lab reviews.

### Screen 3: Glucose Monitoring
* **Route / State**: `currentScreen === 'monitoring'`
* **Primary Layout**:
  - **Sensor Quality Strip**: Active Wearable Health ($99.4\%$ valid packets, zero sensor drift, battery: $84\%$).
  - **Interactive Time Window Bar**: Pills for `[2 Hours]` `[6 Hours]` `[12 Hours]` `[24 Hours]`.
  - **High-Density Recharts Panel**:
    - Full-width `TrajectoryChart` with annotated meal events (Fork icon) and bolus events (Syringe icon).
    - Clinical reference bands clearly labeled (Severe Low $<54$, Low $54\text{--}69$, Target $70\text{--}180$, High $>180$, Severe High $>250$).
  - **Synchronized Secondary Telemetry**: `BiometricsChart` aligning Continuous Glucose with Heart Rate (BPM) and HRV RMSSD (ms) to visualize physiological stress correlations.
  - **Clinical AGP Metrics Panel**: Average Glucose, Glucose Management Indicator (GMI), Coefficient of Variation (%CV).

### Screen 4: Predictive Analytics & Explainable AI (XAI)
* **Route / State**: `currentScreen === 'prediction'`
* **Primary Layout**:
  - **Top Prediction Metric Header**: 
    - 2-Hour Spike Probability Gauge (Circular or segmented progress bar: $0\text{--}30\%$ Low, $31\text{--}60\%$ Moderate, $61\text{--}100\%$ High).
    - Estimated Peak Time and Estimated Nadir Time.
  - **Prediction Trajectory with Uncertainty Cone**: Recharts line chart showing the median projection line surrounded by an upper ($95\text{th}$ percentile) and lower ($5\text{th}$ percentile) shaded area representing predictive uncertainty.
  - **SHAP Feature Attribution Section**:
    - Title: *"Physiological Drivers Influencing Current Prediction"*
    - Subtitle: *"Model: Proposed XGBoost / LightGBM Regressor (Simulated Attribution Weights)"*
    - `ShapWaterfallChart`: Diverging horizontal bar chart displaying factor contributions (e.g., Active Carbohydrates $+42\text{ mg/dL}$, Insulin on Board $-24\text{ mg/dL}$, Resting Heart Rate $+6\text{ mg/dL}$, Circadian Basal Drift $-4\text{ mg/dL}$).

### Screen 5: What-If Simulation (Counterfactual Sandbox)
* **Route / State**: `currentScreen === 'simulation'`
* **Primary Layout**:
  - **Two-Column Interactive Sandbox (40% Controls / 60% Visualization)**:
    - **Controls Panel**:
      - `PresetSelector`: Quick scenario buttons (`[High Carb Meal]`, `[Light Exercise]`, `[Missed Bolus]`, `[Extended Sleep]`).
      - `SliderInput` for Physical Activity: $-30\text{ min}$ to $+90\text{ min}$ (default: $+20\text{ min}$).
      - `SliderInput` for Sleep / Rest: $-2\text{ hours}$ to $+2\text{ hours}$ (default: $+1\text{ hour}$).
      - `SliderInput` for Meal Carbs: $0\text{g}$ to $120\text{g}$ (default: $45\text{g}$).
      - Medication Toggle: Rapid Insulin Adjustment ($0\text{ to }6\text{ Units}$).
      - Button Group: Primary Teal `[Run Simulation]` and Ghost `[Reset to Baseline]`.
    - **Visualization Panel**:
      - `SimulationChart`: Simultaneous overlay of **Baseline Forecast** (Solid Slate Line) vs. **Counterfactual Twin Forecast** (Dashed Violet Line).
      - `DeltaSummary` Card: Clear comparative readout:
        * Projected Peak: $198\text{ mg/dL} \rightarrow 164\text{ mg/dL}$ ($-34\text{ mg/dL}$ reduction).
        * Estimated Time-in-Range: $78\% \rightarrow 86\%$ ($+8\%$ improvement).
        * Risk Tier: Moderate $\rightarrow$ Low.

### Screen 6: Alert Centre
* **Route / State**: `currentScreen === 'alerts'`
* **Primary Layout**:
  - **Triage Filter Bar**: Filter pills with badges (`[All Alerts (5)]`, `[Critical (1)]`, `[Warnings (3)]`, `[System Info (1)]`).
  - **Alert Feed Queue**: Sorted chronologically by urgency.
    - Each `AlertCard` features a left severity strip, clear timestamp, category icon, trigger source (Predictive Engine vs. Threshold), actionable advice, and two action buttons: `[Acknowledge]` and `[Escalate]`.
  - **Escalation & Resolution Drawer**: Displays audit trail of previous alerts, who acknowledged them, and what clinical actions were logged.

---

## 4. Responsive Design Strategy

The layout relies on clean CSS Grid and Flexbox with responsive breakpoints:

```
[ Breakpoint Map ]
├── Desktop (Large):   >= 1440px  -> Full 4-column KPI grid, 65/35 dual-panel main body, persistent 240px sidebar
├── Desktop (Standard): 1025px - 1439px -> 4-column KPI grid, stacked charts if needed
├── Tablet (Landscape): 768px - 1024px  -> 2-column KPI grid, collapsible sidebar into top bar icon, stacked simulation panels
└── Mobile:             < 768px         -> 1-column KPI cards, full-width charts with horizontal scroll, bottom-sheet controls
```

### Breakpoint Specifications
1. **Desktop ($>1024\text{px}$)**:
   - Sidebar: Fixed width $240\text{px}$.
   - Content: Flexible `calc(100vw - 240px)` with max-width container $1600\text{px}$.
   - Charts: Multi-axis and side-by-side comparative views.
2. **Tablet ($768\text{px} \text{ to } 1024\text{px}$)**:
   - Sidebar: Collapses to a compact icon-only rail ($64\text{px}$) or hamburger drawer.
   - KPI metrics: Wrap into a $2 \times 2$ grid.
   - Simulation panel: Controls stack directly above the comparative chart.
3. **Mobile ($<768\text{px}$)**:
   - Sidebar: Hidden behind a modern mobile slide-over drawer.
   - Top Nav: Streamlined patient identity badge and notification counter.
   - KPI metrics: Vertical stack or single-row horizontal swipe carousel.
   - Charts: `<ResponsiveContainer width="100%" height={260}>` with optimized axis tick density.

---

## 5. State Management & Data Flow Architecture

A lightweight React Context structure avoids heavy external dependencies while keeping states clean and modular:

```
                  [ App Root ]
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
    [ PatientContext ]    [ AlertContext ]
             │                   │
             └─────────┬─────────┘
                       ▼
             [ SimulationContext ]
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
[ OverviewScreen ] [ Monitoring ] [ SimulationScreen ]
```

1. **`PatientContext`**: Stores active patient identity (defaulting to synthetic patient *"Sarah Jenkins, 34y, T1D Archetype"*), demographics, personal baseline sensitivity, and longitudinal records.
2. **`useTelemetryStream`**: Provides a simulated 5-minute sampling clock. In mock mode, every 2 seconds advances the synthetic timeline by one 5-minute increment, feeding `TrajectoryChart` and `MetricCard` components.
3. **`SimulationContext`**: Maintains slider parameter states (Activity, Sleep, Carbs, Insulin). When modified, a deterministic pharmacokinetic calculation immediately updates the simulated comparison curve.
4. **`AlertContext`**: Holds active and historical alerts, handles `acknowledgeAlert(id)` and `escalateAlert(id)` state mutations, and calculates unread counter badges.

---

## 6. Implementation Readiness & Safety Controls

1. **Synthetic Indicator**: The `SyntheticNotice` component is mounted globally in `AppLayout.jsx` and cannot be obscured or dismissed.
2. **Performance Optimization for Recharts**:
   - `isAnimationActive={false}` or short duration ($300\text{ms}$) on high-frequency streaming charts to eliminate render lag.
   - Downsampling: Historical data arrays are capped at 288 points ($24\text{ hours}$ at $5\text{-min}$ intervals) to preserve 60fps interaction.
3. **API Decoupling**: All screen views import methods from `src/services/apiClient.js`. If `VITE_USE_MOCK_DATA` is true (default), responses resolve immediately from `mockData.js`.
