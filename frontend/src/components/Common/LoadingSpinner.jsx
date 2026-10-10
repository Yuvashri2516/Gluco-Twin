import React from 'react';

export default function LoadingSpinner({ message = 'Loading clinical data...' }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px 20px',
      gap: '16px',
      color: 'var(--text-secondary)',
    }}>
      <div style={{
        width: '36px',
        height: '36px',
        border: '3px solid var(--border-medium)',
        borderTopColor: 'var(--primary)',
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
      }} />
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
      <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>{message}</span>
    </div>
  );
}
