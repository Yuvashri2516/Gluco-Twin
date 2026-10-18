import React, { useState, useEffect, useId } from 'react';
import { fetchDigitalTwinDetail } from '../api/client';
import LoadingSpinner from './Common/LoadingSpinner';

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

export default function DigitalTwinPanel({
  selectedPatient,
  glucoseReadings = [],
  vitalReadings = [],
}) {
  const [twinData, setTwinData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const panelId = useId();

  const patientId = selectedPatient?.id;

  useEffect(() => {
    if (!patientId) {
      setTwinData(null);
      setIsLoading(false);
      setError(null);
      return;
    }

    let isCurrent = true;
    const controller = new AbortController();

    setIsLoading(true);
    setTwinData(null);
    setError(null);

    async function loadTwinDetail() {
      try {
        const data = await fetchDigitalTwinDetail(patientId, controller.signal);
        if (isCurrent) {
          setTwinData(data);
          setError(null);
        }
      } catch (err) {
        if (err.name === 'AbortError') return;
        if (isCurrent) {
          setError(err.message || 'Failed to fetch digital twin intelligence.');
        }
      } finally {
        if (isCurrent) {
          setIsLoading(false);
        }
      }
    }

    loadTwinDetail();

    return () => {
      isCurrent = false;
      controller.abort();
    };
  }, [patientId]);

  if (!selectedPatient) {
    return null;
  }

  // Fallback to local calculations if backend intelligence is loading or failed
  const latestGlucose = glucoseReadings.length > 0 ? glucoseReadings[glucoseReadings.length - 1] : null;
  const latestVital = vitalReadings.length > 0 ? vitalReadings[vitalReadings.length - 1] : null;

  const currentG = twinData?.latest_glucose != null
    ? twinData.latest_glucose.toFixed(1)
    : latestGlucose ? latestGlucose.value.toFixed(1) : null;

  const mean1h = twinData?.mean_glucose_1h != null ? twinData.mean_glucose_1h.toFixed(1) : null;
  const mean24h = twinData?.mean_glucose_24h != null ? twinData.mean_glucose_24h.toFixed(1) : null;
  const min24h = twinData?.min_glucose_24h != null ? twinData.min_glucose_24h.toFixed(1) : null;
  const max24h = twinData?.max_glucose_24h != null ? twinData.max_glucose_24h.toFixed(1) : null;
  const change1h = twinData?.glucose_change_1h != null ? twinData.glucose_change_1h.toFixed(1) : null;
  const std1h = twinData?.glucose_std_1h != null ? twinData.glucose_std_1h.toFixed(1) : null;
  const slope = twinData?.glucose_trend_slope != null ? twinData.glucose_trend_slope.toFixed(3) : null;

  const hr = twinData?.latest_heart_rate != null
    ? twinData.latest_heart_rate.toFixed(0)
    : latestVital && latestVital.heart_rate != null ? latestVital.heart_rate.toFixed(0) : null;

  const hrv = twinData?.latest_hrv != null
    ? twinData.latest_hrv.toFixed(1)
    : latestVital && latestVital.hrv != null ? latestVital.hrv.toFixed(1) : null;

  return (
    <div className="section-container digital-twin-container" id={`twin-panel-${panelId}`}>
      {/* Header Banner */}
      <div className="section-header-banner">
        <div>
          <div className="section-title-row">
            <h2 className="section-title">Patient Digital Twin Intelligence</h2>
            <span className="badge badge-twin">Twin ID: DT-00{selectedPatient.id}</span>
            <span className="badge badge-neutral">State: Synchronized</span>
          </div>
          <p className="section-desc">
            Virtual replica synthesizing demographic phenotype, continuous telemetry vectors, baseline comparisons, and live risk states.
          </p>
        </div>
      </div>

      {/* Distinction Notice */}
      <div className="telemetry-notice-box">
        <div className="notice-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2a4 4 0 0 1 4 4v1a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4z" />
            <path d="M16 11a4 4 0 0 1 4 4v1a4 4 0 0 1-8 0v-1a4 4 0 0 1 4-4z" />
            <circle cx="12" cy="12" r="10" />
          </svg>
        </div>
        <div className="notice-content">
          <strong className="notice-title">Twin Synchronization: Multi-Vector Aggregation</strong>
          <p className="notice-text">
            This replica continuously tracks physiological deviations from the patient's 24-hour historical baseline.
            <em> Non-diagnostic research prototype. Telemetry is sourced from synthetic models.</em>
          </p>
        </div>
      </div>

      {isLoading && (
        <div style={{ padding: '30px 0' }}>
          <LoadingSpinner message={`Synchronizing Digital Twin DT-00${selectedPatient.id}...`} />
        </div>
      )}

      {error && !isLoading && (
        <div className="twin-error-note">
          <span>Note: Real-time twin metrics calculated from client telemetry buffer ({error})</span>
        </div>
      )}

      {!isLoading && (
        <div className="twin-grid">
          {/* Card 1: Phenotype Profile Vector */}
          <div className="twin-card">
            <h3 className="twin-card-heading">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
              Phenotype Profile Vector
            </h3>

            <div className="twin-param-list">
              <div className="twin-param-row">
                <span className="param-label">Target Subject</span>
                <span className="param-value">{selectedPatient.name}</span>
              </div>
              <div className="twin-param-row">
                <span className="param-label">Clinical Type</span>
                <span className="param-value highlight-cyan">{selectedPatient.diabetes_type}</span>
              </div>
              <div className="twin-param-row">
                <span className="param-label">Age &amp; Sex</span>
                <span className="param-value">{selectedPatient.age} yrs &bull; {selectedPatient.gender}</span>
              </div>
              <div className="twin-param-row">
                <span className="param-label">Progression Span</span>
                <span className="param-value">{selectedPatient.years_since_diagnosis} years</span>
              </div>
              <div className="twin-param-row">
                <span className="param-label">Physical Scale</span>
                <span className="param-value">
                  {selectedPatient.weight_kg ? `${selectedPatient.weight_kg} kg` : 'N/A'} /{' '}
                  {selectedPatient.height_cm ? `${selectedPatient.height_cm} cm` : 'N/A'}
                  {twinData?.bmi && ` (BMI: ${twinData.bmi})`}
                </span>
              </div>
            </div>
          </div>

          {/* Card 2: Observed Physiological State & Baseline Comparison */}
          <div className="twin-card">
            <h3 className="twin-card-heading">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
              </svg>
              Telemetry &amp; Baseline Delta
            </h3>

            <div className="twin-param-list">
              <div className="twin-param-row">
                <span className="param-label">Latest Glucose</span>
                <span className="param-value highlight-cyan">
                  {currentG ? `${currentG} mg/dL` : <span className="missing-val">No reading</span>}
                  {twinData?.latest_glucose_timestamp && (
                    <span className="baseline-sub"> ({formatTimestamp(twinData.latest_glucose_timestamp)})</span>
                  )}
                </span>
              </div>
              <div className="twin-param-row">
                <span className="param-label">1h Mean vs 24h Baseline</span>
                <span className="param-value">
                  {mean1h ? `${mean1h} mg/dL` : '--'}
                  {mean24h && (
                    <span className="baseline-sub"> (24h avg: {mean24h} mg/dL)</span>
                  )}
                </span>
              </div>
              <div className="twin-param-row">
                <span className="param-label">24h Extrema (Min &ndash; Max)</span>
                <span className="param-value">
                  {min24h && max24h ? `${min24h} – ${max24h} mg/dL` : '--'}
                </span>
              </div>
              <div className="twin-param-row">
                <span className="param-label">1h Trajectory Delta (&Delta;)</span>
                <span className="param-value">
                  {change1h != null ? (
                    <span className={Number(change1h) > 0 ? 'highlight-warning' : 'highlight-cyan'}>
                      {Number(change1h) > 0 ? `+${change1h}` : change1h} mg/dL
                    </span>
                  ) : '--'}
                </span>
              </div>
              <div className="twin-param-row">
                <span className="param-label">Glycemic Variability (&sigma;)</span>
                <span className="param-value">
                  {std1h ? `±${std1h} mg/dL` : '--'}
                </span>
              </div>
              <div className="twin-param-row">
                <span className="param-label">Trend Trajectory (Slope)</span>
                <span className="param-value">
                  {slope != null ? `${slope > 0 ? '+' : ''}${slope} mg/dL/min` : '--'}
                </span>
              </div>
              <div className="twin-param-row">
                <span className="param-label">Autonomic Signals</span>
                <span className="param-value">
                  {hr ? `${hr} bpm` : <span className="missing-val">HR N/A</span>} &bull;{' '}
                  {hrv ? `${hrv} ms` : <span className="missing-val">HRV N/A</span>}
                </span>
              </div>
            </div>
          </div>

          {/* Card 3: Live Surveillance & Model Forecast Vector */}
          <div className="twin-card">
            <h3 className="twin-card-heading">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                <path d="M13.73 21a2 2 0 0 1-3.46 0" />
              </svg>
              Twin Surveillance &amp; Forecast
            </h3>

            <div className="twin-param-list">
              <div className="twin-param-row">
                <span className="param-label">Active Clinical Alerts</span>
                <span className="param-value">
                  {twinData?.active_alerts_count != null ? (
                    <span className={twinData.active_alerts_count > 0 ? 'highlight-critical' : 'highlight-normal'}>
                      {twinData.active_alerts_count} Active
                      {twinData.alert_severity_distribution && (twinData.alert_severity_distribution.critical > 0 || twinData.alert_severity_distribution.warning > 0) ? (
                        <span className="baseline-sub">
                          {' '}({twinData.alert_severity_distribution.critical || 0} crit, {twinData.alert_severity_distribution.warning || 0} warn)
                        </span>
                      ) : ''}
                    </span>
                  ) : '--'}
                </span>
              </div>
              <div className="twin-param-row">
                <span className="param-label">Telemetry Freshness</span>
                <span className="param-value">
                  {twinData?.data_freshness_status === 'stale' ? (
                    <span className="badge badge-warning" style={{ fontSize: '0.72rem' }}>STALE TELEMETRY</span>
                  ) : twinData?.data_freshness_status === 'no_data' ? (
                    <span className="badge badge-critical" style={{ fontSize: '0.72rem' }}>NO TELEMETRY</span>
                  ) : (
                    <span className="badge badge-normal" style={{ fontSize: '0.72rem' }}>SYNCHRONIZED</span>
                  )}
                </span>
              </div>
              <div className="twin-param-row">
                <span className="param-label">24h Telemetry Coverage</span>
                <span className="param-value">
                  {twinData?.total_readings_24h != null
                    ? `${twinData.total_readings_24h} sensor readings`
                    : `${glucoseReadings.length} readings`}
                </span>
              </div>
              <div className="twin-param-row">
                <span className="param-label">Forward Model Risk Score</span>
                <span className="param-value">
                  {twinData?.latest_prediction ? (
                    <>
                      <strong>{(twinData.latest_prediction.risk_score * 100).toFixed(1)}%</strong>
                      <span className="baseline-sub"> ({twinData.latest_prediction.risk_category} tier)</span>
                    </>
                  ) : 'Evaluated in Predictions Panel'}
                </span>
              </div>
              <div className="twin-param-row">
                <span className="param-label">Predicted Spike Status</span>
                <span className="param-value">
                  {twinData?.latest_prediction ? (
                    twinData.latest_prediction.spike_predicted ? (
                      <span className="badge badge-critical" style={{ fontSize: '0.72rem' }}>SPIKE RISK</span>
                    ) : (
                      <span className="badge badge-normal" style={{ fontSize: '0.72rem' }}>STABLE RANGE</span>
                    )
                  ) : '--'}
                </span>
              </div>
              <div className="twin-param-row">
                <span className="param-label">Data Quality Status</span>
                <span className="param-value">
                  {twinData?.data_quality_warnings && twinData.data_quality_warnings.length > 0 ? (
                    <span className="text-warning">{twinData.data_quality_warnings.length} Quality Warnings</span>
                  ) : (
                    <span className="text-normal">Complete Profile</span>
                  )}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Warnings strip if any exist */}
      {twinData?.data_quality_warnings && twinData.data_quality_warnings.length > 0 && (
        <div className="twin-warnings-box">
          <strong>Telemetry Notice:</strong>
          <ul>
            {twinData.data_quality_warnings.map((w, idx) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
