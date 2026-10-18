import React, { useState, useEffect, useCallback, useId } from 'react';
import {
  fetchAlerts,
  acknowledgeAlert,
  resolveAlert,
  evaluateAlerts,
} from '../api/client';
import LoadingSpinner from './Common/LoadingSpinner';
import EmptyState from './Common/EmptyState';

function formatTimestamp(timestampStr) {
  if (!timestampStr) return '--';
  try {
    const d = new Date(timestampStr);
    if (isNaN(d.getTime())) return String(timestampStr);
    return d.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return String(timestampStr);
  }
}

export default function AlertsPanel({ selectedPatient, onSelectPatient, onAlertsUpdated }) {
  const [alerts, setAlerts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('active'); // 'all' | 'active' | 'acknowledged' | 'resolved'
  const [sourceFilter, setSourceFilter] = useState('all'); // 'all' | 'observed_reading' | 'experimental_prediction'
  const [patientScope, setPatientScope] = useState('current'); // 'current' | 'all'

  // Action states to prevent repeated duplicate clicks
  const [activeTab, setActiveTab] = useState('surveillance'); // 'surveillance' | 'dispatch'
  const [actionInProgressId, setActionInProgressId] = useState(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const panelId = useId();

  const loadAlerts = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const patientId = patientScope === 'current' && selectedPatient?.id ? selectedPatient.id : null;
      const status = statusFilter === 'all' ? null : statusFilter;
      const source = sourceFilter === 'all' ? null : sourceFilter;

      const data = await fetchAlerts({ patientId, status, source });
      setAlerts(data);
      if (onAlertsUpdated) {
        onAlertsUpdated(data);
      }
    } catch (err) {
      setError(err.message || 'Failed to load clinical risk alerts.');
    } finally {
      setIsLoading(false);
    }
  }, [patientScope, selectedPatient, statusFilter, sourceFilter, onAlertsUpdated]);

  useEffect(() => {
    loadAlerts();
  }, [loadAlerts]);

  // Handle Acknowledge
  const handleAcknowledge = async (alertId) => {
    if (actionInProgressId === alertId) return;
    setActionInProgressId(alertId);
    try {
      const updated = await acknowledgeAlert(alertId);
      setAlerts((prev) => prev.map((a) => (a.id === alertId ? updated : a)));
      if (onAlertsUpdated) onAlertsUpdated();
    } catch (err) {
      alert(`Failed to acknowledge alert: ${err.message}`);
    } finally {
      setActionInProgressId(null);
    }
  };

  // Handle Resolve
  const handleResolve = async (alertId) => {
    if (actionInProgressId === alertId) return;
    setActionInProgressId(alertId);
    try {
      const updated = await resolveAlert(alertId);
      setAlerts((prev) => prev.map((a) => (a.id === alertId ? updated : a)));
      if (onAlertsUpdated) onAlertsUpdated();
    } catch (err) {
      alert(`Failed to resolve alert: ${err.message}`);
    } finally {
      setActionInProgressId(null);
    }
  };

  // Trigger evaluation
  const handleEvaluate = async () => {
    if (isEvaluating) return;
    setIsEvaluating(true);
    try {
      const patientId = patientScope === 'current' && selectedPatient?.id ? selectedPatient.id : null;
      await evaluateAlerts(patientId);
      await loadAlerts();
    } catch (err) {
      alert(`Evaluation error: ${err.message}`);
    } finally {
      setIsEvaluating(false);
    }
  };

  const activeCount = alerts.filter((a) => a.status === 'active').length;

  return (
    <div className="section-container alerts-container" id={`alerts-panel-${panelId}`}>
      {/* Header Banner */}
      <div className="section-header-banner">
        <div className="predictions-header-row">
          <div>
            <div className="section-title-row">
              <h2 className="section-title">Clinical Risk Alert Engine</h2>
              <span className="badge badge-warning">Demonstration Thresholds</span>
              {activeCount > 0 && (
                <span className="badge badge-critical">{activeCount} Active</span>
              )}
            </div>
            <p className="section-desc">
              Automated surveillance distinguishing recorded telemetry threshold breaches from experimental model predictions.
            </p>
          </div>

          <div className="alerts-header-actions" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <div className="filter-btn-pill" style={{ marginRight: '8px' }}>
              <button
                type="button"
                className={`filter-btn ${activeTab === 'surveillance' ? 'active' : ''}`}
                onClick={() => setActiveTab('surveillance')}
              >
                Surveillance Feed ({alerts.length})
              </button>
              <button
                type="button"
                className={`filter-btn ${activeTab === 'dispatch' ? 'active' : ''}`}
                onClick={() => setActiveTab('dispatch')}
              >
                Simulated Clinician Pager ({alerts.filter(a => a.severity === 'critical' || a.severity === 'warning').length})
              </button>
            </div>
            <button
              type="button"
              className="prediction-action-btn"
              onClick={handleEvaluate}
              disabled={isEvaluating}
              title="Re-evaluate all rules & models against telemetry"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                style={{ animation: isEvaluating ? 'spin 1s linear infinite' : 'none' }}
              >
                <path d="M23 4v6h-6" />
                <path d="M1 20v-6h6" />
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
              </svg>
              <span>{isEvaluating ? 'Evaluating...' : 'Scan / Re-evaluate'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="alerts-filter-bar">
        {/* Patient Scope Filter */}
        <div className="filter-group">
          <span className="filter-group-label">Scope:</span>
          <div className="filter-btn-pill">
            <button
              type="button"
              className={`filter-btn ${patientScope === 'current' ? 'active' : ''}`}
              onClick={() => setPatientScope('current')}
              disabled={!selectedPatient}
            >
              {selectedPatient ? `Active (#${selectedPatient.id})` : 'Active Patient'}
            </button>
            <button
              type="button"
              className={`filter-btn ${patientScope === 'all' ? 'active' : ''}`}
              onClick={() => setPatientScope('all')}
            >
              All Cohort
            </button>
          </div>
        </div>

        {/* Status Filter */}
        <div className="filter-group">
          <span className="filter-group-label">Status:</span>
          <div className="filter-btn-pill">
            {['active', 'acknowledged', 'resolved', 'all'].map((st) => (
              <button
                key={st}
                type="button"
                className={`filter-btn ${statusFilter === st ? 'active' : ''}`}
                onClick={() => setStatusFilter(st)}
              >
                {st.charAt(0).toUpperCase() + st.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Source Filter */}
        <div className="filter-group">
          <span className="filter-group-label">Source:</span>
          <div className="filter-btn-pill">
            <button
              type="button"
              className={`filter-btn ${sourceFilter === 'all' ? 'active' : ''}`}
              onClick={() => setSourceFilter('all')}
            >
              All
            </button>
            <button
              type="button"
              className={`filter-btn ${sourceFilter === 'observed_reading' ? 'active' : ''}`}
              onClick={() => setSourceFilter('observed_reading')}
            >
              Observed
            </button>
            <button
              type="button"
              className={`filter-btn ${sourceFilter === 'experimental_prediction' ? 'active' : ''}`}
              onClick={() => setSourceFilter('experimental_prediction')}
            >
              Model
            </button>
          </div>
        </div>
      </div>

      {/* Demonstration Notice */}
      <div className="alert-engine-notice">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        <span>
          <strong>Configured Demonstration Thresholds:</strong> Severe Hypoglycemia &lt; 54 mg/dL,
          Hypoglycemia &lt; 70 mg/dL, Hyperglycemia &ge; 180 mg/dL, Severe Hyperglycemia &ge; 250 mg/dL,
          Tachycardia &ge; 100 bpm + depressed HRV &le; 25 ms, Predicted Spike Risk &ge; 0.50.
          <em> These values are configured for prototype evaluation only and do not represent clinical guidelines.</em>
        </span>
      </div>

      {/* Main Content States */}
      {isLoading && (
        <div style={{ padding: '40px 0' }}>
          <LoadingSpinner message="Querying clinical risk surveillance alerts..." />
        </div>
      )}

      {!isLoading && error && (
        <div className="prediction-state-card error-state-card">
          <h4 className="error-state-title">Alert Retrieval Failed</h4>
          <p className="error-state-detail">{error}</p>
          <button type="button" className="error-retry-btn" onClick={loadAlerts}>
            Retry
          </button>
        </div>
      )}

      {!isLoading && !error && alerts.length === 0 && (
        <EmptyState
          title="No Alerts Found"
          message={`No ${statusFilter !== 'all' ? statusFilter : ''} alerts match the current filter selection.`}
          icon={
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
          }
        />
      )}

      {!isLoading && !error && alerts.length > 0 && activeTab === 'surveillance' && (
        <div className="alerts-card-list">
          {alerts.map((alert) => {
            const isObserved = alert.source === 'observed_reading';
            const isPredicted = alert.source === 'experimental_prediction';
            const isProcessing = actionInProgressId === alert.id;

            return (
              <div
                key={alert.id}
                className={`alert-record-card ${
                  isPredicted ? 'card-predicted' : 'card-observed'
                } status-${alert.status}`}
              >
                {/* Header Row */}
                <div className="alert-card-top">
                  <div className="alert-badges-strip">
                    {/* Severity Badge */}
                    <span
                      className={`badge ${
                        alert.severity === 'critical'
                          ? 'badge-critical'
                          : alert.severity === 'warning'
                          ? 'badge-warning'
                          : 'badge-neutral'
                      }`}
                    >
                      {alert.severity.toUpperCase()}
                    </span>

                    {/* Source Distinction Badge */}
                    {isObserved ? (
                      <span className="badge badge-normal source-tag">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                        </svg>
                        Observed Telemetry
                      </span>
                    ) : (
                      <span className="badge badge-twin source-tag">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                          <polyline points="17 6 23 6 23 12" />
                        </svg>
                        Model Prediction
                      </span>
                    )}

                    {/* Status Pill */}
                    <span className={`alert-status-pill status-${alert.status}`}>
                      {alert.status}
                    </span>
                  </div>

                  <span className="alert-time-tag">
                    {formatTimestamp(alert.timestamp)}
                  </span>
                </div>

                {/* Patient & Subject Info */}
                <div className="alert-card-subject">
                  <div className="subject-left">
                    <button
                      type="button"
                      className="alert-patient-name"
                      style={{ background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', padding: 0 }}
                      onClick={() => onSelectPatient && onSelectPatient(alert.patient_id)}
                      title="Switch active patient to this subject"
                    >
                      {alert.patient_name || `Patient #${alert.patient_id}`}
                    </button>
                    <span className="alert-patient-id">Record #{alert.patient_id}</span>
                  </div>

                  {/* Trigger vs Threshold Tag */}
                  {alert.trigger_value != null && (
                    <div className="alert-trigger-box">
                      <span className="trigger-label">Triggered by:</span>
                      <strong className="trigger-val">
                        {isPredicted
                          ? `Risk Score: ${(alert.trigger_value * 100).toFixed(1)}%`
                          : `${alert.trigger_value} mg/dL`}
                      </strong>
                      {alert.threshold != null && (
                        <span className="trigger-thresh">
                          (Thresh: {isPredicted ? `${(alert.threshold * 100).toFixed(0)}%` : `${alert.threshold} mg/dL`})
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Alert Message Explanation */}
                <p className="alert-card-message">{alert.message}</p>

                {/* Card Actions Footer */}
                <div className="alert-card-footer">
                  <div className="alert-source-hint">
                    {isObserved
                      ? 'Detected from verified stored time-series sensor data.'
                      : 'Generated by prototype forward-looking inference pipeline.'}
                  </div>

                  <div className="alert-actions-group">
                    {alert.status === 'active' && (
                      <>
                        <button
                          type="button"
                          className="alert-btn btn-ack"
                          onClick={() => handleAcknowledge(alert.id)}
                          disabled={isProcessing}
                        >
                          {isProcessing ? 'Saving...' : 'Acknowledge'}
                        </button>
                        <button
                          type="button"
                          className="alert-btn btn-res"
                          onClick={() => handleResolve(alert.id)}
                          disabled={isProcessing}
                        >
                          {isProcessing ? 'Saving...' : 'Resolve'}
                        </button>
                      </>
                    )}

                    {alert.status === 'acknowledged' && (
                      <>
                        <span className="ack-time-note">
                          Acked {formatTimestamp(alert.acknowledged_at)}
                        </span>
                        <button
                          type="button"
                          className="alert-btn btn-res"
                          onClick={() => handleResolve(alert.id)}
                          disabled={isProcessing}
                        >
                          {isProcessing ? 'Saving...' : 'Resolve'}
                        </button>
                      </>
                    )}

                    {alert.status === 'resolved' && (
                      <span className="res-tag">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                        Resolved {formatTimestamp(alert.resolved_at)}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Simulated Clinician Triage Pager Tab */}
      {!isLoading && !error && activeTab === 'dispatch' && (
        <div className="dispatch-inbox-container">
          <div className="alert-engine-notice" style={{ background: 'rgba(56, 189, 248, 0.08)', borderColor: '#38bdf8' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            <div>
              <strong style={{ color: '#38bdf8', display: 'block' }}>Simulated Clinician Triage Notification Center</strong>
              <span>
                Demonstration of clinical escalation routing. In a production hospital system, these critical and warning breaches trigger on-call pagers and staff notification queues.
                <strong style={{ color: '#e2e8f0', display: 'block', marginTop: '4px' }}>
                  Notice: External SMS, Push notifications, and SMTP Email delivery are intentionally unconfigured in this demonstration prototype. All items below represent simulated local event dispatches.
                </strong>
              </span>
            </div>
          </div>

          <div className="dispatch-list" style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' }}>
            {alerts
              .filter((a) => a.severity === 'critical' || a.severity === 'warning')
              .map((a) => (
                <div
                  key={`dispatch-${a.id}`}
                  style={{
                    background: '#1e293b',
                    borderRadius: '8px',
                    borderLeft: `4px solid ${a.severity === 'critical' ? '#ef4444' : '#f59e0b'}`,
                    padding: '14px 18px',
                    border: '1px solid #334155',
                    borderLeftWidth: '4px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <span className={`badge ${a.severity === 'critical' ? 'badge-critical' : 'badge-warning'}`}>
                        {a.severity.toUpperCase()} ESCALATION
                      </span>
                      <span className="badge badge-normal" style={{ fontSize: '11px' }}>
                        📡 [SIMULATED INTERNAL PAGER]
                      </span>
                      <span style={{ fontSize: '12px', color: '#94a3b8' }}>
                        Recipient: <strong>Endocrinology On-Call / Diabetes Triage Desk</strong>
                      </span>
                    </div>
                    <span style={{ fontSize: '12px', color: '#64748b' }}>
                      {formatTimestamp(a.timestamp)}
                    </span>
                  </div>

                  <div style={{ fontSize: '14px', fontWeight: 600, color: '#f1f5f9', marginBottom: '4px' }}>
                    {a.patient_name || `Patient #${a.patient_id}`} (ID #{a.patient_id}) — {a.message}
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', color: '#94a3b8', marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #334155' }}>
                    <div>
                      <span>Trigger Value: <strong style={{ color: '#f8fafc' }}>{a.trigger_value}</strong></span>
                      {a.threshold && <span> | Threshold: {a.threshold}</span>}
                      <span> | Status: <strong style={{ color: a.status === 'active' ? '#ef4444' : '#10b981' }}>{a.status.toUpperCase()}</strong></span>
                    </div>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <span style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                        Simulated Local Delivery Confirmed
                      </span>
                      {a.status === 'active' && (
                        <button
                          type="button"
                          className="alert-btn btn-ack"
                          style={{ padding: '4px 8px', fontSize: '11px' }}
                          onClick={() => handleAcknowledge(a.id)}
                          disabled={actionInProgressId === a.id}
                        >
                          Ack Triage
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
