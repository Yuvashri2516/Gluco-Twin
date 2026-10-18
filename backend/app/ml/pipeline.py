"""
pipeline.py - ML Feature Engineering, Training, and Inference Pipeline
======================================================================
Implements a reproducible, honest ML pipeline for predicting glucose-spike
events (glucose >= 180 mg/dL) within a 2-hour forward horizon.

RESEARCH PROTOTYPE NOTICE:
  This module operates on synthetic data for academic research prototyping.
  It is NOT clinically validated and must not be used for medical decisions.
"""

import math
import os
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple, List

import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, accuracy_score
)

# ---------------------------------------------------------------------------
# Constants & Clinical / Prototype Parameters
# ---------------------------------------------------------------------------
MODEL_VERSION = "0.1.0-prototype"
SPIKE_THRESHOLD_MG_DL = 180.0     # Level 1 Hyperglycemia upper boundary (mg/dL)
PREDICTION_HORIZON_MINUTES = 120  # 2 hours forward horizon
OBSERVATION_WINDOW_MINUTES = 60   # 1 hour lookback window
MIN_READINGS_IN_WINDOW = 2        # Minimum readings required to compute slope/trend

FEATURE_NAMES = [
    "curr_glucose",
    "mean_glucose_1h",
    "std_glucose_1h",
    "slope_glucose_1h",
    "curr_hr",
    "curr_hrv",
    "mean_hr_1h",
    "mean_hrv_1h",
    "circadian_sin",
    "circadian_cos",
    "age",
    "years_diagnosis",
    "is_type1",
    "is_prediabetes",
]


def extract_features_at_timestamp(
    patient_info: Dict[str, Any],
    glucose_readings: List[Dict[str, Any]],
    vital_readings: List[Dict[str, Any]],
    prediction_time: datetime,
) -> Tuple[Optional[Dict[str, float]], List[str]]:
    """
    Extract historical features strictly at or before `prediction_time`.
    Zero future readings are accessed, guaranteeing no target leakage.

    Returns:
        (features_dict, warnings_list)
        If insufficient historical data exists, features_dict is None.
    """
    warnings: List[str] = []

    # 1. Filter readings strictly <= prediction_time
    # Ensure timezone normalization
    def parse_ts(ts):
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts

    p_time = parse_ts(prediction_time)

    hist_glucose = [
        r for r in glucose_readings
        if parse_ts(r["timestamp"]) <= p_time
    ]
    hist_vitals = [
        r for r in vital_readings
        if parse_ts(r["timestamp"]) <= p_time
    ]

    if not hist_glucose:
        warnings.append("No historical glucose readings available at prediction timestamp.")
        return None, warnings

    # Sort chronologically
    hist_glucose.sort(key=lambda r: parse_ts(r["timestamp"]))
    hist_vitals.sort(key=lambda r: parse_ts(r["timestamp"]))

    latest_glucose = hist_glucose[-1]
    latest_g_time = parse_ts(latest_glucose["timestamp"])

    # Check latency of latest reading
    time_since_last_g = (p_time - latest_g_time).total_seconds() / 60.0
    if time_since_last_g > 30.0:
        warnings.append(f"Latest glucose reading is {time_since_last_g:.0f} minutes old (> 30 min).")

    # Readings in lookback window [prediction_time - 60 min, prediction_time]
    window_start = p_time - timedelta(minutes=OBSERVATION_WINDOW_MINUTES)
    window_glucose = [
        r for r in hist_glucose
        if parse_ts(r["timestamp"]) >= window_start
    ]

    if len(window_glucose) < MIN_READINGS_IN_WINDOW:
        warnings.append(
            f"Insufficient readings in 1-hour lookback window "
            f"({len(window_glucose)} found, minimum {MIN_READINGS_IN_WINDOW} required)."
        )
        return None, warnings

    # Compute glucose statistics
    g_values = [float(r["value"]) for r in window_glucose]
    curr_glucose = float(latest_glucose["value"])
    mean_glucose_1h = float(np.mean(g_values))
    std_glucose_1h = float(np.std(g_values, ddof=1)) if len(g_values) > 1 else 0.0

    # Rate of change: slope across lookback window (mg/dL per minute)
    oldest_in_window = window_glucose[0]
    dt_minutes = (latest_g_time - parse_ts(oldest_in_window["timestamp"])).total_seconds() / 60.0
    if dt_minutes >= 10.0:
        slope_glucose_1h = float((curr_glucose - float(oldest_in_window["value"])) / dt_minutes)
    else:
        slope_glucose_1h = 0.0

    # Vitals processing
    window_vitals = [
        r for r in hist_vitals
        if parse_ts(r["timestamp"]) >= window_start
    ]
    if window_vitals:
        latest_vital = window_vitals[-1]
        curr_hr = float(latest_vital["heart_rate"]) if latest_vital.get("heart_rate") is not None else 72.0
        curr_hrv = float(latest_vital["hrv"]) if latest_vital.get("hrv") is not None else 50.0

        hr_vals = [float(r["heart_rate"]) for r in window_vitals if r.get("heart_rate") is not None]
        hrv_vals = [float(r["hrv"]) for r in window_vitals if r.get("hrv") is not None]
        mean_hr_1h = float(np.mean(hr_vals)) if hr_vals else curr_hr
        mean_hrv_1h = float(np.mean(hrv_vals)) if hrv_vals else curr_hrv
    else:
        # Default cohort imputation if vital telemetry is absent
        warnings.append("No concurrent vitals in lookback window; defaulted to cohort baseline (HR: 72 bpm, HRV: 50 ms).")
        curr_hr = 72.0
        curr_hrv = 50.0
        mean_hr_1h = 72.0
        mean_hrv_1h = 50.0

    # Circadian features
    hour_decimal = p_time.hour + p_time.minute / 60.0
    circadian_sin = float(np.sin(2.0 * np.pi * hour_decimal / 24.0))
    circadian_cos = float(np.cos(2.0 * np.pi * hour_decimal / 24.0))

    # Patient demographics
    age = float(patient_info.get("age", 45))
    years_diag = float(patient_info.get("years_since_diagnosis", 5))
    diabetes_type = str(patient_info.get("diabetes_type", "Type 2"))
    is_type1 = 1.0 if diabetes_type == "Type 1" else 0.0
    is_prediabetes = 1.0 if diabetes_type == "Pre-diabetic" else 0.0

    features = {
        "curr_glucose": round(curr_glucose, 2),
        "mean_glucose_1h": round(mean_glucose_1h, 2),
        "std_glucose_1h": round(std_glucose_1h, 2),
        "slope_glucose_1h": round(slope_glucose_1h, 4),
        "curr_hr": round(curr_hr, 1),
        "curr_hrv": round(curr_hrv, 1),
        "mean_hr_1h": round(mean_hr_1h, 1),
        "mean_hrv_1h": round(mean_hrv_1h, 1),
        "circadian_sin": round(circadian_sin, 4),
        "circadian_cos": round(circadian_cos, 4),
        "age": age,
        "years_diagnosis": years_diag,
        "is_type1": is_type1,
        "is_prediabetes": is_prediabetes,
    }

    return features, warnings


def build_supervised_dataset(
    patients: List[Dict[str, Any]],
    glucose_by_patient: Dict[int, List[Dict[str, Any]]],
    vitals_by_patient: Dict[int, List[Dict[str, Any]]],
    spike_threshold: float = SPIKE_THRESHOLD_MG_DL,
    horizon_minutes: int = PREDICTION_HORIZON_MINUTES,
) -> pd.DataFrame:
    """
    Construct leak-free training dataset:
      - Features calculated strictly from t <= T.
      - Label y = 1 if ANY glucose in (T, T + horizon] >= spike_threshold, else 0.
      - Samples lacking full future horizon coverage are strictly dropped.
    """
    rows = []

    def parse_ts(ts):
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts

    for p in patients:
        pid = p["id"]
        g_list = sorted(glucose_by_patient.get(pid, []), key=lambda r: parse_ts(r["timestamp"]))
        v_list = sorted(vitals_by_patient.get(pid, []), key=lambda r: parse_ts(r["timestamp"]))

        if len(g_list) < 10:
            continue

        for i, reading in enumerate(g_list):
            t = parse_ts(reading["timestamp"])
            horizon_end = t + timedelta(minutes=horizon_minutes)

            # Check future readings within (t, horizon_end]
            future_readings = [
                r for r in g_list[i + 1:]
                if t < parse_ts(r["timestamp"]) <= horizon_end
            ]

            # Require full future horizon coverage (must span at least horizon_minutes - 1.0 min)
            if not future_readings:
                continue
            future_span = (parse_ts(future_readings[-1]["timestamp"]) - t).total_seconds() / 60.0
            if future_span < (horizon_minutes - 1.0):
                # Sample near end of patient recording; lacking full 2h coverage cannot confirm absence of spike
                continue

            # Extract features strictly at t
            feat, _ = extract_features_at_timestamp(p, g_list[:i + 1], v_list, t)
            if feat is None:
                continue

            # Label construction: positive if any reading exceeds threshold
            has_spike = any(float(r["value"]) >= spike_threshold for r in future_readings)
            label = 1 if has_spike else 0

            row = dict(feat)
            row["patient_id"] = pid
            row["timestamp"] = t
            row["step_idx"] = i
            row["label"] = label
            rows.append(row)

    return pd.DataFrame(rows)


def train_pipeline(
    df: pd.DataFrame,
    test_ratio: float = 0.28,
    purge_gap_steps: int = 8,
    random_state: int = 42,
) -> Tuple[Pipeline, Dict[str, Any]]:
    """
    Train leak-free LogisticRegression pipeline with chronological split.
    Purges `purge_gap_steps` (2 hours) between train and test to prevent
    overlapping forward label leakage.
    """
    # Order by step index chronologically
    df_sorted = df.sort_values(["step_idx", "timestamp"]).reset_index(drop=True)
    max_step = df_sorted["step_idx"].max()
    min_step = df_sorted["step_idx"].min()
    total_steps = max_step - min_step + 1

    train_step_cutoff = min_step + int(total_steps * (1.0 - test_ratio))
    test_step_start = train_step_cutoff + purge_gap_steps

    train_mask = df_sorted["step_idx"] < train_step_cutoff
    test_mask = df_sorted["step_idx"] >= test_step_start

    df_train = df_sorted[train_mask]
    df_test = df_sorted[test_mask]

    X_train = df_train[FEATURE_NAMES]
    y_train = df_train["label"]
    X_test = df_test[FEATURE_NAMES]
    y_test = df_test["label"]

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(penalty="l2", C=1.0, random_state=random_state, max_iter=1000))
    ])

    pipeline.fit(X_train, y_train)

    # Evaluate
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    cm = confusion_matrix(y_test, y_pred).tolist()
    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_prob)) if len(np.unique(y_test)) > 1 else None

    # Baseline comparison (Majority class baseline)
    maj_class = int(y_train.mode()[0])
    y_pred_maj = np.full_like(y_test, maj_class)
    maj_f1 = float(f1_score(y_test, y_pred_maj, zero_division=0))
    maj_acc = float(accuracy_score(y_test, y_pred_maj))

    # Feature weights (coefficients in standardized space)
    scaler: StandardScaler = pipeline.named_steps["scaler"]
    logreg: LogisticRegression = pipeline.named_steps["model"]
    coefficients = {
        name: float(coef)
        for name, coef in zip(FEATURE_NAMES, logreg.coef_[0])
    }

    metadata = {
        "model_version": MODEL_VERSION,
        "model_type": "StandardScaler + LogisticRegression (L2, C=1.0)",
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "random_state": random_state,
        "spike_threshold_mg_dl": SPIKE_THRESHOLD_MG_DL,
        "prediction_horizon_minutes": PREDICTION_HORIZON_MINUTES,
        "observation_window_minutes": OBSERVATION_WINDOW_MINUTES,
        "features": FEATURE_NAMES,
        "feature_coefficients": coefficients,
        "feature_means": {name: float(mean) for name, mean in zip(FEATURE_NAMES, scaler.mean_)},
        "feature_scales": {name: float(scale) for name, scale in zip(FEATURE_NAMES, scaler.scale_)},
        "intercept": float(logreg.intercept_[0]),
        "data_summary": {
            "total_usable_samples": len(df),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "purged_gap_samples": len(df) - len(X_train) - len(X_test),
            "train_positive_rate": float(y_train.mean()),
            "test_positive_rate": float(y_test.mean()),
        },
        "evaluation_metrics": {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc_auc, 4) if roc_auc is not None else None,
            "confusion_matrix": {
                "true_negative": cm[0][0],
                "false_positive": cm[0][1],
                "false_negative": cm[1][0],
                "true_positive": cm[1][1],
            },
            "majority_baseline_f1": round(maj_f1, 4),
            "majority_baseline_accuracy": round(maj_acc, 4),
        },
        "limitations": [
            "Dataset is purely synthetic (5 synthetic patients generated via seed.py).",
            "Vital signs in synthetic generator share circadian oscillation but lack physiological coupling to acute meal spikes.",
            "Cross-patient generalization is confounded by small sample size (only 1 Type 1, 1 Pre-diabetic).",
            "This prototype is an academic software demonstration and not a clinical diagnostic device."
        ]
    }

    return pipeline, metadata


def save_model_artifact(pipeline: Pipeline, metadata: Dict[str, Any], artifact_dir: str) -> Tuple[str, str]:
    """Save model pipeline and accompanying metadata JSON."""
    os.makedirs(artifact_dir, exist_ok=True)
    model_path = os.path.join(artifact_dir, "glucose_spike_model.joblib")
    meta_path = os.path.join(artifact_dir, "model_metadata.json")

    joblib.dump(pipeline, model_path)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return model_path, meta_path


def load_model_artifact(artifact_dir: str) -> Tuple[Optional[Pipeline], Optional[Dict[str, Any]]]:
    """Load model pipeline and metadata from relative or absolute directory."""
    model_path = os.path.join(artifact_dir, "glucose_spike_model.joblib")
    meta_path = os.path.join(artifact_dir, "model_metadata.json")

    if not os.path.exists(model_path) or not os.path.exists(meta_path):
        return None, None

    pipeline = joblib.load(model_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    return pipeline, metadata
