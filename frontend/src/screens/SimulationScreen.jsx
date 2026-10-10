import React, { useState } from 'react';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import SliderInput from '../components/common/SliderInput';
import SimulationCompareChart from '../components/charts/SimulationCompareChart';
import { simulateCounterfactualResponse } from '../services/mockData';
import { Play, RotateCcw, Sparkles } from 'lucide-react';

const PRESETS = [
  { label: 'Post-Meal Walk (+30m)', activity: 30, sleep: 0, carbs: 45, insulin: 0 },
  { label: 'High Carb Intake (85g)', activity: 0, sleep: 0, carbs: 85, insulin: 0 },
  { label: 'Corrective Bolus (+2U)', activity: 0, sleep: 0, carbs: 45, insulin: 2 },
  { label: 'Deep Rest (+1.5h)', activity: 0, sleep: 1.5, carbs: 45, insulin: 0 }
];

/**
 * Screen 5: What-If Simulation (Counterfactual Sandbox)
 */
export default function SimulationScreen() {
  const [activity, setActivity] = useState(20);
  const [sleep, setSleep] = useState(1.0);
  const [carbs, setCarbs] = useState(45);
  const [insulin, setInsulin] = useState(2.0);

  // Compute simulation response
  const [simulationResult, setSimulationResult] = useState(() =>
    simulateCounterfactualResponse({
      activity_minutes: 20,
      sleep_hours: 1.0,
      carbs_grams: 45,
      insulin_units: 2.0
    })
  );

  const handleRunSimulation = () => {
    const res = simulateCounterfactualResponse({
      activity_minutes: activity,
      sleep_hours: sleep,
      carbs_grams: carbs,
      insulin_units: insulin
    });
    setSimulationResult(res);
  };

  const handleReset = () => {
    setActivity(0);
    setSleep(0);
    setCarbs(45);
    setInsulin(0);
    const res = simulateCounterfactualResponse({
      activity_minutes: 0,
      sleep_hours: 0,
      carbs_grams: 45,
      insulin_units: 0
    });
    setSimulationResult(res);
  };

  const handleApplyPreset = (p) => {
    setActivity(p.activity);
    setSleep(p.sleep);
    setCarbs(p.carbs);
    setInsulin(p.insulin);
    const res = simulateCounterfactualResponse({
      activity_minutes: p.activity,
      sleep_hours: p.sleep,
      carbs_grams: p.carbs,
      insulin_units: p.insulin
    });
    setSimulationResult(res);
  };

  return (
    <div className="content-area">
      <div className="page-header">
        <div>
          <h1 className="page-title">Counterfactual "What-If" Simulation</h1>
          <p className="page-description">
            Simulate candidate physiological, lifestyle, and pharmacological adjustments to preview the digital twin's glycemic response.
          </p>
        </div>
        <Badge variant="twin">In Silico Sandbox Active</Badge>
      </div>

      {/* Preset Quick Actions */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 'var(--spacing-md)', flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-navy-700)', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          <Sparkles size={14} color="var(--color-teal-600)" /> Scenario Presets:
        </span>
        {PRESETS.map((pr, idx) => (
          <button
            key={idx}
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => handleApplyPreset(pr)}
          >
            {pr.label}
          </button>
        ))}
      </div>

      {/* Two-Column Workspace: Controls & Results */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 2fr', gap: 'var(--spacing-md)', marginBottom: 'var(--spacing-md)' }}>
        {/* Controls Column */}
        <Card
          title="Adjust Simulation Variables"
          subtitle="Modify patient inputs to re-predict metabolic outcomes"
          footer={
            <div style={{ display: 'flex', gap: 10 }}>
              <Button variant="primary" icon={Play} onClick={handleRunSimulation}>
                Run Simulation
              </Button>
              <Button variant="secondary" icon={RotateCcw} onClick={handleReset}>
                Reset
              </Button>
            </div>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <SliderInput
              label="Physical Activity Adjustment"
              value={activity}
              unit="min"
              valuePrefix={activity > 0 ? '+' : ''}
              min={-30}
              max={90}
              step={5}
              onChange={setActivity}
              helperText="Aerobic exercise enhances peripheral insulin sensitivity"
            />

            <SliderInput
              label="Sleep / Rest Recovery"
              value={sleep}
              unit="hours"
              valuePrefix={sleep > 0 ? '+' : ''}
              min={-2}
              max={3}
              step={0.5}
              onChange={setSleep}
              helperText="Sleep quality buffers cortisol-driven dawn phenomenon"
            />

            <SliderInput
              label="Meal Carbohydrates"
              value={carbs}
              unit="grams"
              min={0}
              max={120}
              step={5}
              onChange={setCarbs}
              helperText="Total carbohydrates planned for prospective meal"
            />

            <SliderInput
              label="Insulin Dose Adjustment"
              value={insulin}
              unit="Units"
              valuePrefix={insulin > 0 ? '+' : ''}
              min={0}
              max={6}
              step={0.5}
              onChange={setInsulin}
              helperText="Rapid-acting bolus insulin adjustment"
            />
          </div>
        </Card>

        {/* Results Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
          <SimulationCompareChart
            trajectory={simulationResult.comparative_trajectory}
            height={280}
          />

          {/* Outcome Delta Summary Table */}
          <Card title="Projected Metabolic Outcome Comparison">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
              <div style={{ backgroundColor: 'var(--color-canvas)', padding: 12, borderRadius: 8 }}>
                <div style={{ fontSize: 11, color: 'var(--color-navy-500)', textTransform: 'uppercase' }}>Peak Glucose</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-navy-900)' }}>
                  {simulationResult.simulated_peak_mgdl} mg/dL
                </div>
                <div style={{ fontSize: 11, color: simulationResult.peak_reduction_mgdl >= 0 ? 'var(--color-target-green-dark)' : 'var(--color-critical-rose)', fontWeight: 600 }}>
                  {simulationResult.peak_reduction_mgdl >= 0 ? `-${simulationResult.peak_reduction_mgdl}` : `+${Math.abs(simulationResult.peak_reduction_mgdl)}`} mg/dL delta
                </div>
              </div>

              <div style={{ backgroundColor: 'var(--color-canvas)', padding: 12, borderRadius: 8 }}>
                <div style={{ fontSize: 11, color: 'var(--color-navy-500)', textTransform: 'uppercase' }}>Time In Range</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-target-green-dark)' }}>
                  {simulationResult.simulated_tir_pct}%
                </div>
                <div style={{ fontSize: 11, color: 'var(--color-navy-500)' }}>
                  from {simulationResult.baseline_tir_pct}% baseline
                </div>
              </div>

              <div style={{ backgroundColor: 'var(--color-canvas)', padding: 12, borderRadius: 8 }}>
                <div style={{ fontSize: 11, color: 'var(--color-navy-500)', textTransform: 'uppercase' }}>Risk Classification</div>
                <div style={{ marginTop: 4 }}>
                  <Badge variant={simulationResult.risk_tier_change.after === 'low' ? 'target' : simulationResult.risk_tier_change.after === 'moderate' ? 'warning' : 'critical'}>
                    {simulationResult.risk_tier_change.after.toUpperCase()} RISK
                  </Badge>
                </div>
                <div style={{ fontSize: 11, color: 'var(--color-navy-500)', marginTop: 4 }}>
                  was {simulationResult.risk_tier_change.before}
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
