import React from 'react';

/**
 * Reusable Slider Input with live badge and label
 */
export default function SliderInput({
  label,
  value,
  unit = '',
  min,
  max,
  step = 1,
  onChange,
  valuePrefix = '',
  helperText
}) {
  return (
    <div className="slider-container">
      <div className="slider-label-row">
        <span>{label}</span>
        <span className="slider-value-pill">
          {valuePrefix}{value} {unit}
        </span>
      </div>
      <input
        type="range"
        className="range-slider"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
      {helperText && (
        <span style={{ fontSize: 11, color: 'var(--color-navy-500)', marginTop: -2 }}>
          {helperText}
        </span>
      )}
    </div>
  );
}
