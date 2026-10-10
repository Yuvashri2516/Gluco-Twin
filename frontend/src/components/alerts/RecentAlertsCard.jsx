import React from 'react';
import { AlertCircle, AlertTriangle, Info, Check } from 'lucide-react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import Button from '../common/Button';

/**
 * Recent Alerts Feed Component
 */
export default function RecentAlertsCard({ alerts = [], onAcknowledge, onViewAll }) {
  const getSeverityIcon = (sev) => {
    if (sev === 'critical') return <AlertCircle size={18} color="var(--color-critical-rose)" />;
    if (sev === 'warning') return <AlertTriangle size={18} color="var(--color-warning-amber)" />;
    return <Info size={18} color="var(--color-blue-500)" />;
  };

  return (
    <Card
      title="Clinical Alert Feed"
      subtitle="Early warnings prioritized by physiological urgency and risk projection"
      headerAction={
        onViewAll && (
          <Button variant="outline" size="sm" onClick={onViewAll}>
            View All ({alerts.length})
          </Button>
        )
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {alerts.length === 0 ? (
          <div style={{ padding: 20, textAlign: 'center', color: 'var(--color-navy-500)', fontSize: 13 }}>
            No active unacknowledged alerts.
          </div>
        ) : (
          alerts.slice(0, 3).map((item) => {
            const isAck = item.status === 'acknowledged';
            return (
              <div key={item.id} className={`alert-card ${item.severity}`}>
                <div className="alert-icon-col">{getSeverityIcon(item.severity)}</div>
                <div className="alert-content-col">
                  <div className="alert-title-row">
                    <span className="alert-title">{item.title}</span>
                    <span className="alert-time">
                      {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <div className="alert-desc">{item.description}</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 11, color: 'var(--color-navy-500)' }}>
                      Origin: <strong>{item.trigger_source}</strong>
                    </span>
                    <div>
                      {isAck ? (
                        <span style={{ fontSize: 11, color: 'var(--color-target-green-dark)', display: 'inline-flex', alignItems: 'center', gap: 4, fontWeight: 600 }}>
                          <Check size={13} /> Acknowledged
                        </span>
                      ) : (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => onAcknowledge && onAcknowledge(item.id)}
                        >
                          Acknowledge
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </Card>
  );
}
