import React, { useState } from 'react';
import GlucoseChart from '../components/charts/GlucoseChart';
import BiometricsChart from '../components/charts/BiometricsChart';
import TimeInRangeBar from '../components/charts/TimeInRangeBar';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';

/**
 * Screen 3: Glucose Monitoring (High-Resolution Sensor Telemetry)
 */
export default function MonitoringScreen({ telemetry, predictions, twinStatus }) {
  const [selectedHours, setSelectedHours] = useState(4);

  return (
    <div className="content-area">
      <div className="page-header">
        <div>
          <h1 className="page-title">Continuous Sensor Monitoring</h1>
          <p className="page-description">
            High-frequency continuous glucose telemetry synchronized with autonomic biometrics (Heart Rate & HRV).
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <Badge variant="target">Signal Quality: 99.4% Valid</Badge>
          <Badge variant="neutral">Battery: 88%</Badge>
        </div>
      </div>

      {/* Ambulatory Glucose Profile (AGP) Summary Bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--spacing-md)', marginBottom: 'var(--spacing-md)' }}>
        <div className="metric-card">
          <div className="metric-title">Mean Glucose</div>
          <div className="metric-value-row">
            <span className="metric-value">134</span>
            <span className="metric-unit">mg/dL</span>
          </div>
          <div className="metric-footer">Standard deviation: ±28 mg/dL</div>
        </div>

        <div className="metric-card">
          <div className="metric-title">Glycemic Variability (%CV)</div>
          <div className="metric-value-row">
            <span className="metric-value">24.2%</span>
          </div>
          <div className="metric-footer">Target &le; 36% (Stable)</div>
        </div>

        <div className="metric-card">
          <div className="metric-title">Glucose Mgmt Indicator (GMI)</div>
          <div className="metric-value-row">
            <span className="metric-value">6.6%</span>
          </div>
          <div className="metric-footer">Estimated HbA1c equivalent</div>
        </div>

        <div className="metric-card">
          <div className="metric-title">Sensor Active Time</div>
          <div className="metric-value-row">
            <span className="metric-value">99.8%</span>
          </div>
          <div className="metric-footer">0 minutes data interruption</div>
        </div>
      </div>

      {/* Primary High-Resolution CGM Chart */}
      <div style={{ marginBottom: 'var(--spacing-md)' }}>
        <GlucoseChart
          telemetryData={telemetry}
          predictionData={predictions}
          selectedWindow={selectedHours}
          onWindowChange={setSelectedHours}
          showPredictions={true}
          height={320}
        />
      </div>

      {/* Synchronized Biometrics Chart */}
      <div style={{ marginBottom: 'var(--spacing-md)' }}>
        <BiometricsChart telemetryData={telemetry} height={220} />
      </div>

      {/* Time in Range Clinical Distribution Card */}
      <Card
        title="Ambulatory Glucose Target Zone Distribution"
        subtitle="Standard international consensus criteria for continuous glucose monitoring"
      >
        <TimeInRangeBar target={78} low={6} veryLow={1} high={13} veryHigh={2} />
      </Card>
    </div>
  );
}
