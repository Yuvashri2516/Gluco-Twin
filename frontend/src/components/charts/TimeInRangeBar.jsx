import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';

/**
 * Standardized Clinical Time In Range (TIR) Component
 */
export default function TimeInRangeBar({
  veryLow = 1,
  low = 5,
  target = 78,
  high = 14,
  veryHigh = 2,
  compact = false
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-navy-700)' }}>
          Time In Range (TIR)
        </span>
        <Badge variant={target >= 70 ? 'target' : 'warning'}>
          {target}% in Target (Goal &gt; 70%)
        </Badge>
      </div>

      <div className="tir-bar-container" title={`Target: ${target}%, Low: ${low}%, High: ${high}%`}>
        <div style={{ width: `${veryLow}%`, backgroundColor: 'var(--color-critical-rose-dark)' }} title={`Very Low (<54): ${veryLow}%`} />
        <div style={{ width: `${low}%`, backgroundColor: 'var(--color-critical-rose)' }} title={`Low (54-69): ${low}%`} />
        <div style={{ width: `${target}%`, backgroundColor: 'var(--color-target-green)' }} title={`Target (70-180): ${target}%`} />
        <div style={{ width: `${high}%`, backgroundColor: 'var(--color-warning-amber)' }} title={`High (181-250): ${high}%`} />
        <div style={{ width: `${veryHigh}%`, backgroundColor: 'var(--color-critical-rose)' }} title={`Very High (>250): ${veryHigh}%`} />
      </div>

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: 11,
          color: 'var(--color-navy-500)',
          flexWrap: 'wrap',
          gap: 6
        }}
      >
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          <span style={{ width: 8, height: 8, borderRadius: 2, backgroundColor: 'var(--color-critical-rose)' }} />
          Below (&lt;70): {veryLow + low}%
        </span>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          <span style={{ width: 8, height: 8, borderRadius: 2, backgroundColor: 'var(--color-target-green)' }} />
          Target (70-180): {target}%
        </span>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          <span style={{ width: 8, height: 8, borderRadius: 2, backgroundColor: 'var(--color-warning-amber)' }} />
          Above (&gt;180): {high + veryHigh}%
        </span>
      </div>
    </div>
  );
}
