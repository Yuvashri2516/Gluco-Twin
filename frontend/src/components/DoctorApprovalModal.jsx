import React, { useState, useEffect, useCallback } from 'react';
import { fetchDoctorRequests, approveDoctorRequest, rejectDoctorRequest } from '../api/client';
import LoadingSpinner from './Common/LoadingSpinner';

export default function DoctorApprovalModal({ isOpen, onClose }) {
  const [requests, setRequests] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [actionInProgressId, setActionInProgressId] = useState(null);
  const [error, setError] = useState(null);
  const [successNotice, setSuccessNotice] = useState(null);

  const loadRequests = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchDoctorRequests();
      setRequests(data);
    } catch (err) {
      setError(err.detail || err.message || 'Failed to load doctor registration requests.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      loadRequests();
      setSuccessNotice(null);
    }
  }, [isOpen, loadRequests]);

  const handleApprove = async (userId, username) => {
    setActionInProgressId(userId);
    setError(null);
    setSuccessNotice(null);
    try {
      await approveDoctorRequest(userId);
      setSuccessNotice(`Doctor account '${username}' successfully approved! They may now sign in.`);
      await loadRequests();
    } catch (err) {
      setError(err.detail || err.message || 'Failed to approve doctor request.');
    } finally {
      setActionInProgressId(null);
    }
  };

  const handleReject = async (userId, username) => {
    setActionInProgressId(userId);
    setError(null);
    setSuccessNotice(null);
    try {
      await rejectDoctorRequest(userId);
      setSuccessNotice(`Doctor request for '${username}' was rejected.`);
      await loadRequests();
    } catch (err) {
      setError(err.detail || err.message || 'Failed to reject doctor request.');
    } finally {
      setActionInProgressId(null);
    }
  };

  if (!isOpen) return null;

  const pendingRequests = requests.filter((r) => r.approval_status === 'pending');
  const pastRequests = requests.filter((r) => r.approval_status !== 'pending');

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card doctor-approval-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-wrap">
            <div className="modal-badge-icon doctor">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <polyline points="16 11 18 13 22 9" />
              </svg>
            </div>
            <div>
              <h2 className="modal-title">Doctor Account Approval Requests</h2>
              <p className="modal-subtitle">
                Review and approve clinician access requests with server-side authorization enforcement.
              </p>
            </div>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close">
            &times;
          </button>
        </div>

        <div className="modal-body">
          {error && (
            <div className="portal-alert error-alert" style={{ marginBottom: '16px' }}>
              <span>{error}</span>
            </div>
          )}

          {successNotice && (
            <div className="portal-alert success-alert" style={{ marginBottom: '16px' }}>
              <span>{successNotice}</span>
            </div>
          )}

          {isLoading ? (
            <div style={{ padding: '40px 0' }}>
              <LoadingSpinner message="Fetching doctor registration requests..." />
            </div>
          ) : (
            <>
              {/* Pending Section */}
              <div className="requests-section">
                <h3 className="requests-section-title">
                  Pending Approval ({pendingRequests.length})
                </h3>
                {pendingRequests.length === 0 ? (
                  <p className="empty-requests-text">No pending doctor requests awaiting review.</p>
                ) : (
                  <div className="requests-list">
                    {pendingRequests.map((req) => (
                      <div key={req.id} className="request-item-card">
                        <div className="req-main-info">
                          <div className="req-name-row">
                            <strong>{req.full_name || req.username}</strong>
                            <span className="req-badge pending">PENDING</span>
                          </div>
                          <div className="req-meta-row">
                            <span>Username: <code>{req.username}</code></span>
                            <span>Email: {req.email || 'N/A'}</span>
                            {req.medical_license_number && (
                              <span>License: <code>{req.medical_license_number}</code></span>
                            )}
                            <span>Requested: {new Date(req.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                        <div className="req-actions">
                          <button
                            type="button"
                            className="btn-approve"
                            disabled={actionInProgressId === req.id}
                            onClick={() => handleApprove(req.id, req.username)}
                          >
                            {actionInProgressId === req.id ? 'Processing...' : 'Approve'}
                          </button>
                          <button
                            type="button"
                            className="btn-reject"
                            disabled={actionInProgressId === req.id}
                            onClick={() => handleReject(req.id, req.username)}
                          >
                            Reject
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Resolved / Approved History Section */}
              {pastRequests.length > 0 && (
                <div className="requests-section" style={{ marginTop: '24px' }}>
                  <h3 className="requests-section-title">
                    Approved Clinicians &amp; Resolved Requests ({pastRequests.length})
                  </h3>
                  <div className="requests-table-wrapper">
                    <table className="requests-table">
                      <thead>
                        <tr>
                          <th>Clinician Name</th>
                          <th>Username</th>
                          <th>Email</th>
                          <th>License #</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {pastRequests.map((r) => (
                          <tr key={r.id}>
                            <td><strong>{r.full_name || r.username}</strong></td>
                            <td><code>{r.username}</code></td>
                            <td>{r.email || 'N/A'}</td>
                            <td>{r.medical_license_number || 'N/A'}</td>
                            <td>
                              <span className={`req-badge ${r.approval_status}`}>
                                {r.approval_status.toUpperCase()}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        <div className="modal-footer">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
