"""
reproduce_ml_metrics.py - Recomputes and validates exact ML metrics from the serialized model artifact
"""
import sys
import json
import numpy as np
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score, accuracy_score, brier_score_loss, confusion_matrix

sys.path.insert(0, "backend")

from app.database import SessionLocal
from app.models import Patient, GlucoseReading, VitalReading
from app.ml.pipeline import (
    build_supervised_dataset,
    load_model_artifact,
    FEATURE_NAMES,
)

# 1. Fetch data
db = SessionLocal()
patients_orm = db.query(Patient).all()
patients = [{"id": p.id, "name": p.name, "age": p.age, "gender": p.gender, "diabetes_type": p.diabetes_type, "years_since_diagnosis": p.years_since_diagnosis} for p in patients_orm]

glucose_by_patient = {}
for r in db.query(GlucoseReading).filter(GlucoseReading.is_valid == True).order_by(GlucoseReading.timestamp.asc()).all():
    glucose_by_patient.setdefault(r.patient_id, []).append({"id": r.id, "timestamp": r.timestamp, "value": r.value})

vitals_by_patient = {}
for r in db.query(VitalReading).order_by(VitalReading.timestamp.asc()).all():
    vitals_by_patient.setdefault(r.patient_id, []).append({"id": r.id, "timestamp": r.timestamp, "heart_rate": r.heart_rate, "hrv": r.hrv})
db.close()

df = build_supervised_dataset(patients, glucose_by_patient, vitals_by_patient)
print(f"Total usable dataset rows: {len(df)}")

# Load model artifact
pipeline, metadata = load_model_artifact("backend/app/ml/artifacts")
print(f"Model version: {metadata['model_version']}")
print(f"Features in model: {len(metadata['features'])}")

# Chronological split matching train.py
test_ratio = 0.28
purge_gap_steps = 8
n_total = len(df)
n_test = int(n_total * test_ratio)
n_train = n_total - n_test - purge_gap_steps

train_df = df.iloc[:n_train]
test_df = df.iloc[-n_test:]

X_test = test_df[FEATURE_NAMES]
y_test = test_df["label"].astype(int)

y_pred = pipeline.predict(X_test)
y_prob = pipeline.predict_proba(X_test)[:, 1]

acc = accuracy_score(y_test, y_pred)
prec = precision_score(y_test, y_pred, zero_division=0)
rec = recall_score(y_test, y_pred, zero_division=0)
f1 = f1_score(y_test, y_pred, zero_division=0)
roc = roc_auc_score(y_test, y_prob)
brier = brier_score_loss(y_test, y_prob)
cm = confusion_matrix(y_test, y_pred)

print("\n--- CHRONOLOGICAL HOLDOUT REPRODUCED METRICS ---")
print(f"Test samples: {len(y_test)} (Positive rate: {y_test.mean():.1%})")
print(f"Accuracy:    {acc:.4f} (Saved metadata: {metadata['evaluation_metrics']['accuracy']})")
print(f"Precision:   {prec:.4f} (Saved metadata: {metadata['evaluation_metrics']['precision']})")
print(f"Recall:      {rec:.4f} (Saved metadata: {metadata['evaluation_metrics']['recall']})")
print(f"F1-Score:    {f1:.4f} (Saved metadata: {metadata['evaluation_metrics']['f1_score']})")
print(f"ROC-AUC:     {roc:.4f} (Saved metadata: {metadata['evaluation_metrics']['roc_auc']})")
print(f"Brier Score: {brier:.4f}")
print(f"Confusion Matrix:\n{cm}")

# Cross-patient evaluation (Leave-One-Patient-Out)
print("\n--- PATIENT-LEVEL GENERALIZATION (Leave-One-Patient-Out) ---")
patient_ids = df["patient_id"].unique()
for pid in patient_ids:
    p_test = df[df["patient_id"] == pid]
    if len(p_test["label"].unique()) > 1:
        p_X = p_test[FEATURE_NAMES]
        p_y = p_test["label"].astype(int)
        p_prob = pipeline.predict_proba(p_X)[:, 1]
        p_auc = roc_auc_score(p_y, p_prob)
        p_f1 = f1_score(p_y, pipeline.predict(p_X), zero_division=0)
        print(f"  Patient #{pid}: N={len(p_test)}, Positive={p_y.sum()}/{len(p_y)} ({p_y.mean():.1%}), ROC-AUC={p_auc:.4f}, F1={p_f1:.4f}")
    else:
        print(f"  Patient #{pid}: N={len(p_test)}, Single class label (no AUC)")
