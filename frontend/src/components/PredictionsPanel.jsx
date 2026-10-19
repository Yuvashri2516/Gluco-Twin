import React, { useState, useEffect, useCallback, useId } from 'react';
import { predictGlucoseSpike, API_BASE_URL } from '../api/client';
import LoadingSpinner from './Common/LoadingSpinner';

const FEATURE_LABELS = {
  curr_glucose: 'Current Glucose Level',
  mean_glucose_1h: '1-Hour Mean Glucose',
  std_glucose_1h: '1-Hour Glucose Variability (Std Dev)',
  slope_glucose_1h: '1-Hour Glucose Rate of Change (Slope)',
  curr_hr: 'Current Heart Rate',
  curr_hrv: 'Current Heart Rate Variability (HRV)',
  mean_hr_1h: '1-Hour Mean Heart Rate',
  mean_hrv_1h: '1-Hour Mean HRV',
  circadian_sin: 'Circadian Rhythm (Sine component)',
  circadian_cos: 'Circadian Rhythm (Cosine component)',
  age: 'Patient Age',
  years_diagnosis: 'Years Since Diagnosis',
  is_type1: 'Type 1 Diabetes Indicator',
  is_prediabetes: 'Prediabetes Indicator',
};

function formatFeatureName(key) {
  if (FEATURE_LABELS[key]) return FEATURE_LABELS[key];
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatTimestamp(timestampStr) {
  if (!timestampStr) return '--';
  try {
    const d = new Date(timestampStr);
    if (isNaN(d.getTime())) return String(timestampStr);
    return d.toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZoneName: 'short',
    });
  } catch {
    return String(timestampStr);
  }
}

export default function PredictionsPanel({ selectedPatient }) {
  const [prediction, setPrediction] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorInfo, setErrorInfo] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const uniqueId = useId();

  const handleRetry = useCallback(() => {
    setRefreshTrigger((prev) => prev + 1);
  }, []);

  const patientId = selectedPatient?.id;
  const patientName = selectedPatient?.name;

  useEffect(() => {
    if (!patientId) {
      return;
    }

    let isCurrent = true;
    const controller = new AbortController();

    async function executePrediction() {
      // Clear previous states and start loading
      setIsLoading(true);
      setPrediction(null);
      setErrorInfo(null);

      try {
        const data = await predictGlucoseSpike(patientId, controller.signal);
        if (isCurrent) {
          setPrediction(data);
          setErrorInfo(null);
        }
      } catch (err) {
        if (err.name === 'AbortError') {
          return;
        }
        if (isCurrent) {
          setPrediction(null);
          // Parse structured error attributes
          const status = err.status || (err.message && err.message.match(/\((\d{3})\)/)?.[1]);
          const detail = err.detail || err.message || 'Unknown network or service error';

          let errorType = 'UNKNOWN';
          let userTitle = 'Prediction Service Error';
          let userHelper = 'The prediction request failed. Please check the backend connection and retry.';

          if (Number(status) === 503) {
            errorType = 'MODEL_UNAVAILABLE';
            userTitle = 'Model Artifact Unavailable (503)';
            userHelper = 'The prediction model artifact is not loaded on the backend. Ensure the ML pipeline has been executed (python -m app.ml.train).';
          } else if (Number(status) === 422) {
            errorType = 'INSUFFICIENT_DATA';
            userTitle = 'Insufficient Patient History / Not Validated for this Patient';
            userHelper = 'The predictive model requires at least 1 hour of continuous sensor telemetry to calculate glycemic rate-of-change, variance, and circadian features. This newly registered or empty patient profile does not yet have enough readings. Please add manual readings or upload a CGM sensor export in the Medical Documents tab to activate predictions.';
          } else if (Number(status) === 404) {
            errorType = 'PATIENT_NOT_FOUND';
            userTitle = 'Patient Record Not Found (404)';
            userHelper = `Patient record #${patientId} was not found in the database.`;
          } else if (!navigator.onLine || err.message?.toLowerCase().includes('failed to fetch')) {
            errorType = 'NETWORK_OFFLINE';
            userTitle = 'Backend API Unreachable';
            userHelper = `Unable to connect to the prediction API at ${API_BASE_URL}. Ensure the FastAPI server is running.`;
          }

          setErrorInfo({
            type: errorType,
            status: status || null,
            title: userTitle,
            detail,
            helper: userHelper,
          });
        }
      } finally {
        if (isCurrent) {
          setIsLoading(false);
        }
      }
    }

    executePrediction();

    return () => {
      isCurrent = false;
      controller.abort();
    };
  }, [patientId, patientName, refreshTrigger]);

  // Separate positive and negative feature contributions if provided
  const featureContributions = prediction?.feature_contributions || null;
  const contributionEntries = featureContributions
    ? Object.entries(featureContributions)
    : [];

  const positiveContributions = contributionEntries
    .filter(([, val]) => typeof val === 'number' && val > 0)
    .sort(([, a], [, b]) => b - a);

  const negativeContributions = contributionEntries
    .filter(([, val]) => typeof val === 'number' && val < 0)
    .sort(([, a], [, b]) => a - b);

  // Maximum absolute contribution value for proportional bar scaling
  const maxAbsContrib = contributionEntries.reduce(
    (acc, [, val]) => Math.max(acc, Math.abs(val || 0)),
    0.001
  );

  return (
    <div className="section-container predictions-container" id={`prediction-panel-${uniqueId}`}>
      {/* Section Header */}
      <div className="section-header-banner">
        <div className="predictions-header-row">
          <div>
            <div className="section-title-row">
              <h2 className="section-title">Glucose Spike Prediction Engine</h2>
              <span className="badge badge-twin">Forward Horizon: 2h</span>
              {prediction?.model_version && (
                <span className="badge badge-neutral">Model {prediction.model_version}</span>
              )}
            </div>
            <p className="section-desc">
              Supervised machine learning inference predicting whether glucose will breach 180 mg/dL within the forward 2-hour window.
            </p>
          </div>

          {selectedPatient && !isLoading && (
            <button
              type="button"
              className="prediction-action-btn"
              onClick={handleRetry}
              title="Re-run inference for active patient"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="23 4 23 10 17 10" />
                <polyline points="1 20 1 14 7 14" />
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
              </svg>
              <span>Re-run Inference</span>
            </button>
          )}
        </div>
      </div>

      {/* STATE 1: No patient selected */}
      {!selectedPatient && (
        <div className="prediction-state-card empty-state-card">
          <div className="state-icon-box">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </div>
          <h3 className="state-title">No Patient Selected</h3>
          <p className="state-desc">
            Please choose a patient from the roster above to compute forward-looking glucose spike predictions.
          </p>
        </div>
      )}

      {/* STATE 2: Loading State */}
      {selectedPatient && isLoading && (
        <div className="prediction-state-card loading-state-card">
          <LoadingSpinner
            message={`Running ML inference for ${selectedPatient.name} (Patient #${selectedPatient.id})...`}
          />
          <p className="loading-subtext">
            Extracting 1-hour and 24-hour historical telemetry without lookahead leakage.
          </p>
        </div>
      )}

      {/* STATE 3: Error State */}
      {selectedPatient && !isLoading && errorInfo && (
        <div className="prediction-state-card error-state-card">
          <div className="error-icon-box">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
          <h3 className="error-state-title">{errorInfo.title}</h3>
          <p className="error-state-detail">{errorInfo.detail}</p>
          <p className="error-state-helper">{errorInfo.helper}</p>

          <button
            type="button"
            className="error-retry-btn"
            onClick={handleRetry}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 4 23 10 17 10" />
              <polyline points="1 20 1 14 7 14" />
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
            </svg>
            <span>Retry Prediction</span>
          </button>
        </div>
      )}

      {/* STATE 4: Successful Prediction */}
      {selectedPatient && !isLoading && !errorInfo && prediction && (
        <div className="prediction-results-wrapper">
          {/* Main Prediction Hero Card */}
          <div className={`prediction-hero-card ${prediction.spike_predicted ? 'hero-spike' : 'hero-safe'}`}>
            <div className="hero-top-row">
              <div className="hero-status-group">
                <span className={`status-pill ${prediction.spike_predicted ? 'pill-critical' : 'pill-normal'}`}>
                  {prediction.spike_predicted ? (
                    <>
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                        <line x1="12" y1="9" x2="12" y2="13" />
                        <line x1="12" y1="17" x2="12.01" y2="17" />
                      </svg>
                      <strong>GLUCOSE SPIKE PREDICTED</strong>
                    </>
                  ) : (
                    <>
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                        <polyline points="22 4 12 14.01 9 11.01" />
                      </svg>
                      <strong>NO SPIKE PREDICTED</strong>
                    </>
                  )}
                </span>
                <span className="hero-status-subtitle">
                  {prediction.spike_predicted
                    ? `Estimated to cross threshold (≥ ${prediction.threshold_mg_dl || 180} mg/dL) within ${prediction.horizon_minutes || 120} minutes`
                    : `Estimated to remain below threshold (< ${prediction.threshold_mg_dl || 180} mg/dL) within ${prediction.horizon_minutes || 120} minutes`}
                </span>
              </div>

              {/* Backend Risk Tier Badge */}
              {prediction.risk_category && (
                <div className="hero-risk-tier-box">
                  <span className="risk-tier-label">Backend Risk Tier</span>
                  <span
                    className={`badge ${
                      prediction.risk_category === 'HIGH'
                        ? 'badge-critical'
                        : prediction.risk_category === 'MODERATE'
                        ? 'badge-warning'
                        : 'badge-normal'
                    }`}
                  >
                    {prediction.risk_category}
                  </span>
                </div>
              )}
            </div>

            {/* Score & Parameters Strip */}
            <div className="hero-metrics-grid">
              {/* Uncalibrated Model Score */}
              <div className="metric-box score-box">
                <span className="metric-box-label">Uncalibrated Model Score</span>
                <div className="metric-box-score">
                  <span className="score-number">
                    {typeof prediction.risk_score === 'number'
                      ? prediction.risk_score.toFixed(4)
                      : '--'}
                  </span>
                  {typeof prediction.risk_score === 'number' && (
                    <span className="score-percentage">
                      ({(prediction.risk_score * 100).toFixed(1)}%)
                    </span>
                  )}
                </div>
                <span className="uncalibrated-caution">
                  *Uncalibrated model score. Not a clinically validated probability.
                </span>
              </div>

              {/* Prediction Horizon */}
              <div className="metric-box">
                <span className="metric-box-label">Prediction Horizon</span>
                <span className="metric-box-value">
                  {prediction.horizon_minutes
                    ? `${prediction.horizon_minutes / 60} hours (${prediction.horizon_minutes} min)`
                    : '2 hours'}
                </span>
                <span className="metric-box-sub">Forward evaluation window</span>
              </div>

              {/* Glycemic Spike Threshold */}
              <div className="metric-box">
                <span className="metric-box-label">Glycemic Threshold</span>
                <span className="metric-box-value highlight-cyan">
                  {prediction.threshold_mg_dl
                    ? `${prediction.threshold_mg_dl} mg/dL`
                    : '180.0 mg/dL'}
                </span>
                <span className="metric-box-sub">Level 1 Hyperglycemia cut-off</span>
              </div>

              {/* Patient Record */}
              <div className="metric-box">
                <span className="metric-box-label">Target Patient</span>
                <span className="metric-box-value">
                  {prediction.patient_name || selectedPatient.name}
                </span>
                <span className="metric-box-sub">Record #{prediction.patient_id || selectedPatient.id}</span>
              </div>

              {/* Prediction Timestamp */}
              <div className="metric-box">
                <span className="metric-box-label">Prediction Timestamp</span>
                <span className="metric-box-value time-val">
                  {formatTimestamp(prediction.prediction_timestamp)}
                </span>
                <span className="metric-box-sub">As-of telemetry timestamp</span>
              </div>

              {/* Model Status */}
              <div className="metric-box">
                <span className="metric-box-label">Model Status</span>
                <span className="metric-box-value status-val">
                  {prediction.model_status || 'TRAINED_PROTOTYPE'}
                </span>
                <span className="metric-box-sub">
                  Version: {prediction.model_version || '0.1.0-prototype'}
                </span>
              </div>
            </div>
          </div>

          {/* Data-Quality Warnings Banner */}
          {Array.isArray(prediction.data_quality_warnings) && prediction.data_quality_warnings.length > 0 && (
            <div className="data-warnings-panel">
              <div className="warnings-header">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                <strong>Telemetry Data-Quality Warnings ({prediction.data_quality_warnings.length})</strong>
              </div>
              <ul className="warnings-list">
                {prediction.data_quality_warnings.map((warn, idx) => (
                  <li key={`warn-${idx}`}>{warn}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Model Feature Contributions Section */}
          <div className="feature-contributions-section">
            <div className="contributions-header-block">
              <div>
                <h3 className="contributions-title">Model Feature Contributions</h3>
                <p className="contributions-lead">
                  Linear product of standardized inputs and model weights (<code>scaled_feature × coefficient</code>).
                  These describe the model's calculation, <strong>not biological causation</strong>.
                </p>
              </div>
            </div>

            {contributionEntries.length === 0 ? (
              <div className="contributions-empty-box">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="8" y1="12" x2="16" y2="12" />
                </svg>
                <p>No model feature contributions returned for this prediction run.</p>
              </div>
            ) : (
              <div className="contributions-grid">
                {/* Positive Contributions: Increasing Predicted Spike Risk */}
                <div className="contribution-column col-positive">
                  <div className="col-header">
                    <span className="col-indicator positive-indicator" />
                    <h4>Factors Increasing Spike Likelihood (+ weight)</h4>
                    <span className="count-tag">{positiveContributions.length}</span>
                  </div>

                  {positiveContributions.length === 0 ? (
                    <div className="sub-empty-note">No positive feature contributions.</div>
                  ) : (
                    <div className="contribution-items-list">
                      {positiveContributions.map(([featKey, featVal]) => {
                        const pct = Math.min(100, Math.round((Math.abs(featVal) / maxAbsContrib) * 100));
                        return (
                          <div key={featKey} className="contribution-item">
                            <div className="contrib-label-row">
                              <span className="contrib-name">{formatFeatureName(featKey)}</span>
                              <span className="contrib-val val-positive">+{featVal.toFixed(4)}</span>
                            </div>
                            <div className="contrib-bar-track">
                              <div
                                className="contrib-bar-fill bar-positive"
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                            <div className="contrib-meta-row">
                              <span className="raw-key">{featKey}</span>
                              {prediction.features_used?.[featKey] !== undefined && (
                                <span className="raw-val">
                                  Raw: {typeof prediction.features_used[featKey] === 'number'
                                    ? prediction.features_used[featKey].toFixed(2)
                                    : String(prediction.features_used[featKey])}
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Negative Contributions: Decreasing Predicted Spike Risk */}
                <div className="contribution-column col-negative">
                  <div className="col-header">
                    <span className="col-indicator negative-indicator" />
                    <h4>Factors Decreasing Spike Likelihood (- weight)</h4>
                    <span className="count-tag">{negativeContributions.length}</span>
                  </div>

                  {negativeContributions.length === 0 ? (
                    <div className="sub-empty-note">No negative feature contributions.</div>
                  ) : (
                    <div className="contribution-items-list">
                      {negativeContributions.map(([featKey, featVal]) => {
                        const pct = Math.min(100, Math.round((Math.abs(featVal) / maxAbsContrib) * 100));
                        return (
                          <div key={featKey} className="contribution-item">
                            <div className="contrib-label-row">
                              <span className="contrib-name">{formatFeatureName(featKey)}</span>
                              <span className="contrib-val val-negative">{featVal.toFixed(4)}</span>
                            </div>
                            <div className="contrib-bar-track">
                              <div
                                className="contrib-bar-fill bar-negative"
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                            <div className="contrib-meta-row">
                              <span className="raw-key">{featKey}</span>
                              {prediction.features_used?.[featKey] !== undefined && (
                                <span className="raw-val">
                                  Raw: {typeof prediction.features_used[featKey] === 'number'
                                    ? prediction.features_used[featKey].toFixed(2)
                                    : String(prediction.features_used[featKey])}
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Safety, Transparency & Clinical Disclaimer */}
          <div className="clinical-safety-card">
            <div className="safety-card-header">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
              <h4>Research Prototype &amp; Clinical Safety Transparency</h4>
            </div>

            {prediction.clinical_disclaimer && (
              <p className="backend-disclaimer-text">
                {prediction.clinical_disclaimer}
              </p>
            )}

            <div className="safety-guidelines-grid">
              <div className="guideline-item">
                <strong>Synthetic Patient Data</strong>
                <span>
                  Telemetry and clinical profiles are generated synthetically. They do not represent real-world medical records.
                </span>
              </div>
              <div className="guideline-item">
                <strong>Experimental Prototype</strong>
                <span>
                  This predictive pipeline is an academic demonstration and is not clinically validated or cleared by regulatory bodies.
                </span>
              </div>
              <div className="guideline-item">
                <strong>Non-Diagnostic Notice</strong>
                <span>
                  Model outputs must not be used for diagnosis, medical treatment, insulin dosing, or clinical decision-making.
                </span>
              </div>
              <div className="guideline-item">
                <strong>No Causation Implied</strong>
                <span>
                  Feature contributions explain model weights inside this linear model only; they do not imply biological cause and effect.
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
