import React from 'react';

/**
 * Reusable Card container
 */
export default function Card({ title, subtitle, headerAction, children, footer, className = '' }) {
  return (
    <div className={`card ${className}`}>
      {(title || headerAction) && (
        <div className="card-header">
          <div>
            {title && <h3 className="card-title">{title}</h3>}
            {subtitle && <p className="card-subtitle">{subtitle}</p>}
          </div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}
      <div className="card-body">{children}</div>
      {footer && <div className="card-footer">{footer}</div>}
    </div>
  );
}
