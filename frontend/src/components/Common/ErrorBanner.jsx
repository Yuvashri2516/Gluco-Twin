import React from 'react';

export default function ErrorBanner({ message, onRetry }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '16px',
      padding: '16px 20px',
      backgroundColor: 'var(--status-critical-bg)',
      border: '1px solid rgba(239, 68, 68, 0.3)',
      borderRadius: 'var(--radius-md)',
      color: 'var(--status-critical)',
      margin: '12px 0',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>{message}</span>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            padding: '6px 14px',
            backgroundColor: 'rgba(239, 68, 68, 0.2)',
            color: 'var(--text-main)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.82rem',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
          onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.35)'}
          onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.2)'}
        >
          Retry
        </button>
      )}
    </div>
  );
}
