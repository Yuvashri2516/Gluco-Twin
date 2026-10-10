import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';

/**
 * ShapWaterfallChart — Explainable AI Feature Attribution Bars
 */
export default function ShapWaterfallChart({ features = [], compact = false }) {
  const displayFeatures = compact ? features.slice(0, 4) : features;

  return (
    <Card
      title="Explainable AI (XAI) Attribution Drivers"
      subtitle="Top physiological and lifestyle factors influencing the current 2-hour trajectory prediction"
      headerAction={<Badge variant="twin">Proposed TreeSHAP Explainer</Badge>}
      footer={
        <div style={{ fontSize: 11, color: 'var(--color-navy-500)', display: 'flex', justifyContent: 'space-between' }}>
          <span>*Illustrative SHAP attribution values for system demonstration</span>
          <span>Baseline Reference: 135 mg/dL</span>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {displayFeatures.map((feat) => {
          const isPositive = feat.impact_mgdl > 0;
          const barWidth = Math.min(100, Math.abs(feat.impact_mgdl) * 2.1);
          const barColor = isPositive ? 'var(--color-warning-amber)' : 'var(--color-teal-600)';

          return (
            <div key={feat.id || feat.name} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, alignItems: 'center' }}>
                <span style={{ fontWeight: 600, color: 'var(--color-navy-900)' }}>
                  {feat.name}
                </span>
                <span
                  style={{
                    fontWeight: 700,
                    color: isPositive ? 'var(--color-warning-amber-dark)' : 'var(--color-teal-700)',
                    fontSize: 12
                  }}
                >
                  {isPositive ? `+${feat.impact_mgdl.toFixed(1)}` : feat.impact_mgdl.toFixed(1)} mg/dL
                </span>
              </div>

              {/* Attribution Bar Track */}
              <div
                style={{
                  height: 10,
                  backgroundColor: 'var(--color-border-subtle)',
                  borderRadius: 5,
                  overflow: 'hidden',
                  position: 'relative'
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: `${barWidth}%`,
                    backgroundColor: barColor,
                    borderRadius: 5,
                    transition: 'width 0.4s ease-out'
                  }}
                />
              </div>

              {!compact && feat.description && (
                <div style={{ fontSize: 11, color: 'var(--color-navy-500)' }}>
                  {feat.description}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}
