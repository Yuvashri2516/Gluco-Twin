import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import PatientOverview from './components/PatientOverview';
import MonitoringCards from './components/MonitoringCards';
import GlucoseChart from './components/GlucoseChart';
import VitalsChart from './components/VitalsChart';
import DigitalTwinPanel from './components/DigitalTwinPanel';
import PredictionsPanel from './components/PredictionsPanel';
import AlertsPanel from './components/AlertsPanel';
import WhatIfSimulation from './components/WhatIfSimulation';
import LoadingSpinner from './components/Common/LoadingSpinner';
import ErrorBanner from './components/Common/ErrorBanner';
import {
  fetchHealth,
  fetchPatients,
  fetchGlucoseReadings,
  fetchVitalReadings,
  fetchAlerts,
} from './api/client';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  // Data states
  const [patients, setPatients] = useState([]);
  const [selectedPatientId, setSelectedPatientId] = useState(null);
  const [hours, setHours] = useState(24);
  const [glucoseReadings, setGlucoseReadings] = useState([]);
  const [vitalReadings, setVitalReadings] = useState([]);
  const [activeNotifications, setActiveNotifications] = useState([]);

  // UI / Status states
  const [isLoadingPatients, setIsLoadingPatients] = useState(true);
  const [isLoadingReadings, setIsLoadingReadings] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);
  const [error, setError] = useState(null);

  // Load active notifications
  const loadNotifications = useCallback(async () => {
    try {
      const data = await fetchAlerts({ status: 'active' });
      setActiveNotifications(data);
    } catch {
      // background sync
    }
  }, []);

  // 1. Initial Load: Check Health, Fetch Patient Roster, and Active Notifications
  const loadPatientsAndHealth = useCallback(async () => {
    setIsLoadingPatients(true);
    setError(null);
    try {
      // Check health
      try {
        await fetchHealth();
        setBackendOnline(true);
      } catch {
        setBackendOnline(false);
      }

      // Fetch patients from real API
      const patientList = await fetchPatients();
      setPatients(patientList);

      if (patientList.length > 0) {
        setSelectedPatientId((prev) => {
          const exists = patientList.some((p) => p.id === prev);
          return exists ? prev : patientList[0].id;
        });
      }

      // Fetch active notifications
      loadNotifications();
    } catch (err) {
      setError(err.message || 'Failed to connect to GlucoTwin backend API.');
      setBackendOnline(false);
    } finally {
      setIsLoadingPatients(false);
    }
  }, [loadNotifications]);

  useEffect(() => {
    loadPatientsAndHealth();
  }, [loadPatientsAndHealth]);

  // 2. Fetch Time-Series Readings when Selected Patient or Hours Window changes
  const loadPatientReadings = useCallback(async (patientId, windowHours, signal) => {
    if (!patientId) return;
    setIsLoadingReadings(true);
    setGlucoseReadings([]);
    setVitalReadings([]);
    setError(null);
    try {
      const [glucoseData, vitalsData] = await Promise.all([
        fetchGlucoseReadings(patientId, windowHours, signal),
        fetchVitalReadings(patientId, windowHours, signal),
      ]);
      setGlucoseReadings(glucoseData);
      setVitalReadings(vitalsData);
      setBackendOnline(true);
    } catch (err) {
      if (err.name === 'AbortError') return;
      setError(err.message || 'Error fetching telemetry readings for active patient.');
    } finally {
      setIsLoadingReadings(false);
    }
  }, []);

  useEffect(() => {
    if (selectedPatientId) {
      const controller = new AbortController();
      loadPatientReadings(selectedPatientId, hours, controller.signal);
      return () => controller.abort();
    }
  }, [selectedPatientId, hours, loadPatientReadings]);

  // Handle Manual Refresh
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await loadPatientsAndHealth();
      if (selectedPatientId) {
        await loadPatientReadings(selectedPatientId, hours);
      }
      await loadNotifications();
    } finally {
      setIsRefreshing(false);
    }
  };

  const selectedPatient = patients.find((p) => p.id === selectedPatientId) || null;

  return (
    <div className="app-layout">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        isMobileOpen={isMobileOpen}
        onCloseMobile={() => setIsMobileOpen(false)}
        unreadAlertsCount={activeNotifications.length}
        backendOnline={backendOnline}
      />

      <div className="main-wrapper">
        {/* Top Header Bar */}
        <Topbar
          patients={patients}
          selectedPatientId={selectedPatientId}
          onSelectPatient={setSelectedPatientId}
          hours={hours}
          onChangeHours={setHours}
          backendOnline={backendOnline}
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
          onOpenMobileSidebar={() => setIsMobileOpen(true)}
          notifications={activeNotifications}
          onNavigateTab={setActiveTab}
        />

        {/* Main Content Dashboard */}
        <main className="content-container">
          {/* Global Error Banner */}
          {error && <ErrorBanner message={error} onRetry={handleRefresh} />}

          {/* Initial Loading State */}
          {isLoadingPatients && (
            <div style={{ padding: '60px 0' }}>
              <LoadingSpinner message="Connecting to GlucoTwin backend and fetching patient cohort..." />
            </div>
          )}

          {!isLoadingPatients && (
            <>
              {/* TAB 1: OVERVIEW */}
              {activeTab === 'overview' && (
                <>
                  <PatientOverview
                    patients={patients}
                    selectedPatient={selectedPatient}
                    onSelectPatient={setSelectedPatientId}
                    isLoading={isLoadingPatients}
                  />

                  <MonitoringCards
                    glucoseReadings={glucoseReadings}
                    vitalReadings={vitalReadings}
                    isLoading={isLoadingReadings}
                  />

                  <GlucoseChart
                    readings={glucoseReadings}
                    isLoading={isLoadingReadings}
                    hours={hours}
                  />

                  <VitalsChart
                    readings={vitalReadings}
                    isLoading={isLoadingReadings}
                    hours={hours}
                  />

                  <DigitalTwinPanel
                    selectedPatient={selectedPatient}
                    glucoseReadings={glucoseReadings}
                    vitalReadings={vitalReadings}
                  />

                  <PredictionsPanel selectedPatient={selectedPatient} />

                  <AlertsPanel
                    selectedPatient={selectedPatient}
                    onSelectPatient={setSelectedPatientId}
                    onAlertsUpdated={loadNotifications}
                  />

                  <WhatIfSimulation selectedPatient={selectedPatient} />
                </>
              )}

              {/* TAB 2: PATIENTS */}
              {activeTab === 'patients' && (
                <div className="section-container">
                  <div className="section-header-banner">
                    <h2 className="section-title">Cohort &amp; Patient Profiles</h2>
                    <p className="section-desc">
                      Demographic records, clinical types, and baseline physical scale fetched from the SQLite database.
                    </p>
                  </div>
                  <PatientOverview
                    patients={patients}
                    selectedPatient={selectedPatient}
                    onSelectPatient={setSelectedPatientId}
                    isLoading={isLoadingPatients}
                  />
                </div>
              )}

              {/* TAB 3: GLUCOSE MONITORING */}
              {activeTab === 'glucose' && (
                <div className="section-container">
                  <div className="section-header-banner">
                    <h2 className="section-title">Continuous Glucose Telemetry</h2>
                    <p className="section-desc">
                      Sensor time-series, target in-range metrics (70-180 mg/dL), and historical glycemic curve.
                    </p>
                  </div>
                  <MonitoringCards
                    glucoseReadings={glucoseReadings}
                    vitalReadings={vitalReadings}
                    isLoading={isLoadingReadings}
                  />
                  <GlucoseChart
                    readings={glucoseReadings}
                    isLoading={isLoadingReadings}
                    hours={hours}
                  />
                </div>
              )}

              {/* TAB 4: VITAL SIGNS */}
              {activeTab === 'vitals' && (
                <div className="section-container">
                  <h2 className="section-title" style={{ marginBottom: '6px' }}>Autonomic &amp; Cardiovascular Monitoring</h2>
                  <p className="section-desc" style={{ marginBottom: '20px' }}>
                    Heart rate telemetry and RMSSD heart rate variability synchronised with glucose events.
                  </p>
                  <MonitoringCards
                    glucoseReadings={glucoseReadings}
                    vitalReadings={vitalReadings}
                    isLoading={isLoadingReadings}
                  />
                  <VitalsChart
                    readings={vitalReadings}
                    isLoading={isLoadingReadings}
                    hours={hours}
                  />
                </div>
              )}

              {/* TAB 5: DIGITAL TWIN */}
              {activeTab === 'twin' && (
                <>
                  <DigitalTwinPanel
                    selectedPatient={selectedPatient}
                    glucoseReadings={glucoseReadings}
                    vitalReadings={vitalReadings}
                  />
                  <WhatIfSimulation selectedPatient={selectedPatient} />
                </>
              )}

              {/* TAB 6: PREDICTIONS */}
              {activeTab === 'predictions' && (
                <PredictionsPanel selectedPatient={selectedPatient} />
              )}

              {/* TAB 7: ALERTS */}
              {activeTab === 'alerts' && (
                <AlertsPanel
                  selectedPatient={selectedPatient}
                  onSelectPatient={setSelectedPatientId}
                  onAlertsUpdated={loadNotifications}
                />
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
