import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ReferenceArea,
  CartesianGrid,
} from 'recharts';
import EmptyState from './Common/EmptyState';
import LoadingSpinner from './Common/LoadingSpinner';

function formatTickTime(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);
  if (isNaN(d.getTime())) return '';
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
}

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const val = payload[0].value;
    const d = new Date(label);
    const dateFormatted = !isNaN(d.getTime())
      ? d.toLocaleString([], {
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        })
      : label;

    let status = 'In Target';
    let statusClass = 'badge-normal';
    if (val < 70) {
      status = 'Hypoglycemia Risk';
      statusClass = 'badge-critical';
    } else if (val > 180) {
      status = 'Hyperglycemia / Spike';
      statusClass = 'badge-warning';
    }

    return (
      <div className="custom-chart-tooltip">
        <div className="tooltip-time">{dateFormatted}</div>
        <div className="tooltip-val-row">
          <span className="tooltip-indicator" style={{ backgroundColor: '#0ea5e9' }} />
          <span className="tooltip-label">Glucose:</span>
          <span className="tooltip-value">{val.toFixed(1)} mg/dL</span>
        </div>
        <div style={{ marginTop: '6px' }}>
          <span className={`badge ${statusClass}`}>{status}</span>
        </div>
      </div>
    );
  }
  return null;
};

export default function GlucoseChart({ readings = [], isLoading, hours = 24 }) {
  if (isLoading) {
    return (
      <div className="chart-panel">
        <div className="chart-header">
          <h3 className="chart-title">Continuous Glucose Monitoring (CGM)</h3>
        </div>
        <LoadingSpinner message="Loading historical glucose curve..." />
      </div>
    );
  }

  if (!readings || readings.length === 0) {
    return (
      <div className="chart-panel">
        <div className="chart-header">
          <h3 className="chart-title">Continuous Glucose Monitoring (CGM)</h3>
        </div>
        <EmptyState
          title="No Glucose Readings Recorded"
          message={`No continuous glucose monitoring readings are available for the selected ${hours}-hour timeframe.`}
        />
      </div>
    );
  }

  // Calculate statistics
  const values = readings.map((r) => r.value);
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const avgVal = (values.reduce((a, b) => a + b, 0) / values.length).toFixed(1);
  const inRangeCount = values.filter((v) => v >= 70 && v <= 180).length;
  const timeInRange = ((inRangeCount / values.length) * 100).toFixed(0);

  return (
    <div className="chart-panel">
      <div className="chart-header">
        <div>
          <div className="chart-title-row">
            <h3 className="chart-title">Continuous Glucose Monitoring (CGM)</h3>
            <span className="badge badge-neutral">{hours}h Window ({readings.length} points)</span>
          </div>
          <p className="chart-subtitle">
            Time-series glucose values (mg/dL) from CGM telemetry
          </p>
        </div>

        <div className="chart-metrics-strip">
          <div className="metric-chip">
            <span className="metric-chip-label">Avg:</span>
            <span className="metric-chip-value">{avgVal} mg/dL</span>
          </div>
          <div className="metric-chip">
            <span className="metric-chip-label">Range:</span>
            <span className="metric-chip-value">{minVal.toFixed(0)} - {maxVal.toFixed(0)}</span>
          </div>
          <div className="metric-chip">
            <span className="metric-chip-label">TIR (70-180):</span>
            <span className="metric-chip-value" style={{ color: Number(timeInRange) >= 70 ? 'var(--status-normal)' : 'var(--status-warning)' }}>
              {timeInRange}%
            </span>
          </div>
        </div>
      </div>

      <div className="chart-body" style={{ height: '320px', width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={readings}
            margin={{ top: 20, right: 20, left: 0, bottom: 20 }}
          >
            <defs>
              <linearGradient id="glucoseGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatTickTime}
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              minTickGap={40}
            />
            <YAxis
              domain={[Math.floor(Math.min(minVal - 10, 50)), Math.ceil(Math.max(maxVal + 20, 220))]}
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              unit=" mg/dL"
              width={75}
            />
            <Tooltip content={<CustomTooltip />} />

            {/* Target glucose clinical band (70 - 180 mg/dL) */}
            <ReferenceArea
              y1={70}
              y2={180}
              fill="rgba(16, 185, 129, 0.06)"
              strokeOpacity={0}
            />
            <ReferenceLine
              y={180}
              stroke="rgba(245, 158, 11, 0.6)"
              strokeDasharray="4 4"
              label={{
                value: 'Hyper (180)',
                fill: '#f59e0b',
                fontSize: 10,
                position: 'insideTopRight',
              }}
            />
            <ReferenceLine
              y={70}
              stroke="rgba(239, 68, 68, 0.6)"
              strokeDasharray="4 4"
              label={{
                value: 'Hypo (70)',
                fill: '#ef4444',
                fontSize: 10,
                position: 'insideBottomRight',
              }}
            />

            <Area
              type="monotone"
              dataKey="value"
              stroke="#0ea5e9"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#glucoseGradient)"
              activeDot={{ r: 6, fill: '#38bdf8', stroke: '#090d16', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="chart-legend-footer">
        <div className="legend-item">
          <span className="legend-dot" style={{ backgroundColor: '#0ea5e9' }} />
          <span>Observed CGM Readings</span>
        </div>
        <div className="legend-item">
          <span className="legend-box" style={{ backgroundColor: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981' }} />
          <span>Target Range (70-180 mg/dL)</span>
        </div>
        <div className="legend-item">
          <span className="legend-line" style={{ borderTop: '2px dashed #f59e0b' }} />
          <span>Hyperglycemia Threshold (180 mg/dL)</span>
        </div>
        <div className="legend-item">
          <span className="legend-line" style={{ borderTop: '2px dashed #ef4444' }} />
          <span>Hypoglycemia Limit (70 mg/dL)</span>
        </div>
      </div>
    </div>
  );
}
