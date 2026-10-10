import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';

export default function TwinStatusCard({ twinStatus }) {
  if (!twinStatus) return null;

  return (
    <Card
      title="Digital Twin Engine Status"
      subtitle="Virtual metabolic model state & real-time telemetry synchronization"
      headerAction={<Badge variant="target">Synchronized (12ms)</Badge>}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, backgroundColor: 'var(--color-canvas)', padding: 12, borderRadius: 8 }}>
          <div>
            <div style={{ fontSize: 11, color: 'var(--color-navy-500)', textTransform: 'uppercase' }}>Insulin on Board</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-navy-900)' }}>
              {twinStatus.active_iob_units} <span style={{ fontSize: 13, fontWeight: 500 }}>Units</span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: 11, color: 'var(--color-navy-500)', textTransform: 'uppercase' }}>Carbs on Board</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-navy-900)' }}>
              {twinStatus.active_cob_grams} <span style={{ fontSize: 13, fontWeight: 500 }}>grams</span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: 6 }}>
          <span style={{ fontSize: 12, color: 'var(--color-navy-500)' }}>Model Architecture:</span>
          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-navy-800)' }}>
            {twinStatus.model_architecture}
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: 6 }}>
          <span style={{ fontSize: 12, color: 'var(--color-navy-500)' }}>Sensor Packet Integrity:</span>
          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-target-green-dark)' }}>
            {twinStatus.data_quality_pct}% Valid Packets
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: 6 }}>
          <span style={{ fontSize: 12, color: 'var(--color-navy-500)' }}>Sensor Drift Index:</span>
          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-navy-800)' }}>
            {twinStatus.sensor_drift_status} (0.038 score)
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: 2 }}>
          <span style={{ fontSize: 11, color: 'var(--color-navy-500)' }}>Last Calibration:</span>
          <span style={{ fontSize: 11, color: 'var(--color-navy-700)' }}>
            {new Date(twinStatus.last_calibration_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>
    </Card>
  );
}
