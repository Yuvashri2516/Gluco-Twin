import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine
} from 'recharts';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';

/**
 * Screen 2: Patient History (Longitudinal EHR & Baseline Profile)
 */
export default function PatientHistoryScreen({ patient }) {
  if (!patient) return null;

  const labHistory = patient.lab_history || [];

  return (
    <div className="content-area">
      <div className="page-header">
        <div>
          <h1 className="page-title">Patient Clinical History</h1>
          <p className="page-description">
            Longitudinal EHR context: demographics, laboratory progression, active pharmacological regimens, and encounter notes.
          </p>
        </div>
        <Badge variant="neutral">EHR ID: {patient.id}</Badge>
      </div>

      {/* Grid: Profile Summary & Lab History */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 'var(--spacing-md)', marginBottom: 'var(--spacing-md)' }}>
        {/* Baseline Demographics Card */}
        <Card title="Demographic & Metabolic Baseline">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: 6 }}>
              <span style={{ color: 'var(--color-navy-500)', fontSize: 13 }}>Archetype Classification:</span>
              <span style={{ fontWeight: 600, color: 'var(--color-teal-700)', fontSize: 13 }}>{patient.archetype}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: 6 }}>
              <span style={{ color: 'var(--color-navy-500)', fontSize: 13 }}>Diagnosis Year:</span>
              <span style={{ fontWeight: 600 }}>{patient.demographics?.diagnosis_year}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: 6 }}>
              <span style={{ color: 'var(--color-navy-500)', fontSize: 13 }}>Height & Weight:</span>
              <span style={{ fontWeight: 600 }}>{patient.demographics?.height_cm} cm / {patient.demographics?.weight_kg} kg (BMI: {patient.bmi})</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: 6 }}>
              <span style={{ color: 'var(--color-navy-500)', fontSize: 13 }}>Insulin Sensitivity Factor:</span>
              <span style={{ fontWeight: 600 }}>1:{patient.basal_profile?.insulin_sensitivity_factor} mg/dL</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: 6 }}>
              <span style={{ color: 'var(--color-navy-500)', fontSize: 13 }}>Carb-to-Insulin Ratio:</span>
              <span style={{ fontWeight: 600 }}>1:{patient.basal_profile?.carb_insulin_ratio} g/U</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: 6 }}>
              <span style={{ color: 'var(--color-navy-500)', fontSize: 13 }}>Genetic Marker Stream:</span>
              <span style={{ fontSize: 12, color: 'var(--color-navy-500)' }}>Unconfigured (Optional module)</span>
            </div>
          </div>
        </Card>

        {/* Longitudinal HbA1c Lab Progression Chart */}
        <Card
          title="Longitudinal HbA1c Progression"
          subtitle="Serial laboratory measurements (Synthea) against clinical guideline target (<7.0%)"
          headerAction={<Badge variant="target">Current: 6.8%</Badge>}
        >
          <div style={{ width: '100%', height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={labHistory} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" vertical={false} />
                <XAxis dataKey="date" tickLine={false} tick={{ fill: 'var(--color-navy-500)', fontSize: 11 }} />
                <YAxis domain={[5.5, 9.0]} ticks={[6.0, 7.0, 8.0, 9.0]} tickLine={false} tick={{ fill: 'var(--color-navy-500)', fontSize: 11 }} unit="%" />
                <Tooltip />
                <ReferenceLine
                  y={7.0}
                  stroke="var(--color-target-green)"
                  strokeDasharray="4 4"
                  label={{ value: 'Target Goal (7.0%)', fill: 'var(--color-target-green-dark)', fontSize: 11, position: 'top' }}
                />
                <Area
                  type="monotone"
                  dataKey="hba1c"
                  name="HbA1c (%)"
                  stroke="var(--color-teal-600)"
                  strokeWidth={2.5}
                  fill="rgba(13, 148, 136, 0.12)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Medication Regimen Table */}
      <Card
        title="Active Pharmacological Regimens"
        subtitle="Current prescribed insulin protocols, oral agents, and adherence records"
        className="mb-4"
      >
        <table className="clinical-table">
          <thead>
            <tr>
              <th>Medication Name</th>
              <th>Prescribed Dosage</th>
              <th>Administration Frequency</th>
              <th>Adherence Rate</th>
            </tr>
          </thead>
          <tbody>
            {(patient.active_medications || []).map((med, idx) => (
              <tr key={idx}>
                <td style={{ fontWeight: 600 }}>{med.name}</td>
                <td>{med.dosage}</td>
                <td>{med.frequency}</td>
                <td>
                  <Badge variant={med.adherence_pct >= 90 ? 'target' : 'warning'}>
                    {med.adherence_pct}% Confirmed
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      {/* Clinical Encounters Log */}
      <div style={{ marginTop: 'var(--spacing-md)' }}>
        <Card title="Clinical Encounters & Consultation Log">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {(patient.encounters || []).map((enc, idx) => (
              <div
                key={idx}
                style={{
                  padding: 12,
                  backgroundColor: 'var(--color-canvas)',
                  borderRadius: 8,
                  borderLeft: '4px solid var(--color-teal-600)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontWeight: 600, color: 'var(--color-navy-900)' }}>{enc.type}</span>
                  <span style={{ fontSize: 12, color: 'var(--color-navy-500)' }}>{enc.date} • {enc.clinician}</span>
                </div>
                <p style={{ fontSize: 13, color: 'var(--color-navy-700)', margin: 0 }}>
                  {enc.notes}
                </p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
