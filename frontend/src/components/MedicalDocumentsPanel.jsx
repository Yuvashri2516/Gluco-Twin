import React, { useState, useEffect, useRef } from 'react';
import {
  uploadMedicalDocument,
  fetchPatientDocuments,
  deleteMedicalDocument,
  downloadDocumentFile,
} from '../api/client';
import LoadingSpinner from './Common/LoadingSpinner';

export default function MedicalDocumentsPanel({
  selectedPatient,
  onOpenReview,
  onDocumentConfirmed,
}) {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [category, setCategory] = useState('lab_report');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const patientId = selectedPatient?.id;

  const loadDocuments = async (signal) => {
    if (!patientId) return;
    setIsLoading(true);
    setUploadError(null);
    try {
      const data = await fetchPatientDocuments(patientId, signal);
      setDocuments(data || []);
    } catch (err) {
      if (err.name !== 'AbortError') {
        setUploadError(err.message || 'Failed to load medical documents.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (patientId) {
      const controller = new AbortController();
      loadDocuments(controller.signal);
      return () => controller.abort();
    }
  }, [patientId]);

  if (!selectedPatient) {
    return (
      <div className="section-container">
        <div className="empty-state-card">
          <p className="empty-state-text">Please select a patient to view and manage medical documents.</p>
        </div>
      </div>
    );
  }

  const handleFileUpload = async (file) => {
    if (!file) return;

    // Client-side extension validation
    const allowed = ['.pdf', '.png', '.jpg', '.jpeg', '.csv', '.xlsx'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowed.includes(ext)) {
      setUploadError(`File '${file.name}' has an unsupported extension. Allowed: PDF, PNG, JPG, JPEG, CSV, XLSX.`);
      return;
    }

    // 15MB limit
    if (file.size > 15 * 1024 * 1024) {
      setUploadError(`File '${file.name}' (${(file.size / (1024 * 1024)).toFixed(1)}MB) exceeds the 15MB upload limit.`);
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const res = await uploadMedicalDocument(patientId, file, category);
      setUploadSuccess(`✓ Successfully uploaded and analyzed '${res.original_filename}'. Ready for draft review.`);
      await loadDocuments();
      if (fileInputRef.current) fileInputRef.current.value = '';
      // Offer prompt or open review directly
      if (onOpenReview) {
        onOpenReview(res.id);
      }
    } catch (err) {
      setUploadError(err.message || 'Error uploading document.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (docId, fileName) => {
    if (!window.confirm(`Are you sure you want to permanently delete '${fileName}'?`)) return;
    try {
      await deleteMedicalDocument(docId);
      setUploadSuccess(`Document '${fileName}' removed.`);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch (err) {
      setUploadError(err.message || 'Failed to delete document.');
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="section-container">
      <div className="section-header-banner">
        <div>
          <h2 className="section-title">Medical Documents &amp; Diagnostic Ingestion</h2>
          <p className="section-desc">
            Upload clinical laboratory panels, physician encounter notes, and CGM telemetry exports for{' '}
            <strong>{selectedPatient.name}</strong> (#{selectedPatient.id}). Local intelligence automatically parses
            text, detects physiological markers, and isolates unconfirmed values in reviewable drafts.
          </p>
        </div>
      </div>

      {uploadSuccess && (
        <div className="form-success-banner">
          <span>{uploadSuccess}</span>
          <button className="banner-dismiss" onClick={() => setUploadSuccess(null)}>
            &times;
          </button>
        </div>
      )}
      {uploadError && (
        <div className="form-error-banner">
          <span className="error-icon">&#9888;</span>
          <span>{uploadError}</span>
          <button className="banner-dismiss" onClick={() => setUploadError(null)}>
            &times;
          </button>
        </div>
      )}

      {/* Upload Drop Zone Card */}
      <div className="card upload-drop-zone-card">
        <div className="upload-controls-top">
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label" style={{ marginBottom: '4px' }}>
              Document Category
            </label>
            <select
              className="form-select"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              disabled={isUploading}
            >
              <option value="lab_report">Clinical Laboratory Panel (HbA1c / Lipids / CMP)</option>
              <option value="clinical_note">Physician Consultation / Encounter Summary</option>
              <option value="cgm_export">CGM Sensor Telemetry Export (CSV / XLSX)</option>
              <option value="other">General Diagnostic Record / Other</option>
            </select>
          </div>
        </div>

        <div
          className={`drop-area ${dragActive ? 'drag-over' : ''} ${isUploading ? 'uploading-state' : ''}`}
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => !isUploading && fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.csv,.xlsx"
            style={{ display: 'none' }}
            onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
            disabled={isUploading}
          />

          {isUploading ? (
            <div className="upload-progress-box">
              <LoadingSpinner size="md" />
              <p className="upload-progress-title">Uploading &amp; Extracting Medical Entities...</p>
              <p className="upload-progress-sub">PyMuPDF text extraction &amp; entity parsing in progress.</p>
            </div>
          ) : (
            <div className="drop-prompt-box">
              <svg className="upload-cloud-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              <p className="drop-main-text">
                <strong>Click to browse</strong> or drag &amp; drop medical files here
              </p>
              <p className="drop-sub-text">
                Supports PDF reports, scanned image reports (PNG, JPG), and telemetry tables (CSV, XLSX) up to 15MB
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Document Roster */}
      <div className="card" style={{ marginTop: '24px' }}>
        <div className="card-header-clean">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h3 className="card-title">Patient Documents ({documents.length})</h3>
            <span className="badge badge-normal">{selectedPatient.name}</span>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={() => loadDocuments()} disabled={isLoading}>
            Refresh List
          </button>
        </div>

        {isLoading ? (
          <div style={{ padding: '36px 0' }}>
            <LoadingSpinner message="Fetching patient document registry..." />
          </div>
        ) : documents.length === 0 ? (
          <div className="empty-state-card">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            <p className="empty-state-text" style={{ marginTop: '8px' }}>
              No medical documents uploaded yet for {selectedPatient.name}.
            </p>
            <p className="empty-state-sub" style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Use the upload area above to attach PDF laboratory panels or CSV/XLSX sensor records.
            </p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="medical-docs-table">
              <thead>
                <tr>
                  <th>Document Name</th>
                  <th>Category</th>
                  <th>Size</th>
                  <th>Uploaded</th>
                  <th>Extraction Status</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => {
                  const isConfirmed = doc.is_confirmed;
                  const isCancelled = doc.processing_status === 'cancelled';
                  return (
                    <tr key={doc.id} className={isConfirmed ? 'row-confirmed' : ''}>
                      <td>
                        <div className="doc-name-cell">
                          <span className="doc-icon-badge">
                            {doc.original_filename.endsWith('.pdf')
                              ? 'PDF'
                              : doc.original_filename.match(/\.(csv|xlsx)$/i)
                              ? 'TAB'
                              : 'IMG'}
                          </span>
                          <div>
                            <span className="doc-filename-link" onClick={() => onOpenReview && onOpenReview(doc.id)}>
                              {doc.original_filename}
                            </span>
                            <span className="doc-id-sub">Doc #{doc.id}</span>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className="category-pill">
                          {doc.document_category === 'lab_report'
                            ? 'Lab Panel'
                            : doc.document_category === 'clinical_note'
                            ? 'Clinical Note'
                            : doc.document_category === 'cgm_export'
                            ? 'CGM Telemetry'
                            : 'General'}
                        </span>
                      </td>
                      <td>{formatFileSize(doc.file_size)}</td>
                      <td>
                        {doc.upload_timestamp
                          ? new Date(doc.upload_timestamp).toLocaleDateString(undefined, {
                              month: 'short',
                              day: 'numeric',
                              year: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })
                          : '--'}
                      </td>
                      <td>
                        {isConfirmed ? (
                          <span className="badge badge-normal">✓ Confirmed to EHR</span>
                        ) : isCancelled ? (
                          <span className="badge" style={{ backgroundColor: 'rgba(100, 116, 139, 0.1)', color: 'var(--text-muted)' }}>
                            Draft Cancelled
                          </span>
                        ) : doc.processing_status === 'completed' ? (
                          <span className="badge badge-warning">Reviewable Draft</span>
                        ) : doc.processing_status === 'failed' ? (
                          <span className="badge badge-critical">Parsing Error</span>
                        ) : (
                          <span className="badge badge-twin">Processing...</span>
                        )}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <div className="action-buttons-group">
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => onOpenReview && onOpenReview(doc.id)}
                            title="Inspect draft extractions and map values"
                          >
                            {isConfirmed ? 'View Draft' : 'Review & Confirm'}
                          </button>
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => downloadDocumentFile(doc.id, doc.original_filename)}
                            title="Download file securely with auth"
                          >
                            Download
                          </button>
                          <button
                            className="btn btn-danger-subtle btn-sm"
                            onClick={() => handleDelete(doc.id, doc.original_filename)}
                            title="Delete document"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
