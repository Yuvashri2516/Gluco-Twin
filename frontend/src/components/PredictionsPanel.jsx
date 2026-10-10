import React from 'react';

export default function PredictionsPanel({ selectedPatient }) {
  return (
    <div className="section-container predictions-container">
      <div className="section-header-banner">
        <div>
          <div className="section-title-row">
            <h2 className="section-title">Glucose Spike &amp; Hypoglycemia Prediction</h2>
            <span className="badge badge-neutral">Phase 3 Milestone</span>
          </div>
          <p className="section-desc">
            Machine learning inference engine for estimating future glucose fluctuations and spike likelihood.
          </p>
        </div>
      </div>

      <div className="unimplemented-feature-card">
        <div className="unimplemented-icon-box">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="1.8">
            <line x1="18" y1="20" x2="18" y2="10" />
            <line x1="12" y1="20" x2="12" y2="4" />
            <line x1="6" y1="20" x2="6" y2="14" />
            <circle cx="12" cy="4" r="2" />
          </svg>
        </div>

        <h3 className="unimplemented-title">Predictive model not yet implemented</h3>

        <p className="unimplemented-lead">
          The Phase 2 frontend connects directly to recorded telemetry. Forward-looking risk scores, spike probability estimations, and model explanations are reserved for Phase 3.
        </p>

        <div className="pipeline-preview-box">
          <h4 className="preview-heading">Planned Phase 3 ML Architecture:</h4>
          <ul className="preview-list">
            <li>
              <strong>Feature Extraction:</strong> Rolling 1h/3h window averages, rate of change (slope mg/dL/min), glycemic variability, and circadian rhythm phase.
            </li>
            <li>
              <strong>Multimodal Inputs:</strong> Time-synchronized heart rate and HRV autonomic metrics.
            </li>
            <li>
              <strong>Model Pipeline:</strong> Supervised binary &amp; multiclass classifiers (scikit-learn) trained on synthetic patient CGM datasets.
            </li>
            <li>
              <strong>Clinician Explainability:</strong> Honest SHAP feature attribution without clinical overclaim.
            </li>
          </ul>
        </div>

        <div className="integrity-note">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
          <span>
            Strict prototype integrity: No mock risk scores, fake accuracy percentages, or simulated clinical recommendations are shown.
          </span>
        </div>
      </div>
    </div>
  );
}
