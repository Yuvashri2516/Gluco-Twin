import React, { useState } from 'react';
import MetricCard from '../components/common/MetricCard';
import GlucoseChart from '../components/charts/GlucoseChart';
import ShapWaterfallChart from '../components/charts/ShapWaterfallChart';
import TimeInRangeBar from '../components/charts/TimeInRangeBar';
import RecentAlertsCard from '../components/alerts/RecentAlertsCard';
import PatientSummaryCard from '../components/patient/PatientSummaryCard';
import TwinStatusCard from '../components/twin/TwinStatusCard';
import Card from '../components/common/Card';

/**
 * Screen 1: Overview Dashboard (Command Center & Triage)
 */
export default function OverviewScreen({
  patient,
  telemetry,
  predictions,
  xaiFeatures,
  alerts,
  twinStatus,
  onAcknowledgeAlert,
  onNavigate
}) {
  const [chartWindow, setChartWindow] = useState(4);

  const currentGlucose = patient?.current_glucose || 142;
  const predictedPeak = predictions?.risk_assessment?.projected_peak_mgdl || 198;
  const spikeProb = predictions?.risk_assessment?.spike_probability_pct || 58;

  return (
    <div className="content-area">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Overview Dashboard</h1>
          <p className="page-description">
            Real-time glycemic telemetry, proactive 2-hour digital twin forecast, and active clinical risk indicators.
          </p>
        </div>
      </div>

      {/* 4 Summary KPI Metric Cards */}
      <div className="kpi-grid">
        <MetricCard
          title="Current Glucose"
          value={currentGlucose}
          unit="mg/dL"
          badgeText="Target Zone"
          badgeVariant="target"
          trend={patient?.trend || 'rising'}
          deltaText="+12 mg/dL"
          subtext="vs 1 hour ago"
        />

        <MetricCard
          title="2-Hour Projected Peak"
          value={predictedPeak}
          unit="mg/dL"
          badgeText={`Spike Risk: ${spikeProb}%`}
          badgeVariant="warning"
          trend="rising"
          deltaText="+56 mg/dL"
          subtext="Projected in ~60m"
        />

        <MetricCard
          title="Time In Range (Today)"
          value="78%"
          unit="TIR"
          badgeText="Goal > 70%"
          badgeVariant="target"
          trend="stable"
          deltaText="18h 42m"
          subtext="in 70-180 mg/dL"
        />

        <MetricCard
          title="Active Metabolic Load"
          value={`${twinStatus?.active_iob_units || 1.2} U`}
          unit="IOB"
          badgeText="COB: 35g"
          badgeVariant="twin"
          trend="stable"
          deltaText="Insulin / Carbs"
          subtext="Last bolus 45m ago"
        />
      </div>

      {/* Main Workspace Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 'var(--spacing-md)', marginBottom: 'var(--spacing-md)' }}>
        {/* Left Column: Primary Glucose Chart */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
          <GlucoseChart
            telemetryData={telemetry}
            predictionData={predictions}
            selectedWindow={chartWindow}
            onWindowChange={setChartWindow}
            showPredictions={true}
            height={340}
          />

          {/* Time in Range Breakdown Card */}
          <Card
            title="Ambulatory Glycemic Status"
            subtitle="Distribution of readings across clinical target ranges"
          >
            <TimeInRangeBar target={78} low={6} veryLow={1} high={13} veryHigh={2} />
          </Card>
        </div>

        {/* Right Column: Twin Status & Patient Summary */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
          <TwinStatusCard twinStatus={twinStatus} />
          <PatientSummaryCard patient={patient} />
        </div>
      </div>

      {/* Bottom Row: XAI Feature Drivers Preview + Recent Alerts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-md)' }}>
        <ShapWaterfallChart features={xaiFeatures} compact={true} />
        <RecentAlertsCard
          alerts={alerts}
          onAcknowledge={onAcknowledgeAlert}
          onViewAll={() => onNavigate('alerts')}
        />
      </div>
    </div>
  );
}
