# GlucoTwin — Figma UI/UX Design System & Specification

**Role**: Senior UI/UX Designer & Frontend Architect  
**Design Paradigm**: Modern Clinical SaaS Dashboard  
**Primary Aesthetic**: Pristine White Canvas, Dark Navy Typography, Medical Teal & Clinical Blue Accents, Clean Charts, Rounded Cards  
**Accessibility Target**: WCAG 2.1 AA Compliant (Minimum 4.5:1 text contrast ratio)  

---

## 1. Design System & Visual Tokens

### 1.1 Color Palette & Semantic Roles

| Token Name | Hex Code | Role & Usage |
| :--- | :--- | :--- |
| `--color-canvas` | `#F8FAFC` (Slate 50) | Main application background backdrop |
| `--color-surface` | `#FFFFFF` (Pure White) | Card containers, modal sheets, table rows |
| `--color-border` | `#E2E8F0` (Slate 200) | 1px clean borders, divider lines, card outlines |
| `--color-border-subtle` | `#F1F5F9` (Slate 100) | Inner gridlines, subtle separators |
| `--color-navy-900` | `#0F172A` (Navy Slate) | High-contrast page headers, primary metric values |
| `--color-navy-700` | `#334155` (Slate 700) | Body typography, card headings, active tabs |
| `--color-navy-500` | `#64748B` (Slate 500) | Secondary metadata, units (`mg/dL`), timestamps |
| `--color-teal-600` | `#0D9488` (Teal 600) | Primary brand accent, primary CTA buttons, active state |
| `--color-teal-500` | `#14B8A6` (Teal 500) | Secondary brand highlights, interactive hover states |
| `--color-blue-600` | `#2563EB` (Blue 600) | Historical continuous glucose (CGM) line, sensor streams |
| `--color-target-green` | `#10B981` (Emerald 500) | Target glucose zone ($70\text{--}180\text{ mg/dL}$), normal vitals |
| `--color-target-bg` | `rgba(16, 185, 129, 0.08)` | Shaded green reference zone on time-series charts |
| `--color-warning-amber`| `#F59E0B` (Amber 500) | Moderate risk ($31\text{--}60\%$), impending hypo/hyper, alerts |
| `--color-critical-rose` | `#EF4444` (Rose 500) | High risk ($61\text{--}100\%$), severe hypo ($<54$), acute alarms |
| `--color-twin-violet` | `#8B5CF6` (Violet 500) | Digital Twin future predictions, dashed curves, simulations |
| `--color-twin-cone` | `rgba(139, 92, 246, 0.12)` | 95% predictive uncertainty envelope band |

### 1.2 Typography Hierarchy (Font: Inter / System Sans)

| Style Name | Font Size | Weight | Line Height | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Display Metric** | 36px | Bold (700) | 44px | Large KPI values ($142\text{ mg/dL}$, $78\%$) |
| **Heading 1** | 24px | SemiBold (600) | 32px | Screen titles ("Overview Dashboard") |
| **Heading 2** | 18px | SemiBold (600) | 26px | Card titles ("Continuous Glucose Telemetry") |
| **Heading 3** | 15px | Medium (500) | 22px | Section labels, sub-card headers |
| **Body Regular** | 14px | Regular (400) | 20px | Standard clinical notes, descriptions, table cells |
| **Body Medium** | 14px | Medium (500) | 20px | Button labels, interactive tabs, form inputs |
| **Caption / Meta** | 12px | Regular (400) | 16px | Timestamps, sensor units, disclaimer text |
| **Badge Micro** | 11px | SemiBold (600) | 14px | Status pills ("TARGET ZONE", "HIGH RISK") |

### 1.3 Spacing, Radii & Shadows (8px Spatial Grid)

* **Base Unit**: `8px` (`4px` for tight padding, `8px`, `12px`, `16px`, `24px`, `32px`).
* **Corner Radii**:
  - Cards & Containers: `12px` (Smooth, modern, non-aggressive curves).
  - Buttons & Inputs: `8px`.
  - Badges & Status Pills: `9999px` (Full pill shape).
* **Elevation & Shadows**:
  - `Shadow-Sm` (Cards): `0 1px 3px 0 rgba(15, 23, 42, 0.05), 0 1px 2px -1px rgba(15, 23, 42, 0.05)`
  - `Shadow-Md` (Hover / Modals): `0 4px 6px -1px rgba(15, 23, 42, 0.08), 0 2px 4px -2px rgba(15, 23, 42, 0.04)`

---

## 2. Reusable Figma Component Specifications

### 1. `MetricCard` (KPI Tile)
* **Auto Layout**: Vertical, padding `16px`, gap `8px`, fixed height `132px`, corner radius `12px`.
* **Layers**:
  1. Top Row: Title (13px Slate 500) + Status Icon / Micro Badge.
  2. Middle Row: Value (32px Navy 900) + Unit (14px Slate 500).
  3. Bottom Row: Trend Arrow (Green $\uparrow$ or Amber $\downarrow$) + Delta Label ("$+12\text{ mg/dL}$ vs last hour").

### 2. `TrajectoryChartCard` (Main Recharts Frame)
* **Auto Layout**: Vertical, padding `20px`, gap `16px`, fill container, corner radius `12px`.
* **Layers**:
  1. Header: Chart Title + Interactive Range Tabs (`[2h]`, `[4h]`, `[8h]`, `[24h]`).
  2. Chart Canvas Area (Height `320px` Desktop):
     - Background grid: Light dashed horizontal lines (`#F1F5F9`).
     - Target Range Band: Shaded soft green area between $70$ and $180\text{ mg/dL}$.
     - Solid Line: Historical sensor stream in `#2563EB` ending at "NOW" vertical dashed line.
     - Dashed Line: Projected forward curve in `#8B5CF6` with shaded violet uncertainty cone.
  3. Legend Bar: Dot `#2563EB` (Historical), Dashed `#8B5CF6` (Predicted Twin), Green Fill (Target Zone $70\text{--}180$).

### 3. `SimulationControlGroup`
* **Auto Layout**: Vertical, padding `20px`, gap `16px`, corner radius `12px`.
* **Elements**:
  - Custom Range Sliders with active teal fill and circular drag thumbs.
  - Parameter labels with live value pills (e.g., `+20 min`, `45g`, `2.0 U`).
  - Action buttons: Primary Teal (`Run Simulation`), Outline (`Reset`).

### 4. `AlertListItem`
* **Auto Layout**: Horizontal, padding `14px 16px`, gap `12px`, border-left `4px solid` (Red, Amber, or Blue).
* **Elements**:
  - Severity Icon (AlertCircle / AlertTriangle / Info).
  - Content Block: Title (14px SemiBold) + Description (13px Slate) + Relative Timestamp ("12 min ago").
  - Action Buttons: `[Acknowledge]` (Ghost Teal) and `[Escalate]` (Ghost Slate).

---

## 3. Responsive Screen Layout Blueprints

### Desktop Frame (`1440 x 960px`)
```
+---------------------------------------------------------------------------------------------------------+
| [TopNav: 64px] Logo "GlucoTwin" | Patient Selector | Twin Sync Pill | Notice: "Synthetic Environment"  |
+---------------------------------------------------------------------------------------------------------+
| [Sidebar: 240px] | [Screen Content Workspace: Fill Container, Padding 24px]                             |
| • Overview       | +----------------------------------------------------------------------------------+ |
| • History        | | KPI 1: Current Glucose | KPI 2: 2h Predicted | KPI 3: Time in Range | KPI 4: IOB/COB | |
| • Monitoring     | +---------------------------------------------------+------------------------------+ |
| • Prediction/XAI | |                                                   |                              | |
| • What-If        | | Main Trajectory Chart (CGM + 2h Forecast)         | Digital Twin State & Quality | |
| • Alert Centre   | | (Solid Blue + Dashed Violet Cone)                 | (Model Sync, Sensor Drift)   | |
|                  | |                                                   |                              | |
|                  | +---------------------------------------------------+------------------------------+ |
|                  | | XAI Feature Drivers (SHAP Bars)                   | Active Alert Feed (Top 3)    | |
|                  | +----------------------------------------------------------------------------------+ |
+---------------------------------------------------------------------------------------------------------+
```

### Tablet Frame (`768 x 1024px`)
* Sidebar collapses into a compact left icon rail ($64\text{px}$) or top drawer.
* KPI Metric row wraps into $2 \times 2$ grid.
* Charts take $100\%$ width with twin status cards stacked beneath.

### Mobile Frame (`375 x 812px`)
* TopNav contains hamburger menu, logo, and unread alert counter.
* KPI cards render as a vertical stack or swipeable carousel.
* Recharts containers set to full-width with touch-friendly tooltips.

---

## 4. Production-Grade Figma AI Prompt

Copy and paste the exact prompt below into **Figma AI** or UI design generator plugins:

```text
Design a modern, high-fidelity healthcare SaaS web application dashboard called "GlucoTwin: Predictive Patient Digital Twin with Early Warning & Intelligent Clinical Alerts".

Frame Dimensions & Grid:
- Primary Frame: Desktop 1440x960px.
- Use 8px spatial grid, Auto Layout on all parent and child containers, with 12px rounded corner cards.

Design Style & Color Tokens:
- Background: Very clean, subtle cool white/slate (#F8FAFC).
- Cards & Surfaces: Pure White (#FFFFFF) with 1px subtle borders (#E2E8F0) and soft ambient shadows.
- Typography: Inter font. High-contrast dark navy (#0F172A) for titles and big numbers, slate (#334155) for body, muted slate (#64748B) for labels.
- Brand Accents: Medical Teal (#0D9488) for primary CTAs and active states; Clinical Blue (#2563EB) for sensor telemetry.
- Clinical Semantic Colors:
  * Safe / Target Range (70-180 mg/dL): Emerald Green (#10B981)
  * Moderate Risk / Impending Spike: Amber (#F59E0B)
  * Critical / High Risk: Rose Red (#EF4444)
  * Digital Twin Forecast & What-If Simulation: Royal Violet (#8B5CF6)
- Mandatory Notice: Clean, persistent top banner: "Synthetic Demonstration Environment — Not for Diagnostic Use".

Required Screens to Design:

1. Overview Dashboard (Clinical Command Center):
   - Left Navigation Sidebar (240px, Dark navy #0F172A or crisp white): Logo with teal pulse icon "GlucoTwin", 6 navigation items with icons: Overview, Patient History, Glucose Monitoring, Predictive Analytics & XAI, What-if Simulation, Alert Centre.
   - Top Header Bar: Patient switcher dropdown ("Sarah Jenkins, 34y, T1D Archetype"), Twin Status badge ("Twin Synced | 12ms"), Notification Bell (badge: 2), and Synthetic Notice banner.
   - Row 1: 4 KPI Cards:
     * Card 1: "Current Glucose" -> "142 mg/dL", trend vector slanted up, Target Zone badge.
     * Card 2: "2-Hour Predicted Spike" -> "198 mg/dL", Amber Risk badge "Moderate (58% Prob)".
     * Card 3: "Time in Range (Today)" -> "78%", target ">70%", green progress bar.
     * Card 4: "Active Metabolic Load" -> "IOB: 1.2 U | COB: 35g".
   - Row 2: Main Telemetry Card (65% width) showing Recharts-style line chart: past 4h in solid blue (#2563EB), green shaded target zone (70-180 mg/dL), vertical "NOW" marker, dashed violet curve (#8B5CF6) projecting 2h forward with a soft shaded confidence envelope. Alongside it, Digital Twin Status card (35% width) displaying metabolic parameters and wearable data quality (99.4%).
   - Row 3: XAI Feature Drivers preview and recent unacknowledged alerts.

2. Predictive Analytics & Explainable AI (XAI) Screen:
   - Header with 2-Hour Forward Spike Probability Gauge (0-30% Green Low, 31-60% Orange Moderate, 61-100% Red High).
   - High-resolution Prediction Cone chart with 95% confidence bounds.
   - "SHAP Feature Attribution Waterfall": Horizontal diverging bar chart showing factors driving the prediction: "Active Carbs +38 mg/dL" (orange bar), "Insulin on Board -24 mg/dL" (blue bar), "Resting HR Exertion +8 mg/dL" (orange bar).

3. What-If Simulation Sandbox Screen:
   - Left Column (Controls, 380px): Sliders for Activity (-30 to +60 min), Sleep (-2 to +2 hrs), Meal Carbs (0 to 100g), and Insulin dose adjustment (0 to 6 Units). Primary teal button "Run Twin Simulation" and "Reset" button.
   - Right Column (Comparison): Dual-curve overlay chart comparing "Baseline Forecast" (Grey) vs. "Simulated Twin Response" (Violet), with an outcome table showing predicted peak drop from 198 to 164 mg/dL.

4. Alert Centre Screen:
   - Filter chips: All (4), Critical (1), Warning (2), Info (1).
   - Card-based queue with severity edge strips:
     * Critical: "Predicted Hypoglycemia in ~35 min (<65 mg/dL)" with [Acknowledge] and [Escalate] buttons.
     * Warning: "Impending Postprandial Spike >200 mg/dL at 14:15".

Ensure generous whitespace, 16-20px internal card padding, legible labels, and modern healthcare elegance.
```

---

## 5. Design Safety & Synthetic Data Guardrails

* **Explicit Labeling**: Every chart containing future predictions must include a visual legend item labeled *"Projected Twin Trajectory (Simulated)"*.
* **No Fabricated Accuracies**: Do not add marketing badges like *"99.9% Clinically Validated"*. Instead, use realistic engineering indicators such as *"Data Quality: 99.4% Valid Packets"* or *"Calibration: Nominal"*.
* **Status Badges**: Use clear clinical boundary labels (*Target $70\text{--}180\text{ mg/dL}$*, *Hypo $<70\text{ mg/dL}$*, *Hyper $>180\text{ mg/dL}$*).
