import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceArea,
  Legend
} from 'recharts';
import Card from '../common/Card';
import Badge from '../common/Badge';

export default function SimulationCompareChart({ trajectory = [], height = 300 }) {
  return (
    <Card
      title="Counterfactual Trajectory Comparison"
      subtitle="Comparing current baseline forecast against simulated digital twin response"
      headerAction={<Badge variant="twin">Simulation Model Active</Badge>}
    >
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={trajectory} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" vertical={false} />
            <XAxis
              dataKey="timeLabel"
              tickLine={false}
              axisLine={{ stroke: 'var(--color-border)' }}
              tick={{ fill: 'var(--color-navy-500)', fontSize: 11 }}
            />
            <YAxis
              domain={[60, 240]}
              ticks={[70, 100, 140, 180, 220]}
              tickLine={false}
              axisLine={{ stroke: 'var(--color-border)' }}
              tick={{ fill: 'var(--color-navy-500)', fontSize: 11 }}
              unit=" mg/dL"
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

            {/* Target Glycemic Area (70 - 180 mg/dL) */}
            <ReferenceArea
              y1={70}
              y2={180}
              fill="var(--color-target-green)"
              fillOpacity={0.08}
              stroke="none"
            />

            {/* Curve 1: Baseline Unmodified Forecast */}
            <Line
              type="monotone"
              dataKey="baseline_glucose"
              name="Baseline Forecast"
              stroke="var(--color-navy-500)"
              strokeWidth={2.5}
              dot={{ r: 3, fill: 'var(--color-navy-500)' }}
              isAnimationActive={false}
            />

            {/* Curve 2: Counterfactual Simulated Twin */}
            <Line
              type="monotone"
              dataKey="simulated_glucose"
              name="Simulated Twin Response"
              stroke="var(--color-twin-violet)"
              strokeWidth={3}
              strokeDasharray="4 4"
              dot={{ r: 4, fill: 'var(--color-twin-violet)' }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
