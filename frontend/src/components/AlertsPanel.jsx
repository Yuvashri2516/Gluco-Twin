import React from 'react';

export default function AlertsPanel() {
  return (
    <div className="section-container alerts-container">
      <div className="section-header-banner">
        <div>
          <div className="section-title-row">
            <h2 className="section-title">Clinical Risk Alerts</h2>
            <span className="badge badge-neutral">Rule &amp; Model Engine</span>
          </div>
          <p className="section-desc">
            Notification dispatcher for threshold breaches, nocturnal dips, and rapid glycemic rate-of-change.
          </p>
        </div>
      </div>

      <div className="unimplemented-feature-card">
        <div className="unimplemented-icon-box" style={{ color: 'var(--status-warning)' }}>
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
        </div>

        <h3 className="unimplemented-title">Automated alert engine is not yet implemented</h3>

        <p className="unimplemented-lead">
          The alert generation and triage workflow will be hooked into the backend once the Phase 3 prediction models and alerting rules are operational.
        </p>

        <div className="pipeline-preview-box">
          <h4 className="preview-heading">Target Notification Dispatch Schema:</h4>
          <div className="alert-criteria-grid">
            <div className="criteria-item">
              <span className="badge badge-critical">Critical Severity</span>
              <p className="criteria-desc">Active severe hypoglycemia (&lt; 54 mg/dL) or rapid downward trajectory.</p>
            </div>
            <div className="criteria-item">
              <span className="badge badge-warning">High Severity</span>
              <p className="criteria-desc">Sustained postprandial glucose spike (&gt; 250 mg/dL) lasting over 2 hours.</p>
            </div>
            <div className="criteria-item">
              <span className="badge badge-twin">Twin Warning</span>
              <p className="criteria-desc">Elevated heart rate coupled with sudden autonomic HRV depression.</p>
            </div>
          </div>
        </div>

        <div className="integrity-note">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>
            No fabricated warnings or mock emergency alarms are generated. The system prioritizes genuine medical software integrity.
          </span>
        </div>
      </div>
    </div>
  );
}
