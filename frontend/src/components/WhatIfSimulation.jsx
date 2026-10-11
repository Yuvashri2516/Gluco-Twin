import React, { useState, useEffect, useCallback, useId } from 'react';
import { runWhatIfSimulation } from '../api/client';

export default function WhatIfSimulation({ selectedPatient }) {
  const [carbs, setCarbs] = useState(30);
  const [activityMins, setActivityMins] = useState(0);
  const [simulationResult, setSimulationResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const simId = useId();

  const patientId = selectedPatient?.id;

  const executeSimulation = useCallback(async (carbsVal, activityVal) => {
    if (!patientId) return;
    setIsLoading(true);
    setSimulationResult(null);
    setError(null);
    try {
      const res = await runWhatIfSimulation({
        patientId,
        additionalCarbs: carbsVal,
        activityMinutes: activityVal,
      });
      setSimulationResult(res);
    } catch (err) {
      setError(err.message || 'Failed to calculate scenario simulation.');
    } finally {
      setIsLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    if (patientId) {
      executeSimulation(carbs, activityMins);
    } else {
      setSimulationResult(null);
    }
  }, [patientId, executeSimulation, carbs, activityMins]);

  if (!selectedPatient) {
    return null;
  }

  const baselineG = simulationResult?.baseline_glucose ?? 120.0;
  const projectedG = simulationResult?.projected_scenario_glucose ?? baselineG;
  const delta = (projectedG - baselineG).toFixed(1);
  const isBreach = simulationResult?.projected_spike_risk_breach ?? (projectedG >= 180.0);

  return (
    <div className="section-container simulation-container" id={`what-if-${simId}`}>
      {/* Header Banner */}
      <div className="section-header-banner">
        <div className="predictions-header-row">
          <div>
            <div className="section-title-row">
              <h2 className="section-title">What-If Counterfactual Sandbox</h2>
              <span className="badge badge-twin">Illustrative Scenario Calculator</span>
            </div>
            <p className="section-desc">
              Deterministic, software-only simulation evaluating hypothetical meal carbohydrate and physical exertion perturbations.
            </p>
          </div>
        </div>
      </div>

      {/* Mandatory Clinical Disclaimer Banner */}
      <div className="simulation-disclaimer-banner">
        <div className="disclaimer-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        </div>
        <div className="disclaimer-text-group">
          <strong>SIMULATED — NOT A CLINICAL PREDICTION</strong>
          <p>
            This calculator is an educational prototype. It demonstrates mathematical scenario sensitivity using simplified heuristics.
            <strong> It does NOT prescribe insulin doses, evaluate clinical treatments, or represent actual patient physiology.</strong>
          </p>
        </div>
      </div>

      <div className="simulation-layout-grid">
        {/* Controls Column */}
        <div className="sim-card sim-controls-card">
          <h3 className="sim-card-heading">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
            Hypothetical Inputs
          </h3>

          <div className="sim-baseline-strip">
            <div className="baseline-item">
              <span className="baseline-lbl">Subject</span>
              <span className="baseline-val">{selectedPatient.name}</span>
            </div>
            <div className="baseline-item">
              <span className="baseline-lbl">Clinical Type</span>
              <span className="baseline-val">{selectedPatient.diabetes_type}</span>
            </div>
            <div className="baseline-item">
              <span className="baseline-lbl">Baseline Glucose</span>
              <span className="baseline-val highlight-cyan">{baselineG} mg/dL</span>
            </div>
          </div>

          {/* Input 1: Additional Meal Carbs */}
          <div className="sim-slider-group">
            <div className="slider-label-row">
              <label htmlFor="carb-slider" className="slider-title">
                Additional Meal Carbohydrates:
              </label>
              <span className="slider-current-badge">{carbs}g</span>
            </div>
            <input
              id="carb-slider"
              type="range"
              min="0"
              max="120"
              step="5"
              value={carbs}
              onChange={(e) => setCarbs(Number(e.target.value))}
              className="sim-range-input"
            />
            <div className="slider-scale-row">
              <span>0g (Fasting)</span>
              <span>30g (Snack)</span>
              <span>60g (Standard)</span>
              <span>120g (Heavy)</span>
            </div>
          </div>

          {/* Input 2: Physical Exertion Duration */}
          <div className="sim-slider-group">
            <div className="slider-label-row">
              <label htmlFor="activity-slider" className="slider-title">
                Moderate Physical Exertion:
              </label>
              <span className="slider-current-badge">{activityMins} min</span>
            </div>
            <input
              id="activity-slider"
              type="range"
              min="0"
              max="90"
              step="5"
              value={activityMins}
              onChange={(e) => setActivityMins(Number(e.target.value))}
              className="sim-range-input"
            />
            <div className="slider-scale-row">
              <span>0 min</span>
              <span>30 min (Walk)</span>
              <span>60 min (Jog)</span>
              <span>90 min</span>
            </div>
          </div>
        </div>

        {/* Output Projection Column */}
        <div className={`sim-card sim-output-card ${isBreach ? 'sim-breach' : 'sim-safe'}`}>
          <h3 className="sim-card-heading">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
            Calculated Scenario Projection
          </h3>

          <div className="sim-result-hero">
            <span className="sim-result-label">
              Projected Postprandial Glucose {isLoading ? '(Calculating...)' : ''}
            </span>
            {error && <div className="twin-error-note">{error}</div>}
            <div className="sim-result-score-row">
              <span className="sim-projected-number">{projectedG}</span>
              <span className="sim-unit">mg/dL</span>
              <span className={`sim-delta-badge ${Number(delta) >= 0 ? 'delta-pos' : 'delta-neg'}`}>
                {Number(delta) >= 0 ? `+${delta}` : delta} mg/dL
              </span>
            </div>

            <div className="sim-status-banner">
              {isBreach ? (
                <span className="badge badge-critical" style={{ fontSize: '0.86rem', padding: '6px 14px' }}>
                  Threshold Breach Projected (&ge; 180 mg/dL)
                </span>
              ) : (
                <span className="badge badge-normal" style={{ fontSize: '0.86rem', padding: '6px 14px' }}>
                  Target Range Maintained (&lt; 180 mg/dL)
                </span>
              )}
            </div>
          </div>

          {/* Breakdown Items */}
          <div className="sim-breakdown-list">
            <div className="breakdown-item">
              <span className="breakdown-lbl">Baseline Blood Glucose:</span>
              <span className="breakdown-val">{baselineG} mg/dL</span>
            </div>
            <div className="breakdown-item">
              <span className="breakdown-lbl">Carbohydrate Glycemic Influx (+{carbs}g):</span>
              <span className="breakdown-val highlight-warning">
                +{simulationResult?.projected_carb_impact_mg_dl ?? 0} mg/dL
              </span>
            </div>
            <div className="breakdown-item">
              <span className="breakdown-lbl">Muscular Activity Clearance (-{activityMins}m):</span>
              <span className="breakdown-val highlight-normal">
                {simulationResult?.projected_activity_impact_mg_dl ?? 0} mg/dL
              </span>
            </div>
          </div>

          {/* Documented Assumptions Box */}
          <div className="sim-assumptions-box">
            <h4>Documented Heuristic Assumptions:</h4>
            <ul>
              {simulationResult?.assumptions ? (
                simulationResult.assumptions.map((assump, idx) => (
                  <li key={idx}>{assump}</li>
                ))
              ) : (
                <>
                  <li>Standard linear carbohydrate absorption curve scaled to patient weight.</li>
                  <li>Insulin resistance modifier calibrated to {selectedPatient.diabetes_type}.</li>
                  <li>Approx. 0.75 mg/dL clearance rate per minute of exertion.</li>
                </>
              )}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
