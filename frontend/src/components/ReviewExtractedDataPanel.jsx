import React, { useState, useEffect } from 'react';
import {
  fetchDocumentPreview,
  confirmDocumentExtraction,
  cancelDocumentExtraction,
  fetchPatientDocuments,
  downloadDocumentFile,
} from '../api/client';
import LoadingSpinner from './Common/LoadingSpinner';

export default function ReviewExtractedDataPanel({
  documentId,
  selectedPatient,
  onBackToDocuments,
  onConfirmSuccess,
}) {
  const [docPreview, setDocPreview] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorBanner, setErrorBanner] = useState(null);
  const [successBanner, setSuccessBanner] = useState(null);

  // Editable candidate states
  const [editableLabs, setEditableLabs] = useState([]);
  const [editableReadings, setEditableReadings] = useState([]);
  const [clinicalNotes, setClinicalNotes] = useState('');
  const [nameMismatchConfirmed, setNameMismatchConfirmed] = useState(false);
  const [showRawText, setShowRawText] = useState(false);

  // Document switcher dropdown
  const [allDocs, setAllDocs] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(documentId);

  // Load document list for switcher
  useEffect(() => {
    if (selectedPatient?.id) {
      fetchPatientDocuments(selectedPatient.id)
        .then((docs) => setAllDocs(docs || []))
        .catch(() => {});
    }
  }, [selectedPatient?.id]);

  useEffect(() => {
    if (documentId) {
      setSelectedDocId(documentId);
    }
  }, [documentId]);

  useEffect(() => {
    if (!selectedDocId) {
      setIsLoading(false);
      return;
    }

    let isCurrent = true;
    const controller = new AbortController();

    async function loadPreview() {
      setIsLoading(true);
      setErrorBanner(null);
      setSuccessBanner(null);
      try {
        const data = await fetchDocumentPreview(selectedDocId, controller.signal);
        if (isCurrent) {
          setDocPreview(data);
          const ext = data.extraction || {};
          const candidateLabs = (ext.candidate_labs || []).map((l, idx) => ({
            id: `lab-${idx}`,
            test_name: l.test_name || '',
            result: l.result !== undefined ? String(l.result) : '',
            unit: l.unit || '%',
            reference_range: l.reference_range || '',
            measurement_date: l.measurement_date || new Date().toISOString().split('T')[0],
            warnings: l.warnings || [],
            included: true,
          }));
          const candidateReadings = (ext.candidate_readings || []).map((r, idx) => ({
            id: `read-${idx}`,
            value: r.value !== undefined ? String(r.value) : '',
            unit: r.unit || 'mg/dL',
            timestamp: r.timestamp || new Date().toISOString(),
            included: true,
          }));

          setEditableLabs(candidateLabs);
          setEditableReadings(candidateReadings);
          setNameMismatchConfirmed(false);
        }
      } catch (err) {
        if (isCurrent && err.name !== 'AbortError') {
          setErrorBanner(err.message || 'Failed to load document preview.');
        }
      } finally {
        if (isCurrent) setIsLoading(false);
      }
    }

    loadPreview();
    return () => {
      isCurrent = false;
      controller.abort();
    };
  }, [selectedDocId]);

  if (!selectedPatient) {
    return (
      <div className="section-container">
        <div className="empty-state-card">
          <p className="empty-state-text">Please select a patient from the top bar to review documents.</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="section-container">
        <div style={{ padding: '60px 0' }}>
          <LoadingSpinner message="Extracting structured clinical data &amp; verifying patient identity..." />
        </div>
      </div>
    );
  }

  if (!docPreview) {
    return (
      <div className="section-container">
        <div className="card">
          <div className="card-header-clean">
            <h3 className="card-title">Document Intelligence Review</h3>
          </div>
          <div className="empty-state-card">
            <p className="empty-state-text">No document currently selected for extraction review.</p>
            {allDocs.length > 0 ? (
              <div style={{ marginTop: '16px' }}>
                <label className="form-label">Choose a document to review:</label>
                <select
                  className="form-select"
                  style={{ maxWidth: '400px', margin: '0 auto' }}
                  onChange={(e) => setSelectedDocId(Number(e.target.value))}
                  value={selectedDocId || ''}
                >
                  <option value="">-- Select uploaded document --</option>
                  {allDocs.map((d) => (
                    <option key={d.id} value={d.id}>
                      Doc #{d.id} - {d.original_filename} ({d.is_confirmed ? 'Confirmed' : 'Draft'})
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <button className="btn btn-primary" onClick={onBackToDocuments} style={{ marginTop: '12px' }}>
                Upload Medical Documents First
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  const extraction = docPreview.extraction || {};
  const hasMismatch = extraction.patient_name_match === false;
  const isAlreadyConfirmed = docPreview.is_confirmed;
  const isCancelled = docPreview.processing_status === 'cancelled';

  const handleLabFieldChange = (id, field, value) => {
    setEditableLabs((prev) =>
      prev.map((item) => (item.id === id ? { ...item, [field]: value } : item))
    );
  };

  const handleLabToggle = (id) => {
    setEditableLabs((prev) =>
      prev.map((item) => (item.id === id ? { ...item, included: !item.included } : item))
    );
  };

  const handleAddCustomLabRow = () => {
    setEditableLabs((prev) => [
      ...prev,
      {
        id: `custom-lab-${Date.now()}`,
        test_name: 'Fasting Blood Glucose',
        result: '',
        unit: 'mg/dL',
        reference_range: '70 - 99 mg/dL',
        measurement_date: new Date().toISOString().split('T')[0],
        warnings: [],
        included: true,
      },
    ]);
  };

  const handleConfirm = async () => {
    if (hasMismatch && !nameMismatchConfirmed) {
      setErrorBanner(
        'Identity Safety Check: The document patient name differs from the active patient profile. Please review the identity warning and check the confirmation box before proceeding.'
      );
      return;
    }

    const confirmedLabs = editableLabs
      .filter((l) => l.included && l.test_name && l.result && !isNaN(parseFloat(l.result)))
      .map((l) => ({
        patient_id: selectedPatient.id,
        test_name: l.test_name.trim(),
        result: parseFloat(l.result),
        unit: l.unit.trim(),
        reference_range: l.reference_range ? l.reference_range.trim() : null,
        measurement_date: l.measurement_date ? new Date(l.measurement_date).toISOString() : null,
      }));

    const confirmedReadings = editableReadings
      .filter((r) => r.included && r.value && !isNaN(parseFloat(r.value)))
      .map((r) => ({
        patient_id: selectedPatient.id,
        value: parseFloat(r.value),
        unit: r.unit || 'mg/dL',
        timestamp: r.timestamp || null,
      }));

    if (confirmedLabs.length === 0 && confirmedReadings.length === 0 && !clinicalNotes.trim()) {
      setErrorBanner('No valid laboratory results or readings selected to commit to EHR.');
      return;
    }

    setIsSubmitting(true);
    setErrorBanner(null);
    setSuccessBanner(null);

    try {
      const res = await confirmDocumentExtraction(docPreview.document_id, {
        confirmedLabs,
        confirmedReadings,
        clinicalNotes: clinicalNotes.trim(),
      });
      setSuccessBanner(
        `✓ ${res.message} Ingested ${res.confirmed_labs_count} lab panel(s) and ${res.confirmed_readings_count} reading(s) into ${selectedPatient.name}'s active EHR.`
      );
      setDocPreview((prev) => ({ ...prev, is_confirmed: true, processing_status: 'confirmed' }));
      if (onConfirmSuccess) onConfirmSuccess();
    } catch (err) {
      setErrorBanner(err.message || 'Failed to confirm document extraction.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancelExtraction = async () => {
    if (!window.confirm('Cancel this extraction draft? No values will be committed to the patient record.')) {
      return;
    }
    setIsSubmitting(true);
    try {
      await cancelDocumentExtraction(docPreview.document_id);
      setSuccessBanner('Extraction draft has been cancelled. Active medical records were left untouched.');
      setDocPreview((prev) => ({ ...prev, processing_status: 'cancelled' }));
    } catch (err) {
      setErrorBanner(err.message || 'Failed to cancel extraction.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="section-container">
      {/* Top Header & Navigation */}
      <div className="section-header-banner">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', width: '100%' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button className="btn btn-secondary btn-sm" onClick={onBackToDocuments}>
                &larr; Back to Documents
              </button>
              <h2 className="section-title" style={{ margin: 0 }}>
                Review Document Intelligence Draft
              </h2>
            </div>
            <p className="section-desc" style={{ marginTop: '4px' }}>
              Draft extraction from <strong>{docPreview.original_filename}</strong> for patient{' '}
              <strong>{selectedPatient.name}</strong>. Values remain strictly unconfirmed until approved by the clinician.
            </p>
          </div>

          {/* Quick Switcher */}
          {allDocs.length > 1 && (
            <div style={{ minWidth: '220px' }}>
              <label className="form-label" style={{ fontSize: '0.75rem', marginBottom: '2px' }}>
                Review Another Document:
              </label>
              <select
                className="form-select form-select-sm"
                value={selectedDocId}
                onChange={(e) => setSelectedDocId(Number(e.target.value))}
              >
                {allDocs.map((d) => (
                  <option key={d.id} value={d.id}>
                    #{d.id}: {d.original_filename.slice(0, 24)} {d.is_confirmed ? '(Confirmed)' : ''}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
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

      {/* Identity Mismatch Warning Alert */}
      {hasMismatch && !isAlreadyConfirmed && (
        <div className="identity-mismatch-banner">
          <div className="mismatch-icon">&#9888;</div>
          <div className="mismatch-content">
            <h4 className="mismatch-title">Patient Identity Mismatch Detected</h4>
            <p className="mismatch-desc">
              The document text indicates patient <strong>'{extraction.extracted_patient_name}'</strong>, which differs
              from the active dashboard profile <strong>'{selectedPatient.name}'</strong> (#{selectedPatient.id}).
              Automated identity merging is prohibited by clinical safety policy.
            </p>
            <label className="mismatch-checkbox-label">
              <input
                type="checkbox"
                checked={nameMismatchConfirmed}
                onChange={(e) => setNameMismatchConfirmed(e.target.checked)}
              />
              <span>
                I confirm that this document clinically belongs to patient <strong>{selectedPatient.name}</strong> and
                authorize ingesting these records under patient ID #{selectedPatient.id}.
              </span>
            </label>
          </div>
        </div>
      )}

      {/* Document Meta Summary Card */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div className="doc-meta-strip">
          <div className="doc-meta-item">
            <span className="doc-meta-label">Original File</span>
            <span className="doc-meta-val">{docPreview.original_filename}</span>
          </div>
          <div className="doc-meta-item">
            <span className="doc-meta-label">File Type</span>
            <span className="doc-meta-val" style={{ textTransform: 'uppercase' }}>
              {extraction.document_type || 'Unknown'}
            </span>
          </div>
          <div className="doc-meta-item">
            <span className="doc-meta-label">Document Date</span>
            <span className="doc-meta-val">
              {extraction.extracted_dates && extraction.extracted_dates[0]
                ? extraction.extracted_dates[0]
                : 'Not Detected'}
            </span>
          </div>
          <div className="doc-meta-item">
            <span className="doc-meta-label">OCR Status</span>
            <span className="doc-meta-val">
              {extraction.ocr_used
                ? 'OCR Applied (Tesseract)'
                : extraction.ocr_available
                ? 'Native Text Layer'
                : 'OCR Engine Unavailable'}
            </span>
          </div>
          <div className="doc-meta-item">
            <span className="doc-meta-label">Status</span>
            <span className="doc-meta-val">
              {isAlreadyConfirmed ? (
                <span className="badge badge-normal">✓ Confirmed to EHR</span>
              ) : isCancelled ? (
                <span className="badge">Draft Cancelled</span>
              ) : (
                <span className="badge badge-warning">Unconfirmed Draft</span>
              )}
            </span>
          </div>
          <div className="doc-meta-item" style={{ marginLeft: 'auto' }}>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => downloadDocumentFile(docPreview.document_id, docPreview.original_filename)}
            >
              Download Original File
            </button>
          </div>
        </div>
      </div>

      {/* SECTION 1: Candidate Lab Results */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div className="card-header-clean">
          <div>
            <h3 className="card-title">Candidate Laboratory Panels</h3>
            <p className="card-subtitle">
              Verify detected analytes, values, units, and reference ranges. Clinicians can adjust any field before
              saving.
            </p>
          </div>
          {!isAlreadyConfirmed && (
            <button className="btn btn-secondary btn-sm" onClick={handleAddCustomLabRow}>
              + Add Another Lab Field
            </button>
          )}
        </div>

        {editableLabs.length === 0 ? (
          <div className="empty-state-card" style={{ padding: '24px' }}>
            <p className="empty-state-text">No standard lab panel values were automatically extracted.</p>
            <p className="empty-state-sub" style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              You may click '+ Add Another Lab Field' to manually map values from the document text below.
            </p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="medical-docs-table candidate-labs-table">
              <thead>
                <tr>
                  <th style={{ width: '40px' }}>Include</th>
                  <th>Laboratory Test</th>
                  <th>Result Value</th>
                  <th>Unit</th>
                  <th>Reference Range</th>
                  <th>Collection Date</th>
                  <th>Warnings / Notes</th>
                </tr>
              </thead>
              <tbody>
                {editableLabs.map((lab) => (
                  <tr key={lab.id} className={!lab.included ? 'row-excluded' : ''}>
                    <td>
                      <input
                        type="checkbox"
                        checked={lab.included}
                        onChange={() => handleLabToggle(lab.id)}
                        disabled={isAlreadyConfirmed}
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        className="form-input form-input-sm"
                        value={lab.test_name}
                        onChange={(e) => handleLabFieldChange(lab.id, 'test_name', e.target.value)}
                        disabled={!lab.included || isAlreadyConfirmed}
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        step="0.01"
                        className="form-input form-input-sm"
                        value={lab.result}
                        onChange={(e) => handleLabFieldChange(lab.id, 'result', e.target.value)}
                        disabled={!lab.included || isAlreadyConfirmed}
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        className="form-input form-input-sm"
                        value={lab.unit}
                        onChange={(e) => handleLabFieldChange(lab.id, 'unit', e.target.value)}
                        disabled={!lab.included || isAlreadyConfirmed}
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        className="form-input form-input-sm"
                        value={lab.reference_range}
                        onChange={(e) => handleLabFieldChange(lab.id, 'reference_range', e.target.value)}
                        disabled={!lab.included || isAlreadyConfirmed}
                      />
                    </td>
                    <td>
                      <input
                        type="date"
                        className="form-input form-input-sm"
                        value={lab.measurement_date}
                        onChange={(e) => handleLabFieldChange(lab.id, 'measurement_date', e.target.value)}
                        disabled={!lab.included || isAlreadyConfirmed}
                      />
                    </td>
                    <td>
                      {lab.warnings && lab.warnings.length > 0 ? (
                        <span className="candidate-warning-badge" title={lab.warnings.join('; ')}>
                          &#9888; {lab.warnings[0]}
                        </span>
                      ) : (
                        <span className="candidate-clean-badge">✓ Valid Range</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* SECTION 2: Candidate Glucose Time-Series Readings (if tabular) */}
      {editableReadings.length > 0 && (
        <div className="card" style={{ marginBottom: '20px' }}>
          <div className="card-header-clean">
            <div>
              <h3 className="card-title">Candidate Time-Series Telemetry ({editableReadings.length} Points)</h3>
              <p className="card-subtitle">Parsed from tabular glucose or CGM log file.</p>
            </div>
          </div>
          <div className="table-responsive" style={{ maxHeight: '240px', overflowY: 'auto' }}>
            <table className="medical-docs-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Glucose Value</th>
                  <th>Unit</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {editableReadings.slice(0, 15).map((r) => (
                  <tr key={r.id}>
                    <td>{new Date(r.timestamp).toLocaleString()}</td>
                    <td>
                      <strong>{r.value}</strong>
                    </td>
                    <td>{r.unit}</td>
                    <td>
                      <span className="badge badge-normal">Ready for Ingestion</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SECTION 3: Clinical Notes & Approval */}
      {!isAlreadyConfirmed && !isCancelled && (
        <div className="card" style={{ marginBottom: '20px' }}>
          <div className="card-header-clean">
            <h3 className="card-title">Clinician Approval &amp; Context Notes</h3>
          </div>
          <div className="form-group">
            <label className="form-label">Add Note to Patient Medical History (Optional)</label>
            <textarea
              rows="2"
              className="form-textarea"
              placeholder="e.g. Ingested quarterly HbA1c panel. Glycemic control is improving with lifestyle interventions..."
              value={clinicalNotes}
              onChange={(e) => setClinicalNotes(e.target.value)}
            />
          </div>

          <div className="review-actions-bar">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleCancelExtraction}
              disabled={isSubmitting}
            >
              Cancel Draft (Leave EHR Untouched)
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleConfirm}
              disabled={isSubmitting || (hasMismatch && !nameMismatchConfirmed)}
            >
              {isSubmitting ? (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                  <LoadingSpinner size="sm" />
                  Saving to EHR...
                </span>
              ) : (
                'Confirm & Save to EHR'
              )}
            </button>
          </div>
        </div>
      )}

      {/* SECTION 4: Raw Extracted Document Text Accordion */}
      <div className="card">
        <div
          className="card-header-clean"
          style={{ cursor: 'pointer', userSelect: 'none' }}
          onClick={() => setShowRawText(!showRawText)}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h3 className="card-title">Raw Document Text / OCR Extraction</h3>
            <span className="badge">{showRawText ? 'Hide' : 'Inspect'}</span>
          </div>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            {showRawText ? '▲ Collapse' : '▼ Expand'}
          </span>
        </div>

        {showRawText && (
          <div className="raw-text-container">
            <pre className="raw-text-pre">{extraction.raw_text || 'No raw text available.'}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
