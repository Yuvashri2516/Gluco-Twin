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
import PatientEhrHistory from './components/PatientEhrHistory';
import SleepActivityPanel from './components/SleepActivityPanel';
import AddReadingPanel from './components/AddReadingPanel';
import MedicalDocumentsPanel from './components/MedicalDocumentsPanel';
import ReviewExtractedDataPanel from './components/ReviewExtractedDataPanel';
import PatientModal from './components/PatientModal';
import LoadingSpinner from './components/Common/LoadingSpinner';
import ErrorBanner from './components/Common/ErrorBanner';
import LoginScreen from './components/LoginScreen';
import {
  fetchHealth,
  fetchPatients,
  fetchGlucoseReadings,
  fetchVitalReadings,
  fetchAlerts,
  getCurrentUser,
  getAuthToken,
  logoutUser,
} from './api/client';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  // Authentication states
  const [currentUser, setCurrentUser] = useState(() => getCurrentUser());
  const [authToken, setAuthToken] = useState(() => getAuthToken());

  // Data states
  const [patients, setPatients] = useState([]);
  const [selectedPatientId, setSelectedPatientId] = useState(null);
  const [hours, setHours] = useState(24);
  const [glucoseReadings, setGlucoseReadings] = useState([]);
  const [vitalReadings, setVitalReadings] = useState([]);
  const [activeNotifications, setActiveNotifications] = useState([]);

  // UI / Modal / Review states
  const [isLoadingPatients, setIsLoadingPatients] = useState(true);
  const [isLoadingReadings, setIsLoadingReadings] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);
  const [error, setError] = useState(null);

  // Patient Registration & Edit Modal
  const [isPatientModalOpen, setIsPatientModalOpen] = useState(false);
  const [patientModalMode, setPatientModalMode] = useState('create'); // 'create' | 'edit'

  // Document Intelligence Review Target
  const [activeReviewDocId, setActiveReviewDocId] = useState(null);

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
  const loadPatientsAndHealth = useCallback(async (targetPatientIdToSelect = null) => {
    setIsLoadingPatients(true);
    setError(null);
    try {
      try {
        await fetchHealth();
        setBackendOnline(true);
      } catch {
        setBackendOnline(false);
      }

      const patientList = await fetchPatients();
      setPatients(patientList);

      if (patientList.length > 0) {
        if (targetPatientIdToSelect) {
          setSelectedPatientId(targetPatientIdToSelect);
        } else {
          setSelectedPatientId((prev) => {
            const exists = patientList.some((p) => p.id === prev);
            return exists ? prev : patientList[0].id;
          });
        }
      }

      loadNotifications();
    } catch (err) {
      setError(err.message || 'Failed to connect to GlucoTwin backend API.');
      setBackendOnline(false);
    } finally {
      setIsLoadingPatients(false);
    }
  }, [loadNotifications]);

  // Listen to global auth session state changes
  useEffect(() => {
    const handleAuthChange = (e) => {
      setAuthToken(e.detail.token);
      setCurrentUser(e.detail.user);
    };
    window.addEventListener('glucotwin:auth_changed', handleAuthChange);
    return () => window.removeEventListener('glucotwin:auth_changed', handleAuthChange);
  }, []);

  // Fetch initial data only when authenticated
  useEffect(() => {
    if (authToken) {
      loadPatientsAndHealth();
    } else {
      setIsLoadingPatients(false);
      setPatients([]);
      setSelectedPatientId(null);
    }
  }, [authToken, loadPatientsAndHealth]);

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

  // Callback after saving manual reading or confirming document extraction
  const handleDataIngested = async () => {
    if (selectedPatientId) {
      await loadPatientReadings(selectedPatientId, hours);
    }
    await loadNotifications();
  };

  // Patient Modal Open Handlers
  const handleOpenAddPatient = () => {
    setPatientModalMode('create');
    setIsPatientModalOpen(true);
  };

  const handleOpenEditPatient = () => {
    setPatientModalMode('edit');
    setIsPatientModalOpen(true);
  };

  const handlePatientSaved = (savedPatient) => {
    // Refresh roster and select the new/updated patient
    loadPatientsAndHealth(savedPatient.id);
  };

  // Transition from Documents to Review Draft
  const handleOpenReview = (docId) => {
    setActiveReviewDocId(docId);
    setActiveTab('review_extraction');
  };

  const selectedPatient = patients.find((p) => p.id === selectedPatientId) || null;

  if (!authToken) {
    return (
      <LoginScreen
        onLoginSuccess={(user) => {
          setCurrentUser(user);
          setAuthToken(getAuthToken());
        }}
      />
    );
  }

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
        onOpenAddPatient={handleOpenAddPatient}
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
          onOpenAddPatient={handleOpenAddPatient}
          onOpenEditPatient={handleOpenEditPatient}
          currentUser={currentUser}
          onLogout={logoutUser}
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
              {/* TAB 1: PATIENT OVERVIEW */}
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

                  <SleepActivityPanel
                    selectedPatient={selectedPatient}
                    hours={hours}
                  />

                  <DigitalTwinPanel
                    selectedPatient={selectedPatient}
                    glucoseReadings={glucoseReadings}
                    vitalReadings={vitalReadings}
                    onFeedIngested={handleRefresh}
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

              {/* TAB 2: PATIENT & EHR HISTORY */}
              {(activeTab === 'ehr' || activeTab === 'patients') && (
                <>
                  <PatientOverview
                    patients={patients}
                    selectedPatient={selectedPatient}
                    onSelectPatient={setSelectedPatientId}
                    isLoading={isLoadingPatients}
                  />
                  <PatientEhrHistory selectedPatient={selectedPatient} />
                </>
              )}

              {/* TAB 3: ADD READING (MANUAL MEDICAL ENTRY) */}
              {activeTab === 'add_reading' && (
                <AddReadingPanel
                  selectedPatient={selectedPatient}
                  onDataSaved={handleDataIngested}
                />
              )}

              {/* TAB 4: MEDICAL DOCUMENTS & UPLOADS */}
              {activeTab === 'documents' && (
                <MedicalDocumentsPanel
                  selectedPatient={selectedPatient}
                  onOpenReview={handleOpenReview}
                  onDocumentConfirmed={handleDataIngested}
                />
              )}

              {/* TAB 5: REVIEW EXTRACTED DATA */}
              {activeTab === 'review_extraction' && (
                <ReviewExtractedDataPanel
                  documentId={activeReviewDocId}
                  selectedPatient={selectedPatient}
                  onBackToDocuments={() => setActiveTab('documents')}
                  onConfirmSuccess={handleDataIngested}
                />
              )}

              {/* TAB 6: DIGITAL TWIN */}
              {activeTab === 'twin' && (
                <>
                  <DigitalTwinPanel
                    selectedPatient={selectedPatient}
                    glucoseReadings={glucoseReadings}
                    vitalReadings={vitalReadings}
                    onFeedIngested={handleRefresh}
                  />
                  <WhatIfSimulation selectedPatient={selectedPatient} />
                </>
              )}

              {/* TAB 7: GLUCOSE TELEMETRY */}
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

              {/* TAB 8: AUTONOMIC VITALS */}
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

              {/* TAB 9: SLEEP & ACTIVITY */}
              {activeTab === 'sleep_activity' && (
                <SleepActivityPanel
                  selectedPatient={selectedPatient}
                  hours={hours}
                />
              )}

              {/* TAB 10: PREDICTIONS */}
              {activeTab === 'predictions' && (
                <PredictionsPanel selectedPatient={selectedPatient} />
              )}

              {/* TAB 11: ALERTS */}
              {activeTab === 'alerts' && (
                <AlertsPanel
                  selectedPatient={selectedPatient}
                  onSelectPatient={setSelectedPatientId}
                  onAlertsUpdated={loadNotifications}
                />
              )}

              {/* TAB 12: WHAT-IF SIMULATION */}
              {activeTab === 'simulation' && (
                <div className="section-container">
                  <WhatIfSimulation selectedPatient={selectedPatient} />
                </div>
              )}
            </>
          )}
        </main>
      </div>

      {/* Patient Registration & Edit Modal */}
      <PatientModal
        isOpen={isPatientModalOpen}
        onClose={() => setIsPatientModalOpen(false)}
        mode={patientModalMode}
        initialData={patientModalMode === 'edit' ? selectedPatient : null}
        onPatientSaved={handlePatientSaved}
      />
    </div>
  );
}
