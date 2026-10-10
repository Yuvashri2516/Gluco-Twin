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
    throw new Error(`Failed to load ${endpointName} (${response.status}): ${errorDetail}`);
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

export { API_BASE_URL };
