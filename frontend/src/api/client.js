/**
 * API client for GlucoTwin backend
 */

/**
 * Resolves the backend API base URL with proper environment and mode fallbacks.
 *
 * Priority:
 * 1. Explicit import.meta.env.VITE_API_BASE_URL (configured in Vercel or local .env)
 * 2. Production fallback: https://gluco-twin.onrender.com (prevents querying 127.0.0.1 in production)
 * 3. Development fallback: http://127.0.0.1:8000
 */
export function resolveApiBaseUrl() {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.trim() !== '') {
    return envUrl.trim().replace(/\/+$/, '');
  }
  if (import.meta.env.PROD) {
    return 'https://gluco-twin.onrender.com';
  }
  return 'http://127.0.0.1:8000';
}

const API_BASE_URL = resolveApiBaseUrl();

// ---------------------------------------------------------------------------
// Authentication & Session Management (Phase A)
// ---------------------------------------------------------------------------
let currentAuthToken = localStorage.getItem('glucotwin_auth_token') || null;
let currentAuthUser = null;
try {
  const cachedUser = localStorage.getItem('glucotwin_auth_user');
  if (cachedUser) currentAuthUser = JSON.parse(cachedUser);
} catch {
  currentAuthUser = null;
}

export function getAuthToken() {
  return currentAuthToken;
}

export function getCurrentUser() {
  return currentAuthUser;
}

export function setAuthSession(token, user) {
  currentAuthToken = token;
  currentAuthUser = user;
  if (token) {
    localStorage.setItem('glucotwin_auth_token', token);
  } else {
    localStorage.removeItem('glucotwin_auth_token');
  }
  if (user) {
    localStorage.setItem('glucotwin_auth_user', JSON.stringify(user));
  } else {
    localStorage.removeItem('glucotwin_auth_user');
  }
  // Dispatch event for reactive UI updates
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('glucotwin:auth_changed', {
      detail: { token: currentAuthToken, user: currentAuthUser }
    }));
  }
}

export function clearAuthSession() {
  setAuthSession(null, null);
}

export function isAuthenticated() {
  return Boolean(currentAuthToken);
}

export async function loginUser(username, password) {
  const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  const data = await handleResponse(res, 'user authentication');
  setAuthSession(data.access_token, data.user);
  return data;
}

export function logoutUser() {
  clearAuthSession();
}

export async function authFetch(url, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (currentAuthToken && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${currentAuthToken}`;
  }
  const response = await fetch(url, { ...options, headers });
  if (response.status === 401) {
    // Invalidate stale or expired session and trigger transition to login screen
    clearAuthSession();
  }
  return response;
}

async function handleResponse(response, endpointName) {
  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errorJson = await response.json();
      if (errorJson && errorJson.detail) {
        errorDetail = errorJson.detail;
      }
    } catch {
      // ignore json parse error on error response
    }
    const error = new Error(`Failed to load ${endpointName} (${response.status}): ${errorDetail}`);
    error.status = response.status;
    error.detail = errorDetail;
    throw error;
  }
  return response.json();
}

export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  return handleResponse(response, 'health status');
}

export async function fetchPatients() {
  const response = await authFetch(`${API_BASE_URL}/api/patients`);
  return handleResponse(response, 'patients list');
}

export async function fetchPatient(patientId) {
  const response = await authFetch(`${API_BASE_URL}/api/patients/${patientId}`);
  return handleResponse(response, `patient #${patientId}`);
}

export async function fetchGlucoseReadings(patientId, hours = 24, signal) {
  const response = await authFetch(`${API_BASE_URL}/api/readings/glucose/${patientId}?hours=${hours}`, { signal });
  return handleResponse(response, `glucose readings for patient #${patientId}`);
}

export async function fetchVitalReadings(patientId, hours = 24, signal) {
  const response = await authFetch(`${API_BASE_URL}/api/readings/vitals/${patientId}?hours=${hours}`, { signal });
  return handleResponse(response, `vital readings for patient #${patientId}`);
}

export async function fetchTwinState(patientId, signal) {
  const response = await authFetch(`${API_BASE_URL}/api/twin/${patientId}`, { signal });
  return handleResponse(response, `digital twin state for patient #${patientId}`);
}

export async function fetchAlerts(params = {}, signal) {
  const query = new URLSearchParams();
  if (params.patientId !== undefined && params.patientId !== null) query.append('patient_id', params.patientId);
  if (params.status) query.append('status', params.status);
  if (params.severity) query.append('severity', params.severity);
  if (params.source) query.append('source', params.source);
  if (params.limit) query.append('limit', params.limit);

  const queryString = query.toString();
  const endpoint = queryString ? `${API_BASE_URL}/api/alerts?${queryString}` : `${API_BASE_URL}/api/alerts`;
  const response = await authFetch(endpoint, { signal });
  return handleResponse(response, 'alerts');
}

export async function acknowledgeAlert(alertId) {
  const response = await authFetch(`${API_BASE_URL}/api/alerts/${alertId}/acknowledge`, {
    method: 'POST',
  });
  return handleResponse(response, `acknowledging alert #${alertId}`);
}

export async function resolveAlert(alertId) {
  const response = await authFetch(`${API_BASE_URL}/api/alerts/${alertId}/resolve`, {
    method: 'POST',
  });
  return handleResponse(response, `resolving alert #${alertId}`);
}

export async function evaluateAlerts(patientId = null) {
  const response = await authFetch(`${API_BASE_URL}/api/alerts/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ patient_id: patientId }),
  });
  return handleResponse(response, 'evaluating alerts');
}

export async function predictGlucoseSpike(patientId, signal) {
  const response = await authFetch(`${API_BASE_URL}/api/predictions/glucose-spike`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ patient_id: patientId }),
    signal,
  });
  return handleResponse(response, `glucose spike prediction for patient #${patientId}`);
}

export async function fetchPatientLabs(patientId, signal) {
  const response = await authFetch(`${API_BASE_URL}/api/patients/${patientId}/labs`, { signal });
  return handleResponse(response, `laboratory results for patient #${patientId}`);
}

export async function fetchPatientGenetics(patientId, signal) {
  const response = await authFetch(`${API_BASE_URL}/api/patients/${patientId}/genetics`, { signal });
  return handleResponse(response, `genetic markers for patient #${patientId}`);
}

export async function fetchSleepReadings(patientId, hours = 24, signal) {
  const response = await authFetch(`${API_BASE_URL}/api/readings/sleep/${patientId}?hours=${hours}`, { signal });
  return handleResponse(response, `sleep telemetry for patient #${patientId}`);
}

export async function fetchStepReadings(patientId, hours = 24, signal) {
  const response = await authFetch(`${API_BASE_URL}/api/readings/steps/${patientId}?hours=${hours}`, { signal });
  return handleResponse(response, `step telemetry for patient #${patientId}`);
}

export async function fetchDigitalTwinDetail(patientId, signal) {
  const response = await authFetch(`${API_BASE_URL}/api/digital-twin/${patientId}`, { signal });
  return handleResponse(response, `digital twin intelligence for patient #${patientId}`);
}

export async function runWhatIfSimulation(patientId, carbsGrams, activityMinutes) {
  const response = await authFetch(`${API_BASE_URL}/api/simulation/what-if`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      patient_id: patientId,
      carbohydrates_grams: carbsGrams,
      activity_minutes: activityMinutes,
    }),
  });
  return handleResponse(response, `what-if simulation for patient #${patientId}`);
}

export async function simulateSensorFeed(patientId) {
  const response = await authFetch(`${API_BASE_URL}/api/digital-twin/simulate-feed`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ patient_id: patientId }),
  });
  return handleResponse(response, `simulated sensor epoch for patient #${patientId}`);
}

// ---------------------------------------------------------------------------
// Phase 1 & 2: Patient Registration & Manual Data Ingestion
// ---------------------------------------------------------------------------
export async function createPatient(patientData) {
  const response = await authFetch(`${API_BASE_URL}/api/patients`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patientData),
  });
  return handleResponse(response, 'creating patient');
}

export async function updatePatient(patientId, updateData) {
  const response = await authFetch(`${API_BASE_URL}/api/patients/${patientId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updateData),
  });
  return handleResponse(response, `updating patient #${patientId}`);
}

export async function recordManualGlucose({ patientId, value, unit = 'mg/dL', timestamp = null, dataSource = 'manual' }) {
  const response = await authFetch(`${API_BASE_URL}/api/readings/glucose`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      patient_id: Number(patientId),
      value: parseFloat(value),
      unit,
      timestamp,
      data_source: dataSource,
    }),
  });
  return handleResponse(response, 'recording manual glucose');
}

export async function recordManualVitals({ patientId, heartRate = null, hrv = null, timestamp = null, dataSource = 'manual' }) {
  const payload = {
    patient_id: Number(patientId),
    data_source: dataSource,
    timestamp,
  };
  if (heartRate !== null && heartRate !== '') payload.heart_rate = parseFloat(heartRate);
  if (hrv !== null && hrv !== '') payload.hrv = parseFloat(hrv);

  const response = await authFetch(`${API_BASE_URL}/api/readings/vitals`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse(response, 'recording manual vitals');
}

export async function recordManualLab(patientId, { testName, result, unit, referenceRange = null, measurementDate = null, labSource = null, dataSource = 'manual' }) {
  const response = await authFetch(`${API_BASE_URL}/api/patients/${patientId}/labs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      patient_id: Number(patientId),
      test_name: testName,
      result: parseFloat(result),
      unit,
      reference_range: referenceRange,
      measurement_date: measurementDate,
      lab_source: labSource,
      data_source: dataSource,
    }),
  });
  return handleResponse(response, `recording lab result for patient #${patientId}`);
}

export async function recordManualDiagnosis(patientId, { diagnosisName, date = null, notes = null, status = 'active' }) {
  const response = await authFetch(`${API_BASE_URL}/api/patients/${patientId}/diagnoses`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      patient_id: Number(patientId),
      diagnosis_name: diagnosisName,
      date: date || null,
      notes: notes || null,
      status,
    }),
  });
  return handleResponse(response, 'recording diagnosis and clinical history');
}

// ---------------------------------------------------------------------------
// Phase 3 & 4: Medical Documents & Intelligence API Methods
// ---------------------------------------------------------------------------
export async function uploadMedicalDocument(patientId, file, documentCategory = 'lab_report') {
  const formData = new FormData();
  formData.append('patient_id', patientId);
  formData.append('document_category', documentCategory);
  formData.append('file', file);

  const response = await authFetch(`${API_BASE_URL}/api/documents/upload`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse(response, 'uploading medical document');
}

export async function fetchPatientDocuments(patientId, signal) {
  const response = await authFetch(`${API_BASE_URL}/api/documents/patient/${patientId}`, { signal });
  return handleResponse(response, `documents list for patient #${patientId}`);
}

export async function fetchDocumentPreview(documentId, signal) {
  const response = await authFetch(`${API_BASE_URL}/api/documents/${documentId}/preview`, { signal });
  return handleResponse(response, `document preview #${documentId}`);
}

export async function confirmDocumentExtraction(documentId, { confirmedLabs = [], confirmedReadings = [], clinicalNotes = '' }) {
  const response = await authFetch(`${API_BASE_URL}/api/documents/${documentId}/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      confirmed_labs: confirmedLabs,
      confirmed_readings: confirmedReadings,
      clinical_notes: clinicalNotes,
    }),
  });
  return handleResponse(response, `confirming extraction for document #${documentId}`);
}

export async function cancelDocumentExtraction(documentId) {
  const response = await authFetch(`${API_BASE_URL}/api/documents/${documentId}/cancel`, {
    method: 'POST',
  });
  return handleResponse(response, `cancelling extraction for document #${documentId}`);
}

export async function deleteMedicalDocument(documentId) {
  const response = await authFetch(`${API_BASE_URL}/api/documents/${documentId}`, {
    method: 'DELETE',
  });
  return handleResponse(response, `deleting document #${documentId}`);
}

export async function downloadDocumentFile(documentId, filename = null) {
  const res = await authFetch(`${API_BASE_URL}/api/documents/${documentId}/download`);
  if (!res.ok) {
    throw new Error(`Failed to download document #${documentId} (${res.status})`);
  }
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename || `document_${documentId}`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

export function getDocumentDownloadUrl(documentId) {
  return `${API_BASE_URL}/api/documents/${documentId}/download`;
}

export { API_BASE_URL };
