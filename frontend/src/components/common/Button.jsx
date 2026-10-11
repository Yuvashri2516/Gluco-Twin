import React from 'react';

/**
 * Reusable Button component
 * @param {'primary' | 'secondary' | 'outline'} variant
 * @param {'sm' | 'md'} size
 */
export default function Button({
  variant = 'primary',
  size = 'md',
  children,
  icon: Icon,
  onClick,
  disabled = false,
  className = '',
  type = 'button'
}) {
  const btnClass = `btn btn-${variant} ${size === 'sm' ? 'btn-sm' : ''} ${className}`;
  return (
    <button type={type} className={btnClass} onClick={onClick} disabled={disabled}>
      {Icon && <Icon size={size === 'sm' ? 14 : 16} />}
      {children}
    </button>
  );
}
