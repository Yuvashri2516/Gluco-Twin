import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
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

const CustomVitalsTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const d = new Date(label);
    const dateFormatted = !isNaN(d.getTime())
      ? d.toLocaleString([], {
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        })
      : label;

    return (
      <div className="custom-chart-tooltip">
        <div className="tooltip-time">{dateFormatted}</div>
        {payload.map((item, idx) => (
          <div key={idx} className="tooltip-val-row" style={{ marginTop: '4px' }}>
            <span className="tooltip-indicator" style={{ backgroundColor: item.color }} />
            <span className="tooltip-label">{item.name}:</span>
            <span className="tooltip-value">
              {item.value != null ? Number(item.value).toFixed(1) : '--'}{' '}
              {item.dataKey === 'heart_rate' ? 'bpm' : 'ms'}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export default function VitalsChart({ readings = [], isLoading, hours = 24 }) {
  if (isLoading) {
    return (
      <div className="chart-panel">
        <div className="chart-header">
          <h3 className="chart-title">Autonomic & Cardiovascular Vitals</h3>
        </div>
        <LoadingSpinner message="Loading historical vitals readings..." />
      </div>
    );
  }

  if (!readings || readings.length === 0) {
    return (
      <div className="chart-panel">
        <div className="chart-header">
          <h3 className="chart-title">Autonomic & Cardiovascular Vitals</h3>
        </div>
        <EmptyState
          title="No Vital Readings Recorded"
          message={`No heart-rate or HRV time-series records are available for the selected ${hours}-hour timeframe.`}
        />
      </div>
    );
  }

  // Check if HRV readings exist
  const hasHrv = readings.some((r) => r.hrv != null);

  return (
    <div className="chart-panel">
      <div className="chart-header">
        <div>
          <div className="chart-title-row">
            <h3 className="chart-title">Autonomic & Cardiovascular Vitals</h3>
            <span className="badge badge-neutral">{hours}h Window ({readings.length} points)</span>
          </div>
          <p className="chart-subtitle">
            Resting heart rate (bpm) and heart-rate variability (RMSSD/SDNN, ms)
          </p>
        </div>
      </div>

      <div className="chart-body" style={{ height: '300px', width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={readings}
            margin={{ top: 20, right: 20, left: 0, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(15, 23, 42, 0.06)" />
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatTickTime}
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              minTickGap={40}
            />
            {/* Left Y-Axis for Heart Rate */}
            <YAxis
              yAxisId="left"
              stroke="#f43f5e"
              fontSize={11}
              tickLine={false}
              unit=" bpm"
              width={65}
              domain={['auto', 'auto']}
            />
            {/* Right Y-Axis for HRV if present */}
            {hasHrv && (
              <YAxis
                yAxisId="right"
                orientation="right"
                stroke="#a855f7"
                fontSize={11}
                tickLine={false}
                unit=" ms"
                width={60}
                domain={['auto', 'auto']}
              />
            )}
            <Tooltip content={<CustomVitalsTooltip />} />
            <Legend
              wrapperStyle={{ paddingTop: '10px' }}
              formatter={(val) => <span style={{ color: '#cbd5e1', fontSize: '12px' }}>{val}</span>}
            />

            <Line
              yAxisId="left"
              type="monotone"
              dataKey="heart_rate"
              name="Heart Rate"
              stroke="#f43f5e"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 5, fill: '#fb7185' }}
            />
            {hasHrv && (
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="hrv"
                name="Heart Rate Variability (HRV)"
                stroke="#a855f7"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 5, fill: '#c084fc' }}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="chart-legend-footer">
        <div className="legend-item">
          <span className="legend-dot" style={{ backgroundColor: '#f43f5e' }} />
          <span>Heart Rate (left axis, bpm)</span>
        </div>
        {hasHrv && (
          <div className="legend-item">
            <span className="legend-dot" style={{ backgroundColor: '#a855f7' }} />
            <span>HRV (right axis, ms - higher values reflect autonomic flexibility)</span>
          </div>
        )}
      </div>
    </div>
  );
}
