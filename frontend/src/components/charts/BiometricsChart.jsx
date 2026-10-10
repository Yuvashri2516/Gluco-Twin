import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import Card from '../common/Card';
import Badge from '../common/Badge';

export default function BiometricsChart({ telemetryData = [], height = 220 }) {
  return (
    <Card
      title="Synchronized Autonomic Biometrics"
      subtitle="Heart Rate (BPM) and Heart Rate Variability (RMSSD ms) as physiological stress & exertion proxies"
      headerAction={<Badge variant="neutral">Wearable IoT Stream (5-min)</Badge>}
    >
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={telemetryData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" vertical={false} />
            <XAxis
              dataKey="timeStr"
              tickLine={false}
              axisLine={{ stroke: 'var(--color-border)' }}
              tick={{ fill: 'var(--color-navy-500)', fontSize: 11 }}
            />
            {/* Left Axis: Heart Rate */}
            <YAxis
              yAxisId="left"
              domain={[50, 120]}
              tickLine={false}
              axisLine={{ stroke: 'var(--color-border)' }}
              tick={{ fill: 'var(--color-critical-rose)', fontSize: 11 }}
              unit=" bpm"
            />
            {/* Right Axis: HRV RMSSD */}
            <YAxis
              yAxisId="right"
              orientation="right"
              domain={[10, 80]}
              tickLine={false}
              axisLine={{ stroke: 'var(--color-border)' }}
              tick={{ fill: 'var(--color-teal-600)', fontSize: 11 }}
              unit=" ms"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#FFFFFF',
                borderRadius: 8,
                border: '1px solid var(--color-border)',
                fontSize: 12
              }}
            />
            <Legend wrapperStyle={{ fontSize: 12, paddingTop: 6 }} />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="heartRate"
              name="Heart Rate (BPM)"
              stroke="var(--color-critical-rose)"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="hrvRmssd"
              name="HRV RMSSD (ms)"
              stroke="var(--color-teal-600)"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
