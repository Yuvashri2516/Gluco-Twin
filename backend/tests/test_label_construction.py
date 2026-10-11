"""
Tests for Supervised Label Construction, Horizon Coverage, and Leakage Prevention.
"""

from datetime import datetime, timedelta, timezone
import pytest

from app.ml.pipeline import (
    build_supervised_dataset,
    SPIKE_THRESHOLD_MG_DL,
    PREDICTION_HORIZON_MINUTES,
)

def test_label_construction_positive_and_negative():
    """Verify positive label (1) when glucose >= 180 in forward 2h, and 0 when below."""
    base_t = datetime(2026, 10, 10, 10, 0, 0, tzinfo=timezone.utc)
    patient = {
        "id": 1,
        "name": "Subject A",
        "age": 45,
        "gender": "Male",
        "diabetes_type": "Type 2",
        "years_since_diagnosis": 5,
    }

    # 15 readings total (spaced 15 min apart from 10:00 to 13:30)
    # Reading at index 4 (11:00):
    # Future window is 11:15 to 13:00 (8 readings: indices 5 to 12)
    # Let index 7 (11:45) be 185 mg/dL -> index 4 should have label=1
    readings = []
    for step in range(16):
        t = base_t + timedelta(minutes=step * 15)
        val = 130.0
        if step == 7:
            val = 185.0  # Spike event
        readings.append({"id": step + 1, "timestamp": t, "value": val})

    df = build_supervised_dataset(
        patients=[patient],
        glucose_by_patient={1: readings},
        vitals_by_patient={1: []},
        spike_threshold=180.0,
        horizon_minutes=120,
    )

    assert not df.empty
    # Check sample at step 4 (11:00) - future window includes step 7 (185 mg/dL)
    sample_step_4 = df[df["step_idx"] == 4]
    assert len(sample_step_4) == 1
    assert sample_step_4.iloc[0]["label"] == 1

    # Check sample at step 1 (10:15) - has 2 readings in 1h window, future includes step 7 -> label=1
    sample_step_1 = df[df["step_idx"] == 1]
    assert len(sample_step_1) == 1
    assert sample_step_1.iloc[0]["label"] == 1


def test_insufficient_future_coverage_excludes_sample():
    """
    Samples near the end of the recording that lack the full 2-hour future
    horizon must be dropped rather than assumed to be negative.
    """
    base_t = datetime(2026, 10, 10, 10, 0, 0, tzinfo=timezone.utc)
    patient = {
        "id": 1,
        "name": "Subject B",
        "age": 40,
        "gender": "Female",
        "diabetes_type": "Type 2",
        "years_since_diagnosis": 3,
    }

    # Total 12 readings (spanning 10:00 to 12:45)
    readings = [
        {"id": step + 1, "timestamp": base_t + timedelta(minutes=step * 15), "value": 120.0}
        for step in range(12)
    ]

    df = build_supervised_dataset(
        patients=[patient],
        glucose_by_patient={1: readings},
        vitals_by_patient={1: []},
        spike_threshold=180.0,
        horizon_minutes=120,
    )

    # For step 11 (12:45), future readings is empty -> cannot be in dataset
    # For step 10 (12:30), future span is only 15 min (< 105 min) -> must be excluded
    # For step 9 (12:15), future span is only 30 min -> must be excluded
    # Only steps with at least 105 min future span (steps 0 to 4) should remain
    max_step_in_df = df["step_idx"].max()
    assert max_step_in_df <= 4
    # End-of-series steps (5 to 11) must NOT be present
    assert not any(df["step_idx"] >= 5)
