import React from 'react';

export default function PatientOverview({
  patients = [],
  selectedPatient,
  onSelectPatient,
  isLoading,
}) {
  if (isLoading && (!patients || patients.length === 0)) {
    return null;
  }

  // Calculate BMI if weight and height are present
  let bmi = null;
  if (selectedPatient && selectedPatient.weight_kg && selectedPatient.height_cm) {
    const heightM = selectedPatient.height_cm / 100;
    bmi = (selectedPatient.weight_kg / (heightM * heightM)).toFixed(1);
  }

  return (
    <div className="patient-overview-section">
      {/* Active Selected Patient Header Card */}
      {selectedPatient && (
        <div className="active-patient-card">
          <div className="patient-avatar-box">
            <span className="avatar-initials">
              {selectedPatient.name
                .split(' ')
                .map((n) => n[0])
                .join('')
                .substring(0, 2)
                .toUpperCase()}
            </span>
          </div>

          <div className="patient-main-info">
            <div className="patient-title-row">
              <h2 className="patient-name">{selectedPatient.name}</h2>
              <span className="patient-id-tag">Record #{selectedPatient.id}</span>
              <span className={`badge ${
                selectedPatient.diabetes_type === 'Type 1'
                  ? 'badge-warning'
                  : selectedPatient.diabetes_type === 'Type 2'
                  ? 'badge-twin'
                  : 'badge-normal'
              }`}>
                {selectedPatient.diabetes_type}
              </span>
            </div>

            <div className="patient-vitals-strip">
              <div className="strip-item">
                <span className="strip-label">Age</span>
                <span className="strip-value">{selectedPatient.age} yrs</span>
              </div>
              <div className="strip-divider" />
              <div className="strip-item">
                <span className="strip-label">Gender</span>
                <span className="strip-value">{selectedPatient.gender}</span>
              </div>
              <div className="strip-divider" />
              <div className="strip-item">
                <span className="strip-label">Diagnosis Duration</span>
                <span className="strip-value">{selectedPatient.years_since_diagnosis} yrs</span>
              </div>
              <div className="strip-divider" />
              <div className="strip-item">
                <span className="strip-label">Weight</span>
                <span className="strip-value">
                  {selectedPatient.weight_kg ? `${selectedPatient.weight_kg} kg` : 'N/A'}
                </span>
              </div>
              <div className="strip-divider" />
              <div className="strip-item">
                <span className="strip-label">Height</span>
                <span className="strip-value">
                  {selectedPatient.height_cm ? `${selectedPatient.height_cm} cm` : 'N/A'}
                </span>
              </div>
              {bmi && (
                <>
                  <div className="strip-divider" />
                  <div className="strip-item">
                    <span className="strip-label">BMI</span>
                    <span className="strip-value">{bmi} kg/m²</span>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Cohort Switcher Grid */}
      <div className="cohort-selector-container">
        <div className="cohort-header">
          <span className="cohort-title">Registered Cohort ({patients.length} Patients)</span>
          <span className="cohort-subtitle">Click to switch digital twin context</span>
        </div>

        <div className="cohort-grid">
          {patients.map((p) => {
            const isSelected = selectedPatient && selectedPatient.id === p.id;
            return (
              <div
                key={p.id}
                className={`cohort-card ${isSelected ? 'selected' : ''}`}
                onClick={() => onSelectPatient(p.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') onSelectPatient(p.id);
                }}
              >
                <div className="cohort-card-top">
                  <span className="cohort-name">{p.name}</span>
                  <span className="cohort-id">#{p.id}</span>
                </div>
                <div className="cohort-card-meta">
                  <span>{p.age}y &bull; {p.gender}</span>
                  <span className={`cohort-type-tag ${
                    p.diabetes_type === 'Type 1'
                      ? 'type-1'
                      : p.diabetes_type === 'Type 2'
                      ? 'type-2'
                      : 'pre-diab'
                  }`}>
                    {p.diabetes_type}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
