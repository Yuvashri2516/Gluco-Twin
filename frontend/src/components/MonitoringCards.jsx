import React from 'react';

function formatTimestamp(isoString) {
  if (!isoString) return '--';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    return d.toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoString;
  }
}

export default function MonitoringCards({
  glucoseReadings = [],
  vitalReadings = [],
  isLoading,
}) {
  // Latest readings are at the end of chronologically sorted readings
  const latestGlucose = glucoseReadings.length > 0
    ? glucoseReadings[glucoseReadings.length - 1]
    : null;

  const latestVital = vitalReadings.length > 0
    ? vitalReadings[vitalReadings.length - 1]
    : null;

  // Determine glucose status
  let glucoseBadge = { label: 'No Reading', class: 'badge-neutral' };
  if (latestGlucose) {
    const val = latestGlucose.value;
    if (val < 70) {
      glucoseBadge = { label: 'Hypoglycemic Risk (<70)', class: 'badge-critical' };
    } else if (val > 180) {
      glucoseBadge = { label: 'Elevated (>180)', class: 'badge-warning' };
    } else {
      glucoseBadge = { label: 'In Target (70-180)', class: 'badge-normal' };
    }
  }

  // Determine heart rate status
  let hrBadge = { label: 'No Reading', class: 'badge-neutral' };
  if (latestVital && latestVital.heart_rate != null) {
    const hr = latestVital.heart_rate;
    if (hr < 60) {
      hrBadge = { label: 'Bradycardia (<60)', class: 'badge-warning' };
    } else if (hr > 100) {
      hrBadge = { label: 'Tachycardia (>100)', class: 'badge-warning' };
    } else {
      hrBadge = { label: 'Normal Resting', class: 'badge-normal' };
    }
  }

  // Check if HRV is provided
  const hasHrv = latestVital && latestVital.hrv != null;

  return (
    <div className="monitoring-cards-grid">
      {/* 1. Glucose Card */}
      <div className="monitor-card glucose-card">
        <div className="monitor-card-header">
          <div className="monitor-icon-wrapper glucose-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
            </svg>
          </div>
          <span className="monitor-card-title">Latest Glucose</span>
          <span className={`badge ${glucoseBadge.class}`}>{glucoseBadge.label}</span>
        </div>

        <div className="monitor-card-body">
          {latestGlucose ? (
            <>
              <div className="monitor-value-row">
                <span className="monitor-main-value">{latestGlucose.value.toFixed(1)}</span>
                <span className="monitor-unit">mg/dL</span>
              </div>
              <div className="monitor-meta-row">
                <span className="monitor-timestamp">
                  Observed: {formatTimestamp(latestGlucose.timestamp)}
                </span>
                <span className="monitor-data-type">Recorded CGM</span>
              </div>
            </>
          ) : (
            <div className="monitor-empty-reading">
              {isLoading ? 'Fetching glucose...' : 'No readings recorded'}
            </div>
          )}
        </div>
      </div>

      {/* 2. Heart Rate Card */}
      <div className="monitor-card vitals-card">
        <div className="monitor-card-header">
          <div className="monitor-icon-wrapper heart-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
          </div>
          <span className="monitor-card-title">Heart Rate</span>
          <span className={`badge ${hrBadge.class}`}>{hrBadge.label}</span>
        </div>

        <div className="monitor-card-body">
          {latestVital && latestVital.heart_rate != null ? (
            <>
              <div className="monitor-value-row">
                <span className="monitor-main-value">{latestVital.heart_rate.toFixed(1)}</span>
                <span className="monitor-unit">bpm</span>
              </div>
              <div className="monitor-meta-row">
                <span className="monitor-timestamp">
                  Observed: {formatTimestamp(latestVital.timestamp)}
                </span>
                <span className="monitor-data-type">Recorded Vitals</span>
              </div>
            </>
          ) : (
            <div className="monitor-empty-reading">
              {isLoading ? 'Fetching heart rate...' : 'No readings recorded'}
            </div>
          )}
        </div>
      </div>

      {/* 3. HRV Card (rendered only if provided) */}
      {hasHrv && (
        <div className="monitor-card hrv-card">
          <div className="monitor-card-header">
            <div className="monitor-icon-wrapper hrv-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
              </svg>
            </div>
            <span className="monitor-card-title">HR Variability (HRV)</span>
            <span className="badge badge-twin">Autonomic Metric</span>
          </div>

          <div className="monitor-card-body">
            <div className="monitor-value-row">
              <span className="monitor-main-value">{latestVital.hrv.toFixed(1)}</span>
              <span className="monitor-unit">ms</span>
            </div>
            <div className="monitor-meta-row">
              <span className="monitor-timestamp">
                Observed: {formatTimestamp(latestVital.timestamp)}
              </span>
              <span className="monitor-data-type">RMSSD / SDNN</span>
            </div>
          </div>
        </div>
      )}

      {/* 4. Sensor Coverage Card */}
      <div className="monitor-card coverage-card">
        <div className="monitor-card-header">
          <div className="monitor-icon-wrapper sensor-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
              <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
            </svg>
          </div>
          <span className="monitor-card-title">Sensor Activity</span>
          <span className="badge badge-normal">Active Sync</span>
        </div>

        <div className="monitor-card-body">
          <div className="coverage-stats-row">
            <div className="coverage-stat">
              <span className="cov-num">{glucoseReadings.length}</span>
              <span className="cov-text">Glucose Points</span>
            </div>
            <div className="coverage-stat">
              <span className="cov-num">{vitalReadings.length}</span>
              <span className="cov-text">Vitals Points</span>
            </div>
          </div>
          <div className="monitor-meta-row" style={{ marginTop: '10px' }}>
            <span className="monitor-data-type">Sampling rate: 15-min intervals</span>
          </div>
        </div>
      </div>
    </div>
  );
}
