"""
routers/alerts.py - Clinical Alerts API Endpoints (Phase 5)
=============================================================

Endpoints for clinical alert triage, notification dispatch, and evaluation:
  GET   /api/alerts                     -> list alerts (filterable by patient, status, source)
  GET   /api/alerts/{alert_id}          -> single alert details
  POST  /api/alerts/{alert_id}/acknowledge -> acknowledge an alert
  POST  /api/alerts/{alert_id}/resolve     -> resolve an alert
  POST  /api/alerts/evaluate            -> trigger controlled alert evaluation
"""

from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, Patient
from app.schemas import (
    AlertRead,
    AlertEvaluationRequest,
    AlertEvaluationResponse,
)
from app.alerts_engine import evaluate_all_alerts_for_patient

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


def _format_alert(alert: Alert, patient_name: Optional[str] = None) -> AlertRead:
    """Format an ORM Alert instance into Pydantic AlertRead with patient_name."""
    name = patient_name or (alert.patient.name if alert.patient else None)
    return AlertRead(
        id=alert.id,
        patient_id=alert.patient_id,
        patient_name=name,
        timestamp=alert.timestamp,
        severity=alert.severity,
        message=alert.message,
        alert_type=alert.alert_type,
        source=alert.source or "observed_reading",
        status=alert.status or ("acknowledged" if alert.acknowledged else "active"),
        trigger_value=alert.trigger_value,
        threshold=alert.threshold,
        acknowledged=bool(alert.acknowledged),
        acknowledged_at=alert.acknowledged_at,
        resolved_at=alert.resolved_at,
        dedup_key=alert.dedup_key,
    )


@router.get("", response_model=List[AlertRead])
@router.get("/", response_model=List[AlertRead], include_in_schema=False)
def list_alerts(
    patient_id: Optional[int] = Query(default=None, description="Filter alerts by patient ID"),
    status: Optional[str] = Query(default=None, description="Filter alerts by status (active/acknowledged/resolved)"),
    source: Optional[str] = Query(default=None, description="Filter by source (observed_reading/experimental_prediction)"),
    severity: Optional[str] = Query(default=None, description="Filter by severity (critical/warning/info)"),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    List alerts with flexible filtering. Active alerts are prioritized first,
    followed by most recent timestamps.
    """
    query = db.query(Alert)

    if patient_id is not None:
        # Validate patient exists
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=404,
                detail=f"Patient #{patient_id} not found."
            )
        query = query.filter(Alert.patient_id == patient_id)

    if status:
        query = query.filter(Alert.status == status)

    if source:
        query = query.filter(Alert.source == source)

    if severity:
        query = query.filter(Alert.severity == severity)

    # Order by active status first, then by timestamp descending
    alerts = query.order_by(
        Alert.status == "active",  # in SQLite True is 1, so active goes last in asc, first in desc
        Alert.timestamp.desc(),
    ).all()

    # Re-sort to guarantee 'active' > 'acknowledged' > 'resolved' then timestamp desc
    status_priority = {"active": 0, "acknowledged": 1, "resolved": 2}
    sorted_alerts = sorted(
        alerts,
        key=lambda a: (status_priority.get(a.status, 3), -(a.timestamp.timestamp() if a.timestamp else 0))
    )[:limit]

    return [_format_alert(a) for a in sorted_alerts]


@router.get("/{alert_id}", response_model=AlertRead)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """Retrieve details for a specific alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert #{alert_id} not found.")
    return _format_alert(alert)


@router.post("/{alert_id}/acknowledge", response_model=AlertRead)
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Acknowledge an active alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert #{alert_id} not found.")

    if alert.status == "resolved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid alert transition: Alert #{alert_id} is already resolved and cannot be acknowledged.",
        )

    alert.acknowledged = True
    alert.acknowledged_at = datetime.now(timezone.utc)
    if alert.status == "active":
        alert.status = "acknowledged"

    db.commit()
    db.refresh(alert)
    return _format_alert(alert)


@router.post("/{alert_id}/resolve", response_model=AlertRead)
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """Resolve an alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert #{alert_id} not found.")

    if alert.status == "resolved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid alert transition: Alert #{alert_id} is already resolved.",
        )

    alert.acknowledged = True
    if not alert.acknowledged_at:
        alert.acknowledged_at = datetime.now(timezone.utc)
    alert.status = "resolved"
    alert.resolved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(alert)
    return _format_alert(alert)


@router.post("/evaluate", response_model=AlertEvaluationResponse)
def trigger_alert_evaluation(
    request: AlertEvaluationRequest = AlertEvaluationRequest(),
    db: Session = Depends(get_db),
):
    """
    Trigger controlled evaluation of alerts for a specific patient or all patients.
    Idempotent due to deterministic deduplication keys.
    """
    patients_to_eval: List[Patient] = []

    if request.patient_id is not None:
        p = db.query(Patient).filter(Patient.id == request.patient_id).first()
        if not p:
            raise HTTPException(status_code=404, detail=f"Patient #{request.patient_id} not found.")
        patients_to_eval = [p]
    else:
        patients_to_eval = db.query(Patient).all()

    total_new = 0
    all_created: List[Alert] = []

    for patient in patients_to_eval:
        created = evaluate_all_alerts_for_patient(db, patient)
        total_new += len(created)
        all_created.extend(created)

    # Return all current alerts for evaluated patient(s)
    query = db.query(Alert)
    if request.patient_id is not None:
        query = query.filter(Alert.patient_id == request.patient_id)

    current_alerts = query.order_by(Alert.timestamp.desc()).limit(50).all()

    return AlertEvaluationResponse(
        evaluated_patients=len(patients_to_eval),
        new_alerts_created=total_new,
        alerts=[_format_alert(a) for a in current_alerts],
    )
