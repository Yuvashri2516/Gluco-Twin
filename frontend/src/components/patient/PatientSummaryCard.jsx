import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';

/**
 * Patient Summary Profile Card
 */
export default function PatientSummaryCard({ patient }) {
  if (!patient) return null;

  return (
    <Card
      title="Patient Clinical Profile"
      subtitle="Synthetic EHR context feeding the personalized Digital Twin"
      headerAction={<Badge variant="neutral">{patient.id}</Badge>}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: 8 }}>
          <span style={{ color: 'var(--color-navy-500)', fontSize: 13 }}>Full Name:</span>
          <span style={{ fontWeight: 600, color: 'var(--color-navy-900)', fontSize: 13 }}>{patient.name}</span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: 8 }}>
          <span style={{ color: 'var(--color-navy-500)', fontSize: 13 }}>Archetype:</span>
          <span style={{ fontWeight: 600, color: 'var(--color-teal-700)', fontSize: 12 }}>{patient.archetype}</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: 8 }}>
          <div>
            <div style={{ color: 'var(--color-navy-500)', fontSize: 11 }}>Age / Gender:</div>
            <div style={{ fontWeight: 600, fontSize: 13 }}>{patient.age}y / {patient.gender}</div>
          </div>
          <div>
            <div style={{ color: 'var(--color-navy-500)', fontSize: 11 }}>BMI / Height:</div>
            <div style={{ fontWeight: 600, fontSize: 13 }}>{patient.bmi} ({patient.demographics?.height_cm} cm)</div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: 8 }}>
          <div>
            <div style={{ color: 'var(--color-navy-500)', fontSize: 11 }}>Basal Rate:</div>
            <div style={{ fontWeight: 600, fontSize: 13 }}>{patient.basal_profile?.basal_rate_units_per_hour} U/hr</div>
          </div>
          <div>
            <div style={{ color: 'var(--color-navy-500)', fontSize: 11 }}>Sensitivity (ISF):</div>
            <div style={{ fontWeight: 600, fontSize: 13 }}>1:{patient.basal_profile?.insulin_sensitivity_factor} mg/dL</div>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: 2 }}>
          <span style={{ color: 'var(--color-navy-500)', fontSize: 11 }}>Attending Physician:</span>
          <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-navy-800)' }}>
            {patient.demographics?.attending_physician || 'Staff Endocrinologist'}
          </span>
        </div>
      </div>
    </Card>
  );
}
