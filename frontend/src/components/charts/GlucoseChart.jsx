import React, { useState } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceArea,
  ReferenceLine
} from 'recharts';
import Card from '../common/Card';
import Badge from '../common/Badge';

/**
 * Custom Tooltip for Clinical Glucose Trajectory
 */
function ClinicalChartTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0]?.payload;
  if (!data) return null;

  const actual = data.actualGlucose;
  const predicted = data.predictedGlucose;
  const lower = data.ciLower;
  const upper = data.ciUpper;

  let zoneText = 'Target Zone (70-180)';
  let zoneColor = 'var(--color-target-green-dark)';
  const val = actual !== null && actual !== undefined ? actual : predicted;

  if (val > 180) {
    zoneText = 'Hyperglycemia Zone (>180)';
    zoneColor = 'var(--color-warning-amber-dark)';
  } else if (val < 70) {
    zoneText = 'Hypoglycemia Zone (<70)';
    zoneColor = 'var(--color-critical-rose-dark)';
  }

  return (
    <div
      style={{
        backgroundColor: '#FFFFFF',
        border: '1px solid var(--color-border)',
        borderRadius: 8,
        padding: '10px 14px',
        boxShadow: 'var(--shadow-md)',
        fontSize: 12,
        lineHeight: 1.5,
        minWidth: 180
      }}
    >
      <div style={{ fontWeight: 700, color: 'var(--color-navy-900)', marginBottom: 4 }}>
        Time: {data.timeStr || label}
      </div>

      {actual !== null && actual !== undefined && (
        <div style={{ color: 'var(--color-blue-600)', fontWeight: 600 }}>
          Historical Reading: <strong>{actual} mg/dL</strong>
        </div>
      )}

      {predicted !== null && predicted !== undefined && (
        <div style={{ color: 'var(--color-twin-violet-dark)', fontWeight: 600 }}>
          Projected Twin: <strong>{predicted} mg/dL</strong>
        </div>
      )}

      {lower !== null && upper !== null && lower !== undefined && (
        <div style={{ color: 'var(--color-navy-500)', fontSize: 11 }}>
          Illustrative 95% CI: [{lower} – {upper} mg/dL]
        </div>
      )}

      <div style={{ marginTop: 4, fontWeight: 600, color: zoneColor }}>
        {zoneText}
      </div>

      {data.event && (
        <div
          style={{
            marginTop: 6,
            padding: '4px 6px',
            backgroundColor: '#F8FAFC',
            borderRadius: 4,
            borderLeft: '3px solid var(--color-teal-600)',
            fontSize: 11
          }}
        >
          <strong>Event:</strong> {data.event.label}
        </div>
      )}
    </div>
  );
}

/**
 * GlucoseChart — Main Continuous Glucose Monitoring & 2h Projection Visualizer
 */
export default function GlucoseChart({
  telemetryData = [],
  predictionData = null,
  selectedWindow = 4,
  onWindowChange,
  showPredictions = true,
  height = 340
}) {
  // Combine telemetry with prediction points into one continuous sequence
  const chartData = React.useMemo(() => {
    const combined = [...telemetryData];
    if (showPredictions && predictionData?.forecast_points) {
      // Append prediction points (skipping index 0 which matches current reading)
      predictionData.forecast_points.forEach((pt, index) => {
        if (index > 0) {
          combined.push({
            timeStr: pt.timeStr,
            actualGlucose: null,
            predictedGlucose: pt.predictedGlucose,
            ciLower: pt.ciLower,
            ciUpper: pt.ciUpper,
            // For uncertainty area rendering:
            ciSpread: [pt.ciLower, pt.ciUpper],
            uncertaintyDelta: pt.ciUpper - pt.ciLower
          });
        }
      });
    }
    return combined;
  }, [telemetryData, predictionData, showPredictions]);

  // Find index of the "Now" transition point
  const lastActualTimeStr = telemetryData[telemetryData.length - 1]?.timeStr;

  return (
    <Card
      title="Continuous Glucose Telemetry & Predictive Horizon"
      subtitle="Historical sensor readings (solid blue) and forward 2-hour projected digital twin trajectory (dashed violet with uncertainty cone)"
      headerAction={
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          {onWindowChange && (
            <div style={{ display: 'flex', gap: 4, backgroundColor: 'var(--color-surface-hover)', padding: 3, borderRadius: 6 }}>
              {[2, 4, 8, 24].map((hrs) => (
                <button
                  key={hrs}
                  type="button"
                  onClick={() => onWindowChange(hrs)}
                  style={{
                    padding: '3px 8px',
                    fontSize: 11,
                    fontWeight: 600,
                    borderRadius: 4,
                    border: 'none',
                    backgroundColor: selectedWindow === hrs ? '#FFFFFF' : 'transparent',
                    color: selectedWindow === hrs ? 'var(--color-teal-700)' : 'var(--color-navy-500)',
                    boxShadow: selectedWindow === hrs ? 'var(--shadow-xs)' : 'none',
                    cursor: 'pointer'
                  }}
                >
                  {hrs}h
                </button>
              ))}
            </div>
          )}
          <Badge variant="twin">2h Forecast Horizon</Badge>
        </div>
      }
      footer={
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: 12,
            gap: 12
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 14, height: 3, backgroundColor: 'var(--color-blue-600)', display: 'inline-block' }} />
              <span style={{ fontWeight: 600 }}>Historical Telemetry (Sensor)</span>
            </span>

            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 14, height: 3, borderTop: '2px dashed var(--color-twin-violet)', display: 'inline-block' }} />
              <span style={{ fontWeight: 600 }}>Digital Twin Projection (Dashed)</span>
            </span>

            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 14, height: 10, backgroundColor: 'rgba(139, 92, 246, 0.18)', borderRadius: 2, display: 'inline-block' }} />
              <span style={{ color: 'var(--color-navy-700)' }}>Illustrative 95% Uncertainty Range</span>
            </span>

            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 14, height: 10, backgroundColor: 'rgba(16, 185, 129, 0.15)', borderRadius: 2, display: 'inline-block' }} />
              <span style={{ color: 'var(--color-target-green-dark)' }}>Target Band (70-180 mg/dL)</span>
            </span>
          </div>

          <div style={{ color: 'var(--color-navy-500)', fontSize: 11 }}>
            *Demonstration simulation model
          </div>
        </div>
      }
    >
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" vertical={false} />
            <XAxis
              dataKey="timeStr"
              tickLine={false}
              axisLine={{ stroke: 'var(--color-border)' }}
              tick={{ fill: 'var(--color-navy-500)', fontSize: 11 }}
            />
            <YAxis
              domain={[40, 260]}
              ticks={[54, 70, 100, 140, 180, 220, 250]}
              tickLine={false}
              axisLine={{ stroke: 'var(--color-border)' }}
              tick={{ fill: 'var(--color-navy-500)', fontSize: 11 }}
              unit=" mg/dL"
            />
            <Tooltip content={<ClinicalChartTooltip />} />

            {/* Clinical Target Glycemic Band: 70 to 180 mg/dL */}
            <ReferenceArea
              y1={70}
              y2={180}
              fill="var(--color-target-green)"
              fillOpacity={0.08}
              stroke="none"
            />

            {/* Severe Hypoglycemia Reference Line at 54 mg/dL */}
            <ReferenceLine
              y={54}
              stroke="var(--color-critical-rose)"
              strokeDasharray="2 2"
              label={{ value: 'Severe Low (<54)', fill: 'var(--color-critical-rose)', fontSize: 10, position: 'insideBottomLeft' }}
            />

            {/* Target Ceiling Line at 180 mg/dL */}
            <ReferenceLine
              y={180}
              stroke="var(--color-warning-amber)"
              strokeDasharray="3 3"
              label={{ value: 'Target Max (180)', fill: 'var(--color-warning-amber-dark)', fontSize: 10, position: 'insideTopLeft' }}
            />

            {/* Vertical Marker for Current Time ("Now") */}
            {lastActualTimeStr && (
              <ReferenceLine
                x={lastActualTimeStr}
                stroke="var(--color-navy-700)"
                strokeDasharray="4 4"
                label={{ value: 'NOW', fill: 'var(--color-navy-900)', fontSize: 11, fontWeight: 700, position: 'top' }}
              />
            )}

            {/* 1. Illustrative 95% Uncertainty Range Envelope (Upper Bound Fill) */}
            {showPredictions && (
              <Area
                type="monotone"
                dataKey="ciUpper"
                stroke="transparent"
                fill="rgba(139, 92, 246, 0.12)"
                connectNulls
                isAnimationActive={false}
              />
            )}

            {/* 2. Uncertainty Lower Cutout (fills canvas background to simulate band) */}
            {showPredictions && (
              <Area
                type="monotone"
                dataKey="ciLower"
                stroke="transparent"
                fill="#FFFFFF"
                connectNulls
                isAnimationActive={false}
              />
            )}

            {/* 3. Historical Telemetry: Solid Clinical Blue Line (#2563EB) */}
            <Line
              type="monotone"
              dataKey="actualGlucose"
              stroke="var(--color-blue-600)"
              strokeWidth={2.8}
              dot={{ r: 2, fill: 'var(--color-blue-600)' }}
              activeDot={{ r: 5, fill: 'var(--color-blue-600)' }}
              connectNulls={false}
              isAnimationActive={false}
            />

            {/* 4. Digital Twin Prediction: Dashed Royal Violet Line (#8B5CF6) */}
            {showPredictions && (
              <Line
                type="monotone"
                dataKey="predictedGlucose"
                stroke="var(--color-twin-violet)"
                strokeWidth={2.8}
                strokeDasharray="5 5"
                dot={{ r: 3, fill: 'var(--color-twin-violet)' }}
                activeDot={{ r: 6, fill: 'var(--color-twin-violet)' }}
                connectNulls
                isAnimationActive={false}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
