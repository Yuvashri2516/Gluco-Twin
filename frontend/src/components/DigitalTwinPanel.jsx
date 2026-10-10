import React from 'react';

export default function DigitalTwinPanel({
  selectedPatient,
  glucoseReadings = [],
  vitalReadings = [],
}) {
  if (!selectedPatient) return null;

  const latestGlucose = glucoseReadings.length > 0
    ? glucoseReadings[glucoseReadings.length - 1]
    : null;

  const latestVital = vitalReadings.length > 0
    ? vitalReadings[vitalReadings.length - 1]
    : null;

  // Compute basic baseline summary stats from current observed time series
  const glucoseValues = glucoseReadings.map((r) => r.value);
  const avgGlucose = glucoseValues.length > 0
    ? (glucoseValues.reduce((a, b) => a + b, 0) / glucoseValues.length).toFixed(1)
    : '--';

  const variance = glucoseValues.length > 1
    ? (glucoseValues.reduce((acc, val) => acc + Math.pow(val - avgGlucose, 2), 0) / (glucoseValues.length - 1))
    : 0;
  const stdDev = Math.sqrt(variance).toFixed(1);

  return (
    <div className="section-container digital-twin-container">
      <div className="section-header-banner">
        <div>
          <div className="section-title-row">
            <h2 className="section-title">Digital Twin Snapshot</h2>
            <span className="badge badge-twin">Twin ID: DT-00{selectedPatient.id}</span>
          </div>
          <p className="section-desc">
            Virtual physiological replica aggregating recorded time-series parameters and patient demographics.
          </p>
        </div>
      </div>

      {/* Explicit Distinction Notice */}
      <div className="telemetry-notice-box">
        <div className="notice-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
        </div>
        <div className="notice-content">
          <strong className="notice-title">Telemetry Mode: Recorded &amp; Simulated Telemetry Only</strong>
          <p className="notice-text">
            All parameters displayed below reflect verified sensor telemetry from the backend SQLite database.
            <strong> Forward-looking predictions and clinical risk estimations are NOT active in this snapshot.</strong>
          </p>
        </div>
      </div>

      <div className="twin-grid">
        {/* Patient Profile Vector */}
        <div className="twin-card">
          <h3 className="twin-card-heading">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
            Phenotype Vector
          </h3>

          <div className="twin-param-list">
            <div className="twin-param-row">
              <span className="param-label">Patient Subject</span>
              <span className="param-value">{selectedPatient.name}</span>
            </div>
            <div className="twin-param-row">
              <span className="param-label">Clinical Category</span>
              <span className="param-value">{selectedPatient.diabetes_type}</span>
            </div>
            <div className="twin-param-row">
              <span className="param-label">Age &amp; Sex</span>
              <span className="param-value">{selectedPatient.age} yrs &bull; {selectedPatient.gender}</span>
            </div>
            <div className="twin-param-row">
              <span className="param-label">Disease Progression</span>
              <span className="param-value">{selectedPatient.years_since_diagnosis} years</span>
            </div>
            <div className="twin-param-row">
              <span className="param-label">Physiological Scale</span>
              <span className="param-value">
                {selectedPatient.weight_kg ? `${selectedPatient.weight_kg} kg` : 'N/A'} /{' '}
                {selectedPatient.height_cm ? `${selectedPatient.height_cm} cm` : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Dynamic Telemetry Snapshot */}
        <div className="twin-card">
          <h3 className="twin-card-heading">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
            Observed Physiological State
          </h3>

          <div className="twin-param-list">
            <div className="twin-param-row">
              <span className="param-label">Most Recent Glucose</span>
              <span className="param-value highlight-cyan">
                {latestGlucose ? `${latestGlucose.value.toFixed(1)} mg/dL` : 'No reading'}
              </span>
            </div>
            <div className="twin-param-row">
              <span className="param-label">Window Mean Glucose</span>
              <span className="param-value">{avgGlucose} mg/dL</span>
            </div>
            <div className="twin-param-row">
              <span className="param-label">Glucose Variability (&sigma;)</span>
              <span className="param-value">&plusmn;{stdDev} mg/dL</span>
            </div>
            <div className="twin-param-row">
              <span className="param-label">Resting Heart Rate</span>
              <span className="param-value">
                {latestVital && latestVital.heart_rate != null
                  ? `${latestVital.heart_rate.toFixed(1)} bpm`
                  : 'N/A'}
              </span>
            </div>
            <div className="twin-param-row">
              <span className="param-label">Autonomic Metric (HRV)</span>
              <span className="param-value">
                {latestVital && latestVital.hrv != null
                  ? `${latestVital.hrv.toFixed(1)} ms`
                  : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
