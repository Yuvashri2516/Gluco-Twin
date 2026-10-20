import React, { useState, useEffect, useCallback, useId } from 'react';
import { runWhatIfSimulation } from '../api/client';

export default function WhatIfSimulation({ selectedPatient }) {
  const [carbs, setCarbs] = useState(30);
  const [activityMins, setActivityMins] = useState(0);
  const [simulationResult, setSimulationResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const simId = useId();

  // Support either id or patient_id depending on the patient object.
  const rawPatientId = selectedPatient?.id ?? selectedPatient?.patient_id;
  const patientId = Number(rawPatientId);

  const hasValidPatient =
    Number.isInteger(patientId) && patientId > 0;

  const patientName =
    selectedPatient?.name ??
    selectedPatient?.patient_name ??
    'Selected patient';

  const diabetesType =
    selectedPatient?.diabetes_type ?? 'Not specified';

  // Run the simulation using the three arguments expected by client.js.
  const executeSimulation = useCallback(
    async (carbsValue, activityValue) => {
      if (!hasValidPatient) {
        setSimulationResult(null);
        setError('Please select a valid patient before running the simulation.');
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const result = await runWhatIfSimulation(
          patientId,
          Number(carbsValue),
          Number(activityValue)
        );

        setSimulationResult(result);
      } catch (err) {
        setSimulationResult(null);

        setError(
          err?.detail ||
          err?.message ||
          'Failed to calculate the scenario simulation.'
        );
      } finally {
        setIsLoading(false);
      }
    },
    [patientId, hasValidPatient]
  );

  // Recalculate whenever the patient or slider values change.
  useEffect(() => {
    let cancelled = false;

    async function calculate() {
      if (!hasValidPatient) {
        setSimulationResult(null);
        setError(
          selectedPatient
            ? 'Please select a valid patient before running the simulation.'
            : null
        );
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const result = await runWhatIfSimulation(
          patientId,
          Number(carbs),
          Number(activityMins)
        );

        if (!cancelled) {
          setSimulationResult(result);
        }
      } catch (err) {
        if (!cancelled) {
          setSimulationResult(null);
          setError(
            err?.detail ||
            err?.message ||
            'Failed to calculate the scenario simulation.'
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    calculate();

    return () => {
      cancelled = true;
    };
  }, [
    patientId,
    hasValidPatient,
    carbs,
    activityMins,
    selectedPatient,
  ]);

  if (!selectedPatient) {
    return null;
  }

  const baselineG =
    simulationResult?.baseline_glucose ?? null;

  const projectedG =
    simulationResult?.projected_scenario_glucose ?? null;

  const delta =
    baselineG !== null && projectedG !== null
      ? (projectedG - baselineG).toFixed(1)
      : null;

  const isBreach =
    simulationResult?.projected_spike_risk_breach ??
    (projectedG !== null && projectedG >= 180);

  const formatNumber = (value) => {
    if (value === null || value === undefined || !Number.isFinite(Number(value))) {
      return '—';
    }

    return Number(value).toFixed(1);
  };

  return (
    <div
      className="section-container simulation-container"
      id={`what-if-${simId}`}
    >
      {/* Header */}
      <div className="section-header-banner">
        <div className="predictions-header-row">
          <div>
            <div className="section-title-row">
              <h2 className="section-title">
                What-If Counterfactual Sandbox
              </h2>

              <span className="badge badge-twin">
                Illustrative Scenario Calculator
              </span>
            </div>

            <p className="section-desc">
              Deterministic, software-only simulation evaluating
              hypothetical meal carbohydrate and physical exertion
              scenarios.
            </p>
          </div>
        </div>
      </div>

      {/* Clinical disclaimer */}
      <div className="simulation-disclaimer-banner">
        <div className="disclaimer-icon">
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        </div>

        <div className="disclaimer-text-group">
          <strong>
            SIMULATED — NOT A CLINICAL PREDICTION
          </strong>

          <p>
            This calculator is an educational prototype. It demonstrates
            mathematical scenario sensitivity using simplified heuristics.
            <strong>
              {' '}It does NOT prescribe insulin doses, evaluate clinical
              treatments, or represent actual patient physiology.
            </strong>
          </p>
        </div>
      </div>

      {/* Main layout */}
      <div className="simulation-layout-grid">

        {/* Input controls */}
        <div className="sim-card sim-controls-card">
          <h3 className="sim-card-heading">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>

            Hypothetical Inputs
          </h3>

          {/* Patient details */}
          <div className="sim-baseline-strip">
            <div className="baseline-item">
              <span className="baseline-lbl">
                Subject
              </span>

              <span className="baseline-val">
                {patientName}
              </span>
            </div>

            <div className="baseline-item">
              <span className="baseline-lbl">
                Clinical Type
              </span>

              <span className="baseline-val">
                {diabetesType}
              </span>
            </div>

            <div className="baseline-item">
              <span className="baseline-lbl">
                Baseline Glucose
              </span>

              <span className="baseline-val highlight-cyan">
                {baselineG !== null
                  ? `${formatNumber(baselineG)} mg/dL`
                  : 'Waiting for result'}
              </span>
            </div>
          </div>

          {/* Carbohydrates slider */}
          <div className="sim-slider-group">
            <div className="slider-label-row">
              <label
                htmlFor={`carb-slider-${simId}`}
                className="slider-title"
              >
                Additional Meal Carbohydrates:
              </label>

              <span className="slider-current-badge">
                {carbs}g
              </span>
            </div>

            <input
              id={`carb-slider-${simId}`}
              type="range"
              min="0"
              max="120"
              step="5"
              value={carbs}
              onChange={(event) =>
                setCarbs(Number(event.target.value))
              }
              className="sim-range-input"
              aria-label="Additional meal carbohydrates in grams"
            />

            <div className="slider-scale-row">
              <span>0g (Fasting)</span>
              <span>30g (Snack)</span>
              <span>60g (Standard)</span>
              <span>120g (Heavy)</span>
            </div>
          </div>

          {/* Physical activity slider */}
          <div className="sim-slider-group">
            <div className="slider-label-row">
              <label
                htmlFor={`activity-slider-${simId}`}
                className="slider-title"
              >
                Moderate Physical Exertion:
              </label>

              <span className="slider-current-badge">
                {activityMins} min
              </span>
            </div>

            <input
              id={`activity-slider-${simId}`}
              type="range"
              min="0"
              max="90"
              step="5"
              value={activityMins}
              onChange={(event) =>
                setActivityMins(Number(event.target.value))
              }
              className="sim-range-input"
              aria-label="Physical activity duration in minutes"
            />

            <div className="slider-scale-row">
              <span>0 min</span>
              <span>30 min (Walk)</span>
              <span>60 min (Jog)</span>
              <span>90 min</span>
            </div>
          </div>

          {!hasValidPatient && (
            <div className="twin-error-note" role="alert">
              Please select a valid patient to run this simulation.
            </div>
          )}

          <button
            type="button"
            className="btn btn-primary"
            onClick={() => executeSimulation(carbs, activityMins)}
            disabled={!hasValidPatient || isLoading}
            style={{ marginTop: '16px' }}
          >
            {isLoading ? 'Calculating...' : 'Recalculate Scenario'}
          </button>
        </div>

        {/* Calculated output */}
        <div
          className={`sim-card sim-output-card ${
            isBreach ? 'sim-breach' : 'sim-safe'
          }`}
        >
          <h3 className="sim-card-heading">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              aria-hidden="true"
            >
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
              Projected Postprandial Glucose
              {isLoading ? ' (Calculating...)' : ''}
            </span>

            {error && (
              <div
                className="twin-error-note"
                role="alert"
                style={{ margin: '12px 0' }}
              >
                {error}
              </div>
            )}

            <div className="sim-result-score-row">
              <span className="sim-projected-number">
                {projectedG !== null
                  ? formatNumber(projectedG)
                  : '—'}
              </span>

              <span className="sim-unit">
                mg/dL
              </span>

              {delta !== null && (
                <span
                  className={`sim-delta-badge ${
                    Number(delta) >= 0 ? 'delta-pos' : 'delta-neg'
                  }`}
                >
                  {Number(delta) >= 0 ? '+' : ''}
                  {delta} mg/dL
                </span>
              )}
            </div>

            <div className="sim-status-banner">
              {simulationResult ? (
                isBreach ? (
                  <span
                    className="badge badge-critical"
                    style={{
                      fontSize: '0.86rem',
                      padding: '6px 14px',
                    }}
                  >
                    Threshold Breach Projected (≥ 180 mg/dL)
                  </span>
                ) : (
                  <span
                    className="badge badge-normal"
                    style={{
                      fontSize: '0.86rem',
                      padding: '6px 14px',
                    }}
                  >
                    Target Range Maintained (&lt; 180 mg/dL)
                  </span>
                )
              ) : (
                <span className="badge badge-neutral">
                  {isLoading
                    ? 'Calculating scenario...'
                    : 'Waiting for a valid simulation result'}
                </span>
              )}
            </div>
          </div>

          {/* Result breakdown */}
          <div className="sim-breakdown-list">
            <div className="breakdown-item">
              <span className="breakdown-lbl">
                Baseline Blood Glucose:
              </span>

              <span className="breakdown-val">
                {baselineG !== null
                  ? `${formatNumber(baselineG)} mg/dL`
                  : '—'}
              </span>
            </div>

            <div className="breakdown-item">
              <span className="breakdown-lbl">
                Carbohydrate Glycemic Influx (+{carbs}g):
              </span>

              <span className="breakdown-val highlight-warning">
                {simulationResult
                  ? `+${formatNumber(
                      simulationResult.projected_carb_impact_mg_dl
                    )} mg/dL`
                  : '—'}
              </span>
            </div>

            <div className="breakdown-item">
              <span className="breakdown-lbl">
                Muscular Activity Clearance (-{activityMins}m):
              </span>

              <span className="breakdown-val highlight-normal">
                {simulationResult
                  ? `${formatNumber(
                      simulationResult.projected_activity_impact_mg_dl
                    )} mg/dL`
                  : '—'}
              </span>
            </div>
          </div>

          {/* Assumptions */}
          <div className="sim-assumptions-box">
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '8px',
                gap: '8px',
                flexWrap: 'wrap',
              }}
            >
              <h4 style={{ margin: 0 }}>
                Documented Heuristic Assumptions:
              </h4>

              <span
                className="badge badge-neutral"
                style={{ fontSize: '0.68rem' }}
              >
                {simulationResult?.formula_version ||
                  'v1.0.0-heuristic'}
              </span>
            </div>

            {simulationResult?.data_quality_warnings?.length > 0 && (
              <div
                style={{
                  margin: '6px 0 10px',
                  padding: '6px 10px',
                  background: 'rgba(234, 179, 8, 0.1)',
                  borderRadius: '4px',
                  borderLeft: '3px solid #eab308',
                  fontSize: '0.78rem',
                }}
                role="status"
              >
                {simulationResult.data_quality_warnings.map(
                  (warning, index) => (
                    <div key={`${index}-${warning}`}>
                      ⚠ {warning}
                    </div>
                  )
                )}
              </div>
            )}

            <ul>
              {simulationResult?.assumptions?.length > 0 ? (
                simulationResult.assumptions.map(
                  (assumption, index) => (
                    <li key={`${index}-${assumption}`}>
                      {assumption}
                    </li>
                  )
                )
              ) : (
                <>
                  <li>
                    Standard linear carbohydrate absorption curve
                    scaled to patient weight.
                  </li>
                  <li>
                    Insulin resistance modifier calibrated to{' '}
                    {diabetesType}.
                  </li>
                  <li>
                    Approx. 0.75 mg/dL clearance rate per minute
                    of exertion.
                  </li>
                </>
              )}
            </ul>

            {simulationResult?.disclaimer && (
              <p style={{ marginTop: '12px', fontSize: '0.8rem' }}>
                {simulationResult.disclaimer}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}