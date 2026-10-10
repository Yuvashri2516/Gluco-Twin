import React from 'react';

export default function EmptyState({ title = 'No Data Available', message, icon }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '48px 24px',
      backgroundColor: 'rgba(255, 255, 255, 0.02)',
      borderRadius: 'var(--radius-md)',
      border: '1px dashed var(--border-medium)',
      textAlign: 'center',
      color: 'var(--text-secondary)',
    }}>
      <div style={{
        width: '48px',
        height: '48px',
        borderRadius: '50%',
        backgroundColor: 'rgba(255, 255, 255, 0.04)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: '16px',
        color: 'var(--text-muted)',
      }}>
        {icon || (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="8" y1="12" x2="16" y2="12" />
          </svg>
        )}
      </div>
      <h4 style={{ color: 'var(--text-main)', fontSize: '1rem', fontWeight: 600, marginBottom: '6px' }}>
        {title}
      </h4>
      {message && (
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', maxWidth: '420px', lineHeight: 1.5 }}>
          {message}
        </p>
      )}
    </div>
  );
}
