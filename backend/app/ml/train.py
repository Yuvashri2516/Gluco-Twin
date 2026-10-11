"""
train.py - CLI Script to Train and Save the Glucose-Spike Prediction Model
==========================================================================
Usage:
    cd backend
    python -m app.ml.train
"""

import os
import sys
from datetime import datetime, timezone

from app.database import SessionLocal
from app.models import Patient, GlucoseReading, VitalReading
from app.ml.pipeline import (
    build_supervised_dataset,
    train_pipeline,
    save_model_artifact,
    FEATURE_NAMES,
    SPIKE_THRESHOLD_MG_DL,
    PREDICTION_HORIZON_MINUTES,
)

def run_training():
    print("=" * 70)
    print("GLUCOTWIN: Phase 3 Machine Learning Training Pipeline")
    print("=" * 70)
    print(f"Target: Binary Glucose Spike (>= {SPIKE_THRESHOLD_MG_DL} mg/dL)")
    print(f"Prediction Horizon: Next {PREDICTION_HORIZON_MINUTES} minutes (2 hours)")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")

    # 1. Fetch data from SQLite
    db = SessionLocal()
    try:
        print("\n[1/4] Loading patients and time-series readings from SQLite ...")
        patients_orm = db.query(Patient).all()
        patients = [
            {
                "id": p.id,
                "name": p.name,
                "age": p.age,
                "gender": p.gender,
                "diabetes_type": p.diabetes_type,
                "years_since_diagnosis": p.years_since_diagnosis,
            }
            for p in patients_orm
        ]

        glucose_by_patient = {}
        for r in db.query(GlucoseReading).filter(GlucoseReading.is_valid == True).order_by(GlucoseReading.timestamp.asc()).all():
            glucose_by_patient.setdefault(r.patient_id, []).append({
                "id": r.id,
                "timestamp": r.timestamp,
                "value": r.value,
            })

        vitals_by_patient = {}
        for r in db.query(VitalReading).order_by(VitalReading.timestamp.asc()).all():
            vitals_by_patient.setdefault(r.patient_id, []).append({
                "id": r.id,
                "timestamp": r.timestamp,
                "heart_rate": r.heart_rate,
                "hrv": r.hrv,
            })

        print(f"  Loaded {len(patients)} patients.")
        total_g = sum(len(v) for v in glucose_by_patient.values())
        total_v = sum(len(v) for v in vitals_by_patient.values())
        print(f"  Loaded {total_g} glucose readings and {total_v} vital readings.")

    finally:
        db.close()

    # 2. Build leak-free supervised dataset
    print("\n[2/4] Constructing leak-free training dataset ...")
    df = build_supervised_dataset(patients, glucose_by_patient, vitals_by_patient)
    print(f"  Constructed {len(df)} total eligible observations.")
    pos_count = int(df["label"].sum())
    neg_count = len(df) - pos_count
    print(f"  Class balance: {pos_count} positive ({pos_count/len(df):.1%}), {neg_count} negative.")

    # 3. Train pipeline
    print("\n[3/4] Fitting Logistic Regression with leak-free chronological split ...")
    pipeline, metadata = train_pipeline(df, test_ratio=0.28, purge_gap_steps=8, random_state=42)

    eval_m = metadata["evaluation_metrics"]
    data_s = metadata["data_summary"]
    print(f"  Train set: {data_s['train_samples']} samples (Positive: {data_s['train_positive_rate']:.1%})")
    print(f"  Test set:  {data_s['test_samples']} samples (Positive: {data_s['test_positive_rate']:.1%})")
    print(f"  Gap purged: {data_s['purged_gap_samples']} samples (buffer to prevent forward leakage)")

    print("\n--- EVALUATION METRICS (Chronological Holdout) ---")
    print(f"  Accuracy:  {eval_m['accuracy']:.4f}  (Baseline Majority: {eval_m['majority_baseline_accuracy']:.4f})")
    print(f"  Precision: {eval_m['precision']:.4f}")
    print(f"  Recall:    {eval_m['recall']:.4f}")
    print(f"  F1 Score:  {eval_m['f1_score']:.4f}  (Baseline Majority: {eval_m['majority_baseline_f1']:.4f})")
    print(f"  ROC-AUC:   {eval_m['roc_auc']:.4f}")
    cm = eval_m["confusion_matrix"]
    print(f"  Confusion Matrix: TN={cm['true_negative']}, FP={cm['false_positive']}, FN={cm['false_negative']}, TP={cm['true_positive']}")

    # 4. Save artifacts
    print("\n[4/4] Saving model artifact and metadata ...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    artifact_dir = os.path.join(base_dir, "artifacts")
    model_path, meta_path = save_model_artifact(pipeline, metadata, artifact_dir)
    print(f"  Model saved to:    {model_path}")
    print(f"  Metadata saved to: {meta_path}")

    print("\n[OK] Model training and serialization complete.")
    return metadata

if __name__ == "__main__":
    run_training()
