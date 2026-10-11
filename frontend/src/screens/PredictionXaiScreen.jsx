import React from 'react';
import GlucoseChart from '../components/charts/GlucoseChart';
import ShapWaterfallChart from '../components/charts/ShapWaterfallChart';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';

/**
 * Screen 4: Predictive Analytics & Explainable AI (XAI)
 */
export default function PredictionXaiScreen({ telemetry, predictions, xaiFeatures }) {
  const risk = predictions?.risk_assessment || {
    spike_probability_pct: 58,
    risk_tier: 'moderate',
    projected_peak_mgdl: 198,
    time_to_peak_minutes: 60,
    hypo_risk_pct: 6
  };

  const getRiskBadge = (tier) => {
    if (tier === 'low') return <Badge variant="target">Low Risk (0–30%)</Badge>;
    if (tier === 'moderate') return <Badge variant="warning">Moderate Risk (31–60%)</Badge>;
    return <Badge variant="critical">High Risk (61–100%)</Badge>;
  };

  return (
    <div className="content-area">
      <div className="page-header">
        <div>
          <h1 className="page-title">Predictive Analytics & Explainable AI (XAI)</h1>
          <p className="page-description">
            Early-warning forward projections: 2-hour glycemic trajectory, probabilistic risk classification, and SHAP root-cause drivers.
          </p>
        </div>
        {getRiskBadge(risk.risk_tier)}
      </div>

      {/* Prediction Risk KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--spacing-md)', marginBottom: 'var(--spacing-md)' }}>
        <div className="metric-card">
          <div className="metric-title">2-Hour Spike Probability</div>
          <div className="metric-value-row">
            <span className="metric-value">{risk.spike_probability_pct}%</span>
          </div>
          <div className="metric-footer">
            <span style={{ color: 'var(--color-warning-amber-dark)', fontWeight: 600 }}>Moderate Spike Tier</span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-title">Projected Peak Value</div>
          <div className="metric-value-row">
            <span className="metric-value">{risk.projected_peak_mgdl}</span>
            <span className="metric-unit">mg/dL</span>
          </div>
          <div className="metric-footer">Predicted in ~{risk.time_to_peak_minutes} minutes</div>
        </div>

        <div className="metric-card">
          <div className="metric-title">Hypoglycemia Risk (2h)</div>
          <div className="metric-value-row">
            <span className="metric-value">{risk.hypo_risk_pct}%</span>
          </div>
          <div className="metric-footer">Under current insulin curve</div>
        </div>

        <div className="metric-card">
          <div className="metric-title">Inference Horizon</div>
          <div className="metric-value-row">
            <span className="metric-value">120</span>
            <span className="metric-unit">mins</span>
          </div>
          <div className="metric-footer">Sampled every 15 minutes</div>
        </div>
      </div>

      {/* High-Resolution Prediction Horizon Chart */}
      <div style={{ marginBottom: 'var(--spacing-md)' }}>
        <GlucoseChart
          telemetryData={telemetry}
          predictionData={predictions}
          showPredictions={true}
          height={320}
        />
      </div>

      {/* SHAP Feature Attribution Full Section */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.8fr 1fr', gap: 'var(--spacing-md)' }}>
        <ShapWaterfallChart features={xaiFeatures} compact={false} />

        <Card
          title="Model Architecture & Metadata"
          subtitle="Proposed predictive inference pipeline"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: 6 }}>
              <span style={{ color: 'var(--color-navy-500)', fontSize: 13 }}>Regressor:</span>
              <span style={{ fontWeight: 600 }}>XGBoost / LightGBM</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: 6 }}>
              <span style={{ color: 'var(--color-navy-500)', fontSize: 13 }}>Explainability:</span>
              <span style={{ fontWeight: 600 }}>TreeSHAP Explainer</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: 6 }}>
              <span style={{ color: 'var(--color-navy-500)', fontSize: 13 }}>Uncertainty Model:</span>
              <span style={{ fontWeight: 600 }}>95% Confidence Interval</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: 6 }}>
              <span style={{ color: 'var(--color-navy-500)', fontSize: 13 }}>Input Streams:</span>
              <span style={{ fontWeight: 600 }}>CGM + HR + HRV + IOB + COB</span>
            </div>
            <div style={{ padding: 10, backgroundColor: 'var(--color-canvas)', borderRadius: 6, fontSize: 11, color: 'var(--color-navy-500)', marginTop: 8 }}>
              *Illustrative prototype architecture. Model weights and accuracy metrics will be calibrated upon backend model training completion.
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
