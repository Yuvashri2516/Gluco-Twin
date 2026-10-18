import React, { useState, useEffect } from 'react';
import { fetchSleepReadings, fetchStepReadings } from '../api/client';
import LoadingSpinner from './Common/LoadingSpinner';

export default function SleepActivityPanel({ selectedPatient, hours = 24 }) {
  const patientId = selectedPatient?.id;
  const [sleepData, setSleepData] = useState(null);
  const [stepData, setStepData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!patientId) return;
    let isMounted = true;
    const controller = new AbortController();

    async function loadData() {
      setIsLoading(true);
      setError(null);
      try {
        const [sleepRes, stepRes] = await Promise.all([
          fetchSleepReadings(patientId, hours, controller.signal),
          fetchStepReadings(patientId, hours, controller.signal),
        ]);
        if (isMounted) {
          setSleepData(sleepRes);
          setStepData(stepRes);
        }
      } catch (err) {
        if (err.name !== 'AbortError' && isMounted) {
          setError(err.message || 'Failed to load sleep and activity telemetry.');
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadData();
    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [patientId, hours]);

  if (!selectedPatient) {
    return (
      <div className="section-container">
        <p className="section-desc">Select a patient to inspect sleep and physical activity streams.</p>
      </div>
    );
  }

  // Sleep stage color mapping
  const stageColors = {
    deep: '#3b82f6',   // Solid Blue
    rem: '#8b5cf6',    // Purple
    light: '#06b6d4',  // Cyan
    awake: '#f59e0b',  // Amber
  };

  return (
    <div className="section-container" style={{ animation: 'fadeIn 0.3s ease' }}>
      <div className="section-header-banner" style={{ marginBottom: '20px' }}>
        <div>
          <h2 className="section-title">Sleep Architecture & Physical Activity Telemetry</h2>
          <p className="section-desc">
            Longitudinal polysomnography stages and 15-minute interval step tracking synchronized with metabolic rhythms.
          </p>
        </div>
        <span className="badge badge-normal" style={{ fontSize: '0.75rem', padding: '6px 12px' }}>
          Window: Last {hours} Hours
        </span>
      </div>

      {isLoading && (
        <div style={{ padding: '40px 0' }}>
          <LoadingSpinner message="Ingesting sleep architecture and physical activity streams..." />
        </div>
      )}

      {error && (
        <div style={{ padding: '16px', background: 'var(--status-critical-bg)', color: 'var(--status-critical)', borderRadius: 'var(--radius-md)', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {!isLoading && !error && (
        <>
          {/* SECTION 1: SLEEP ARCHITECTURE */}
          <div style={{ marginBottom: '32px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span>🌙</span> Sleep Architecture & Restorative Metrics
              </h3>
              <span className="badge badge-neutral" style={{ fontSize: '0.72rem' }}>
                Synthetic Polysomnography
              </span>
            </div>

            {/* Sleep Summary Metric Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px', marginBottom: '16px' }}>
              <div className="metric-card" style={{ padding: '16px', borderLeft: '4px solid #3b82f6' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Sleep Duration</span>
                <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '4px' }}>
                  {sleepData?.total_sleep_hours ?? 0} <span style={{ fontSize: '0.85rem', fontWeight: 400 }}>hrs</span>
                </div>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Target: 7.0 - 9.0 hrs</span>
              </div>

              <div className="metric-card" style={{ padding: '16px', borderLeft: '4px solid #10b981' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Sleep Efficiency</span>
                <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--status-normal)', marginTop: '4px' }}>
                  {sleepData?.sleep_efficiency_pct ?? 0}%
                </div>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Time in bed vs sleep</span>
              </div>

              <div className="metric-card" style={{ padding: '16px', borderLeft: '4px solid #8b5cf6' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Deep Sleep (N3)</span>
                <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#a78bfa', marginTop: '4px' }}>
                  {sleepData?.deep_sleep_hours ?? 0} <span style={{ fontSize: '0.85rem', fontWeight: 400 }}>hrs</span>
                </div>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Physical restoration</span>
              </div>

              <div className="metric-card" style={{ padding: '16px', borderLeft: '4px solid #06b6d4' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>REM Sleep</span>
                <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#22d3ee', marginTop: '4px' }}>
                  {sleepData?.rem_sleep_hours ?? 0} <span style={{ fontSize: '0.85rem', fontWeight: 400 }}>hrs</span>
                </div>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Neural consolidation</span>
              </div>
            </div>

            {/* Visual Stage Distribution Bar */}
            <div className="metric-card" style={{ padding: '18px', marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)' }}>Sleep Stage Distribution</span>
                <div style={{ display: 'flex', gap: '12px', fontSize: '0.75rem' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: stageColors.deep }} /> Deep
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: stageColors.rem }} /> REM
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: stageColors.light }} /> Light
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: stageColors.awake }} /> Awake
                  </span>
                </div>
              </div>

              {/* Progress bar depicting stage ratios */}
              <div style={{ display: 'flex', height: '24px', borderRadius: '6px', overflow: 'hidden', background: 'rgba(255,255,255,0.05)' }}>
                {sleepData?.records && sleepData.records.length > 0 ? (
                  sleepData.records.map((r, i) => (
                    <div
                      key={r.id || i}
                      title={`${r.stage.toUpperCase()}: ${r.duration_minutes} min (${new Date(r.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})`}
                      style={{
                        flex: r.duration_minutes,
                        backgroundColor: stageColors[r.stage] || '#64748b',
                        borderRight: '1px solid rgba(0,0,0,0.3)',
                        transition: 'opacity 0.2s',
                        cursor: 'pointer',
                      }}
                    />
                  ))
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    No recorded sleep intervals in the selected window
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* SECTION 2: PHYSICAL ACTIVITY (STEP COUNTS) */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span>🚶‍♂️</span> Physical Activity & 15-Minute Interval Step Counts
              </h3>
              <span className="badge badge-neutral" style={{ fontSize: '0.72rem' }}>
                Synthetic Accelerometry
              </span>
            </div>

            {/* Step Summary Metric Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px', marginBottom: '16px' }}>
              <div className="metric-card" style={{ padding: '16px', borderLeft: '4px solid #10b981' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Steps (Window)</span>
                <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '4px' }}>
                  {stepData?.total_steps_24h?.toLocaleString() ?? 0}
                </div>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Cumulative active steps</span>
              </div>

              <div className="metric-card" style={{ padding: '16px', borderLeft: '4px solid #38bdf8' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Latest 15m Interval</span>
                <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--primary)', marginTop: '4px' }}>
                  {stepData?.latest_interval_steps ?? 0} <span style={{ fontSize: '0.85rem', fontWeight: 400 }}>steps</span>
                </div>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Current cadence</span>
              </div>

              <div className="metric-card" style={{ padding: '16px', borderLeft: '4px solid #f59e0b' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Peak Exertion Interval</span>
                <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--status-warning)', marginTop: '4px' }}>
                  {stepData?.peak_interval_steps ?? 0} <span style={{ fontSize: '0.85rem', fontWeight: 400 }}>steps</span>
                </div>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Max in 15 minutes</span>
              </div>

              <div className="metric-card" style={{ padding: '16px', borderLeft: '4px solid #a855f7' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Hourly Average</span>
                <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#c084fc', marginTop: '4px' }}>
                  {stepData?.hourly_average_steps ?? 0} <span style={{ fontSize: '0.85rem', fontWeight: 400 }}>steps/h</span>
                </div>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Baseline exertion pace</span>
              </div>
            </div>

            {/* Step Time-Series Visualization */}
            <div className="metric-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <span style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-main)' }}>
                  15-Minute Interval Step Profile
                </span>
                <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                  {stepData?.records?.length || 0} telemetry epochs
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'flex-end', height: '140px', gap: '2px', paddingBottom: '10px', borderBottom: '1px solid var(--border)' }}>
                {stepData?.records && stepData.records.length > 0 ? (
                  stepData.records.map((r, i) => {
                    const peak = stepData.peak_interval_steps || 1000;
                    const heightPct = Math.min(100, Math.max(3, (r.interval_steps / peak) * 100));
                    const isPeak = r.interval_steps > 600;
                    return (
                      <div
                        key={r.id || i}
                        title={`${new Date(r.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}: ${r.interval_steps} steps (Cumulative: ${r.daily_cumulative_steps.toLocaleString()})`}
                        style={{
                          flex: 1,
                          height: `${heightPct}%`,
                          backgroundColor: isPeak ? 'var(--status-normal)' : 'var(--primary)',
                          opacity: r.interval_steps === 0 ? 0.2 : 0.85,
                          borderRadius: '2px 2px 0 0',
                          cursor: 'pointer',
                        }}
                      />
                    );
                  })
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                    No step telemetry available for this window
                  </div>
                )}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '8px' }}>
                <span>-{hours}h Start</span>
                <span>Interval Exertion (Steps / 15-Min)</span>
                <span>Latest Reading</span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
