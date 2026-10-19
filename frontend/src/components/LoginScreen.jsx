import React, { useState } from 'react';
import { loginUser } from '../api/client';

export default function LoginScreen({ onLoginSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setErrorMessage('Please enter both username and password.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await loginUser(username.trim(), password);
      if (onLoginSuccess) {
        onLoginSuccess(data.user);
      }
    } catch (err) {
      setErrorMessage(err.detail || err.message || 'Login failed. Please verify your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const fillDemoAccount = (demoUser, demoPass) => {
    setUsername(demoUser);
    setPassword(demoPass);
    setErrorMessage(null);
  };

  return (
    <div className="login-screen-wrapper">
      <div className="login-card">
        <div className="login-header">
          <div className="login-logo-badge">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </div>
          <h1 className="login-title">GlucoTwin</h1>
          <p className="login-subtitle">
            Predictive Multimodal Digital Twin Platform for Proactive Glycemic Management
          </p>
        </div>

        {errorMessage && (
          <div className="login-error-alert" role="alert">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="login-username" className="form-label">Username</label>
            <input
              id="login-username"
              type="text"
              className="form-input"
              placeholder="e.g. dr_sharma or rajesh_kumar"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isLoading}
              autoFocus
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="login-password" className="form-label">Password</label>
            <input
              id="login-password"
              type="password"
              className="form-input"
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
              required
            />
          </div>

          <button
            type="submit"
            className="login-submit-btn"
            disabled={isLoading}
          >
            {isLoading ? (
              <span className="login-btn-content">
                <svg className="login-spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                </svg>
                Authenticating...
              </span>
            ) : (
              'Sign In to GlucoTwin'
            )}
          </button>
        </form>

        {import.meta.env.DEV && (
          <div className="demo-accounts-helper">
            <span className="demo-helper-title">Development Demo Credentials (Click to Fill)</span>
            <div className="demo-chips">
              <button
                type="button"
                className="demo-chip-btn"
                onClick={() => fillDemoAccount('dr_sharma', 'Clinician123!')}
                disabled={isLoading}
                title="Click to auto-fill clinician credentials"
              >
                <div className="demo-chip-header">
                  <span className="demo-role-tag clinician">Clinician</span>
                  <span className="demo-name">Dr. Sharma</span>
                </div>
                <div className="demo-credential-details">
                  <span className="demo-cred-field">Username: <code>dr_sharma</code></span>
                  <span className="demo-cred-field">Password: <code>Clinician123!</code></span>
                </div>
              </button>
              <button
                type="button"
                className="demo-chip-btn"
                onClick={() => fillDemoAccount('rajesh_kumar', 'Patient123!')}
                disabled={isLoading}
                title="Click to auto-fill patient credentials"
              >
                <div className="demo-chip-header">
                  <span className="demo-role-tag patient">Patient</span>
                  <span className="demo-name">Rajesh Kumar</span>
                </div>
                <div className="demo-credential-details">
                  <span className="demo-cred-field">Username: <code>rajesh_kumar</code></span>
                  <span className="demo-cred-field">Password: <code>Patient123!</code></span>
                </div>
              </button>
            </div>
            <p className="demo-local-note">
              Note: These credentials are for local development and testing only.
            </p>
          </div>
        )}

        <div className="login-footer-disclaimer">
          <span>RESEARCH & DEMONSTRATION PROTOTYPE ONLY</span>
          <p>
            Role-based access control (RBAC) enforced server-side. Not clinically certified.
            Do not enter real protected health information (PHI).
          </p>
        </div>
      </div>
    </div>
  );
}
