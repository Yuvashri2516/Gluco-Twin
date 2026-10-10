import React, { useState, useEffect } from 'react';
import AppLayout from './components/layout/AppLayout';
import OverviewScreen from './screens/OverviewScreen';
import PatientHistoryScreen from './screens/PatientHistoryScreen';
import MonitoringScreen from './screens/MonitoringScreen';
import PredictionXaiScreen from './screens/PredictionXaiScreen';
import SimulationScreen from './screens/SimulationScreen';
import AlertCentreScreen from './screens/AlertCentreScreen';
import { apiClient } from './services/apiClient';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState('overview');
  const [patients, setPatients] = useState([]);
  const [activePatientId, setActivePatientId] = useState('GT-9042');
  const [activePatient, setActivePatient] = useState(null);
  const [telemetry, setTelemetry] = useState([]);
  const [predictions, setPredictions] = useState(null);
  const [xaiFeatures, setXaiFeatures] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [twinStatus, setTwinStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load initial patients & alerts
  useEffect(() => {
    async function loadInitialData() {
      try {
        const [pts, alts] = await Promise.all([
          apiClient.getPatients(),
          apiClient.getAlerts()
        ]);
        setPatients(pts);
        setAlerts(alts);
      } catch (err) {
        console.error('Failed to load initial data:', err);
      }
    }
    loadInitialData();
  }, []);

  // Load patient-specific data when active patient changes
  useEffect(() => {
    async function loadPatientData() {
      setLoading(true);
      try {
        const [pt, telem, preds, xai, twin] = await Promise.all([
          apiClient.getPatientById(activePatientId),
          apiClient.getTelemetry(activePatientId, 4),
          apiClient.getPredictions(activePatientId),
          apiClient.getXaiFeatures(activePatientId),
          apiClient.getTwinStatus(activePatientId)
        ]);
        setActivePatient(pt);
        setTelemetry(telem);
        setPredictions(preds);
        setXaiFeatures(xai);
        setTwinStatus(twin);
      } catch (err) {
        console.error('Failed to load patient data:', err);
      } finally {
        setLoading(false);
      }
    }

    if (activePatientId) {
      loadPatientData();
    }
  }, [activePatientId]);

  // Handle alert acknowledgement
  const handleAcknowledgeAlert = async (alertId) => {
    try {
      await apiClient.acknowledgeAlert(alertId);
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, status: 'acknowledged' } : a))
      );
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  // Handle alert escalation
  const handleEscalateAlert = async (alertId) => {
    try {
      await apiClient.escalateAlert(alertId);
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, status: 'escalated' } : a))
      );
    } catch (err) {
      console.error('Failed to escalate alert:', err);
    }
  };

  const unreadAlertCount = alerts.filter((a) => a.status === 'unacknowledged').length;

  return (
    <AppLayout
      patients={patients}
      activePatientId={activePatientId}
      onSelectPatient={setActivePatientId}
      currentScreen={currentScreen}
      onNavigate={setCurrentScreen}
      unreadAlertCount={unreadAlertCount}
    >
      {currentScreen === 'overview' && (
        <OverviewScreen
          patient={activePatient}
          telemetry={telemetry}
          predictions={predictions}
          xaiFeatures={xaiFeatures}
          alerts={alerts}
          twinStatus={twinStatus}
          onAcknowledgeAlert={handleAcknowledgeAlert}
          onNavigate={setCurrentScreen}
        />
      )}

      {currentScreen === 'history' && (
        <PatientHistoryScreen patient={activePatient} />
      )}

      {currentScreen === 'monitoring' && (
        <MonitoringScreen
          telemetry={telemetry}
          predictions={predictions}
          twinStatus={twinStatus}
        />
      )}

      {currentScreen === 'prediction' && (
        <PredictionXaiScreen
          telemetry={telemetry}
          predictions={predictions}
          xaiFeatures={xaiFeatures}
        />
      )}

      {currentScreen === 'simulation' && (
        <SimulationScreen />
      )}

      {currentScreen === 'alerts' && (
        <AlertCentreScreen
          alerts={alerts}
          onAcknowledge={handleAcknowledgeAlert}
          onEscalate={handleEscalateAlert}
        />
      )}
    </AppLayout>
  );
}
