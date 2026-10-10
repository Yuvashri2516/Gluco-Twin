import React from 'react';

export default function WhatIfSimulation({ selectedPatient }) {
  return (
    <div className="section-container simulation-container">
      <div className="section-header-banner">
        <div>
          <div className="section-title-row">
            <h2 className="section-title">What-If Counterfactual Simulation</h2>
            <span className="badge badge-twin">Digital Twin Sandbox</span>
          </div>
          <p className="section-desc">
            Virtual scenario testing for synthetic meal intake perturbations, physical activity, and insulin timing.
          </p>
        </div>
      </div>

      <div className="unimplemented-feature-card">
        <div className="unimplemented-icon-box" style={{ color: 'var(--status-twin)' }}>
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
        </div>

        <h3 className="unimplemented-title">What-if simulation engine is planned for a future phase</h3>

        <p className="unimplemented-lead">
          Counterfactual physiological modeling requires calibrated ODE / compartmental metabolic equations or trained generative dynamics. This capability is currently under design.
        </p>

        <div className="pipeline-preview-box">
          <h4 className="preview-heading">Planned Counterfactual Scenarios:</h4>
          <ul className="preview-list">
            <li>
              <strong>Postprandial Carbohydrate Perturbation:</strong> Simulate impact of +30g or +60g carbohydrates on peak glucose latency and magnitude.
            </li>
            <li>
              <strong>Physical Exertion Response:</strong> Model acute exercise-induced insulin sensitivity and muscular glucose uptake.
            </li>
            <li>
              <strong>Basal / Bolus Insulin Timing:</strong> Evaluate delay vs. pre-bolus effects on excursion reduction.
            </li>
          </ul>
        </div>

        <div className="integrity-note">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>
            <strong>Disclaimer:</strong> Any future simulation tools are strictly exploratory research prototypes and do not claim causal, deterministic, or clinically validated prescriptive validity.
          </span>
        </div>
      </div>
    </div>
  );
}
