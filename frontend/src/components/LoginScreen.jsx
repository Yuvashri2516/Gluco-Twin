import React, { useState } from 'react';
import {
  loginUser,
  registerPatientAccount,
} from '../api/client';

const INITIAL_REGISTER_FORM = {
  name: '',
  email: '',
  username: '',
  password: '',
  confirmPassword: '',
  age: '',
  gender: '',
  diabetes_type: '',
};

export default function LoginScreen({ onLoginSuccess }) {
  const [mode, setMode] = useState('login');

  // Login state
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showLoginPassword, setShowLoginPassword] = useState(false);

  // Registration state
  const [registerForm, setRegisterForm] = useState({
    ...INITIAL_REGISTER_FORM,
  });

  const [showRegisterPassword, setShowRegisterPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Shared state
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const switchMode = (nextMode) => {
    setMode(nextMode);
    setErrorMessage('');
    setSuccessMessage('');
  };

  // =========================================================
  // LOGIN
  // =========================================================

  const handleLogin = async (event) => {
    event.preventDefault();

    if (!username.trim() || !password) {
      setErrorMessage('Please enter both username and password.');
      return;
    }

    setIsLoading(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      const data = await loginUser(username.trim(), password);

      if (onLoginSuccess) {
        onLoginSuccess(data.user);
      }
    } catch (error) {
      setErrorMessage(
        error.detail ||
          error.message ||
          'Login failed. Please verify your credentials.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  // =========================================================
  // REGISTRATION FORM INPUTS
  // =========================================================

  const handleRegisterChange = (event) => {
    const { name, value } = event.target;

    setRegisterForm((previous) => ({
      ...previous,
      [name]: value,
    }));

    setErrorMessage('');
  };

  // =========================================================
  // REGISTER PATIENT ACCOUNT
  // =========================================================

  const handleRegister = async (event) => {
    event.preventDefault();

    const cleanName = registerForm.name.trim();
    const cleanEmail = registerForm.email.trim();
    const cleanUsername = registerForm.username.trim();

    if (
      !cleanName ||
      !cleanEmail ||
      !cleanUsername ||
      !registerForm.password ||
      !registerForm.confirmPassword ||
      !registerForm.age ||
      !registerForm.gender ||
      !registerForm.diabetes_type
    ) {
      setErrorMessage('Please complete all required fields.');
      return;
    }

    if (cleanName.length < 2) {
      setErrorMessage('Full name must contain at least 2 characters.');
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(cleanEmail)) {
      setErrorMessage('Please enter a valid email address.');
      return;
    }

    if (cleanUsername.length < 3) {
      setErrorMessage('Username must contain at least 3 characters.');
      return;
    }

    if (registerForm.password.length < 8) {
      setErrorMessage('Password must contain at least 8 characters.');
      return;
    }

    if (registerForm.password.length > 128) {
      setErrorMessage('Password cannot exceed 128 characters.');
      return;
    }

    if (registerForm.password !== registerForm.confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    const age = Number(registerForm.age);

    if (!Number.isInteger(age) || age < 1 || age > 120) {
      setErrorMessage('Please enter an age between 1 and 120.');
      return;
    }

    setIsLoading(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      // Public registration can create patient accounts only.
      // Never send a client-selected role or patient_id.
      const payload = {
        name: cleanName,
        email: cleanEmail,
        username: cleanUsername,
        password: registerForm.password,
        age,
        gender: registerForm.gender,
        diabetes_type: registerForm.diabetes_type,
      };

      await registerPatientAccount(payload);

      // Return to login after successful registration.
      setUsername(cleanUsername);
      setPassword('');
      setRegisterForm({ ...INITIAL_REGISTER_FORM });

      setMode('login');
      setSuccessMessage(
        'Account created successfully! Please sign in with your new credentials.'
      );
    } catch (error) {
      setErrorMessage(
        error.detail ||
          error.message ||
          'Registration failed. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  // =========================================================
  // UI
  // =========================================================

  return (
    <main className="login-screen-wrapper">
      <section
        className={`login-card ${
          mode === 'register' ? 'login-card-register' : ''
        }`}
        aria-labelledby="login-page-title"
      >
        {/* BRAND HEADER */}

        <header className="login-header">
          <div className="login-logo-badge" aria-hidden="true">
            <svg
              width="30"
              height="30"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </div>

          <h1 id="login-page-title" className="login-title">
            GlucoTwin
          </h1>

          <p className="login-subtitle">
            Predictive Multimodal Digital Twin Platform for Proactive
            Glycemic Management
          </p>
        </header>

        {/* PAGE HEADING */}

        <div className="auth-section-heading">
          <h2>
            {mode === 'login' ? 'Welcome Back' : 'Create Your Account'}
          </h2>

          <p>
            {mode === 'login'
              ? 'Sign in to continue to your GlucoTwin dashboard.'
              : 'Register as a patient to get started with GlucoTwin.'}
          </p>
        </div>

        {/* ERROR MESSAGE */}

        {errorMessage && (
          <div className="login-error-alert" role="alert">
            <svg
              width="19"
              height="19"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>

            <span>{errorMessage}</span>
          </div>
        )}

        {/* SUCCESS MESSAGE */}

        {successMessage && (
          <div className="login-success-alert" role="status">
            <svg
              width="19"
              height="19"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="m8 12 2.5 2.5L16 9" />
            </svg>

            <span>{successMessage}</span>
          </div>
        )}

        {/* ===================================================
            LOGIN FORM
        =================================================== */}

        {mode === 'login' && (
          <>
            <form onSubmit={handleLogin} className="login-form">
              <div className="form-group">
                <label htmlFor="login-username" className="form-label">
                  Username
                </label>

                <input
                  id="login-username"
                  name="username"
                  type="text"
                  className="form-input"
                  placeholder="Enter your username"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  disabled={isLoading}
                  autoComplete="username"
                  autoFocus
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="login-password" className="form-label">
                  Password
                </label>

                <div className="auth-password-wrapper">
                  <input
                    id="login-password"
                    name="password"
                    type={showLoginPassword ? 'text' : 'password'}
                    className="form-input auth-password-input"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    disabled={isLoading}
                    autoComplete="current-password"
                    required
                  />

                  <button
                    type="button"
                    className="auth-password-toggle"
                    onClick={() =>
                      setShowLoginPassword((visible) => !visible)
                    }
                    disabled={isLoading}
                    aria-label={
                      showLoginPassword ? 'Hide password' : 'Show password'
                    }
                  >
                    {showLoginPassword ? 'Hide' : 'Show'}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                className="login-submit-btn"
                disabled={isLoading}
              >
                {isLoading ? (
                  <span className="login-btn-content">
                    <span className="login-spinner" aria-hidden="true" />
                    Signing in...
                  </span>
                ) : (
                  'Sign In to GlucoTwin'
                )}
              </button>
            </form>

            {/* CREATE ACCOUNT OPTION */}

            <div className="auth-switch-panel">
              <p>New to GlucoTwin?</p>

              <button
                type="button"
                className="auth-switch-btn"
                onClick={() => switchMode('register')}
                disabled={isLoading}
              >
                Create an account <span aria-hidden="true">→</span>
              </button>
            </div>
          </>
        )}

        {/* ===================================================
            REGISTRATION FORM
        =================================================== */}

        {mode === 'register' && (
          <>
            <form
              onSubmit={handleRegister}
              className="login-form register-form"
            >
              <div className="register-form-grid">
                {/* FULL NAME */}

                <div className="form-group register-field-full">
                  <label htmlFor="register-name" className="form-label">
                    Full Name
                  </label>

                  <input
                    id="register-name"
                    name="name"
                    type="text"
                    className="form-input"
                    placeholder="Enter your full name"
                    value={registerForm.name}
                    onChange={handleRegisterChange}
                    disabled={isLoading}
                    autoComplete="name"
                    minLength={2}
                    maxLength={120}
                    required
                  />
                </div>

                {/* EMAIL */}

                <div className="form-group register-field-full">
                  <label htmlFor="register-email" className="form-label">
                    Email Address
                  </label>

                  <input
                    id="register-email"
                    name="email"
                    type="email"
                    className="form-input"
                    placeholder="you@example.com"
                    value={registerForm.email}
                    onChange={handleRegisterChange}
                    disabled={isLoading}
                    autoComplete="email"
                    maxLength={254}
                    required
                  />
                </div>

                {/* USERNAME */}

                <div className="form-group register-field-full">
                  <label htmlFor="register-username" className="form-label">
                    Username
                  </label>

                  <input
                    id="register-username"
                    name="username"
                    type="text"
                    className="form-input"
                    placeholder="Choose a username"
                    value={registerForm.username}
                    onChange={handleRegisterChange}
                    disabled={isLoading}
                    autoComplete="username"
                    minLength={3}
                    maxLength={64}
                    required
                  />
                </div>

                {/* AGE */}

                <div className="form-group">
                  <label htmlFor="register-age" className="form-label">
                    Age
                  </label>

                  <input
                    id="register-age"
                    name="age"
                    type="number"
                    className="form-input"
                    placeholder="Your age"
                    value={registerForm.age}
                    onChange={handleRegisterChange}
                    disabled={isLoading}
                    min="1"
                    max="120"
                    step="1"
                    required
                  />
                </div>

                {/* GENDER */}

                <div className="form-group">
                  <label htmlFor="register-gender" className="form-label">
                    Gender
                  </label>

                  <select
                    id="register-gender"
                    name="gender"
                    className="form-input auth-select"
                    value={registerForm.gender}
                    onChange={handleRegisterChange}
                    disabled={isLoading}
                    required
                  >
                    <option value="">Select gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                {/* DIABETES TYPE */}

                <div className="form-group register-field-full">
                  <label
                    htmlFor="register-diabetes-type"
                    className="form-label"
                  >
                    Diabetes Type
                  </label>

                  <select
                    id="register-diabetes-type"
                    name="diabetes_type"
                    className="form-input auth-select"
                    value={registerForm.diabetes_type}
                    onChange={handleRegisterChange}
                    disabled={isLoading}
                    required
                  >
                    <option value="">Select diabetes type</option>
                    <option value="Type 1">Type 1</option>
                    <option value="Type 2">Type 2</option>
                    <option value="Gestational">Gestational</option>
                    <option value="Other">Other</option>
                    <option value="Not diagnosed">Not diagnosed</option>
                  </select>

                  <small className="auth-field-hint">
                    Select the option that best describes your situation.
                    This information is not a medical diagnosis.
                  </small>
                </div>

                {/* PASSWORD */}

                <div className="form-group register-field-full">
                  <label htmlFor="register-password" className="form-label">
                    Password
                  </label>

                  <div className="auth-password-wrapper">
                    <input
                      id="register-password"
                      name="password"
                      type={showRegisterPassword ? 'text' : 'password'}
                      className="form-input auth-password-input"
                      placeholder="Create a password (minimum 8 characters)"
                      value={registerForm.password}
                      onChange={handleRegisterChange}
                      disabled={isLoading}
                      autoComplete="new-password"
                      minLength={8}
                      maxLength={128}
                      required
                    />

                    <button
                      type="button"
                      className="auth-password-toggle"
                      onClick={() =>
                        setShowRegisterPassword((visible) => !visible)
                      }
                      disabled={isLoading}
                      aria-label={
                        showRegisterPassword ? 'Hide password' : 'Show password'
                      }
                    >
                      {showRegisterPassword ? 'Hide' : 'Show'}
                    </button>
                  </div>
                </div>

                {/* CONFIRM PASSWORD */}

                <div className="form-group register-field-full">
                  <label
                    htmlFor="register-confirm-password"
                    className="form-label"
                  >
                    Confirm Password
                  </label>

                  <div className="auth-password-wrapper">
                    <input
                      id="register-confirm-password"
                      name="confirmPassword"
                      type={showConfirmPassword ? 'text' : 'password'}
                      className="form-input auth-password-input"
                      placeholder="Re-enter your password"
                      value={registerForm.confirmPassword}
                      onChange={handleRegisterChange}
                      disabled={isLoading}
                      autoComplete="new-password"
                      required
                    />

                    <button
                      type="button"
                      className="auth-password-toggle"
                      onClick={() =>
                        setShowConfirmPassword((visible) => !visible)
                      }
                      disabled={isLoading}
                      aria-label={
                        showConfirmPassword
                          ? 'Hide confirmation password'
                          : 'Show confirmation password'
                      }
                    >
                      {showConfirmPassword ? 'Hide' : 'Show'}
                    </button>
                  </div>
                </div>
              </div>

              {/* SUBMIT REGISTRATION */}

              <button
                type="submit"
                className="login-submit-btn"
                disabled={isLoading}
              >
                {isLoading ? (
                  <span className="login-btn-content">
                    <span className="login-spinner" aria-hidden="true" />
                    Creating account...
                  </span>
                ) : (
                  'Create Patient Account'
                )}
              </button>

              <p className="auth-privacy-note">
                Public registration creates a patient account only. Your
                password is hashed before storage.
              </p>
            </form>

            {/* BACK TO LOGIN */}

            <div className="auth-switch-panel">
              <p>Already have an account?</p>

              <button
                type="button"
                className="auth-switch-btn"
                onClick={() => switchMode('login')}
                disabled={isLoading}
              >
                ← Back to Sign In
              </button>
            </div>
          </>
        )}

        {/* DISCLAIMER */}

        <footer className="login-footer-disclaimer">
          <span>RESEARCH &amp; DEMONSTRATION PROTOTYPE ONLY</span>

          <p>
            Role-based access control is enforced server-side. This platform
            is not clinically certified and is not a substitute for
            professional medical advice.
          </p>
        </footer>
      </section>
    </main>
  );
}