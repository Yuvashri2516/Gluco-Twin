/**
 * API client for GlucoTwin backend.
 *
 * Responsibilities:
 * - Resolve the backend API URL.
 * - Manage authentication and user sessions.
 * - Handle API responses and errors.
 * - Expose functions for patients, readings, alerts,
 *   predictions, digital twins, simulations and documents.
 */

// ---------------------------------------------------------------------------
// API BASE URL
// ---------------------------------------------------------------------------

const AUTH_TOKEN_KEY = 'glucotwin_auth_token';
const AUTH_USER_KEY = 'glucotwin_auth_user';

/**
 * Resolve the API URL.
 *
 * Priority:
 * 1. VITE_API_BASE_URL environment variable.
 * 2. Production: deployed Render backend.
 * 3. Development: local FastAPI backend.
 */
export function resolveApiBaseUrl() {
  const envUrl = import.meta.env.VITE_API_BASE_URL;

  if (typeof envUrl === 'string' && envUrl.trim()) {
    const cleanUrl = envUrl.trim().replace(/\/+$/, '');
    const isLocalhost = /^https?:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/i.test(cleanUrl);

    // In production builds, ignore local loopback addresses (127.0.0.1 / localhost)
    // inherited from local development .env files, ensuring production uses the deployed backend.
    if (!import.meta.env.PROD || !isLocalhost) {
      return cleanUrl;
    }
  }

  if (import.meta.env.PROD) {
    return 'https://gluco-twin.onrender.com';
  }

  return 'http://127.0.0.1:8000';
}

const API_BASE_URL = resolveApiBaseUrl();

// ---------------------------------------------------------------------------
// AUTHENTICATION AND SESSION MANAGEMENT
// ---------------------------------------------------------------------------

let currentAuthToken = null;
let currentAuthUser = null;

try {
  if (typeof localStorage !== 'undefined') {
    currentAuthToken = localStorage.getItem(AUTH_TOKEN_KEY) || null;

    const cachedUser = localStorage.getItem(AUTH_USER_KEY);

    if (cachedUser) {
      currentAuthUser = JSON.parse(cachedUser);
    }
  }
} catch {
  currentAuthToken = null;
  currentAuthUser = null;
}

export function getAuthToken() {
  return currentAuthToken;
}

export function getCurrentUser() {
  return currentAuthUser;
}

export function isAuthenticated() {
  return Boolean(currentAuthToken);
}

/**
 * Save or clear the authentication session.
 */
export function setAuthSession(token, user) {
  currentAuthToken = token || null;
  currentAuthUser = user || null;

  try {
    if (typeof localStorage !== 'undefined') {
      if (currentAuthToken) {
        localStorage.setItem(AUTH_TOKEN_KEY, currentAuthToken);
      } else {
        localStorage.removeItem(AUTH_TOKEN_KEY);
      }

      if (currentAuthUser) {
        localStorage.setItem(
          AUTH_USER_KEY,
          JSON.stringify(currentAuthUser)
        );
      } else {
        localStorage.removeItem(AUTH_USER_KEY);
      }
    }
  } catch (error) {
    console.warn(
      'Unable to persist authentication session.',
      error
    );
  }

  if (typeof window !== 'undefined') {
    window.dispatchEvent(
      new CustomEvent('glucotwin:auth_changed', {
        detail: {
          token: currentAuthToken,
          user: currentAuthUser,
        },
      })
    );
  }
}

export function clearAuthSession() {
  setAuthSession(null, null);
}

export async function registerPatient(formData) {
  const res = await fetch(`${API_BASE_URL}/api/auth/register-patient`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData),
  });
  return handleResponse(res, 'patient registration');
}

export async function registerDoctor(formData) {
  const res = await fetch(`${API_BASE_URL}/api/auth/register-doctor`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData),
  });
  return handleResponse(res, 'doctor registration request');
}

export async function fetchDoctorRequests(statusFilter = null) {
  let url = `${API_BASE_URL}/api/auth/doctor-requests`;
  if (statusFilter) url += `?status_filter=${encodeURIComponent(statusFilter)}`;
  const res = await authFetch(url);
  return handleResponse(res, 'doctor requests');
}

export async function approveDoctorRequest(userId) {
  const res = await authFetch(`${API_BASE_URL}/api/auth/doctor-requests/${userId}/approve`, {
    method: 'POST',
  });
  return handleResponse(res, 'doctor approval');
}

export async function rejectDoctorRequest(userId) {
  const res = await authFetch(`${API_BASE_URL}/api/auth/doctor-requests/${userId}/reject`, {
    method: 'POST',
  });
  return handleResponse(res, 'doctor rejection');
}

export async function fetchPatientReport(patientId) {
  const res = await authFetch(`${API_BASE_URL}/api/reports/patient/${patientId}`);
  return handleResponse(res, 'patient report');
}

export function getPatientReportExportUrl(patientId) {
  return `${API_BASE_URL}/api/reports/patient/${patientId}/export`;
}

export async function downloadPatientReportHtml(patientId, filename = null) {
  const res = await authFetch(`${API_BASE_URL}/api/reports/patient/${patientId}/export`);
  if (!res.ok) {
    let errorDetail = res.statusText;
    try {
      const errJson = await res.json();
      if (errJson && errJson.detail) {
        errorDetail = errJson.detail;
      }
    } catch {
      // ignore JSON parse error on non-JSON response
    }
    const error = new Error(`Failed to download report (${res.status}): ${errorDetail}`);
    error.status = res.status;
    error.detail = errorDetail;
    throw error;
  }
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename || `glucotwin_patient_${patientId}_report.html`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}
export function logoutUser() {
  clearAuthSession();
}

// ---------------------------------------------------------------------------
// RESPONSE HANDLING
// ---------------------------------------------------------------------------

/**
 * Parse an API response and provide useful error details.
 */
async function handleResponse(response, endpointName) {
  if (!response.ok) {
    let errorDetail =
      response.statusText || 'Unknown server error';

    try {
      const errorJson = await response.json();

      if (errorJson?.detail !== undefined) {
        if (typeof errorJson.detail === 'string') {
          errorDetail = errorJson.detail;
        } else if (Array.isArray(errorJson.detail)) {
          errorDetail = errorJson.detail
            .map((item) => {
              const location = Array.isArray(item.loc)
                ? item.loc.join('.')
                : 'input';

              return `${location}: ${item.msg || 'Invalid value'}`;
            })
            .join('; ');
        } else {
          errorDetail = JSON.stringify(errorJson.detail);
        }
      }
    } catch {
      // The server might return a non-JSON error response.
    }

    const error = new Error(
      `Failed to load ${endpointName} (${response.status}): ${errorDetail}`
    );

    error.status = response.status;
    error.detail = errorDetail;

    throw error;
  }

  if (response.status === 204) {
    return null;
  }

  if (response.status === 205) {
    return null;
  }

  const contentType = response.headers.get('content-type') || '';

  if (contentType.includes('application/json')) {
    return response.json();
  }

  const text = await response.text();

  return text || null;
}

/**
 * Build a helpful network error.
 */
function createNetworkError(error, endpointName) {
  const networkError = new Error(
    `Unable to connect to the GlucoTwin backend while ${endpointName}. ` +
    `Check that the backend is running and the API URL is correct. ` +
    `API URL: ${API_BASE_URL}`
  );

  networkError.cause = error;

  return networkError;
}

/**
 * Fetch wrapper with readable network errors.
 */
async function safeFetch(url, options = {}, endpointName = 'calling the API') {
  try {
    return await fetch(url, options);
  } catch (error) {
    if (error?.name === 'AbortError') {
      throw error;
    }

    throw createNetworkError(error, endpointName);
  }
}

// ---------------------------------------------------------------------------
// AUTHENTICATED FETCH
// ---------------------------------------------------------------------------

/**
 * Attach the JWT to requests when a session exists.
 *
 * HTTP 401 clears an invalid or expired session.
 */
export async function authFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});

  if (currentAuthToken && !headers.has('Authorization')) {
    headers.set(
      'Authorization',
      `Bearer ${currentAuthToken}`
    );
  }

  const response = await safeFetch(
    url,
    {
      ...options,
      headers,
    },
    'sending an authenticated request'
  );

  if (response.status === 401) {
    clearAuthSession();
  }

  return response;
}

// ---------------------------------------------------------------------------
// LOGIN
// ---------------------------------------------------------------------------

export async function loginUser(username, password, portal = null) {
  const normalizedUsername = String(username || '').trim();

  if (!normalizedUsername || !password) {
    throw new Error('Please enter both username and password.');
  }

  const payload = {
    username: normalizedUsername,
    password,
  };
  if (portal) {
    payload.portal = portal;
  }

  const response = await safeFetch(
    `${API_BASE_URL}/api/auth/login`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
    'signing in'
  );

  const data = await handleResponse(
    response,
    'user authentication'
  );

  if (!data?.access_token || !data?.user) {
    throw new Error(
      'The backend returned an invalid login response.'
    );
  }

  setAuthSession(data.access_token, data.user);

  return data;
}

// ---------------------------------------------------------------------------
// HEALTH CHECK
// ---------------------------------------------------------------------------

export async function fetchHealth() {
  const response = await safeFetch(
    `${API_BASE_URL}/health`,
    {},
    'checking backend health'
  );

  return handleResponse(response, 'health status');
}

// ---------------------------------------------------------------------------
// PATIENTS
// ---------------------------------------------------------------------------

export async function fetchPatients() {
  const response = await authFetch(
    `${API_BASE_URL}/api/patients`
  );

  return handleResponse(response, 'patients list');
}

export async function fetchPatient(patientId) {
  const response = await authFetch(
    `${API_BASE_URL}/api/patients/${patientId}`
  );

  return handleResponse(
    response,
    `patient #${patientId}`
  );
}

export async function createPatient(patientData) {
  const response = await authFetch(
    `${API_BASE_URL}/api/patients`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(patientData),
    }
  );

  return handleResponse(response, 'creating patient');
}

export async function updatePatient(patientId, updateData) {
  const response = await authFetch(
    `${API_BASE_URL}/api/patients/${patientId}`,
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updateData),
    }
  );

  return handleResponse(
    response,
    `updating patient #${patientId}`
  );
}

// ---------------------------------------------------------------------------
// PATIENT READINGS
// ---------------------------------------------------------------------------

export async function fetchGlucoseReadings(
  patientId,
  hours = 24,
  signal
) {
  const response = await authFetch(
    `${API_BASE_URL}/api/readings/glucose/${patientId}?hours=${hours}`,
    { signal }
  );

  return handleResponse(
    response,
    `glucose readings for patient #${patientId}`
  );
}

export async function fetchVitalReadings(
  patientId,
  hours = 24,
  signal
) {
  const response = await authFetch(
    `${API_BASE_URL}/api/readings/vitals/${patientId}?hours=${hours}`,
    { signal }
  );

  return handleResponse(
    response,
    `vital readings for patient #${patientId}`
  );
}

export async function fetchSleepReadings(
  patientId,
  hours = 24,
  signal
) {
  const response = await authFetch(
    `${API_BASE_URL}/api/readings/sleep/${patientId}?hours=${hours}`,
    { signal }
  );

  return handleResponse(
    response,
    `sleep telemetry for patient #${patientId}`
  );
}

export async function fetchStepReadings(
  patientId,
  hours = 24,
  signal
) {
  const response = await authFetch(
    `${API_BASE_URL}/api/readings/steps/${patientId}?hours=${hours}`,
    { signal }
  );

  return handleResponse(
    response,
    `step telemetry for patient #${patientId}`
  );
}

export async function recordManualGlucose({
  patientId,
  value,
  unit = 'mg/dL',
  timestamp = null,
  dataSource = 'manual',
}) {
  const response = await authFetch(
    `${API_BASE_URL}/api/readings/glucose`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        patient_id: Number(patientId),
        value: Number.parseFloat(value),
        unit,
        timestamp,
        data_source: dataSource,
      }),
    }
  );

  return handleResponse(
    response,
    'recording manual glucose'
  );
}

export async function recordManualVitals({
  patientId,
  heartRate = null,
  hrv = null,
  timestamp = null,
  dataSource = 'manual',
}) {
  const payload = {
    patient_id: Number(patientId),
    data_source: dataSource,
    timestamp,
  };

  if (heartRate !== null && heartRate !== '') {
    payload.heart_rate = Number.parseFloat(heartRate);
  }

  if (hrv !== null && hrv !== '') {
    payload.hrv = Number.parseFloat(hrv);
  }

  const response = await authFetch(
    `${API_BASE_URL}/api/readings/vitals`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(
    response,
    'recording manual vitals'
  );
}

// ---------------------------------------------------------------------------
// ALERTS
// ---------------------------------------------------------------------------

export async function fetchAlerts(params = {}, signal) {
  const query = new URLSearchParams();

  if (params.patientId !== undefined && params.patientId !== null) {
    query.append('patient_id', String(params.patientId));
  }

  if (params.status) {
    query.append('status', params.status);
  }

  if (params.severity) {
    query.append('severity', params.severity);
  }

  if (params.source) {
    query.append('source', params.source);
  }

  if (params.limit) {
    query.append('limit', String(params.limit));
  }

  const queryString = query.toString();

  const endpoint = queryString
    ? `${API_BASE_URL}/api/alerts?${queryString}`
    : `${API_BASE_URL}/api/alerts`;

  const response = await authFetch(endpoint, { signal });

  return handleResponse(response, 'alerts');
}

export async function acknowledgeAlert(alertId) {
  const response = await authFetch(
    `${API_BASE_URL}/api/alerts/${alertId}/acknowledge`,
    { method: 'POST' }
  );

  return handleResponse(
    response,
    `acknowledging alert #${alertId}`
  );
}

export async function resolveAlert(alertId) {
  const response = await authFetch(
    `${API_BASE_URL}/api/alerts/${alertId}/resolve`,
    { method: 'POST' }
  );

  return handleResponse(
    response,
    `resolving alert #${alertId}`
  );
}

export async function evaluateAlerts(patientId = null) {
  const response = await authFetch(
    `${API_BASE_URL}/api/alerts/evaluate`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        patient_id: patientId,
      }),
    }
  );

  return handleResponse(
    response,
    'evaluating alerts'
  );
}

// ---------------------------------------------------------------------------
// PREDICTIONS
// ---------------------------------------------------------------------------

export async function predictGlucoseSpike(patientId, signal) {
  const response = await authFetch(
    `${API_BASE_URL}/api/predictions/glucose-spike`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        patient_id: Number(patientId),
      }),
      signal,
    }
  );

  return handleResponse(
    response,
    `glucose spike prediction for patient #${patientId}`
  );
}

// ---------------------------------------------------------------------------
// LAB RESULTS, GENETICS AND DIAGNOSES
// ---------------------------------------------------------------------------

export async function fetchPatientLabs(patientId, signal) {
  const response = await authFetch(
    `${API_BASE_URL}/api/patients/${patientId}/labs`,
    { signal }
  );

  return handleResponse(
    response,
    `laboratory results for patient #${patientId}`
  );
}

export async function fetchPatientGenetics(patientId, signal) {
  const response = await authFetch(
    `${API_BASE_URL}/api/patients/${patientId}/genetics`,
    { signal }
  );

  return handleResponse(
    response,
    `genetic markers for patient #${patientId}`
  );
}

export async function recordManualLab(
  patientId,
  {
    testName,
    result,
    unit,
    referenceRange = null,
    measurementDate = null,
    labSource = null,
    dataSource = 'manual',
  }
) {
  const response = await authFetch(
    `${API_BASE_URL}/api/patients/${patientId}/labs`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        patient_id: Number(patientId),
        test_name: testName,
        result: Number.parseFloat(result),
        unit,
        reference_range: referenceRange,
        measurement_date: measurementDate,
        lab_source: labSource,
        data_source: dataSource,
      }),
    }
  );

  return handleResponse(
    response,
    `recording lab result for patient #${patientId}`
  );
}

export async function recordManualDiagnosis(
  patientId,
  {
    diagnosisName,
    date = null,
    notes = null,
    status = 'active',
  }
) {
  const response = await authFetch(
    `${API_BASE_URL}/api/patients/${patientId}/diagnoses`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        patient_id: Number(patientId),
        diagnosis_name: diagnosisName,
        date: date || null,
        notes: notes || null,
        status,
      }),
    }
  );

  return handleResponse(
    response,
    'recording diagnosis and clinical history'
  );
}

// ---------------------------------------------------------------------------
// DIGITAL TWIN
// ---------------------------------------------------------------------------

export async function fetchTwinState(patientId, signal) {
  const response = await authFetch(
    `${API_BASE_URL}/api/twin/${patientId}`,
    { signal }
  );

  return handleResponse(
    response,
    `digital twin state for patient #${patientId}`
  );
}

export async function fetchDigitalTwinDetail(patientId, signal) {
  const response = await authFetch(
    `${API_BASE_URL}/api/digital-twin/${patientId}`,
    { signal }
  );

  return handleResponse(
    response,
    `digital twin intelligence for patient #${patientId}`
  );
}

// ---------------------------------------------------------------------------
// WHAT-IF SIMULATION
// ---------------------------------------------------------------------------

/**
 * Backend request fields:
 * - patient_id
 * - additional_carbs_g
 * - activity_minutes
 */
export async function runWhatIfSimulation(
  patientId,
  carbsGrams = 30,
  activityMinutes = 0
) {
  const normalizedPatientId = Number(patientId);
  const normalizedCarbs = Number(carbsGrams);
  const normalizedActivity = Number(activityMinutes);

  if (
    !Number.isInteger(normalizedPatientId) ||
    normalizedPatientId <= 0
  ) {
    throw new Error(
      'Please select a valid patient before running the simulation.'
    );
  }

  if (
    !Number.isFinite(normalizedCarbs) ||
    normalizedCarbs < 0 ||
    normalizedCarbs > 300
  ) {
    throw new Error(
      'Carbohydrates must be between 0 and 300 grams.'
    );
  }

  if (
    !Number.isFinite(normalizedActivity) ||
    normalizedActivity < 0 ||
    normalizedActivity > 360
  ) {
    throw new Error(
      'Activity must be between 0 and 360 minutes.'
    );
  }

  const response = await authFetch(
    `${API_BASE_URL}/api/simulation/what-if`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        patient_id: normalizedPatientId,
        additional_carbs_g: normalizedCarbs,
        activity_minutes: normalizedActivity,
      }),
    }
  );

  return handleResponse(
    response,
    `what-if simulation for patient #${normalizedPatientId}`
  );
}

// ---------------------------------------------------------------------------
// SYNTHETIC SENSOR FEED
// ---------------------------------------------------------------------------

export async function simulateSensorFeed(patientId) {
  const normalizedPatientId = Number(patientId);

  if (
    !Number.isInteger(normalizedPatientId) ||
    normalizedPatientId <= 0
  ) {
    throw new Error('Please select a valid patient.');
  }

  const response = await authFetch(
    `${API_BASE_URL}/api/digital-twin/simulate-feed`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        patient_id: normalizedPatientId,
      }),
    }
  );

  return handleResponse(
    response,
    `simulated sensor epoch for patient #${normalizedPatientId}`
  );
}

// ---------------------------------------------------------------------------
// MEDICAL DOCUMENTS
// ---------------------------------------------------------------------------

export async function uploadMedicalDocument(
  patientId,
  file,
  documentCategory = 'lab_report'
) {
  const formData = new FormData();

  formData.append('patient_id', String(patientId));
  formData.append('document_category', documentCategory);
  formData.append('file', file);

  const response = await authFetch(
    `${API_BASE_URL}/api/documents/upload`,
    {
      method: 'POST',
      body: formData,
    }
  );

  return handleResponse(
    response,
    'uploading medical document'
  );
}

export async function fetchPatientDocuments(patientId, signal) {
  const response = await authFetch(
    `${API_BASE_URL}/api/documents/patient/${patientId}`,
    { signal }
  );

  return handleResponse(
    response,
    `documents list for patient #${patientId}`
  );
}

export async function fetchDocumentPreview(documentId, signal) {
  const response = await authFetch(
    `${API_BASE_URL}/api/documents/${documentId}/preview`,
    { signal }
  );

  return handleResponse(
    response,
    `document preview #${documentId}`
  );
}

export async function confirmDocumentExtraction(
  documentId,
  {
    confirmedLabs = [],
    confirmedReadings = [],
    clinicalNotes = '',
  } = {}
) {
  const response = await authFetch(
    `${API_BASE_URL}/api/documents/${documentId}/confirm`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        confirmed_labs: confirmedLabs,
        confirmed_readings: confirmedReadings,
        clinical_notes: clinicalNotes,
      }),
    }
  );

  return handleResponse(
    response,
    `confirming extraction for document #${documentId}`
  );
}

export async function cancelDocumentExtraction(documentId) {
  const response = await authFetch(
    `${API_BASE_URL}/api/documents/${documentId}/cancel`,
    { method: 'POST' }
  );

  return handleResponse(
    response,
    `cancelling extraction for document #${documentId}`
  );
}

export async function deleteMedicalDocument(documentId) {
  const response = await authFetch(
    `${API_BASE_URL}/api/documents/${documentId}`,
    { method: 'DELETE' }
  );

  return handleResponse(
    response,
    `deleting document #${documentId}`
  );
}

export async function downloadDocumentFile(
  documentId,
  filename = null
) {
  const response = await authFetch(
    `${API_BASE_URL}/api/documents/${documentId}/download`
  );

  if (!response.ok) {
    let detail =
      response.statusText || 'Download failed';

    try {
      const errorJson = await response.json();

      if (errorJson?.detail) {
        detail =
          typeof errorJson.detail === 'string'
            ? errorJson.detail
            : JSON.stringify(errorJson.detail);
      }
    } catch {
      // Ignore non-JSON download errors.
    }

    throw new Error(
      `Failed to download document #${documentId} ` +
      `(${response.status}): ${detail}`
    );
  }

  const blob = await response.blob();
  const objectUrl = window.URL.createObjectURL(blob);

  const anchor = document.createElement('a');

  anchor.href = objectUrl;
  anchor.download = filename || `document_${documentId}`;

  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();

  // Revoke after the browser has had a chance to begin the download.
  window.setTimeout(() => {
    window.URL.revokeObjectURL(objectUrl);
  }, 1000);
}

export function getDocumentDownloadUrl(documentId) {
  return `${API_BASE_URL}/api/documents/${documentId}/download`;
}

// ---------------------------------------------------------------------------
// PUBLIC PATIENT REGISTRATION
// ---------------------------------------------------------------------------

/**
 * Public patient registration.
 *
 * The backend must enforce patient-only registration and assign
 * the role and patient association itself.
 */
export async function registerPatientAccount(payload) {
  if (!payload || typeof payload !== 'object') {
    throw new Error('Please provide valid registration details.');
  }

  const response = await safeFetch(
    `${API_BASE_URL}/api/auth/register-patient`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
    'creating a patient account'
  );

  return handleResponse(
    response,
    'patient registration'
  );
}

// ---------------------------------------------------------------------------
// EXPORTS
// ---------------------------------------------------------------------------

export { API_BASE_URL };