import React, { useState, useEffect } from 'react';
import { fetchPatientLabs, fetchPatientGenetics } from '../api/client';
import LoadingSpinner from './Common/LoadingSpinner';

export default function PatientEhrHistory({ selectedPatient }) {
  const patientId = selectedPatient?.id;
  const [labs, setLabs] = useState([]);
  const [genetics, setGenetics] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!patientId) return;
    let isMounted = true;
    const controller = new AbortController();

    async function loadEhrData() {
      setIsLoading(true);
      setError(null);
      try {
        const [labsData, geneticsData] = await Promise.all([
          fetchPatientLabs(patientId, controller.signal),
          fetchPatientGenetics(patientId, controller.signal),
        ]);
        if (isMounted) {
          setLabs(labsData || []);
          setGenetics(geneticsData || []);
        }
      } catch (err) {
        if (err.name !== 'AbortError' && isMounted) {
          setError(err.message || 'Failed to load historical EHR data.');
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadEhrData();
    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [patientId]);

  if (!selectedPatient) {
    return (
      <div className="section-container">
        <p className="section-desc">Select a patient from the top bar to inspect historical EHR records.</p>
      </div>
    );
  }

  // Parse diagnoses list
  const diagnosesList = selectedPatient.historical_diagnoses
    ? selectedPatient.historical_diagnoses.split(',').map((d) => d.trim()).filter(Boolean)
    : ['Type 2 Diabetes Mellitus'];

  // Group labs by measurement date
  const labsByDate = labs.reduce((acc, lab) => {
    const dStr = new Date(lab.measurement_date).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
    if (!acc[dStr]) acc[dStr] = [];
    acc[dStr].push(lab);
    return acc;
  }, {});

  const datesAsc = Object.keys(labsByDate);

  return (
    <div className="section-container" style={{ animation: 'fadeIn 0.3s ease' }}>
      <div className="section-header-banner" style={{ marginBottom: '20px' }}>
        <div>
          <h2 className="section-title">Patient Historical EHR & Clinical Phenotype</h2>
          <p className="section-desc">
            Baseline demographics, documented diagnoses, longitudinal laboratory results, and simulated genetic markers.
          </p>
        </div>
        <span className="badge badge-neutral" style={{ fontSize: '0.75rem', padding: '6px 12px' }}>
          EHR Record ID: GT-P{selectedPatient.id.toString().padStart(4, '0')}
        </span>
      </div>

      {/* Safety Notice */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '12px 16px',
          backgroundColor: 'rgba(56, 189, 248, 0.08)',
          borderLeft: '4px solid var(--primary)',
          borderRadius: 'var(--radius-sm)',
          marginBottom: '24px',
          fontSize: '0.84rem',
          color: 'var(--text-muted)',
        }}
      >
        <span style={{ fontSize: '1.1rem' }}>ℹ️</span>
        <div>
          <strong style={{ color: 'var(--text-main)' }}>Synthetic Electronic Health Record (EHR):</strong> All clinical diagnoses,
          laboratory panels, and genetic markers displayed below are deterministically simulated for research demonstration. Not for medical diagnosis or clinical decision-making.
        </div>
      </div>

      {/* Grid: Diagnoses & Physical Scale */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        {/* Historical Diagnoses Card */}
        <div className="metric-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>📋</span> Documented Historical Diagnoses
          </h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '16px' }}>
            <span className="badge badge-normal" style={{ fontSize: '0.82rem', padding: '6px 10px' }}>
              Primary: {selectedPatient.diabetes_type}
            </span>
            {diagnosesList.map((diag, idx) => (
              <span key={idx} className="badge badge-neutral" style={{ fontSize: '0.82rem', padding: '6px 10px' }}>
                {diag}
              </span>
            ))}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border)', paddingTop: '12px' }}>
            Vintage: Diagnosed {selectedPatient.years_since_diagnosis} years ago | Status: Under Active Continuous Telemetry Monitoring
          </div>
        </div>

        {/* Physical Scale & BMI Card */}
        <div className="metric-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>⚖️</span> Anthropometric Baseline
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', textAlign: 'center' }}>
            <div style={{ padding: '10px', background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Height</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-main)' }}>{selectedPatient.height_cm || '—'} cm</div>
            </div>
            <div style={{ padding: '10px', background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Weight</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-main)' }}>{selectedPatient.weight_kg || '—'} kg</div>
            </div>
            <div style={{ padding: '10px', background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>BMI</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--primary)' }}>
                {selectedPatient.weight_kg && selectedPatient.height_cm
                  ? (selectedPatient.weight_kg / Math.pow(selectedPatient.height_cm / 100, 2)).toFixed(1)
                  : '—'}
              </div>
            </div>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '14px', borderTop: '1px solid var(--border)', paddingTop: '12px' }}>
            Clinical Type: <strong style={{ color: 'var(--text-main)' }}>{selectedPatient.diabetes_type}</strong> | Sex: {selectedPatient.gender} | Age: {selectedPatient.age}
          </div>
        </div>
      </div>

      {isLoading && (
        <div style={{ padding: '40px 0' }}>
          <LoadingSpinner message="Retrieving laboratory and genomic panels..." />
        </div>
      )}

      {error && (
        <div style={{ padding: '16px', background: 'var(--status-critical-bg)', color: 'var(--status-critical)', borderRadius: 'var(--radius-md)', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {/* Laboratory Results Longitudinal Timeline */}
      {!isLoading && !error && (
        <div style={{ marginBottom: '32px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>🧪</span> Longitudinal Laboratory Panels (HbA1c & Lipids)
            </h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {labs.length} test records across {datesAsc.length} collection dates
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
            {datesAsc.map((dateStr) => {
              const testGroup = labsByDate[dateStr];
              const hba1cTest = testGroup.find((t) => t.test_name === 'HbA1c');
              return (
                <div key={dateStr} className="metric-card" style={{ padding: '18px', borderTop: '3px solid var(--primary)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.92rem', color: 'var(--text-main)' }}>{dateStr}</span>
                    {hba1cTest && (
                      <span
                        className={`badge ${hba1cTest.result >= 8.0 ? 'badge-critical' : hba1cTest.result >= 7.0 ? 'badge-warning' : 'badge-normal'}`}
                        style={{ fontSize: '0.78rem' }}
                      >
                        HbA1c: {hba1cTest.result}%
                      </span>
                    )}
                  </div>

                  <table style={{ width: '100%', fontSize: '0.82rem', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--border)', textAlign: 'left' }}>
                        <th style={{ padding: '4px 0' }}>Test Name</th>
                        <th style={{ padding: '4px 0', textAlign: 'right' }}>Result</th>
                        <th style={{ padding: '4px 0', textAlign: 'right' }}>Ref Range</th>
                      </tr>
                    </thead>
                    <tbody>
                      {testGroup.map((lab) => (
                        <tr key={lab.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                          <td style={{ padding: '6px 0', color: 'var(--text-main)', fontWeight: lab.test_name === 'HbA1c' ? 600 : 400 }}>
                            {lab.test_name}
                          </td>
                          <td style={{ padding: '6px 0', textAlign: 'right', fontWeight: 600, color: lab.test_name === 'HbA1c' ? 'var(--primary)' : 'var(--text-main)' }}>
                            {lab.result} {lab.unit}
                          </td>
                          <td style={{ padding: '6px 0', textAlign: 'right', color: 'var(--text-muted)', fontSize: '0.76rem' }}>
                            {lab.reference_range || '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Synthetic Genetic Susceptibility Markers */}
      {!isLoading && !error && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>🧬</span> Synthetic Genetic Susceptibility Profiles
            </h3>
            <span className="badge badge-neutral" style={{ fontSize: '0.72rem' }}>
              Simulated Illumina Array
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '14px' }}>
            {genetics.map((marker) => (
              <div key={marker.id} className="metric-card" style={{ padding: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '0.92rem' }}>{marker.marker_id}</span>
                  <span className="badge badge-normal" style={{ fontSize: '0.72rem' }}>Gene: {marker.gene}</span>
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--primary)', fontWeight: 600, marginBottom: '6px' }}>
                  {marker.genotype}
                </div>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                  Platform: {marker.data_source} | Recorded: {new Date(marker.recorded_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>

          <p style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: '12px', fontStyle: 'italic' }}>
            * Note: Genetic markers are presented as contextual genomic background. The prediction model relies on validated multi-vital time-series features and does not incorporate genetic variants without prospective clinical calibration.
          </p>
        </div>
      )}
    </div>
  );
}
