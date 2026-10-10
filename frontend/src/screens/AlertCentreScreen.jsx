import React, { useState } from 'react';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import { AlertCircle, AlertTriangle, Info, Check, ShieldAlert, ArrowUpRight } from 'lucide-react';

/**
 * Screen 6: Alert Centre (Triage, Routing & Escalation)
 */
export default function AlertCentreScreen({ alerts = [], onAcknowledge, onEscalate }) {
  const [filterSeverity, setFilterSeverity] = useState('all');

  const filteredAlerts = alerts.filter((a) => {
    if (filterSeverity === 'all') return true;
    return a.severity === filterSeverity;
  });

  const criticalCount = alerts.filter((a) => a.severity === 'critical').length;
  const warningCount = alerts.filter((a) => a.severity === 'warning').length;
  const infoCount = alerts.filter((a) => a.severity === 'info').length;

  const getSeverityIcon = (sev) => {
    if (sev === 'critical') return <AlertCircle size={20} color="var(--color-critical-rose)" />;
    if (sev === 'warning') return <AlertTriangle size={20} color="var(--color-warning-amber)" />;
    return <Info size={20} color="var(--color-blue-500)" />;
  };

  return (
    <div className="content-area">
      <div className="page-header">
        <div>
          <h1 className="page-title">Intelligent Alert Centre</h1>
          <p className="page-description">
            Prioritized clinical notifications: early-warning predictive alerts, threshold violations, and audit history.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Badge variant={criticalCount > 0 ? 'critical' : 'target'}>
            {criticalCount} Critical
          </Badge>
          <Badge variant="warning">{warningCount} Warnings</Badge>
        </div>
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 'var(--spacing-md)' }}>
        <button
          type="button"
          className={`btn ${filterSeverity === 'all' ? 'btn-primary' : 'btn-secondary'} btn-sm`}
          onClick={() => setFilterSeverity('all')}
        >
          All Notifications ({alerts.length})
        </button>
        <button
          type="button"
          className={`btn ${filterSeverity === 'critical' ? 'btn-primary' : 'btn-secondary'} btn-sm`}
          onClick={() => setFilterSeverity('critical')}
        >
          Critical ({criticalCount})
        </button>
        <button
          type="button"
          className={`btn ${filterSeverity === 'warning' ? 'btn-primary' : 'btn-secondary'} btn-sm`}
          onClick={() => setFilterSeverity('warning')}
        >
          Warnings ({warningCount})
        </button>
        <button
          type="button"
          className={`btn ${filterSeverity === 'info' ? 'btn-primary' : 'btn-secondary'} btn-sm`}
          onClick={() => setFilterSeverity('info')}
        >
          System & Info ({infoCount})
        </button>
      </div>

      {/* Alert Feed Cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 'var(--spacing-xl)' }}>
        {filteredAlerts.map((item) => {
          const isAck = item.status === 'acknowledged';
          const isEscalated = item.status === 'escalated';

          return (
            <div key={item.id} className={`alert-card ${item.severity}`}>
              <div className="alert-icon-col">{getSeverityIcon(item.severity)}</div>
              <div className="alert-content-col">
                <div className="alert-title-row">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span className="alert-title">{item.title}</span>
                    <Badge variant={item.severity === 'critical' ? 'critical' : item.severity === 'warning' ? 'warning' : 'neutral'}>
                      {item.severity.toUpperCase()}
                    </Badge>
                  </div>
                  <span className="alert-time">
                    {new Date(item.timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                  </span>
                </div>

                <p className="alert-desc">{item.description}</p>

                {item.clinical_recommendation && (
                  <div
                    style={{
                      padding: '8px 12px',
                      backgroundColor: 'var(--color-canvas)',
                      borderRadius: 6,
                      fontSize: 12,
                      color: 'var(--color-navy-800)',
                      marginBottom: 10,
                      borderLeft: '3px solid var(--color-teal-600)'
                    }}
                  >
                    <strong>Decision Support Guidance:</strong> {item.clinical_recommendation}
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                  <div style={{ fontSize: 11, color: 'var(--color-navy-500)', display: 'flex', gap: 12 }}>
                    <span>Patient: <strong>{item.patient_id}</strong></span>
                    <span>Trigger: <strong>{item.trigger_source}</strong></span>
                  </div>

                  <div className="alert-actions">
                    {isAck ? (
                      <span style={{ fontSize: 12, color: 'var(--color-target-green-dark)', display: 'inline-flex', alignItems: 'center', gap: 4, fontWeight: 600 }}>
                        <Check size={14} /> Acknowledged by Attending Clinician
                      </span>
                    ) : isEscalated ? (
                      <span style={{ fontSize: 12, color: 'var(--color-critical-rose-dark)', display: 'inline-flex', alignItems: 'center', gap: 4, fontWeight: 600 }}>
                        <ArrowUpRight size={14} /> Escalated to On-Call Nurse
                      </span>
                    ) : (
                      <>
                        <Button
                          variant="secondary"
                          size="sm"
                          icon={Check}
                          onClick={() => onAcknowledge && onAcknowledge(item.id)}
                        >
                          Acknowledge
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          icon={ArrowUpRight}
                          onClick={() => onEscalate && onEscalate(item.id)}
                        >
                          Escalate Protocol
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Escalation Policy & Smart Routing Overview */}
      <Card
        title="Intelligent Alert Routing Architecture"
        subtitle="Stage 6 Alert Prioritization Engine rules & deduplication safeguards"
      >
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
          <div style={{ padding: 12, backgroundColor: 'var(--color-canvas)', borderRadius: 8 }}>
            <h4 style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-navy-900)', marginBottom: 4 }}>
              1. Deduplication Filter
            </h4>
            <p style={{ fontSize: 12, color: 'var(--color-navy-700)', margin: 0 }}>
              Suppresses repetitive threshold alarms within a 30-minute window while the metabolic curve remains within projected tolerance.
            </p>
          </div>

          <div style={{ padding: 12, backgroundColor: 'var(--color-canvas)', borderRadius: 8 }}>
            <h4 style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-navy-900)', marginBottom: 4 }}>
              2. Proactive Lead-Time
            </h4>
            <p style={{ fontSize: 12, color: 'var(--color-navy-700)', margin: 0 }}>
              Fires 30–45 minutes prior to anticipated hypoglycemic excursions (&lt;70 mg/dL), enabling oral carbohydrate ingestion before acute symptoms.
            </p>
          </div>

          <div style={{ padding: 12, backgroundColor: 'var(--color-canvas)', borderRadius: 8 }}>
            <h4 style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-navy-900)', marginBottom: 4 }}>
              3. Automated Escalation
            </h4>
            <p style={{ fontSize: 12, color: 'var(--color-navy-700)', margin: 0 }}>
              Critical unacknowledged alerts trigger automatic escalation to secondary on-call clinical channels after 10 minutes.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
