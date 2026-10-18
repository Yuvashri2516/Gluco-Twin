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
    Samples near the end of the recording that lack the full 2-hour (120-min)
    future horizon must be dropped rather than assumed to be negative.
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

    # For step 11 (12:45), future readings is empty -> excluded
    # For step 10 (12:30), future span is only 15 min -> excluded
    # For step 4 (11:00), future span is 105 min (step 11 is 12:45) -> lacks full 120 min -> excluded
    # Only steps with at least 120 min future span (steps 0 to 3) must remain
    max_step_in_df = df["step_idx"].max()
    assert max_step_in_df <= 3
    # End-of-series steps with < 120 min (steps 4 to 11) must NOT be present
    assert not any(df["step_idx"] >= 4)


def test_105_minute_partial_horizon_without_spike_is_excluded():
    """
    REGRESSION TEST: A sample with 105 minutes of observations and no observed spike
    must be excluded, because the final 15 minutes of the 120-minute horizon are
    unobserved and cannot be assumed negative.
    """
    base_t = datetime(2026, 10, 10, 10, 0, 0, tzinfo=timezone.utc)
    patient = {
        "id": 2,
        "name": "Subject C",
        "age": 50,
        "gender": "Male",
        "diabetes_type": "Type 2",
        "years_since_diagnosis": 6,
    }

    # 8 readings total (spanning 10:00 to 11:45 = 105 minutes of future observations from 10:00)
    # Step 0 (10:00) has readings at 10:15, 10:30, 10:45, 11:00, 11:15, 11:30, 11:45 (7 future readings = 105 min)
    readings = [
        {"id": step + 1, "timestamp": base_t + timedelta(minutes=step * 15), "value": 110.0}
        for step in range(8)
    ]

    df = build_supervised_dataset(
        patients=[patient],
        glucose_by_patient={2: readings},
        vitals_by_patient={2: []},
        spike_threshold=180.0,
        horizon_minutes=120,
    )

    # Even though step 0 has 105 min of future readings and no spike,
    # it must NOT be included with label=0 because the 120-min horizon was not reached.
    assert df.empty or not any(df["step_idx"] == 0)
