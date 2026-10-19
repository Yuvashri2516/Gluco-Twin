import React, { useState, useEffect } from 'react';
import { createPatient, updatePatient } from '../api/client';
import LoadingSpinner from './Common/LoadingSpinner';

export default function PatientModal({
  isOpen,
  onClose,
  mode = 'create',
  initialData = null,
  onPatientSaved,
}) {
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    gender: 'Male',
    diabetes_type: 'Type 2',
    years_since_diagnosis: '0',
    historical_diagnoses: '',
    medical_history: '',
    weight_kg: '',
    height_cm: '',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});

  useEffect(() => {
    if (isOpen) {
      setErrorMessage(null);
      setFieldErrors({});
      if (mode === 'edit' && initialData) {
        setFormData({
          name: initialData.name || '',
          age: initialData.age ? String(initialData.age) : '',
          gender: initialData.gender || 'Male',
          diabetes_type: initialData.diabetes_type || 'Type 2',
          years_since_diagnosis: initialData.years_since_diagnosis !== undefined ? String(initialData.years_since_diagnosis) : '0',
          historical_diagnoses: initialData.historical_diagnoses && initialData.historical_diagnoses !== 'None' ? initialData.historical_diagnoses : '',
          medical_history: initialData.medical_history || '',
          weight_kg: initialData.weight_kg ? String(initialData.weight_kg) : '',
          height_cm: initialData.height_cm ? String(initialData.height_cm) : '',
        });
      } else {
        setFormData({
          name: '',
          age: '',
          gender: 'Male',
          diabetes_type: 'Type 2',
          years_since_diagnosis: '0',
          historical_diagnoses: '',
          medical_history: '',
          weight_kg: '',
          height_cm: '',
        });
      }
    }
  }, [isOpen, mode, initialData]);

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (fieldErrors[name]) {
      setFieldErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const calculatedBmi = () => {
    const w = parseFloat(formData.weight_kg);
    const h = parseFloat(formData.height_cm);
    if (w > 0 && h > 0) {
      return (w / ((h / 100) ** 2)).toFixed(1);
    }
    return null;
  };

  const validate = () => {
    const errors = {};
    if (!formData.name.trim() || formData.name.trim().length < 2) {
      errors.name = 'Patient name must be at least 2 characters.';
    }
    const ageNum = parseInt(formData.age, 10);
    if (isNaN(ageNum) || ageNum < 1 || ageNum > 120) {
      errors.age = 'Age must be between 1 and 120 years.';
    }
    const yearsNum = parseInt(formData.years_since_diagnosis, 10);
    if (isNaN(yearsNum) || yearsNum < 0 || yearsNum > 100) {
      errors.years_since_diagnosis = 'Years since diagnosis must be between 0 and 100.';
    }
    if (formData.weight_kg && (parseFloat(formData.weight_kg) < 10 || parseFloat(formData.weight_kg) > 400)) {
      errors.weight_kg = 'Weight must be between 10 kg and 400 kg.';
    }
    if (formData.height_cm && (parseFloat(formData.height_cm) < 40 || parseFloat(formData.height_cm) > 260)) {
      errors.height_cm = 'Height must be between 40 cm and 260 cm.';
    }
    return errors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errors = validate();
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    const payload = {
      name: formData.name.trim(),
      age: parseInt(formData.age, 10),
      gender: formData.gender,
      diabetes_type: formData.diabetes_type,
      years_since_diagnosis: parseInt(formData.years_since_diagnosis, 10),
      historical_diagnoses: formData.historical_diagnoses.trim() || 'None',
      medical_history: formData.medical_history.trim(),
      weight_kg: formData.weight_kg ? parseFloat(formData.weight_kg) : null,
      height_cm: formData.height_cm ? parseFloat(formData.height_cm) : null,
    };

    try {
      let saved;
      if (mode === 'edit' && initialData) {
        saved = await updatePatient(initialData.id, payload);
      } else {
        saved = await createPatient(payload);
      }
      onPatientSaved(saved);
      onClose();
    } catch (err) {
      setErrorMessage(err.message || 'Failed to save patient profile.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const bmi = calculatedBmi();

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-group">
            <h3 className="modal-title">
              {mode === 'edit' ? `Edit Patient Profile (#${initialData?.id})` : 'Register New Patient'}
            </h3>
            <p className="modal-subtitle">
              {mode === 'edit'
                ? 'Update physiological attributes, baseline diagnoses, and clinical history.'
                : 'Create an isolated digital twin context. No fake telemetry is silently created.'}
            </p>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            &times;
          </button>
        </div>

        {errorMessage && (
          <div className="form-error-banner" style={{ margin: '0 24px 16px' }}>
            <span className="error-icon">&#9888;</span>
            <span>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="modal-body-scroll">
            {/* Full Name */}
            <div className="form-group">
              <label htmlFor="patient-name-input" className="form-label">
                Full Name <span className="required-star">*</span>
              </label>
              <input
                id="patient-name-input"
                name="name"
                type="text"
                className={`form-input ${fieldErrors.name ? 'input-error' : ''}`}
                placeholder="e.g. Ramesh Patel"
                value={formData.name}
                onChange={handleChange}
                autoFocus
              />
              {fieldErrors.name && <span className="field-error-text">{fieldErrors.name}</span>}
            </div>

            {/* Row: Age, Sex, Diabetes Type */}
            <div className="form-row-3">
              <div className="form-group">
                <label htmlFor="patient-age-input" className="form-label">
                  Age <span className="required-star">*</span>
                </label>
                <input
                  id="patient-age-input"
                  name="age"
                  type="number"
                  min="1"
                  max="120"
                  className={`form-input ${fieldErrors.age ? 'input-error' : ''}`}
                  placeholder="e.g. 52"
                  value={formData.age}
                  onChange={handleChange}
                />
                {fieldErrors.age && <span className="field-error-text">{fieldErrors.age}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="patient-gender-select" className="form-label">
                  Sex <span className="required-star">*</span>
                </label>
                <select
                  id="patient-gender-select"
                  name="gender"
                  className="form-select"
                  value={formData.gender}
                  onChange={handleChange}
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="patient-diabetes-select" className="form-label">
                  Diabetes Type <span className="required-star">*</span>
                </label>
                <select
                  id="patient-diabetes-select"
                  name="diabetes_type"
                  className="form-select"
                  value={formData.diabetes_type}
                  onChange={handleChange}
                >
                  <option value="Type 2">Type 2</option>
                  <option value="Type 1">Type 1</option>
                  <option value="Pre-diabetic">Pre-diabetic</option>
                  <option value="Gestational">Gestational</option>
                  <option value="None / Healthy">None / Healthy</option>
                </select>
              </div>
            </div>

            {/* Row: Years since diagnosis, Weight, Height */}
            <div className="form-row-3">
              <div className="form-group">
                <label htmlFor="patient-years-input" className="form-label">
                  Years Diagnosed
                </label>
                <input
                  id="patient-years-input"
                  name="years_since_diagnosis"
                  type="number"
                  min="0"
                  max="100"
                  className={`form-input ${fieldErrors.years_since_diagnosis ? 'input-error' : ''}`}
                  value={formData.years_since_diagnosis}
                  onChange={handleChange}
                />
                {fieldErrors.years_since_diagnosis && (
                  <span className="field-error-text">{fieldErrors.years_since_diagnosis}</span>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="patient-weight-input" className="form-label">
                  Weight (kg)
                </label>
                <input
                  id="patient-weight-input"
                  name="weight_kg"
                  type="number"
                  step="0.1"
                  min="10"
                  max="400"
                  placeholder="e.g. 74.5"
                  className={`form-input ${fieldErrors.weight_kg ? 'input-error' : ''}`}
                  value={formData.weight_kg}
                  onChange={handleChange}
                />
                {fieldErrors.weight_kg && <span className="field-error-text">{fieldErrors.weight_kg}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="patient-height-input" className="form-label">
                  Height (cm)
                </label>
                <input
                  id="patient-height-input"
                  name="height_cm"
                  type="number"
                  step="0.5"
                  min="40"
                  max="260"
                  placeholder="e.g. 170"
                  className={`form-input ${fieldErrors.height_cm ? 'input-error' : ''}`}
                  value={formData.height_cm}
                  onChange={handleChange}
                />
                {fieldErrors.height_cm && <span className="field-error-text">{fieldErrors.height_cm}</span>}
              </div>
            </div>

            {/* Live BMI Preview if calculated */}
            {bmi && (
              <div className="bmi-preview-banner">
                <span className="bmi-label">Computed Baseline BMI:</span>
                <span className="bmi-value">{bmi} kg/m²</span>
                <span className="bmi-category">
                  {parseFloat(bmi) < 18.5
                    ? '(Underweight)'
                    : parseFloat(bmi) < 25
                    ? '(Normal weight)'
                    : parseFloat(bmi) < 30
                    ? '(Overweight)'
                    : '(Obese)'}
                </span>
              </div>
            )}

            {/* Diagnoses */}
            <div className="form-group">
              <label htmlFor="patient-diagnoses-input" className="form-label">
                Baseline Diagnoses (comma-separated)
              </label>
              <input
                id="patient-diagnoses-input"
                name="historical_diagnoses"
                type="text"
                className="form-input"
                placeholder="e.g. Hypertension, Essential Tremor, Hyperlipidemia"
                value={formData.historical_diagnoses}
                onChange={handleChange}
              />
            </div>

            {/* Medical History */}
            <div className="form-group">
              <label htmlFor="patient-history-input" className="form-label">
                Relevant Medical History &amp; Clinical Notes
              </label>
              <textarea
                id="patient-history-input"
                name="medical_history"
                rows="3"
                className="form-textarea"
                placeholder="Enter clinical encounter summaries, surgical history, or medication regimens..."
                value={formData.medical_history}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
              {isSubmitting ? (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                  <LoadingSpinner size="sm" />
                  Saving...
                </span>
              ) : mode === 'edit' ? (
                'Save Changes'
              ) : (
                'Register Patient'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
