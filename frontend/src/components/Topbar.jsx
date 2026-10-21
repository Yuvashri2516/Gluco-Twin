import React, { useState, useRef, useEffect } from 'react';

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
  notifications = [],
  onNavigateTab,
  onOpenAddPatient,
  onOpenEditPatient,
  onOpenDoctorApprovals,
  currentUser,
  onLogout,
}) {
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const dropdownRef = useRef(null);

  const selectedPatient = patients.find((p) => p.id === Number(selectedPatientId));
  const activeAlerts = notifications.filter((n) => n.status === 'active');

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsNotificationsOpen(false);
      }
    }
    if (isNotificationsOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isNotificationsOpen]);

  const handleSelectAlert = (alert) => {
    setIsNotificationsOpen(false);
    if (onSelectPatient && alert.patient_id) {
      onSelectPatient(alert.patient_id);
    }
    if (onNavigateTab) {
      onNavigateTab('alerts');
    }
  };

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

        {currentUser?.role === 'patient' ? (
          <div className="patient-portal-identity-badge">
            <span className="badge badge-normal" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#059669', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
              Patient Portal
            </span>
            <span style={{ fontWeight: 600, fontSize: '0.92rem', color: 'var(--text-primary)', marginLeft: '8px' }}>
              {selectedPatient ? `${selectedPatient.name} (Patient #${selectedPatient.id})` : `Patient Record #${currentUser?.patient_id || ''}`}
            </span>
          </div>
        ) : (
          <>
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

            {/* Patient Action Buttons */}
            <div className="patient-action-btns-group" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: '6px' }}>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={onOpenEditPatient}
                disabled={!selectedPatient}
                title="Edit Active Patient Demographics"
              >
                Edit Profile
              </button>
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={onOpenAddPatient}
                title="Register New Patient Context"
              >
                + Add Patient
              </button>
              {onOpenDoctorApprovals && (
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={onOpenDoctorApprovals}
                  title="Review Pending Doctor Registration Requests"
                  style={{ borderColor: 'rgba(59, 130, 246, 0.4)', color: '#3b82f6' }}
                >
                  Doctor Requests
                </button>
              )}
            </div>
          </>
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

        {/* Notifications Bell Dropdown */}
        <div className="notifications-wrapper" ref={dropdownRef}>
          <button
            type="button"
            className={`topbar-notification-btn ${activeAlerts.length > 0 ? 'has-alerts' : ''}`}
            onClick={() => setIsNotificationsOpen((prev) => !prev)}
            title="Doctor / Staff Alert Notifications"
            aria-label="Alert Notifications"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            {activeAlerts.length > 0 && (
              <span className="notification-badge-count">{activeAlerts.length}</span>
            )}
          </button>

          {isNotificationsOpen && (
            <div className="notifications-dropdown-menu">
              <div className="notif-header">
                <strong>In-Dashboard Alert Center</strong>
                <span className="badge badge-neutral">{activeAlerts.length} Active</span>
              </div>

              {activeAlerts.length === 0 ? (
                <div className="notif-empty">
                  <span>No active unacknowledged alerts</span>
                </div>
              ) : (
                <div className="notif-list">
                  {activeAlerts.slice(0, 6).map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      className="notif-item"
                      onClick={() => handleSelectAlert(item)}
                    >
                      <div className="notif-item-top">
                        <span className={`badge ${
                          item.severity === 'critical' ? 'badge-critical' : 'badge-warning'
                        }`}>
                          {item.severity}
                        </span>
                        <span className="notif-patient">{item.patient_name || `Patient #${item.patient_id}`}</span>
                      </div>
                      <p className="notif-message">{item.message}</p>
                    </button>
                  ))}
                </div>
              )}

              <div className="notif-footer">
                <button
                  type="button"
                  className="notif-view-all-btn"
                  onClick={() => {
                    setIsNotificationsOpen(false);
                    if (onNavigateTab) onNavigateTab('alerts');
                  }}
                >
                  Open Full Alerts Dashboard &rarr;
                </button>
                <span className="notif-disclaimer">
                  In-dashboard notification workflow (no external SMS/Email integration).
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Authenticated User Session Badge & Logout */}
        <div className="auth-user-badge" title={`Logged in as ${currentUser?.username || 'User'} (${currentUser?.role || 'authenticated'})`}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          <span className="auth-username">
            {currentUser?.role === 'clinician'
              ? (currentUser.username.startsWith('dr_') ? `Dr. ${currentUser.username.slice(3).replace('_', ' ')}` : currentUser.username)
              : (currentUser?.username || 'User')}
          </span>
          <span className={`auth-role-tag ${currentUser?.role || 'clinician'}`}>
            {currentUser?.role === 'clinician' ? 'Clinician' : 'Patient'}
          </span>
          {onLogout && (
            <button
              type="button"
              className="auth-logout-btn"
              onClick={onLogout}
              title="Sign Out of Session"
              aria-label="Sign Out"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </button>
          )}
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
          <span className="indicator-label">{backendOnline ? 'API Online' : 'API Offline'}</span>
        </div>
      </div>
    </header>
  );
}

