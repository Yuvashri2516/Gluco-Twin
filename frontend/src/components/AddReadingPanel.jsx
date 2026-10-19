import React, { useState } from 'react';
import {
  recordManualGlucose,
  recordManualVitals,
  recordManualLab,
  recordManualDiagnosis,
} from '../api/client';
import LoadingSpinner from './Common/LoadingSpinner';

const COMMON_LAB_PRESETS = [
  { testName: 'HbA1c', unit: '%', referenceRange: '< 5.7%' },
  { testName: 'Fasting Blood Glucose', unit: 'mg/dL', referenceRange: '70 - 99 mg/dL' },
  { testName: 'Random Blood Glucose', unit: 'mg/dL', referenceRange: '70 - 140 mg/dL' },
  { testName: 'Total Cholesterol', unit: 'mg/dL', referenceRange: '< 200 mg/dL' },
  { testName: 'HDL Cholesterol', unit: 'mg/dL', referenceRange: '> 40 mg/dL' },
  { testName: 'LDL Cholesterol', unit: 'mg/dL', referenceRange: '< 100 mg/dL' },
  { testName: 'Triglycerides', unit: 'mg/dL', referenceRange: '< 150 mg/dL' },
  { testName: 'Serum Creatinine', unit: 'mg/dL', referenceRange: '0.6 - 1.2 mg/dL' },
  { testName: 'eGFR', unit: 'mL/min/1.73m²', referenceRange: '> 90 mL/min/1.73m²' },
  { testName: 'Microalbumin', unit: 'mg/g', referenceRange: '< 30 mg/g' },
];

export default function AddReadingPanel({ selectedPatient, onDataSaved }) {
  const [activeFormTab, setActiveFormTab] = useState('glucose'); // 'glucose' | 'vitals' | 'labs' | 'diagnosis'
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successBanner, setSuccessBanner] = useState(null);
  const [errorBanner, setErrorBanner] = useState(null);

  // Form states
  const [glucoseForm, setGlucoseForm] = useState({
    value: '',
    unit: 'mg/dL',
    timestamp: '',
    dataSource: 'manual',
  });

  const [vitalsForm, setVitalsForm] = useState({
    heartRate: '',
    hrv: '',
    timestamp: '',
    dataSource: 'manual',
  });

  const [labForm, setLabForm] = useState({
    testName: 'HbA1c',
    customTestName: '',
    result: '',
    unit: '%',
    referenceRange: '< 5.7%',
    measurementDate: '',
    labSource: 'Diagnostic Pathology Lab',
    dataSource: 'manual',
  });

  const [diagnosisForm, setDiagnosisForm] = useState({
    diagnosisName: '',
    date: new Date().toISOString().split('T')[0],
    status: 'active',
    notes: '',
  });

  if (!selectedPatient) {
    return (
      <div className="section-container">
        <div className="empty-state-card">
          <p className="empty-state-text">Please select a patient from the top bar to record medical entries.</p>
        </div>
      </div>
    );
  }

  const handleLabPresetChange = (e) => {
    const selectedName = e.target.value;
    const preset = COMMON_LAB_PRESETS.find((p) => p.testName === selectedName);
    if (preset) {
      setLabForm((prev) => ({
        ...prev,
        testName: preset.testName,
        unit: preset.unit,
        referenceRange: preset.referenceRange,
      }));
    } else {
      setLabForm((prev) => ({
        ...prev,
        testName: 'Custom',
        unit: 'mg/dL',
        referenceRange: '',
      }));
    }
  };

  const handleGlucoseSubmit = async (e) => {
    e.preventDefault();
    if (!glucoseForm.value || isNaN(parseFloat(glucoseForm.value))) {
      setErrorBanner('Please enter a valid numeric glucose value.');
      return;
    }
    setIsSubmitting(true);
    setErrorBanner(null);
    setSuccessBanner(null);
    try {
      const res = await recordManualGlucose({
        patientId: selectedPatient.id,
        value: glucoseForm.value,
        unit: glucoseForm.unit,
        timestamp: glucoseForm.timestamp ? new Date(glucoseForm.timestamp).toISOString() : null,
        dataSource: glucoseForm.dataSource,
      });
      setSuccessBanner(
        `✓ Successfully saved glucose measurement (${res.value} mg/dL, recorded via ${res.data_source || 'manual'}). Digital twin and alerts updated.`
      );
      setGlucoseForm({ value: '', unit: 'mg/dL', timestamp: '', dataSource: 'manual' });
      if (onDataSaved) onDataSaved();
    } catch (err) {
      setErrorBanner(err.message || 'Failed to save glucose reading.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleVitalsSubmit = async (e) => {
    e.preventDefault();
    if (!vitalsForm.heartRate && !vitalsForm.hrv) {
      setErrorBanner('Please enter at least one measurement: Heart Rate or HRV.');
      return;
    }
    setIsSubmitting(true);
    setErrorBanner(null);
    setSuccessBanner(null);
    try {
      const res = await recordManualVitals({
        patientId: selectedPatient.id,
        heartRate: vitalsForm.heartRate,
        hrv: vitalsForm.hrv,
        timestamp: vitalsForm.timestamp ? new Date(vitalsForm.timestamp).toISOString() : null,
        dataSource: vitalsForm.dataSource,
      });
      setSuccessBanner(
        `✓ Successfully recorded autonomic vitals (HR: ${res.heart_rate || '--'} bpm, HRV: ${res.hrv || '--'} ms).`
      );
      setVitalsForm({ heartRate: '', hrv: '', timestamp: '', dataSource: 'manual' });
      if (onDataSaved) onDataSaved();
    } catch (err) {
      setErrorBanner(err.message || 'Failed to save vital readings.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLabSubmit = async (e) => {
    e.preventDefault();
    const finalTestName =
      labForm.testName === 'Custom' ? labForm.customTestName.trim() : labForm.testName;
    if (!finalTestName) {
      setErrorBanner('Please specify a laboratory test name.');
      return;
    }
    if (!labForm.result || isNaN(parseFloat(labForm.result))) {
      setErrorBanner('Please enter a valid numeric result value.');
      return;
    }

    setIsSubmitting(true);
    setErrorBanner(null);
    setSuccessBanner(null);
    try {
      const res = await recordManualLab(selectedPatient.id, {
        testName: finalTestName,
        result: labForm.result,
        unit: labForm.unit,
        referenceRange: labForm.referenceRange,
        measurementDate: labForm.measurementDate ? new Date(labForm.measurementDate).toISOString() : null,
        labSource: labForm.labSource,
        dataSource: labForm.dataSource,
      });
      setSuccessBanner(
        `✓ Successfully added laboratory result: ${res.test_name} = ${res.result} ${res.unit} (Source: ${res.lab_source}).`
      );
      setLabForm((prev) => ({ ...prev, result: '', measurementDate: '' }));
      if (onDataSaved) onDataSaved();
    } catch (err) {
      setErrorBanner(err.message || 'Failed to record laboratory panel.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDiagnosisSubmit = async (e) => {
    e.preventDefault();
    if (!diagnosisForm.diagnosisName.trim()) {
      setErrorBanner('Please enter a diagnosis or clinical condition name.');
      return;
    }

    setIsSubmitting(true);
    setErrorBanner(null);
    setSuccessBanner(null);
    try {
      const res = await recordManualDiagnosis(selectedPatient.id, {
        diagnosisName: diagnosisForm.diagnosisName.trim(),
        date: diagnosisForm.date,
        notes: diagnosisForm.notes,
        status: diagnosisForm.status,
      });
      setSuccessBanner(
        `✓ Updated clinical history for ${res.name}. Current diagnoses: ${res.historical_diagnoses}`
      );
      setDiagnosisForm({
        diagnosisName: '',
        date: new Date().toISOString().split('T')[0],
        status: 'active',
        notes: '',
      });
      if (onDataSaved) onDataSaved();
    } catch (err) {
      setErrorBanner(err.message || 'Failed to record diagnosis.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="section-container">
      <div className="section-header-banner">
        <div>
          <h2 className="section-title">Manual Medical Data Ingestion</h2>
          <p className="section-desc">
            Directly record physiological measurements, laboratory panel results, and clinical history for{' '}
            <strong>{selectedPatient.name}</strong> (#{selectedPatient.id}). Data is tagged with its source and
            immediately integrates with the digital twin model and alert engine.
          </p>
        </div>
      </div>

      {/* Segmented Form Tabs */}
      <div className="form-tab-nav">
        <button
          className={`form-tab-btn ${activeFormTab === 'glucose' ? 'active' : ''}`}
          onClick={() => {
            setActiveFormTab('glucose');
            setErrorBanner(null);
            setSuccessBanner(null);
          }}
        >
          Continuous / Spot Glucose
        </button>
        <button
          className={`form-tab-btn ${activeFormTab === 'vitals' ? 'active' : ''}`}
          onClick={() => {
            setActiveFormTab('vitals');
            setErrorBanner(null);
            setSuccessBanner(null);
          }}
        >
          Autonomic Vitals (HR / HRV)
        </button>
        <button
          className={`form-tab-btn ${activeFormTab === 'labs' ? 'active' : ''}`}
          onClick={() => {
            setActiveFormTab('labs');
            setErrorBanner(null);
            setSuccessBanner(null);
          }}
        >
          Laboratory Panels (HbA1c / Lipids)
        </button>
        <button
          className={`form-tab-btn ${activeFormTab === 'diagnosis' ? 'active' : ''}`}
          onClick={() => {
            setActiveFormTab('diagnosis');
            setErrorBanner(null);
            setSuccessBanner(null);
          }}
        >
          Diagnoses &amp; Clinical Notes
        </button>
      </div>

      {/* Notifications */}
      {successBanner && (
        <div className="form-success-banner">
          <span>{successBanner}</span>
          <button className="banner-dismiss" onClick={() => setSuccessBanner(null)}>
            &times;
          </button>
        </div>
      )}
      {errorBanner && (
        <div className="form-error-banner">
          <span className="error-icon">&#9888;</span>
          <span>{errorBanner}</span>
          <button className="banner-dismiss" onClick={() => setErrorBanner(null)}>
            &times;
          </button>
        </div>
      )}

      {/* FORM A: GLUCOSE */}
      {activeFormTab === 'glucose' && (
        <div className="card form-panel-card">
          <div className="card-header-clean">
            <h3 className="card-title">Record Blood Glucose Reading</h3>
            <span className="source-tag-badge source-manual">Source: Manual Entry</span>
          </div>
          <form onSubmit={handleGlucoseSubmit} className="ingestion-form">
            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label">
                  Glucose Value <span className="required-star">*</span>
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0.5"
                  max="800"
                  placeholder={glucoseForm.unit === 'mg/dL' ? 'e.g. 138' : 'e.g. 7.6'}
                  className="form-input"
                  value={glucoseForm.value}
                  onChange={(e) => setGlucoseForm({ ...glucoseForm, value: e.target.value })}
                  required
                />
                {glucoseForm.unit === 'mmol/L' && glucoseForm.value && !isNaN(parseFloat(glucoseForm.value)) && (
                  <span className="helper-note">
                    Standard equivalent: ~{(parseFloat(glucoseForm.value) * 18.0182).toFixed(1)} mg/dL
                  </span>
                )}
              </div>

              <div className="form-group">
                <label className="form-label">Unit of Measurement</label>
                <select
                  className="form-select"
                  value={glucoseForm.unit}
                  onChange={(e) => setGlucoseForm({ ...glucoseForm, unit: e.target.value })}
                >
                  <option value="mg/dL">mg/dL (Standard US/International)</option>
                  <option value="mmol/L">mmol/L (UK/European/Canadian)</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Measurement Timestamp</label>
                <input
                  type="datetime-local"
                  className="form-input"
                  value={glucoseForm.timestamp}
                  onChange={(e) => setGlucoseForm({ ...glucoseForm, timestamp: e.target.value })}
                />
                <span className="helper-note">Leave blank to use current UTC time.</span>
              </div>

              <div className="form-group">
                <label className="form-label">Data Ingestion Source Label</label>
                <select
                  className="form-select"
                  value={glucoseForm.dataSource}
                  onChange={(e) => setGlucoseForm({ ...glucoseForm, dataSource: e.target.value })}
                >
                  <option value="manual">Manual Entry (Clinician / Patient)</option>
                  <option value="measured">Measured (CGM Sensor Reading)</option>
                  <option value="imported">Imported (External Health Record)</option>
                </select>
              </div>
            </div>

            <div className="form-actions-right">
              <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                {isSubmitting ? 'Saving Measurement...' : 'Save Glucose Reading'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* FORM B: VITALS */}
      {activeFormTab === 'vitals' && (
        <div className="card form-panel-card">
          <div className="card-header-clean">
            <h3 className="card-title">Record Autonomic &amp; Cardiovascular Vitals</h3>
            <span className="source-tag-badge source-manual">Source: Manual Entry</span>
          </div>
          <form onSubmit={handleVitalsSubmit} className="ingestion-form">
            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label">Heart Rate (bpm)</label>
                <input
                  type="number"
                  step="0.5"
                  min="30"
                  max="240"
                  placeholder="e.g. 72.0"
                  className="form-input"
                  value={vitalsForm.heartRate}
                  onChange={(e) => setVitalsForm({ ...vitalsForm, heartRate: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Heart Rate Variability (HRV - RMSSD, ms)</label>
                <input
                  type="number"
                  step="0.5"
                  min="1"
                  max="300"
                  placeholder="e.g. 48.0"
                  className="form-input"
                  value={vitalsForm.hrv}
                  onChange={(e) => setVitalsForm({ ...vitalsForm, hrv: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Timestamp</label>
                <input
                  type="datetime-local"
                  className="form-input"
                  value={vitalsForm.timestamp}
                  onChange={(e) => setVitalsForm({ ...vitalsForm, timestamp: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Data Source</label>
                <select
                  className="form-select"
                  value={vitalsForm.dataSource}
                  onChange={(e) => setVitalsForm({ ...vitalsForm, dataSource: e.target.value })}
                >
                  <option value="manual">Manual Entry</option>
                  <option value="measured">Measured (Smartwatch / ECG Sensor)</option>
                  <option value="imported">Imported Telemetry</option>
                </select>
              </div>
            </div>

            <div className="form-actions-right">
              <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                {isSubmitting ? 'Saving Vitals...' : 'Save Vital Reading'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* FORM C: LABS */}
      {activeFormTab === 'labs' && (
        <div className="card form-panel-card">
          <div className="card-header-clean">
            <h3 className="card-title">Record Clinical Laboratory Panel</h3>
            <span className="source-tag-badge source-manual">Source: Manual Entry</span>
          </div>
          <form onSubmit={handleLabSubmit} className="ingestion-form">
            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label">
                  Laboratory Test Preset <span className="required-star">*</span>
                </label>
                <select className="form-select" value={labForm.testName} onChange={handleLabPresetChange}>
                  {COMMON_LAB_PRESETS.map((p) => (
                    <option key={p.testName} value={p.testName}>
                      {p.testName} ({p.unit})
                    </option>
                  ))}
                  <option value="Custom">Custom / Other Panel...</option>
                </select>
              </div>

              {labForm.testName === 'Custom' && (
                <div className="form-group">
                  <label className="form-label">Custom Test Name</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. C-Peptide"
                    value={labForm.customTestName}
                    onChange={(e) => setLabForm({ ...labForm, customTestName: e.target.value })}
                    required
                  />
                </div>
              )}

              <div className="form-group">
                <label className="form-label">
                  Result Numeric Value <span className="required-star">*</span>
                </label>
                <input
                  type="number"
                  step="0.01"
                  placeholder="e.g. 7.4"
                  className="form-input"
                  value={labForm.result}
                  onChange={(e) => setLabForm({ ...labForm, result: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Result Unit</label>
                <input
                  type="text"
                  className="form-input"
                  value={labForm.unit}
                  onChange={(e) => setLabForm({ ...labForm, unit: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Reference Range</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. < 5.7%"
                  value={labForm.referenceRange}
                  onChange={(e) => setLabForm({ ...labForm, referenceRange: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Sample Collection Date</label>
                <input
                  type="date"
                  className="form-input"
                  value={labForm.measurementDate}
                  onChange={(e) => setLabForm({ ...labForm, measurementDate: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Laboratory / Diagnostic Facility</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Central Diagnostic Laboratories"
                  value={labForm.labSource}
                  onChange={(e) => setLabForm({ ...labForm, labSource: e.target.value })}
                />
              </div>
            </div>

            <div className="form-actions-right">
              <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                {isSubmitting ? 'Saving Lab Result...' : 'Save Laboratory Result'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* FORM D: DIAGNOSIS */}
      {activeFormTab === 'diagnosis' && (
        <div className="card form-panel-card">
          <div className="card-header-clean">
            <h3 className="card-title">Add Diagnosis &amp; Clinical Encounter Notes</h3>
            <span className="source-tag-badge source-manual">Source: Clinical Entry</span>
          </div>
          <form onSubmit={handleDiagnosisSubmit} className="ingestion-form">
            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label">
                  Diagnosis / Medical Condition <span className="required-star">*</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g. Diabetic Peripheral Neuropathy, Coronary Artery Disease"
                  className="form-input"
                  value={diagnosisForm.diagnosisName}
                  onChange={(e) => setDiagnosisForm({ ...diagnosisForm, diagnosisName: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Encounter / Onset Date</label>
                <input
                  type="date"
                  className="form-input"
                  value={diagnosisForm.date}
                  onChange={(e) => setDiagnosisForm({ ...diagnosisForm, date: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Clinical Status</label>
                <select
                  className="form-select"
                  value={diagnosisForm.status}
                  onChange={(e) => setDiagnosisForm({ ...diagnosisForm, status: e.target.value })}
                >
                  <option value="active">Active Condition</option>
                  <option value="chronic">Chronic / Ongoing</option>
                  <option value="resolved">Resolved / Historical</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Encounter Notes / Assessment</label>
              <textarea
                rows="3"
                className="form-textarea"
                placeholder="Document clinical observations, medication adjustments, or specialist consultations..."
                value={diagnosisForm.notes}
                onChange={(e) => setDiagnosisForm({ ...diagnosisForm, notes: e.target.value })}
              />
            </div>

            <div className="form-actions-right">
              <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                {isSubmitting ? 'Logging Diagnosis...' : 'Append Diagnosis to Record'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
