import React from 'react';

/**
 * Reusable clinical status badge pill
 * @param {'target' | 'warning' | 'critical' | 'twin' | 'neutral'} variant
 */
export default function Badge({ variant = 'neutral', children, icon: Icon, className = '' }) {
  const variantClass = `badge-${variant}`;
  return (
    <span className={`badge ${variantClass} ${className}`}>
      {Icon && <Icon size={11} style={{ marginRight: 2 }} />}
      {children}
    </span>
  );
}
