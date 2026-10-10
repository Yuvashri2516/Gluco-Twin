import React from 'react';
import { User, Bell, Activity, Database } from 'lucide-react';

/**
 * Global Top Navigation Bar
 */
export default function TopNav({
  patients = [],
  activePatientId,
  onSelectPatient,
  unreadAlertCount = 2,
  onAlertClick
}) {
  const activePatient = patients.find((p) => p.id === activePatientId) || patients[0];

  return (
    <header className="top-nav">
      <div className="top-nav-left">
        <div className="patient-selector-box">
          <div className="patient-avatar">
            <User size={16} />
          </div>
          <div>
            <select
              className="patient-dropdown-select"
              value={activePatientId}
              onChange={(e) => onSelectPatient(e.target.value)}
              aria-label="Select Patient Archetype"
            >
              {patients.map((pt) => (
                <option key={pt.id} value={pt.id}>
                  {pt.name} ({pt.id}) — {pt.archetype.split('(')[0].trim()}
                </option>
              ))}
            </select>
          </div>
        </div>

        {activePatient && (
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-navy-500)', display: 'inline-flex', gap: 8 }}>
            <span>Age: <strong>{activePatient.age}</strong></span>
            <span>•</span>
            <span>BMI: <strong>{activePatient.bmi}</strong></span>
          </span>
        )}
      </div>

      <div className="top-nav-right">
        <div className="status-chip success">
          <span className="pulse-dot" />
          <span>Twin Synced (12ms)</span>
        </div>

        <div className="status-chip mock">
          <Database size={13} />
          <span>Synthetic Mode</span>
        </div>

        <button
          className="icon-button"
          onClick={onAlertClick}
          title="Clinical Alerts"
          aria-label="Clinical Alerts"
        >
          <Bell size={18} />
          {unreadAlertCount > 0 && <span className="badge-counter">{unreadAlertCount}</span>}
        </button>
      </div>
    </header>
  );
}
