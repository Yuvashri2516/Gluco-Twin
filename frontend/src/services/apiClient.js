/**
 * GlucoTwin API Service Client
 * Handles HTTP/REST communication with Python FastAPI backend.
 * Automatically falls back to mockDataService when VITE_USE_MOCK_DATA is true.
 * Complies with docs/API_INTEGRATION.md.
 */

import {
  MOCK_PATIENTS,
  generateSyntheticTelemetry,
  generateSyntheticPredictions,
  getMockXaiFeatures,
  simulateCounterfactualResponse,
  MOCK_ALERTS,
  getMockTwinStatus
} from './mockData';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const USE_MOCK = import.meta.env.VITE_USE_MOCK_DATA !== 'false';

// Helper to simulate realistic network delay in mock mode
const simulateLatency = (ms = 120) => new Promise((resolve) => setTimeout(resolve, ms));

export const apiClient = {
  /**
   * Fetch all synthetic patient archetypes
   */
  async getPatients() {
    if (USE_MOCK) {
      await simulateLatency();
      return [...MOCK_PATIENTS];
    }
    const res = await fetch(`${BASE_URL}/api/v1/patients`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  /**
   * Fetch patient profile by ID
   */
  async getPatientById(patientId) {
    if (USE_MOCK) {
      await simulateLatency();
      const patient = MOCK_PATIENTS.find((p) => p.id === patientId) || MOCK_PATIENTS[0];
      return { ...patient };
    }
    const res = await fetch(`${BASE_URL}/api/v1/patients/${patientId}`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  /**
   * Fetch continuous telemetry readings (CGM, HR, HRV)
   */
  async getTelemetry(patientId, hours = 4) {
    if (USE_MOCK) {
      await simulateLatency();
      return generateSyntheticTelemetry(patientId, hours);
    }
    const res = await fetch(`${BASE_URL}/api/v1/patients/${patientId}/telemetry?hours=${hours}`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  /**
   * Fetch forward-looking 2-hour predictions & uncertainty bounds
   */
  async getPredictions(patientId) {
    if (USE_MOCK) {
      await simulateLatency();
      return generateSyntheticPredictions(patientId);
    }
    const res = await fetch(`${BASE_URL}/api/v1/patients/${patientId}/predictions`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  /**
   * Fetch SHAP feature attribution weights for Explainable AI
   */
  async getXaiFeatures(patientId) {
    if (USE_MOCK) {
      await simulateLatency();
      return getMockXaiFeatures(patientId);
    }
    const res = await fetch(`${BASE_URL}/api/v1/patients/${patientId}/xai`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  /**
   * Run What-If Counterfactual simulation
   */
  async runCounterfactualSimulation(params) {
    if (USE_MOCK) {
      await simulateLatency(160);
      return simulateCounterfactualResponse(params);
    }
    const res = await fetch(`${BASE_URL}/api/v1/simulation/counterfactual`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  /**
   * Fetch clinical alerts list
   */
  async getAlerts(status = 'all') {
    if (USE_MOCK) {
      await simulateLatency();
      if (status === 'all') return [...MOCK_ALERTS];
      return MOCK_ALERTS.filter((a) => a.status === status);
    }
    const res = await fetch(`${BASE_URL}/api/v1/alerts?status=${status}`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  /**
   * Acknowledge an alert
   */
  async acknowledgeAlert(alertId, actionTaken = 'Clinical review confirmed') {
    if (USE_MOCK) {
      await simulateLatency(80);
      const alert = MOCK_ALERTS.find((a) => a.id === alertId);
      if (alert) {
        alert.status = 'acknowledged';
        alert.action_taken = actionTaken;
        alert.acknowledged_at = new Date().toISOString();
      }
      return { success: true, alert };
    }
    const res = await fetch(`${BASE_URL}/api/v1/alerts/${alertId}/acknowledge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action_taken: actionTaken })
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  /**
   * Escalate an alert
   */
  async escalateAlert(alertId) {
    if (USE_MOCK) {
      await simulateLatency(80);
      const alert = MOCK_ALERTS.find((a) => a.id === alertId);
      if (alert) {
        alert.status = 'escalated';
        alert.escalated_at = new Date().toISOString();
      }
      return { success: true, alert };
    }
    const res = await fetch(`${BASE_URL}/api/v1/alerts/${alertId}/escalate`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  /**
   * Fetch Digital Twin engine status
   */
  async getTwinStatus(patientId) {
    if (USE_MOCK) {
      await simulateLatency();
      return getMockTwinStatus(patientId);
    }
    const res = await fetch(`${BASE_URL}/api/v1/twin/${patientId}/status`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  }
};
