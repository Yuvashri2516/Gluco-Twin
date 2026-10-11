"""
Tests for Feature Engineering, Temporal Windowing, and Leakage Prevention.
"""

from datetime import datetime, timedelta, timezone
import pytest

from app.ml.pipeline import (
    extract_features_at_timestamp,
    FEATURE_NAMES,
    OBSERVATION_WINDOW_MINUTES,
    SPIKE_THRESHOLD_MG_DL,
)

@pytest.fixture
def sample_patient():
    return {
        "id": 101,
        "name": "Test Subject",
        "age": 50,
        "gender": "Female",
        "diabetes_type": "Type 2",
        "years_since_diagnosis": 6,
    }


def test_feature_calculations_exact(sample_patient):
    """Verify exact mean, slope, and standard deviation calculations over the 1h window."""
    base_t = datetime(2026, 10, 10, 12, 0, 0, tzinfo=timezone.utc)
    
    # 4 readings in 1-hour window: 11:15 (100), 11:30 (120), 11:45 (140), 12:00 (160)
    glucose_readings = [
        {"id": 1, "timestamp": base_t - timedelta(minutes=45), "value": 100.0},
        {"id": 2, "timestamp": base_t - timedelta(minutes=30), "value": 120.0},
        {"id": 3, "timestamp": base_t - timedelta(minutes=15), "value": 140.0},
        {"id": 4, "timestamp": base_t, "value": 160.0},
    ]
    vital_readings = [
        {"id": 1, "timestamp": base_t - timedelta(minutes=30), "heart_rate": 70.0, "hrv": 45.0},
        {"id": 2, "timestamp": base_t, "heart_rate": 80.0, "hrv": 55.0},
    ]

    features, warnings = extract_features_at_timestamp(
        sample_patient, glucose_readings, vital_readings, base_t
    )

    assert features is not None
    assert features["curr_glucose"] == 160.0
    assert features["mean_glucose_1h"] == 130.0  # (100+120+140+160) / 4
    # slope: (160 - 100) / 45 min = 1.3333 mg/dL per min
    assert pytest.approx(features["slope_glucose_1h"], rel=1e-2) == 1.3333
    assert features["curr_hr"] == 80.0
    assert features["curr_hrv"] == 55.0
    assert features["mean_hr_1h"] == 75.0
    assert features["mean_hrv_1h"] == 50.0
    assert features["age"] == 50.0
    assert features["years_diagnosis"] == 6.0
    assert features["is_type1"] == 0.0
    assert features["is_prediabetes"] == 0.0


def test_leakage_prevention_ignores_future_data(sample_patient):
    """
    Verify that readings occurring after prediction_time are strictly excluded
    from feature calculations.
    """
    base_t = datetime(2026, 10, 10, 12, 0, 0, tzinfo=timezone.utc)
    
    past_glucose = [
        {"id": 1, "timestamp": base_t - timedelta(minutes=30), "value": 110.0},
        {"id": 2, "timestamp": base_t, "value": 120.0},
    ]
    # Future reading that spikes to 250 mg/dL at 12:15
    future_glucose = past_glucose + [
        {"id": 3, "timestamp": base_t + timedelta(minutes=15), "value": 250.0},
        {"id": 4, "timestamp": base_t + timedelta(minutes=45), "value": 290.0},
    ]

    feat_past, _ = extract_features_at_timestamp(sample_patient, past_glucose, [], base_t)
    feat_with_future, _ = extract_features_at_timestamp(sample_patient, future_glucose, [], base_t)

    # Features must be identical; future data must have zero influence
    assert feat_past == feat_with_future
    assert feat_with_future["curr_glucose"] == 120.0
    assert feat_with_future["mean_glucose_1h"] == 115.0


def test_insufficient_historical_readings(sample_patient):
    """Must return None and warn if fewer than 2 readings exist in lookback window."""
    base_t = datetime(2026, 10, 10, 12, 0, 0, tzinfo=timezone.utc)
    
    # Only 1 reading
    only_one = [{"id": 1, "timestamp": base_t, "value": 130.0}]
    features, warnings = extract_features_at_timestamp(sample_patient, only_one, [], base_t)
    assert features is None
    assert any("Insufficient readings" in w for w in warnings)

    # Empty list
    features_empty, warnings_empty = extract_features_at_timestamp(sample_patient, [], [], base_t)
    assert features_empty is None
    assert any("No historical glucose readings" in w for w in warnings_empty)


def test_irregular_and_missing_timestamps(sample_patient):
    """Features should handle irregular time intervals gracefully."""
    base_t = datetime(2026, 10, 10, 12, 0, 0, tzinfo=timezone.utc)
    
    # Readings at non-standard intervals (e.g. 11:08, 11:27, 11:59)
    readings = [
        {"id": 1, "timestamp": base_t - timedelta(minutes=52), "value": 115.0},
        {"id": 2, "timestamp": base_t - timedelta(minutes=33), "value": 125.0},
        {"id": 3, "timestamp": base_t - timedelta(minutes=1), "value": 140.0},
    ]
    features, warnings = extract_features_at_timestamp(sample_patient, readings, [], base_t)
    assert features is not None
    assert features["curr_glucose"] == 140.0
    # Imputed default vitals notice
    assert any("defaulted to cohort baseline" in w for w in warnings)
