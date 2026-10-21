import React, { useState } from 'react';
import { loginUser, registerPatient, registerDoctor } from '../api/client';

export default function AccountEntryScreen({ onLoginSuccess }) {
  // activePortal: 'patient' | 'doctor'
  const [activePortal, setActivePortal] = useState('patient');
  // activeMode: 'signin' | 'register'
  const [activeMode, setActiveMode] = useState('signin');

  // Sign-in state
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // Patient Registration state
  const [patientForm, setPatientForm] = useState({
    fullName: '',
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    age: '',
    gender: 'Other',
    diabetesType: 'Type 2',
  });

  // Doctor Registration state
  const [doctorForm, setDoctorForm] = useState({
    fullName: '',
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    medicalLicenseNumber: '',
  });

  // UI status states
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  const resetFormFeedback = () => {
    setErrorMessage(null);
    setSuccessMessage(null);
  };

  const handlePortalSwitch = (portal) => {
    setActivePortal(portal);
    setActiveMode('signin');
    resetFormFeedback();
  };

  const handleModeSwitch = (mode) => {
    setActiveMode(mode);
    resetFormFeedback();
  };

  // Sign-in submit
  const handleSignIn = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setErrorMessage('Please provide both username and password.');
      return;
    }

    setIsLoading(true);
    resetFormFeedback();

    try {
      const data = await loginUser(username.trim(), password, activePortal);
      if (onLoginSuccess) {
        onLoginSuccess(data.user);
      }
    } catch (err) {
      setErrorMessage(err.detail || err.message || 'Authentication failed. Please verify your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  // Patient registration submit
  const handlePatientRegister = async (e) => {
    e.preventDefault();
    if (!patientForm.fullName.trim() || !patientForm.email.trim() || !patientForm.username.trim() || !patientForm.password) {
      setErrorMessage('Please fill in all required fields.');
      return;
    }
    if (patientForm.password.length < 8) {
      setErrorMessage('Password must be at least 8 characters long.');
      return;
    }
    if (patientForm.password !== patientForm.confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    setIsLoading(true);
    resetFormFeedback();

    try {
      const payload = {
        full_name: patientForm.fullName.trim(),
        email: patientForm.email.trim(),
        username: patientForm.username.trim(),
        password: patientForm.password,
        confirm_password: patientForm.confirmPassword,
        age: patientForm.age ? parseInt(patientForm.age, 10) : 35,
        gender: patientForm.gender,
        diabetes_type: patientForm.diabetesType,
      };

      await registerPatient(payload);
      setSuccessMessage('Patient account created successfully! You may now sign in.');
      setActiveMode('signin');
      setUsername(patientForm.username.trim());
      setPassword('');
    } catch (err) {
      setErrorMessage(err.detail || err.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Doctor account request submit
  const handleDoctorRegister = async (e) => {
    e.preventDefault();
    if (!doctorForm.fullName.trim() || !doctorForm.email.trim() || !doctorForm.username.trim() || !doctorForm.password) {
      setErrorMessage('Please fill in all required fields.');
      return;
    }
    if (doctorForm.password.length < 8) {
      setErrorMessage('Password must be at least 8 characters long.');
      return;
    }
    if (doctorForm.password !== doctorForm.confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    setIsLoading(true);
    resetFormFeedback();

    try {
      const payload = {
        full_name: doctorForm.fullName.trim(),
        email: doctorForm.email.trim(),
        username: doctorForm.username.trim(),
        password: doctorForm.password,
        confirm_password: doctorForm.confirmPassword,
        medical_license_number: doctorForm.medicalLicenseNumber.trim() || undefined,
      };

      await registerDoctor(payload);
      setSuccessMessage(
        'Doctor account request submitted! Your account is stored as pending review. ' +
        'An authorized clinician must approve your request before access to patient data is granted.'
      );
      setActiveMode('signin');
      setUsername(doctorForm.username.trim());
      setPassword('');
    } catch (err) {
      setErrorMessage(err.detail || err.message || 'Doctor account request failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Fill development credentials
  const fillDevAccount = (u, p, portal) => {
    setActivePortal(portal);
    setActiveMode('signin');
    setUsername(u);
    setPassword(p);
    resetFormFeedback();
  };

  const isPatient = activePortal === 'patient';

  return (
    <div className="account-entry-screen">
      <div className="account-entry-container">
        {/* Brand Header */}
        <div className="account-entry-header">
          <div className="account-brand-badge">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </div>
          <h1 className="account-brand-title">GlucoTwin</h1>
          <p className="account-brand-subtitle">
            Intelligent Predictive Digital Twin Platform for Proactive Glycemic Management
          </p>
        </div>

        {/* Portal Selection Cards */}
        <div className="portal-selector-row">
          <button
            type="button"
            className={`portal-choice-card ${isPatient ? 'selected patient-theme' : ''}`}
            onClick={() => handlePortalSwitch('patient')}
            aria-pressed={isPatient}
          >
            <div className="portal-card-icon patient-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
            </div>
            <div className="portal-card-text">
              <span className="portal-card-tag">Patient Portal</span>
              <h2 className="portal-card-title">Patient Access</h2>
              <p className="portal-card-desc">Personal glucose telemetry, digital twin &amp; health reports</p>
            </div>
          </button>

          <button
            type="button"
            className={`portal-choice-card ${!isPatient ? 'selected doctor-theme' : ''}`}
            onClick={() => handlePortalSwitch('doctor')}
            aria-pressed={!isPatient}
          >
            <div className="portal-card-icon doctor-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z" />
                <path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z" />
                <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0" />
                <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5" />
              </svg>
            </div>
            <div className="portal-card-text">
              <span className="portal-card-tag">Doctor Portal</span>
              <h2 className="portal-card-title">Clinician Access</h2>
              <p className="portal-card-desc">Patient cohort oversight, twin analytics &amp; clinical triage</p>
            </div>
          </button>
        </div>

        {/* Portal Content Box */}
        <div className={`portal-content-box ${isPatient ? 'patient-border' : 'doctor-border'}`}>
          {/* Sub-tabs: Sign In vs Register / Request */}
          <div className="portal-subtabs">
            <button
              type="button"
              className={`subtab-btn ${activeMode === 'signin' ? 'active' : ''}`}
              onClick={() => handleModeSwitch('signin')}
            >
              {isPatient ? 'Patient Sign In' : 'Doctor Sign In'}
            </button>
            <button
              type="button"
              className={`subtab-btn ${activeMode === 'register' ? 'active' : ''}`}
              onClick={() => handleModeSwitch('register')}
            >
              {isPatient ? 'Create Patient Account' : 'Request Doctor Account'}
            </button>
          </div>

          {/* Feedback Messages */}
          {errorMessage && (
            <div className="portal-alert error-alert" role="alert">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <span>{errorMessage}</span>
            </div>
          )}

          {successMessage && (
            <div className="portal-alert success-alert" role="status">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
              <span>{successMessage}</span>
            </div>
          )}

          {/* 1. SIGN IN FORM */}
          {activeMode === 'signin' && (
            <form onSubmit={handleSignIn} className="portal-form">
              <div className="form-group">
                <label className="form-label" htmlFor="portal-username">
                  {isPatient ? 'Patient Username' : 'Clinician Username'}
                </label>
                <input
                  id="portal-username"
                  type="text"
                  className="form-input"
                  placeholder={isPatient ? "e.g. ananya_sharma or rajesh_kumar" : "e.g. dr_sharma"}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  disabled={isLoading}
                  required
                  autoFocus
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="portal-password">Password</label>
                <input
                  id="portal-password"
                  type="password"
                  className="form-input"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isLoading}
                  required
                />
              </div>

              <button
                type="submit"
                className={`portal-submit-btn ${isPatient ? 'patient-btn' : 'doctor-btn'}`}
                disabled={isLoading}
              >
                {isLoading ? (
                  <span className="btn-loading">
                    <svg className="login-spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                    </svg>
                    Authenticating credentials...
                  </span>
                ) : (
                  isPatient ? 'Sign In to Patient Portal' : 'Sign In to Doctor Portal'
                )}
              </button>
            </form>
          )}

          {/* 2. PATIENT REGISTRATION FORM */}
          {activeMode === 'register' && isPatient && (
            <form onSubmit={handlePatientRegister} className="portal-form">
              <div className="form-group">
                <label className="form-label" htmlFor="p-fullname">Full Name *</label>
                <input
                  id="p-fullname"
                  type="text"
                  className="form-input"
                  placeholder="e.g. Rajesh Kumar"
                  value={patientForm.fullName}
                  onChange={(e) => setPatientForm({ ...patientForm, fullName: e.target.value })}
                  disabled={isLoading}
                  required
                />
              </div>

              <div className="form-row-2">
                <div className="form-group">
                  <label className="form-label" htmlFor="p-email">Email Address *</label>
                  <input
                    id="p-email"
                    type="email"
                    className="form-input"
                    placeholder="name@example.com"
                    value={patientForm.email}
                    onChange={(e) => setPatientForm({ ...patientForm, email: e.target.value })}
                    disabled={isLoading}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="p-username">Username *</label>
                  <input
                    id="p-username"
                    type="text"
                    className="form-input"
                    placeholder="Choose username"
                    value={patientForm.username}
                    onChange={(e) => setPatientForm({ ...patientForm, username: e.target.value })}
                    disabled={isLoading}
                    required
                  />
                </div>
              </div>

              <div className="form-row-2">
                <div className="form-group">
                  <label className="form-label" htmlFor="p-password">Password (min 8 chars) *</label>
                  <input
                    id="p-password"
                    type="password"
                    className="form-input"
                    placeholder="Create password"
                    value={patientForm.password}
                    onChange={(e) => setPatientForm({ ...patientForm, password: e.target.value })}
                    disabled={isLoading}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="p-confirm">Confirm Password *</label>
                  <input
                    id="p-confirm"
                    type="password"
                    className="form-input"
                    placeholder="Confirm password"
                    value={patientForm.confirmPassword}
                    onChange={(e) => setPatientForm({ ...patientForm, confirmPassword: e.target.value })}
                    disabled={isLoading}
                    required
                  />
                </div>
              </div>

              <div className="form-row-3">
                <div className="form-group">
                  <label className="form-label" htmlFor="p-age">Age (optional)</label>
                  <input
                    id="p-age"
                    type="number"
                    min="1"
                    max="120"
                    className="form-input"
                    placeholder="e.g. 45"
                    value={patientForm.age}
                    onChange={(e) => setPatientForm({ ...patientForm, age: e.target.value })}
                    disabled={isLoading}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="p-gender">Gender</label>
                  <select
                    id="p-gender"
                    className="form-input"
                    value={patientForm.gender}
                    onChange={(e) => setPatientForm({ ...patientForm, gender: e.target.value })}
                    disabled={isLoading}
                  >
                    <option value="Female">Female</option>
                    <option value="Male">Male</option>
                    <option value="Other">Other</option>
                    <option value="Prefer not to say">Prefer not to say</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="p-type">Diabetes Status</label>
                  <select
                    id="p-type"
                    className="form-input"
                    value={patientForm.diabetesType}
                    onChange={(e) => setPatientForm({ ...patientForm, diabetesType: e.target.value })}
                    disabled={isLoading}
                  >
                    <option value="Type 2">Type 2</option>
                    <option value="Type 1">Type 1</option>
                    <option value="Pre-diabetic">Pre-diabetic</option>
                    <option value="Gestational">Gestational</option>
                    <option value="None">None / Screening</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                className="portal-submit-btn patient-btn"
                disabled={isLoading}
              >
                {isLoading ? 'Creating Patient Account...' : 'Complete Patient Registration'}
              </button>
            </form>
          )}

          {/* 3. DOCTOR REQUEST FORM */}
          {activeMode === 'register' && !isPatient && (
            <form onSubmit={handleDoctorRegister} className="portal-form">
              <div className="security-notice-callout">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                </svg>
                <span>
                  <strong>Clinical Access Security Policy:</strong> Public registration requests require verified clinical administrator approval.
                  Pending accounts are prevented from accessing patient records or clinician tools.
                </span>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="d-fullname">Full Name &amp; Title *</label>
                <input
                  id="d-fullname"
                  type="text"
                  className="form-input"
                  placeholder="e.g. Dr. Jane Doe, MD"
                  value={doctorForm.fullName}
                  onChange={(e) => setDoctorForm({ ...doctorForm, fullName: e.target.value })}
                  disabled={isLoading}
                  required
                />
              </div>

              <div className="form-row-2">
                <div className="form-group">
                  <label className="form-label" htmlFor="d-email">Professional Hospital Email *</label>
                  <input
                    id="d-email"
                    type="email"
                    className="form-input"
                    placeholder="doctor@hospital.org"
                    value={doctorForm.email}
                    onChange={(e) => setDoctorForm({ ...doctorForm, email: e.target.value })}
                    disabled={isLoading}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="d-username">Clinician Username *</label>
                  <input
                    id="d-username"
                    type="text"
                    className="form-input"
                    placeholder="Choose username"
                    value={doctorForm.username}
                    onChange={(e) => setDoctorForm({ ...doctorForm, username: e.target.value })}
                    disabled={isLoading}
                    required
                  />
                </div>
              </div>

              <div className="form-row-2">
                <div className="form-group">
                  <label className="form-label" htmlFor="d-password">Password (min 8 chars) *</label>
                  <input
                    id="d-password"
                    type="password"
                    className="form-input"
                    placeholder="Create strong password"
                    value={doctorForm.password}
                    onChange={(e) => setDoctorForm({ ...doctorForm, password: e.target.value })}
                    disabled={isLoading}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="d-confirm">Confirm Password *</label>
                  <input
                    id="d-confirm"
                    type="password"
                    className="form-input"
                    placeholder="Confirm password"
                    value={doctorForm.confirmPassword}
                    onChange={(e) => setDoctorForm({ ...doctorForm, confirmPassword: e.target.value })}
                    disabled={isLoading}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="d-license">Medical Registration / License Number</label>
                <input
                  id="d-license"
                  type="text"
                  className="form-input"
                  placeholder="e.g. MED-REG-482910"
                  value={doctorForm.medicalLicenseNumber}
                  onChange={(e) => setDoctorForm({ ...doctorForm, medicalLicenseNumber: e.target.value })}
                  disabled={isLoading}
                />
              </div>

              <button
                type="submit"
                className="portal-submit-btn doctor-btn"
                disabled={isLoading}
              >
                {isLoading ? 'Submitting Clinical Request...' : 'Submit Doctor Account Request'}
              </button>
            </form>
          )}

          {/* Development Demo Credentials Helper (STRIPPED IN PRODUCTION ASSETS) */}
          {import.meta.env.DEV && (
            <div className="demo-credentials-dock">
              <span className="demo-dock-title">
                Development Synthetic Demo Credentials (Click to Fill)
              </span>
              <div className="demo-dock-chips">
                <button
                  type="button"
                  className="demo-dock-chip doctor"
                  onClick={() => fillDevAccount('dr_sharma', 'Clinician123!', 'doctor')}
                  disabled={isLoading}
                  title="Auto-fill verified clinician account"
                >
                  <span className="chip-badge doctor">Clinician</span>
                  <span className="chip-label">Dr. Sharma</span>
                  <code className="chip-creds">dr_sharma / Clinician123!</code>
                </button>
                <button
                  type="button"
                  className="demo-dock-chip patient"
                  onClick={() => fillDevAccount('ananya_sharma', 'Patient123!', 'patient')}
                  disabled={isLoading}
                  title="Auto-fill patient #1 account"
                >
                  <span className="chip-badge patient">Patient #1</span>
                  <span className="chip-label">Ananya Sharma</span>
                  <code className="chip-creds">ananya_sharma / Patient123!</code>
                </button>
                <button
                  type="button"
                  className="demo-dock-chip patient"
                  onClick={() => fillDevAccount('rajesh_kumar', 'Patient123!', 'patient')}
                  disabled={isLoading}
                  title="Auto-fill patient #2 account"
                >
                  <span className="chip-badge patient">Patient #2</span>
                  <span className="chip-label">Rajesh Kumar</span>
                  <code className="chip-creds">rajesh_kumar / Patient123!</code>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Legal Disclaimer */}
        <div className="account-entry-disclaimer">
          <p>
            <strong>RESEARCH &amp; DEMONSTRATION PROTOTYPE:</strong> Role-based access control and patient data isolation
            are cryptographically enforced server-side. Not clinically certified. Never enter real protected health information (PHI).
          </p>
        </div>
      </div>
    </div>
  );
}
