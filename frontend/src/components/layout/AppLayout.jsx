import React from 'react';
import SyntheticNotice from '../common/SyntheticNotice';
import TopNav from './TopNav';
import SidebarNav from './SidebarNav';
import Footer from './Footer';

/**
 * Global Application Layout Frame
 */
export default function AppLayout({
  children,
  patients,
  activePatientId,
  onSelectPatient,
  currentScreen,
  onNavigate,
  unreadAlertCount
}) {
  return (
    <div className="app-container">
      {/* 1. Persistent Top Safety Banner */}
      <SyntheticNotice />

      {/* 2. Top Navigation Bar */}
      <TopNav
        patients={patients}
        activePatientId={activePatientId}
        onSelectPatient={onSelectPatient}
        unreadAlertCount={unreadAlertCount}
        onAlertClick={() => onNavigate('alerts')}
      />

      {/* 3. Main Body: Sidebar + Dynamic Workspace */}
      <div className="app-body">
        <SidebarNav
          currentScreen={currentScreen}
          onNavigate={onNavigate}
          alertCount={unreadAlertCount}
        />

        <main className="app-main">
          {children}
        </main>
      </div>

      {/* 4. Global Footer */}
      <Footer />
    </div>
  );
}
