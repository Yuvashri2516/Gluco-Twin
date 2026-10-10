import React from 'react';

export default function Topbar({
  patients = [],
  selectedPatientId,
  onSelectPatient,
  hours,
  onChangeHours,
  backendOnline,
  onRefresh,
  isRefreshing,
  onOpenMobileSidebar,
}) {
  const selectedPatient = patients.find((p) => p.id === Number(selectedPatientId));

  return (
    <header className="topbar">
      <div className="topbar-left">
        <button
          className="mobile-menu-trigger"
          onClick={onOpenMobileSidebar}
          aria-label="Open Navigation"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>

        <div className="patient-quick-select-wrapper">
          <label htmlFor="patient-select" className="quick-select-label">
            Active Patient:
          </label>
          <select
            id="patient-select"
            className="patient-select-dropdown"
            value={selectedPatientId || ''}
            onChange={(e) => onSelectPatient(Number(e.target.value))}
          >
            {patients.map((p) => (
              <option key={p.id} value={p.id}>
                #{p.id} - {p.name} ({p.diabetes_type}, {p.age}y)
              </option>
            ))}
          </select>
        </div>

        {selectedPatient && (
          <div className="active-patient-badge">
            <span className={`badge ${
              selectedPatient.diabetes_type === 'Type 1'
                ? 'badge-warning'
                : selectedPatient.diabetes_type === 'Type 2'
                ? 'badge-twin'
                : 'badge-normal'
            }`}>
              {selectedPatient.diabetes_type}
            </span>
          </div>
        )}
      </div>

      <div className="topbar-right">
        {/* Time Window Selector */}
        <div className="timeframe-picker">
          <span className="timeframe-label">Window:</span>
          {[24, 48, 72].map((h) => (
            <button
              key={h}
              className={`time-btn ${hours === h ? 'active' : ''}`}
              onClick={() => onChangeHours(h)}
            >
              {h}h
            </button>
          ))}
        </div>

        {/* Refresh Button */}
        <button
          className="refresh-btn"
          onClick={onRefresh}
          disabled={isRefreshing}
          title="Refresh Data from API"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            style={{ animation: isRefreshing ? 'spin 1s linear infinite' : 'none' }}
          >
            <path d="M23 4v6h-6" />
            <path d="M1 20v-6h6" />
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
          </svg>
          <span className="refresh-text">{isRefreshing ? 'Syncing...' : 'Sync'}</span>
        </button>

        {/* Backend Connectivity Status */}
        <div className="backend-indicator" title={backendOnline ? 'Backend API Connected' : 'Backend API Disconnected'}>
          <span
            className="pulse-dot"
            style={{
              backgroundColor: backendOnline ? 'var(--status-normal)' : 'var(--status-critical)',
              boxShadow: backendOnline
                ? '0 0 0 0 rgba(16, 185, 129, 0.7)'
                : '0 0 0 0 rgba(239, 68, 68, 0.7)',
            }}
          />
          <span className="indicator-label">{backendOnline ? 'API 8000 OK' : 'API Offline'}</span>
        </div>
      </div>
    </header>
  );
}
