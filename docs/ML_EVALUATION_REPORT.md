# GlucoTwin — Phase 2: Machine Learning Audit, Evaluation & Reliability Report

**Document Version:** 1.0.0  
**Audit Date:** October 18, 2026  
**Repository:** `Yuvashri2516/Gluco-Twin`  
**Evaluation Scope:** Binary Glucose-Spike Forecaster ($y \in \{0, 1\}$, Horizon: 120 minutes, Threshold: $\ge 180\text{ mg/dL}$)  
**Model Architecture:** `StandardScaler` + `LogisticRegression(penalty='l2', C=1.0)`  
**Safety Classification:** Academic & Hackathon Research Demonstration Prototype — Synthetic Data Only  

---

## 1. Executive Summary

This report delivers a rigorous, evidence-based audit of the machine-learning pipeline powering GlucoTwin's experimental 2-hour glucose-spike early warning system. 

### Key Audit Conclusions:
1. **Target Construction Audit & Defect Resolution:** Previously, samples lacking the final 15 minutes of the 120-minute forward evaluation horizon (spanning only 105 minutes / 7 readings) were permitted into the dataset and silently assumed negative ($y=0$) if no spike occurred. This introduced false-negative label noise. The target generator has been corrected to mandate full 120-minute forward coverage ($t \in (T, T+120\text{ min}]$), eliminating 10 unconfirmed negative samples.
2. **Leakage Audit: ZERO Data Leakage:** All 14 engineered features are strictly extracted from historical telemetry at or before prediction time ($t \le T$, 1-hour lookback). `StandardScaler` is fitted exclusively on training sets. A mandatory 8-step (120-minute) purge gap separates chronological train and test splits, preventing forward-label overlap.
3. **Performance Against Baselines:**
   - On the chronological holdout test set (1,055 samples), the trained Logistic Regression model achieves an **F1 score of 0.4313** and **Recall of 42.67%** with **ROC-AUC of 0.6520** and **Brier Score of 0.2005**.
   - In contrast, the Majority-Class baseline achieves an F1 of **0.0000** (detects 0 spikes).
   - The strict clinical persistence baseline (`curr_glucose >= 180`) achieves a Recall of only **8.00%** (F1 = 0.1370), proving that the multi-vital ML model adds significant value by anticipating upcoming spikes *before* thresholds are crossed.
4. **Generalization Barrier (Inter-Patient Transfer):**
   - In Leave-One-Patient-Out (LOPO) cross-validation across the 5 synthetic patient cohorts, mean ROC-AUC drops to **~0.48–0.56** (near random chance).
   - The model learns intra-cohort temporal dynamics well, but cannot generalize to unseen individuals because demographic features (`is_type1`, `is_prediabetes`, `age`) act as confounding proxies for the small 5-patient cohort.
5. **Model Artifact Policy:** The existing production model artifact (`glucose_spike_model.joblib`) remains intact and verified. The frontend disclaimer (*"Uncalibrated Model Score. Not a clinically validated probability"*) and linear log-odds feature attributions are mathematically sound.

---

## 2. Existing Model Architecture

The current production forecaster implements an interpretable, linear pipeline:

```
Raw Telemetry (t <= T)
   │  - CGM readings (mg/dL)
   │  - Synchronized HR (bpm) & HRV (ms)
   │  - Patient Demographics & Circadian Phase
   ▼
Feature Extraction (1-Hour Lookback Window [T - 60 min, T])
   │  - 14 engineered numerical features
   ▼
StandardScaler()
   │  - Centering & scaling fitted strictly on training data
   ▼
LogisticRegression(penalty='l2', C=1.0, solver='lbfgs', random_state=42)
   │  - Outputs uncalibrated probability score: p = 1 / (1 + exp(-z))
   ▼
Threshold Decision (Default: p >= 0.50 -> Spike Forecasted)
```

- **Inference Runtime:** In-memory execution within FastAPI endpoint `POST /api/predictions/glucose-spike`.
- **Artifact Files:**
  - Weights & pipeline: [`backend/app/ml/artifacts/glucose_spike_model.joblib`](file:///d:/Projects/Gluco-Twin/backend/app/ml/artifacts/glucose_spike_model.joblib)
  - Provenance & metadata: [`backend/app/ml/artifacts/model_metadata.json`](file:///d:/Projects/Gluco-Twin/backend/app/ml/artifacts/model_metadata.json)

---

## 3. Target Definition

The clinical prediction objective is binary classification:

$$y_T = \begin{cases} 1 & \text{if } \exists t \in (T, T + 120\text{ min}] \text{ such that } G(t) \ge 180.0\text{ mg/dL} \\ 0 & \text{otherwise} \end{cases}$$

### Target Audit Specifications:
- **Threshold:** Exactly $180.0\text{ mg/dL}$ (Level 1 Hyperglycemia boundary according to American Diabetes Association / International Consensus guidelines).
- **Forward Horizon:** Next $120\text{ minutes}$ (2 hours).
- **Sampling Cadence:** 15-minute sensor intervals ($8\text{ readings}$ inside the forward window: $+15, +30, +45, +60, +75, +90, +105, +120\text{ min}$).
- **Exclusion Rule:** Current reading $G(T)$ is strictly excluded from target construction ($t > T$).

---

## 4. Dataset Description

The active dataset is generated deterministically via [`seed.py`](file:///d:/Projects/Gluco-Twin/backend/app/seed.py) with 15-minute continuous glucose and autonomic vital readings:

| Patient ID | Name | Diabetes Subtype | Age | Gender | Years Dx | Total Readings | Spike Rate (2h) |
|---|---|---|---|---|---|---|---|
| **1** | Ananya Sharma | Type 2 Diabetes | 52 | Female | 8 yrs | 789 CGM, 789 Vitals | 47.09% |
| **2** | Rajesh Kumar | Type 2 Diabetes | 45 | Male | 5 yrs | 789 CGM, 789 Vitals | 47.09% |
| **3** | Priya Patel | Type 1 Diabetes | 34 | Female | 12 yrs | 789 CGM, 789 Vitals | 51.23% |
| **4** | Vikram Singh | Type 2 Diabetes | 61 | Male | 15 yrs | 789 CGM, 789 Vitals | 48.64% |
| **5** | Meera Reddy | Pre-diabetic | 28 | Female | 1 yr | 789 CGM, 789 Vitals | 0.00% |

- **Total Synchronized Telemetry Points:** 3,945 glucose readings, 3,945 vital readings.
- **Total Eligible Supervised Samples:** 3,865 samples (after discarding end-of-series boundary points).
- **Overall Class Balance:** 1,500 Positive (38.81%), 2,365 Negative (61.19%).

---

## 5. Synthetic-Data Limitations

1. **Cohort Diversity Deficiency:** With only 5 synthetic profiles (1 Type 1, 1 Pre-diabetic, 3 Type 2), patient subtype indicators are collinear with individual patient IDs.
2. **Simplified Autonomic Coupling:** In real physiology, HRV suppression and acute tachycardia correlate with catecholamine release and acute mental/physical stress. In the synthetic generator, vitals follow diurnal sinusoidal rhythms with Gaussian noise rather than non-linear meal-absorption dynamics.
3. **No Clinical Generalization:** High performance within the synthetic time series reflects pattern recognition of synthetic harmonic equations, not true human metabolic pharmacokinetics.

---

## 6. Feature Definitions

Every sample at index $T$ accesses exclusively $t \le T$:

| # | Feature Key | Source | Lookback Window | Mathematical Definition | Clinical / Physiological Rational |
|---|---|---|---|---|---|
| 1 | `curr_glucose` | CGM | $t = T$ | $G(T)$ | Immediate glycemic level |
| 2 | `mean_glucose_1h` | CGM | $[T-60\text{m}, T]$ | $\frac{1}{K}\sum G(t)$ | Rolling 1-hour central tendency |
| 3 | `std_glucose_1h` | CGM | $[T-60\text{m}, T]$ | $\sqrt{\frac{\sum (G(t) - \bar{G})^2}{K-1}}$ | Glycemic variability and instability |
| 4 | `slope_glucose_1h` | CGM | $[T-60\text{m}, T]$ | $\frac{G(T) - G(T-60)}{\Delta t}$ | Glucose velocity / trajectory (mg/dL/min) |
| 5 | `curr_hr` | Wearable | $t = T$ | $HR(T)$ | Current heart rate (bpm) |
| 6 | `curr_hrv` | Wearable | $t = T$ | $HRV(T)$ | Autonomic vagal tone (ms) |
| 7 | `mean_hr_1h` | Wearable | $[T-60\text{m}, T]$ | $\frac{1}{M}\sum HR(t)$ | Baseline resting cardiovascular load |
| 8 | `mean_hrv_1h` | Wearable | $[T-60\text{m}, T]$ | $\frac{1}{M}\sum HRV(t)$ | Baseline autonomic parasympathetic state |
| 9 | `circadian_sin` | Clock | $T$ | $\sin(2\pi \cdot \text{hour} / 24)$ | Circadian diurnal phase cycle |
| 10 | `circadian_cos` | Clock | $T$ | $\cos(2\pi \cdot \text{hour} / 24)$ | Circadian orthogonal phase cycle |
| 11 | `age` | EHR | Static | Patient age in years | Age-related insulin resistance |
| 12 | `years_diagnosis` | EHR | Static | Years since initial diagnosis | Beta-cell depletion vintage |
| 13 | `is_type1` | EHR | Static | $\mathbb{I}(\text{Type 1})$ | Complete endogenous insulin deficiency |
| 14 | `is_prediabetes` | EHR | Static | $\mathbb{I}(\text{Pre-diabetic})$ | Preserved glycemic regulation flag |

---

## 7. Leakage Audit Findings

| Potential Leakage Vector | Audit Finding | Verdict |
|---|---|---|
| **Future Lookahead in Features** | Code inspection confirmed `[r for r in hist if parse_ts(r['timestamp']) <= p_time]`. Zero readings with $t > T$ are touched. | 🟢 **PASS** |
| **StandardScaler Contamination** | `StandardScaler` is fitted inside `pipeline.fit(X_train, y_train)` strictly on training folds. Test folds are only transformed via `.transform()`. | 🟢 **PASS** |
| **Target Label Overlap across Split** | Evaluated split logic. An 8-step ($120\text{ min}$) purge gap is enforced between `train_cutoff` and `test_start`. | 🟢 **PASS** |
| **Target-Derived Data in Features** | Target column `label` is instantiated separately after feature dictionary generation. | 🟢 **PASS** |

---

## 8. Target-Label Audit Findings & Fix

### Investigation of 105-Minute Coverage Issue:
- **Prior Code:** In [`pipeline.py:234`](file:///d:/Projects/Gluco-Twin/backend/app/ml/pipeline.py), the check was:
  ```python
  if future_span < (horizon_minutes - 15.0): # i.e. < 105.0 min
      continue
  ```
- **Observed Empirical Behavior:**
  - Exactly 10 samples (2 per patient) near the end of the recording had `future_span == 105.0 min` (7 readings: $+15, \dots, +105$).
  - 1 sample experienced a spike within 105 minutes (true positive).
  - 9 samples experienced no spike within 105 minutes, but the final 15 minutes of the 120-minute horizon ($t \in (105, 120]$) were never observed.
  - Prior logic labeled all 9 samples as $y=0$ (negative).
- **Correction Applied:**
  - Updated the boundary condition in [`pipeline.py`](file:///d:/Projects/Gluco-Twin/backend/app/ml/pipeline.py) to mandate full 120-minute forward coverage:
    ```python
    if future_span < (horizon_minutes - 1.0): # requires >= 119.0 min
        continue
    ```
  - Result: The 10 censored boundary points are excluded.
  - Regression Test Added: [`test_105_minute_partial_horizon_without_spike_is_excluded()`](file:///d:/Projects/Gluco-Twin/backend/tests/test_label_construction.py#L98-L140) verifies that unobserved partial horizons are never assumed negative.

---

## 9. Train/Test Methodology

1. **Chronological Holdout (Primary Evaluation):**
   - Samples sorted by timeline step index ($T$).
   - Train Split: Earlier 72% of timeline ($N=2,770$ samples, Positive rate: 39.82%).
   - Purge Buffer: 8 steps ($120\text{ min}$, $N=40$ samples dropped to prevent split-boundary leakage).
   - Test Split: Final 28% of timeline ($N=1,055$ samples, Positive rate: 35.55%).
2. **Leave-One-Patient-Out (LOPO) Cross-Validation (Secondary Generalization Test):**
   - Iterates through all 5 patients. In fold $k$, model trains on 4 patients and tests on the held-out patient.

---

## 10. Baseline Comparison Table (Chronological Holdout)

The table below reports real measured metrics on the identical 1,055 test samples:

| Model / Baseline | Description | Accuracy | Precision | Recall | F1-Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|---|
| **Majority-Class Baseline** | Predicts $y=0$ for all samples (no spikes ever) | **0.6445** | 0.0000 | 0.0000 | 0.0000 | N/A | 0.2309 |
| **Strict Persistence Rule** | Predicts spike if current glucose $G(T) \ge 180.0\text{ mg/dL}$ | 0.6417 | **0.4762** | 0.0800 | 0.1370 | N/A | 0.2509 |
| **Clinical Threshold Baseline** | Predicts spike if current glucose $G(T) \ge 150.0\text{ mg/dL}$ | 0.6256 | 0.4609 | 0.3147 | 0.3740 | N/A | N/A |
| **GlucoTwin Logistic Regression** | Multi-vital 14-feature standardized linear model | 0.6000 | 0.4360 | **0.4267** | **0.4313** | **0.6520** | **0.2005** |

### Analysis:
- **The "Accuracy Paradox":** The Majority-Class baseline achieves higher accuracy (64.45%) than the ML model (60.00%) solely due to class imbalance (64.45% of test samples are negative). However, it detects 0 spikes ($\text{Recall} = 0\%$).
- **Early Warning Superiority:** The strict persistence rule only detects spikes that have *already occurred* at $T$, yielding an unacceptable Recall of 8.00%.
- **Logistic Regression Value-Add:** The trained model achieves **Recall = 42.67%** and **F1 = 0.4313**, catching more than 5 times as many upcoming spikes as persistence while lowering the probabilistic Brier error from 0.2309 to 0.2005.

---

## 11. Confusion Matrix (Chronological Test Set)

```
                       Actual Negative (y=0)    Actual Positive (y=1)
Predicted No Spike              473                      215
Predicted Spike (y=1)           207                      160
```
- **True Negatives (TN):** 473
- **False Positives (FP):** 207 (false alarms)
- **False Negatives (FN):** 215 (missed spikes)
- **True Positives (TP):** 160 (successfully anticipated spikes)

---

## 12. Patient-Grouped (LOPO) Generalization Results

| Held-Out Patient | Diabetes Subtype | Evaluation Samples | Positive Rate | Accuracy | Precision | Recall | F1-Score | ROC-AUC |
|---|---|---|---|---|---|---|---|---|
| **Ananya Sharma** | Type 2 | 773 | 47.09% | 0.4631 | 0.4371 | 0.4011 | 0.4180 | **0.4856** |
| **Rajesh Kumar** | Type 2 | 773 | 47.09% | 0.5175 | 0.4839 | 0.1648 | 0.2434 | **0.5145** |
| **Priya Patel** | Type 1 | 773 | 51.23% | 0.4877 | 0.1667 | 0.0051 | 0.0100 | **0.5633** |
| **Vikram Singh** | Type 2 | 773 | 48.64% | 0.4877 | 0.4628 | 0.2686 | 0.3400 | **0.4767** |
| **Meera Reddy** | Pre-diabetic | 773 | 0.00% | 1.0000 | 0.0000 | 0.0000 | 0.0000 | *Undefined (1 class)* |

> [!CRITICAL]
> **Inter-Patient Transfer Failure:**
> In every cross-patient fold, ROC-AUC ranges between **0.48 and 0.56** (statistically indistinguishable from random coin-flipping). Because Priya Patel is the *only* Type 1 patient and Meera Reddy is the *only* Pre-diabetic in the dataset, the model cannot learn transferable physiological phenotypes across different patient cohorts.

---

## 13. Prediction-Score Interpretation & Calibration

- **Mathematical Identity:** The endpoint returns:
  $$\hat{p} = \sigma\left(w_0 + \sum_{j=1}^{14} w_j \frac{x_j - \mu_j}{\sigma_j}\right) = \frac{1}{1 + e^{-z}}$$
- **Uncalibrated Status:** This score represents the uncalibrated sigmoid posterior probability under an $L_2$-regularized logistic loss on synthetic data.
- **Brier Score:** 0.2005 (better than random/majority, but reflecting modest calibration).
- **Clinical Policy:** The score **MUST NEVER** be presented as an absolute clinical risk (e.g., *"Patient has a 72% probability of medical emergency"*). The UI correctly identifies this as:
  > **"Uncalibrated Model Score. Not a clinically validated probability."**

---

## 14. Feature-Contribution Methodology (XAI Audit)

The prediction API calculates linear attribution as:
$$\phi_j = w_j \cdot z_j = w_j \cdot \left(\frac{x_j - \mu_j}{\sigma_j}\right)$$

### Audit Findings on Contributions:
1. **Mathematical Validity:** Because the log-odds logit is strictly linear in standardized space ($z = w_0 + \sum \phi_j$), each $\phi_j$ represents the exact contribution of feature $j$ to the log-odds of a spike.
2. **Directionality:**
   - $\phi_j > 0$: Increases predicted log-odds (risk driver).
   - $\phi_j < 0$: Decreases predicted log-odds (protective factor).
3. **Frontend Visual Alignment:** [`PredictionsPanel.jsx`](file:///d:/Projects/Gluco-Twin/frontend/src/components/PredictionsPanel.jsx) properly splits $\phi_j > 0$ into **Risk Factors** (red bars) and $\phi_j < 0$ into **Protective Factors** (blue/green bars), ensuring the user interface reflects the fitted weights.

---

## 15. Reproduction Commands

To independently reproduce all data generation, metrics, and regression tests:

```bash
# 1. Run all 36 backend automated tests (including label construction & leakage tests)
cd backend
python -m pytest tests/ -v

# 2. Run the standalone reproducible ML audit script
python -c "from app.ml.pipeline import *; print('Pipeline module verified.')"
python ..\scratch\evaluate_ml.py

# 3. Verify frontend build & linting
cd ../frontend
npm run lint
npm run build
```

---

## 16. Final Recommendation

1. **Preserve the Existing Production Model:** The serialized model artifact (`glucose_spike_model.joblib`) was trained under the verified chronological split and serves its intended research demonstration purpose.
2. **Retain All Disclaimers:** Keep the prominent disclaimers regarding uncalibrated scores and synthetic data in both the UI and documentation.
3. **Future Modeling Roadmap (Post-Hackathon):**
   - Ingest larger multi-patient real datasets (e.g. OhioT1DM or D1NAMO).
   - Transition from linear models to Sequence-to-Sequence Recurrent Neural Networks (LSTM/GRU) or Transformer-based Temporal Fusion Transformers to capture non-linear metabolic lag times.
