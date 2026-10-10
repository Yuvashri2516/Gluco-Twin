import React from 'react';
import {
  LayoutDashboard,
  Clock,
  Activity,
  BrainCircuit,
  SlidersHorizontal,
  BellRing,
  Cpu
} from 'lucide-react';

const NAV_ITEMS = [
  { id: 'overview', label: 'Overview Dashboard', icon: LayoutDashboard },
  { id: 'history', label: 'Patient History', icon: Clock },
  { id: 'monitoring', label: 'Glucose Monitoring', icon: Activity },
  { id: 'prediction', label: 'Predictive & XAI', icon: BrainCircuit },
  { id: 'simulation', label: 'What-if Simulation', icon: SlidersHorizontal },
  { id: 'alerts', label: 'Alert Centre', icon: BellRing, badgeKey: 'alerts' }
];

/**
 * Global Sidebar Navigation
 */
export default function SidebarNav({ currentScreen, onNavigate, alertCount = 2 }) {
  return (
    <aside className="app-sidebar" aria-label="Main Navigation">
      <div>
        <div className="sidebar-brand">
          <div className="brand-icon">
            <Cpu size={20} />
          </div>
          <div>
            <div className="brand-title">GlucoTwin</div>
            <div className="brand-subtitle">Digital Twin v0.1</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = currentScreen === item.id;
            return (
              <button
                key={item.id}
                type="button"
                className={`nav-item ${isActive ? 'active' : ''}`}
                onClick={() => onNavigate(item.id)}
              >
                <Icon size={18} />
                <span className="nav-text">{item.label}</span>
                {item.badgeKey === 'alerts' && alertCount > 0 && (
                  <span className="nav-badge">{alertCount}</span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="sidebar-footer">
        <div className="twin-sync-status">
          <span className="pulse-dot" />
          <span>Patient Twin Engine</span>
        </div>
        <p style={{ fontSize: 11, color: 'var(--color-navy-500)', margin: 0 }}>
          PK/PD + XGBoost Pipeline
        </p>
      </div>
    </aside>
  );
}
