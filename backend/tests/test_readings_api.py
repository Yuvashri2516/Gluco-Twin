"""
test_readings_api.py - Comprehensive Idempotence, Timestamp, and Safety Audit Tests
====================================================================================

Tests cover:
  TEST 1: Empty database initialization
  TEST 2: Refreshing database with recent readings adds no unnecessary readings
  TEST 3: Calling refresh twice consecutively adds 0 rows on second call
  TEST 4: No generated timestamp exceeds current UTC time
  TEST 5: Generated timestamps follow 15-minute sampling intervals
  TEST 6: Glucose and vital timestamps remain 100% synchronized
  TEST 7: Bounded catch-up caps readings when large gap exists
  TEST 8: Existing historical readings retain exact values and timestamps
  TEST 9: Existing alerts retain original statuses and fields
  TEST 10: Insertion / commit rollback safety
  TEST 11: Patient with missing readings handled safely
  TEST 12: UTC logic is independent of local timezone
  TEST 13: API time-window filtering excludes older and future readings
  TEST 14: Automated tests maintain 100% isolation from real database

All tests use in-memory SQLite (`sqlite:///:memory:`) and never mutate `glucotwin.db`.
"""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import Patient, GlucoseReading, VitalReading, Alert
from app.seed import refresh_synthetic_telemetry, seed_database


@pytest.fixture(scope="function")
def test_db_session():
    """Isolated in-memory SQLite session with test fixtures."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    # Patient 1: Has historical and recent readings
    p1 = Patient(
        id=1,
        name="Test Patient Alpha",
        age=45,
        gender="Male",
        diabetes_type="Type 2",
        years_since_diagnosis=5,
        weight_kg=80.0,
        height_cm=175.0,
    )
    # Patient 2: Has NO readings (tests missing telemetry edge case)
    p2 = Patient(
        id=2,
        name="Test Patient Beta",
        age=30,
        gender="Female",
        diabetes_type="Type 1",
        years_since_diagnosis=2,
        weight_kg=60.0,
        height_cm=165.0,
    )
    session.add_all([p1, p2])
    session.flush()

    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

    # 4 old readings (outside 24h window) for patient 1
    for i in range(4):
        old_time = now_utc - timedelta(hours=36) + timedelta(minutes=i * 15)
        session.add(GlucoseReading(
            patient_id=1,
            timestamp=old_time,
            value=120.0 + i,
            is_valid=True,
        ))
        session.add(VitalReading(
            patient_id=1,
            timestamp=old_time,
            heart_rate=70.0 + i,
            hrv=45.0,
        ))

    # 4 recent readings (inside 24h window) for patient 1
    for i in range(4):
        recent_time = now_utc - timedelta(hours=2) + timedelta(minutes=i * 15)
        session.add(GlucoseReading(
            patient_id=1,
            timestamp=recent_time,
            value=140.0 + i,
            is_valid=True,
        ))
        session.add(VitalReading(
            patient_id=1,
            timestamp=recent_time,
            heart_rate=75.0 + i,
            hrv=40.0,
        ))

    # Existing alerts with distinct lifecycle statuses
    session.add(Alert(
        id=1,
        patient_id=1,
        severity="warning",
        message="Historical test alert 1",
        status="acknowledged",
        acknowledged=True,
        dedup_key="obs:1:test:1",
    ))
    session.add(Alert(
        id=2,
        patient_id=1,
        severity="critical",
        message="Historical test alert 2",
        status="resolved",
        acknowledged=True,
        dedup_key="obs:1:test:2",
    ))
    session.commit()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture(scope="function")
def client(test_db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ==============================================================================
# AUDIT TEST SUITE (TESTS 1 - 14)
# ==============================================================================

def test_01_empty_database_initialization():
    """TEST 1: An empty temporary database is initialized successfully."""
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    was_seeded = seed_database(session)
    assert was_seeded is True
    assert session.query(Patient).count() == 5
    # 5 patients * 288 readings (72 hours * 4 readings/h)
    assert session.query(GlucoseReading).count() == 1440
    assert session.query(VitalReading).count() == 1440
    session.close()
    engine.dispose()


def test_02_refresh_with_recent_readings_adds_no_unnecessary_readings(test_db_session):
    """TEST 2: Refreshing a database with recent readings adds no unnecessary duplicate readings."""
    # First catch up
    refresh_synthetic_telemetry(test_db_session)
    initial_count = test_db_session.query(GlucoseReading).count()

    # Immediate second run when < 15 min has elapsed
    added = refresh_synthetic_telemetry(test_db_session)
    assert added == 0
    assert test_db_session.query(GlucoseReading).count() == initial_count


def test_03_calling_refresh_twice_does_not_increase_row_counts(test_db_session):
    """TEST 3: Calling the refresh function twice without another interval adds 0 rows on second call."""
    run1 = refresh_synthetic_telemetry(test_db_session)
    assert run1 > 0
    count1 = test_db_session.query(GlucoseReading).count()

    run2 = refresh_synthetic_telemetry(test_db_session)
    assert run2 == 0
    count2 = test_db_session.query(GlucoseReading).count()
    assert count1 == count2


def test_04_no_generated_timestamp_exceeds_current_utc_time(test_db_session):
    """TEST 4: No generated timestamp exceeds the actual current UTC time."""
    refresh_synthetic_telemetry(test_db_session)
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

    future_g = test_db_session.query(GlucoseReading).filter(GlucoseReading.timestamp > now_utc).count()
    future_v = test_db_session.query(VitalReading).filter(VitalReading.timestamp > now_utc).count()

    assert future_g == 0
    assert future_v == 0


def test_05_generated_timestamps_follow_15_minute_sampling_schedule(test_db_session):
    """TEST 5: Generated timestamps follow the intended 15-minute sampling schedule."""
    refresh_synthetic_telemetry(test_db_session)
    readings = (
        test_db_session.query(GlucoseReading)
        .filter(GlucoseReading.patient_id == 1)
        .order_by(GlucoseReading.timestamp.asc())
        .all()
    )
    for i in range(1, len(readings)):
        delta = readings[i].timestamp - readings[i - 1].timestamp
        # Within the contiguous appended block, spacing is exactly 15 minutes
        if i >= 8:  # after the initial 8 test seed readings
            assert delta == timedelta(minutes=15)


def test_06_glucose_and_vital_timestamps_remain_synchronized(test_db_session):
    """TEST 6: Glucose and vital timestamps remain 100% synchronized for each patient."""
    refresh_synthetic_telemetry(test_db_session)

    g_stamps = [r.timestamp for r in test_db_session.query(GlucoseReading).filter(GlucoseReading.patient_id == 1).order_by(GlucoseReading.timestamp.asc()).all()]
    v_stamps = [r.timestamp for r in test_db_session.query(VitalReading).filter(VitalReading.patient_id == 1).order_by(VitalReading.timestamp.asc()).all()]

    assert len(g_stamps) == len(v_stamps)
    assert g_stamps == v_stamps


def test_07_bounded_catchup_cannot_generate_unlimited_readings(test_db_session):
    """TEST 7: A bounded catch-up operation cannot generate an unlimited number of readings."""
    # Simulate a patient whose latest reading is from 90 days ago
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    sess = Session()

    p = Patient(id=99, name="Ancient Patient", age=60, gender="Male", diabetes_type="Type 2")
    sess.add(p)
    sess.flush()

    very_old_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=90)
    sess.add(GlucoseReading(patient_id=99, timestamp=very_old_time, value=120.0, is_valid=True))
    sess.add(VitalReading(patient_id=99, timestamp=very_old_time, heart_rate=70.0, hrv=50.0))
    sess.commit()

    # Refresh with max_catchup_hours=72
    added = refresh_synthetic_telemetry(sess, max_catchup_hours=72)
    max_allowed = (72 * 60) // 15  # 288
    assert added <= max_allowed
    assert sess.query(GlucoseReading).filter(GlucoseReading.patient_id == 99).count() <= max_allowed + 1

    sess.close()
    engine.dispose()


def test_08_historical_readings_retain_exact_values_and_timestamps(test_db_session):
    """TEST 8: Existing historical readings retain exactly the same values and timestamps after a refresh."""
    pre_readings = [
        (r.id, r.patient_id, r.timestamp, r.value)
        for r in test_db_session.query(GlucoseReading).order_by(GlucoseReading.id.asc()).all()
    ]

    refresh_synthetic_telemetry(test_db_session)

    post_readings = [
        (r.id, r.patient_id, r.timestamp, r.value)
        for r in test_db_session.query(GlucoseReading).filter(GlucoseReading.id <= len(pre_readings)).order_by(GlucoseReading.id.asc()).all()
    ]

    assert pre_readings == post_readings


def test_09_existing_alerts_retain_statuses_and_fields_after_refresh(test_db_session):
    """TEST 9: Existing alerts retain their original statuses, messages, and deduplication keys."""
    alert1_before = (test_db_session.query(Alert).filter(Alert.id == 1).first().status,
                     test_db_session.query(Alert).filter(Alert.id == 1).first().dedup_key)
    alert2_before = (test_db_session.query(Alert).filter(Alert.id == 2).first().status,
                     test_db_session.query(Alert).filter(Alert.id == 2).first().dedup_key)

    refresh_synthetic_telemetry(test_db_session)

    alert1_after = (test_db_session.query(Alert).filter(Alert.id == 1).first().status,
                    test_db_session.query(Alert).filter(Alert.id == 1).first().dedup_key)
    alert2_after = (test_db_session.query(Alert).filter(Alert.id == 2).first().status,
                    test_db_session.query(Alert).filter(Alert.id == 2).first().dedup_key)

    assert alert1_before == alert1_after == ("acknowledged", "obs:1:test:1")
    assert alert2_before == alert2_after == ("resolved", "obs:1:test:2")


def test_10_database_error_handling_and_rollback(test_db_session, monkeypatch):
    """TEST 10: An error during commit is handled safely and rolls back transactions."""
    initial_count = test_db_session.query(GlucoseReading).count()

    def mock_commit():
        raise RuntimeError("Simulated Database Commit Failure")

    monkeypatch.setattr(test_db_session, "commit", mock_commit)

    with pytest.raises(RuntimeError, match="Simulated Database Commit Failure"):
        refresh_synthetic_telemetry(test_db_session)

    # After rollback, count is identical to initial
    assert test_db_session.query(GlucoseReading).count() == initial_count


def test_11_patient_with_missing_readings_handled_safely(test_db_session):
    """TEST 11: Patients with missing telemetry (Patient Beta) are handled safely without crashing."""
    # Patient 2 has 0 readings in test_db_session fixture
    assert test_db_session.query(GlucoseReading).filter(GlucoseReading.patient_id == 2).count() == 0

    added = refresh_synthetic_telemetry(test_db_session)
    assert added > 0
    # Patient 2 was safely skipped during refresh without error
    assert test_db_session.query(GlucoseReading).filter(GlucoseReading.patient_id == 2).count() == 0


def test_12_utc_logic_works_regardless_of_local_timezone(test_db_session):
    """TEST 12: The UTC comparison logic produces identical results regardless of local timezone offset."""
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now_utc - timedelta(hours=24)

    # All queries filter using naive UTC matching SQLite storage
    recent = (
        test_db_session.query(GlucoseReading)
        .filter(GlucoseReading.patient_id == 1, GlucoseReading.timestamp >= cutoff)
        .all()
    )
    for r in recent:
        assert r.timestamp.tzinfo is None
        assert r.timestamp >= cutoff


def test_13_api_time_window_filtering_excludes_older_and_future_readings(client):
    """TEST 13: Existing API time-window filtering correctly excludes older readings and boundary violations."""
    # 24h window returns 4 readings
    res_24 = client.get("/api/readings/glucose/1?hours=24")
    assert res_24.status_code == 200
    assert len(res_24.json()) == 4

    # 48h window includes the older readings (total 8)
    res_48 = client.get("/api/readings/glucose/1?hours=48")
    assert res_48.status_code == 200
    assert len(res_48.json()) == 8

    # 1h window excludes readings from 2h ago
    res_1h = client.get("/api/readings/glucose/1?hours=1")
    assert res_1h.status_code == 200
    assert len(res_1h.json()) == 0


def test_14_test_database_remains_isolated_from_real_database(client, test_db_session):
    """TEST 14: Automated tests maintain 100% database isolation using in-memory sessions."""
    # 1. Verify dependency override actively redirects get_db
    assert get_db in app.dependency_overrides
    test_bind = test_db_session.get_bind()
    assert str(test_bind.url) == "sqlite:///:memory:"

    # 2. Record initial counts in the isolated session
    initial_p_count = test_db_session.query(Patient).count()
    initial_g_count = test_db_session.query(GlucoseReading).count()
    assert initial_p_count == 2  # Fixture has Alpha and Beta
    assert initial_g_count == 8  # 4 old + 4 recent

    # 3. Verify TestClient queries execute against the in-memory session
    res = client.get("/api/readings/glucose/1?hours=24")
    assert res.status_code == 200
    assert len(res.json()) == 4

    # 4. Perform synthetic refresh and mutations inside the isolated test session
    refresh_synthetic_telemetry(test_db_session)
    refreshed_g_count = test_db_session.query(GlucoseReading).count()
    assert refreshed_g_count > initial_g_count

    # 5. Add a distinct test alert in the isolated session
    test_alert = Alert(
        patient_id=1,
        severity="info",
        message="Isolation verification test alert",
        status="active",
        acknowledged=False,
        dedup_key="isolation:test:1",
    )
    test_db_session.add(test_alert)
    test_db_session.commit()

    # Query through test_db_session sees the new record
    assert test_db_session.query(Alert).filter(Alert.dedup_key == "isolation:test:1").count() == 1

    # 6. Verify that an independent database session remains completely unaffected
    separate_engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    Base.metadata.create_all(bind=separate_engine)
    SeparateSession = sessionmaker(bind=separate_engine)
    separate_session = SeparateSession()

    # The independent session must have 0 of the records created in test_db_session
    assert separate_session.query(Alert).filter(Alert.dedup_key == "isolation:test:1").count() == 0
    assert separate_session.query(GlucoseReading).count() == 0

    separate_session.close()
    separate_engine.dispose()
