/**
 * API client for GlucoTwin backend
 */

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');

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
  const response = await fetch(`${API_BASE_URL}/api/patients`);
  return handleResponse(response, 'patients list');
}

export async function fetchPatient(patientId) {
  const response = await fetch(`${API_BASE_URL}/api/patients/${patientId}`);
  return handleResponse(response, `patient #${patientId}`);
}

export async function fetchGlucoseReadings(patientId, hours = 24) {
  const response = await fetch(`${API_BASE_URL}/api/readings/glucose/${patientId}?hours=${hours}`);
  return handleResponse(response, `glucose readings for patient #${patientId}`);
}

export async function fetchVitalReadings(patientId, hours = 24) {
  const response = await fetch(`${API_BASE_URL}/api/readings/vitals/${patientId}?hours=${hours}`);
  return handleResponse(response, `vital readings for patient #${patientId}`);
}

export async function predictGlucoseSpike(patientId, signal) {
  const response = await fetch(`${API_BASE_URL}/api/predictions/glucose-spike`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ patient_id: patientId }),
    signal,
  });
  return handleResponse(response, `glucose-spike prediction for patient #${patientId}`);
}

export async function fetchAlerts({ patientId, status, source, severity } = {}, signal) {
  const params = new URLSearchParams();
  if (patientId) params.append('patient_id', patientId);
  if (status) params.append('status', status);
  if (source) params.append('source', source);
  if (severity) params.append('severity', severity);
  const qs = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE_URL}/api/alerts${qs}`, { signal });
  return handleResponse(response, 'alerts list');
}

export async function fetchAlert(alertId, signal) {
  const response = await fetch(`${API_BASE_URL}/api/alerts/${alertId}`, { signal });
  return handleResponse(response, `alert #${alertId}`);
}

export async function acknowledgeAlert(alertId) {
  const response = await fetch(`${API_BASE_URL}/api/alerts/${alertId}/acknowledge`, {
    method: 'POST',
  });
  return handleResponse(response, `acknowledging alert #${alertId}`);
}

export async function resolveAlert(alertId) {
  const response = await fetch(`${API_BASE_URL}/api/alerts/${alertId}/resolve`, {
    method: 'POST',
  });
  return handleResponse(response, `resolving alert #${alertId}`);
}

export async function evaluateAlerts(patientId = null) {
  const response = await fetch(`${API_BASE_URL}/api/alerts/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patientId ? { patient_id: patientId } : {}),
  });
  return handleResponse(response, 'evaluating alerts');
}

export async function fetchDigitalTwinDetail(patientId, signal) {
  const response = await fetch(`${API_BASE_URL}/api/digital-twin/${patientId}`, { signal });
  return handleResponse(response, `digital twin intelligence for patient #${patientId}`);
}

export async function runWhatIfSimulation({ patientId, additionalCarbs = 30.0, activityMinutes = 0.0, asOfGlucose = null }, signal) {
  const response = await fetch(`${API_BASE_URL}/api/simulation/what-if`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      patient_id: patientId,
      additional_carbs_g: additionalCarbs,
      activity_minutes: activityMinutes,
      as_of_glucose: asOfGlucose,
    }),
    signal,
  });
  return handleResponse(response, `what-if simulation for patient #${patientId}`);
}

export { API_BASE_URL };
